"""
Analisa videos e imagens de referencia para extrair caracteristicas de estilo.

Pipeline de analise:
  1. Extrai frames representativos do video de referencia (via OpenCV)
  2. Combina frames do video com imagens do mood board
  3. Envia as imagens para o modelo de visao junto com uma descricao manual (opcional)
  4. Retorna um dicionario estruturado com:
       - characteristics: estilo, tipografia, ritmo, transicoes, fundo, atmosfera
       - palette:         lista de cores hex dominantes
       - prompt:          prompt gerado em portugues para usar na geracao das cenas
"""

import os
import json
from utils.image_utils import image_to_base64, extract_dominant_colors
from utils.json_streamer import log


class ReferenceAnalyzer:
    def __init__(self, ai_client):
        self.client = ai_client

    def analyze(self, video_path: str = None, style_images: list = None,
                manual_description: str = None) -> dict:
        """
        Ponto de entrada da analise de referencia.

        Args:
            video_path:          Caminho para o video de referencia (opcional)
            style_images:        Lista de caminhos ou data URLs de imagens de mood board
            manual_description:  Descricao textual manual do estilo desejado

        Returns:
            Dicionario com characteristics, palette e prompt gerado
        """
        frames = []

        if video_path and os.path.isfile(video_path):
            log("Extraindo frames do video...")
            frames = self._extract_video_frames(video_path, max_frames=6)

        all_images = frames + (style_images or [])

        if not all_images and not manual_description:
            return {}

        log("Analisando estilo com IA vision...")
        analysis = self._analyze_with_vision(all_images[:8], manual_description)

        if all_images:
            log("Extraindo paleta de cores...")
            try:
                colors = extract_dominant_colors(all_images[0]) if os.path.isfile(all_images[0]) else []
                if colors:
                    analysis["palette"] = colors
            except Exception:
                pass

        return analysis

    def _extract_video_frames(self, video_path: str, max_frames: int = 6) -> list:
        """
        Extrai frames distribuidos ao longo do video usando OpenCV.
        Salva os frames como JPG em uma pasta temporaria .motion_agent_frames/.
        Retorna a lista de caminhos dos arquivos gerados.
        """
        # Logica de negocio omitida intencionalmente — produto comercial ativo
        # Business logic omitted — see live demo
        raise NotImplementedError

    def _analyze_with_vision(self, images: list, manual_description: str) -> dict:
        """
        Envia imagens para o modelo de visao e interpreta a resposta JSON.
        Retorna um dicionario com characteristics, palette e prompt.
        Em caso de falha, retorna valores padrao para nao interromper o fluxo.
        """
        # Logica de negocio omitida intencionalmente — produto comercial ativo
        # Business logic omitted — see live demo
        raise NotImplementedError
