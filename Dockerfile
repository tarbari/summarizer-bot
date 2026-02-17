FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py ./
COPY config.toml ./
COPY bot/ ./bot/

# Health check (example: check if main.py can import critical modules)
HEALTHCHECK --interval=30s --timeout=3s \
    CMD python3 -c "import main; print('OK')" || exit 1

# Command to run the bot
CMD ["python3", "main.py"]

