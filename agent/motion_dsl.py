"""
Motion DSL — Metadados de movimento puro.

O LLM SOMENTE gera este DSL.
O LLM NÃO possui autoridade sobre:
  - composição
  - geometria
  - objetos
  - layout

Este DSL controla SOMENTE:
  - movimento de câmera
  - parallax por camada
  - timing cinematic
  - pacing
  - atmosfera
  - partículas
  - transições
  - text overlays mínimos (se existiam no frame)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
import json


@dataclass
class CameraPhysics:
    """
    Parâmetros físicos do movimento de câmera.
    Spring physics para comportamento cinematográfico realista.
    """
    type: str = "slow_dolly_in"
    # tipos: static, slow_dolly_in, dolly_out, pan_right, pan_left,
    #        parallax, float, orbit, handheld, push_in, pull_back

    speed: float = 0.25            # 0.05 (ultra slow) – 1.0 (fast)
    easing: str = "easeInOut"      # spring | easeInOut | easeOut | linear
    parallax: float = 0.08         # intensidade do parallax (0–0.3)
    inertia: float = 1.0           # massa da câmera (spring mass)
    velocity: float = 0.3          # velocidade inicial
    acceleration: float = 0.1      # aceleração inicial
    damping: float = 14.0          # spring damping (10=bouncy, 20=overdamped)
    stiffness: float = 120.0       # spring stiffness
    micro_jitter: float = 0.0      # handheld jitter (0=none, 0.5=subtle, 1=strong)
    tilt: float = 0.0              # inclinação da câmera (-1 a 1)
    direction: str = "none"        # in | out | left | right | up | down | none

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "speed": self.speed,
            "easing": self.easing,
            "parallax": self.parallax,
            "inertia": self.inertia,
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "damping": self.damping,
            "stiffness": self.stiffness,
            "micro_jitter": self.micro_jitter,
            "tilt": self.tilt,
            "direction": self.direction,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CameraPhysics":
        if not d:
            return cls()
        return cls(
            type=d.get("type", "static"),
            speed=float(d.get("speed", 0.25)),
            easing=d.get("easing", "easeInOut"),
            parallax=float(d.get("parallax", 0.08)),
            inertia=float(d.get("inertia", 1.0)),
            velocity=float(d.get("velocity", 0.3)),
            acceleration=float(d.get("acceleration", 0.1)),
            damping=float(d.get("damping", 14.0)),
            stiffness=float(d.get("stiffness", 120.0)),
            micro_jitter=float(d.get("micro_jitter", 0.0)),
            tilt=float(d.get("tilt", 0.0)),
            direction=d.get("direction", "none"),
        )


@dataclass
class LayerAnimation:
    """Animação aplicada a uma camada do SceneGraph pelo seu ID."""
    target: str                    # id do SceneLayer (deve existir no SceneGraph)
    animation: str = "none"        # subtle_sway | drift | pulse | breathe | none
    intensity: float = 0.05        # 0–1
    speed: float = 1.0             # multiplicador de velocidade
    delay: int = 0                 # delay em frames antes de iniciar

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "animation": self.animation,
            "intensity": self.intensity,
            "speed": self.speed,
            "delay": self.delay,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LayerAnimation":
        return cls(
            target=d.get("target", ""),
            animation=d.get("animation", "none"),
            intensity=float(d.get("intensity", 0.05)),
            speed=float(d.get("speed", 1.0)),
            delay=int(d.get("delay", 0)),
        )


@dataclass
class ParticleConfig:
    enabled: bool = False
    type: str = "dust"             # dust | sparkle | smoke | rain | snow
    count: int = 15
    intensity: float = 0.15        # 0–1
    color: str = "#ffffff"
    opacity: float = 0.3
    size_min: float = 1.0
    size_max: float = 3.0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "type": self.type,
            "count": self.count,
            "intensity": self.intensity,
            "color": self.color,
            "opacity": self.opacity,
            "size_min": self.size_min,
            "size_max": self.size_max,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ParticleConfig":
        if not d:
            return cls()
        return cls(
            enabled=bool(d.get("enabled", False)),
            type=d.get("type", "dust"),
            count=int(d.get("count", 15)),
            intensity=float(d.get("intensity", 0.15)),
            color=d.get("color", "#ffffff"),
            opacity=float(d.get("opacity", 0.3)),
            size_min=float(d.get("size_min", 1.0)),
            size_max=float(d.get("size_max", 3.0)),
        )


@dataclass
class AtmosphereConfig:
    vignette: float = 0.3          # 0–1
    grain: float = 0.02            # 0–1
    glow_enabled: bool = False
    glow_color: str = "#ffffff"
    glow_opacity: float = 0.15
    glow_x: float = 50.0           # %
    glow_y: float = 40.0           # %
    glow_size: float = 60.0        # %
    color_grade: str = "none"      # none | warm | cool | desaturate | boost
    color_grade_intensity: float = 0.0

    def to_dict(self) -> dict:
        return {
            "vignette": self.vignette,
            "grain": self.grain,
            "glow_enabled": self.glow_enabled,
            "glow_color": self.glow_color,
            "glow_opacity": self.glow_opacity,
            "glow_x": self.glow_x,
            "glow_y": self.glow_y,
            "glow_size": self.glow_size,
            "color_grade": self.color_grade,
            "color_grade_intensity": self.color_grade_intensity,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AtmosphereConfig":
        if not d:
            return cls()
        return cls(
            vignette=float(d.get("vignette", 0.3)),
            grain=float(d.get("grain", 0.02)),
            glow_enabled=bool(d.get("glow_enabled", False)),
            glow_color=d.get("glow_color", "#ffffff"),
            glow_opacity=float(d.get("glow_opacity", 0.15)),
            glow_x=float(d.get("glow_x", 50)),
            glow_y=float(d.get("glow_y", 40)),
            glow_size=float(d.get("glow_size", 60)),
            color_grade=d.get("color_grade", "none"),
            color_grade_intensity=float(d.get("color_grade_intensity", 0.0)),
        )


@dataclass
class TransitionConfig:
    type: str = "fade"             # fade | fade_black | cut | dissolve | wipe
    duration: int = 20             # frames

    def to_dict(self) -> dict:
        return {"type": self.type, "duration": self.duration}

    @classmethod
    def from_dict(cls, d: dict) -> "TransitionConfig":
        if not d:
            return cls()
        return cls(type=d.get("type", "fade"), duration=int(d.get("duration", 20)))


@dataclass
class TextOverlay:
    """
    Text overlay mínimo — apenas se existia no frame ou é requerido pelo conceito.
    NÃO deve ser usado para inventar elementos que não existem na composição original.
    """
    id: str
    text: str
    x: float = 50.0               # % do frame
    y: float = 85.0               # % — por padrão na parte inferior (não sobre o frame)
    font_size: int = 40
    font_weight: int = 600
    color: str = "#ffffff"
    opacity: float = 0.9
    enter_frame: int = 0
    exit_frame: int = -1           # -1 = até o fim da cena
    enter_animation: str = "fade_up"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "color": self.color,
            "opacity": self.opacity,
            "enter_frame": self.enter_frame,
            "exit_frame": self.exit_frame,
            "enter_animation": self.enter_animation,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TextOverlay":
        return cls(
            id=d.get("id", "text"),
            text=d.get("text", ""),
            x=float(d.get("x", 50)),
            y=float(d.get("y", 85)),
            font_size=int(d.get("font_size", 40)),
            font_weight=int(d.get("font_weight", 600)),
            color=d.get("color", "#ffffff"),
            opacity=float(d.get("opacity", 0.9)),
            enter_frame=int(d.get("enter_frame", 0)),
            exit_frame=int(d.get("exit_frame", -1)),
            enter_animation=d.get("enter_animation", "fade_up"),
        )


@dataclass
class MotionDSL:
    """
    DSL de movimento puro — a única saída que o LLM autoriza.

    CONTÉM SOMENTE:
      - camera_motion    (como a câmera se move)
      - layer_animations (micro-animações por camada)
      - particles        (partículas atmosféricas)
      - atmosphere       (vinheta, grain, glow, color grade)
      - transitions      (enter/exit da cena)
      - text_overlays    (texto mínimo, se requerido)
      - timing           (pacing cinematic)

    NÃO CONTÉM:
      - composição
      - objetos
      - layout
      - background
      - image_elements
      - shape_elements
      - geometry
    """
    scene_id: int = 1
    duration: int = 90             # frames
    fps: int = 30
    description: str = ""

    camera: CameraPhysics = field(default_factory=CameraPhysics)
    layer_animations: List[LayerAnimation] = field(default_factory=list)
    particles: ParticleConfig = field(default_factory=ParticleConfig)
    atmosphere: AtmosphereConfig = field(default_factory=AtmosphereConfig)
    transition_in: Optional[TransitionConfig] = field(default_factory=lambda: TransitionConfig(type="fade", duration=20))
    transition_out: Optional[TransitionConfig] = field(default_factory=lambda: TransitionConfig(type="fade", duration=20))
    text_overlays: List[TextOverlay] = field(default_factory=list)

    # Metadados cinematográficos
    cinematic_energy: float = 0.5  # 0=calmo, 1=intenso
    pacing_note: str = ""          # nota do motion planner
    agent_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "duration": self.duration,
            "fps": self.fps,
            "description": self.description,
            "camera": self.camera.to_dict(),
            "layer_animations": [a.to_dict() for a in self.layer_animations],
            "particles": self.particles.to_dict(),
            "atmosphere": self.atmosphere.to_dict(),
            "transition_in": self.transition_in.to_dict() if self.transition_in else None,
            "transition_out": self.transition_out.to_dict() if self.transition_out else None,
            "text_overlays": [t.to_dict() for t in self.text_overlays],
            "cinematic_energy": self.cinematic_energy,
            "pacing_note": self.pacing_note,
            "agent_notes": self.agent_notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MotionDSL":
        ti = d.get("transition_in")
        to_ = d.get("transition_out")
        return cls(
            scene_id=int(d.get("scene_id", 1)),
            duration=int(d.get("duration", 90)),
            fps=int(d.get("fps", 30)),
            description=d.get("description", ""),
            camera=CameraPhysics.from_dict(d.get("camera", {})),
            layer_animations=[LayerAnimation.from_dict(a) for a in d.get("layer_animations", [])],
            particles=ParticleConfig.from_dict(d.get("particles", {})),
            atmosphere=AtmosphereConfig.from_dict(d.get("atmosphere", {})),
            transition_in=TransitionConfig.from_dict(ti) if ti else TransitionConfig(),
            transition_out=TransitionConfig.from_dict(to_) if to_ else TransitionConfig(),
            text_overlays=[TextOverlay.from_dict(t) for t in d.get("text_overlays", [])],
            cinematic_energy=float(d.get("cinematic_energy", 0.5)),
            pacing_note=d.get("pacing_note", ""),
            agent_notes=d.get("agent_notes", ""),
        )

    def apply_delta(self, delta: dict) -> "MotionDSL":
        """
        Aplica um delta patch sem recriar o MotionDSL do zero.
        Usado pelo DeltaPatcher para alterações parciais baseadas em feedback.
        """
        import copy
        updated = copy.deepcopy(self.to_dict())

        def _deep_set(obj: dict, path: str, value):
            keys = path.split(".")
            for k in keys[:-1]:
                obj = obj.setdefault(k, {})
            obj[keys[-1]] = value

        for path, value in delta.items():
            _deep_set(updated, path, value)

        return MotionDSL.from_dict(updated)
