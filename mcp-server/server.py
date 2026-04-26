import contextlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
from api_models import *

# Step 1 — create MCP instance and define tools
mcp = FastMCP("DhanMind", stateless_http=True)


@mcp.tool()
def get_stock_quote(symbol: str) -> dict:
    """Get the current stock price for a given ticker symbol"""
    print(f"[MCP SERVER] get_stock_quote called with symbol={symbol}")
    for stock in dummy_stocks:
        if stock["symbol"] == symbol:
            return stock
    raise ValueError(f"Unknown stock symbol: {symbol}")

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