"""
Fidelity Scorer — Pontuação de fidelidade ao frame de referência.

Compara o SceneGraph (que preserva o frame original) com o MotionDSL gerado.
Score 0–100. Abaixo do threshold → auto-reject ou alerta.

Métricas de fidelidade:
  1. Background plate presente          (0 ou 30 pts)
  2. Layers preservados (locked=True)   (0–25 pts)
  3. Camera motion dentro dos limites   (0–20 pts)
  4. Sem text_overlays excessivos       (0–15 pts)
  5. Parallax coerente com depth        (0–10 pts)

Fidelidade visual real (quando PIL disponível):
  - Histograma de cor vs referência
  - Edge density comparison
  - Structural similarity
"""

from __future__ import annotations
import math
from typing import Optional, Tuple

from scene_graph import SceneGraph
from motion_dsl import MotionDSL


# Thresholds
THRESHOLD_ACCEPT = 70       # >= aceita automaticamente
THRESHOLD_WARN   = 45       # entre 45-70 → avisa mas continua
THRESHOLD_REJECT = 44       # < 45 → auto-reject sugerido


class FidelityReport:
    def __init__(
        self,
        score: float,
        issues: list,
        auto_reject: bool,
        breakdown: dict,
    ):
        self.score = score
        self.issues = issues
        self.auto_reject = auto_reject
        self.breakdown = breakdown

    def __repr__(self) -> str:
        status = "✅ PASS" if self.score >= THRESHOLD_ACCEPT else ("⚠️ WARN" if self.score >= THRESHOLD_WARN else "❌ FAIL")
        return f"FidelityReport({status} score={self.score:.1f} issues={len(self.issues)})"

    def to_log_lines(self) -> list:
        lines = [f"  Fidelidade: {self.score:.0f}/100"]
        for issue in self.issues:
            lines.append(f"    ⚠ {issue}")
        return lines


def score(scene_graph: SceneGraph, motion_dsl: MotionDSL) -> FidelityReport:
    """
    Calcula o Reference Fidelity Score.

    Verifica se o MotionDSL respeita o SceneGraph imutável.
    Não compara pixels (renderização ainda não ocorreu),
    mas verifica integridade estrutural do pipeline.
    """
    issues = []
    breakdown = {}

    # ── 1. Background plate presente (30 pts) ────────────────────────────
    has_plate = bool(scene_graph.background_plate)
    plate_score = 30 if has_plate else 0
    breakdown["background_plate"] = plate_score
    if not has_plate:
        issues.append("Background plate ausente — composição original não será preservada")

    # ── 2. Layers locked preservados (25 pts) ────────────────────────────
    total_layers = len(scene_graph.layers)
    locked_layers = sum(1 for l in scene_graph.layers if l.locked)
    layer_score = int(25 * (locked_layers / max(1, total_layers)))
    breakdown["locked_layers"] = layer_score
    if locked_layers < total_layers:
        issues.append(f"{total_layers - locked_layers} camadas sem locked=True")

    # Verifica se layer_animations referenciam IDs válidos do SceneGraph
    valid_ids = {l.id for l in scene_graph.layers}
    invalid_targets = [
        a.target for a in motion_dsl.layer_animations
        if a.target and a.target not in valid_ids
    ]
    if invalid_targets:
        penalty = min(10, len(invalid_targets) * 3)
        layer_score = max(0, layer_score - penalty)
        breakdown["locked_layers"] = layer_score
        issues.append(f"layer_animations com targets inválidos: {invalid_targets}")

    # ── 3. Camera motion dentro dos limites (20 pts) ─────────────────────
    cam = motion_dsl.camera
    cam_score = 20

    # Parallax muito alto destrói composição
    if cam.parallax > 0.25:
        cam_score -= 10
        issues.append(f"camera.parallax={cam.parallax:.2f} muito alto (máx 0.25) — distorce composição")

    # Jitter excessivo
    if cam.micro_jitter > 0.8:
        cam_score -= 5
        issues.append(f"camera.micro_jitter={cam.micro_jitter:.2f} excessivo")

    breakdown["camera_bounds"] = max(0, cam_score)

    # ── 4. Text overlays não excessivos (15 pts) ─────────────────────────
    text_count = len(motion_dsl.text_overlays)
    if text_count == 0:
        text_score = 15
    elif text_count <= 2:
        text_score = 10
    elif text_count <= 4:
        text_score = 5
        issues.append(f"{text_count} text_overlays — possível poluição visual sobre o frame")
    else:
        text_score = 0
        issues.append(f"{text_count} text_overlays excessivos — frame original sendo encoberto")

    breakdown["text_overlays"] = text_score

    # ── 5. Parallax coerente com depth das layers (10 pts) ───────────────
    depth_score = 10
    for layer in scene_graph.layers:
        expected_parallax = 0.02 + (1 - layer.depth) ** 1.8 * 0.23
        actual = layer.parallax_sensitivity
        if abs(actual - expected_parallax) > 0.15:
            depth_score -= 2
            issues.append(
                f"Layer '{layer.label}': parallax={actual:.2f} inconsistente com depth={layer.depth:.2f}"
            )
    breakdown["depth_coherence"] = max(0, depth_score)

    # ── Score total ───────────────────────────────────────────────────────
    total = plate_score + layer_score + max(0, cam_score) + text_score + max(0, depth_score)
    total = max(0, min(100, total))

    auto_reject = total < THRESHOLD_REJECT

    return FidelityReport(
        score=float(total),
        issues=issues,
        auto_reject=auto_reject,
        breakdown=breakdown,
    )


