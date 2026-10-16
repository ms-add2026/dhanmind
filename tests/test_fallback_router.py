"""Hermetic routing regression test: no Ollama, Finnhub or server needed."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from services.fallback_router import classify_fallback  # noqa: E402


class FallbackRoutingTests(unittest.TestCase):
    def test_golden_cases(self):
        dataset = ROOT / "evals" / "routing_cases.jsonl"
        cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(cases), 20)
        for case in cases:
            with self.subTest(message=case["message"]):
                self.assertEqual(
                    classify_fallback(case["message"], case.get("active_topic")),
                    case["expected_path"],
                )


if __name__ == "__main__":
    unittest.main()
