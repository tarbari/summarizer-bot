# Dockerfile for Summarizer Bot
# Single-stage build for simplicity

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Create and switch to non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync

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