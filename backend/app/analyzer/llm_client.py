import json
import time

from app import config


class LLMClient:
    def __init__(self):
        self.api_key = getattr(config, "LLM_API_KEY", "") or ""
        self.base_url = getattr(config, "LLM_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1"
        self.model = getattr(config, "LLM_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
        self.available = bool(self.api_key)
        if self.available:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

    def is_available(self) -> bool:
        return self.available

    def chat_json(self, system_prompt: str, user_prompt: str, max_retries: int = 2) -> dict:
        if not self.available:
            raise RuntimeError("LLM 未配置")
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    timeout=60,
                )
                content = response.choices[0].message.content
                return json.loads(content)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(2)
        raise last_exception
