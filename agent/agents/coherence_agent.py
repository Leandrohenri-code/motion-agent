"""
Coherence Agent — V2.

Verifica e CORRIGE coerência visual entre DSLs de cenas.
Opera diretamente no JSON do SceneDSL, sem precisar de LLM para patches simples.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_client import AIClient
    from visual_dna import VisualDNA
    from scene_dsl import SceneDSL


@dataclass
class CoherenceIssue:
    severity: str          # "critical", "warning", "info"
    scene: int
    field: str             # ex: "environment.background", "typography.color"
    description: str
    auto_fixable: bool
    fix_value: Optional[str] = None


@dataclass
class CoherenceReport:
    score: float           # 0-10
    issues: List[CoherenceIssue] = field(default_factory=list)
    patches_applied: int = 0
    summary: str = ""


class CoherenceAgent:
    """
    Verifica coerência entre cenas e aplica patches automáticos no DSL.
    """

    def __init__(self, client: Optional["AIClient"] = None):
        self.client = client   # opcional, para análise semântica

    def check_and_repair(
        self,
        scenes: List["SceneDSL"],
        dna: "VisualDNA",
    ) -> CoherenceReport:
        """
        Verifica coerência entre todas as cenas e corrige automaticamente.
        Retorna relatório com score e patches aplicados.
        """
        report = CoherenceReport(score=10.0)
        issues = []

        for i, scene in enumerate(scenes):
            scene_issues = self._check_scene(scene, dna, i, scenes)
            issues.extend(scene_issues)

        # Aplica patches automáticos
        patches = 0
        for issue in issues:
            if issue.auto_fixable and issue.fix_value is not None:
                if self._apply_patch(scenes[issue.scene - 1], issue):
                    patches += 1
                    issue.auto_fixable = False  # marca como corrigido

        report.patches_applied = patches

        # Calcula score
        critical = sum(1 for i in issues if i.severity == "critical")
        warnings = sum(1 for i in issues if i.severity == "warning")
        remaining_critical = sum(1 for i in issues if i.severity == "critical" and i.auto_fixable)

        score = 10.0
        score -= remaining_critical * 1.5
        score -= warnings * 0.3
        report.score = max(0.0, min(10.0, score))
        report.issues = issues

        issue_count = len([i for i in issues if i.auto_fixable])
        report.summary = (
            f"Score: {report.score:.1f}/10 | "
            f"Patches: {patches} | "
            f"Issues restantes: {issue_count}"
        )

        return report

    def _check_scene(
        self,
        scene: "SceneDSL",
        dna: "VisualDNA",
        scene_index: int,
        all_scenes: List["SceneDSL"],
    ) -> List[CoherenceIssue]:
        issues = []
        scene_num = scene.scene_id

        # 1. Verifica paleta de cores
        dna_palette_lower = [c.lower() for c in dna.palette]
        for el in scene.text_elements:
            color = el.typography.color.lower()
            if color not in dna_palette_lower and not _is_close_color(color, dna.palette):
                issues.append(CoherenceIssue(
                    severity="warning",
                    scene=scene_num,
                    field=f"text_elements[{el.id}].typography.color",
                    description=f"Cor '{color}' fora da paleta DNA",
                    auto_fixable=True,
                    fix_value=dna.text_color if hasattr(dna, 'text_color') else "#ffffff",
                ))

        # 2. Verifica background coerente
        bg = scene.environment.background
        if bg and bg.startswith("#"):
            if bg.lower() not in dna_palette_lower and not _is_close_color(bg, dna.palette):
                issues.append(CoherenceIssue(
                    severity="warning",
                    scene=scene_num,
                    field="environment.background",
                    description=f"Background '{bg}' diverge do DNA",
                    auto_fixable=True,
                    fix_value=dna.background_color if hasattr(dna, 'background_color') else "#0a0a0a",
                ))

        # 3. Verifica continuidade de transição entre cenas
        if scene_index > 0:
            prev = all_scenes[scene_index - 1]
            prev_out = prev.transition_out.type if prev.transition_out else "fade"
            curr_in = scene.transition_in.type if scene.transition_in else None

            if curr_in and curr_in != prev_out:
                issues.append(CoherenceIssue(
                    severity="critical",
                    scene=scene_num,
                    field="transition_in.type",
                    description=f"Transição in '{curr_in}' não combina com out da cena anterior '{prev_out}'",
                    auto_fixable=True,
                    fix_value=prev_out,
                ))

        # 4. Verifica spring physics
        cam_motion = scene.camera.motion
        if cam_motion.easing == "spring":
            if abs(cam_motion.damping - dna.spring_damping) > 3.0:
                issues.append(CoherenceIssue(
                    severity="warning",
                    scene=scene_num,
                    field="camera.motion.damping",
                    description=f"Spring damping {cam_motion.damping} diverge do DNA ({dna.spring_damping})",
                    auto_fixable=True,
                    fix_value=str(dna.spring_damping),
                ))

        # 5. Verifica tamanho de fonte (consistência)
        headlines = [el for el in scene.text_elements if el.role == "headline"]
        for el in headlines:
            if el.typography.font_size < 40 or el.typography.font_size > 200:
                issues.append(CoherenceIssue(
                    severity="info",
                    scene=scene_num,
                    field=f"text_elements[{el.id}].typography.font_size",
                    description=f"Font size {el.typography.font_size}px parece inadequado para headline",
                    auto_fixable=False,
                ))

        return issues

    def _apply_patch(self, scene: "SceneDSL", issue: CoherenceIssue) -> bool:
        """Aplica um patch de campo simples no SceneDSL."""
        try:
            parts = issue.field.split(".")

            if parts[0] == "environment" and len(parts) == 2:
                setattr(scene.environment, parts[1], issue.fix_value)
                return True

            if parts[0] == "transition_in" and len(parts) == 2:
                if scene.transition_in:
                    setattr(scene.transition_in, parts[1], issue.fix_value)
                return True

            if parts[0] == "camera" and len(parts) == 3:
                # camera.motion.damping → scene.camera.motion.damping
                obj = scene.camera
                for p in parts[1:-1]:
                    obj = getattr(obj, p)
                val = float(issue.fix_value) if issue.fix_value.replace('.','').isdigit() else issue.fix_value
                setattr(obj, parts[-1], val)
                return True

            # text_elements[id].typography.color
            if parts[0].startswith("text_elements[") and len(parts) >= 3:
                el_id = parts[0][len("text_elements["):-1]
                for el in scene.text_elements:
                    if el.id == el_id:
                        sub = getattr(el, parts[1])
                        setattr(sub, parts[2], issue.fix_value)
                        return True

            return False
        except Exception:
            return False

    def summarize_for_log(self, report: CoherenceReport) -> List[str]:
        """Retorna linhas para o log do agente."""
        lines = [f"Coerência: {report.score:.1f}/10 — {report.patches_applied} patches aplicados"]
        for issue in report.issues[:5]:
            status = "✓ corrigido" if not issue.auto_fixable else "⚠ pendente"
            lines.append(f"  [{issue.severity}] Cena {issue.scene}: {issue.description} — {status}")
        return lines


def _is_close_color(color: str, palette: List[str], threshold: int = 30) -> bool:
    """Verifica se uma cor está próxima de alguma cor da paleta."""
    try:
        r1, g1, b1 = _hex_to_rgb(color)
        for p in palette:
            try:
                r2, g2, b2 = _hex_to_rgb(p)
                if abs(r1-r2) + abs(g1-g2) + abs(b1-b2) < threshold:
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
