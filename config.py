"""
Configuration for the Multi-Agent Study Planner.

Uses NVIDIA NIM API (OpenAI-compatible) with gpt-oss-120b.
"""

import os

# ── NVIDIA NIM API ──────────────────────────────────────────────────────
NVIDIA_BASE_URL: str = os.getenv(
    "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
)
NVIDIA_API_KEY: str = os.getenv(
    "NVIDIA_API_KEY",
    "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",
)
NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "openai/gpt-oss-120b")

# ── Generation parameters ──────────────────────────────────────────────
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))

# ── Orchestrator settings ──────────────────────────────────────────────
MAX_REVISION_ROUNDS: int = int(os.getenv("MAX_REVISION_ROUNDS", "3"))
