"""
Orchestrator – coordinates the multi-agent collaboration loop.

Flow
────
1. Curriculum Agent proposes a study plan.
2. Time Estimation Agent evaluates whether the schedule is feasible.
3. Critic Agent reviews both and either approves or requests revisions.
4. If not approved, the cycle repeats (up to MAX_REVISION_ROUNDS).
5. The final validated plan is returned.
"""

from __future__ import annotations

import json
import logging
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import config
from agents.base_agent import AgentMessage, MessageRole
from agents.critic_agent import CriticAgent
from agents.curriculum_agent import CurriculumAgent
from agents.time_estimation_agent import TimeEstimationAgent

logger = logging.getLogger(__name__)


# ── Pretty-printing helpers ─────────────────────────────────────────────
class Colors:
    HEADER  = "\033[95m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    BOLD    = "\033[1m"
    RESET   = "\033[0m"


def _banner(text: str, color: str = Colors.HEADER) -> None:
    width = 70
    print(f"\n{color}{'═' * width}")
    print(f"  {text}")
    print(f"{'═' * width}{Colors.RESET}\n")


def _section(title: str, body: str, color: str = Colors.CYAN) -> None:
    print(f"{color}{Colors.BOLD}── {title} ──{Colors.RESET}")
    # Indent the body for readability
    for line in body.strip().splitlines():
        print(f"  {line}")
    print()


# ── Collaboration log entry ─────────────────────────────────────────────
@dataclass
class LogEntry:
    round: int
    agent: str
    timestamp: str
    summary: str
    data: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════
# Orchestrator
# ═══════════════════════════════════════════════════════════════════════
class Orchestrator:
    """
    Drives the agent collaboration loop until the Critic approves the
    plan or the maximum number of revision rounds is reached.
    """

    def __init__(self):
        self.curriculum_agent = CurriculumAgent()
        self.time_agent = TimeEstimationAgent()
        self.critic_agent = CriticAgent()
        self.max_rounds = config.MAX_REVISION_ROUNDS
        self.log: List[LogEntry] = []

    # ── internal helpers ─────────────────────────────────────────────
    def _log(self, round_num: int, agent: str, summary: str, data: Dict = None):
        entry = LogEntry(
            round=round_num,
            agent=agent,
            timestamp=datetime.now().isoformat(),
            summary=summary,
            data=data or {},
        )
        self.log.append(entry)
        logger.info("[Round %d][%s] %s", round_num, agent, summary)

    # ── main loop ────────────────────────────────────────────────────
    def run(self, user_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the full multi-agent study-plan generation loop.

        Parameters
        ----------
        user_request : dict with keys
            topic, skill_level, available_hours, duration_weeks, goals (opt)

        Returns
        -------
        dict with keys: plan, time_report, review, rounds, log
        """
        _banner("🎓  MULTI-AGENT STUDY PLANNER  🎓")
        print(f"  Topic          : {user_request.get('topic')}")
        print(f"  Skill level    : {user_request.get('skill_level')}")
        print(f"  Hours/week     : {user_request.get('available_hours')}")
        print(f"  Duration       : {user_request.get('duration_weeks')} weeks")
        if user_request.get("goals"):
            print(f"  Goals          : {user_request['goals']}")
        print()

        plan_data: Dict = {}
        time_report: Dict = {}
        review: Dict = {}
        critic_feedback: str = ""
        time_feedback: str = ""
        approved = False

        for round_num in range(1, self.max_rounds + 1):
            _banner(f"📋  ROUND {round_num} / {self.max_rounds}", Colors.YELLOW)

            # ─── Step 1: Curriculum Agent ───────────────────────────
            _section("Step 1 → Curriculum Agent", "Generating study plan …", Colors.BLUE)
            curriculum_ctx = {
                **user_request,
                "critic_feedback": critic_feedback,
                "time_feedback": time_feedback,
                "previous_plan": plan_data if round_num > 1 else None,
            }
            curriculum_msg = self.curriculum_agent.run(curriculum_ctx)
            plan_data = curriculum_msg.data.get("plan", {})
            self._log(round_num, "Curriculum Agent", "Plan generated", plan_data)

            if plan_data:
                _section("📝 Proposed Plan Summary", _summarise_plan(plan_data), Colors.GREEN)
            else:
                _section("⚠️  Warning", "Could not parse plan JSON from Curriculum Agent output.", Colors.RED)
                _section("Raw output", curriculum_msg.content[:1000], Colors.YELLOW)

            # ─── Step 2: Time Estimation Agent ─────────────────────
            _section("Step 2 → Time Estimation Agent", "Validating schedule feasibility …", Colors.BLUE)
            time_ctx = {
                "plan": plan_data,
                "available_hours": user_request.get("available_hours", 10),
                "skill_level": user_request.get("skill_level", "beginner"),
                "duration_weeks": user_request.get("duration_weeks", 4),
            }
            time_msg = self.time_agent.run(time_ctx)
            time_report = time_msg.data.get("time_report", {})
            self._log(round_num, "Time Estimation Agent", "Time report generated", time_report)

            if time_report:
                _section("⏱️  Time Report Summary", _summarise_time(time_report), Colors.GREEN)
            else:
                _section("⚠️  Warning", "Could not parse time report JSON.", Colors.RED)

            # ─── Step 3: Critic Agent ──────────────────────────────
            _section("Step 3 → Critic Agent", "Reviewing plan quality …", Colors.BLUE)
            critic_ctx = {
                "plan": plan_data,
                "time_report": time_report,
                "skill_level": user_request.get("skill_level", "beginner"),
                "available_hours": user_request.get("available_hours", 10),
                "round_number": round_num,
                "max_rounds": self.max_rounds,
            }
            critic_msg = self.critic_agent.run(critic_ctx)
            review = critic_msg.data.get("review", {})
            self._log(round_num, "Critic Agent", "Review complete", review)

            if review:
                _section("🔍 Critic Verdict", _summarise_review(review), Colors.GREEN)
            else:
                _section("⚠️  Warning", "Could not parse critic JSON.", Colors.RED)

            # ─── Check approval ────────────────────────────────────
            approved = review.get("approved", False)
            if approved:
                _banner("✅  PLAN APPROVED!", Colors.GREEN)
                break

            # Prepare feedback for next round
            critic_feedback = review.get("verdict", critic_msg.content)
            changes = review.get("required_changes", [])
            if changes:
                change_lines = "\n".join(
                    f"  • [{c.get('area', '?')}] {c.get('issue', '')} → {c.get('recommendation', '')}"
                    for c in changes
                )
                critic_feedback += "\n\nRequired changes:\n" + change_lines

            time_issues = time_report.get("issues", [])
            if time_issues:
                time_feedback = "\n".join(
                    f"  • [{i.get('severity', '?')}] {i.get('description', '')} → {i.get('suggestion', '')}"
                    for i in time_issues
                )
            else:
                time_feedback = time_report.get("summary", "")

            if round_num < self.max_rounds:
                _section(
                    "🔄 Revising …",
                    f"Critic did not approve. Sending feedback for round {round_num + 1}.",
                    Colors.YELLOW,
                )

        if not approved:
            _banner("⚠️  MAX ROUNDS REACHED – returning best plan", Colors.YELLOW)

        # ── Build final result ──────────────────────────────────────
        result = {
            "plan": plan_data,
            "time_report": time_report,
            "review": review,
            "approved": approved,
            "rounds": round_num,
            "log": [
                {
                    "round": e.round,
                    "agent": e.agent,
                    "timestamp": e.timestamp,
                    "summary": e.summary,
                }
                for e in self.log
            ],
        }

        _print_final_plan(result)
        return result


# ═══════════════════════════════════════════════════════════════════════
# Summary / pretty-print helpers
# ═══════════════════════════════════════════════════════════════════════
def _summarise_plan(plan: Dict) -> str:
    lines = [
        f"Topic         : {plan.get('topic', '?')}",
        f"Duration      : {plan.get('total_weeks', '?')} weeks",
        f"Hours/week    : {plan.get('hours_per_week', '?')}",
        f"Difficulty    : {plan.get('difficulty_level', '?')}",
        f"Final outcome : {plan.get('final_outcome', '?')}",
    ]
    weekly = plan.get("weekly_plan", [])
    if weekly:
        lines.append(f"\nWeek-by-week ({len(weekly)} weeks):")
        for w in weekly:
            topics = ", ".join(t.get("name", "?") for t in w.get("topics", []))
            lines.append(f"  Week {w.get('week', '?')}: {w.get('theme', '?')}  [{topics}]")
    return "\n".join(lines)


def _summarise_time(report: Dict) -> str:
    lines = [
        f"Feasible      : {'Yes ✅' if report.get('feasible') else 'No ❌'}",
        f"Score         : {report.get('overall_score', '?')} / 10",
        f"Proposed hrs  : {report.get('total_hours_proposed', '?')}",
        f"Available hrs : {report.get('total_hours_available', '?')}",
    ]
    issues = report.get("issues", [])
    if issues:
        lines.append(f"\nIssues ({len(issues)}):")
        for i in issues:
            lines.append(f"  [{i.get('severity', '?')}] {i.get('description', '?')}")
    return "\n".join(lines)


def _summarise_review(review: Dict) -> str:
    status = "APPROVED ✅" if review.get("approved") else "NOT APPROVED ❌"
    lines = [
        f"Verdict       : {status}",
        f"Quality score : {review.get('quality_score', '?')} / 10",
    ]
    strengths = review.get("strengths", [])
    if strengths:
        lines.append("Strengths:")
        for s in strengths:
            lines.append(f"  ✓ {s}")
    weaknesses = review.get("weaknesses", [])
    if weaknesses:
        lines.append("Weaknesses:")
        for w in weaknesses:
            lines.append(f"  ✗ {w}")
    changes = review.get("required_changes", [])
    if changes:
        lines.append("Required changes:")
        for c in changes:
            lines.append(f"  → [{c.get('area', '?')}] {c.get('recommendation', '?')}")
    if review.get("verdict"):
        lines.append(f"\n{review['verdict']}")
    return "\n".join(lines)


def _print_final_plan(result: Dict) -> None:
    _banner("📖  FINAL STUDY PLAN", Colors.GREEN)

    plan = result.get("plan", {})
    if not plan:
        print("  (no structured plan available)")
        return

    print(f"  {Colors.BOLD}Topic:{Colors.RESET}      {plan.get('topic', '?')}")
    print(f"  {Colors.BOLD}Duration:{Colors.RESET}   {plan.get('total_weeks', '?')} weeks")
    print(f"  {Colors.BOLD}Hours/wk:{Colors.RESET}   {plan.get('hours_per_week', '?')}")
    print(f"  {Colors.BOLD}Level:{Colors.RESET}      {plan.get('difficulty_level', '?')}")
    prereqs = plan.get("prerequisites", [])
    if prereqs:
        print(f"  {Colors.BOLD}Prerequisites:{Colors.RESET} {', '.join(prereqs)}")
    print()

    for week in plan.get("weekly_plan", []):
        print(f"  {Colors.CYAN}{Colors.BOLD}Week {week.get('week', '?')}: {week.get('theme', '')}{Colors.RESET}")
        for topic in week.get("topics", []):
            hrs = topic.get("estimated_hours", "?")
            print(f"    • {topic.get('name', '?')} ({hrs}h)")
            for obj in topic.get("learning_objectives", []):
                print(f"        ◦ {obj}")
            resources = topic.get("resources", [])
            if resources:
                print(f"        📚 {', '.join(resources)}")
        milestone = week.get("milestone", "")
        if milestone:
            print(f"    🏁 Milestone: {milestone}")
        print()

    outcome = plan.get("final_outcome", "")
    if outcome:
        print(f"  {Colors.GREEN}{Colors.BOLD}🎯 Final Outcome:{Colors.RESET} {outcome}")

    # Print approval status
    print()
    if result.get("approved"):
        print(f"  {Colors.GREEN}Status: APPROVED ✅  (after {result.get('rounds', '?')} round(s)){Colors.RESET}")
    else:
        print(f"  {Colors.YELLOW}Status: BEST EFFORT ⚠️  (after {result.get('rounds', '?')} round(s)){Colors.RESET}")
    print()

    # Agent collaboration log
    log = result.get("log", [])
    if log:
        print(f"  {Colors.BOLD}Agent Collaboration Log:{Colors.RESET}")
        for entry in log:
            print(f"    Round {entry['round']} │ {entry['agent']:<25} │ {entry['summary']}")
    print()
