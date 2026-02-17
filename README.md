# Summarizer Bot for Discord

A Discord bot that monitors channel messages and generates daily summaries of conversations.

## Installation and Setup

### Prerequisites
- Python 3.12+
- UV package manager (included in project)

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure the Bot

#### Configuration Files

1. **Rename and edit config file:**
```bash
cp example.config.toml config.toml
```

Edit `config.toml` with your settings:

```toml
# Summarizer Bot Configuration
# This file uses TOML format for configuration

[bot]
# Channel ID to monitor for messages (this channel's messages are summarized)
monitor_channel = 0

# Time to post daily summary (24h format)
summary_time = "09:00"

# Timezone for summary scheduling
timezone = "UTC"

# List of channel IDs to send summaries to (summaries are sent to these channels only)
subscriber_channels = [
    123456789,  # Example: replace with actual channel IDs
]

[whitelist]
# List of user IDs whose messages should be included in summaries
# Use string format for user IDs
users = [
    "1234"
]

[api]
# LLM Model to use for summarization
# This should match a model available in your API
model = "gpt-3.5-turbo"

# Maximum tokens for LLM responses (adjust based on your model's context window)
# Common values: 2000 for basic models, 4000-8000 for larger context windows
# Note that the discord maximum length for a message is 2000 characters.
max_tokens = 4000
```

2. **Create .env file:**
```bash
echo "BOT_TOKEN=your_discord_bot_token_here" > .env
echo "LLM_API_URL=http://your-api-endpoint.com/v1" >> .env
echo "LLM_API_KEY=your-api-key-here" >> .env
```

**Note**: The LLM API should be OpenAI-compatible (e.g., LM Studio, LocalAI, or OpenAI API).

### 3. Run the Bot

```bash
uv run python main.py
```

## Running with Docker

### Prerequisites
- Docker installed on your system
- Docker Compose (for compose deployment)

### Build and Run

```bash
# Build the Docker image
docker build -t summarizer-bot .

# Create directories for persistent storage
mkdir -p data logs

# Run the container
docker run -d --name summarizer-bot \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  --env-file .env \
  summarizer-bot
```

### Using Docker Compose

```bash
docker compose up -d
```

## Configuration Options

### Environment Variables (required in .env)
- `BOT_TOKEN`: Your Discord bot token
- `LLM_API_URL`: OpenAI-compatible API endpoint
- `LLM_API_KEY`: API authentication key

### Config.toml Settings
- `[bot.monitor_channel]`: Channel ID to monitor for messages (this channel's messages are summarized)
- `[bot.summary_time]`: Daily summary time in 24h format (e.g., "09:00", "22:30")
- `[bot.timezone]`: Timezone for scheduling (e.g., "UTC", "America/New_York", "Europe/Helsinki")
- `[bot.subscriber_channels]`: Array of channel IDs that will receive the summaries
- `[whitelist.users]`: Array of user IDs whose messages should be processed
- `[api.model]`: LLM Model to use for summarization (e.g., "gpt-3.5-turbo")
- `[api.max_tokens]`: Maximum tokens for LLM responses

### Timezone Examples

```toml
# UTC (default)
timezone = "UTC"

# UTC+3 (Eastern European Time)
timezone = "Europe/Helsinki"

# UTC-5 (Eastern Standard Time)
timezone = "America/New_York"

# UTC+2 (Central European Time)
timezone = "Europe/Berlin"
```

See full list of timezones: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

## Features

- **Message Logging**: Stores messages from whitelisted users in monitor channel into an SQLite database
- **Daily Summaries**: Automatically generates and posts summaries at configured time
- **User Whitelisting**: Only processes messages from approved users
- **Timezone Support**: Configurable timezone for scheduling
- **Recovery System**: Recovers missed messages on bot restart

## Usage Commands

- `!echo` - Test command (responds with your message)
- `!summary` - Manual summary generation (whitelist only)

## Database

Messages are stored in `data/messages.db` using SQLite. The database includes:

- Message content and metadata
- Author information
- Timestamps
- Channel IDs

## Roadmap

- [ ] Add unit tests
