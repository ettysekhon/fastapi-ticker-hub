# fastapi-ticker-hub

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

## Running Locally

Start the API with hot reload:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### REST endpoints

- `GET /tickers` – list all prices
- `GET /tickers/{symbol}` – single ticker data

## WebSocket endpoints

-- Prices: ws://localhost:8000/ws/prices
-- News: ws://localhost:8000/ws/news

Clients should accept the connection and will immediately receive the current full snapshot (`state.prices` or `state.news`), then only incremental updates as JSON objects.

## Docker Compose

Build and run with Redis:

```bash
docker compose up --build
```

- API available at `http://localhost:8000`
- WebSocket endpoints at `ws://localhost:8000/ws/prices` and `/ws/news`

## Testing

Run unit tests:

```bash
uv run pytest -q
```

## Deployment

- On-premise: use Docker Compose or your orchestrator with the same image
- Cloud: push to registry and deploy (Kubernetes, ECS, Cloud Run, etc.)
