"""
Delta Patcher — Aplicação localizada de feedback sem regeneração destrutiva.

PRINCÍPIO: Feedback do usuário NUNCA recria a cena inteira.
Apenas modifica os campos específicos do MotionDSL afetados.
A composição (SceneGraph) permanece INTACTA E IMUTÁVEL.

Exemplos de delta patches:
  "mais vibrante"   → atmosphere.color_grade = "boost", atmosphere.color_grade_intensity += 0.2
  "câmera mais rápida" → camera.speed += 0.2, camera.parallax += 0.03
  "mais suave"      → camera.damping += 4, camera.speed *= 0.7
  "adicionar partículas" → particles.enabled = True, particles.count += 10
  "menos glow"      → atmosphere.glow_opacity -= 0.05
"""

from __future__ import annotations
import re
from typing import Optional, TYPE_CHECKING

from motion_dsl import MotionDSL

if TYPE_CHECKING:
    from motion_planner import MotionPlanner
    from scene_graph import SceneGraph
    from visual_dna import VisualDNA


# Mapa de palavras-chave para patches determinísticos
# Ordem: mais específico → menos específico
_KEYWORD_PATCHES: list[tuple[list[str], dict]] = [
    # Câmera — velocidade
    (["mais rápido", "faster", "mais velocidade", "acelera"],
     {"camera.speed": "+0.2", "camera.parallax": "+0.02"}),
    (["mais lento", "slower", "mais devagar", "calmo"],
     {"camera.speed": "*0.6", "camera.damping": "+4"}),

    # Câmera — intensidade
    (["mais movimento", "more motion", "dinâmico"],
     {"camera.parallax": "+0.04", "camera.micro_jitter": "+0.2"}),
    (["menos movimento", "less motion", "estático", "static"],
     {"camera.parallax": "*0.5", "camera.micro_jitter": "*0.3"}),

    # Câmera — tipo
    (["dolly in", "avança", "zoom in"],
     {"camera.type": "slow_dolly_in", "camera.direction": "in"}),
    (["dolly out", "recua", "zoom out"],
     {"camera.type": "dolly_out", "camera.direction": "out"}),
    (["panorâmica", "pan", "lateral"],
     {"camera.type": "pan_right"}),
    (["parallax", "profundidade"],
     {"camera.type": "parallax", "camera.parallax": "+0.03"}),
    (["handheld", "tremido", "orgânico"],
     {"camera.type": "handheld", "camera.micro_jitter": "0.4"}),
    (["estático", "parado", "locked"],
     {"camera.type": "static", "camera.micro_jitter": "0.0"}),

    # Cor / Grade
    (["mais vibrante", "mais saturado", "vibrant", "colorido"],
     {"atmosphere.color_grade": "boost", "atmosphere.color_grade_intensity": "0.25"}),
    (["mais quente", "warm", "dourado", "sunset"],
     {"atmosphere.color_grade": "warm", "atmosphere.color_grade_intensity": "0.2"}),
    (["mais frio", "cool", "azul", "frio"],
     {"atmosphere.color_grade": "cool", "atmosphere.color_grade_intensity": "0.2"}),
    (["dessaturar", "menos cor", "cinza", "desaturate"],
     {"atmosphere.color_grade": "desaturate", "atmosphere.color_grade_intensity": "0.3"}),

    # Vinheta
    (["mais vinheta", "more vignette", "mais escuro nas bordas"],
     {"atmosphere.vignette": "+0.15"}),
    (["menos vinheta", "less vignette", "mais aberto"],
     {"atmosphere.vignette": "-0.1"}),

    # Glow
    (["mais glow", "mais brilho", "glowing"],
     {"atmosphere.glow_enabled": True, "atmosphere.glow_opacity": "+0.1"}),
    (["menos glow", "sem glow", "no glow"],
     {"atmosphere.glow_enabled": False, "atmosphere.glow_opacity": "*0.3"}),

    # Grain
    (["mais grain", "mais textura", "mais filme"],
     {"atmosphere.grain": "+0.03"}),
    (["menos grain", "limpo", "clean"],
     {"atmosphere.grain": "*0.3"}),

    # Partículas
    (["mais partículas", "more particles", "mais poeira"],
     {"particles.enabled": True, "particles.count": "+10", "particles.intensity": "+0.1"}),
    (["menos partículas", "less particles", "sem partículas", "no particles"],
     {"particles.enabled": False}),
    (["partículas", "particles", "poeira", "dust"],
     {"particles.enabled": True, "particles.count": 15, "particles.intensity": 0.15}),

    # Energia cinematic
    (["mais intenso", "impactante", "energético", "intense"],
     {"cinematic_energy": "+0.2", "camera.speed": "+0.15"}),
    (["mais suave", "tranquilo", "relaxado", "calm"],
     {"cinematic_energy": "-0.2", "camera.speed": "*0.7", "camera.damping": "+3"}),

    # Transição
    (["corte seco", "hard cut", "sem fade"],
     {"transition_in.type": "cut", "transition_out.type": "cut"}),
    (["fade negro", "fade to black"],
     {"transition_out.type": "fade_black", "transition_out.duration": 25}),
    (["mais longa transição", "longer transition"],
     {"transition_in.duration": "+10", "transition_out.duration": "+10"}),
]


