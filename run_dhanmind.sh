#!/bin/bash

# DhanMind — start all services
# Usage: ./run_dhanmind.sh

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting DhanMind..."

# Check Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Ollama is not running. Start it with: ollama serve"
    exit 1
fi
echo "Ollama is running"

# Create logs dir if missing
mkdir -p "$ROOT/logs"

# MCP server
echo "Starting MCP server on port 8001..."
cd "$ROOT/mcp-server"
python3.11 -m uvicorn server:app --port 8001 --reload > "$ROOT/logs/mcp-server.log" 2>&1 &
MCP_PID=$!

# Backend
echo "Starting backend on port 8000..."
cd "$ROOT/backend"
python3.11 -m uvicorn main:app --port 8000 --reload > "$ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!

# Frontend
echo "Starting frontend on port 5173..."
cd "$ROOT/frontend"
npm run dev > "$ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!



echo "All services started:"
echo "  MCP server  → http://localhost:8001  (pid $MCP_PID)"
echo "  Backend     → http://localhost:8000  (pid $BACKEND_PID)"
echo "  Frontend    → http://localhost:5173  (pid $FRONTEND_PID)"
echo ""
echo "Logs: ./logs/"
echo "Press Ctrl+C to stop all services"

# Stop all on exit
trap "echo 'Stopping...'; kill $MCP_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

wait
