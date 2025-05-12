# fastapi-ticker-hub

[![CI](https://github.com/ettysekhon/fastapi-ticker-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/ettysekhon/fastapi-ticker-hub/actions/workflows/ci.yml)

A minimal, Kubernetes and Docker friendly mono-repo consisting of two services:

- **poller**: periodically fetches market data (via yfinance), computes diffs, publishes to Redis pub/sub, and maintains a full snapshot in Redis.  
- **api**: exposes REST endpoints and WebSockets, serving the Redis snapshot and real-time diffs to clients (with optional per-connection watchlists).

Project structure using packages follows [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) guidance.

---

## Client example

```js
const socket = new WebSocket("ws://localhost:8000/ws/prices");
socket.addEventListener("open", () => {
  setInterval(() => socket.send("ping"), 30000);
  socket.send(JSON.stringify({ watchlist: ["AAPL", "MSFT"] }));
});
socket.addEventListener("message", evt => {
  try { console.log("Update:", JSON.parse(evt.data)); }
  catch { console.warn("Non-JSON:", evt.data); }
});
socket.addEventListener("close", () => console.log("Closed"));
socket.addEventListener("error", e => console.error("WS error", e));
```

## Prerequisites

- Python 3.13+ installed
- Docker & Docker Compose
- make (for convenience)

## How It Works

1. **poller service**  
   - `settings.py` reads `TICKERS`, `POLL_FREQ`, `REDIS_URL` from environment / `.env`  .
   - `main.py` launches one asyncio task per symbol:

     ```python
      while True:
        info = await to_thread(yf.Ticker(sym).info)
        await update_prices({ sym: data })
        await redis.publish("price-diffs", json.dumps(payload))
        await sleep(POLL_FREQ)
     ```

   - Maintains an in-memory snapshot map for fast merges, atomically `SET prices` in Redis.
   - Stores the latest full snapshot in a Redis hash (key prices).
   - Publishes incremental diffs on a Redis pub/sub channel (prices).

2. **api service (REST)**
   - `GET /tickers` - full snapshot from Redis (`GET prices`)
   - `GET /tickers/{symbol}` - one symbol or 404

3. **api service (WebSockets)**
    - `/ws/prices` — on connect, send full snapshot then stream diff messages
    - `/ws/news`   — same pattern for news items
    - Clients may send `{ "watchlist": ["SYM",…] }` to receive only those symbols.

    ```javascript
    { "watchlist": ["AAPL", "MSFT", ...] }
    ```

## Quick start (Docker Compose)

Simply clone the repo and run make start:

```bash
make start
```

- API available at `http://localhost:8000`
- WebSocket endpoints at `ws://localhost:8000/ws/prices` and `/ws/news`

## Testing

Run unit tests:

```bash
make test
```

There is also an Azure CI pipeline that will run lint checks and execute tests.

## Linting & Formatting

The project uses [Ruff](https://docs.astral.sh/ruff/) for linting, formatting and sorting imports for code consistency. Simply run:

```bash
make format
```