from __future__ import annotations

from typing import Any

MAX_MESSAGES = 10

_SESSION_STORE: dict[str, dict[str, Any]] = {}


def _new_session() -> dict[str, Any]:
    return {
        "messages": [],
        "state": {
            "active_topic": None,
            "last_stock_symbol": None,
            "last_account": None,
            "last_tool_results": {
                "stock": None,
                "account": None,
            },
        },
        "summary": None,
    }


def get_session_memory(session_id: str) -> dict[str, Any]:
    if session_id not in _SESSION_STORE:
        _SESSION_STORE[session_id] = _new_session()
    return _SESSION_STORE[session_id]


def add_message(session_id: str, role: str, content: str) -> None:
    memory = get_session_memory(session_id)
    memory["messages"].append({"role": role, "content": content})

    if len(memory["messages"]) > MAX_MESSAGES:
        memory["messages"] = memory["messages"][-MAX_MESSAGES:]


def update_session_state(session_id: str, **kwargs: Any) -> None:
    memory = get_session_memory(session_id)
    state = memory["state"]

    for key, value in kwargs.items():
        if key == "last_tool_results" and isinstance(value, dict):
            state["last_tool_results"].update(value)
        else:
            state[key] = value


def get_recent_messages(session_id: str) -> list[dict[str, str]]:
    memory = get_session_memory(session_id)
    return memory["messages"]


def get_session_state(session_id: str) -> dict[str, Any]:
    memory = get_session_memory(session_id)
    return memory["state"]