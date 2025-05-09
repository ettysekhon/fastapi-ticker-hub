#!/usr/bin/env bash

set -euo pipefail

export REDIS_URL=redis://localhost:6379
export TICKERS=AAPL,MSFT
export POLL_FREQ=5

echo "Running tests with local environment..."
uv run --active pytest -q --tb=short "$@"
