import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta
import toml
from dotenv import load_dotenv
import pytz


class Config:
    def __init__(self):
        self.config_data: Dict[str, Any] = {}
        self._load_config()
        self._validate_config()

    def _load_config(self) -> None:
        """Load configuration from TOML file and environment variables.
        .env is loaded after config.toml.
        """
        # Load .env file first
        load_dotenv()

        # Load TOML config
        # TODO: This looks sus.. Check if this logic is ok.
        config_path = Path(__file__).parent.parent / "config.toml"
        if config_path.exists():
            with open(config_path, "r") as f:
                self.config_data = toml.load(f)
        else:
            raise FileNotFoundError(f"Configuration file not found at {config_path}")

        # Override with environment variables if present
        self._override_with_env()

    def _override_with_env(self) -> None:
        """Override config values with environment variables if present"""
        # Bot token MUST come from .env (cannot be set in config.toml)
        if "BOT_TOKEN" and "LLM_API_URL" and "LLM_API_KEY" in os.environ:
            self.config_data["bot"]["token"] = os.environ["BOT_TOKEN"]
            self.config_data["api"]["key"] = os.environ["LLM_API_KEY"]
            self.config_data["api"]["url"] = os.environ["LLM_API_URL"]
        else:
            raise ValueError(
                ".env file is missing BOT_TOKEN, LLM_API_KEY, or LLM_API_URL"
            )

        # Monitor channel ID can come from .env
        if "MONITOR_CHANNEL" in os.environ:
            self.config_data["bot"]["monitor_channel"] = int(os.environ["MONITOR_CHANNEL"])

    def _validate_config(self) -> None:
        """Validate that required configuration values are present"""
        required_fields = {
            "bot.monitor_channel": int,
            "bot.summary_time": str,
            "bot.timezone": str,
            "bot.subscriber_channels": list,
            "whitelist.users": list,
            "api.model": str,
        }

        for field_path, expected_type in required_fields.items():
            keys = field_path.split(".")
            value = self.config_data

            try:
                for key in keys:
                    value = value[key]

                # Type validation
                if not isinstance(value, expected_type):
                    raise ValueError(
                        f"{field_path} should be {expected_type.__name__}, got {type(value).__name__}"
                    )

            except KeyError:
                raise ValueError(f"Missing required configuration: {field_path}")
            except Exception as e:
                raise ValueError(f"Invalid configuration for {field_path}: {e}")

    def get_bot_token(self) -> str:
        """Get the Discord bot token"""
        return self.config_data["bot"]["token"]

    def get_monitor_channel(self) -> int:
        """Get the channel ID to monitor for messages"""
        return self.config_data["bot"]["monitor_channel"]

    def get_subscriber_channels(self) -> list:
        """Get the list of subscriber channel IDs where summaries should be sent"""
        return self.config_data["bot"]["subscriber_channels"]

    def get_summary_time(self) -> datetime:
        """Get the scheduled summary time as a timezone-aware datetime"""
        time_str = self.config_data["bot"]["summary_time"]
        timezone_str = self.config_data["bot"]["timezone"]

        try:
            # Parse time
            hour, minute = map(int, time_str.split(":"))

            # Get timezone
            tz = pytz.timezone(timezone_str)

            # Create datetime for today at the specified time
            now = datetime.now(tz)
            summary_time = now.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )

            # If the time has already passed today, schedule for tomorrow
            if summary_time < now:
                summary_time = summary_time + timedelta(days=1)

            return summary_time

        except Exception as e:
            raise ValueError(f"Invalid time configuration: {e}")

    def get_whitelisted_users(self) -> list:
        """Get the list of whitelisted user IDs"""
        return self.config_data["whitelist"]["users"]

    def get_timezone(self) -> str:
        """Get the configured timezone"""
        return self.config_data["bot"]["timezone"]

    def get_llm_model(self) -> str:
        """Get the configured LLM model name"""
        return self.config_data["api"]["model"]
