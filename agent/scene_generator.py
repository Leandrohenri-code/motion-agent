"""
Gerador de componentes Remotion por cena usando IA.

Implementa contexto persistente entre cenas para garantir coerência visual:
  - Memória de paleta, tipografia e timing estabelecidos nas cenas anteriores
  - Código da cena anterior como referência de continuidade
  - Descrição da próxima cena para preparar transições
  - Comportamento de câmera e objetos acumulado ao longo do projeto
"""

import re
from utils.json_streamer import log


SYSTEM_PROMPT = """You are an elite motion graphics engineer who writes production-ready Remotion (TypeScript/React) code for commercial projects. Your animations rival Apple, Nike, and high-end agency work.

## YOUR CORE SKILL: CONTINUITY
You are generating ONE SCENE inside a multi-scene video. Your #1 job is consistency:
- Extract the exact colors, fonts, animation timing, and patterns from the previous scene
- Continue the same visual language — never reinvent the palette or font mid-video
- Match the rhythm and easing style established in earlier scenes
- Prepare smooth transitions into the next scene

## REMOTION API

```typescript
import {
  AbsoluteFill, useCurrentFrame, useVideoConfig,
  interpolate, spring, Easing, Sequence, Img, random
} from 'remotion';
import React from 'react';

const frame = useCurrentFrame();
const { fps, durationInFrames, width, height } = useVideoConfig();
```

### Spring physics
```typescript
// Organic enter: smooth entrance
const enter = spring({ frame, fps, config: { damping: 14, stiffness: 160 }, durationInFrames: 25 });
// Tight snap: UI elements
const snap = spring({ frame, fps, config: { damping: 22, stiffness: 280 } });
// Bouncy: playful elements
const bounce = spring({ frame, fps, config: { damping: 8, stiffness: 120 } });
```

### Exit (ALWAYS include)
```typescript
const exitStart = durationInFrames - 18;
const exitFade = interpolate(frame, [exitStart, durationInFrames], [1, 0], {
  extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  easing: Easing.in(Easing.cubic),
});
// Combine: const visible = enterOpacity * exitFade;
```

### Stagger
```typescript
items.map((item, i) => {
  const delay = i * 5;
  const t = spring({ frame: frame - delay, fps, config: { damping: 14, stiffness: 160 } });
  return <div style={{ transform: `translateY(${(1-t)*40}px)`, opacity: t }} />;
})
```

### Clip reveal
```typescript
clipPath: `inset(0 ${interpolate(frame,[0,25],[100,0],{extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)})}% 0 0)`
```

### Kinetic counter
```typescript
const value = Math.round(interpolate(frame,[10,60],[0,100],{extrapolateRight:'clamp',easing:Easing.out(Easing.exp)}));
```

### Particle field (deterministic — use random() from remotion)
```typescript
Array.from({length:20},(_,i)=>{
  const t = interpolate(frame-random(`d${i}`)*30,[0,20],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return <div key={i} style={{position:'absolute',left:random(`x${i}`)*width,top:random(`y${i}`)*height,width:2+random(`s${i}`)*3,height:2+random(`s${i}`)*3,borderRadius:'50%',background:'white',opacity:t*0.5}}/>;
})
```

## VISUAL STANDARDS

### Typography
- Headlines: 80-140px, fontWeight 800-900, letterSpacing -2 to -4px
- Body: 24-36px, lineHeight 1.4-1.6, fontWeight 400-500
- Labels: 11-16px, fontWeight 600, letterSpacing 4-8px, textTransform 'uppercase'
- Font stack: `'Helvetica Neue','Arial Black',system-ui,sans-serif`

### Backgrounds (never flat)
```typescript
// Dark gradient
background: 'linear-gradient(160deg, #08080f 0%, #0d0a1a 50%, #080810 100%)'
// With glow
<div style={{position:'absolute',inset:0,background:'radial-gradient(ellipse 80% 60% at 50% 40%, rgba(108,99,255,0.18) 0%, transparent 70%)'}}/>
```

### Glass card
```typescript
background:'rgba(255,255,255,0.04)', backdropFilter:'blur(20px)',
border:'1px solid rgba(255,255,255,0.08)', borderRadius:24,
boxShadow:'0 40px 100px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.08)'
```

## OUTPUT FORMAT
- TypeScript only. No markdown. No explanations.
- Named export: `export const SceneN: React.FC = () => { ... }`
- Root: `<AbsoluteFill>`
- Import all used from 'remotion'
- Never Math.random() — use random() from remotion
- All text animates — no static text
"""


