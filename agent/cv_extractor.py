"""
CV Extractor — Extração determinística do SceneGraph a partir de frames.

Pipeline:
  1. Vision LLM extrai SceneGraph estruturado via JSON schema estrito
  2. Validação e normalização das bounding boxes
  3. Cálculo automático de parallax_sensitivity por depth
  4. Fallback geométrico se LLM falhar

REGRA: IA NÃO decide geometria. CV decide geometria. IA decide movimento.

Para produção com hardware GPU, substituir pelas implementações:
  - Depth Anything V2  → profundidade densa (depth map)
  - SAM2               → segmentação de objetos com máscaras
  - GroundingDINO      → detecção de objetos com texto
  - YOLOv8             → detecção de objetos em tempo real

Aqui implementamos a versão LLM-vision que funciona sem GPU.
"""

from __future__ import annotations
import json
import re
import math
from typing import Optional, List, TYPE_CHECKING

from scene_graph import SceneGraph, SceneLayer, BBox

if TYPE_CHECKING:
    from ai_client import AIClient


# Prompt de extração — muito estrito para garantir geometria precisa
_EXTRACTION_PROMPT = """Você é um sistema de Computer Vision analisando uma imagem frame a frame.
Sua tarefa é extrair a estrutura geométrica EXATA do frame para preservação em animação.

CRÍTICO: Os valores de posição devem ser tão precisos quanto possível.
Esses dados serão usados para PRESERVAR a composição — não para inspiração criativa.

Retorne JSON puro (sem markdown, sem explicação):
{
  "frame_width": 1920,
  "frame_height": 1080,
  "horizon_y": 0.55,
  "vanishing_point_x": 0.50,
  "composition_style": "centered",
  "color_temperature": "warm",
  "depth_cues": ["perspective_lines", "size_variation"],
  "primary_subject_bbox": {"x": 0.35, "y": 0.20, "width": 0.30, "height": 0.60},
  "layers": [
    {
      "id": "layer_01",
      "label": "nome_preciso_do_objeto",
      "bbox": {"x": 0.10, "y": 0.30, "width": 0.25, "height": 0.40},
      "depth": 0.15,
      "depth_layer": 0,
      "importance": "primary"
    },
    {
      "id": "layer_02",
      "label": "nome_objeto_fundo",
      "bbox": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
      "depth": 0.90,
      "depth_layer": 2,
      "importance": "background"
    }
  ]
}

Regras obrigatórias:
- bbox: x, y, width, height são 0.0–1.0 proporcional ao frame (não pixels)
- x, y = canto superior esquerdo do elemento
- depth: 0.0=foreground extremo, 1.0=background extremo
- depth_layer: 0=foreground, 1=midground, 2=background
- composition_style: "centered" | "rule_of_thirds" | "left_heavy" | "right_heavy" | "diagonal" | "symmetrical"
- color_temperature: "warm" | "cool" | "neutral" | "mixed"
- depth_cues: lista de ["perspective_lines", "size_variation", "atmospheric_haze", "overlap", "texture_gradient"]
- Identifique no máximo 8 elementos mais visualmente importantes
- NUNCA invente elementos que não existem — apenas descreva o que está presente
- Seja geometricamente preciso — estes valores preservam a composição original"""


def _depth_to_parallax(depth: float) -> float:
    """
    Converte depth (0=foreground, 1=background) em parallax_sensitivity.
    Foreground se move mais. Background se move menos.
    Curva não-linear para efeito mais realista.
    """
    # Foreground (depth=0): parallax 0.25 (move muito)
    # Midground (depth=0.5): parallax 0.10
    # Background (depth=1.0): parallax 0.02 (quase estático)
    return 0.02 + (1 - depth) ** 1.8 * 0.23


def _depth_to_motion_allowance(depth: float) -> float:
    """Deslocamento máximo em px permitido para animações sutis."""
    return 4.0 + (1 - depth) * 16.0   # background: 4px, foreground: 20px


