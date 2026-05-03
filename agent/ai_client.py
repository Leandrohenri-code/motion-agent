"""
Cliente universal de IA com suporte a qualquer provider registrado.

Abstrai as diferencas entre SDKs e APIs de forma que o resto do agente
sempre chame apenas client.complete() ou client.stream(), independente
do provider escolhido pelo usuario.

Providers suportados e seus SDKs:
  - openai_compat  : OpenAI, Mistral, Groq, Together, DeepSeek, xAI, OpenRouter,
                     HuggingFace, Fireworks, Anyscale, LM Studio, Azure OpenAI
                     (todos usam o mesmo formato de API OpenAI-compatible)
  - anthropic      : Claude via SDK oficial anthropic-python
  - google         : Gemini via SDK google-generativeai
  - ollama         : Modelos locais via API Ollama (formato proprio)
"""

import time
import json
from typing import Iterator, Optional
from provider_registry import get_provider, PROVIDERS


class AIClient:
    def __init__(self, provider_id: str, api_key: str, base_url: str = None,
                 model: str = None, temperature: float = 0.7, max_tokens: int = 4096,
                 timeout: int = 120, streaming: bool = True, system_prompt: str = ""):
        self.provider_id = provider_id
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.streaming = streaming
        self.system_prompt = system_prompt
        self.provider = get_provider(provider_id)
        self.base_url = base_url or self.provider["base_url"]

    def _build_messages(self, prompt: str, images: list = None) -> list:
        """
        Constroi a lista de mensagens no formato OpenAI (multimodal quando ha imagens).

        Quando ha imagens, cada uma e inserida como image_url antes do texto,
        seguindo o formato de content array do OpenAI Vision.
        O system prompt e injetado como primeira mensagem quando presente.
        """
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        content = []
        if images:
            for img in images:
                content.append({"type": "image_url", "image_url": {"url": img}})
        content.append({"type": "text", "text": prompt})
        if len(content) == 1 and content[0]["type"] == "text":
            messages.append({"role": "user", "content": prompt})
        else:
            messages.append({"role": "user", "content": content})
        return messages

    def complete(self, prompt: str, images: list = None) -> str:
        """
        Completion sem streaming. Retorna o texto completo da resposta.
        Tenta ate 3 vezes com backoff exponencial antes de lancar excecao.
        """
        sdk = self.provider.get("sdk", "openai_compat")
        for attempt in range(3):
            try:
                if sdk == "anthropic":
                    return self._complete_anthropic(prompt, images)
                elif sdk == "google":
                    return self._complete_google(prompt, images)
                elif sdk == "ollama":
                    return self._complete_ollama(prompt, images)
                else:
                    return self._complete_openai_compat(prompt, images)
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

    def stream(self, prompt: str, images: list = None) -> Iterator[str]:
        """
        Streaming completion. Itera sobre chunks de texto conforme chegam.
        """
        sdk = self.provider.get("sdk", "openai_compat")
        if sdk == "anthropic":
            yield from self._stream_anthropic(prompt, images)
        elif sdk == "google":
            yield from self._stream_google(prompt, images)
        else:
            yield from self._stream_openai_compat(prompt, images)

    # ── Implementacoes por provider ──────────────────────────────────────────
    # Logica de negocio omitida intencionalmente — produto comercial ativo
    # Business logic omitted — see live demo

    def _complete_openai_compat(self, prompt: str, images: list = None) -> str:
        raise NotImplementedError

    def _stream_openai_compat(self, prompt: str, images: list = None) -> Iterator[str]:
        raise NotImplementedError

    def _complete_anthropic(self, prompt: str, images: list = None) -> str:
        raise NotImplementedError

    def _stream_anthropic(self, prompt: str, images: list = None) -> Iterator[str]:
        raise NotImplementedError

    def _complete_google(self, prompt: str, images: list = None) -> str:
        raise NotImplementedError

    def _stream_google(self, prompt: str, images: list = None) -> Iterator[str]:
        raise NotImplementedError

    def _complete_ollama(self, prompt: str, images: list = None) -> str:
        raise NotImplementedError
