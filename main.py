#!/usr/bin/env python3
"""
main.py – CLI entry-point for the Multi-Agent Study Planner.

Usage
─────
  # Interactive mode (asks questions)
  python main.py

  # One-liner
  python main.py --topic "Machine Learning" --level beginner --hours 12 --weeks 6

  # Save result to JSON
  python main.py --topic "Rust Programming" --level intermediate --hours 8 --weeks 4 --output plan.json

Environment Variables
─────────────────────
  NVIDIA_API_KEY   your NVIDIA NIM API key
  NVIDIA_MODEL     model name (default: openai/gpt-oss-120b)
  ...              (see config.py for all options)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from orchestrator import Orchestrator


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
        datefmt="%H:%M:%S",
    )
    # Quiet noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def interactive_input() -> dict:
    """Gather study plan parameters interactively."""
    print("\n🎓  Multi-Agent Study Planner  🎓")
    print("─" * 40)

    topic = input("📚 What do you want to study? ").strip()
    if not topic:
        topic = "Python Programming"
        print(f"   (defaulting to: {topic})")

    print("\n📊 Your current skill level:")
    print("   1. Beginner")
    print("   2. Intermediate")
    print("   3. Advanced")
    level_choice = input("   Choose (1/2/3): ").strip()
    level_map = {"1": "beginner", "2": "intermediate", "3": "advanced"}
    skill_level = level_map.get(level_choice, "beginner")

    hours_str = input("\n⏰ Hours you can study per week (default 10): ").strip()
    available_hours = float(hours_str) if hours_str else 10.0

    weeks_str = input("📅 How many weeks for the plan (default 4): ").strip()
    duration_weeks = int(weeks_str) if weeks_str else 4

    goals = input("🎯 Any specific goals? (optional, press Enter to skip): ").strip()

    return {
        "topic": topic,
        "skill_level": skill_level,
        "available_hours": available_hours,
        "duration_weeks": duration_weeks,
        "goals": goals or None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-Agent AI Study Planner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--topic", "-t", help="Subject to study")
    parser.add_argument(
        "--level", "-l",
        choices=["beginner", "intermediate", "advanced"],
        default="beginner",
        help="Current skill level (default: beginner)",
    )
    parser.add_argument(
        "--hours", "-hr",
        type=float,
        default=10,
        help="Available study hours per week (default: 10)",
    )
    parser.add_argument(
        "--weeks", "-w",
        type=int,
        default=4,
        help="Plan duration in weeks (default: 4)",
    )
    parser.add_argument("--goals", "-g", help="Specific learning goals")
    parser.add_argument(
        "--output", "-o",
        help="Save final plan to this JSON file",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)

    # Gather user input
    if args.topic:
        user_request = {
            "topic": args.topic,
            "skill_level": args.level,
            "available_hours": args.hours,
            "duration_weeks": args.weeks,
            "goals": args.goals,
        }
    else:
        user_request = interactive_input()

    # Run the multi-agent pipeline
    orchestrator = Orchestrator()
    result = orchestrator.run(user_request)

    # Optionally save to file
    if args.output:
        out_path = Path(args.output)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n💾 Plan saved to {out_path.resolve()}")


if __name__ == "__main__":
    main()
