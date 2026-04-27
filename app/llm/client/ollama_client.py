import json
from typing import Any

import requests


class OllamaClient:
    def __init__(self, base_url: str, model: str, temperature: float, request_timeout_sec: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.request_timeout_sec = request_timeout_sec

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }
        resp = requests.post(url, json=payload, timeout=self.request_timeout_sec)
        resp.raise_for_status()
        data = self._decode_response_json(resp.text)
        text = data.get("response", "")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("LLM returned empty response")
        return text

    def _decode_response_json(self, response_text: str) -> dict[str, Any]:
        """Handle both single JSON and NDJSON responses from Ollama variants."""
        try:
            data = json.loads(response_text)
            if isinstance(data, dict):
                return data
            raise ValueError("Unexpected non-object JSON payload from Ollama")
        except json.JSONDecodeError:
            pass

        chunks: list[dict[str, Any]] = []
        for raw_line in response_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                snippet = line[:240]
                raise ValueError(f"Invalid Ollama JSON line: {snippet}") from exc
            if isinstance(item, dict):
                chunks.append(item)

        if not chunks:
            snippet = response_text[:400]
            raise ValueError(f"Unable to parse Ollama response as JSON/NDJSON: {snippet}")

        combined = "".join(str(chunk.get("response", "")) for chunk in chunks)
        return {
            "response": combined,
            "done": bool(chunks[-1].get("done", False)),
        }
