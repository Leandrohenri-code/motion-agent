"""
DSL Generator Agent.

Responsável por:
- Gerar o SceneDSL completo a partir do plano de cena
- Traduzir intenção artística em parâmetros DSL exatos
- O LLM nunca mais gera TSX diretamente — apenas SceneDSL JSON
"""

from __future__ import annotations
import json
import re
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_client import AIClient
    from visual_dna import VisualDNA
    from temporal_memory import TemporalMemory
    from agents.scene_planner import ScenePlan
    from composition_extractor import CompositionConstraints

from scene_dsl import (
    SceneDSL, VisualDNA as SceneDSLDNA, CameraConfig, MotionProfile,
    EnvironmentConfig, Transition, TextElement, ImageElement, ShapeElement,
    ParticleField, Position, Scale, Typography, ElementAnimation
)

# TYPE_CHECKING import for CompositionConstraints (avoids circular imports)
try:
    from composition_extractor import CompositionConstraints
except ImportError:
    CompositionConstraints = None  # type: ignore


DSL_GENERATOR_SYSTEM = """Você é um DSL Generator para motion design cinematográfico.
Você recebe um plano de cena e gera um SceneDSL JSON preciso e completo.
Você conhece profundamente os princípios de animação, motion design e cinematografia.
Você é extremamente preciso nos valores numéricos — spring physics, timing, easing.
NUNCA gere código TypeScript. APENAS JSON SceneDSL."""

DSL_GENERATOR_SYSTEM_LOCKED = """Você é um Motion Operator — não um artista criativo.
Você recebe um frame de referência que é VERDADE ABSOLUTA e IMUTÁVEL.
Sua única função é ANIMAR esse frame. Não recriar. Não reinterpretar.

REGRAS ABSOLUTAS:
1. NÃO redesenhe o ambiente, arquitetura ou objetos
2. NÃO mova posições de elementos — preserve a geometria exata
3. NÃO invente novos elementos visuais
4. NÃO altere composição, framing ou proporções
5. APENAS: câmera, parallax, profundidade, timing, iluminação dinâmica

O frame original é inserido como background_plate.
Você gera SceneDSL JSON. NUNCA TypeScript."""

# Referência completa dos campos DSL para o prompt
DSL_SCHEMA_REFERENCE = """
SCHEMA SCENE DSL (campos chave):
{
  "scene_id": int,
  "duration": int,          // frames totais
  "fps": 30,
  "description": "string",
  "visual_dna": {           // SEMPRE copie do DNA fornecido
    "palette": [...], "primary_color": "#hex", "accent_color": "#hex",
    "background_color": "#hex", "lighting_style": "...", "camera_language": "...",
    "motion_signature": "...", "typography_style": "...", "transition_signature": "...",
    "cinematic_mood": "...", "font_primary": "...", "font_display": "..."
  },
  "camera": {
    "motion": {
      "type": "dolly_in|dolly_out|pan_right|pan_left|zoom|float|parallax|orbit|shake|static",
      "velocity": 0.3,       // 0.1 (lento) a 1.0 (rápido)
      "acceleration": 0.1,
      "momentum": 0.6,
      "easing": "spring|easeInOut|easeOut|linear",
      "intensity": 0.3,      // 0.1 a 0.8
      "direction": "in|out|left|right|up|down|none",
      "damping": 14.0,       // spring: 10-20
      "stiffness": 160.0     // spring: 100-250
    },
    "parallax_depth": 0.15,
    "shake_intensity": 0.0,
    "tilt": 0.0
  },
  "environment": {
    "background": "#hex ou 'linear-gradient(135deg, #hex 0%, #hex 100%)'",
    "glow_color": "#hex",    // cor principal do glow atmosférico
    "glow_x": 50.0,          // posição X do glow (%)
    "glow_y": 40.0,
    "glow_size": 60.0,
    "glow_opacity": 0.2,
    "vignette": 0.3,         // 0-1
    "grain": 0.02,           // 0-1, sutil é melhor
    "depth_layers": 3
  },
  "text_elements": [{
    "id": "text_headline",
    "text": "TEXTO AQUI",
    "role": "headline|subheading|body|label|counter|caption",
    "start": 0,
    "duration": 180,
    "position": {"x": 50.0, "y": 50.0, "z": 0.5, "unit": "percent"},
    "typography": {
      "font_family": "'Helvetica Neue', Arial, sans-serif",
      "font_size": 80,       // px: headline=60-120, sub=32-50, body=20-28
      "font_weight": 800,
      "letter_spacing": -2.0,
      "line_height": 1.15,
      "color": "#ffffff",
      "text_transform": "uppercase|none|lowercase",
      "gradient": ""         // ex: "linear-gradient(135deg, #fff 0%, #aaa 100%)"
    },
    "animation": {
      "enter_start": 0,
      "enter_duration": 25,
      "enter_type": "fade_up|fade_in|clip_left|scale_in|blur_in|word_stagger",
      "enter_easing": "spring",
      "exit_start": -1,      // -1 = auto (duration - exit_duration)
      "exit_duration": 18,
      "exit_type": "fade_out|clip_right|scale_out|blur_out|slide_up",
      "exit_easing": "easeIn",
      "idle_motion": null    // ou MotionProfile para float/parallax durante idle
    },
    "max_width": 1600,
    "align": "center|left|right",
    "word_stagger_delay": 4
  }],
  "shape_elements": [{
    "id": "bg_gradient",
    "shape": "rect|circle|gradient_blob",
    "start": 0, "duration": 180,
    "position": {"x": 0, "y": 0, "z": 0, "unit": "percent"},
    "width": 100.0, "height": 100.0,
    "color": "#hex",
    "opacity": 1.0,
    "blur": 0.0,
    "gradient": "linear-gradient(135deg, #hex 0%, #hex 100%)",
    "animation": { "enter_type": "fade_in", "enter_duration": 30, ... }
  }],
  "particle_fields": [{
    "id": "particles_bg",
    "count": 20,
    "start": 0, "duration": 180,
    "color": "#ffffff",
    "size_min": 1.5, "size_max": 4.0,
    "opacity_min": 0.2, "opacity_max": 0.6,
    "motion_type": "float|drift|burst|orbit",
    "seed": 42
  }],
  "transition_in": {"type": "fade|fade_black|slide_left|clip_wipe", "duration": 20},
  "transition_out": {"type": "fade|fade_black|slide_left|clip_wipe", "duration": 20},
  "agent_notes": "notas do Creative Director"
}
"""