def fallback_scene(scene_num: int, description: str, duration_frames: int) -> str:
    return (
        f"import {{AbsoluteFill,useCurrentFrame,useVideoConfig,interpolate,spring,Easing}} from 'remotion';\n"
        f"import React from 'react';\n\n"
        f"export const Scene{scene_num}: React.FC = () => {{\n"
        f"  const frame = useCurrentFrame();\n"
        f"  const {{fps,durationInFrames}} = useVideoConfig();\n"
        f"  const enter = spring({{frame,fps,config:{{damping:14,stiffness:140}},durationInFrames:20}});\n"
        f"  const exitFade = interpolate(frame,[durationInFrames-15,durationInFrames],[1,0],{{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.in(Easing.cubic)}});\n"
        f"  return (\n"
        f"    <AbsoluteFill style={{{{background:'linear-gradient(160deg,#08080f,#0d0a1a)',display:'flex',alignItems:'center',justifyContent:'center'}}}}>\n"
        f"      <div style={{{{position:'absolute',width:500,height:500,borderRadius:'50%',left:'50%',top:'50%',transform:'translate(-50%,-50%)',background:'radial-gradient(circle,rgba(108,99,255,0.2) 0%,transparent 70%)',filter:'blur(60px)'}}}}/>\n"
        f"      <div style={{{{opacity:enter*exitFade,transform:`translateY(${{(1-enter)*40}}px)`,textAlign:'center',padding:'0 80px'}}}}>\n"
        f"        <div style={{{{fontSize:80,fontWeight:800,color:'#fff',fontFamily:\"'Helvetica Neue',Arial,sans-serif\",letterSpacing:-2,textShadow:'0 0 60px rgba(108,99,255,0.7)'}}}}>Cena {scene_num}</div>\n"
        f"        <div style={{{{fontSize:22,color:'rgba(255,255,255,0.45)',marginTop:18,fontFamily:'system-ui,sans-serif'}}}}>{description[:100]}</div>\n"
        f"      </div>\n"
        f"    </AbsoluteFill>\n"
        f"  );\n"
        f"}};\n"
    )


class SceneContext:
    """
    Contexto persistente acumulado ao longo da geração de todas as cenas.
    Garante coerência visual — paleta, tipografia, timing, câmera.
    """

    def __init__(self):
        self.established_colors: list = []        # Cores hex extraídas das cenas geradas
        self.established_fonts: list = []         # Fontes detectadas no código
        self.established_timing: dict = {}        # spring config dominante do projeto
        self.camera_behavior: str = ""            # Padrão de câmera estabelecido
        self.object_behavior: str = ""            # Como objetos se movem (direção, física)
        self.transition_style: str = ""           # Estilo de transição entre cenas
        self.scenes_summary: list = []            # [{num, description, duration, key_elements}]
        self.previous_code: str = ""              # Código TypeScript da última cena gerada

    def update_from_code(self, scene_num: int, code: str, frame: dict):
        """Extrai informações do código gerado para persistir no contexto."""
        # Extrai cores hex
        colors = list(set(re.findall(r"#[0-9a-fA-F]{6}", code)))
        for c in colors:
            if c not in self.established_colors:
                self.established_colors.append(c)
        self.established_colors = self.established_colors[:12]  # mantém top 12

        # Extrai fontes
        fonts = re.findall(r"fontFamily['\"]?:\s*['\"]([^'\"]+)['\"]", code)
        for f in fonts:
            if f not in self.established_fonts:
                self.established_fonts.append(f)

        # Detecta spring config dominante
        spring_configs = re.findall(r"damping:\s*(\d+).*?stiffness:\s*(\d+)", code)
        if spring_configs:
            avg_damping  = sum(int(d) for d, _ in spring_configs) // len(spring_configs)
            avg_stiff    = sum(int(s) for _, s in spring_configs) // len(spring_configs)
            self.established_timing = {"damping": avg_damping, "stiffness": avg_stiff}

        # Detecta padrão de câmera/objeto
        if "scale" in code and not self.camera_behavior:
            self.camera_behavior = "Zoom-in entrance, scale spring from 0.85 to 1.0"
        if "translateY" in code and not self.object_behavior:
            self.object_behavior = "Elements enter from below (translateY), exit upward"
        if "translateX" in code and not self.object_behavior:
            self.object_behavior = "Elements slide horizontally"

        # Detecta estilo de transição (exit animation)
        if "exitFade" in code or "exitOpacity" in code:
            self.transition_style = "Fade out on exit"
        if "clipPath" in code:
            self.transition_style = "Clip path wipe transition"

        # Adiciona resumo da cena
        self.scenes_summary.append({
            "num": scene_num,
            "description": frame.get("description", "")[:80],
            "duration": frame.get("duration", 3),
            "key_colors": colors[:4],
        })

        self.previous_code = code

    def to_prompt_section(self, next_frame: dict = None) -> str:
        """Serializa o contexto em texto para incluir no prompt."""
        lines = ["## PROJECT MEMORY (maintain consistency with this)"]

        if self.established_colors:
            lines.append(f"Established palette: {', '.join(self.established_colors[:8])}")
            lines.append("  ↳ USE THESE EXACT COLORS. Do not introduce new dominant colors.")

        if self.established_fonts:
            lines.append(f"Established fonts: {', '.join(self.established_fonts[:3])}")
            lines.append("  ↳ USE THE SAME FONT STACK across all scenes.")

        if self.established_timing:
            d = self.established_timing.get("damping", 14)
            s = self.established_timing.get("stiffness", 160)
            lines.append(f"Established spring timing: damping={d}, stiffness={s}")
            lines.append("  ↳ Match this spring feel for continuity of rhythm.")

        if self.camera_behavior:
            lines.append(f"Camera behavior: {self.camera_behavior}")

        if self.object_behavior:
            lines.append(f"Object behavior: {self.object_behavior}")

        if self.transition_style:
            lines.append(f"Transition style: {self.transition_style}")

        if self.scenes_summary:
            lines.append("\nScene history:")
            for s in self.scenes_summary[-3:]:  # últimas 3 cenas
                lines.append(f"  Scene {s['num']}: \"{s['description']}\" ({s['duration']}s)")

        if self.previous_code:
            # Passa apenas as primeiras 50 linhas do código anterior (suficiente para padrões)
            prev_lines = self.previous_code.split("\n")[:50]
            lines.append("\n## PREVIOUS SCENE CODE (extract colors, fonts, patterns — match them exactly)")
            lines.append("```typescript")
            lines.extend(prev_lines)
            if len(self.previous_code.split("\n")) > 50:
                lines.append("// ... (truncated)")
            lines.append("```")

        if next_frame:
            next_desc = next_frame.get("description", "")
            next_dur = next_frame.get("duration", 3)
            lines.append(f"\n## NEXT SCENE GOAL (prepare transition for this)")
            lines.append(f"Next scene: \"{next_desc}\" ({next_dur}s)")
            lines.append("  ↳ Your EXIT animation should visually lead INTO the next scene.")
            lines.append("  ↳ If next scene has similar elements, set them up at the same screen position.")

        return "\n".join(lines)


