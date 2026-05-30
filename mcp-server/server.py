import contextlib
import os
import re

import httpx
from api_models import dummy_stocks
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# Step 1 — create MCP instance and define tools
mcp = FastMCP("DhanMind", stateless_http=True)


# @mcp.tool()
# def get_stock_quote(symbol: str) -> dict:
#     """Get the current stock price for a given ticker symbol"""
#     print(f"[MCP SERVER] get_stock_quote called with symbol={symbol}")
#     for stock in dummy_stocks:
#         if stock["symbol"] == symbol:
#             return stock
#     raise ValueError(f"Unknown stock symbol: {symbol}")


def looks_like_ticker(query: str) -> bool:
    cleaned = query.strip().upper()
    return bool(re.fullmatch(r"[A-Z]{1,5}", cleaned))


def extract_search_term_from_stock_query(query: str) -> str:
    cleaned = query.strip().lower()
    cleaned = re.sub(r"[^a-zA-Z0-9\s$]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    filler_patterns = [
        r"^what is\s+", r"^what s\s+", r"^tell me\s+", r"^show me\s+",
        r"^give me\s+", r"^can you show me\s+", r"^can you tell me\s+",
        r"^how about\s+", r"^what about\s+", r"^stock price of\s+",
        r"^price of\s+", r"^stock of\s+", r"^quote for\s+", r"^quote of\s+",
    ]
    for pattern in filler_patterns:
        cleaned = re.sub(pattern, "", cleaned).strip()

    trailing_words = {"stock", "price", "share", "shares", "quote", "today", "now", "currently", "trading", "market"}
    parts = [p for p in cleaned.split() if p not in trailing_words]
    return " ".join(parts)


async def resolve_symbol_from_query(query: str) -> str | None:
    normalized_query = extract_search_term_from_stock_query(query)
    normalized_upper = normalized_query.upper()

    if not normalized_query:
        return None
    if looks_like_ticker(normalized_upper):
        # TODO: cache verified tickers to avoid redundant API calls
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(
                    "https://finnhub.io/api/v1/quote",
                    params={"symbol": normalized_upper, "token": FINNHUB_API_KEY},
                )
                data = r.json()
            if data.get("c"):  # valid price means it's a real ticker
                return normalized_upper
            # price is 0 or null — likely a company name, fall through to search
        except Exception:
            pass  # fall through to search

    if not FINNHUB_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://finnhub.io/api/v1/search",
                params={"q": normalized_query, "token": FINNHUB_API_KEY},
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("result", [])
        if not results:
            return None

        for item in results:
            symbol = item.get("symbol")
            description = (item.get("description") or "").upper()
            if symbol and symbol.upper() == normalized_upper:
                return symbol.upper()
            if description == normalized_upper and symbol and looks_like_ticker(symbol):
                return symbol.upper()

        for item in results:
            symbol = item.get("symbol")
            if symbol and looks_like_ticker(symbol):
                return symbol.upper()

        return None
    except Exception:
        return None


@mcp.tool()
async def get_stock_quote(query: str) -> dict:
    query = query.strip()

    def return_error_stock_quote(error_msg: str, resolved_symbol: str | None = None):
        return {"query": query, "symbol": resolved_symbol, "price": None, "currency": "USD", "source": "error", "error": error_msg}

    if not query:
        return return_error_stock_quote("A stock query is required.")
    if not FINNHUB_API_KEY:
        return return_error_stock_quote("Finnhub API key is missing.")

    symbol = await resolve_symbol_from_query(query)
    if not symbol:
        return return_error_stock_quote("Could not resolve a valid ticker symbol from the query.")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://finnhub.io/api/v1/quote",
                params={"symbol": symbol, "token": FINNHUB_API_KEY},
            )
            response.raise_for_status()
            data = response.json()

        current_price = data.get("c")
        if current_price is None or current_price == 0:
            return return_error_stock_quote("Finnhub did not return a valid current price.", resolved_symbol=symbol)

        return {
            "query": query, "symbol": symbol, "price": current_price,
            "currency": "USD", "source": "live_finnhub",
            "raw": {"current": data.get("c"), "high": data.get("h"), "low": data.get("l"), "open": data.get("o"), "previous_close": data.get("pc")},
        }
    except Exception as e:
        return return_error_stock_quote(f"Error occurred while querying Finnhub: {str(e)}", resolved_symbol=symbol)

# Step 2 — lifespan that starts the MCP session manager
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield

# Step 3 — create FastAPI app with lifespan
app = FastAPI(title="DhanMind MCP Server", lifespan=lifespan)
# app = FastAPI(title="DhanMind MCP Server")


# Step 4 — CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Step 5 — mount MCP app
app.mount("/mcp-server", mcp.streamable_http_app())

# Regular FastAPI endpoints
@app.get("/health")
def health():
    return {"status": "ok", "service": "DhanMind MCP Server"}

@app.get("/stocks_info/{symbol}")
def get_stock_info_by_symbol(symbol: str):
    for stock in dummy_stocks:
        if stock["symbol"] == symbol:
            return stock
    raise HTTPException(status_code=404, detail="Stock symbol not found")