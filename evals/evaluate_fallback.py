"""Evaluate the deterministic routing fallback with zero service dependencies.

Run from the repository root:
    python evals/evaluate_fallback.py --min-accuracy 1.0
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from services.fallback_router import classify_fallback  # noqa: E402


def evaluate(dataset: Path) -> tuple[int, int, list[dict]]:
    passed = 0
    count = 0
    failures: list[dict] = []
    for line_no, raw_line in enumerate(dataset.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        item = json.loads(raw_line)
        expected = item["expected_path"]
        actual = classify_fallback(item["message"], item.get("active_topic"))
        count += 1
        if actual == expected:
            passed += 1
        else:
            failures.append({"line": line_no, "message": item["message"], "expected": expected, "actual": actual})
    if not count:
        raise ValueError("Empty evaluation dataset")
    return passed, count, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "evals" / "routing_cases.jsonl")
    parser.add_argument("--min-accuracy", type=float, default=1.0)
    args = parser.parse_args()
    if not 0 <= args.min_accuracy <= 1:
        parser.error("--min-accuracy must be between 0 and 1")
    passed, total, failures = evaluate(args.dataset)
    accuracy = passed / total
    print(f"Fallback routing accuracy: {passed}/{total} ({accuracy:.1%})")
    for row in failures:
        print(f"  Line {row['line']}: {row['message']!r} => {row['actual']} (expected {row['expected']})")
    return 0 if accuracy >= args.min_accuracy else 1


if __name__ == "__main__":
    raise SystemExit(main())
