# fastapi-ticker-hub

[![CI](https://github.com/ettysekhon/fastapi-ticker-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/ettysekhon/fastapi-ticker-hub/actions/workflows/ci.yml)

A minimal FastAPI service that polls market prices (and news) and serves them via REST endpoints and raw WebSockets.

---

## Client example

```js
const socket = new WebSocket("ws://localhost:8000/ws/prices");

// Listen for errors
socket.addEventListener("error", (event) => {
  console.log("WebSocket error:", event);
});

// Handle incoming messages
socket.addEventListener("message", (event) => {
  try {
    const payload = JSON.parse(event.data);
    console.log("Price update:", payload);
  } catch (err) {
    console.warn("Non-JSON message:", event.data);
  }
});

// On open, send a heartbeat every 30s so the server-side receive loop doesn’t stall
socket.addEventListener("open", () => {
  console.log("WebSocket open");
  setInterval(() => socket.send("ping"), 30000);
});

// Log closes
socket.addEventListener("close", (event) => {
  console.log("WebSocket close:", event);
});
```

## Prerequisites

- Python 3.11+ installed
- Docker & Docker Compose (for containerized mode)
- `uv` CLI installed (optional but recommended)

## Setup

Dependencies are already declared in `pyproject.toml` and `uv.lock`. Simply install them:

```bash
uv sync
```

If you don't have `uv` installed then follow install instructions [here](https://docs.astral.sh/uv/getting-started/installation/).

## How It Works

1. **Configuration**  
   - Reads `TICKERS` and `POLL_FREQ` from environment (or `.env`).  
   - Builds a list of symbols to poll.

2. **Polling Loop**  
   - On startup, launches an `asyncio` background task that:

     ```python
     while True:
         data = await fetch_prices(TICKERS)       # runs yfinance calls in a threadpool
         await publish_price_changes(data)  # computes diffs & broadcasts to WS clients
         await asyncio.sleep(POLL_FREQ)
     ```

   - Keeps the REST API and WebSocket server responsive by off‐loading blocking I/O to threads.

3. **REST API**  
   - `GET /tickers` → returns the current snapshot of all prices.  
   - `GET /tickers/{symbol}` → returns a single symbol's latest data.

4. **WebSockets**  
   - Two endpoints:  
     - `/ws/prices` — push real-time price diffs  
     - `/ws/news`   — push any news items  
   - When a client connects, it immediately receives the full current state, then only incremental updates.

## Running Locally

Start the API with hot reload:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Compose

Build and run:

```bash
docker compose up --build
```

- API available at `http://localhost:8000`
- WebSocket endpoints at `ws://localhost:8000/ws/prices` and `/ws/news`

## Testing

Run unit tests:

```bash
make test
```

## Deployment

- On-premise: use Docker Compose or your orchestrator with the same image
- Cloud: push to registry and deploy (Kubernetes, ECS, Cloud Run, etc.)
