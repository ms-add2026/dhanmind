# Rust Ingestion Service — V2 Foundation

DhanMind's ingestion service will be a small Rust component responsible for turning raw financial exports into deterministic, normalized records that the rest of the application can trust.

This document defines the service boundary before implementation begins.

## Goals

The ingestion service should:

- run locally and keep imported financial data on the user's machine;
- parse financial exports without loading an entire file into memory;
- normalize provider-specific fields into a stable DhanMind schema;
- validate required fields and surface malformed records clearly;
- generate deterministic fingerprints so repeated imports are idempotent;
- keep parsing and normalization independent from LLM availability.

## Initial Scope

The first implementation will target transaction files, starting with CSV and expanding to OFX/QFX.

```text
file
  ↓
format detection
  ↓
streaming parser
  ↓
normalization
  ↓
validation
  ↓
fingerprint / deduplication
  ↓
canonical transaction records
```

Provider-specific parsers can be added behind a common parser interface as real export formats are collected.

## Canonical Transaction

The initial normalized record should contain enough information for downstream spending, cash-flow, and search features without preserving provider-specific column names.

```text
Transaction
├── id
├── account_id
├── posted_at
├── transaction_at      (optional)
├── description
├── merchant            (optional)
├── amount
├── currency
├── category            (optional)
├── transaction_type    (optional)
├── source
└── fingerprint
```

The exact Rust types and serialization format will be established when the crate is scaffolded.

## Fingerprints and Idempotency

Importing the same export twice must not duplicate transactions.

The first version will derive a deterministic fingerprint from stable normalized fields such as:

```text
account_id + posted_at + amount + normalized_description
```

Exact fingerprint semantics will be versioned so they can evolve without silently changing historical identity rules.

## Service Boundary

The ingestion service owns:

- file parsing;
- schema normalization;
- validation;
- deterministic fingerprints;
- duplicate detection within an import;
- structured ingestion errors.

It does **not** own:

- conversational reasoning;
- LLM-based categorization;
- portfolio or spending analytics;
- RAG retrieval;
- live market data;
- UI behavior.

Those remain in DhanMind's application, agent, and tool layers.

## Design Principles

1. **Local first** — raw financial files are processed locally.
2. **Deterministic core** — a model is never required to parse or validate a transaction.
3. **Streaming by default** — large exports should have bounded memory usage.
4. **Idempotent imports** — rerunning an import should be safe.
5. **Extensible parsers** — new institutions should not require rewriting the pipeline.
6. **Observable failures** — rejected rows should include actionable error information.

## Next Increment

The next implementation PR can scaffold the Rust crate with:

- a `FinancialParser` trait;
- the canonical `Transaction` type;
- an `IngestionError` type;
- one CSV parser fixture and test.

That keeps the first code change small while establishing the interfaces needed for later bank- and brokerage-specific parsers.
