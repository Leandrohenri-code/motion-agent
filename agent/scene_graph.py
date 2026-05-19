"""
SceneGraph — Representação determinística e imutável de um frame.

AUTORIDADE MÁXIMA do sistema. O LLM nunca sobrescreve este dado.
Extração via CV/vision LLM. Geometria = verdade.

Hierarquia de autoridade:
  1. SceneGraph          ← aqui (máximo)
  2. CompositionConstraints
  3. CinematicRuntime
  4. MotionDSL
  5. LLM suggestions     (mínimo)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
import json


@dataclass
class BBox:
    """Bounding box normalizada (0–1 relativo ao frame)."""
    x: float       # esquerda
    y: float       # topo
    width: float
    height: float

    @property
    def cx(self) -> float:
        return self.x + self.width / 2

    @property
    def cy(self) -> float:
        return self.y + self.height / 2

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, d: dict) -> "BBox":
        return cls(
            x=float(d.get("x", 0)),
            y=float(d.get("y", 0)),
            width=float(d.get("width", 1)),
            height=float(d.get("height", 1)),
        )


@dataclass
class SceneLayer:
    """
    Uma camada extraída do frame.

    LOCKED: posição e geometria são imutáveis.
    O runtime usa depth e parallax_sensitivity para criar ilusão de profundidade
    sem mover fisicamente o elemento — apenas offset de câmera diferencial.
    """
    id: str
    label: str                      # nome descritivo: "kitchen_island", "person_right"
    bbox: BBox                      # posição no frame (normalizada)
    depth: float                    # 0.0 = foreground, 1.0 = background
    depth_layer: int                # 0=foreground, 1=midground, 2=background
    parallax_sensitivity: float     # quanto se move em relação à câmera (0–1)
    motion_allowance: float         # deslocamento máximo permitido em px (para animações)
    importance: str                 # "primary" | "secondary" | "background"
    locked: bool = True             # SEMPRE True — nunca pode ser alterado pelo LLM

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "bbox": self.bbox.to_dict(),
            "depth": self.depth,
            "depth_layer": self.depth_layer,
            "parallax_sensitivity": self.parallax_sensitivity,
            "motion_allowance": self.motion_allowance,
            "importance": self.importance,
            "locked": self.locked,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SceneLayer":
        return cls(
            id=d.get("id", "layer_unknown"),
            label=d.get("label", "element"),
            bbox=BBox.from_dict(d.get("bbox", {})),
            depth=float(d.get("depth", 0.5)),
            depth_layer=int(d.get("depth_layer", 1)),
            parallax_sensitivity=float(d.get("parallax_sensitivity", 0.1)),
            motion_allowance=float(d.get("motion_allowance", 8.0)),
            importance=d.get("importance", "secondary"),
            locked=True,   # forçado sempre
        )


@dataclass
class SceneGraph:
    """
    Representação geométrica e estrutural completa de um frame.

    IMUTÁVEL. Construído uma vez via CV/vision. Nunca alterado.
    É a fonte absoluta da verdade para composição, geometria e layout.

    O runtime usa este dado para:
      - Renderizar background_plate (frame original)
      - Criar parallax diferencial por layer (depth-based)
      - Preservar composição exata durante toda a animação
    """
    background_plate: str           # base64 data URL do frame original
    frame_width: int = 1920
    frame_height: int = 1080
    layers: List[SceneLayer] = field(default_factory=list)
    horizon_y: float = 0.5          # linha do horizonte (0–1)
    vanishing_point_x: float = 0.5  # ponto de fuga
    composition_style: str = "centered"
    color_temperature: str = "neutral"
    depth_cues: List[str] = field(default_factory=list)
    primary_subject_bbox: Optional[BBox] = None

    # ── Camadas por profundidade (para parallax rendering) ────────────────
    @property
    def foreground_layers(self) -> List[SceneLayer]:
        return [l for l in self.layers if l.depth_layer == 0]

    @property
    def midground_layers(self) -> List[SceneLayer]:
        return [l for l in self.layers if l.depth_layer == 1]

    @property
    def background_layers(self) -> List[SceneLayer]:
        return [l for l in self.layers if l.depth_layer == 2]

    def to_dict(self) -> dict:
        d = {
            "background_plate": self.background_plate,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "layers": [l.to_dict() for l in self.layers],
            "horizon_y": self.horizon_y,
            "vanishing_point_x": self.vanishing_point_x,
            "composition_style": self.composition_style,
            "color_temperature": self.color_temperature,
            "depth_cues": self.depth_cues,
        }
        if self.primary_subject_bbox:
            d["primary_subject_bbox"] = self.primary_subject_bbox.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "SceneGraph":
        layers = [SceneLayer.from_dict(l) for l in d.get("layers", [])]
        psb = d.get("primary_subject_bbox")
        return cls(
            background_plate=d.get("background_plate", ""),
            frame_width=int(d.get("frame_width", 1920)),
            frame_height=int(d.get("frame_height", 1080)),
            layers=layers,
            horizon_y=float(d.get("horizon_y", 0.5)),
            vanishing_point_x=float(d.get("vanishing_point_x", 0.5)),
            composition_style=d.get("composition_style", "centered"),
            color_temperature=d.get("color_temperature", "neutral"),
            depth_cues=d.get("depth_cues", []),
            primary_subject_bbox=BBox.from_dict(psb) if psb else None,
        )

    def to_prompt_description(self) -> str:
        """
        Serializa para texto para injeção no prompt do Motion Planner.
        NÃO expõe background_plate (base64) — apenas metadados geométricos.
        """
        lines = [
            "=== SCENE GRAPH (IMUTÁVEL — NÃO ALTERE) ===",
            f"Composição: {self.composition_style} | Temp. cor: {self.color_temperature}",
            f"Horizonte: y={self.horizon_y:.2f} | Fuga: x={self.vanishing_point_x:.2f}",
            f"Total de camadas: {len(self.layers)}",
        ]
        if self.depth_cues:
            lines.append(f"Indicadores de profundidade: {', '.join(self.depth_cues)}")
        if self.layers:
            lines.append("Camadas (LOCKED):")
            for l in self.layers:
                depth_str = ["FOREGROUND", "MIDGROUND", "BACKGROUND"][min(l.depth_layer, 2)]
                lines.append(
                    f"  [{depth_str}] {l.label}: "
                    f"pos=({l.bbox.cx:.2f},{l.bbox.cy:.2f}) "
                    f"size=({l.bbox.width:.2f}×{l.bbox.height:.2f}) "
                    f"depth={l.depth:.2f} parallax={l.parallax_sensitivity:.2f}"
                )
        lines.append("===========================================")
        return "\n".join(lines)
