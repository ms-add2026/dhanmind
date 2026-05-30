import json
import re
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph
from services.llm_service import ask_llm, extract_intent
from services.mcp_stock_client import MCPStockClientError, get_stock_quote_from_mcp
from services.session_memory import (
    add_message,
    get_recent_messages,
    get_session_state,
    update_session_state,
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
    llm_extraction_info: dict | None

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


async def classify_node(state: AgentState) -> AgentState:
    message = state["message"]
    session_id = state.get("session_id", "default-session")

    # Try LLM-based intent extraction first
    recent = get_recent_messages(session_id)
    extraction = await extract_intent(message, recent)

    if extraction:
        match extraction["intent"]:
            case "stock":
                topic = "stock"
            case "accounts":
                topic = "kb"
            case "fin_knowledge" | "fin_recommendation":
                topic = "llm"
            case _:
                topic = "llm"
    else:
        # Fallback: keyword classifier + session memory
        if is_stock_query(message):
            topic = "stock"
        else:
            session_state = get_session_state(session_id)
            active_topic = session_state.get("active_topic")
            topic = "stock" if active_topic == "stock" else "kb"

    return {**state, "path": topic, "llm_extraction_info": extraction}

async def stock_node(state: AgentState) -> AgentState:
    extraction = state.get("llm_extraction_info")
    queries = []

    if extraction and extraction.get("stock_queries"):
        queries = extraction["stock_queries"]
    else:
        # Fallback when Ollama unavailable
        symbol = extract_symbol(state["message"])
        queries = [symbol] if symbol else [state["message"]]

    results = []
    last_tool_result = {}

    for query in queries:
        try:
            data = await get_stock_quote_from_mcp(query)
            if data.get("price") is not None:
                results.append(f"{data['symbol']} is currently trading at ${data['price']} {data['currency']}.")
                last_tool_result = data
            else:
                results.append(data.get("error", f"Could not retrieve price for {query}."))
        except MCPStockClientError as e:
            results.append(f"MCP server error for {query}: {str(e)}")

    return {
        **state,
        "tool_result": last_tool_result,
        "answer": "\n".join(results),
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


async def llm_node(state: AgentState) -> AgentState:
    intent = (state.get("llm_extraction_info") or {}).get("intent", "other")

    if intent == "fin_recommendation":
        system_context = "You are a financial assistant. Always remind the user that this is not professional financial advice."
    else:
        system_context = "You are a knowledgeable financial assistant. Answer clearly and concisely."

    prompt = f"{system_context}\n\nUser: {state['message']}\nAssistant:"
    answer = await ask_llm(prompt)

    return {**state, "answer": answer, "tool_result": {}}


def route(state: AgentState) -> str:
    return state["path"]


builder = StateGraph(AgentState)
builder.add_node("classify", classify_node)
builder.add_node("stock", stock_node)
builder.add_node("kb", kb_node)
builder.add_node("llm", llm_node)

builder.set_entry_point("classify")
builder.add_conditional_edges("classify", route, {"stock": "stock", "kb": "kb", "llm": "llm"})
builder.add_edge("stock", END)
builder.add_edge("kb", END)
builder.add_edge("llm", END)

graph = builder.compile()


async def run_agent(message: str, session_id: str) -> dict:
    initial_state: AgentState = {
        "message": message,
        "path": "",
        "answer": "",
        "tool_result": {},
        "session_id": session_id,
        "llm_extraction_info": None
    }

    result = await graph.ainvoke(initial_state)

    # Centralized memory update — nodes stay focused on reasoning only
    add_message(session_id, "user", message)
    add_message(session_id, "assistant", result["answer"])

    if result["path"] == "stock" and result.get("tool_result"):
        update_session_state(
            session_id,
            active_topic="stock",
            last_stock_symbol=result["tool_result"].get("symbol"),
            last_tool_results={"stock": result["tool_result"]},
        )
    elif result["path"] == "kb":
        update_session_state(
            session_id,
            active_topic="accounts",
            last_tool_results={"account": result["tool_result"]},
        )

    return {
        "answer": result["answer"],
        "path_used": result["path"],
        "tool_result": result["tool_result"],
    }