# Builder Stage
FROM python:3.13-alpine AS builder
RUN apk add --no-cache \
    build-base musl-dev python3-dev libffi-dev openssl-dev \
    freetype-dev libpng-dev

WORKDIR /app
RUN python3 -m venv /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip \
    && pip install uv \
    && uv sync --no-dev

# Final Stage
FROM python:3.13-alpine

RUN apk add --no-cache libffi openssl freetype libpng

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV UV_PROJECT_ENVIRONMENT=/root/.local
ENV PATH=/root/.local/bin:$PATH

COPY --from=builder /app/pyproject.toml /app/uv.lock ./
COPY packages/poller packages/poller

ENTRYPOINT ["uv", "run", "--package", "poller", "python", "-m", "poller.main"]