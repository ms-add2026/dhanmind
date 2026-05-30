"""
Integration tests for DhanMind App.

Requires both servers running:
  - Backend:    uvicorn main:app --port 8000  (from backend/)
  - MCP Server: uvicorn server:app --port 8001 (from mcp-server/)

Run with:
  python -m pytest tests/test_integration.py -v
"""

import pytest
import httpx

BACKEND_URL = "http://127.0.0.1:8000"
MCP_URL = "http://127.0.0.1:8001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def chat(message: str, session_id: str = "test-session") -> httpx.Response:
    return httpx.post(
        f"{BACKEND_URL}/api/chat/",
        json={"message": message, "session_id": session_id},
        timeout=30.0,
    )


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

def test_backend_health():
    r = httpx.get(f"{BACKEND_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_mcp_server_health():
    r = httpx.get(f"{MCP_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Stock queries — routed to MCP stock tool
# ---------------------------------------------------------------------------

def test_stock_query_exact_ticker():
    r = chat("Stock price of AAPL")
    assert r.status_code == 200
    body = r.json()
    assert body["path_used"] == "stock"
    assert "AAPL" in body["answer"]
    assert body["tool_result"]["symbol"] == "AAPL"
    assert body["tool_result"]["price"] is not None


def test_stock_query_company_name():
    r = chat("What is Amazon stock price?")
    assert r.status_code == 200
    body = r.json()
    assert body["path_used"] == "stock"
    assert body["tool_result"]["symbol"] == "AMZN"
    assert body["tool_result"]["price"] is not None


def test_stock_query_dollar_sign():
    r = chat("How is $TSLA doing today?")
    assert r.status_code == 200
    body = r.json()
    assert body["path_used"] == "stock"
    assert body["tool_result"]["symbol"] == "TSLA"


def test_stock_query_unknown_symbol_returns_error():
    r = chat("What is the stock price of ZZZZZ?")
    assert r.status_code == 200
    body = r.json()
    assert body["path_used"] == "stock"
    # Should not crash — answer should contain an error message
    assert body["answer"]


# ---------------------------------------------------------------------------
# KB / account queries — routed to local knowledge base
# ---------------------------------------------------------------------------

def test_kb_query_savings():
    r = chat("What is my savings account balance?", session_id="test-kb-savings")
    assert r.status_code == 200
    body = r.json()
    assert body["path_used"] == "kb"
    assert "Savings Account" in body["answer"]
    assert body["tool_result"] is not None


def test_kb_query_checking():
    r = chat("Show me my checking account", session_id="test-kb-checking")
    assert r.status_code == 200
    body = r.json()
    assert body["path_used"] == "kb"
    assert "Checking Account" in body["answer"]


def test_kb_query_all_accounts():
    r = chat("What are all my accounts?", session_id="test-kb-all")
    assert r.status_code == 200
    body = r.json()
    assert body["path_used"] == "kb"
    assert body["answer"]


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------

def test_response_has_required_fields():
    r = chat("What is MSFT stock price?")
    assert r.status_code == 200
    body = r.json()
    assert "answer" in body
    assert "path_used" in body
    assert "tool_result" in body


def test_empty_message_does_not_crash():
    r = chat(" ")
    assert r.status_code in (200, 422, 500)  # should not hang or throw unhandled


# ---------------------------------------------------------------------------
# Multi-stock queries
# ---------------------------------------------------------------------------

def test_stock_query_multiple_stocks():
    """
    User asks for two stocks in a single query.
    Both should be resolved and returned in the answer.
    """
    r = chat("How about Apple and VOO?", session_id="test-multi-stock-001")
    assert r.status_code == 200
    body = r.json()
    assert body["path_used"] == "stock"
    # Both symbols should appear in the answer
    assert "AAPL" in body["answer"]
    assert "VOO" in body["answer"]


# ---------------------------------------------------------------------------
# Session memory — follow-up queries 
# ---------------------------------------------------------------------------

def test_session_memory_stock_followup():
    """
    User asks about Amazon stock, then asks a vague follow-up "what about apple?".
    The system should use session context to understand the follow-up is also
    a stock price query and route it to the stock tool.
    """
    session_id = "test-session-memory-001"

    # Query 1 — establishes context: this session is about stock prices
    r1 = chat("What is Amazon stock price?", session_id=session_id)
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["path_used"] == "stock"
    assert body1["tool_result"]["symbol"] == "AMZN"

    # Query 2 — vague follow-up, no explicit mention of "stock" or "price"
    r2 = chat("what about apple?", session_id=session_id)
    assert r2.status_code == 200
    body2 = r2.json()
    # System should infer stock context from session and route to stock tool
    assert body2["path_used"] == "stock"
    assert body2["tool_result"].get("symbol") == "AAPL"
    assert body2["tool_result"].get("price") is not None


# ---------------------------------------------------------------------------
# Session memory — correction handling
# ---------------------------------------------------------------------------

def test_session_memory_correction():
    """
    User asks about a misspelled company, gets wrong result, then corrects themselves.
    System should understand the correction and return the right stock.
    """
    session_id = "test-session-correction-001"
    # Query 1 — misspelled
    r1 = chat("and amazonn?", session_id=session_id)
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["path_used"] == "stock"
    assert body1["tool_result"].get("symbol") == "AMZN"

    # Query 2 — explicit correction
    r2 = chat("No I meant Amazon", session_id=session_id)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["path_used"] == "stock"
    assert body2["tool_result"].get("symbol") == "AMZN"
    assert body2["tool_result"].get("price") is not None


# ---------------------------------------------------------------------------
# MCP server direct endpoint
# ---------------------------------------------------------------------------

def test_mcp_stocks_info_endpoint():
    r = httpx.get(f"{MCP_URL}/stocks_info/AAPL")
    assert r.status_code in (200, 404)  # 404 if dummy data removed, that's fine
