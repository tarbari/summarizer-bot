# Summarizer Bot for Discord

A Discord bot that monitors channel messages and generates daily summaries of conversations.

## Features

- **Message Logging**: Stores messages from whitelisted users in SQLite database
- **Daily Summaries**: Automatically generates and posts summaries at configured time
- **User Whitelisting**: Only processes messages from approved users
- **Timezone Support**: Configurable timezone for scheduling
- **Recovery System**: Recovers missed messages on bot restart
- **Security**: Bot token must be set via .env file

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure the Bot

Rename `example.config.toml` to `config.toml`.
Edit `config.toml`:

```toml
[bot]
channel_id = 123456789          # Channel ID to monitor
summary_time = "09:00"         # Daily summary time (24h format)
timezone = "UTC"               # Timezone for scheduling

[whitelist]
# List of user IDs whose messages should be included
users = [
    "user_id_1",
    "user_id_2"
]
```

Create `.env` file:

```bash
echo "BOT_TOKEN=your_discord_bot_token_here" > .env
echo "LLM_API_URL=http://your-api-endpoint.com/v1" >> .env
echo "LLM_API_KEY=your-api-key-here" >> .env
echo "CHANNEL_ID=your_channel_id" >> .env  # Optional override
```

**Note**: The LLM API should be OpenAI-compatible (e.g., LM Studio, LocalAI, or OpenAI API).

### 3. Run the Bot

```bash
uv run python main.py
```

## Docker Deployment

### Prerequisites
- Docker installed on your system
- Docker Compose (for compose deployment)

### Build the Docker Image
```bash
docker build -t summarizer-bot .
```

### Run with Docker
```bash
# Create data directory for persistent storage
mkdir -p data logs

# Run the container
docker run -d --name summarizer-bot \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  --env-file .env \
  summarizer-bot
```

### Run with Docker Compose
```bash
# Start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the services
docker-compose down
```

### Configuration Notes
- The `.env` file is automatically loaded by Docker Compose
- Database files are persisted in the `./data` directory
- Logs are persisted in the `./logs` directory (optional)
- To update configuration, modify `.env` and restart containers

### Docker Commands
```bash
# Check container status
docker ps

# View container logs
docker logs -f summarizer-bot

# Restart container
docker restart summarizer-bot

# Update and rebuild
docker-compose down && docker-compose up -d --build
```

## Usage

### Commands

- `!echo` - Test command (responds with your message)
- `!summary` - Manual summary generation (whitelist only)

### Configuration

- **Bot Token**: Must be set in `.env` file for security
- **LLM API URL**: Must be set in `.env` file (OpenAI-compatible API endpoint)
- **LLM API Key**: Must be set in `.env` file for API authentication
- **Channel ID**: Can be set in `config.toml` or `.env`
- **Summary Time**: 24-hour format (e.g., "09:00", "22:30")
- **Timezone**: Any valid timezone (e.g., "UTC", "America/New_York", "Europe/Helsinki")
- **Whitelist**: Add user IDs as strings

#### Timezone Examples

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

## Database

Messages are stored in `data/messages.db` using SQLite. The database includes:

- Message content and metadata
- Author information
- Timestamps
- Channel IDs

## Development

### Adding Dependencies

```bash
uv add package-name
```

### Running Tests

> ![NOTE]
> These tests won't do much. Unit tests will be implemented later.

```bash
# Test configuration
python -c "from bot.config import Config; print('Config OK')"

# Test database
python -c "from bot.database import MessageStore; print('DB OK')"

# Test full integration
python -c "from bot.bot import SummarizerBot; print('Bot OK')"
```

## Security

- **Never commit `.env`** - it contains sensitive tokens and API keys
- **Bot token enforcement**: Configuration will fail if `.env` doesn't contain `BOT_TOKEN`
- **API validation**: Configuration requires both `LLM_API_URL` and `LLM_API_KEY`
- **Whitelist required**: Only whitelisted users' messages are processed

## Roadmap

- [ ] Add unit tetst
