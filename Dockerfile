FROM python:3.12-slim

RUN apt-get update && apt-get install -y dumb-init && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos "" mcpuser

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project

COPY src/ src/
RUN uv sync --no-dev --frozen

RUN chown -R mcpuser:mcpuser /app

ENV FABRIC_BASE_URL=https://api.fabric.so/v2

USER mcpuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD pgrep -f "python.*fabric_mcp" || exit 1

ENTRYPOINT ["dumb-init", "--"]
CMD [".venv/bin/python", "-m", "fabric_mcp"]
