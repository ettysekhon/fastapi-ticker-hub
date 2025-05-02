# fastapi-ticker-hub

A minimal FastAPI + Socket.IO service that polls market prices and serves them via REST and WebSocket rooms.

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

WebSocket namespace for real-time updates: connect to `ws://localhost:8000/ws and emit { "room": "prices" } or { "room": "news" }`.

## Docker Compose

Build and run with Redis:

```bash
docker compose up --build
```

- API available at `http://localhost:8000`
- Redis at `localhost:6379`

## Testing

Run unit tests:

```bash
uv run pytest -q
```

## Deployment

- On-premise: use Docker Compose or your orchestrator with the same image
- Cloud: push to registry and deploy (Kubernetes, ECS, Cloud Run, etc.)
