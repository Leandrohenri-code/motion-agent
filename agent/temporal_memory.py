"""
Temporal Memory — Memória Hierárquica do Agente.

3 camadas de memória para coerência cinematográfica:
  - Short-term:  última cena (detalhes exatos)
  - Mid-term:    sequência atual (padrões emergentes)
  - Long-term:   Visual DNA + assinaturas globais
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from visual_dna import VisualDNA


@dataclass
class SceneMemory:
    """Snapshot de uma cena para memória temporal."""
    scene_num: int
    description: str
    duration_frames: int

    # Elementos DSL extraídos
    text_elements: List[str] = field(default_factory=list)    # textos principais
    camera_motion: str = "static"
    dominant_colors: List[str] = field(default_factory=list)
    enter_animations: List[str] = field(default_factory=list)
    exit_animations: List[str] = field(default_factory=list)
    transition_out: str = "fade"

    # DSL bruto
    dsl_json: str = ""

    def brief(self) -> str:
        """Resumo curto para o prompt."""
        texts = ", ".join(f'"{t}"' for t in self.text_elements[:3])
        return (
            f"Cena {self.scene_num}: {self.description[:60]} | "
            f"Câmera: {self.camera_motion} | Textos: [{texts}] | "
            f"Saída: {self.transition_out}"
        )


class TemporalMemory:
    """
    Memória hierárquica do agente de motion design.

    SHORT-TERM:  última cena (máximo detalhe)
    MID-TERM:    últimas N cenas (tendências e padrões)
    LONG-TERM:   Visual DNA + regras globais (nunca apagado)
    """

    def __init__(self, dna: Optional[VisualDNA] = None, mid_term_size: int = 5):
        self._short_term: Optional[SceneMemory] = None
        self._mid_term: List[SceneMemory] = []
        self._mid_term_size = mid_term_size
        self._long_term_dna: VisualDNA = dna or VisualDNA()

        # Padrões emergentes detectados no mid-term
        self._camera_sequence: List[str] = []
        self._dominant_motion: str = "spring_organic"
        self._color_usage: Dict[str, int] = {}

    # ── Propriedades ─────────────────────────────────────────────────────────

    @property
    def dna(self) -> VisualDNA:
        return self._long_term_dna

    @dna.setter
    def dna(self, value: VisualDNA):
        self._long_term_dna = value

    @property
    def short_term(self) -> Optional[SceneMemory]:
        return self._short_term

    @property
    def mid_term(self) -> List[SceneMemory]:
        return list(self._mid_term)

    @property
    def scene_count(self) -> int:
        if not self._mid_term and not self._short_term:
            return 0
        if self._mid_term:
            return self._mid_term[-1].scene_num
        return self._short_term.scene_num if self._short_term else 0

    # ── Atualização ──────────────────────────────────────────────────────────

    def record_scene(self, scene_num: int, dsl_dict: dict, frame: dict):
        """Registra uma cena na memória após geração."""
        mem = self._extract_scene_memory(scene_num, dsl_dict, frame)

        # Atualiza short-term
        self._short_term = mem

        # Atualiza mid-term (FIFO)
        self._mid_term.append(mem)
        if len(self._mid_term) > self._mid_term_size:
            self._mid_term.pop(0)

        # Atualiza padrões mid-term
        self._update_patterns(mem)

    def _extract_scene_memory(self, scene_num: int, dsl_dict: dict, frame: dict) -> SceneMemory:
        """Extrai SceneMemory de um dicionário DSL."""
        mem = SceneMemory(
            scene_num=scene_num,
            description=frame.get("description", "")[:120],
            duration_frames=dsl_dict.get("duration", 90),
        )

        # Câmera
        camera = dsl_dict.get("camera", {})
        motion = camera.get("motion", {}) if isinstance(camera, dict) else {}
        mem.camera_motion = motion.get("type", "static") if isinstance(motion, dict) else "static"

        # Cores do ambiente
        env = dsl_dict.get("environment", {})
        if isinstance(env, dict):
            bg = env.get("background", "")
            if bg and bg.startswith("#"):
                mem.dominant_colors.append(bg)
            glow = env.get("glow_color", "")
            if glow and glow.startswith("#"):
                mem.dominant_colors.append(glow)

        # Textos
        for el in dsl_dict.get("text_elements", []):
            if isinstance(el, dict) and el.get("text"):
                mem.text_elements.append(el["text"][:40])

        # Animações de entrada/saída
        for el in dsl_dict.get("text_elements", []) + dsl_dict.get("shape_elements", []):
            if isinstance(el, dict):
                anim = el.get("animation", {})
                if isinstance(anim, dict):
                    if anim.get("enter_type"):
                        mem.enter_animations.append(anim["enter_type"])
                    if anim.get("exit_type"):
                        mem.exit_animations.append(anim["exit_type"])

        # Transição de saída
        trans_out = dsl_dict.get("transition_out", {})
        if isinstance(trans_out, dict):
            mem.transition_out = trans_out.get("type", "fade")

        return mem

    def _update_patterns(self, mem: SceneMemory):
        """Atualiza padrões emergentes."""
        self._camera_sequence.append(mem.camera_motion)
        if len(self._camera_sequence) > self._mid_term_size:
            self._camera_sequence.pop(0)

        for color in mem.dominant_colors:
            self._color_usage[color] = self._color_usage.get(color, 0) + 1

    # ── Consulta para o Prompt ────────────────────────────────────────────────

    def to_prompt_section(self, next_frame: Optional[dict] = None) -> str:
        """Serializa a memória para injeção no prompt de geração."""
        parts = []

        # Long-term: DNA
        parts.append(self._long_term_dna.to_prompt_section())
        parts.append("")

        # Mid-term: histórico de cenas
        if self._mid_term:
            parts.append("=== MEMÓRIA MID-TERM — HISTÓRICO DE CENAS ===")
            for m in self._mid_term:
                parts.append(f"  • {m.brief()}")

            # Padrões detectados
            if self._camera_sequence:
                cam_pattern = " → ".join(self._camera_sequence[-4:])
                parts.append(f"Sequência de câmera atual: {cam_pattern}")
            parts.append("")

        # Short-term: última cena
        if self._short_term:
            st = self._short_term
            parts.append("=== MEMÓRIA SHORT-TERM — CENA ANTERIOR (EXATA) ===")
            parts.append(f"Última cena: #{st.scene_num} — {st.description[:80]}")
            parts.append(f"Câmera usada: {st.camera_motion}")
            if st.text_elements:
                parts.append(f"Últimos textos: {', '.join(st.text_elements[:2])}")
            parts.append(f"Transição de saída: {st.transition_out}")
            parts.append("")
            parts.append("CONTINUIDADE OBRIGATÓRIA:")
            parts.append(f"  → Transition_in desta cena deve ser '{st.transition_out}'")
            parts.append(f"  → Mantenha a evolução da câmera (evite repetir '{st.camera_motion}' imediatamente)")

        # Próxima cena (lookahead)
        if next_frame:
            next_desc = next_frame.get("description", "")[:80]
            if next_desc:
                parts.append("")
                parts.append(f"=== LOOKAHEAD — PRÓXIMA CENA ===")
                parts.append(f"Próxima cena: {next_desc}")
                parts.append("→ Prepare uma transição de saída coerente com o que vem depois")

        return "\n".join(parts)

    def get_continuity_constraints(self) -> dict:
        """Retorna constraints de continuidade para o DSL Generator."""
        constraints = {
            "palette": self._long_term_dna.palette,
            "avoid_camera": self._short_term.camera_motion if self._short_term else None,
            "transition_in": self._short_term.transition_out if self._short_term else "fade",
            "spring_damping": self._long_term_dna.spring_damping,
            "spring_stiffness": self._long_term_dna.spring_stiffness,
        }
        return constraints
