"""
Base Agent and Agent Message types.

Every agent inherits from `BaseAgent` and implements `run()`.
Communication between agents uses structured `AgentMessage` dicts so the
orchestrator can log, inspect, and route data transparently.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from llm_provider import query_llm

logger = logging.getLogger(__name__)


# ── Message types ───────────────────────────────────────────────────────
class MessageRole(str, Enum):
    CURRICULUM = "curriculum_agent"
    TIME_ESTIMATION = "time_estimation_agent"
    CRITIC = "critic_agent"
    ORCHESTRATOR = "orchestrator"
    USER = "user"


@dataclass
class AgentMessage:
    """Structured message exchanged between agents."""
    role: MessageRole
    content: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "content": self.content,
            "data": self.data,
            "timestamp": self.timestamp,
        }


# ── Base agent ──────────────────────────────────────────────────────────
class BaseAgent:
    """
    Abstract base class for every agent in the system.

    Sub-classes must define:
        name        – human-readable label
        role        – MessageRole enum value
        system_prompt – the system prompt that primes the LLM
    and implement:
        run(context) -> AgentMessage
    """

    name: str = "BaseAgent"
    role: MessageRole = MessageRole.USER
    system_prompt: str = ""

    def __init__(self):
        self.history: List[AgentMessage] = []

    # ── helpers ──────────────────────────────────────────────────────
    def _call_llm(self, user_prompt: str) -> str:
        """Query the LLM with this agent's system prompt."""
        logger.info("[%s] calling LLM …", self.name)
        response = query_llm(self.system_prompt, user_prompt)
        logger.debug("[%s] raw response:\n%s", self.name, response[:500])
        return response

    def _make_message(self, content: str, data: Optional[Dict] = None) -> AgentMessage:
        msg = AgentMessage(role=self.role, content=content, data=data or {})
        self.history.append(msg)
        return msg

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict]:
        """Best-effort extraction of JSON from LLM output."""
        # Try to find a JSON block delimited by ```json ... ```
        m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # Try to find raw JSON object
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return None

    # ── abstract entry-point ─────────────────────────────────────────
    def run(self, context: Dict[str, Any]) -> AgentMessage:
        raise NotImplementedError
