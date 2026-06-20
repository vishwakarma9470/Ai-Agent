
from __future__ import annotations

import os
import re
import json
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def extract_json_object(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


class LLMClient:
    """
    OpenAI wrapper with safe fallback.
    If OPENAI_API_KEY is missing, the pipeline still works with local deterministic planning.
    """

    def __init__(self, model: Optional[str] = None, max_prompt_chars: int = 14000):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_prompt_chars = max_prompt_chars
        self.client = None
        self.available = False

        if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
            try:
                self.client = OpenAI()
                self.available = True
            except Exception:
                self.available = False

    def _clip(self, text: str) -> str:
        return (text or "")[: self.max_prompt_chars]

    def json_chat(self, system: str, user: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        if not self.available:
            return fallback
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self._clip(system)},
                    {"role": "user", "content": self._clip(user)},
                ],
            )
            data = extract_json_object(response.choices[0].message.content or "{}")
            return data or fallback
        except Exception as exc:
            out = dict(fallback)
            out["_llm_error"] = str(exc)
            return out

    def text_chat(self, system: str, user: str, fallback: str) -> str:
        if not self.available:
            return fallback
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": self._clip(system)},
                    {"role": "user", "content": self._clip(user)},
                ],
            )
            return response.choices[0].message.content or fallback
        except Exception:
            return fallback
