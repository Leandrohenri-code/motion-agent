"""
Cliente universal de IA com suporte a qualquer provider registrado.
"""

import time
import json
import httpx
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
                err = str(e)
                # Não retentar erros de cliente (4xx), exceto 429 (rate limit)
                if "400" in err or "401" in err or "403" in err or "404" in err:
                    raise   # falha imediata — não adianta retentar
                if attempt == 2:
                    raise
                if "429" in err:
                    # Rate limit — espera mais antes de retentar
                    time.sleep(20 * (attempt + 1))
                else:
                    time.sleep(2 ** attempt)

    def stream(self, prompt: str, images: list = None) -> Iterator[str]:
        sdk = self.provider.get("sdk", "openai_compat")
        if sdk == "anthropic":
            yield from self._stream_anthropic(prompt, images)
        elif sdk == "google":
            yield from self._stream_google(prompt, images)
        else:
            yield from self._stream_openai_compat(prompt, images)

    # ── OpenAI-compatible ────────────────────────────────────────────────────

    def _complete_openai_compat(self, prompt: str, images: list = None) -> str:
        messages = self._build_messages(prompt, images)
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # OpenRouter extra headers
        if self.provider_id == "openrouter":
            headers["HTTP-Referer"] = "https://motion-agent.app"
            headers["X-Title"] = "Motion Agent"

        url = f"{self.base_url}/chat/completions"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _stream_openai_compat(self, prompt: str, images: list = None) -> Iterator[str]:
        messages = self._build_messages(prompt, images)
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.provider_id == "openrouter":
            headers["HTTP-Referer"] = "https://motion-agent.app"
            headers["X-Title"] = "Motion Agent"

        url = f"{self.base_url}/chat/completions"
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk["choices"][0].get("delta", {})
                            text = delta.get("content", "")
                            if text:
                                yield text
                        except Exception:
                            continue

    # ── Anthropic ────────────────────────────────────────────────────────────

    def _complete_anthropic(self, prompt: str, images: list = None) -> str:
        content = []
        if images:
            for img in images:
                if img.startswith("data:"):
                    mime = img.split(";")[0].split(":")[1]
                    data = img.split(",")[1]
                    content.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": mime, "data": data}
                    })
                else:
                    content.append({
                        "type": "image",
                        "source": {"type": "url", "url": img}
                    })
        content.append({"type": "text", "text": prompt})

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": content}],
        }
        if self.system_prompt:
            payload["system"] = self.system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        url = "https://api.anthropic.com/v1/messages"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    def _stream_anthropic(self, prompt: str, images: list = None) -> Iterator[str]:
        content = []
        if images:
            for img in images:
                if img.startswith("data:"):
                    mime = img.split(";")[0].split(":")[1]
                    data = img.split(",")[1]
                    content.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": mime, "data": data}
                    })
        content.append({"type": "text", "text": prompt})

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": content}],
            "stream": True,
        }
        if self.system_prompt:
            payload["system"] = self.system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        url = "https://api.anthropic.com/v1/messages"
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "content_block_delta":
                            text = event.get("delta", {}).get("text", "")
                            if text:
                                yield text
                    except Exception:
                        continue

    # ── Google Gemini ────────────────────────────────────────────────────────

    def _complete_google(self, prompt: str, images: list = None) -> str:
        parts = []
        if images:
            for img in images:
                if img.startswith("data:"):
                    mime = img.split(";")[0].split(":")[1]
                    data = img.split(",")[1]
                    parts.append({"inlineData": {"mimeType": mime, "data": data}})
        parts.append({"text": prompt})

        contents = [{"parts": parts}]
        if self.system_prompt:
            contents = [{"role": "user", "parts": [{"text": self.system_prompt}]},
                        {"role": "model", "parts": [{"text": "Entendido."}]},
                        {"role": "user", "parts": parts}]

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def _stream_google(self, prompt: str, images: list = None) -> Iterator[str]:
        parts = []
        if images:
            for img in images:
                if img.startswith("data:"):
                    mime = img.split(";")[0].split(":")[1]
                    data_b64 = img.split(",")[1]
                    parts.append({"inlineData": {"mimeType": mime, "data": data_b64}})
        parts.append({"text": prompt})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?key={self.api_key}&alt=sse"
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    try:
                        chunk = json.loads(line[6:])
                        text = chunk["candidates"][0]["content"]["parts"][0].get("text", "")
                        if text:
                            yield text
                    except Exception:
                        continue

    # ── Ollama ───────────────────────────────────────────────────────────────

    def _complete_ollama(self, prompt: str, images: list = None) -> str:
        payload = {
            "model": self.model,
            "prompt": f"{self.system_prompt}\n\n{prompt}" if self.system_prompt else prompt,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        if images:
            b64_images = []
            for img in images:
                if img.startswith("data:"):
                    b64_images.append(img.split(",")[1])
            if b64_images:
                payload["images"] = b64_images

        url = f"{self.base_url}/api/generate"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()["response"]
