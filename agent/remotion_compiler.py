"""
Remotion Compiler — Compilação determinística para TSX.

Dois modos de compilação:
  1. compile(SceneDSL)                → MotionRuntime (modo legado / criativo)
  2. compile_cinematic(SceneGraph, MotionDSL) → CinematicRuntime (modo determinístico)

No modo CinematicRuntime:
  - Composição vem do SceneGraph (extraído por CV) — IMUTÁVEL
  - Movimento vem do MotionDSL (planejado pelo LLM) — apenas animação
  - TSX é 100% determinístico — mesmo SceneGraph = mesma composição garantida
"""

from __future__ import annotations
import json
import os
from typing import List, Optional
from scene_dsl import (
    SceneDSL, TextElement, ImageElement, ShapeElement,
    ParticleField, ElementAnimation, MotionProfile, Position, Typography
)

# Importação condicional para não quebrar quando usado sem novos módulos
try:
    from scene_graph import SceneGraph
    from motion_dsl import MotionDSL
    _CINEMATIC_AVAILABLE = True
except ImportError:
    _CINEMATIC_AVAILABLE = False


class RemotionCompiler:
    """
    Compila SceneDSL → TSX genérico para o Remotion Runtime.
    """

    def compile(self, dsl: SceneDSL) -> str:
        """
        Compila um SceneDSL para TSX.
        Returns: string TSX pronta para salvar como SceneXX.tsx
        """
        # Serializa DSL para injetar como constante JSON no TSX
        dsl_json = json.dumps(dsl.to_dict(), indent=2, ensure_ascii=False)

        tsx = self._render_tsx(dsl, dsl_json)
        return tsx

    def compile_to_file(self, dsl: SceneDSL, output_path: str) -> str:
        """Compila e salva o TSX. Retorna o caminho do arquivo."""
        code = self.compile(dsl)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code)
        return output_path

    def _render_tsx(self, dsl: SceneDSL, dsl_json: str) -> str:
        """Renderiza o TSX completo."""

        imports = self._render_imports(dsl)
        dsl_const = self._render_dsl_const(dsl_json)
        component = self._render_component(dsl)

        return f"""{imports}

{dsl_const}

{component}
"""

    def _render_imports(self, dsl: SceneDSL) -> str:
        has_images = len(dsl.image_elements) > 0
        img_import = "\nimport { Img, staticFile } from 'remotion';" if has_images else ""

        return f"""import React from 'react';
import {{ AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Sequence }} from 'remotion';{img_import}
import {{ MotionRuntime }} from '../runtime/MotionRuntime';"""

    def _render_dsl_const(self, dsl_json: str) -> str:
        # Escapa backticks e $ no JSON para uso em template literals
        escaped = dsl_json.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        return f"""// ─── Scene DSL — gerado automaticamente pelo Motion Agent ───────────────────
// NÃO edite manualmente. Edite o DSL e recompile.
const SCENE_DSL = {dsl_json};
"""

    def _render_component(self, dsl: SceneDSL) -> str:
        scene_id = dsl.scene_id
        duration = dsl.duration
        desc = dsl.description[:60].replace('"', "'") if dsl.description else f"Scene {scene_id}"

        return f"""// Scene {scene_id}: {desc}
export const Scene{scene_id:02d}: React.FC = () => {{
  return <MotionRuntime dsl={{SCENE_DSL}} />;
}};

export default Scene{scene_id:02d};
"""

    # ── Cinematic Runtime Compiler (Deterministic Pipeline) ─────────────────

    def compile_cinematic(self, scene_graph: "SceneGraph", motion_dsl: "MotionDSL") -> str:
        """
        Compila SceneGraph + MotionDSL → TSX usando CinematicRuntime.

        GARANTIA:
          - Composição vem 100% do SceneGraph (imutável)
          - Movimento vem 100% do MotionDSL (sem autoridade visual)
          - O LLM nunca toca na composição
        """
        scene_id = motion_dsl.scene_id

        # Serializa os dois objetos como constantes JSON no TSX
        # O background_plate (base64) vai dentro do SceneGraph
        graph_json = json.dumps(scene_graph.to_dict(), ensure_ascii=True)
        motion_json = json.dumps(motion_dsl.to_dict(), ensure_ascii=True)

        desc = (motion_dsl.description or f"Scene {scene_id}")[:60].replace('"', "'")

        return f"""import React from 'react';
import {{ CinematicRuntime }} from '../runtime/CinematicRuntime';

// ─── Deterministic Cinematic Scene — Motion Agent ────────────────────────────
// SCENE GRAPH: fonte absoluta da verdade — composição imutável
// MOTION DSL: metadata de movimento — planejado pelo LLM como motion operator
// NÃO edite manualmente. Recompile via Motion Agent.

// Scene {scene_id}: {desc}
const SCENE_GRAPH = {graph_json};

const MOTION_DSL = {motion_json};

export const Scene{scene_id:02d}: React.FC = () => (
  <CinematicRuntime graph={{SCENE_GRAPH}} motion={{MOTION_DSL}} />
);

export default Scene{scene_id:02d};
"""

    def ensure_cinematic_runtime(self, runtime_dir: str) -> str:
        """
        Instala o CinematicRuntime.tsx no projeto Remotion.
        Chamado uma vez antes da geração das cenas.
        """
        from utils.file_utils import write_text, ensure_dir
        ensure_dir(runtime_dir)
        runtime_path = os.path.join(runtime_dir, "CinematicRuntime.tsx")
        write_text(runtime_path, generate_cinematic_runtime())
        return runtime_path


