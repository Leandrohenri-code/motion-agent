"""
Creative Director Agent.

Responsável por:
- Interpretar o brief do usuário
- Definir o conceito criativo global
- Traduzir intenção artística em parâmetros DSL
- Manter a visão cinematográfica coerente
"""

from __future__ import annotations
import json
import re
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_client import AIClient
    from visual_dna import VisualDNA


CREATIVE_DIRECTOR_SYSTEM = """Você é um Creative Director de elite especializado em motion design cinematográfico premium.
Sua expertise: Apple, Nike, luxury brands, titles de filmes, vídeos de produto de alto impacto.
Você pensa em termos de conceito, emoção e impacto visual — não código.
Seja preciso, artístico e decisivo. Nunca seja genérico."""


class CreativeDirector:
    """
    Agente diretor criativo. Define conceito e direção para cada cena.
    """

    def __init__(self, client: "AIClient"):
        self.client = client

    def interpret_brief(
        self,
        frames: List[dict],
        style_prompt: str,
        dna: "VisualDNA",
    ) -> dict:
        """
        Analisa o brief completo e retorna direção criativa global.

        Returns:
            {
                "concept": str,
                "narrative_arc": [str, ...],   # arco narrativo cena a cena
                "emotional_journey": str,
                "pacing_notes": str,
                "key_transitions": [str, ...]
            }
        """
        scene_briefs = "\n".join(
            f"  Cena {i+1}: {f.get('description', '(sem descrição)')[:100]}"
            for i, f in enumerate(frames)
        )

        prompt = f"""BRIEF DO PROJETO:
{style_prompt}

CENAS ({len(frames)} no total):
{scene_briefs}

IDENTIDADE VISUAL DEFINIDA:
Mood: {dna.cinematic_mood} | Motion: {dna.motion_signature} | Camera: {dna.camera_language}
Lighting: {dna.lighting_style} | Typography: {dna.typography_style}

Como Creative Director, defina:
1. O conceito criativo central (1-2 frases)
2. O arco narrativo (1 frase por cena)
3. A jornada emocional (do início ao fim)
4. Notas de ritmo e pacing
5. Estilo de transição entre cenas

Responda com JSON válido (sem markdown):
{{
  "concept": "string",
  "narrative_arc": ["cena 1: ...", "cena 2: ..."],
  "emotional_journey": "string descrevendo a emoção ao longo do vídeo",
  "pacing_notes": "string sobre ritmo, velocidade, intensidade",
  "key_transitions": ["entre cena 1→2: ...", "entre cena 2→3: ..."],
  "cinematography_notes": "string sobre linguagem de câmera predominante"
}}"""

        try:
            response = self.client.complete(prompt)
            json_str = _extract_json(response)
            return json.loads(json_str)
        except Exception:
            # Fallback estruturado
            return {
                "concept": f"Motion design {dna.cinematic_mood} com {dna.motion_signature}",
                "narrative_arc": [f.get("description", f"Cena {i+1}")[:60] for i, f in enumerate(frames)],
                "emotional_journey": f"Do impacto inicial ao desfecho {dna.cinematic_mood}",
                "pacing_notes": "Ritmo comercial: abertura de impacto, desenvolvimento fluido, fechamento memorável",
                "key_transitions": [dna.transition_signature] * max(0, len(frames) - 1),
                "cinematography_notes": dna.camera_language,
            }

    def get_scene_direction(
        self,
        scene_num: int,
        frame: dict,
        creative_brief: dict,
        dna: "VisualDNA",
    ) -> str:
        """
        Retorna direção criativa específica para uma cena.
        Injetada no prompt do DSL Generator.
        """
        arc = creative_brief.get("narrative_arc", [])
        scene_arc = arc[scene_num - 1] if scene_num - 1 < len(arc) else ""
        concept = creative_brief.get("concept", "")
        mood = dna.cinematic_mood
        motion = dna.motion_signature

        return f"""
=== DIREÇÃO CRIATIVA — CENA {scene_num} ===
Conceito global: {concept}
Arco desta cena: {scene_arc}
Mood: {mood} | Motion signature: {motion}
Câmera: {dna.camera_language} | Iluminação: {dna.lighting_style}
Pacing: {creative_brief.get('pacing_notes', '')}
""".strip()

    def suggest_camera_for_scene(
        self,
        scene_num: int,
        total_scenes: int,
        previous_cameras: List[str],
        dna: "VisualDNA",
    ) -> str:
        """
        Sugere o tipo de movimento de câmera para evitar repetição.
        """
        all_motions = ["dolly_in", "dolly_out", "pan_right", "pan_left",
                       "zoom", "float", "parallax", "orbit", "shake", "static"]

        # Câmeras usadas recentemente (evitar)
        recent = set(previous_cameras[-3:]) if previous_cameras else set()

        # Câmeras apropriadas para o estilo
        style_map = {
            "luxury_archviz": ["dolly_in", "parallax", "float", "orbit"],
            "commercial_clean": ["dolly_in", "zoom", "pan_right", "parallax"],
            "editorial": ["pan_right", "shake", "zoom", "pan_left"],
            "documentary": ["pan_right", "pan_left", "static", "float"],
        }
        candidates = style_map.get(dna.camera_language, all_motions)

        # Primeiro/último plano
        if scene_num == 1:
            preferred = ["dolly_in", "zoom", "parallax"]
        elif scene_num == total_scenes:
            preferred = ["dolly_out", "float", "parallax"]
        else:
            preferred = candidates

        # Filtra recentes
        available = [c for c in preferred if c not in recent]
        if not available:
            available = [c for c in candidates if c not in recent]
        if not available:
            available = candidates

        return available[0]


def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return m.group(1)
    return text.strip()
