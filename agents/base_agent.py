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
    def _clean_json_string(s: str) -> str:
        """Remove common LLM artefacts that break json.loads."""
        # Remove trailing commas before } or ]
        s = re.sub(r",\s*([}\]])", r"\1", s)
        # Remove single-line // comments
        s = re.sub(r"//[^\n]*", "", s)
        # Remove control characters except newlines/tabs
        s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
        return s.strip()

    @staticmethod
    def _try_parse(text: str) -> Optional[Dict]:
        """Try parsing text as JSON, with fallback cleaning."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Try cleaning common issues
        cleaned = BaseAgent._clean_json_string(text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        return None

    @staticmethod
    def _find_matching_brace(text: str, start: int) -> int:
        """Find the index of the closing brace matching the opening one at `start`."""
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\" and in_string:
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
        return -1

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict]:
        """Best-effort extraction of JSON from LLM output."""
        if not text or not text.strip():
            return None

        # 1. Try ```json ... ``` fenced block
        m = re.search(r"```(?:json)?\s*\n?(\{.*?)\n?\s*```", text, re.DOTALL)
        if m:
            result = BaseAgent._try_parse(m.group(1))
            if result:
                return result

        # 2. Try to find the FIRST top-level { and its matching }
        first_brace = text.find("{")
        if first_brace != -1:
            end = BaseAgent._find_matching_brace(text, first_brace)
            if end != -1:
                candidate = text[first_brace : end + 1]
                result = BaseAgent._try_parse(candidate)
                if result:
                    return result

        # 3. Greedy fallback: largest { … } span
        m = re.search(r"(\{.*\})", text, re.DOTALL)
        if m:
            result = BaseAgent._try_parse(m.group(1))
            if result:
                return result

        # 4. Try to fix truncated JSON (missing closing braces/brackets)
        if first_brace != -1:
            fragment = text[first_brace:]
            # Count unmatched braces/brackets
            opens_b = fragment.count("{") - fragment.count("}")
            opens_s = fragment.count("[") - fragment.count("]")
            if opens_b > 0 or opens_s > 0:
                patched = fragment + ("]" * max(opens_s, 0)) + ("}" * max(opens_b, 0))
                result = BaseAgent._try_parse(patched)
                if result:
                    logger.warning("Recovered truncated JSON by closing %d brace(s)", opens_b + opens_s)
                    return result

        logger.warning("_extract_json: could not parse any JSON from text (len=%d)", len(text))
        return None

    # ── abstract entry-point ─────────────────────────────────────────
    def run(self, context: Dict[str, Any]) -> AgentMessage:
        raise NotImplementedError
