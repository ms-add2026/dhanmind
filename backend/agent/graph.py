import json
import re
from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, END

from services.mcp_stock_client import get_stock_quote_from_mcp, MCPStockClientError
from services.session_memory import (
    get_session_state,
    update_session_state,
    add_message,
)


KB_PATH = Path(__file__).parent.parent / "data" / "accounts.json"

ACCOUNT_KEYWORDS = {
    "savings": "Savings Account",
    "checking": "Checking Account",
    "robinhood": "Robinhood",
}

STOCK_KEYWORDS = {
    "stock",
    "stocks",
    "trading",
    "trade",
    "quote",
    "share price",
    "market price",
    "price of",
    "ticker",
    "symbol",
}

STOP_WORDS = {
    "WHAT", "IS", "THE", "A", "AN", "OF", "FOR", "TO", "AT", "NOW",
    "RIGHT", "CURRENT", "CURRENTLY", "TRADING", "PRICE", "STOCK",
    "STOCKS", "QUOTE", "TELL", "ME", "SHOW", "GET", "HOW", "ABOUT",
    "MY", "YOUR", "PLEASE", "CAN", "YOU", "DOES", "MARKET", "SHARE",
}


class AgentState(TypedDict):
    message: str
    path: str
    answer: str
    tool_result: dict
    session_id: str
    session_state: dict


def is_stock_query(message: str) -> bool:
    lower = message.lower()
    upper = message.upper()

    if any(keyword in lower for keyword in STOCK_KEYWORDS):
        return True

    if re.search(r"\$[A-Z]{1,5}\b", upper):
        return True

    if re.search(r"\b(?:TICKER|SYMBOL)\s+[A-Z]{1,5}\b", upper):
        return True

    return False


def extract_symbol(message: str) -> str | None:
    upper = message.upper()

    # Strong signal: $AMD, $AAPL
    dollar_match = re.search(r"\$([A-Z]{1,5})\b", upper)
    if dollar_match:
        return dollar_match.group(1)

    # Strong signal: ticker AMD / symbol AMD
    explicit_match = re.search(r"\b(?:TICKER|SYMBOL)\s+([A-Z]{1,5})\b", upper)
    if explicit_match:
        return explicit_match.group(1)

    # Natural phrasing: price of AMD / quote for AMD / stock price of AMD
    phrase_match = re.search(
        r"\b(?:PRICE OF|QUOTE FOR|STOCK PRICE OF|SHARE PRICE OF|MARKET PRICE OF)\s+([A-Z]{1,5})\b",
        upper,
    )
    if phrase_match:
        return phrase_match.group(1)

    # Fallback: first ticker-looking word that is not normal English routing text
    candidates = re.findall(r"\b[A-Z]{1,5}\b", upper)

    for candidate in candidates:
        if candidate not in STOP_WORDS:
            return candidate

    return None


def classify_node(state: AgentState) -> AgentState:
    message = state["message"]
    session_id = state.get("session_id", "default-session")

    if is_stock_query(message):
        topic = "stock"
    else:
        # Check session context for ambiguous messages like "what about Amazon?"
        session_state = get_session_state(session_id)
        active_topic = session_state.get("active_topic")
        if active_topic == "stock":
            topic = "stock"
        else:
            topic = "kb"

    return {**state, "path": topic}


async def stock_node(state: AgentState) -> AgentState:
    symbol = extract_symbol(state["message"])
    query = symbol if symbol else state["message"]

    try:
        data = await get_stock_quote_from_mcp(query)

        if data.get("price") is None:
            return {
                **state,
                "tool_result": data,
                "answer": data.get("error", f"Could not retrieve a valid price for {query}."),
            }

        update_session_state(
            state.get("session_id", "default-session"),
            active_topic="stock",
            last_stock_symbol=data["symbol"],
        )
        add_message(state.get("session_id", "default-session"), "user", state["message"])
        return {
            **state,
            "tool_result": data,
            "answer": f"{data['symbol']} is currently trading at ${data['price']} {data['currency']}.",
        }

    except MCPStockClientError as e:
        return {
            **state,
            "answer": f"MCP server error: {str(e)}",
        }


def kb_node(state: AgentState) -> AgentState:
    try:
        with open(KB_PATH, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {**state, "answer": "Knowledge base not found."}

    lower = state["message"].lower()
    accounts = data.get("accounts", [])

    for keyword, account_name in ACCOUNT_KEYWORDS.items():
        if keyword in lower:
            for account in accounts:
                if account["name"] == account_name:
                    return {
                        **state,
                        "tool_result": account,
                        "answer": f"Your {account['name']} at {account['institution']} "
                                  f"has a balance of ${account['balance']:,.2f} {account['currency']} "
                                  f"(last updated: {account['last_updated']})."
                    }

    summary = "\n".join(
        f"- {a['name']} ({a['institution']}): ${a['balance']:,.2f}"
        for a in accounts
    )
    total = sum(a["balance"] for a in accounts)

    return {
        **state,
        "tool_result": {"accounts": accounts},
        "answer": f"Here are your account balances:\n{summary}\n\nTotal: ${total:,.2f} USD"
    }


def route(state: AgentState) -> str:
    return state["path"]


builder = StateGraph(AgentState)
builder.add_node("classify", classify_node)
builder.add_node("stock", stock_node)
builder.add_node("kb", kb_node)

builder.set_entry_point("classify")
builder.add_conditional_edges("classify", route, {"stock": "stock", "kb": "kb"})
builder.add_edge("stock", END)
builder.add_edge("kb", END)

graph = builder.compile()


async def run_agent(message: str, session_id: str) -> dict:
    initial_state: AgentState = {
        "message": message,
        "path": "",
        "answer": "",
        "tool_result": {},
        "session_id": session_id,
        "session_state": {},
    }

    result = await graph.ainvoke(initial_state)

    return {
        "answer": result["answer"],
        "path_used": result["path"],
        "tool_result": result["tool_result"],
    }