class DSLGenerator:
    """
    Gera o SceneDSL JSON completo usando o LLM.
    O LLM recebe um plano estruturado e retorna JSON puro.
    """

    def __init__(self, client: "AIClient"):
        self.client = client

    def generate(
        self,
        scene_num: int,
        frame: dict,
        dna: "VisualDNA",
        memory: "TemporalMemory",
        scene_plan: Optional["ScenePlan"] = None,
        creative_direction: str = "",
        total_scenes: int = 1,
        fps: int = 30,
        frame_image: Optional[str] = None,
        locked_composition: bool = False,
        composition_constraints: Optional["CompositionConstraints"] = None,
    ) -> SceneDSL:
        """
        Gera um SceneDSL completo.

        Args:
            frame_image:            Base64 data URL da imagem de referência (para vision LLM).
            locked_composition:     Modo Referência Bloqueada — preserva composição original.
            composition_constraints: Constraints extraídos do frame (posições, layout).

        Returns:
            SceneDSL object pronto para o Remotion Compiler
        """
        duration_frames = int(float(frame.get("duration", 3)) * fps)
        description = frame.get("description", "")
        is_first = scene_num == 1
        is_last = scene_num == total_scenes

        # Sistema prompt específico por modo
        orig_system = self.client.system_prompt
        if locked_composition:
            self.client.system_prompt = DSL_GENERATOR_SYSTEM_LOCKED

        try:
            prompt = self._build_prompt(
                scene_num=scene_num,
                total_scenes=total_scenes,
                description=description,
                duration_frames=duration_frames,
                fps=fps,
                dna=dna,
                memory=memory,
                scene_plan=scene_plan,
                creative_direction=creative_direction,
                is_first=is_first,
                is_last=is_last,
                has_image=frame_image is not None,
                locked_composition=locked_composition,
                composition_constraints=composition_constraints,
            )

            # Gera via LLM — passa imagem de referência se disponível
            # Se o modelo não suportar visão (400/429), re-tenta sem imagem
            images = [frame_image] if frame_image else None
            try:
                raw = self.client.complete(prompt, images=images)
            except Exception as e:
                if images and _is_vision_unsupported_error(e):
                    raw = self.client.complete(prompt, images=None)
                else:
                    raise
            json_str = _extract_json(raw)

            try:
                data = json.loads(json_str)
                data["scene_id"] = scene_num
                data["duration"] = duration_frames
                data["fps"] = fps
                dsl = SceneDSL.from_dict(data)
            except Exception:
                dsl = self._fallback_dsl(scene_num, description, duration_frames, fps, dna)

        finally:
            self.client.system_prompt = orig_system

        # Modo bloqueado: injeta o frame original como background_plate
        # A composição original é a base; o LLM só anima por cima
        if locked_composition and frame_image:
            _inject_background_plate(dsl, frame_image, duration_frames)

        return dsl

    def _build_prompt(
        self,
        scene_num: int,
        total_scenes: int,
        description: str,
        duration_frames: int,
        fps: int,
        dna: "VisualDNA",
        memory: "TemporalMemory",
        scene_plan: Optional["ScenePlan"],
        creative_direction: str,
        is_first: bool,
        is_last: bool,
        has_image: bool = False,
        locked_composition: bool = False,
        composition_constraints: Optional["CompositionConstraints"] = None,
    ) -> str:
        parts = []

        # ── Modo Referência Bloqueada: constraints primeiro ─────────────────
        if locked_composition and composition_constraints:
            parts.append(composition_constraints.to_prompt_section())
            parts.append("")

        # Contexto de memória temporal
        parts.append(memory.to_prompt_section())
        parts.append("")

        # Direção criativa
        if creative_direction:
            parts.append(creative_direction)
            parts.append("")

        # Plano de cena
        if scene_plan:
            parts.append(scene_plan.to_prompt_section())
            parts.append("")

        # Instruções específicas
        parts.append(f"=== INSTRUÇÃO: GERAR SCENEDSL — CENA {scene_num}/{total_scenes} ===")
        parts.append(f"Descrição: {description}")
        parts.append(f"Duração: {duration_frames} frames ({duration_frames/fps:.1f}s) @ {fps}fps")

        if is_first:
            parts.append("PRIMEIRA CENA: Abertura de impacto. transition_in: null. Câmera dinâmica.")
        elif is_last:
            parts.append("ÚLTIMA CENA: Fechamento memorável. transition_out deve ser impactante.")

        if has_image and not locked_composition:
            # Modo criativo: usa imagem como inspiração
            parts.append("")
            parts.append("IMAGEM DE REFERÊNCIA FORNECIDA:")
            parts.append("Extraia: cores dominantes, composição, estilo, tipografia, mood.")
            parts.append("Gere uma interpretação animada cinematográfica desta imagem.")

        if locked_composition:
            # Modo bloqueado: restrições rígidas de preservação
            parts.append("")
            parts.append("BACKGROUND PLATE: O frame original será renderizado automaticamente como")
            parts.append("  image_element com id='background_plate'. NÃO adicione shape de fundo.")
            parts.append("  Adicione APENAS text_elements e particle_fields sobre o plate.")
            parts.append("  Camera motion e parallax são sua única liberdade compositiva.")
            if has_image:
                parts.append("  A imagem enviada confirma a composição — preserve-a exatamente.")

        parts.append("")
        if locked_composition:
            parts.append("Gere o SceneDSL JSON — SOMENTE motion, câmera, texto overlay e partículas.")
            parts.append("REGRAS ABSOLUTAS:")
            parts.append("1. NÃO adicione shape_elements de fundo (o background_plate já existe)")
            parts.append("2. text_elements: apenas se existiam na imagem original ou são necessários ao concept")
            parts.append(f"3. spring damping={dna.spring_damping}, stiffness={dna.spring_stiffness}")
            parts.append("4. Responda com JSON puro, sem markdown, sem explicações")
        else:
            parts.append("Gere o SceneDSL JSON COMPLETO desta cena.")
            parts.append("REGRAS ABSOLUTAS:")
            parts.append("1. Use SOMENTE as cores do Visual DNA")
            parts.append(f"2. spring damping={dna.spring_damping}, stiffness={dna.spring_stiffness}")
            parts.append("3. Mínimo: 1 shape (background) + 1 texto principal")
            parts.append("4. Responda com JSON puro, sem markdown, sem explicações")

        parts.append("")
        parts.append("SCHEMA DE REFERÊNCIA:")
        parts.append(DSL_SCHEMA_REFERENCE)

        return "\n".join(parts)

    def _fallback_dsl(
        self,
        scene_num: int,
        description: str,
        duration_frames: int,
        fps: int,
        dna: "VisualDNA",
    ) -> SceneDSL:
        """DSL de fallback quando o LLM falha."""
        words = description.split()
        headline = " ".join(words[:4]).upper() if words else f"CENA {scene_num}"
        sub = " ".join(words[4:8]) if len(words) > 4 else ""

        from visual_dna import VisualDNA as ExtDNA
        palette = dna.palette if hasattr(dna, 'palette') else ["#0a0a0a", "#ffffff", "#6c63ff"]
        primary = dna.primary_color if hasattr(dna, 'primary_color') else "#6c63ff"
        accent = dna.accent_color if hasattr(dna, 'accent_color') else "#00d4aa"
        bg = dna.background_color if hasattr(dna, 'background_color') else "#0a0a0a"

        scene = SceneDSL(
            scene_id=scene_num,
            duration=duration_frames,
            fps=fps,
            description=description,
        )

        # Atualiza visual_dna
        scene.visual_dna.palette = palette
        scene.visual_dna.primary_color = primary
        scene.visual_dna.accent_color = accent
        scene.visual_dna.background_color = bg

        # Background
        scene.shape_elements.append(ShapeElement(
            id="bg",
            shape="rect",
            start=0,
            duration=duration_frames,
            position=Position(x=0, y=0, z=0, unit="percent"),
            width=100.0,
            height=100.0,
            color=bg,
            opacity=1.0,
            gradient=f"linear-gradient(135deg, {bg} 0%, {_darken(bg)} 100%)",
            animation=ElementAnimation(enter_type="fade_in", enter_duration=30),
        ))

        # Headline
        scene.text_elements.append(TextElement(
            id="headline",
            text=headline,
            role="headline",
            start=0,
            duration=duration_frames,
            position=Position(x=50.0, y=50.0, z=0.5, unit="percent"),
            typography=Typography(
                font_family=dna.font_primary if hasattr(dna, 'font_primary') else "'Helvetica Neue', Arial, sans-serif",
                font_size=80,
                font_weight=800,
                letter_spacing=-2.0,
                color="#ffffff",
            ),
            animation=ElementAnimation(
                enter_type="fade_up",
                enter_duration=25,
                enter_easing="spring",
            ),
        ))

        if sub:
            scene.text_elements.append(TextElement(
                id="subheading",
                text=sub,
                role="subheading",
                start=15,
                duration=duration_frames - 15,
                position=Position(x=50.0, y=62.0, z=0.5, unit="percent"),
                typography=Typography(
                    font_family=dna.font_primary if hasattr(dna, 'font_primary') else "'Helvetica Neue', Arial, sans-serif",
                    font_size=36,
                    font_weight=400,
                    letter_spacing=0.5,
                    color=accent,
                ),
                animation=ElementAnimation(
                    enter_type="fade_in",
                    enter_start=15,
                    enter_duration=20,
                ),
            ))

        # Câmera
        scene.camera.motion.type = "parallax"
        scene.camera.motion.intensity = 0.2

        # Ambiente
        scene.environment.background = bg
        scene.environment.glow_color = primary
        scene.environment.glow_opacity = 0.2
        scene.environment.vignette = 0.3

        # Transições
        scene.transition_out = Transition(type="fade_black", duration=20)

        return scene


