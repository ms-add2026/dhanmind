import json
import logging
from typing import Any

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:4b"
# OLLAMA_MODEL = "gemma3:1b"

VALID_INTENTS = {"stock", "accounts", "fin_knowledge", "fin_recommendation", "other"}


def build_prompt(message: str, recent_messages: list[dict]) -> str:
    history = ""
    if recent_messages:
        lines = [f"{m['role']}: {m['content']}" for m in recent_messages[-4:]]
        history = "Recent conversation:\n" + "\n".join(lines) + "\n\n"

    return f"""{history}Classify the user message into one of these intents: stock, accounts, fin_knowledge, fin_recommendation, other.
Also extract entities if present.

Respond with ONLY a JSON object:
{{"intent": "stock|accounts|fin_knowledge|fin_recommendation|other", "stock_queries": ["<company or ticker>"], "account_target": "<savings|checking|robinhood or null>"}}

Examples:
"What is Amazon stock price?" -> {{"intent": "stock", "stock_queries": ["Amazon"], "account_target": null}}
"how about apple" -> {{"intent": "stock", "stock_queries": ["Apple"], "account_target": null}}
"and amazonn?" -> {{"intent": "stock", "stock_queries": ["Amazon"], "account_target": null}}
"No I meant Amazon" -> {{"intent": "stock", "stock_queries": ["Amazon"], "account_target": null}}
"I meant AMZN" -> {{"intent": "stock", "stock_queries": ["AMZN"], "account_target": null}}
"How about Apple and VOO?" -> {{"intent": "stock", "stock_queries": ["Apple", "VOO"], "account_target": null}}
"what is my checking balance?" -> {{"intent": "accounts", "stock_queries": [], "account_target": "checking"}}
"what is a P/E ratio?" -> {{"intent": "fin_knowledge", "stock_queries": [], "account_target": null}}
"should I buy AAPL?" -> {{"intent": "fin_recommendation", "stock_queries": ["AAPL"], "account_target": null}}

User message: "{message}"
JSON:"""


async def extract_intent(message: str, recent_messages: list[dict] | None = None) -> dict[str, Any] | None:
    prompt = build_prompt(message, recent_messages or [])

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            raw = response.json().get("response", "")

        # model may wrap JSON in extra text, find the object
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return None

        parsed = json.loads(raw[start:end])
        intent = parsed.get("intent", "other")

        if intent not in VALID_INTENTS:
            intent = "other"

        return {
            "intent": intent,
            "stock_queries": parsed.get("stock_queries") or [],
            "account_target": parsed.get("account_target"),
        }

    except httpx.TimeoutException:
        logging.warning("[extract_intent] Request timed out")
        return None  # falls back to keyword routing
    except Exception as e:
        logging.error(f"[extract_intent] Unexpected error: {e}")
        return None


async def ask_llm(prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
    except httpx.TimeoutException:
        logging.warning("[ask_llm] Request timed out")
        return "This query is taking too long to process. Please try again or simplify your question."
    except Exception as e:
        logging.error(f"[ask_llm] Unexpected error: {e}")
        return "I'm unable to answer that right now. Please try again later."

