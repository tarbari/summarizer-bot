from sys import exit
from discord import Intents, Message
from discord.ext import commands, tasks
from discord.ext.commands import Bot as DiscordBot
from datetime import datetime, timedelta, time as datetime_time
import pytz

from bot.config import Config
from bot.database import MessageStore
from bot.summary import SummaryGenerator


class SummarizerBot:
    def __init__(self):
        """Initialize the summarizer bot with configuration and components"""
        try:
            self.config = Config()
            self.message_store = MessageStore()
            self.summary_generator = SummaryGenerator(self.message_store, self.config)
            self.bot = self._setup_discord_bot()
            self.daily_summary_task = self._setup_daily_task()
            self.bot.run(self.config.get_bot_token())

        except Exception as e:
            print(f"Failed to initialize bot: {e}")
            exit(1)

    def _setup_discord_bot(self) -> DiscordBot:
        """Set up and configure the Discord bot"""
        # Configure intents
        intents = Intents(68608)
        intents.guilds = True
        intents.messages = True
        intents.message_content = True

        # Create bot instance
        bot = commands.Bot(command_prefix="!", intents=intents)

        # Set up event handlers
        bot.event(self.on_ready)
        bot.event(self.on_message)

        # Add commands
        @bot.command(name="echo")
        async def echo_command(ctx: commands.Context):
            """Echo command for testing"""
            await ctx.send(
                f"Hello, {ctx.author}.\nYou just said:\n```\n{ctx.message.content}\n```"
            )

        @bot.command(name="summary")
        async def manual_summary_command(ctx: commands.Context):
            """Manual summary command that generates an LLM-powered summary and sends it to the current channel"""
            await ctx.send("Contacting LLM to generate summary...")

            try:
                # Use the async daily summary method
                summary = await self.summary_generator.generate_daily_summary()
                await ctx.send(summary)
            except Exception as e:
                await ctx.send(f"Failed to generate summary: {e}")

        @bot.command(name="lottonumerot")
        async def lotto_command(ctx: commands.Context):
            """Due to popular demand here is a lotto number generator."""
            valid_nums = [n for n in range(1, 41)]
            from random import shuffle

            shuffle(valid_nums)
            await ctx.send(
                f"Viikon lottonumerot ovat: {valid_nums[0:7]}\nJa lisänumero on: {valid_nums[7]}"
            )

        return bot

    def _setup_daily_task(self) -> tasks.Loop:
        """Set up the daily summary task"""

        @tasks.loop(time=self._get_task_time())
        async def daily_summary_task():
            await self._run_daily_summary()

        return daily_summary_task

    def _get_task_time(self) -> datetime_time:
        """Calculate the time for the daily task"""
        summary_datetime = self.summary_generator.get_summary_schedule()
        return summary_datetime.timetz()

    async def _setup_initial_task_delay(self):
        """Set up the initial delay for the first task run"""
        # Get the scheduled time
        scheduled_time = self.summary_generator.get_summary_schedule()
        now = datetime.now(pytz.timezone(self.config.get_timezone()))

        # If the scheduled time is in the past (for today), schedule for tomorrow
        if scheduled_time < now:
            scheduled_time = scheduled_time + timedelta(days=1)

        # Calculate delay until first run
        delay_seconds = (scheduled_time - now).total_seconds()

        if delay_seconds > 0:
            print(f"First daily summary scheduled in {delay_seconds:.1f} seconds")
            # The task will run at the scheduled time automatically
        else:
            # This shouldn't happen, but handle it just in case
            print("Scheduled time is in the past, running immediately")
            await self._run_daily_summary()

    async def on_ready(self):
        """Handle bot ready event"""
        print(f"Logged in as {self.bot.user}")

        # Start daily summary task
        if not self.daily_summary_task.is_running():
            self.daily_summary_task.start()
            next_run = self.daily_summary_task.next_iteration
            print(f"Daily summary task scheduled for: {next_run}")

        # Check for missed messages on startup
        await self._recover_missed_messages()

        # Set up the initial delay for the first run
        await self._setup_initial_task_delay()

    async def on_message(self, message: Message):
        """Handle incoming messages"""
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return

        # Only process messages from the configured monitor channel
        if message.channel.id == self.config.get_monitor_channel():
            # Check if author is whitelisted
            if str(message.author.id) in self.config.get_whitelisted_users():
                # Debug: Check message components and attachments
                has_components = hasattr(message, "components") and message.components
                has_attachments = (
                    hasattr(message, "attachments") and message.attachments
                )
                has_embeds = message.embeds
                has_content = message.content.strip()

                print(
                    f"DEBUG: Message from {message.author} - Content: {has_content}, Embeds: {has_embeds}, Components: {has_components}, Attachments: {has_attachments}"
                )

                # Store the message
                if self.message_store.store_message(message):
                    # Improved logging to show content type
                    if message.content.strip() and message.embeds:
                        print(
                            f"Stored combined message from {message.author}: text + embeds"
                        )
                    elif message.content.strip():
                        print(
                            f"Stored text message from {message.author}: {message.content[:50]}..."
                        )
                    elif message.embeds:
                        print(f"Stored embed message from {message.author} (RSS feed)")
                    else:
                        print(
                            f"Stored message from {message.author} (no visible content)"
                        )

                    # Update last processed message ID
                    self.message_store.set_last_processed_id(str(message.id))
                else:
                    print(f"Failed to store message from {message.author}")
            else:
                print(f"Ignoring message from non-whitelisted user: {message.author}")

        # Process commands
        await self.bot.process_commands(message)

    async def _run_daily_summary(self):
        """Run the daily summary generation and posting to subscriber channels only"""
        print("Running daily summary task...")

        try:
            # Get subscriber channels from config (only these will receive summaries)
            subscriber_channels = self.config.get_subscriber_channels()

            if not subscriber_channels:
                print("No subscriber channels configured, skipping summary sending")
                return

            print(f"Sending summary to {len(subscriber_channels)} subscriber channels")

            # Send to subscriber channels only
            results = await self.summary_generator.send_summary_to_subscriber_channels(
                self.bot, subscriber_channels
            )

            # Log results
            successful_channels = [cid for cid, success in results.items() if success]
            failed_channels = [cid for cid, success in results.items() if not success]

            print(f"Successfully sent to channels: {successful_channels}")
            if failed_channels:
                print(f"Failed to send to channels: {failed_channels}")

        except Exception as e:
            print(f"Error in daily summary task: {e}")

    async def _recover_missed_messages(self):
        """Recover any missed messages from the last 24 hours"""
        print("Checking for missed messages...")

        # Get last processed message ID
        last_id = self.message_store.get_last_processed_id()

        if last_id:
            print(f"Last processed message ID: {last_id}")
            # TODO: Implement actual Discord API fetching for recovery
            # For now, this is a placeholder
            recovered = self.message_store.recover_missed_messages(
                self.config.get_monitor_channel(), last_id
            )
            print(f"Recovered {recovered} missed messages")
        else:
            print("No previous message ID found, starting fresh")
