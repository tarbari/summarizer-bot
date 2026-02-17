# Dockerfile for Summarizer Bot
# Multi-stage build for optimized image size

# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH for builder stage
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Create and switch to non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /root/.cargo/bin/uv /home/appuser/.local/bin/uv
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Add uv to PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copy application code
COPY main.py bot/ ./

# Set environment variables (will be overridden by docker run -e or .env file)
ENV BOT_TOKEN="" \
    LLM_API_URL="" \
    LLM_API_KEY="" \
    CHANNEL_ID=""

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import sys; sys.exit(0 if open('main.py').read() else 1)" || exit 1

# Command to run the bot
CMD ["uv", "run", "python", "main.py"]
