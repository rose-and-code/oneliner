FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock ./
COPY app/ app/

RUN uv sync --frozen --no-dev && rm -rf /root/.cache

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY app/ app/
COPY data/ data/
COPY .env.release .env.release

ENV PATH="/app/.venv/bin:$PATH"
ENV ENV=release

RUN chown -R 1001:1001 /app

USER 1001

EXPOSE 6868

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6868"]