# ── Runtime TSX Generator ─────────────────────────────────────────────────────

def generate_motion_runtime() -> str:
    """
    Gera o MotionRuntime.tsx — componente genérico que renderiza qualquer SceneDSL.
    Este arquivo vai em src/runtime/MotionRuntime.tsx no projeto Remotion.
    """
    return r"""import React, { useMemo } from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
  Img,
  staticFile,
} from 'remotion';

// ── Tipos DSL ──────────────────────────────────────────────────────────────

interface MotionProfile {
  type: string;
  velocity?: number;
  acceleration?: number;
  momentum?: number;
  easing?: string;
  intensity?: number;
  direction?: string;
  damping?: number;
  stiffness?: number;
}

interface ElementAnimation {
  enter_start?: number;
  enter_duration?: number;
  enter_type?: string;
  enter_easing?: string;
  exit_start?: number;
  exit_duration?: number;
  exit_type?: string;
  exit_easing?: string;
  idle_motion?: MotionProfile | null;
}

interface Position {
  x: number;
  y: number;
  z?: number;
  unit?: string;
}

interface Typography {
  font_family?: string;
  font_size?: number;
  font_weight?: number;
  letter_spacing?: number;
  line_height?: number;
  color?: string;
  text_transform?: string;
  text_shadow?: string;
  gradient?: string;
}

interface TextElement {
  id: string;
  text: string;
  role?: string;
  start?: number;
  duration?: number;
  position?: Position;
  typography?: Typography;
  animation?: ElementAnimation;
  max_width?: number;
  align?: string;
  word_stagger_delay?: number;
}

interface ShapeElement {
  id: string;
  shape?: string;
  start?: number;
  duration?: number;
  position?: Position;
  width?: number;
  height?: number;
  color?: string;
  opacity?: number;
  blur?: number;
  animation?: ElementAnimation;
  gradient?: string;
}

interface ImageElement {
  id: string;
  src: string;
  start?: number;
  duration?: number;
  position?: Position;
  scale?: { x?: number; y?: number };
  animation?: ElementAnimation;
  blur?: number;
  opacity?: number;
  blend_mode?: string;
  fit?: string;
}

interface ParticleField {
  id: string;
  count?: number;
  start?: number;
  duration?: number;
  color?: string;
  size_min?: number;
  size_max?: number;
  opacity_min?: number;
  opacity_max?: number;
  motion_type?: string;
  seed?: number;
}

interface SceneDSL {
  scene_id: number;
  duration: number;
  fps?: number;
  description?: string;
  visual_dna?: any;
  camera?: any;
  environment?: any;
  text_elements?: TextElement[];
  image_elements?: ImageElement[];
  shape_elements?: ShapeElement[];
  particle_fields?: ParticleField[];
  transition_in?: { type: string; duration: number } | null;
  transition_out?: { type: string; duration: number } | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

const useSpring = (frame: number, fps: number, damping = 14, stiffness = 160, delay = 0) => {
  const f = Math.max(0, frame - delay);
  return spring({ frame: f, fps, config: { damping, stiffness } });
};

const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);

const getProgress = (
  frame: number,
  start: number,
  duration: number,
  easing = 'easeOut',
  fps = 30,
  damping = 14,
  stiffness = 160,
): number => {
  if (frame < start) return 0;
  if (frame >= start + duration) return 1;
  const t = (frame - start) / duration;
  if (easing === 'spring') {
    return useSpring(frame - start, fps, damping, stiffness);
  }
  if (easing === 'easeOut') return easeOut(t);
  if (easing === 'easeIn') return Math.pow(t, 3);
  if (easing === 'easeInOut') {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }
  return t; // linear
};

const posToCSS = (pos?: Position, width = 1920, height = 1080): React.CSSProperties => {
  if (!pos) return { left: '50%', top: '50%', transform: 'translate(-50%,-50%)' };
  const unit = pos.unit || 'percent';
  if (unit === 'percent') {
    return {
      left: `${pos.x}%`,
      top: `${pos.y}%`,
      transform: 'translate(-50%,-50%)',
    };
  }
  return { left: pos.x, top: pos.y };
};

// ── Camera System ──────────────────────────────────────────────────────────

const useCameraTransform = (frame: number, fps: number, camera: any, duration: number): string => {
  if (!camera?.motion) return '';
  const { type, velocity = 0.3, intensity = 0.3, damping = 14, stiffness = 160 } = camera.motion;
  const progress = getProgress(frame, 0, duration, 'spring', fps, damping, stiffness);
  const v = velocity * intensity;

  switch (type) {
    case 'dolly_in':
      return `scale(${1 + progress * v})`;
    case 'dolly_out':
      return `scale(${1 + (1 - progress) * v})`;
    case 'pan_right':
      return `translateX(${-progress * v * 80}px)`;
    case 'pan_left':
      return `translateX(${progress * v * 80}px)`;
    case 'zoom':
      return `scale(${1 + progress * v * 0.8})`;
    case 'parallax':
      return `scale(1.08) translateX(${(progress - 0.5) * v * 40}px)`;
    case 'float': {
      const floatY = Math.sin(frame / fps * Math.PI * 0.5) * intensity * 15;
      return `translateY(${floatY}px)`;
    }
    case 'orbit': {
      const angle = (frame / duration) * Math.PI * 2;
      return `translateX(${Math.cos(angle) * intensity * 30}px) translateY(${Math.sin(angle) * intensity * 10}px)`;
    }
    case 'shake': {
      const sx = Math.sin(frame * 2.3) * intensity * 8;
      const sy = Math.cos(frame * 3.1) * intensity * 4;
      return `translate(${sx}px, ${sy}px)`;
    }
    default:
      return '';
  }
};

// ── Transition System ──────────────────────────────────────────────────────

const useTransitionStyle = (
  frame: number,
  duration: number,
  fps: number,
  transitionIn?: { type: string; duration: number } | null,
  transitionOut?: { type: string; duration: number } | null,
): React.CSSProperties => {
  const style: React.CSSProperties = {};
  const totalDuration = duration;

  if (transitionIn) {
    const { type, duration: td } = transitionIn;
    const p = getProgress(frame, 0, td, 'easeOut', fps);
    if (frame < td) {
      if (type === 'fade' || type === 'fade_black') {
        style.opacity = p;
      } else if (type === 'slide_left') {
        style.transform = `translateX(${(1 - p) * 100}%)`;
      } else if (type === 'slide_up') {
        style.transform = `translateY(${(1 - p) * 100}%)`;
      } else if (type === 'scale_out') {
        style.transform = `scale(${0.8 + p * 0.2})`;
        style.opacity = p;
      } else {
        style.opacity = p;
      }
    }
  }

  if (transitionOut) {
    const { type, duration: td } = transitionOut;
    const exitStart = totalDuration - td;
    if (frame >= exitStart) {
      const p = 1 - getProgress(frame, exitStart, td, 'easeIn', fps);
      if (type === 'fade' || type === 'fade_black') {
        style.opacity = (style.opacity as number ?? 1) * p;
      } else if (type === 'slide_left') {
        style.transform = `translateX(${-(1 - p) * 100}%)`;
      } else if (type === 'scale_out') {
        style.transform = `scale(${0.8 + p * 0.2})`;
        style.opacity = (style.opacity as number ?? 1) * p;
      } else {
        style.opacity = (style.opacity as number ?? 1) * p;
      }
    }
  }

  return style;
};

// ── Element Renderers ──────────────────────────────────────────────────────

const useElementAnimation = (
  frame: number,
  fps: number,
  duration: number,
  anim?: ElementAnimation,
  dna?: any,
): React.CSSProperties => {
  if (!anim) return {};
  const {
    enter_start = 0,
    enter_duration = 25,
    enter_type = 'fade_in',
    enter_easing = 'spring',
    exit_start: rawExit = -1,
    exit_duration = 18,
    exit_type = 'fade_out',
    exit_easing = 'easeIn',
  } = anim;

  const damping = dna?.visual_dna?.spring_damping ?? 14;
  const stiffness = dna?.visual_dna?.spring_stiffness ?? 160;

  const exitStart = rawExit === -1 ? duration - exit_duration : rawExit;
  const enterP = getProgress(frame, enter_start, enter_duration, enter_easing, fps, damping, stiffness);
  const exitP = frame >= exitStart
    ? 1 - getProgress(frame, exitStart, exit_duration, exit_easing, fps)
    : 1;

  const style: React.CSSProperties = {};

  // Enter
  switch (enter_type) {
    case 'fade_up':
      style.opacity = enterP;
      style.transform = `translateY(${(1 - enterP) * 40}px)`;
      break;
    case 'fade_in':
      style.opacity = enterP;
      break;
    case 'scale_in':
      style.opacity = enterP;
      style.transform = `scale(${0.7 + enterP * 0.3})`;
      break;
    case 'blur_in':
      style.opacity = enterP;
      style.filter = `blur(${(1 - enterP) * 20}px)`;
      break;
    case 'clip_left':
      style.clipPath = `inset(0 ${(1 - enterP) * 100}% 0 0)`;
      break;
    case 'word_stagger':
      // Handled by WordStagger component
      style.opacity = enterP;
      break;
    default:
      style.opacity = enterP;
  }

  // Exit
  if (frame >= exitStart) {
    switch (exit_type) {
      case 'fade_out':
        style.opacity = (style.opacity as number ?? 1) * exitP;
        break;
      case 'blur_out':
        style.opacity = (style.opacity as number ?? 1) * exitP;
        style.filter = `blur(${(1 - exitP) * 15}px)`;
        break;
      case 'scale_out':
        style.opacity = (style.opacity as number ?? 1) * exitP;
        style.transform = `${style.transform || ''} scale(${exitP})`;
        break;
      case 'slide_up':
        style.opacity = (style.opacity as number ?? 1) * exitP;
        style.transform = `${style.transform || ''} translateY(${(1 - exitP) * -40}px)`;
        break;
      case 'clip_right':
        style.clipPath = `inset(0 0 0 ${(1 - exitP) * 100}%)`;
        break;
      default:
        style.opacity = (style.opacity as number ?? 1) * exitP;
    }
  }

  return style;
};

// ── Shape Renderer ─────────────────────────────────────────────────────────

const ShapeRenderer: React.FC<{ el: ShapeElement; frame: number; fps: number; duration: number; dna: any }> = ({
  el, frame, fps, duration, dna,
}) => {
  const anim = useElementAnimation(frame, fps, duration, el.animation, dna);
  const pos = posToCSS(el.position);

  const bgStyle = el.gradient
    ? { background: el.gradient }
    : { backgroundColor: el.color || '#000000' };

  return (
    <div
      style={{
        position: 'absolute',
        width: el.width != null ? `${el.width}%` : '100%',
        height: el.height != null ? `${el.height}%` : '100%',
        ...pos,
        ...bgStyle,
        opacity: el.opacity ?? 1,
        filter: el.blur ? `blur(${el.blur}px)` : undefined,
        borderRadius: el.shape === 'circle' ? '50%' : el.shape === 'gradient_blob' ? '60% 40% 30% 70% / 60% 30% 70% 40%' : undefined,
        ...anim,
      }}
    />
  );
};

// ── Text Renderer ──────────────────────────────────────────────────────────

const TextRenderer: React.FC<{ el: TextElement; frame: number; fps: number; duration: number; dna: any }> = ({
  el, frame, fps, duration, dna,
}) => {
  const anim = useElementAnimation(frame, fps, duration, el.animation, dna);
  const pos = posToCSS(el.position);
  const typo = el.typography || {};

  const textStyle: React.CSSProperties = {
    fontFamily: typo.font_family || "'Helvetica Neue', Arial, sans-serif",
    fontSize: typo.font_size || 60,
    fontWeight: typo.font_weight || 800,
    letterSpacing: typo.letter_spacing != null ? `${typo.letter_spacing}px` : '-2px',
    lineHeight: typo.line_height || 1.15,
    color: typo.color || '#ffffff',
    textTransform: (typo.text_transform as any) || 'none',
    textShadow: typo.text_shadow || undefined,
    textAlign: (el.align as any) || 'center',
    maxWidth: el.max_width ? `${el.max_width}px` : '1600px',
    whiteSpace: 'pre-wrap',
    ...(typo.gradient ? {
      background: typo.gradient,
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
    } : {}),
  };

  return (
    <div
      style={{
        position: 'absolute',
        ...pos,
        ...anim,
      }}
    >
      <div style={textStyle}>{el.text}</div>
    </div>
  );
};

// ── Image Renderer ─────────────────────────────────────────────────────────

const ImageRenderer: React.FC<{ el: ImageElement; frame: number; fps: number; duration: number; dna: any }> = ({
  el, frame, fps, duration, dna,
}) => {
  const anim = useElementAnimation(frame, fps, duration, el.animation, dna);
  const pos = posToCSS(el.position);
  const src = el.src.startsWith('data:') ? el.src : staticFile(el.src);

  // ── Background Plate mode ──────────────────────────────────────────────────
  // Quando id === 'background_plate', renderiza como camada base bloqueada
  // com parallax sutil e nenhuma recomposição. A imagem é verdade absoluta.
  if (el.id === 'background_plate') {
    const progress = duration > 1 ? frame / (duration - 1) : 0;
    // Parallax horizontal muito sutil — move levemente oposto à câmera
    const parallaxX = interpolate(progress, [0, 1], [-2, 2], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const parallaxY = interpolate(progress, [0, 1], [-1, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const scaleX = (el.scale?.x ?? 1.08);
    const scaleY = (el.scale?.y ?? 1.08);
    const enterOpacity = el.animation?.enter_duration
      ? interpolate(frame, [0, el.animation.enter_duration], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
      : 1;

    return (
      <div style={{
        position: 'absolute', inset: 0, overflow: 'hidden',
        opacity: Math.min(enterOpacity, el.opacity ?? 1),
      }}>
        <Img
          src={src}
          style={{
            position: 'absolute',
            width: `${scaleX * 100}%`,
            height: `${scaleY * 100}%`,
            top: `${(1 - scaleY) * 50}%`,
            left: `${(1 - scaleX) * 50}%`,
            objectFit: 'cover',
            transform: `translate(${parallaxX}%, ${parallaxY}%)`,
          }}
        />
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'absolute',
        width: '100%',
        height: '100%',
        ...pos,
        opacity: el.opacity ?? 1,
        filter: el.blur ? `blur(${el.blur}px)` : undefined,
        mixBlendMode: (el.blend_mode as any) || 'normal',
        ...anim,
      }}
    >
      <Img
        src={src}
        style={{
          width: '100%',
          height: '100%',
          objectFit: (el.fit as any) || 'cover',
        }}
      />
    </div>
  );
};

// ── Particle System ────────────────────────────────────────────────────────

const seededRandom = (seed: number, index: number) => {
  const x = Math.sin(seed * 9301 + index * 49297) * 233280;
  return x - Math.floor(x);
};

const ParticleRenderer: React.FC<{ pf: ParticleField; frame: number; fps: number }> = ({
  pf, frame, fps,
}) => {
  const particles = useMemo(() => {
    const seed = pf.seed ?? 42;
    return Array.from({ length: pf.count ?? 20 }, (_, i) => ({
      x: seededRandom(seed, i * 3) * 100,
      y: seededRandom(seed, i * 3 + 1) * 100,
      size: (pf.size_min ?? 1.5) + seededRandom(seed, i * 3 + 2) * ((pf.size_max ?? 4) - (pf.size_min ?? 1.5)),
      opacity: (pf.opacity_min ?? 0.2) + seededRandom(seed, i) * ((pf.opacity_max ?? 0.6) - (pf.opacity_min ?? 0.2)),
      speed: 0.3 + seededRandom(seed, i + 100) * 0.7,
      phase: seededRandom(seed, i + 200) * Math.PI * 2,
    }));
  }, [pf.seed, pf.count]);

  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {particles.map((p, i) => {
        let tx = 0, ty = 0;
        const t = (frame / fps) * p.speed;
        if (pf.motion_type === 'float') {
          tx = Math.sin(t * 0.8 + p.phase) * 15;
          ty = -t * 10 % 110;
        } else if (pf.motion_type === 'drift') {
          tx = t * 20 + Math.sin(t + p.phase) * 10;
          ty = Math.cos(t * 0.5 + p.phase) * 20;
        } else if (pf.motion_type === 'orbit') {
          const angle = t + p.phase;
          tx = Math.cos(angle) * 20;
          ty = Math.sin(angle) * 20;
        }

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${(p.x + tx) % 100}%`,
              top: `${(p.y + ty) % 100}%`,
              width: p.size,
              height: p.size,
              borderRadius: '50%',
              backgroundColor: pf.color || '#ffffff',
              opacity: p.opacity,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ── Atmosphere / Glow ──────────────────────────────────────────────────────

const AtmosphereLayer: React.FC<{ env: any }> = ({ env }) => {
  if (!env) return null;
  const { glow_color, glow_x = 50, glow_y = 40, glow_size = 60, glow_opacity = 0.2, vignette = 0, grain = 0 } = env;

  return (
    <>
      {glow_color && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(ellipse ${glow_size}% ${glow_size * 0.6}% at ${glow_x}% ${glow_y}%, ${glow_color} 0%, transparent 70%)`,
            opacity: glow_opacity,
            pointerEvents: 'none',
            mixBlendMode: 'screen',
          }}
        />
      )}
      {vignette > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(ellipse 80% 80% at 50% 50%, transparent 40%, rgba(0,0,0,${vignette}) 100%)`,
            pointerEvents: 'none',
          }}
        />
      )}
      {grain > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: grain,
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.4'/%3E%3C/svg%3E")`,
            backgroundSize: '256px',
            pointerEvents: 'none',
            mixBlendMode: 'overlay',
          }}
        />
      )}
    </>
  );
};

// ── Main Runtime ───────────────────────────────────────────────────────────

export const MotionRuntime: React.FC<{ dsl: SceneDSL }> = ({ dsl }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const env = dsl.environment;
  const camera = dsl.camera;
  const duration = dsl.duration ?? durationInFrames;

  const cameraTransform = useCameraTransform(frame, fps, camera, duration);
  const transitionStyle = useTransitionStyle(
    frame,
    duration,
    fps,
    dsl.transition_in,
    dsl.transition_out,
  );

  const bg = env?.background || dsl.visual_dna?.background_color || '#0a0a0a';

  return (
    <AbsoluteFill
      style={{
        backgroundColor: bg.startsWith('#') ? bg : undefined,
        background: !bg.startsWith('#') ? bg : undefined,
        overflow: 'hidden',
        ...transitionStyle,
      }}
    >
      {/* Camera wrapper */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: cameraTransform || undefined,
          transformOrigin: 'center center',
          willChange: 'transform',
        }}
      >
        {/* Shape elements (backgrounds first) */}
        {(dsl.shape_elements || [])
          .filter(el => el.start == null || (frame >= el.start && frame < (el.start + el.duration)))
          .sort((a, b) => (a.position?.z ?? 0) - (b.position?.z ?? 0))
          .map(el => (
            <ShapeRenderer key={el.id} el={el} frame={frame} fps={fps} duration={el.duration ?? duration} dna={dsl} />
          ))}

        {/* Image elements */}
        {(dsl.image_elements || [])
          .filter(el => frame >= (el.start ?? 0) && frame < ((el.start ?? 0) + (el.duration ?? duration)))
          .map(el => (
            <ImageRenderer key={el.id} el={el} frame={frame} fps={fps} duration={el.duration ?? duration} dna={dsl} />
          ))}
      </div>

      {/* Atmosphere (outside camera) */}
      <AtmosphereLayer env={env} />

      {/* Particles */}
      {(dsl.particle_fields || [])
        .filter(pf => frame >= (pf.start ?? 0) && frame < ((pf.start ?? 0) + (pf.duration ?? duration)))
        .map(pf => (
          <ParticleRenderer key={pf.id} pf={pf} frame={frame} fps={fps} />
        ))}

      {/* Text elements (on top) */}
      {(dsl.text_elements || [])
        .filter(el => frame >= (el.start ?? 0) && frame < ((el.start ?? 0) + (el.duration ?? duration)))
        .sort((a, b) => (a.position?.z ?? 0.5) - (b.position?.z ?? 0.5))
        .map(el => (
          <TextRenderer key={el.id} el={el} frame={frame} fps={fps} duration={el.duration ?? duration} dna={dsl} />
        ))}
    </AbsoluteFill>
  );
};

export default MotionRuntime;
"""