class SceneGenerator:
    def __init__(self, ai_client, vision_client=None):
        self.client = ai_client
        self.vision_client = vision_client or ai_client

    def generate(self, scene_num: int, frame: dict, style_prompt: str,
                 context: SceneContext = None,
                 next_frame: dict = None,
                 reference_analysis: dict = None) -> str:
        """
        Gera o código TypeScript/React de uma cena Remotion.

        Args:
            scene_num:           Número da cena (1-based)
            frame:               Dict com name, description, duration, preview, media_type
            style_prompt:        Prompt de estilo global
            context:             Contexto acumulado das cenas anteriores (memória)
            next_frame:          Próximo frame para preparar transição
            reference_analysis:  Análise de referência visual
        """
        prompt = self._build_prompt(
            scene_num, frame, style_prompt,
            context=context,
            next_frame=next_frame,
            reference_analysis=reference_analysis,
        )
        images = []
        if frame.get("preview") and frame["preview"].startswith("data:"):
            images.append(frame["preview"])

        try:
            if self.client.streaming:
                chunks = []
                for chunk in self.client.stream(prompt, images=images or None):
                    chunks.append(chunk)
                raw = "".join(chunks)
            else:
                raw = self.client.complete(prompt, images=images or None)
            code = self._extract_code(raw, scene_num)
            return code
        except Exception as e:
            log(f"SceneGenerator erro (cena {scene_num}): {e}", level="warn")
            duration_frames = int(float(frame.get("duration", 3)) * 30)
            return fallback_scene(scene_num, frame.get("description", ""), duration_frames)

    def describe_image(self, frame: dict) -> str:
        images = []
        if frame.get("preview") and frame["preview"].startswith("data:"):
            images.append(frame["preview"])
        media_type = "vídeo (frame de referência)" if frame.get("media_type") == "video" else "imagem de cena"
        prompt = (
            f"Esta é uma {media_type}. Descreva em 1-2 frases o que deve acontecer nesta cena "
            f"de vídeo motion graphics: elementos visuais, texto, animações e estilo. Responda em português."
        )
        try:
            return self.vision_client.complete(prompt, images=images or None)
        except Exception:
            return frame.get("description", "")

    def _build_prompt(self, scene_num: int, frame: dict, style_prompt: str,
                      context: SceneContext = None,
                      next_frame: dict = None,
                      reference_analysis: dict = None) -> str:
        description = frame.get("description", "").strip()
        duration = float(frame.get("duration", 3))
        duration_frames = int(duration * 30)
        media_type = frame.get("media_type", "image")
        is_first = (scene_num == 1)
        is_last = (next_frame is None)

        # Seção de referência
        ref_section = ""
        if reference_analysis:
            palette = reference_analysis.get("palette", [])
            chars = reference_analysis.get("characteristics", {})
            ref_prompt = reference_analysis.get("prompt", "")
            lines = []
            if palette:
                lines.append(f"Reference palette: {', '.join(palette)}")
            if chars:
                for k, v in chars.items():
                    lines.append(f"  {k}: {v}")
            if ref_prompt:
                lines.append(f"Reference style: {ref_prompt}")
            if lines:
                ref_section = "\n## VISUAL REFERENCE\n" + "\n".join(lines)

        # Contexto persistente das cenas anteriores
        context_section = ""
        if context and context.scenes_summary:
            context_section = "\n" + context.to_prompt_section(next_frame)
        elif is_first:
            context_section = "\n## FIRST SCENE\nEstablish the visual language here. All subsequent scenes will inherit your color palette, fonts, and animation style."

        # Hints de composição baseados na descrição
        hints = []
        desc_lower = description.lower()
        if any(k in desc_lower for k in ["texto", "text", "título", "title", "headline", "palavra", "frase"]):
            hints.append("Kinetic typography: words enter individually with spring+stagger+blur reveal")
        if any(k in desc_lower for k in ["pessoa", "person", "rosto", "face", "entrevista"]):
            hints.append("Cinematic frame: lower thirds, name tags, corner bracket overlays")
        if any(k in desc_lower for k in ["produto", "product", "logo", "marca", "brand"]):
            hints.append("Product hero: layered depth, spotlight gradient, scale spring reveal from 0.85")
        if any(k in desc_lower for k in ["número", "number", "dados", "data", "%", "gráfico", "chart"]):
            hints.append("Data animation: counter with Easing.out(Easing.exp), animated progress bars")
        if not hints:
            hints.append("Layered composition: atmospheric background glow + mid graphic elements + foreground text")

        media_note = "\nThis is based on a VIDEO reference — recreate its visual essence as CSS animation." if media_type == "video" else ""

        # Instrução de posição na sequência
        position_note = ""
        if is_first:
            position_note = "\nPOSITION: OPENING SCENE — establish the full visual identity here. Be bold."
        elif is_last:
            position_note = "\nPOSITION: CLOSING SCENE — create a strong, memorable ending. The exit should feel final."
        else:
            position_note = f"\nPOSITION: Scene {scene_num} in the middle of the sequence — maintain flow, don't reset the visual identity."

        return f"""Create Scene{scene_num} for a high-end commercial motion graphics video.

## SCENE BRIEF
Scene: {scene_num}
Duration: {duration}s = {duration_frames} frames @30fps
Description: {description or 'A visually striking commercial motion graphics scene'}
{media_note}
{position_note}

## PROJECT STYLE
{style_prompt or 'Professional commercial motion design. Dark premium aesthetic, vibrant accents, spring physics.'}
{ref_section}
{context_section}

## COMPOSITION DIRECTION
{chr(10).join(hints)}

## TECHNICAL REQUIREMENTS
- Component: Scene{scene_num} (named export)
- Duration: exactly {duration_frames} frames
- ENTRANCE: animate in first 20-30 frames with spring()
- EXIT: fade/move out last 15-20 frames — lead into next scene if one exists
- 3+ depth layers: background treatment + mid elements + foreground text
- All text animates — never static
- No flat backgrounds — use gradients and radial glows
- Color/font continuity is MANDATORY if previous scene code is provided above

Output TypeScript only. No markdown. No explanations."""

    def _extract_code(self, raw: str, scene_num: int) -> str:
        code = re.sub(r"```(?:typescript|tsx|ts|javascript|jsx|js)?\s*", "", raw)
        code = re.sub(r"```\s*$", "", code, flags=re.MULTILINE)
        code = code.strip()

        if not re.search(rf"export\s+const\s+Scene{scene_num}", code):
            code = re.sub(r"export\s+const\s+Scene\d+", f"export const Scene{scene_num}", code)

        if "from 'remotion'" not in code and 'from "remotion"' not in code:
            code = "import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from 'remotion';\nimport React from 'react';\n\n" + code
        elif "import React" not in code:
            code = "import React from 'react';\n" + code

        return code
