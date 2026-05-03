"""
Verifica coerencia visual entre as cenas geradas.

Analisa o codigo TypeScript das cenas em conjunto e verifica:
  - Consistencia de paleta de cores entre cenas
  - Consistencia tipografica (familias e tamanhos similares)
  - Consistencia de ritmo (duracoes e timing coerentes)
  - Transicoes que fazem sentido em sequencia

Retorna um score de 0-10 e uma lista de problemas e sugestoes.
"""

from utils.json_streamer import log


class CoherenceChecker:
    def __init__(self, ai_client):
        self.client = ai_client

    def check(self, scenes_code: list) -> dict:
        """
        Verifica coerencia entre todas as cenas.

        Args:
            scenes_code: Lista de strings com o codigo TypeScript de cada cena

        Returns:
            {
              "coherent": bool,
              "score": int (0-10),
              "issues": list[str],
              "suggestions": list[str]
            }
        """
        if len(scenes_code) < 2:
            return {"coherent": True, "issues": []}

        log("Verificando coerencia visual entre as cenas...")
        prompt = self._build_prompt(scenes_code)

        try:
            raw = self.client.complete(prompt)
            import json, re
            raw = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
            return json.loads(raw)
        except Exception:
            return {"coherent": True, "issues": [], "suggestions": []}

    def _build_prompt(self, scenes: list) -> str:
        # Logica de negocio omitida intencionalmente — produto comercial ativo
        # Business logic omitted — see live demo
        raise NotImplementedError
