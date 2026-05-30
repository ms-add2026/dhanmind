from pydantic import BaseModel


# Input model
class StockSearchRequest(BaseModel):
    symbol: str


# Output model
class StockSearchResponse(BaseModel):
    symbol: str
    price: float
    currency: str
    change: float
    change_percent: float
    high: float
    low: float
    opening_price: float
    previous_closed_price: float
    timestamp: str
    source:str

dummy_stocks = [
    {
        "symbol": "AAPL",
        "price": 189.45,
        "currency": "USD",
        "change": 2.35,
        "change_percent": 1.26,
        "high": 191.20,
        "low": 187.10,
        "opening_price": 187.80,
        "previous_closed_price": 187.10,
        "timestamp": "2026-04-11T14:30:00Z",
        "source": "dummy"
    },
    {
        "symbol": "GOOGL",
        "price": 172.30,
        "currency": "USD",
        "change": -1.20,
        "change_percent": -0.69,
        "high": 174.50,
        "low": 171.00,
        "opening_price": 173.50,
        "previous_closed_price": 173.50,
        "timestamp": "2026-04-11T14:30:00Z",
        "source": "dummy"
    },
    {
        "symbol": "MSFT",
        "price": 415.60,
        "currency": "USD",
        "change": 5.10,
        "change_percent": 1.24,
        "high": 417.00,
        "low": 410.20,
        "opening_price": 410.50,
        "previous_closed_price": 410.50,
        "timestamp": "2026-04-11T14:30:00Z",
        "source": "dummy"
    },
    {
        "symbol": "TSLA",
        "price": 245.80,
        "currency": "USD",
        "change": -8.40,
        "change_percent": -3.31,
        "high": 255.00,
        "low": 243.10,
        "opening_price": 254.20,
        "previous_closed_price": 254.20,
        "timestamp": "2026-04-11T14:30:00Z",
        "source": "dummy"
    },
    {
        "symbol": "AMZN",
        "price": 198.75,
        "currency": "USD",
        "change": 3.25,
        "change_percent": 1.66,
        "high": 200.10,
        "low": 195.40,
        "opening_price": 195.50,
        "previous_closed_price": 195.50,
        "timestamp": "2026-04-11T14:30:00Z",
        "source": "dummy"
    },
]

"""
Input
{
  "symbol": "AAPL"
}
Output
{
  "symbol": "AAPL",
  "price": 212.45,
  "currency": "USD",
  "change": 1.83,
  "change_percent": 0.87,
  "high": 214.12,
  "low": 209.77,
  "open": 210.50,
  "previous_close": 210.62,
  "timestamp": "2026-04-10T20:15:00Z",
  "source": "mock"
}
"""