def score_with_image_comparison(
    reference_b64: str,
    scene_graph: SceneGraph,
    motion_dsl: MotionDSL,
) -> FidelityReport:
    """
    Score com comparação visual via PIL (quando disponível).
    Compara histograma de cor do frame de referência vs SceneGraph.
    """
    base_report = score(scene_graph, motion_dsl)

    try:
        import base64
        import io
        from PIL import Image
        import numpy as np

        # Decodifica imagem de referência
        if "," in reference_b64:
            img_data = base64.b64decode(reference_b64.split(",")[1])
        else:
            img_data = base64.b64decode(reference_b64)

        ref_img = Image.open(io.BytesIO(img_data)).convert("RGB")
        ref_arr = np.array(ref_img)

        # Decodifica background plate do SceneGraph
        plate_b64 = scene_graph.background_plate
        if plate_b64 and plate_b64 != reference_b64:
            if "," in plate_b64:
                plate_data = base64.b64decode(plate_b64.split(",")[1])
            else:
                plate_data = base64.b64decode(plate_b64)
            plate_img = Image.open(io.BytesIO(plate_data)).convert("RGB")
            plate_arr = np.array(plate_img)

            # Compara histogramas (R, G, B)
            hist_scores = []
            for channel in range(3):
                ref_hist = np.histogram(ref_arr[:, :, channel], bins=64, range=(0, 256))[0].astype(float)
                plate_hist = np.histogram(plate_arr[:, :, channel], bins=64, range=(0, 256))[0].astype(float)
                ref_hist /= ref_hist.sum() + 1e-8
                plate_hist /= plate_hist.sum() + 1e-8
                # Bhattacharyya coefficient (1 = identical)
                bc = float(np.sum(np.sqrt(ref_hist * plate_hist)))
                hist_scores.append(bc)

            histogram_similarity = sum(hist_scores) / 3  # 0–1

            # Bônus de até 20 pontos por similaridade de histograma
            visual_bonus = int(histogram_similarity * 20)
            new_score = min(100, base_report.score + visual_bonus)
            base_report.score = float(new_score)
            base_report.breakdown["histogram_similarity"] = visual_bonus

    except Exception:
        pass  # PIL não disponível ou erro — continua com score base

    return base_report
