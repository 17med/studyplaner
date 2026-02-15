"""
Curriculum Agent – proposes a structured learning roadmap.

Given a topic, current skill level, and time constraints it produces a
week-by-week study plan with topics, sub-topics, learning objectives,
and recommended resources.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from agents.base_agent import AgentMessage, BaseAgent, MessageRole

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are the **Curriculum Agent** in a multi-agent study-planning system.

Your job is to design a detailed, realistic learning roadmap for the student.

────────────────────────────────────────────
OUTPUT FORMAT  (strict JSON – no extra keys)
────────────────────────────────────────────
Return ONLY a JSON object (inside a ```json``` code fence) with this schema:

```json
{
  "topic": "<main subject>",
  "total_weeks": <int>,
  "hours_per_week": <float>,
  "difficulty_level": "<beginner|intermediate|advanced>",
  "prerequisites": ["..."],
  "weekly_plan": [
    {
      "week": <int>,
      "theme": "<weekly theme>",
      "topics": [
        {
          "name": "<topic>",
          "subtopics": ["..."],
          "learning_objectives": ["..."],
          "estimated_hours": <float>,
          "resources": ["..."]
        }
      ],
      "milestone": "<what the student should be able to do by week end>"
    }
  ],
  "final_outcome": "<what the student achieves after completing the plan>"
}
```

RULES
• Be specific – include real book names, course URLs, or tool names.
• Distribute effort evenly; avoid overloading any single week.
• Include practical projects or exercises where appropriate.
• If the student specifies constraints, honour them.
• Output ONLY the JSON block – no prose before or after.
"""


class CurriculumAgent(BaseAgent):
    name = "Curriculum Agent"
    role = MessageRole.CURRICULUM
    system_prompt = SYSTEM_PROMPT

    def run(self, context: Dict[str, Any]) -> AgentMessage:
        """
        Generate or revise a study plan.

        Expected `context` keys
        -----------------------
        topic            : str   – subject to study
        skill_level      : str   – beginner / intermediate / advanced
        available_hours  : float – hours per week the student can commit
        duration_weeks   : int   – desired plan length in weeks
        goals            : str   – (optional) specific goals
        critic_feedback  : str   – (optional) feedback from the Critic Agent
        time_feedback    : str   – (optional) feedback from Time Estimation Agent
        previous_plan    : dict  – (optional) the plan to revise
        """
        # Build the user prompt dynamically
        parts = [
            f"**Topic:** {context.get('topic', 'General programming')}",
            f"**Current skill level:** {context.get('skill_level', 'beginner')}",
            f"**Available hours/week:** {context.get('available_hours', 10)}",
            f"**Desired duration:** {context.get('duration_weeks', 4)} weeks",
        ]
        if context.get("goals"):
            parts.append(f"**Specific goals:** {context['goals']}")

        # If this is a revision round, include the feedback
        if context.get("critic_feedback") or context.get("time_feedback"):
            parts.append("\n--- FEEDBACK FROM OTHER AGENTS (address every point) ---")
            if context.get("critic_feedback"):
                parts.append(f"**Critic Agent feedback:**\n{context['critic_feedback']}")
            if context.get("time_feedback"):
                parts.append(f"**Time Estimation Agent feedback:**\n{context['time_feedback']}")
            if context.get("previous_plan"):
                parts.append(
                    f"**Previous plan to revise:**\n```json\n"
                    f"{json.dumps(context['previous_plan'], indent=2)}\n```"
                )

        user_prompt = "\n".join(parts)
        raw = self._call_llm(user_prompt)

        plan_data = self._extract_json(raw) or {}
        return self._make_message(raw, data={"plan": plan_data})