def _inject_background_plate(dsl: SceneDSL, image_b64: str, duration_frames: int) -> None:
    """
    Injeta o frame original como background_plate no DSL (in-place).
    Remove qualquer shape que cubra o fundo para não sobrepor a imagem.
    A imagem fica ligeiramente over-scaled (1.08x) para dar espaço ao parallax.
    """
    # Remove shapes que cobrem o fundo inteiro (evita cobrir o plate)
    dsl.shape_elements = [
        s for s in dsl.shape_elements
        if not (s.position.x == 0 and s.position.y == 0 and s.width >= 95 and s.height >= 95)
    ]

    # Cria o background_plate como primeiro image_element
    plate = ImageElement(
        id="background_plate",
        src=image_b64,
        start=0,
        duration=duration_frames,
        position=Position(x=50.0, y=50.0, z=0.0, unit="percent"),
        scale=Scale(x=1.08, y=1.08),
        opacity=1.0,
        fit="cover",
        blend_mode="normal",
        animation=ElementAnimation(
            enter_type="fade_in",
            enter_start=0,
            enter_duration=15,
        ),
    )

    # Insere no início para ficar atrás de todos os outros elementos
    dsl.image_elements = [plate] + [
        el for el in dsl.image_elements if el.id != "background_plate"
    ]


def _is_vision_unsupported_error(exc: Exception) -> bool:
    """
    Retorna True se o erro sugere que a imagem causou a falha.
    Inclui: modelo sem suporte a visão (400) e rate limit por excesso de tokens de imagem (429).
    Quando True com images presentes, o caller retenta sem a imagem.
    """
    msg = str(exc).lower()
    return any(k in msg for k in ("400", "429", "image", "vision", "unsupported", "multimodal", "does not support", "too many"))


def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return m.group(1)
    return text.strip()


def _darken(hex_color: str, amount: float = 0.4) -> str:
    """Escurece um hex color."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = int(r * (1 - amount))
        g = int(g * (1 - amount))
        b = int(b * (1 - amount))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#000000"
