# fastapi-ticker-hub

[![CI](https://github.com/ettysekhon/fastapi-ticker-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/ettysekhon/fastapi-ticker-hub/actions/workflows/ci.yml)

A minimal FastAPI service that polls market prices (and news) and serves them via REST endpoints and raw WebSockets. Additionally it supports customised subscriptions with per-connection watchlist.

---

## Client example

```js
const socket = new WebSocket("ws://localhost:8000/ws/prices");

// Handle errors
socket.addEventListener("error", (event) => {
  console.log("WebSocket error:", event);
});

// Receive initial snapshot or updates (diffs)
socket.addEventListener("message", (event) => {
  try {
    const payload = JSON.parse(event.data);
    console.log("Price update:", payload);
  } catch (err) {
    console.warn("Non-JSON message:", event.data);
  }
});

// Keep connection alive with heartbeat
socket.addEventListener("open", () => {
  console.log("WebSocket open");
  setInterval(() => socket.send("ping"), 30000);
  // Optionally, set a custom watchlist right after connecting:
  const myWatchlist = { watchlist: ["AAPL", "MSFT"] };
  socket.send(JSON.stringify(myWatchlist));
});

socket.addEventListener("close", (event) => {
  console.log("WebSocket close:", event);
});
```

## Prerequisites

- Python 3.13+ installed
- Docker & Docker Compose (for containerised mode)

## How It Works

1. **Configuration**  
   - Reads `TICKERS`, `POLL_FREQ` and `REDIS_URL` from environment (or `.env`).  
   - Builds a list of symbols to poll.

2. **Polling Loop (poller service)**  
   - On startup of the poller service (when using Docker Compose), an asyncio background task is launched that:

     ```python
     while True:
        # runs yfinance calls in a threadpool
        data = await fetch_prices(TICKERS)
        # computes diffs & broadcasts to WS clients
        await publish_price_changes(data)
        await asyncio.sleep(POLL_FREQ)
     ```

   - Uses exponential backoff on errors, reset after successful fetch.
   - Stores the latest full snapshot in a Redis hash (key prices).
   - Publishes incremental diffs on a Redis pub/sub channel (prices).

3. **REST API (api service)**  
   - `GET /tickers` returns the current snapshot of all prices.  
   - `GET /tickers/{symbol}` returns a single symbol's latest data.

4. **WebSockets & Watchlists (api service)**  
   - Two endpoints:  
     - `/ws/prices` — publish real-time price diffs  
     - `/ws/news`   — publish any news items  
   - **Default:** on connect, clients receive the full current state of all symbols, then only diffs.
   - **Per-connection watchlist:** clients may send:

    ```javascript
    { "watchlist": ["AAPL", "MSFT", ...] }
    ```

    to subscribe only to those symbols. They then receive:

    - A fresh filtered snapshot from Redis.
    - Subsequent diffs only for symbols in their watchlist.

## Quick start (Docker Compose)

Simply clone the repo and run make start:

```bash
make start
```

which simply builds and runs with `docker compose up --build`. All dependencies are declared in `pyproject.toml` and `uv.lock` and are installed via [uv](https://docs.astral.sh/uv/getting-started/installation/) in the `Dockerfile`.

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
