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
echo "CHANNEL_ID=your_channel_id" >> .env  # Optional override
```

### 3. Run the Bot

```bash
uv run python main.py
```

## Usage

### Commands

- `!echo` - Test command (responds with your message)
- `!summary` - Manual summary generation (whitelist only)

### Configuration

- **Bot Token**: Must be set in `.env` file for security
- **Channel ID**: Can be set in `config.toml` or `.env`
- **Summary Time**: 24-hour format (e.g., "09:00", "22:30")
- **Timezone**: Any valid timezone (e.g., "UTC", "America/New_York")
- **Whitelist**: Add user IDs as strings

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

```bash
# Test configuration
python -c "from bot.config import Config; print('Config OK')"

# Test database
python -c "from bot.database import MessageStore; print('DB OK')"

# Test full integration
python -c "from bot.bot import SummarizerBot; print('Bot OK')"
```

## Security

- **Never commit `.env`** - it contains sensitive tokens
- **Bot token enforcement**: Configuration will fail if `.env` doesn't contain `BOT_TOKEN`
- **Whitelist required**: Only whitelisted users' messages are processed

## Roadmap

- [ ] Enhance summary generation with NLP
- [ ] Add message filtering options
- [ ] Implement backup/export functionality
- [ ] Add monitoring and alerting

## License

MIT
