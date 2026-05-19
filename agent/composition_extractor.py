"""
Composition Extractor — extrai constraints de composição de frames de referência.

O objetivo é transformar o frame em VERDADE IMUTÁVEL:
  - geometria
  - posicionamento
  - layout espacial
  - arquitetura da cena

O agente DSL SOMENTE adiciona movimento sobre essa base.
NÃO redesenha, NÃO recompõe, NÃO inventa.
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_client import AIClient


@dataclass
class LockedElement:
    """Um elemento identificado no frame que deve ser preservado exatamente."""
    id: str
    label: str           # nome descritivo ("product_box", "person_left", "logo_top")
    x: float             # centro x normalizado (0–1)
    y: float             # centro y normalizado (0–1)
    width: float         # largura normalizada (0–1)
    height: float        # altura normalizada (0–1)
    depth_layer: int     # 0=foreground, 1=midground, 2=background
    importance: str      # "primary" | "secondary" | "background"


@dataclass
class CompositionConstraints:
    """
    Constraints extraídos do frame de referência.
    Representa a verdade geométrica da cena — não pode ser alterada.
    Injetada no prompt do DSL generator para forçar preservação.
    """
    horizon_y: float = 0.5           # linha do horizonte (0–1)
    depth_layers: int = 3
    primary_subject_x: float = 0.5
    primary_subject_y: float = 0.5
    composition_style: str = "centered"
    color_temperature: str = "neutral"
    depth_cues: List[str] = field(default_factory=list)
    locked_elements: List[LockedElement] = field(default_factory=list)

    def to_prompt_section(self) -> str:
        """
        Serializa para injeção no prompt do DSL generator.
        Transmite as constraints com instruções explícitas de preservação.
        """
        lines = [
            "╔══════════════════════════════════════════════════════╗",
            "║   LOCKED REFERENCE MODE — COMPOSIÇÃO IMUTÁVEL        ║",
            "╚══════════════════════════════════════════════════════╝",
            "",
            "A imagem de referência é VERDADE ABSOLUTA.",
            "Você é um MOTION OPERATOR — não um artista criativo.",
            "Seu trabalho é ANIMAR a referência, não RECRIAR.",
            "",
            f"  Linha do horizonte: y={self.horizon_y:.2f}",
            f"  Sujeito principal: ({self.primary_subject_x:.2f}, {self.primary_subject_y:.2f})",
            f"  Estilo compositivo: {self.composition_style}",
            f"  Temperatura de cor: {self.color_temperature}",
            f"  Camadas de profundidade: {self.depth_layers}",
        ]

        if self.depth_cues:
            lines.append(f"  Indicadores de profundidade: {', '.join(self.depth_cues)}")

        if self.locked_elements:
            lines.append("")
            lines.append("  ELEMENTOS BLOQUEADOS (posições exatas, não altere):")
            for el in self.locked_elements[:8]:
                depth_label = ["FOREGROUND", "MIDGROUND", "BACKGROUND"][min(el.depth_layer, 2)]
                lines.append(
                    f"    [{depth_label}] \"{el.label}\": "
                    f"center=({el.x:.2f}, {el.y:.2f}) "
                    f"size=({el.width:.2f}×{el.height:.2f}) "
                    f"[{el.importance}]"
                )

        lines += [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "❌ PROIBIDO:",
            "   - Redesenhar o ambiente ou arquitetura",
            "   - Alterar posição ou escala de qualquer objeto",
            "   - Inventar elementos que não existem no frame",
            "   - Mudar composição, framing ou proporções",
            "   - Reinterpretar artisticamente",
            "",
            "✅ PERMITIDO (somente):",
            "   - Animar câmera: parallax, dolly, zoom sutil",
            "   - Criar profundidade: layers com velocidades diferentes",
            "   - Adicionar motion sutil: luz pulsando, partículas, névoa",
            "   - Timing e easing das transições",
            "   - Color grading dinâmico sobre a composição existente",
            "",
            "⚠  O background_plate JÁ está inserido como image_element.",
            "   Não adicione shapes de fundo — a imagem original é o fundo.",
            "   Adicione APENAS text_elements e particle_fields sobre ela.",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        return "\n".join(lines)


class CompositionExtractor:
    """
    Extrai CompositionConstraints de uma imagem via vision LLM.
    Fallback textual quando o modelo não suporta visão.
    """

    def __init__(self, vision_client: "AIClient"):
        self.vision_client = vision_client

    def extract(self, image_b64: str) -> CompositionConstraints:
        """Extrai constraints de composição da imagem."""
        if not image_b64:
            return CompositionConstraints()

        prompt = """Você é um analista de composição cinematográfica e motion design.
Analise esta imagem e mapeie a estrutura compositiva com precisão.
O objetivo é preservar EXATAMENTE essa composição na animação — não alterar nada.

Responda com JSON puro (sem markdown, sem explicação):
{
  "horizon_y": 0.55,
  "primary_subject_x": 0.50,
  "primary_subject_y": 0.45,
  "composition_style": "centered",
  "depth_layers": 3,
  "color_temperature": "warm",
  "depth_cues": ["perspective_lines", "size_variation"],
  "locked_elements": [
    {
      "id": "el_01",
      "label": "nome_descritivo_objeto",
      "x": 0.50,
      "y": 0.60,
      "width": 0.35,
      "height": 0.40,
      "depth_layer": 1,
      "importance": "primary"
    }
  ]
}

Regras:
- Todos os valores de posição/tamanho são proporção normalizada (0.0 a 1.0)
- x, y = centro do elemento; width, height = tamanho
- depth_layer: 0=foreground, 1=midground, 2=background
- composition_style: "centered" | "rule_of_thirds" | "left_heavy" | "right_heavy" | "diagonal"
- color_temperature: "warm" | "cool" | "neutral"
- depth_cues possíveis: "perspective_lines", "size_variation", "atmospheric_haze", "overlap", "texture_gradient"
- Identifique no máximo 6 elementos mais importantes
- Seja preciso — esses valores serão usados para preservar a composição original"""

        try:
            response = self.vision_client.complete(prompt, images=[image_b64])
            m = re.search(r"\{.*\}", response, re.DOTALL)
            if not m:
                return CompositionConstraints()

            data = json.loads(m.group(0))

            constraints = CompositionConstraints(
                horizon_y=float(data.get("horizon_y", 0.5)),
                depth_layers=int(data.get("depth_layers", 3)),
                primary_subject_x=float(data.get("primary_subject_x", 0.5)),
                primary_subject_y=float(data.get("primary_subject_y", 0.5)),
                composition_style=data.get("composition_style", "centered"),
                color_temperature=data.get("color_temperature", "neutral"),
                depth_cues=data.get("depth_cues", []),
            )

            for el_data in data.get("locked_elements", [])[:8]:
                constraints.locked_elements.append(LockedElement(
                    id=el_data.get("id", f"el_{len(constraints.locked_elements):02d}"),
                    label=el_data.get("label", "element"),
                    x=float(el_data.get("x", 0.5)),
                    y=float(el_data.get("y", 0.5)),
                    width=float(el_data.get("width", 0.2)),
                    height=float(el_data.get("height", 0.2)),
                    depth_layer=int(el_data.get("depth_layer", 1)),
                    importance=el_data.get("importance", "secondary"),
                ))

            return constraints

        except Exception:
            return CompositionConstraints()

    def extract_fallback(self) -> CompositionConstraints:
        """Constraints genéricos quando não há imagem ou falha a extração."""
        return CompositionConstraints(
            horizon_y=0.5,
            primary_subject_x=0.5,
            primary_subject_y=0.5,
            composition_style="centered",
        )
