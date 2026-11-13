"""
CLI tool to prevent concept, layout, palette, and naming bias in py5 media art workflows.

Usage:
  uv run python scripts/check_diversity.py plan
  uv run python scripts/check_diversity.py check <work_name>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.diversity import check_sketch_diversity, generate_plan_prescription


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Portfolio diversity prescription and anti-bias sketch validator."
    )
    subparsers = parser.add_subparsers(dest="command")

    plan_parser = subparsers.add_parser(
        "plan",
        help="Analyze WORKS.md and emit a 5-axis diversity prescription for the next artwork.",
    )
    plan_parser.add_argument(
        "--recent",
        type=int,
        default=20,
        help="Number of recent works to inspect (default: 20).",
    )

    check_parser = subparsers.add_parser(
        "check",
        help="Audit sketch/<work_name>/main.py against anti-bias and diversity rules.",
    )
    check_parser.add_argument(
        "work_name",
        help="Directory name of the sketch under sketch/<work_name>.",
    )

    args = parser.parse_args()

    if args.command in (None, "plan"):
        recent = getattr(args, "recent", 20)
        print(generate_plan_prescription(recent_count=recent))
        return 0

    if args.command == "check":
        report = check_sketch_diversity(args.work_name)
        if report.passed:
            print(f"[PASS] Diversity & anti-bias check succeeded for '{args.work_name}'.")
            if report.warnings:
                for w in report.warnings:
                    print(f"  [WARN] {w}")
            return 0
        else:
            print(f"[FAIL] Diversity & anti-bias check failed for '{args.work_name}':")
            for idx, err in enumerate(report.errors, 1):
                print(f"  {idx}. {err}")
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