# ── Cinematic Runtime TSX (Deterministic Pipeline) ────────────────────────────

def generate_cinematic_runtime() -> str:
    """
    Gera o CinematicRuntime.tsx — runtime determinístico para o novo pipeline.

    Arquitetura:
      - SceneGraph define composição (imutável, fonte da verdade)
      - MotionDSL define movimento (câmera, parallax, atmosfera)
      - CameraPhysics: spring physics para movimento realista
      - ParallaxLayer: clipPath CSS para parallax sem segmentação real
      - AtmosphereLayer: vignette, grain, glow, color grading
      - ParticleSystem: dust, sparkle, smoke
    """
    return r"""import React, { useMemo } from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Img,
} from 'remotion';

// ─── Types ────────────────────────────────────────────────────────────────────

interface BBox { x: number; y: number; width: number; height: number; }

interface SceneLayer {
  id: string;
  label: string;
  bbox: BBox;
  depth: number;
  depth_layer: number;
  parallax_sensitivity: number;
  motion_allowance: number;
  importance: string;
  locked: boolean;
}

interface SceneGraph {
  background_plate: string;
  frame_width: number;
  frame_height: number;
  layers: SceneLayer[];
  horizon_y: number;
  vanishing_point_x: number;
  composition_style: string;
  color_temperature: string;
}

interface CameraMotion {
  type: string;
  speed: number;
  easing: string;
  parallax: number;
  inertia: number;
  velocity: number;
  acceleration: number;
  damping: number;
  stiffness: number;
  micro_jitter: number;
  tilt: number;
  direction: string;
}

interface LayerAnimation {
  target: string;
  animation: string;
  intensity: number;
  speed: number;
  delay: number;
}

interface MotionDSL {
  scene_id: number;
  duration: number;
  fps: number;
  camera: CameraMotion;
  layer_animations: LayerAnimation[];
  particles: any;
  atmosphere: any;
  transition_in: any;
  transition_out: any;
  text_overlays: any[];
  cinematic_energy: number;
}

// ─── Camera Physics ───────────────────────────────────────────────────────────
//
// Usa spring() do Remotion para movimento cinematográfico realista.
// Cada tipo de câmera tem física diferente:
//   slow_dolly_in  → scale cresce gradualmente com spring
//   pan_right/left → translateX com inertia
//   parallax/float → movimento senoidal suave
//   handheld       → jitter + parallax irregular
//   static         → nenhum movimento (apenas atmosfera)

interface CameraTransform {
  translateX: number;
  translateY: number;
  scale: number;
  tilt: number;
}

const useCameraTransform = (
  frame: number,
  fps: number,
  duration: number,
  motion: CameraMotion,
): CameraTransform => {
  const progress = duration > 1 ? frame / (duration - 1) : 0;

  // Spring para movimento com inertia natural
  const springVal = spring({
    frame,
    fps,
    config: {
      damping: motion.damping ?? 14,
      stiffness: motion.stiffness ?? 120,
      mass: motion.inertia ?? 1.0,
    },
    durationInFrames: duration,
  });

  // Micro-jitter para handheld
  const jitter = motion.micro_jitter ?? 0;
  const jX = jitter > 0 ? Math.sin(frame * 7.3 + 1.2) * jitter * 3 : 0;
  const jY = jitter > 0 ? Math.cos(frame * 5.7 + 0.8) * jitter * 2 : 0;

  const p = motion.parallax ?? 0.08;
  const spd = motion.speed ?? 0.25;

  let translateX = 0;
  let translateY = 0;
  let scale = 1;

  switch (motion.type) {
    case 'slow_dolly_in':
    case 'push_in':
      scale = 1 + springVal * p * 2.5 * spd;
      translateY = -springVal * p * 30 * spd;
      break;
    case 'dolly_out':
    case 'pull_back':
      scale = 1 + p * 2.5 * spd - springVal * p * 2.5 * spd;
      translateY = springVal * p * 30 * spd;
      break;
    case 'pan_right':
      translateX = -interpolate(frame, [0, duration], [0, p * 120 * spd], {
        extrapolateRight: 'clamp',
      });
      break;
    case 'pan_left':
      translateX = interpolate(frame, [0, duration], [0, p * 120 * spd], {
        extrapolateRight: 'clamp',
      });
      break;
    case 'parallax':
      scale = 1 + p * 0.5 * spd;
      translateX = Math.sin(frame * 0.025 * spd) * p * 40;
      translateY = Math.cos(frame * 0.018 * spd) * p * 25;
      break;
    case 'float':
      scale = 1 + Math.sin(frame * 0.02 * spd) * p * 0.3;
      translateX = Math.sin(frame * 0.015 * spd) * p * 20;
      translateY = Math.cos(frame * 0.012 * spd) * p * 15;
      break;
    case 'handheld':
      scale = 1 + p * 0.3;
      translateX = Math.sin(frame * 11.3) * p * 8 + Math.cos(frame * 7.7) * p * 4;
      translateY = Math.cos(frame * 9.1) * p * 6 + Math.sin(frame * 5.3) * p * 3;
      break;
    case 'orbit':
      translateX = Math.sin(frame * 0.03 * spd) * p * 60;
      translateY = Math.cos(frame * 0.03 * spd) * p * 20;
      scale = 1 + p * 0.2;
      break;
    case 'static':
    default:
      break;
  }

  return {
    translateX: translateX + jX,
    translateY: translateY + jY,
    scale: Math.max(1, scale),
    tilt: motion.tilt ?? 0,
  };
};

// ─── Parallax Layer ───────────────────────────────────────────────────────────
//
// Técnica: Usa CSS clipPath inset() para recortar o frame original
// na região da camada (bbox), depois move o recorte a uma velocidade
// proporcional à profundidade (foreground move mais que background).
//
// Resultado: parallax cinematográfico realista sem segmentação real.
// A imagem original é preservada integralmente — apenas recortada e deslocada.

const ParallaxLayer: React.FC<{
  src: string;
  layer: SceneLayer;
  camX: number;
  camY: number;
  anim?: LayerAnimation;
  frame: number;
}> = ({ src, layer, camX, camY, anim, frame }) => {
  const { bbox, parallax_sensitivity: ps } = layer;

  // Layer se move NA DIREÇÃO OPOSTA à câmera, escalada por parallax_sensitivity
  // Foreground (depth=0, ps alto) → move mais
  // Background (depth=1, ps baixo) → move menos
  const layerX = -camX * ps;
  const layerY = -camY * ps;

  // Animação sutil (sway, drift, breathe)
  let animX = 0;
  let animY = 0;
  let animScale = 1;
  if (anim && anim.animation !== 'none') {
    const intensity = anim.intensity ?? 0.05;
    const speed = anim.speed ?? 1;
    const delay = anim.delay ?? 0;
    const t = Math.max(0, frame - delay);
    switch (anim.animation) {
      case 'subtle_sway':
        animX = Math.sin(t * 0.04 * speed) * intensity * 12;
        animY = Math.cos(t * 0.03 * speed) * intensity * 6;
        break;
      case 'drift':
        animX = Math.sin(t * 0.02 * speed) * intensity * 20;
        animY = Math.cos(t * 0.025 * speed) * intensity * 10;
        break;
      case 'pulse':
        animScale = 1 + Math.sin(t * 0.05 * speed) * intensity * 0.04;
        break;
      case 'breathe':
        animScale = 1 + Math.sin(t * 0.03 * speed) * intensity * 0.02;
        animY = Math.sin(t * 0.03 * speed) * intensity * 5;
        break;
    }
  }

  // Overscale ligeiro para evitar artefatos nas bordas durante o movimento
  const os = 1.06;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        // Recorta o frame original na região exata do elemento (locked bbox)
        clipPath: `inset(
          ${bbox.y * 100}%
          ${(1 - bbox.x - bbox.width) * 100}%
          ${(1 - bbox.y - bbox.height) * 100}%
          ${bbox.x * 100}%
        )`,
        transform: `translate(${layerX + animX}px, ${layerY + animY}px)`,
        willChange: 'transform',
      }}
    >
      <Img
        src={src}
        style={{
          position: 'absolute',
          width: `${os * 100}%`,
          height: `${os * 100}%`,
          top: `${-(os - 1) * 50}%`,
          left: `${-(os - 1) * 50}%`,
          objectFit: 'cover',
          transform: `scale(${animScale})`,
          userSelect: 'none',
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};

// ─── Atmosphere Layer ─────────────────────────────────────────────────────────

const AtmosphereLayer: React.FC<{ atm: any; frame: number; duration: number }> = ({
  atm, frame, duration,
}) => {
  if (!atm) return null;
  const vignette = atm.vignette ?? 0.3;
  const grain = atm.grain ?? 0.02;
  const glowOn = atm.glow_enabled ?? false;
  const glowColor = atm.glow_color ?? '#ffffff';
  const glowOpacity = atm.glow_opacity ?? 0.15;
  const glowX = atm.glow_x ?? 50;
  const glowY = atm.glow_y ?? 40;
  const glowSize = atm.glow_size ?? 60;
  const grade = atm.color_grade ?? 'none';
  const gradeIntensity = atm.color_grade_intensity ?? 0.0;

  const grainSeed = (frame * 127) % 256;

  // Color grading via CSS filter
  let filterStr = '';
  if (grade !== 'none' && gradeIntensity > 0) {
    const i = gradeIntensity;
    switch (grade) {
      case 'warm':   filterStr = `sepia(${i * 0.5}) saturate(${1 + i * 0.3})`; break;
      case 'cool':   filterStr = `hue-rotate(${i * -20}deg) saturate(${1 - i * 0.1})`; break;
      case 'desaturate': filterStr = `saturate(${1 - i * 0.8})`; break;
      case 'boost':  filterStr = `saturate(${1 + i * 0.5}) contrast(${1 + i * 0.1})`; break;
    }
  }

  return (
    <>
      {/* Vignette */}
      {vignette > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(0,0,0,${vignette}) 100%)`,
            pointerEvents: 'none',
          }}
        />
      )}
      {/* Atmospheric glow */}
      {glowOn && glowOpacity > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(ellipse ${glowSize}% ${glowSize * 0.6}% at ${glowX}% ${glowY}%, ${glowColor}${Math.round(glowOpacity * 255).toString(16).padStart(2, '0')} 0%, transparent 70%)`,
            pointerEvents: 'none',
            mixBlendMode: 'screen',
          }}
        />
      )}
      {/* Film grain */}
      {grain > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' seed='${grainSeed}' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
            opacity: grain * 0.4,
            mixBlendMode: 'overlay',
            pointerEvents: 'none',
          }}
        />
      )}
      {/* Color grade overlay */}
      {filterStr && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backdropFilter: filterStr,
            WebkitBackdropFilter: filterStr,
            pointerEvents: 'none',
          }}
        />
      )}
    </>
  );
};

// ─── Particle System ──────────────────────────────────────────────────────────

const seeded = (seed: number, i: number) => {
  const x = Math.sin(seed * 9301 + i * 49297) * 233280;
  return x - Math.floor(x);
};

const ParticleSystem: React.FC<{ cfg: any; frame: number; duration: number }> = ({
  cfg, frame, duration,
}) => {
  if (!cfg?.enabled) return null;
  const count = Math.min(cfg.count ?? 15, 60);
  const color = cfg.color ?? '#ffffff';
  const opacity = cfg.opacity ?? 0.3;
  const sMin = cfg.size_min ?? 1;
  const sMax = cfg.size_max ?? 3;
  const intensity = cfg.intensity ?? 0.15;

  const particles = useMemo(() =>
    Array.from({ length: count }, (_, i) => ({
      x: seeded(42, i * 3) * 100,
      y: seeded(42, i * 3 + 1) * 100,
      size: sMin + seeded(42, i * 3 + 2) * (sMax - sMin),
      speed: 0.3 + seeded(43, i) * 0.7,
      phase: seeded(44, i) * Math.PI * 2,
    }))
  , [count, sMin, sMax]);

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {particles.map((p, i) => {
        const t = frame * p.speed * 0.015;
        const px = (p.x + Math.sin(t + p.phase) * 8) % 100;
        const py = (p.y - t * 3 + 100) % 100;
        const alpha = opacity * intensity * (0.5 + Math.sin(t * 2 + p.phase) * 0.5);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${px}%`,
              top: `${py}%`,
              width: p.size,
              height: p.size,
              borderRadius: '50%',
              background: color,
              opacity: alpha,
            }}
          />
        );
      })}
    </div>
  );
};

// ─── Text Overlay ─────────────────────────────────────────────────────────────

const TextOverlay: React.FC<{ t: any; frame: number; duration: number }> = ({ t, frame, duration }) => {
  const enterEnd = (t.enter_frame ?? 0) + 20;
  const exitStart = t.exit_frame === -1 ? duration : t.exit_frame;

  const opacity = interpolate(
    frame,
    [t.enter_frame ?? 0, enterEnd, exitStart, exitStart + 15],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  const translateY = interpolate(
    frame,
    [t.enter_frame ?? 0, enterEnd],
    [12, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  return (
    <div
      style={{
        position: 'absolute',
        left: `${t.x ?? 50}%`,
        top: `${t.y ?? 85}%`,
        transform: `translate(-50%, -50%) translateY(${translateY}px)`,
        opacity,
        color: t.color ?? '#ffffff',
        fontSize: t.font_size ?? 40,
        fontWeight: t.font_weight ?? 600,
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        textAlign: 'center',
        textShadow: '0 2px 12px rgba(0,0,0,0.6)',
        pointerEvents: 'none',
        whiteSpace: 'nowrap',
        letterSpacing: '-0.5px',
      }}
    >
      {t.text}
    </div>
  );
};

// ─── Cinematic Runtime — Main Component ──────────────────────────────────────
//
// Fonte absoluta da verdade = SceneGraph (composição imutável do frame original)
// Autoridade de movimento   = MotionDSL  (apenas câmera, parallax, atmosfera)
//
// Pipeline de renderização:
//   1. Background plate (frame original, com camera motion global)
//   2. Parallax layers (recortes do frame movendo-se a velocidades diferentes)
//   3. Atmosphere (vignette, glow, grain, color grade)
//   4. Particles (dust, sparkle, etc.)
//   5. Text overlays (mínimos, se necessários)
//   6. Transition (fade in/out)

export const CinematicRuntime: React.FC<{ graph: any; motion: any }> = ({ graph, motion }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const duration = motion.duration ?? durationInFrames;

  const cam = useCameraTransform(frame, fps, duration, motion.camera ?? {});

  // Transição de entrada
  const transIn = motion.transition_in;
  const transOut = motion.transition_out;
  const enterOpacity = transIn
    ? interpolate(frame, [0, transIn.duration ?? 20], [0, 1], { extrapolateRight: 'clamp' })
    : 1;
  const exitOpacity = transOut
    ? interpolate(
        frame,
        [duration - (transOut.duration ?? 20), duration],
        [1, 0],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
      )
    : 1;
  const sceneOpacity = Math.min(enterOpacity, exitOpacity);

  const bgSrc = graph.background_plate ?? '';

  // Overscale do background para espaço de câmera
  const bgOverscale = Math.max(1.08, 1 + (motion.camera?.parallax ?? 0.08) * 2.5);

  return (
    <AbsoluteFill style={{ opacity: sceneOpacity, overflow: 'hidden', background: '#000' }}>

      {/* ── 1. Background Plate — imagem original com câmera global ──────── */}
      <div style={{ position: 'absolute', inset: 0, overflow: 'hidden' }}>
        <Img
          src={bgSrc}
          style={{
            position: 'absolute',
            width: `${bgOverscale * 100}%`,
            height: `${bgOverscale * 100}%`,
            top: `${-(bgOverscale - 1) * 50}%`,
            left: `${-(bgOverscale - 1) * 50}%`,
            objectFit: 'cover',
            transform: `translate(${cam.translateX * 0.4}px, ${cam.translateY * 0.4}px) scale(${cam.scale}) rotate(${cam.tilt}deg)`,
            willChange: 'transform',
            userSelect: 'none',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* ── 2. Parallax Layers — recortes do frame com velocidade por depth ── */}
      {(graph.layers ?? []).map((layer: SceneLayer) => {
        if (layer.depth > 0.85) return null; // background layer → sem parallax extra
        const anim = (motion.layer_animations ?? []).find((a: LayerAnimation) => a.target === layer.id);
        return (
          <ParallaxLayer
            key={layer.id}
            src={bgSrc}
            layer={layer}
            camX={cam.translateX}
            camY={cam.translateY}
            anim={anim}
            frame={frame}
          />
        );
      })}

      {/* ── 3. Atmosphere ──────────────────────────────────────────────────── */}
      <AtmosphereLayer atm={motion.atmosphere} frame={frame} duration={duration} />

      {/* ── 4. Particles ───────────────────────────────────────────────────── */}
      <ParticleSystem cfg={motion.particles} frame={frame} duration={duration} />

      {/* ── 5. Text Overlays ───────────────────────────────────────────────── */}
      {(motion.text_overlays ?? []).map((t: any, i: number) => (
        <TextOverlay key={t.id ?? i} t={t} frame={frame} duration={duration} />
      ))}

    </AbsoluteFill>
  );
};

export default CinematicRuntime;
"""
