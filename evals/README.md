# Agent evaluation baseline

This is a deliberately small, **offline** first step. A deterministic fallback router must still work when Ollama is slow or unavailable. Every case in `routing_cases.jsonl` has a message, an optional active topic, and an expected LangGraph path (`stock`, `kb`, or `llm`).

From the repository root:

```bash
python evals/evaluate_fallback.py --min-accuracy 1.0
python -m unittest discover -s tests -p test_fallback_router.py -v
```

Neither command needs a model, Finnhub key, network access, or running app servers. GitHub Actions runs both on PRs and `main` pushes.

**Scope:** Accuracy here measures *only deterministic fallback path selection*, **not** local LLM classification, stock ticker resolution, tool success, financial correctness, RAG quality, or agent safety. A 100% score on 24 curated cases is a regression baseline, not a production quality guarantee. Expand the dataset with representative real failure patterns stripped of private financial content. Next: mock MCP results and measure intent accuracy, tool selection, end-to-end task success, unsafe action rate, and latency across local models.
