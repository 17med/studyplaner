"""
Time Estimation Agent – validates schedule feasibility.

Receives a proposed study plan and checks whether the time allocations
are realistic given the student's available hours, typical learning
speeds, and topic complexity.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from agents.base_agent import AgentMessage, BaseAgent, MessageRole

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are the **Time Estimation Agent** in a multi-agent study-planning system.

Your job is to audit a proposed study plan and determine whether the
time allocations are **realistic and feasible**.

────────────────────────────────────
EVALUATION CRITERIA
────────────────────────────────────
1. **Total hours math** – Does the sum of estimated hours per week stay
   within the student's available hours?  Allow ≤ 10 % buffer.
2. **Per-topic realism** – Is the time allocated for each topic enough
   to actually learn it?  Consider difficulty and prerequisites.
3. **Cognitive load** – Are weeks balanced, or is there a spike in
   difficulty / hours that could cause burnout?
4. **Buffer time** – Is there room for review, catch-up, and rest?

────────────────────────────────────
OUTPUT FORMAT  (strict JSON)
────────────────────────────────────
Return ONLY a JSON object (inside a ```json``` code fence):

```json
{
  "feasible": <true|false>,
  "overall_score": <1-10>,
  "total_hours_proposed": <float>,
  "total_hours_available": <float>,
  "weekly_analysis": [
    {
      "week": <int>,
      "proposed_hours": <float>,
      "realistic_hours_needed": <float>,
      "is_feasible": <true|false>,
      "notes": "<explanation>"
    }
  ],
  "issues": [
    {
      "severity": "<high|medium|low>",
      "description": "<what is wrong>",
      "suggestion": "<how to fix it>"
    }
  ],
  "summary": "<one-paragraph overall assessment>"
}
```

RULES
• Be quantitative – cite hours, not vague words.
• Consider that beginners learn slower than experts.
• Practical coding / exercises generally take 1.5×–2× the lecture time.
• Output ONLY the JSON block – no prose before or after.
"""


class TimeEstimationAgent(BaseAgent):
    name = "Time Estimation Agent"
    role = MessageRole.TIME_ESTIMATION
    system_prompt = SYSTEM_PROMPT

    def run(self, context: Dict[str, Any]) -> AgentMessage:
        """
        Validate the time feasibility of a study plan.

        Expected `context` keys
        -----------------------
        plan             : dict  – the plan from the Curriculum Agent
        available_hours  : float – hours per week
        skill_level      : str
        duration_weeks   : int
        """
        plan = context.get("plan", {})
        user_prompt = (
            f"**Student available hours/week:** {context.get('available_hours', 10)}\n"
            f"**Skill level:** {context.get('skill_level', 'beginner')}\n"
            f"**Planned duration:** {context.get('duration_weeks', 4)} weeks\n\n"
            f"**Proposed study plan:**\n```json\n{json.dumps(plan, indent=2)}\n```\n\n"
            "Analyse the plan above and return your time-feasibility report."
        )

        raw = self._call_llm(user_prompt)
        report = self._extract_json(raw) or {}
        return self._make_message(raw, data={"time_report": report})