class DeltaPatcher:
    """
    Aplica feedback como delta patches no MotionDSL.
    Nunca toca no SceneGraph.
    Tenta primeiro via mapa de palavras-chave determinístico.
    Fallback: MotionPlanner.plan_delta() via LLM.
    """

    def __init__(self, motion_planner: Optional["MotionPlanner"] = None):
        self.motion_planner = motion_planner

    def apply(
        self,
        feedback: str,
        existing_motion: MotionDSL,
        scene_graph: Optional["SceneGraph"] = None,
        dna: Optional["VisualDNA"] = None,
    ) -> MotionDSL:
        """
        Aplica feedback como delta patch no MotionDSL existente.

        1. Tenta mapa determinístico de palavras-chave
        2. Se não encontrar match suficiente → LLM delta via MotionPlanner
        3. Sempre preserva SceneGraph intacto
        """
        if not feedback.strip():
            return existing_motion

        feedback_lower = feedback.lower()

        # Coleta patches que fazem match com o feedback
        merged_delta = {}
        matched_any = False

        for keywords, patch in _KEYWORD_PATCHES:
            if any(kw in feedback_lower for kw in keywords):
                merged_delta.update(patch)
                matched_any = True

        if matched_any:
            return _apply_delta(existing_motion, merged_delta)

        # Fallback: LLM delta se MotionPlanner disponível
        if self.motion_planner and scene_graph:
            try:
                return self.motion_planner.plan_delta(existing_motion, feedback, scene_graph, dna)
            except Exception:
                pass

        return existing_motion


def _apply_delta(motion: MotionDSL, delta: dict) -> MotionDSL:
    """
    Aplica delta com suporte a operadores: "+", "*", "=" (default).
    Exemplo: {"camera.speed": "+0.2"} adiciona 0.2 ao valor atual.
    """
    import copy
    import json

    current = motion.to_dict()

    for path, value in delta.items():
        keys = path.split(".")
        obj = current
        for k in keys[:-1]:
            if k not in obj:
                obj[k] = {}
            obj = obj[k]

        last_key = keys[-1]
        current_val = obj.get(last_key)

        if isinstance(value, str) and current_val is not None:
            if value.startswith("+") and isinstance(current_val, (int, float)):
                obj[last_key] = round(current_val + float(value[1:]), 4)
            elif value.startswith("*") and isinstance(current_val, (int, float)):
                obj[last_key] = round(current_val * float(value[1:]), 4)
            else:
                try:
                    obj[last_key] = float(value)
                except ValueError:
                    obj[last_key] = value
        else:
            obj[last_key] = value

    return MotionDSL.from_dict(current)
