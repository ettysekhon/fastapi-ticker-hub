# Builder Stage
FROM python:3.13-alpine AS builder
WORKDIR /app
# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync

# Final Stage
FROM python:3.13-alpine
WORKDIR /app
# Install runtime dependencies
RUN apk add --no-cache libffi
RUN pip install --no-cache-dir uv
COPY --from=builder /root/.cache /root/.cache
COPY --from=builder /app /app
COPY . .
RUN uv sync
EXPOSE 8000
CMD ["uv", "run", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", \
    "--workers", "2", \
    "--bind", "0.0.0.0:8000", \
    "app.main:app"]