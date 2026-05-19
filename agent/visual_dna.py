"""
Visual DNA — Extrator e Guardião da Identidade Visual.

Extrai a identidade visual de imagens de referência e mantém
coerência entre TODAS as cenas do projeto.
"""

from __future__ import annotations
import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_client import AIClient


@dataclass
class VisualDNA:
    """Identidade visual do projeto — fonte da verdade estética."""

    # Cor
    palette: List[str] = field(default_factory=lambda: ["#0a0a0a", "#ffffff", "#6c63ff"])
    primary_color: str = "#6c63ff"
    accent_color: str = "#00d4aa"
    background_color: str = "#0a0a0a"
    text_color: str = "#ffffff"

    # Iluminação e atmosfera
    lighting_style: str = "cinematic_soft"       # cinematic_soft, high_contrast, backlit, flat, neon
    contrast_profile: str = "dark_rich"          # dark_rich, bright_clean, moody, pastel
    glow_color: str = "#6c63ff"

    # Movimento
    motion_signature: str = "spring_organic"     # spring_organic, linear_precise, bouncy_playful, cinematic_slow
    camera_language: str = "commercial_clean"    # luxury_archviz, commercial_clean, editorial, documentary
    spring_damping: float = 14.0
    spring_stiffness: float = 160.0
    transition_signature: str = "fade_black"

    # Tipografia
    typography_style: str = "bold_modern"        # bold_modern, elegant_thin, geometric, editorial
    font_primary: str = "'Helvetica Neue', Arial, sans-serif"
    font_display: str = "'Helvetica Neue', 'Arial Black', sans-serif"
    font_weight_display: int = 800
    letter_spacing: float = -2.0

    # Composição
    composition_rule: str = "center_dominant"    # center_dominant, rule_of_thirds, dynamic_asymmetry
    cinematic_mood: str = "professional"         # professional, luxury, energetic, minimal, dramatic

    # Metadados
    extracted_from: str = ""        # descrição da imagem de referência
    confidence: float = 0.8         # 0-1

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "VisualDNA":
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    def to_prompt_section(self) -> str:
        """Serializa o DNA para injeção no prompt da IA."""
        return f"""
=== VISUAL DNA — IDENTIDADE IMUTÁVEL DO PROJETO ===
Palette: {', '.join(self.palette)}
Primary: {self.primary_color} | Accent: {self.accent_color} | BG: {self.background_color}
Lighting: {self.lighting_style} | Contrast: {self.contrast_profile}
Motion Signature: {self.motion_signature} (damping={self.spring_damping}, stiffness={self.spring_stiffness})
Camera Language: {self.camera_language}
Typography: {self.typography_style} | Font: {self.font_primary}
Composition: {self.composition_rule} | Mood: {self.cinematic_mood}
Transition Signature: {self.transition_signature}

REGRAS DE CONSISTÊNCIA:
- Use SOMENTE as cores da palette acima
- Mantenha os valores de spring (damping/stiffness) exatos
- Toda transição deve usar: {self.transition_signature}
- Mood cinematográfico: {self.cinematic_mood}
""".strip()


