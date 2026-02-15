"""
LLM Provider – NVIDIA NIM API via OpenAI SDK.

Uses the official `openai` Python package pointed at NVIDIA's endpoint
with the openai/gpt-oss-120b model.
"""

from __future__ import annotations

import logging

from openai import OpenAI

import config

logger = logging.getLogger(__name__)

# ── Singleton client ────────────────────────────────────────────────────
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=config.NVIDIA_BASE_URL,
            api_key=config.NVIDIA_API_KEY,
        )
        logger.info(
            "OpenAI client initialised → %s  model=%s",
            config.NVIDIA_BASE_URL,
            config.NVIDIA_MODEL,
        )
    return _client


def query_llm(system_prompt: str, user_prompt: str) -> str:
    """Send a (system, user) message pair and return the assistant reply."""
    client = _get_client()
    logger.debug("query_llm  model=%s  user_prompt=%s…", config.NVIDIA_MODEL, user_prompt[:80])

    completion = client.chat.completions.create(
        model=config.NVIDIA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS,
    )
    content = completion.choices[0].message.content
    logger.debug("query_llm  response length=%d", len(content or ""))
    return content or ""
