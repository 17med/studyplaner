"""
Critic Agent – flags unrealistic or low-quality plans.

Reviews both the study plan and the time-estimation report, then either
**approves** the plan or returns actionable feedback for revision.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from agents.base_agent import AgentMessage, BaseAgent, MessageRole

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are the **Critic Agent** in a multi-agent study-planning system.

You receive a study plan (from the Curriculum Agent) and a time-feasibility
report (from the Time Estimation Agent).  Your job is to make the final
quality judgement:

────────────────────────────────────
EVALUATION CRITERIA
────────────────────────────────────
1. **Completeness** – Does the plan cover the topic thoroughly?
2. **Logical ordering** – Are prerequisites taught before dependents?
3. **Realism** – Considering the time report, is the plan achievable?
4. **Resource quality** – Are recommended resources real and reputable?
5. **Learning outcomes** – Are milestones measurable and clear?
6. **Balance** – Is there a healthy mix of theory, practice, and review?
7. **Burnout risk** – Will the student be overwhelmed at any point?

────────────────────────────────────
OUTPUT FORMAT  (strict JSON)
────────────────────────────────────
Return ONLY a JSON object (inside a ```json``` code fence):

```json
{
  "approved": <true|false>,
  "quality_score": <1-10>,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "required_changes": [
    {
      "area": "<which part of the plan>",
      "issue": "<what is wrong>",
      "recommendation": "<how to fix>"
    }
  ],
  "verdict": "<one-paragraph final verdict>"
}
```

RULES
• Be constructive – always explain *why* and give a concrete fix.
• Set `approved` to `true` ONLY if the plan is ready for the student
  with no significant issues remaining.
• If time report flags the plan as infeasible, do NOT approve.
• You MUST approve if quality_score >= 7 and there are no high-severity
  issues.  Do not be needlessly harsh.
• Output ONLY the JSON block – no prose before or after.
"""


class CriticAgent(BaseAgent):
    name = "Critic Agent"
    role = MessageRole.CRITIC
    system_prompt = SYSTEM_PROMPT

    def run(self, context: Dict[str, Any]) -> AgentMessage:
        """
        Review the plan + time report and approve or request revision.

        Expected `context` keys
        -----------------------
        plan          : dict – study plan from Curriculum Agent
        time_report   : dict – report from Time Estimation Agent
        skill_level   : str
        available_hours: float
        round_number  : int  – current revision round
        max_rounds    : int  – total allowed rounds
        """
        plan = context.get("plan", {})
        time_report = context.get("time_report", {})
        round_num = context.get("round_number", 1)
        max_rounds = context.get("max_rounds", 3)

        user_prompt = (
            f"**Revision round:** {round_num} of {max_rounds}\n"
            f"**Student skill level:** {context.get('skill_level', 'beginner')}\n"
            f"**Available hours/week:** {context.get('available_hours', 10)}\n\n"
            f"**Study Plan:**\n```json\n{json.dumps(plan, indent=2)}\n```\n\n"
            f"**Time Feasibility Report:**\n```json\n{json.dumps(time_report, indent=2)}\n```\n\n"
            "Review the plan and time report.  Return your verdict."
        )

        # On the final round, nudge towards approval if plan is reasonable
        if round_num >= max_rounds:
            user_prompt += (
                "\n\n⚠️  This is the FINAL revision round.  If the plan is at"
                " least *acceptable* (score ≥ 6), set `approved: true` with any"
                " remaining suggestions in `weaknesses`."
            )

        raw = self._call_llm(user_prompt)
        review = self._extract_json(raw) or {}
        return self._make_message(raw, data={"review": review})
