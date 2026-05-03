"""
Gera componentes Remotion (TypeScript/React) a partir de imagens de frame e descricoes de cena.

O gerador recebe:
  - Imagem de referencia da cena (base64)
  - Descricao textual da cena
  - Contexto de estilo (prompt do usuario + chips de estilo + analise de referencia)
  - Duracao em segundos e FPS do projeto

E produz um componente .tsx completo e valido para o Remotion, com:
  - Animacoes baseadas em useCurrentFrame()
  - spring() para movimentos organicos, interpolate() para transicoes lineares
  - Pelo menos 3 elementos animados com timings diferentes
  - Fade-in nos primeiros frames
"""

import re
from ai_client import AIClient

# Prompt de sistema e template de prompt por cena omitidos intencionalmente
# Business logic omitted — see live demo
SYSTEM_PROMPT = None
SCENE_PROMPT_TEMPLATE = None


class SceneGenerator:
    def __init__(self, ai_client: AIClient):
        self.client = ai_client

    def generate(self, scene_num: int, frame_image: str, description: str,
                 style: dict, duration: float = 3.0, fps: int = 30) -> str:
        """
        Gera o codigo TypeScript/React de uma cena Remotion.

        Args:
            scene_num:    Numero da cena (determina o nome do componente: Scene1, Scene2...)
            frame_image:  Imagem de referencia em base64 data URL (opcional)
            description:  Descricao textual do que deve aparecer na cena
            style:        Dicionario com executionPrompt, styleChips e referenceAnalysis
            duration:     Duracao da cena em segundos
            fps:          Frames por segundo do projeto

        Returns:
            String com o codigo TypeScript completo do componente Remotion
        """
        # Logica de negocio omitida intencionalmente — produto comercial ativo
        # Business logic omitted — see live demo
        raise NotImplementedError

    def _build_style_instructions(self, style: dict) -> str:
        # Logica de negocio omitida intencionalmente — produto comercial ativo
        # Business logic omitted — see live demo
        raise NotImplementedError

    def _clean_code(self, raw: str, scene_num: int) -> str:
        # Logica de negocio omitida intencionalmente — produto comercial ativo
        # Business logic omitted — see live demo
        raise NotImplementedError


def fallback_scene(scene_num: int, description: str, duration: float = 3.0, fps: int = 30) -> str:
    """
    Componente Remotion minimo gerado quando a IA falha apos 3 tentativas.
    Garante que o projeto sempre tenha um arquivo valido para cada cena.
    """
    frames = int(duration * fps)
    return f"""import {{ AbsoluteFill, useCurrentFrame, interpolate, spring }} from 'remotion';

export const Scene{scene_num}: React.FC = () => {{
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 20], [0, 1], {{ extrapolateRight: 'clamp' }});
  const scale = spring({{ frame, fps: {fps}, config: {{ damping: 12 }} }});
  const y = interpolate(frame, [0, 20], [24, 0], {{ extrapolateRight: 'clamp' }});

  return (
    <AbsoluteFill style={{{{ backgroundColor: '#0d0d0f', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity }}}}>
      <div style={{{{
        textAlign: 'center',
        transform: `translateY(${{y}}px) scale(${{scale}})`,
      }}}}>
        <div style={{{{
          fontSize: 48,
          fontWeight: 700,
          color: '#f0f0f2',
          fontFamily: 'system-ui, sans-serif',
          letterSpacing: '-0.03em',
        }}}}>
          Cena {scene_num}
        </div>
        <div style={{{{
          fontSize: 20,
          color: '#8a8a9a',
          marginTop: 12,
          fontFamily: 'system-ui, sans-serif',
        }}}}>
          {description[:80] if description else 'Scene description'}
        </div>
        <div style={{{{
          width: 60,
          height: 3,
          background: 'linear-gradient(90deg, #6c63ff, #00d4aa)',
          borderRadius: 999,
          margin: '16px auto 0',
        }}}} />
      </div>
    </AbsoluteFill>
  );
}};
"""