class CVExtractor:
    """
    Extrai SceneGraph determinístico de um frame.

    Primary path: Vision LLM com prompt JSON estrito.
    Fallback: SceneGraph mínimo com apenas o background plate.

    Futura expansão (GPU):
      def _extract_depth_map(image_b64) → depth map via Depth Anything V2
      def _extract_segments(image_b64)  → máscaras via SAM2
      def _detect_objects(image_b64)    → bboxes via YOLOv8/GroundingDINO
    """

    def __init__(self, vision_client: "AIClient"):
        self.vision_client = vision_client

    def extract(self, image_b64: str, description: str = "") -> SceneGraph:
        """
        Extrai SceneGraph completo do frame.

        Args:
            image_b64: base64 data URL do frame
            description: descrição textual opcional para contexto

        Returns:
            SceneGraph imutável com todas as camadas mapeadas
        """
        if not image_b64:
            return SceneGraph(background_plate="", layers=[])

        prompt = _EXTRACTION_PROMPT
        if description:
            prompt += f"\n\nContexto adicional: {description}"

        try:
            response = self.vision_client.complete(prompt, images=[image_b64])
            data = _parse_json_response(response)
            if data:
                return self._build_scene_graph(image_b64, data)
        except Exception:
            pass

        # Fallback: SceneGraph mínimo sem layers
        return self._fallback_scene_graph(image_b64)

    def _build_scene_graph(self, image_b64: str, data: dict) -> SceneGraph:
        """Constrói SceneGraph a partir dos dados extraídos pelo LLM."""
        layers = []
        for i, l_data in enumerate(data.get("layers", [])[:8]):
            bbox = BBox.from_dict(l_data.get("bbox", {"x": 0, "y": 0, "width": 1, "height": 1}))

            # Clamp bbox para manter dentro do frame
            bbox = BBox(
                x=max(0.0, min(0.98, bbox.x)),
                y=max(0.0, min(0.98, bbox.y)),
                width=max(0.02, min(1.0 - bbox.x, bbox.width)),
                height=max(0.02, min(1.0 - bbox.y, bbox.height)),
            )

            depth = float(l_data.get("depth", 0.5))
            depth = max(0.0, min(1.0, depth))

            layers.append(SceneLayer(
                id=l_data.get("id", f"layer_{i+1:02d}"),
                label=l_data.get("label", f"element_{i+1}"),
                bbox=bbox,
                depth=depth,
                depth_layer=int(l_data.get("depth_layer", 1)),
                parallax_sensitivity=_depth_to_parallax(depth),
                motion_allowance=_depth_to_motion_allowance(depth),
                importance=l_data.get("importance", "secondary"),
                locked=True,
            ))

        # Ordena por depth (background primeiro para z-order correto)
        layers.sort(key=lambda l: l.depth, reverse=True)

        # Primary subject bbox
        psb_data = data.get("primary_subject_bbox")
        psb = BBox.from_dict(psb_data) if psb_data else None

        return SceneGraph(
            background_plate=image_b64,
            frame_width=int(data.get("frame_width", 1920)),
            frame_height=int(data.get("frame_height", 1080)),
            layers=layers,
            horizon_y=max(0.1, min(0.9, float(data.get("horizon_y", 0.5)))),
            vanishing_point_x=max(0.1, min(0.9, float(data.get("vanishing_point_x", 0.5)))),
            composition_style=data.get("composition_style", "centered"),
            color_temperature=data.get("color_temperature", "neutral"),
            depth_cues=data.get("depth_cues", []),
            primary_subject_bbox=psb,
        )

    def _fallback_scene_graph(self, image_b64: str) -> SceneGraph:
        """SceneGraph mínimo quando a extração falha. Apenas background plate."""
        return SceneGraph(
            background_plate=image_b64,
            layers=[
                SceneLayer(
                    id="background",
                    label="full frame",
                    bbox=BBox(x=0, y=0, width=1, height=1),
                    depth=1.0,
                    depth_layer=2,
                    parallax_sensitivity=0.02,
                    motion_allowance=4.0,
                    importance="background",
                    locked=True,
                )
            ],
        )


def _parse_json_response(text: str) -> Optional[dict]:
    """Extrai JSON da resposta do LLM."""
    # Tenta extrair bloco ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # Tenta extrair JSON direto
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    return None
