import json
from services.mcp_stock_client import get_stock_quote_from_mcp, MCPStockClientError
from pathlib import Path
from langgraph.graph import StateGraph, END
from typing import TypedDict

KB_PATH = Path(__file__).parent.parent / "data" / "accounts.json"

KNOWN_SYMBOLS = ["AAPL", "MSFT", "TSLA", "NVDA", "GOOGL", "AMZN", "META"]
ACCOUNT_KEYWORDS = {
    "savings": "Savings Account",
    "checking": "Checking Account",
    "robinhood": "Robinhood",
}
STOCK_KEYWORDS = ["stock", "price", "trading", "share", "market"]


class AgentState(TypedDict):
    message: str
    path: str
    answer: str
    tool_result: dict


def classify_node(state: AgentState) -> AgentState:
    lower = state["message"].lower()
    upper = state["message"].upper()
    is_stock = any(kw in lower for kw in STOCK_KEYWORDS) or \
               any(sym in upper for sym in KNOWN_SYMBOLS)
    return {**state, "path": "stock" if is_stock else "kb"}

async def stock_node(state: AgentState) -> AgentState:
    upper = state["message"].upper()
    symbol = None
    for ks in KNOWN_SYMBOLS:
        if ks in upper:
            symbol = ks
            break

    if symbol is None:
        return {
            **state,
            "answer": "I couldn't identify a stock symbol. Try asking about AAPL, MSFT, TSLA etc.",
        }

    try:
        data = await get_stock_quote_from_mcp(symbol)

        return {
            **state,
            "tool_result": data,
            "answer": f"{symbol} is currently trading at ${data['price']} {data['currency']}.",
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

    # Try to match specific account
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

    # No specific account matched — return all balances
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


# Build graph
builder = StateGraph(AgentState)
builder.add_node("classify", classify_node)
builder.add_node("stock", stock_node)
builder.add_node("kb", kb_node)

builder.set_entry_point("classify")
builder.add_conditional_edges("classify", route, {"stock": "stock", "kb": "kb"})
builder.add_edge("stock", END)
builder.add_edge("kb", END)

graph = builder.compile()


async def run_agent(message: str) -> dict:
    """Entry point called by FastAPI chat endpoint."""
    initial_state: AgentState = {
        "message": message,
        "path": "",
        "answer": "",
        "tool_result": {},
    }
    result = await graph.ainvoke(initial_state)
    return {
        "answer": result["answer"],
        "path_used": result["path"],
        "tool_result": result["tool_result"],
    }