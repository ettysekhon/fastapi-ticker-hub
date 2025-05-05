# Builder Stage
FROM python:3.13-alpine AS builder
WORKDIR /app
RUN sed -i 's/https:/http:/' /etc/apk/repositories \
    && apk update && apk add --no-cache ca-certificates gcc musl-dev libffi-dev
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync

# API Stage
FROM python:3.13-alpine AS api
WORKDIR /app
RUN sed -i 's/https:/http:/' /etc/apk/repositories \
    && apk update && apk add --no-cache ca-certificates libffi
COPY --from=builder /root/.cache /root/.cache
COPY --from=builder /app /app
COPY . .
RUN pip install --no-cache-dir uv && uv sync
EXPOSE 8000
CMD ["gunicorn","-k","uvicorn.workers.UvicornWorker","--workers","2","--bind","0.0.0.0:8000","app.main:app"]

# Poller Stage
FROM python:3.13-alpine AS poller
WORKDIR /app
RUN sed -i 's/https:/http:/' /etc/apk/repositories \
    && apk update && apk add --no-cache ca-certificates libffi
COPY --from=builder /root/.cache /root/.cache
COPY --from=builder /app /app
COPY . .
RUN pip install --no-cache-dir uv && uv sync
CMD ["python","-m","app.polling_worker"]