# Builder Stage
FROM python:3.13-alpine AS builder
WORKDIR /app

RUN apk add --no-cache ca-certificates \
    && update-ca-certificates \
    && sed -i 's/https:/http:/' /etc/apk/repositories \
    && apk add --no-cache gcc musl-dev libffi-dev

RUN python3 -m venv /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip --no-cache-dir \
    && pip install uv \
    && uv sync --no-dev

# Final Stage
FROM python:3.13-alpine
WORKDIR /app

RUN apk add --no-cache ca-certificates libffi \
    && update-ca-certificates

RUN pip install --no-cache-dir uv

ENV UV_PROJECT_ENVIRONMENT=/root/.local
ENV PATH=/root/.local/bin:$PATH

COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/pyproject.toml /app/uv.lock ./
COPY packages/api packages/api

EXPOSE 8000

CMD ["uv", "run", "--package", "api", "python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0","--port", "8000", "--ws-ping-interval", "30", "--ws-ping-timeout", "60"]
