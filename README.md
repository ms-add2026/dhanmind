# DhanMind 🪙

> **Local-first AI financial copilot** — your personal finance agent that keeps your data private, routes queries intelligently, and connects to live financial tools via MCP.

[![Status](https://img.shields.io/badge/status-in%20progress-orange)](https://github.com/ms-add2026/dhanmind)
[![Stack](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20LangGraph%20%7C%20MCP-blue)](https://github.com/ms-add2026/dhanmind)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## What is DhanMind?

DhanMind is a privacy-first AI agent for personal finance. It runs entirely on your machine — no personal data is ever sent to the cloud. You ask financial questions in natural language, and the agent decides in real time whether to:

- Fetch **live market data** via an MCP tool server
- Retrieve **your private financial data** from a local knowledge base

The architecture is designed to showcase production-grade agentic AI patterns: MCP-based tool integration, LangGraph orchestration, local LLM inference, and vector similarity search — all in a full-stack React + FastAPI application.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React + TypeScript UI                     │
│         Chat window · Path visibility · Tool results         │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/REST
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (port 8000)                 │
│                    POST /api/chat/                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Agent Router                          │
│                                                             │
│   classify_node → detects intent from message               │
│        │                                                    │
│        ├── stock question ──► stock_node                    │
│        │                          │                         │
│        │                          ▼                         │
│        │                   MCP Server (port 8001)           │
│        │                   get_stock_quote tool             │
│        │                   └── Mock → Finnhub (V1.5)        │
│        │                                                    │
│        └── personal question ──► kb_node                   │
│                                      │                      │
│                                      ▼                      │
│                              Local KB Reader                 │
│                              accounts.json → Valkey (V1.5)  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data & Model Layer (all local)              │
│                                                             │
│  Valkey Search (Docker)     nomic-embed-text (Ollama)       │
│  Vector KB — V1.5           Embeddings — V1.5               │
│                                                             │
│  Gemma 4 via Ollama (M1 Metal)     Finnhub API              │
│  Local LLM — V1.5                  Stock quotes — V1.5      │
└─────────────────────────────────────────────────────────────┘
```

---

## Demo Flows (V1 — Working)

### Flow 1 — Live Stock Price via MCP

```
User:  "What is AAPL trading at right now?"
Agent: classifies → stock question
       calls MCP tool → get_stock_quote("AAPL")
       UI shows answer + "MCP · Stock Tool" badge
```

### Flow 2 — Private Account Balance via Local KB

```
User:  "What is my savings balance?"
Agent: classifies → personal finance question
       reads accounts.json locally
       UI shows answer + "Local KB · Private Data" badge
       no data leaves your machine
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 18 + TypeScript + Tailwind CSS v4 | Vite build |
| Backend | Python + FastAPI | Async, port 8000 |
| Agent orchestration | LangGraph | State graph routing |
| MCP server | FastMCP + official MCP SDK 1.27.0 | Streamable HTTP transport |
| Vector DB | Valkey Search (Docker) | VSS via HNSW — V1.5 |
| Local LLM | Gemma 4 (gemma4:e4b) via Ollama | M1 Metal acceleration — V1.5 |
| Embeddings | nomic-embed-text via Ollama | Apache 2.0 — V1.5 |
| Stock API | Finnhub free tier | Real-time quotes — V1.5 |

---

## Project Status

### ✅ V1 — Complete

- [x] React + TypeScript chat UI with path/tool visibility
- [x] FastAPI backend with `/api/chat/` endpoint
- [x] LangGraph agent with classify → route → answer graph
- [x] MCP server with `get_stock_quote` tool (mock data)
- [x] Local KB reader from `accounts.json`
- [x] Two working demo flows end-to-end
- [x] UI shows which path/tool was used per response

### 🔄 V1.5 — In Progress

- [ ] Real Finnhub API for live stock quotes
- [ ] nomic-embed-text embeddings for document chunks
- [ ] Valkey Search VSS vector store (validated locally — see Technical Decisions)
- [ ] Full RAG pipeline — embed → store → KNN retrieve → LLM synthesise
- [ ] Gemma 4 (gemma4:e4b) local LLM via Ollama for answer synthesis
- [ ] Conversation memory — LangGraph session state
- [ ] KB search exposed as MCP tool

### 📋 V2 — Planned

- [ ] Tax summary tool via MCP
- [ ] Rust document ingestion microservice
- [ ] Multi-document knowledge base
- [ ] Dashboard widgets — spending, net worth
- [ ] Support for  US and India based financial literacy

## Running Local

### Prerequisites
- Python 3.11+
- Node 18+
- Docker (for Valkey Search in V1.5)
- Ollama (for local LLM in V1.5)

### Terminal 1 — MCP Server
```bash
cd mcp-server
pip3.11 install fastapi uvicorn mcp httpx
python3.11 -m uvicorn server:app --reload --port 8001
```

### Terminal 2 — Backend
```bash
cd backend
pip3.11 install fastapi uvicorn langgraph langchain-core httpx
python3.11 -m uvicorn main:app --reload --port 8000
```

### Terminal 3 — Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and try:
- `"What is AAPL trading at right now?"`
- `"What is my savings account balance?"`

---

## About

Built by **Manish Addanki** as a portfolio showcase demonstrating:

- Full-stack engineering (React + TypeScript + FastAPI)
- Agentic AI patterns (LangGraph state graph routing)
- Model Context Protocol (MCP) tool integration
- Local-first privacy architecture
- Vector search infrastructure (Valkey Search — contributed to at AWS/ElastiCache)
- Local LLM inference (Gemma 4 via Ollama)

**Resume contact:** manish.add2026@gmail.com
