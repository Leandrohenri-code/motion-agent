"""
Motion Planner — O LLM como Motion Operator.

RESPONSABILIDADE ÚNICA: Planeja movimento, câmera e atmosfera.
NÃO POSSUI AUTORIDADE VISUAL.

O LLM recebe:
  - SceneGraph (descrição textual — NÃO o base64)
  - Visual DNA
  - Creative Brief
  - Temporal Memory (movimentos anteriores)
  - Description / Style Prompt

O LLM retorna SOMENTE MotionDSL JSON.
Não retorna composição, não retorna objetos, não retorna layout.
"""

from __future__ import annotations
import json
import re
from typing import Optional, TYPE_CHECKING

from motion_dsl import (
    MotionDSL, CameraPhysics, LayerAnimation,
    ParticleConfig, AtmosphereConfig, TransitionConfig, TextOverlay
)

if TYPE_CHECKING:
    from ai_client import AIClient
    from visual_dna import VisualDNA
    from temporal_memory import TemporalMemory
    from scene_graph import SceneGraph


# System prompt — redefine o papel do LLM radicalmente
MOTION_OPERATOR_SYSTEM = """You are a MOTION OPERATOR — not an artist, not a director of photography.
You receive a scene that is ALREADY COMPOSED by computer vision.
Your ONLY job is to plan the motion.

You CANNOT:
- redesign the environment
- alter architecture
- reposition objects
- change framing
- invent elements
- create new composition
- replace objects
- modify layout
- add image_elements
- add shape_elements
- add background elements
- modify geometry

You MUST preserve:
- exact geometry (defined by SceneGraph)
- exact framing (defined by SceneGraph)
- exact object positions (locked=true)
- exact composition (locked=true)

You are ONLY responsible for:
- camera motion type and physics
- layer parallax per SceneGraph layer
- atmospheric effects (vignette, grain, glow)
- particle system (if appropriate)
- text overlays (ONLY if concept requires)
- transition in/out timing
- cinematic pacing and energy

Output ONLY MotionDSL JSON. Never output anything else."""


# Schema de referência do MotionDSL para o prompt
_MOTION_DSL_SCHEMA = """
MOTION DSL SCHEMA (output this exact structure):
{
  "scene_id": 1,
  "duration": 90,
  "fps": 30,
  "description": "brief motion description",
  "camera": {
    "type": "slow_dolly_in",
    "speed": 0.25,
    "easing": "easeInOut",
    "parallax": 0.08,
    "inertia": 1.0,
    "velocity": 0.3,
    "acceleration": 0.1,
    "damping": 14.0,
    "stiffness": 120.0,
    "micro_jitter": 0.0,
    "direction": "in"
  },
  "layer_animations": [
    {
      "target": "layer_id_from_scene_graph",
      "animation": "subtle_sway",
      "intensity": 0.05,
      "speed": 1.0,
      "delay": 0
    }
  ],
  "particles": {
    "enabled": false,
    "type": "dust",
    "count": 15,
    "intensity": 0.15,
    "color": "#ffffff",
    "opacity": 0.3,
    "size_min": 1.0,
    "size_max": 3.0
  },
  "atmosphere": {
    "vignette": 0.3,
    "grain": 0.02,
    "glow_enabled": false,
    "glow_color": "#hex",
    "glow_opacity": 0.15,
    "glow_x": 50.0,
    "glow_y": 40.0,
    "glow_size": 60.0,
    "color_grade": "none",
    "color_grade_intensity": 0.0
  },
  "transition_in": {"type": "fade", "duration": 20},
  "transition_out": {"type": "fade", "duration": 20},
  "text_overlays": [],
  "cinematic_energy": 0.5,
  "pacing_note": "slow cinematic build",
  "agent_notes": "rationale"
}

camera.type options: static | slow_dolly_in | dolly_out | pan_right | pan_left | parallax | float | handheld | push_in | pull_back
layer animation options: none | subtle_sway | drift | pulse | breathe
color_grade options: none | warm | cool | desaturate | boost
transition types: fade | fade_black | cut | dissolve | wipe"""


