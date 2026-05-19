"""
Scene Planner Agent.

Responsável por:
- Decompor cada frame em elementos visuais estruturados
- Definir hierarquia de elementos (z-index, timing)
- Planejar o layout antes de gerar o DSL
- Calcular timings de entrada/saída com base na duração
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_client import AIClient
    from visual_dna import VisualDNA


@dataclass
class ElementPlan:
    """Plano de um elemento antes de gerar o DSL completo."""
    element_type: str          # text, image, shape, particle
    role: str                  # headline, subheading, background, accent, particle_field
    content: str               # texto ou path da imagem
    start_frame: int
    duration_frames: int
    position: str              # "center", "top-left", "bottom-right", etc.
    z_index: int               # 0 = fundo, 10 = topo
    animation_style: str       # "dramatic_enter", "subtle_float", "kinetic", "reveal"
    notes: str = ""


@dataclass
class ScenePlan:
    """Plano completo de uma cena antes da geração DSL."""
    scene_num: int
    description: str
    duration_frames: int
    fps: int

    elements: List[ElementPlan] = field(default_factory=list)
    camera_motion: str = "static"
    environment_notes: str = ""
    audio_sync_notes: str = ""

    def to_prompt_section(self) -> str:
        lines = [f"=== PLANO DE CENA {self.scene_num} ==="]
        lines.append(f"Duração: {self.duration_frames} frames ({self.duration_frames/self.fps:.1f}s)")
        lines.append(f"Câmera: {self.camera_motion}")
        lines.append(f"Ambiente: {self.environment_notes}")
        lines.append("Elementos:")
        for i, el in enumerate(self.elements, 1):
            lines.append(
                f"  [{i}] {el.element_type.upper()} — {el.role} | '{el.content[:40]}' | "
                f"z:{el.z_index} | pos:{el.position} | "
                f"frames:{el.start_frame}-{el.start_frame+el.duration_frames} | "
                f"anim:{el.animation_style}"
            )
        return "\n".join(lines)


class ScenePlanner:
    """
    Planeja a estrutura visual de cada cena antes da geração DSL.
    """

    def __init__(self, client: "AIClient"):
        self.client = client

    def plan_scene(
        self,
        scene_num: int,
        frame: dict,
        dna: "VisualDNA",
        camera_motion: str = "parallax",
        fps: int = 30,
        creative_direction: str = "",
    ) -> ScenePlan:
        """
        Planeja os elementos e layout de uma cena.
        """
        duration_sec = float(frame.get("duration", 3))
        duration_frames = int(duration_sec * fps)
        description = frame.get("description", "")

        prompt = f"""Você é um Scene Planner de motion design.
Planeje os elementos visuais desta cena:

Descrição: {description}
Duração: {duration_frames} frames ({duration_sec:.1f}s) @ {fps}fps
Câmera: {camera_motion}
Mood: {dna.cinematic_mood} | Style: {dna.typography_style}
{creative_direction}

Regras de timing:
- Entrada dos elementos: frames 0 a 30
- Zone de atenção principal: frames 15 a {duration_frames - 25}
- Saída: últimos 20 frames

Defina os elementos necessários. Responda com JSON (sem markdown):
{{
  "elements": [
    {{
      "element_type": "shape|text|image|particle",
      "role": "background|headline|subheading|body|accent|particle_field",
      "content": "texto ou descrição visual",
      "start_frame": 0,
      "duration_frames": {duration_frames},
      "position": "center|top-left|bottom-right|lower-third|full",
      "z_index": 0,
      "animation_style": "dramatic_enter|subtle_float|kinetic|reveal|word_stagger",
      "notes": "notas para o DSL Generator"
    }}
  ],
  "environment_notes": "notas sobre background, glow, vignette",
  "camera_motion": "{camera_motion}"
}}

Inclua: 1 background (shape), 1-2 textos principais, opcionalmente particles ou shapes de acento."""

        try:
            response = self.client.complete(prompt)
            json_str = _extract_json(response)
            data = json.loads(json_str)

            plan = ScenePlan(
                scene_num=scene_num,
                description=description,
                duration_frames=duration_frames,
                fps=fps,
                camera_motion=data.get("camera_motion", camera_motion),
                environment_notes=data.get("environment_notes", ""),
            )

            for el_data in data.get("elements", []):
                plan.elements.append(ElementPlan(
                    element_type=el_data.get("element_type", "text"),
                    role=el_data.get("role", "body"),
                    content=el_data.get("content", ""),
                    start_frame=int(el_data.get("start_frame", 0)),
                    duration_frames=int(el_data.get("duration_frames", duration_frames)),
                    position=el_data.get("position", "center"),
                    z_index=int(el_data.get("z_index", 1)),
                    animation_style=el_data.get("animation_style", "dramatic_enter"),
                    notes=el_data.get("notes", ""),
                ))

            return plan

        except Exception:
            return self._fallback_plan(scene_num, frame, duration_frames, fps, camera_motion, dna)

    def _fallback_plan(
        self,
        scene_num: int,
        frame: dict,
        duration_frames: int,
        fps: int,
        camera_motion: str,
        dna: "VisualDNA",
    ) -> ScenePlan:
        description = frame.get("description", f"Cena {scene_num}")
        words = description.split()
        headline = " ".join(words[:4]).upper() if words else f"CENA {scene_num}"

        plan = ScenePlan(
            scene_num=scene_num,
            description=description,
            duration_frames=duration_frames,
            fps=fps,
            camera_motion=camera_motion,
            environment_notes=f"Background {dna.background_color}, glow sutil",
        )

        plan.elements = [
            ElementPlan(
                element_type="shape",
                role="background",
                content=f"gradient {dna.background_color}",
                start_frame=0,
                duration_frames=duration_frames,
                position="full",
                z_index=0,
                animation_style="static",
            ),
            ElementPlan(
                element_type="text",
                role="headline",
                content=headline,
                start_frame=0,
                duration_frames=duration_frames,
                position="center",
                z_index=5,
                animation_style="dramatic_enter",
            ),
        ]

        if len(words) > 4:
            sub = " ".join(words[4:8])
            plan.elements.append(ElementPlan(
                element_type="text",
                role="subheading",
                content=sub,
                start_frame=15,
                duration_frames=duration_frames - 15,
                position="center",
                z_index=4,
                animation_style="reveal",
            ))

        return plan


def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return m.group(1)
    return text.strip()
