# DhanMind 2.0 — learning-driven delivery plan (October 2026)

## Product north star

Build a local-first **personal finance decision-support copilot**, not an autonomous trading bot. Users can ask questions about synthetic or explicitly imported financial information; answers show source documents, deterministic calculations, tool paths, uncertainties and approval points. No live-money write actions until a distinct security/permissions review, and never without explicit confirmation.

## Architecture direction

```
React + TypeScript (chat, charts, sources, execution timeline, approval UI)
        |
FastAPI (typed API, validation, auth for non-local use, request IDs)
        |
LangGraph (router -> planner -> tools/retrieval -> verification -> response)
    |        |         |                 |
  MCP     SQLite/   Valkey Search    Local model gateway
 tools    DuckDB    hybrid retrieval  (Ollama first)
    |        ^         ^
Finnhub  Canonical finance records + indexed document chunks
                 ^
         Rust ingestion worker (CSV, PDFs, deduplication, provenance)
```

Keep **SQLite/DuckDB** as the source of truth for balances and transactions. Valkey Search is a retrieval index, never the source of truth for arithmetic. Generated numbers must come from validated deterministic code, not an LLM response. Separate private document content from market-data requests.

## Implementation slices and why

1. **Restore confidence (now)**: offline fallback-routing evals and CI; clean README/status; safe API error boundaries and input validation. Learn golden datasets, test isolation, failure modes and quality baselines.
2. **Make answers grounded**: ingest one synthetic bank CSV into a local canonical schema, query with an MCP ledger tool, expose source transaction IDs and exact Python/SQL aggregates. Learn typed contracts, financial correctness, idempotency and data lineage.
3. **Add private document intelligence**: design a Rust document-ingestion service with fixtures, chunking and deterministic fingerprints; use local embeddings + Valkey Search hybrid retrieval; cite source file/page and abstain when evidence is missing. Learn Rust service boundaries, indexing, RAG evaluation and retrieval security.
4. **Persist meaningful state**: LangGraph thread checkpointer (SQLite for local experiments; PostgreSQL when deployed), explicit summary/preferences store, user-controlled data deletion. Learn durable execution, resumption, schema migration and memory lifetime.
5. **Deliver RiskOps**: cash runway, account concentration, portfolio concentration and scenario simulation using deterministic engines plus LLM narration; every scenario displays assumptions and what-if controls. Learn tool design, structured outputs, policy-based approval and verification.
6. **Production discipline**: OpenTelemetry traces with sensitive payloads off by default, structured metrics, per-tool timeout/retry budgets, defensive MCP schemas, red-team prompts, containerized reproducible deployment, observability dashboards and performance benchmarks. Learn SLOs, privacy, agent security and systems troubleshooting.

## Definition of done for every feature

- Demonstrable end-to-end behavior with synthetic fixtures
- Deterministic/offline unit tests plus a measurable eval or regression case
- Safe failures, timeouts, typed error handling, no exposed secrets or unnecessary personal data in logs
- Source attribution for facts; verified arithmetic for financial numbers
- Clear README usage, architecture decision and demo prompt
- One reviewable PR, measured result and short learning reflection

## First demo target

Upload a **synthetic bank statement**, ask “How many months of runway do I have if my monthly expenses rise by 15%?”, see exact parsed transactions, source references, a deterministic runway calculation, and an agent timeline showing which tool computed each number. No brokerage trade execution.

## Current truth to preserve

Existing working prototype: React + FastAPI + LangGraph intent routing, a Finnhub-backed FastMCP stock quote tool, local JSON accounts and Ollama (currently `gemma3:4b` in code). Process-local session memory is not durable. Valkey-based RAG and the Rust ingestion service are planned, not shipped. PR #2 separately documents the Rust ingestion boundary and should be reviewed before implementation. Backend error responses currently expose exception messages, and the README has stale sections: both require cleanup before any internet-facing demo.