class MotionPlanner:
    """
    Planeja movimento puro via LLM.
    O LLM recebe SceneGraph como descrição textual (sem imagem).
    Output: MotionDSL JSON estrito.
    """

    def __init__(self, client: "AIClient"):
        self.client = client

    def plan(
        self,
        scene_num: int,
        total_scenes: int,
        frame: dict,
        scene_graph: "SceneGraph",
        dna: "VisualDNA",
        memory: "TemporalMemory",
        creative_brief: dict,
        fps: int = 30,
        feedback: str = "",
    ) -> MotionDSL:
        """
        Planeja o MotionDSL para uma cena.

        Args:
            scene_graph: SceneGraph imutável extraído do frame
            feedback:    Feedback do usuário para regeneração delta

        Returns:
            MotionDSL com metadata de movimento puro
        """
        duration_frames = int(float(frame.get("duration", 3)) * fps)
        description = frame.get("description", "")
        is_first = scene_num == 1
        is_last = scene_num == total_scenes

        orig_system = self.client.system_prompt
        self.client.system_prompt = MOTION_OPERATOR_SYSTEM

        try:
            prompt = self._build_prompt(
                scene_num=scene_num,
                total_scenes=total_scenes,
                description=description,
                duration_frames=duration_frames,
                fps=fps,
                scene_graph=scene_graph,
                dna=dna,
                memory=memory,
                creative_brief=creative_brief,
                is_first=is_first,
                is_last=is_last,
                feedback=feedback,
            )

            # Motion planner NUNCA recebe imagem — usa SceneGraph textual
            # Isso previne que o LLM "reinterprete" visualmente a cena
            raw = self.client.complete(prompt, images=None)
            data = _parse_json(raw)

            if data:
                data["scene_id"] = scene_num
                data["duration"] = duration_frames
                data["fps"] = fps
                return MotionDSL.from_dict(data)

        except Exception:
            pass
        finally:
            self.client.system_prompt = orig_system

        return self._fallback_motion(scene_num, duration_frames, fps, dna, is_first, is_last)

    def plan_delta(
        self,
        existing_motion: MotionDSL,
        feedback: str,
        scene_graph: "SceneGraph",
        dna: "VisualDNA",
    ) -> MotionDSL:
        """
        Gera um delta patch baseado em feedback.
        NÃO regenera o MotionDSL do zero.
        Apenas modifica os campos afetados.
        """
        orig_system = self.client.system_prompt
        self.client.system_prompt = MOTION_OPERATOR_SYSTEM

        try:
            prompt = f"""The user gave feedback: "{feedback}"

Current Motion DSL:
{json.dumps(existing_motion.to_dict(), indent=2)}

Scene Graph (immutable, DO NOT suggest changes to composition):
{scene_graph.to_prompt_description()}

Generate ONLY a delta patch — a JSON object with the specific fields to update.
Use dot notation for nested fields (e.g. "camera.speed", "atmosphere.vignette").
Format:
{{
  "camera.speed": 0.4,
  "atmosphere.vignette": 0.5,
  "particles.enabled": true
}}

Rules:
- ONLY modify motion, camera, atmosphere, particles, timing
- NEVER suggest changes to composition or objects
- NEVER add image_elements or shape_elements
- Output ONLY the delta JSON, nothing else"""

            raw = self.client.complete(prompt, images=None)
            data = _parse_json(raw)

            if data and isinstance(data, dict):
                return existing_motion.apply_delta(data)

        except Exception:
            pass
        finally:
            self.client.system_prompt = orig_system

        return existing_motion

    def _build_prompt(
        self,
        scene_num: int,
        total_scenes: int,
        description: str,
        duration_frames: int,
        fps: int,
        scene_graph: "SceneGraph",
        dna: "VisualDNA",
        memory: "TemporalMemory",
        creative_brief: dict,
        is_first: bool,
        is_last: bool,
        feedback: str = "",
    ) -> str:
        parts = []

        # SceneGraph — verdade geométrica
        parts.append(scene_graph.to_prompt_description())
        parts.append("")

        # Memória temporal — para continuidade de câmera
        parts.append(memory.to_prompt_section())
        parts.append("")

        # DNA — para consistência visual de movimento
        if hasattr(dna, 'to_motion_prompt'):
            parts.append(dna.to_motion_prompt())
        else:
            parts.append(f"Motion signature: {getattr(dna, 'motion_signature', 'spring_organic')}")
            parts.append(f"Camera language: {getattr(dna, 'camera_language', 'cinematic')}")
            parts.append(f"Spring: damping={getattr(dna, 'spring_damping', 14)}, stiffness={getattr(dna, 'spring_stiffness', 120)}")
        parts.append("")

        # Brief criativo
        concept = creative_brief.get("concept", "")
        if concept:
            parts.append(f"Concept: {concept[:120]}")
            pacing = creative_brief.get("pacing_notes", "")
            if pacing:
                parts.append(f"Pacing: {pacing[:80]}")
            parts.append("")

        # Instrução principal
        parts.append(f"=== PLAN MOTION — SCENE {scene_num}/{total_scenes} ===")
        parts.append(f"Description: {description or '(no description)'}")
        parts.append(f"Duration: {duration_frames} frames ({duration_frames/fps:.1f}s) @ {fps}fps")

        if is_first:
            parts.append("FIRST SCENE: Opening impact. transition_in = null or very fast.")
        elif is_last:
            parts.append("LAST SCENE: Memorable close. Strong transition_out.")

        if feedback:
            parts.append(f"\nUser feedback (apply to motion only): {feedback}")

        parts.append("")
        parts.append("Generate MotionDSL JSON — motion metadata ONLY.")
        parts.append("The SceneGraph above defines the composition. You animate it, not recreate it.")
        parts.append("Output pure JSON, no markdown, no explanations.")
        parts.append("")
        parts.append(_MOTION_DSL_SCHEMA)

        return "\n".join(parts)

    def _fallback_motion(
        self,
        scene_num: int,
        duration_frames: int,
        fps: int,
        dna: "VisualDNA",
        is_first: bool,
        is_last: bool,
    ) -> MotionDSL:
        """MotionDSL de fallback quando o LLM falha."""
        damping = getattr(dna, 'spring_damping', 14.0)
        stiffness = getattr(dna, 'spring_stiffness', 120.0)

        camera_types = ["slow_dolly_in", "parallax", "float", "push_in", "static"]
        cam_type = camera_types[(scene_num - 1) % len(camera_types)]

        return MotionDSL(
            scene_id=scene_num,
            duration=duration_frames,
            fps=fps,
            description=f"Scene {scene_num} fallback motion",
            camera=CameraPhysics(
                type=cam_type,
                speed=0.2,
                parallax=0.08,
                damping=damping,
                stiffness=stiffness,
                micro_jitter=0.3 if cam_type == "handheld" else 0.0,
            ),
            particles=ParticleConfig(enabled=False),
            atmosphere=AtmosphereConfig(vignette=0.3, grain=0.02),
            transition_in=TransitionConfig(type="fade", duration=20) if not is_first else None,
            transition_out=TransitionConfig(type="fade_black", duration=20) if is_last else TransitionConfig(type="fade", duration=15),
            cinematic_energy=0.5,
        )


def _parse_json(text: str) -> Optional[dict]:
    """Extrai JSON da resposta do LLM."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return None