class VisualDNAExtractor:
    """
    Extrai o DNA visual de uma imagem de referência usando visão computacional.
    Cacheia o resultado para uso em todas as cenas.
    """

    def __init__(self, vision_client: "AIClient"):
        self.vision_client = vision_client
        self._dna: Optional[VisualDNA] = None

    @property
    def dna(self) -> Optional[VisualDNA]:
        return self._dna

    def extract_from_image(self, image_b64: str, manual_description: str = "") -> VisualDNA:
        """Extrai DNA de uma imagem via IA de visão."""

        context = f"\nContexto adicional do usuário: {manual_description}" if manual_description else ""

        prompt = f"""Você é um diretor de arte especializado em motion design cinematográfico.
Analise esta imagem de referência e extraia a identidade visual completa para um projeto de vídeo.{context}

Responda com JSON válido no seguinte formato (sem markdown, apenas JSON puro):
{{
  "palette": ["#hex1", "#hex2", "#hex3", "#hex4"],
  "primary_color": "#hex",
  "accent_color": "#hex",
  "background_color": "#hex",
  "text_color": "#hex",
  "lighting_style": "cinematic_soft|high_contrast|backlit|flat|neon",
  "contrast_profile": "dark_rich|bright_clean|moody|pastel",
  "glow_color": "#hex",
  "motion_signature": "spring_organic|linear_precise|bouncy_playful|cinematic_slow",
  "camera_language": "luxury_archviz|commercial_clean|editorial|documentary",
  "spring_damping": 14.0,
  "spring_stiffness": 160.0,
  "transition_signature": "fade_black|fade|slide_left|clip_wipe|dissolve",
  "typography_style": "bold_modern|elegant_thin|geometric|editorial",
  "font_primary": "string com font stack CSS",
  "font_display": "string com font stack CSS",
  "font_weight_display": 800,
  "letter_spacing": -2.0,
  "composition_rule": "center_dominant|rule_of_thirds|dynamic_asymmetry",
  "cinematic_mood": "professional|luxury|energetic|minimal|dramatic",
  "extracted_from": "descrição de 1 linha do que foi analisado"
}}"""

        try:
            response = self.vision_client.complete(prompt, images=[image_b64])
            json_str = _extract_json(response)
            data = json.loads(json_str)
            dna = VisualDNA.from_dict(data)
            dna.confidence = 0.9
            self._dna = dna
            return dna
        except Exception as e:
            # Fallback: tenta extrair cores básicas do texto da resposta
            return self._fallback_dna(manual_description, str(e))

    def extract_from_description(self, description: str) -> VisualDNA:
        """Extrai DNA apenas de texto (sem imagem)."""
        prompt = f"""Você é um diretor de arte de motion design.
Com base nesta descrição de projeto, defina a identidade visual completa:

"{description}"

Responda com JSON válido (sem markdown):
{{
  "palette": ["#hex1", "#hex2", "#hex3"],
  "primary_color": "#hex",
  "accent_color": "#hex",
  "background_color": "#hex",
  "text_color": "#hex",
  "lighting_style": "cinematic_soft|high_contrast|backlit|flat|neon",
  "contrast_profile": "dark_rich|bright_clean|moody|pastel",
  "glow_color": "#hex",
  "motion_signature": "spring_organic|linear_precise|bouncy_playful|cinematic_slow",
  "camera_language": "luxury_archviz|commercial_clean|editorial|documentary",
  "spring_damping": 14.0,
  "spring_stiffness": 160.0,
  "transition_signature": "fade_black|fade|dissolve",
  "typography_style": "bold_modern|elegant_thin|geometric|editorial",
  "font_primary": "'Helvetica Neue', Arial, sans-serif",
  "font_display": "'Helvetica Neue', 'Arial Black', sans-serif",
  "font_weight_display": 800,
  "letter_spacing": -2.0,
  "composition_rule": "center_dominant|rule_of_thirds|dynamic_asymmetry",
  "cinematic_mood": "professional|luxury|energetic|minimal|dramatic",
  "extracted_from": "descrição de 1 linha"
}}"""
        try:
            response = self.vision_client.complete(prompt)
            json_str = _extract_json(response)
            data = json.loads(json_str)
            dna = VisualDNA.from_dict(data)
            dna.confidence = 0.7
            self._dna = dna
            return dna
        except Exception:
            return self._fallback_dna(description)

    def _fallback_dna(self, description: str = "", error: str = "") -> VisualDNA:
        """DNA padrão quando a extração falha."""
        # Tenta detectar mood pelo texto
        desc_lower = description.lower()
        if any(w in desc_lower for w in ["luxury", "luxo", "premium", "elegant"]):
            dna = VisualDNA(
                palette=["#0a0a0a", "#ffffff", "#d4af37"],
                primary_color="#d4af37",
                accent_color="#ffffff",
                background_color="#0a0a0a",
                lighting_style="cinematic_soft",
                cinematic_mood="luxury",
                motion_signature="cinematic_slow",
                camera_language="luxury_archviz",
                typography_style="elegant_thin",
            )
        elif any(w in desc_lower for w in ["energy", "energia", "esport", "gaming", "sport"]):
            dna = VisualDNA(
                palette=["#0d0d1a", "#7b2fff", "#00f0ff"],
                primary_color="#7b2fff",
                accent_color="#00f0ff",
                background_color="#0d0d1a",
                lighting_style="neon",
                cinematic_mood="energetic",
                motion_signature="bouncy_playful",
                camera_language="editorial",
                typography_style="bold_modern",
            )
        elif any(w in desc_lower for w in ["minimal", "clean", "white", "branco"]):
            dna = VisualDNA(
                palette=["#ffffff", "#0a0a0a", "#6c63ff"],
                primary_color="#6c63ff",
                accent_color="#0a0a0a",
                background_color="#ffffff",
                text_color="#0a0a0a",
                lighting_style="flat",
                contrast_profile="bright_clean",
                cinematic_mood="minimal",
                motion_signature="linear_precise",
                typography_style="geometric",
            )
        else:
            dna = VisualDNA()

        dna.extracted_from = description[:80] if description else "fallback_default"
        dna.confidence = 0.4
        self._dna = dna
        return dna


def _extract_json(text: str) -> str:
    """Extrai JSON de uma resposta que pode conter markdown."""
    # Tenta bloco de código
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    # Tenta primeiro { ... }
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return m.group(1)
    return text.strip()
