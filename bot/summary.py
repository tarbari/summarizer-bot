from datetime import datetime, timedelta
from discord.ext import commands
from discord import TextChannel


class SummaryGenerator:
    def __init__(self, message_store, config):
        """Initialize summary generator with message store and config"""
        self.message_store = message_store
        self.config = config
        self.llm_client = None
        self._initialize_llm_client()

    def _initialize_llm_client(self) -> None:
        """Initialize the LLM client for summarization"""
        try:
            from bot.llm_client import LLMClient

            self.llm_client = LLMClient(self.config)
            print("LLM client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize LLM client: {e}")
            self.llm_client = None

    async def generate_llm_summary(self) -> str:
        """
        Generate a summary using LLM for the last 24 hours of messages
        """
        if not self.llm_client:
            return "LLM client not available. Using fallback summary."

        try:
            # Get messages from last 24 hours
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
            messages = self.message_store.get_messages_since(twenty_four_hours_ago)

            if not messages:
                return "No messages to summarize from the last 24 hours."

            # Generate summary using LLM
            summary = await self.llm_client.generate_summary(messages)

            # Format the summary with header
            summary_lines = ["**Daily Channel Summary**"]
            summary_lines.append("*Summary period: Last 24 hours*\n")
            summary_lines.append(summary)

            return "\n".join(summary_lines)

        except Exception as e:
            print(f"Failed to generate LLM summary: {e}")
            return f"Failed to generate summary: {e}"

    async def generate_daily_summary(self) -> str:
        """
        Generate a daily summary of messages
        Uses LLM if available, falls back to placeholder if not
        """
        # Try to use LLM summary if available
        if self.llm_client:
            try:
                return await self.generate_llm_summary()
            except Exception as e:
                print(f"LLM summary failed, falling back to placeholder: {e}")

        # Fallback to placeholder implementation
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        message_counts = self.message_store.get_message_count_by_user(
            twenty_four_hours_ago
        )

        if not message_counts:
            return "No messages to summarize from the last 24 hours."

        # Generate placeholder summary
        summary_lines = ["**Daily Channel Summary**"]
        summary_lines.append("*Summary period: Last 24 hours*\n")

        summary_lines.append("**Message activity by user:**")
        for author_name, count in message_counts.items():
            summary_lines.append(f"• {author_name}: {count} messages")

        summary_lines.append(
            "\n*This is a placeholder summary. LLM summarization is not currently available.*"
        )

        return "\n".join(summary_lines)

    async def send_summary_to_subscriber_channels(
        self, bot: commands.Bot, subscriber_channel_ids: list
    ) -> dict:
        """Send summary to all subscriber channels only"""
        results = {}
        summary_content = await self.generate_daily_summary()

        for channel_id in subscriber_channel_ids:
            results[channel_id] = await self._send_to_single_channel(
                bot, channel_id, summary_content
            )

        return results

    async def _send_to_single_channel(
        self, bot: commands.Bot, channel_id: int, summary_content: str
    ) -> bool:
        """Helper method to send summary to a single channel"""
        try:
            channel = bot.get_channel(channel_id)

            if isinstance(channel, TextChannel):
                await channel.send(summary_content)
                return True
            else:
                print(f"Channel {channel_id} is not a text channel")
                return False

        except Exception as e:
            print(f"Error sending summary to channel {channel_id}: {e}")
            return False

    # Deprecated method - kept for backward compatibility but not used
    async def send_summary_to_channel(self, bot: commands.Bot, channel_id: int) -> bool:
        """Deprecated: Send the generated summary to the specified channel"""
        print("Warning: send_summary_to_channel is deprecated. Use send_summary_to_subscriber_channels instead.")
        return await self._send_to_single_channel(bot, channel_id, await self.generate_daily_summary())

    def get_summary_schedule(self) -> datetime:
        """Get the next scheduled summary time"""
        return self.config.get_summary_time()
