#!/usr/bin/env python3
"""
Motion Agent — Orquestrador principal.
Recebe o JSON de configuracao do Electron via stdin e transmite o progresso via stdout.

Fluxo de execucao:
  1. Le configuracao completa via stdin (JSON)
  2. Inicializa clientes de IA (modelo principal + modelo de visao)
  3. Analisa referencias visuais (video + imagens de mood board)
  4. Para cada frame/cena:
       - Gera componente TypeScript/React para Remotion via IA
       - Salva o arquivo no projeto Remotion (dispara hot-reload)
       - (opcional) aguarda aprovacao do usuario antes de continuar
  5. Atualiza Root.tsx com todas as cenas e duracoes
  6. Executa verificacao de coerencia visual entre cenas
  7. Renderiza o video final via Remotion CLI
  8. Abre a pasta de saida (se configurado)

Comunicacao Electron <-> Python: JSON por stdio (ver utils/json_streamer.py)
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(__file__))

from ai_client import AIClient
from scene_generator import SceneGenerator, fallback_scene
from remotion_writer import RemotionWriter
from remotion_controller import RemotionController
from reference_analyzer import ReferenceAnalyzer
from coherence_checker import CoherenceChecker
from audio_processor import AudioProcessor
from style_extractor import StyleExtractor
from utils.json_streamer import log, progress, scene_done, awaiting_approval, done, error, send
from utils.image_utils import image_to_base64


def read_stdin_json() -> dict:
    line = sys.stdin.readline()
    return json.loads(line.strip())


def wait_for_approval(scene_num: int) -> dict:
    """Aguarda mensagem approve/reject/abort/retry do Electron via stdin."""
    while True:
        line = sys.stdin.readline()
        if not line:
            time.sleep(0.1)
            continue
        try:
            msg = json.loads(line.strip())
            if msg.get("type") in ("approve_scene", "reject_scene", "abort", "retry_scene"):
                return msg
        except Exception:
            continue


def run(config: dict):
    # Logica de negocio omitida intencionalmente — produto comercial ativo
    # Business logic omitted — see live demo
    pass


if __name__ == "__main__":
    try:
        config = read_stdin_json()
        run(config)
    except KeyboardInterrupt:
        log("Interrompido.", level="warn")
    except Exception as e:
        import traceback
        error(f"Erro fatal: {e}\n{traceback.format_exc()}", retryable=False)
        sys.exit(1)
