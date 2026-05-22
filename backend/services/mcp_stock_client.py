import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://127.0.0.1:8001/mcp-server/mcp",
)


class MCPStockClientError(Exception):
    pass


async def get_stock_quote_from_mcp(query: str) -> dict[str, Any]:
    cleaned_query = query.strip()

    if not cleaned_query:
        raise MCPStockClientError("Stock query is required.")

    try:
        async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    "get_stock_quote",
                    {"query": cleaned_query},
                )

        if not result.content:
            raise MCPStockClientError("MCP tool returned no content.")

        print(f"[MCP CLIENT] Calling MCP tool get_stock_quote for query={cleaned_query}")
        # FastMCP usually returns tool output as structuredContent when possible.
        if getattr(result, "structuredContent", None):
            data = result.structuredContent
        else:
            first_content = result.content[0]

            # Some MCP responses come back as text content containing JSON-ish text.
            raw_text = getattr(first_content, "text", None)
            if raw_text is None:
                raise MCPStockClientError("MCP tool returned unsupported content.")

            import json

            data = json.loads(raw_text)

        if not isinstance(data, dict):
            raise MCPStockClientError("MCP tool returned unexpected response shape.")

        normalized = {
            "query": data.get("query", cleaned_query),
            "symbol": data.get("symbol"),
            "price": data.get("price"),
            "currency": data.get("currency", "USD"),
            "source": data.get("source", "unknown"),
            "error": data.get("error"),
            "raw": data.get("raw"),
        }

        if normalized["price"] is None:
            raise MCPStockClientError(
                normalized.get("error") or "Quote response did not include a price."
            )

        return normalized

    except Exception as exc:
        raise MCPStockClientError(f"MCP stock quote call failed: {exc}") from exc