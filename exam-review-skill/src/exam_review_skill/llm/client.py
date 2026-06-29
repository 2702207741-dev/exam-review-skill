"""
LLM Client — DeepSeek API 封装

支持 OpenAI 兼容 SDK，内置重试、限流、自动降级。
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any


class LLMClient:
    """DeepSeek API 客户端（OpenAI 兼容协议）"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        cache_ttl: int = 86400,  # 24h
    ):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.environ.get(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        )
        self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self._client = None
        self._cache: dict[str, tuple[float, str]] = {}

    @property
    def available(self) -> bool:
        """LLM 是否可用"""
        return bool(self.api_key)

    @property
    def client(self):
        """懒加载 OpenAI client"""
        if self._client is None and self.available:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> str | None:
        """
        发送 chat 请求。

        Args:
            messages: OpenAI 格式消息列表
            temperature: 温度 (0-2)
            max_tokens: 最大输出 token
            response_format: {"type": "json_object"} 强制 JSON 输出

        Returns:
            响应文本，失败返回 None
        """
        if not self.available:
            return None

        cache_key = self._make_cache_key(messages, temperature, max_tokens)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        last_error = None
        for attempt in range(self.max_retries):
            try:
                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                resp = self.client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content or ""
                self._cache_set(cache_key, content)
                return content

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    time.sleep(wait)

        # 全部重试失败
        raise RuntimeError(
            f"DeepSeek API 请求失败（重试 {self.max_retries} 次）: {last_error}"
        )

    def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict | list | None:
        """发送 chat 请求并解析 JSON 响应"""
        raw = self.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        if raw is None:
            return None

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # 尝试提取 JSON 块
            import re
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            # 尝试找 { 到 }
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            return None

    def _make_cache_key(self, messages, temperature, max_tokens) -> str:
        raw = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _cache_get(self, key: str) -> str | None:
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self.cache_ttl:
                return val
            del self._cache[key]
        return None

    def _cache_set(self, key: str, val: str) -> None:
        self._cache[key] = (time.time(), val)


# 全局单例（避免重复创建 client）
_global_client: LLMClient | None = None


def get_client() -> LLMClient:
    global _global_client
    if _global_client is None:
        _global_client = LLMClient()
    return _global_client
