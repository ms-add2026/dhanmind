"""Deterministic intent routing when local model inference is unavailable.

This pure function is deliberately separate from LangGraph and network clients so
it can be evaluated and regression-tested offline. It routes paths, not actions.
"""

import re

_ACCOUNT_TERMS = re.compile(
    r"\b(?:account|accounts|balance|balances|savings|checking|robinhood|net worth)\b",
    re.IGNORECASE,
)
_ADVICE_TERMS = re.compile(
    r"\b(?:should|could|would|can)\s+i\s+(?:buy|sell|hold|invest|rebalance)\b"
    r"|\b(?:good|bad|safe)\s+(?:investment|buy|time to buy)\b",
    re.IGNORECASE,
)
_KNOWLEDGE_TERMS = re.compile(
    r"\b(?:what is|what does|explain|define|how does)\b.*"
    r"\b(?:ratio|etf|index fund|diversification|inflation|dollar.cost.averaging|capital gains|cpi)\b",
    re.IGNORECASE,
)
_STOCK_TERMS = re.compile(
    r"\b(?:stock|stocks|trading|trade|quote|ticker|symbol)\b"
    r"|\b(?:share price|market price|price of|stock price)\b",
    re.IGNORECASE,
)
_EXPLICIT_SYMBOL = re.compile(r"\$[A-Z]{1,5}\b|\b(?:ticker|symbol)\s+[A-Z]{1,5}\b", re.IGNORECASE)
_FOLLOWUP_WITH_TICKER = re.compile(r"(?i:\b(?:how|what)\s+about\b).*\b[A-Z]{2,5}\b")


def classify_fallback(message: str, active_topic: str | None = None) -> str:
    """Return ``stock``, ``kb`` or ``llm``; never trigger an external action.

    Order matters: requests for advice are not treated as quote lookups, and
    explicit account queries override a previous stock discussion.
    """
    message = message.strip()
    if not message:
        return "llm"
    if _ADVICE_TERMS.search(message):
        return "llm"
    if _ACCOUNT_TERMS.search(message):
        return "kb"
    if _KNOWLEDGE_TERMS.search(message):
        return "llm"
    if _STOCK_TERMS.search(message) or _EXPLICIT_SYMBOL.search(message):
        return "stock"
    if _FOLLOWUP_WITH_TICKER.search(message):
        return "stock"
    if active_topic == "stock":
        # Keep short corrections and follow-ups on the stock path, not every
        # unrelated question in the same session.
        if re.match(r"(?i)^(?:and |(?:no,? )?i meant |(?:how|what) about )", message):
            return "stock"
    return "llm"
