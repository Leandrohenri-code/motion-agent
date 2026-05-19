"""
Scene DSL — Intermediate Scene Representation.

É a fonte da verdade do projeto. O LLM nunca mais escreve TSX diretamente.
Ele gera esta estrutura JSON. O Remotion Compiler converte para TSX genérico.

Benefícios:
  - Hot reload sem regenerar código
  - Timeline editável (cada campo é um parâmetro)
  - Coherence engine pode corrigir campos específicos
  - Preview instantâneo ao mudar qualquer valor
  - Portável: mesma DSL pode compilar para Remotion, After Effects, etc.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import json


# ── Primitivos ───────────────────────────────────────────────────────────────

@dataclass
class MotionProfile:
    """Parâmetros físicos de um movimento. Todos os movimentos têm isso."""
    type: str               # dolly_in, pan_right, zoom, float, parallax, shake, orbit
    velocity: float = 0.3
    acceleration: float = 0.1
    momentum: float = 0.6
    easing: str = "easeInOut"   # easeIn, easeOut, easeInOut, linear, spring, bounce
    intensity: float = 0.3
    direction: str = "none"     # up, down, left, right, in, out, none
    damping: float = 14.0       # spring damping
    stiffness: float = 160.0    # spring stiffness


@dataclass
class Position:
    x: float = 0.0   # 0-100% ou pixels
    y: float = 0.0
    z: float = 0.0   # depth layer (0 = back, 1 = front)
    unit: str = "percent"   # percent | px


@dataclass
class Scale:
    x: float = 1.0
    y: float = 1.0
    origin_x: float = 0.5   # 0-1, transform origin
    origin_y: float = 0.5


@dataclass
class Typography:
    font_family: str = "'Helvetica Neue', Arial, sans-serif"
    font_size: int = 80         # px
    font_weight: int = 800
    letter_spacing: float = -2.0
    line_height: float = 1.15
    color: str = "#ffffff"
    text_transform: str = "none"   # none, uppercase, lowercase
    text_shadow: str = ""
    gradient: str = ""             # CSS gradient para gradient text


@dataclass
class AnimationKeyframe:
    """Keyframe individual de uma propriedade."""
    frame: int
    value: Any
    easing: str = "easeOut"


# ── Elementos ─────────────────────────────────────────────────────────────────

@dataclass
class ElementAnimation:
    """Animação de um elemento: entrada, idle e saída."""
    enter_start: int = 0
    enter_duration: int = 25
    enter_type: str = "fade_up"         # fade_up, fade_in, clip_left, scale_in, blur_in, word_stagger
    enter_easing: str = "spring"
    exit_start: int = -1                # -1 = calculado: durationInFrames - exit_duration
    exit_duration: int = 18
    exit_type: str = "fade_out"         # fade_out, clip_right, scale_out, blur_out, slide_up
    exit_easing: str = "easeIn"
    idle_motion: Optional[MotionProfile] = None   # movimento durante a cena (parallax, float, etc.)


@dataclass
class TextElement:
    id: str
    text: str
    role: str = "headline"          # headline, subheading, body, label, counter, caption
    start: int = 0
    duration: int = 180
    position: Position = field(default_factory=Position)
    typography: Typography = field(default_factory=Typography)
    animation: ElementAnimation = field(default_factory=ElementAnimation)
    max_width: int = 1600           # px
    align: str = "center"          # left, center, right
    word_stagger_delay: int = 4     # frames entre palavras (se enter_type = word_stagger)


@dataclass
class ImageElement:
    id: str
    src: str                        # caminho relativo ou base64
    start: int = 0
    duration: int = 180
    position: Position = field(default_factory=Position)
    scale: Scale = field(default_factory=Scale)
    animation: ElementAnimation = field(default_factory=ElementAnimation)
    blur: float = 0.0
    opacity: float = 1.0
    blend_mode: str = "normal"
    fit: str = "cover"              # cover, contain, fill


@dataclass
class ShapeElement:
    id: str
    shape: str = "rect"             # rect, circle, line, gradient_blob
    start: int = 0
    duration: int = 180
    position: Position = field(default_factory=Position)
    width: float = 100.0            # percent da tela
    height: float = 100.0
    color: str = "#6c63ff"
    opacity: float = 1.0
    blur: float = 0.0
    animation: ElementAnimation = field(default_factory=ElementAnimation)
    gradient: str = ""


@dataclass
class ParticleField:
    id: str
    count: int = 20
    start: int = 0
    duration: int = 180
    color: str = "#ffffff"
    size_min: float = 1.5
    size_max: float = 4.0
    opacity_min: float = 0.2
    opacity_max: float = 0.6
    motion_type: str = "float"      # float, drift, burst, orbit
    seed: int = 42


# ── Câmera ────────────────────────────────────────────────────────────────────

@dataclass
class CameraConfig:
    """
    Comportamento de câmera da cena.
    Implementado como transformação CSS no AbsoluteFill raiz.
    """
    motion: MotionProfile = field(default_factory=lambda: MotionProfile(type="static"))
    fov: float = 40.0           # Field of view simulado (parallax depth)
    parallax_depth: float = 0.15  # Intensidade do efeito parallax entre layers
    shake_intensity: float = 0.0  # 0 = sem shake
    tilt: float = 0.0             # graus de inclinação inicial


# ── Ambiente ──────────────────────────────────────────────────────────────────

@dataclass
class EnvironmentConfig:
    background: str = "#0a0a0a"    # cor, gradiente CSS ou 'transparent'
    glow_color: str = ""           # cor do glow atmosférico (vazio = sem glow)
    glow_x: float = 50.0           # posição X do glow (%)
    glow_y: float = 40.0           # posição Y do glow (%)
    glow_size: float = 60.0        # tamanho do glow (% da tela)
    glow_opacity: float = 0.2
    vignette: float = 0.0          # 0-1, escurecimento nas bordas
    grain: float = 0.0             # 0-1, ruído cinematográfico
    depth_layers: int = 3          # quantidade de planos de profundidade


# ── Transição ─────────────────────────────────────────────────────────────────

@dataclass
class Transition:
    type: str = "fade"      # fade, fade_black, slide_left, slide_up, clip_wipe, scale_out, dissolve
    duration: int = 20      # frames


# ── Visual DNA ───────────────────────────────────────────────────────────────

@dataclass
class VisualDNA:
    """
    Identidade visual do projeto. Persiste entre TODAS as cenas.
    Extraída na primeira cena, herdada por todas as subsequentes.
    """
    palette: List[str] = field(default_factory=lambda: ["#0a0a0a", "#ffffff", "#6c63ff"])
    primary_color: str = "#6c63ff"
    accent_color: str = "#00d4aa"
    background_color: str = "#0a0a0a"
    lighting_style: str = "cinematic_soft"      # cinematic_soft, high_contrast, backlit, flat, neon
    camera_language: str = "commercial_clean"   # luxury_archviz, commercial_clean, editorial, documentary
    motion_signature: str = "spring_organic"    # spring_organic, linear_precise, bouncy_playful, cinematic_slow
    typography_style: str = "bold_modern"       # bold_modern, elegant_thin, geometric, editorial
    transition_signature: str = "fade_black"
    cinematic_mood: str = "professional"        # professional, luxury, energetic, minimal, dramatic
    composition_rule: str = "center_dominant"   # center_dominant, rule_of_thirds, dynamic_asymmetry
    font_primary: str = "'Helvetica Neue', Arial, sans-serif"
    font_display: str = "'Helvetica Neue', 'Arial Black', sans-serif"


# ── Scene DSL Principal ───────────────────────────────────────────────────────

@dataclass
class SceneDSL:
    """
    Representação intermediária completa de uma cena.
    Esta é a fonte da verdade — o LLM gera isso, nunca TSX.
    """
    scene_id: int
    duration: int               # frames totais
    fps: int = 30
    width: int = 1920
    height: int = 1080
    description: str = ""       # descrição legível por humanos

    visual_dna: VisualDNA = field(default_factory=VisualDNA)
    camera: CameraConfig = field(default_factory=CameraConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)

    text_elements: List[TextElement] = field(default_factory=list)
    image_elements: List[ImageElement] = field(default_factory=list)
    shape_elements: List[ShapeElement] = field(default_factory=list)
    particle_fields: List[ParticleField] = field(default_factory=list)

    transition_in: Optional[Transition] = None
    transition_out: Optional[Transition] = field(default_factory=lambda: Transition(type="fade", duration=20))

    # Metadados do agente
    agent_notes: str = ""          # notas do Creative Director
    coherence_score: float = 10.0  # score do Coherence Agent (0-10)
    coherence_issues: List[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SceneDSL":
        """Desserializa do JSON gerado pela IA (tolerante a campos extras/faltantes)."""
        # Reconstrói dataclasses aninhadas
        if "visual_dna" in data:
            data["visual_dna"] = VisualDNA(**{k: v for k, v in data["visual_dna"].items() if k in VisualDNA.__dataclass_fields__})
        if "camera" in data and isinstance(data["camera"], dict):
            motion = data["camera"].pop("motion", {})
            if motion:
                data["camera"]["motion"] = MotionProfile(**{k: v for k, v in motion.items() if k in MotionProfile.__dataclass_fields__})
            data["camera"] = CameraConfig(**{k: v for k, v in data["camera"].items() if k in CameraConfig.__dataclass_fields__})
        if "environment" in data:
            data["environment"] = EnvironmentConfig(**{k: v for k, v in data["environment"].items() if k in EnvironmentConfig.__dataclass_fields__})
        if "transition_out" in data and data["transition_out"]:
            data["transition_out"] = Transition(**data["transition_out"])
        if "transition_in" in data and data["transition_in"]:
            data["transition_in"] = Transition(**data["transition_in"])

        # Filtra apenas campos válidos do SceneDSL
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        # Remove listas complexas por ora (serão processadas pelo compiler)
        valid.pop("text_elements", None)
        valid.pop("image_elements", None)
        valid.pop("shape_elements", None)
        valid.pop("particle_fields", None)

        dsl = cls(**valid)

        # Reconstrói elementos
        for el in data.get("text_elements", []):
            try:
                anim = el.pop("animation", {})
                pos = el.pop("position", {})
                typo = el.pop("typography", {})
                elem = TextElement(
                    animation=ElementAnimation(**{k: v for k, v in anim.items() if k in ElementAnimation.__dataclass_fields__}) if anim else ElementAnimation(),
                    position=Position(**{k: v for k, v in pos.items() if k in Position.__dataclass_fields__}) if pos else Position(),
                    typography=Typography(**{k: v for k, v in typo.items() if k in Typography.__dataclass_fields__}) if typo else Typography(),
                    **{k: v for k, v in el.items() if k in TextElement.__dataclass_fields__}
                )
                dsl.text_elements.append(elem)
            except Exception:
                pass

        for el in data.get("image_elements", []):
            try:
                anim = el.pop("animation", {})
                pos = el.pop("position", {})
                scale = el.pop("scale", {})
                elem = ImageElement(
                    animation=ElementAnimation(**{k: v for k, v in anim.items() if k in ElementAnimation.__dataclass_fields__}) if anim else ElementAnimation(),
                    position=Position(**{k: v for k, v in pos.items() if k in Position.__dataclass_fields__}) if pos else Position(),
                    scale=Scale(**{k: v for k, v in scale.items() if k in Scale.__dataclass_fields__}) if scale else Scale(),
                    **{k: v for k, v in el.items() if k in ImageElement.__dataclass_fields__}
                )
                dsl.image_elements.append(elem)
            except Exception:
                pass

        for el in data.get("shape_elements", []):
            try:
                anim = el.pop("animation", {})
                pos = el.pop("position", {})
                elem = ShapeElement(
                    animation=ElementAnimation(**{k: v for k, v in anim.items() if k in ElementAnimation.__dataclass_fields__}) if anim else ElementAnimation(),
                    position=Position(**{k: v for k, v in pos.items() if k in Position.__dataclass_fields__}) if pos else Position(),
                    **{k: v for k, v in el.items() if k in ShapeElement.__dataclass_fields__}
                )
                dsl.shape_elements.append(elem)
            except Exception:
                pass

        for pf in data.get("particle_fields", []):
            try:
                dsl.particle_fields.append(ParticleField(**{k: v for k, v in pf.items() if k in ParticleField.__dataclass_fields__}))
            except Exception:
                pass

        return dsl
