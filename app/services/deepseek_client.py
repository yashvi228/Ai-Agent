from __future__ import annotations

import json
from typing import Dict, Iterable, List, Optional

import requests
from flask import current_app


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout_sec: float) -> None:
        self.api_key = (api_key or "").strip()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_sec = timeout_sec

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def stream_chat(self, messages: List[Dict[str, str]]) -> Iterable[str]:
        """Stream tokens from DeepSeek using OpenAI-compatible streaming API.

        Expects server-sent 'data: {json}' lines; yields content deltas as plain text.
        """
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is empty; set it in your .env and restart the server")
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        with requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout_sec,
            stream=True,
        ) as r:
            try:
                r.raise_for_status()
            except requests.HTTPError as e:
                # Surface response body to caller for clarity (e.g., 401 Unauthorized)
                detail = ""
                try:
                    detail = r.text
                except Exception:
                    pass
                msg = f"{e}. Response: {detail}" if detail else str(e)
                raise requests.HTTPError(msg) from e
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    data = line[len("data: ") :].strip()
                elif line == "data: [DONE]":
                    break
                else:
                    continue

                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                # OpenAI-like schema: choices[].delta.content
                try:
                    delta = obj["choices"][0]["delta"].get("content")
                except Exception:
                    delta = None
                if delta:
                    yield delta


def get_deepseek_client() -> DeepSeekClient:
    cfg = current_app.config
    return DeepSeekClient(
        api_key=cfg["DEEPSEEK_API_KEY"],
        base_url=cfg["DEEPSEEK_BASE_URL"],
        model=cfg["DEEPSEEK_MODEL"],
        timeout_sec=cfg["REQUEST_TIMEOUT_SEC"],
    )

