# Builder Stage
FROM python:3.13-alpine AS builder
WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev

RUN python3 -m venv /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip --no-cache-dir \
    && pip install uv \
    && uv sync --no-dev

# Final Stage
FROM python:3.13-alpine
WORKDIR /app

RUN apk add --no-cache libffi

RUN pip install --no-cache-dir uv

ENV UV_PROJECT_ENVIRONMENT=/root/.local
ENV PATH=/root/.local/bin:$PATH

COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/pyproject.toml /app/uv.lock ./
COPY packages/poller packages/poller

ENTRYPOINT ["uv", "run", "--package", "poller", "python", "-m", "poller.main"]