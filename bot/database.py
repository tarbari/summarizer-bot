import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from discord import Message


class MessageStore:
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the message store with SQLite database"""
        if db_path is None:
            # Default to data/messages.db in project root
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "messages.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    author_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    channel_id INTEGER NOT NULL
                )
            """)

            # Create bot_state table for tracking last processed message
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            conn.commit()

    def _extract_embed_content(self, message: Message) -> str:
        """Extract content from Discord embeds and format as readable text"""
        if not message.embeds:
            return ""

        content_parts = []

        for embed in message.embeds:
            # Add title if available
            if embed.title:
                content_parts.append(f"**{embed.title}**")

            # Add description if available
            if embed.description:
                content_parts.append(embed.description)

            # Add fields if available
            if embed.fields:
                for field in embed.fields:
                    if field.name and field.value:
                        content_parts.append(f"**{field.name}**: {field.value}")

            # Add URL if available (for source attribution)
            if embed.url:
                content_parts.append(f"Source: {embed.url}")

            # Add footer if available and different from URL
            if (
                embed.footer
                and embed.footer.text
                and (not embed.url or embed.footer.text != embed.url)
            ):
                content_parts.append(f"_{embed.footer.text}_")

        return "\n".join(content_parts)

    def _extract_component_content(self, message: Message) -> str:
        """Extract content from Discord message components (buttons, select menus, etc.)"""
        if not hasattr(message, "components") or not message.components:
            return ""

        content_parts = []

        for component in message.components:
            content_parts.extend(self._extract_from_component(component))

        return "\n\n".join(content_parts) if content_parts else ""

    def _extract_from_component(self, component) -> List[str]:
        """Recursively extract content from a component and its children"""
        content_parts = []

        # Handle different component types
        if hasattr(component, "content") and component.content:
            # TextDisplay components have direct content
            content_parts.append(component.content)

        # Handle children recursively
        if hasattr(component, "children") and component.children:
            for child in component.children:
                content_parts.extend(self._extract_from_component(child))

        # Handle other component attributes
        if hasattr(component, "label") and component.label:
            content_parts.append(f"[{component.label}]")
        if hasattr(component, "value") and component.value:
            content_parts.append(component.value)
        if hasattr(component, "placeholder") and component.placeholder:
            content_parts.append(f"({component.placeholder})")

        return content_parts

    def _extract_attachment_content(self, message: Message) -> str:
        """Extract content from message attachments"""
        if not hasattr(message, "attachments") or not message.attachments:
            return ""

        content_parts = []

        for attachment in message.attachments:
            if attachment.filename:
                content_parts.append(f"Attachment: {attachment.filename}")
            if attachment.url:
                content_parts.append(f"[{attachment.url}]")

        return "\n".join(content_parts) if content_parts else ""

    def store_message(self, message: Message) -> bool:
        """Store a Discord message in the database, combining text, embed, component, and attachment content"""
        try:
            # Start with text content
            content_parts = []

            # Add regular message content if it exists
            if message.content.strip():
                content_parts.append(message.content)

            # Add embed content if embeds exist
            if message.embeds:
                embed_content = self._extract_embed_content(message)
                if embed_content:
                    content_parts.append(embed_content)

            # Add component content if components exist
            component_content = self._extract_component_content(message)
            if component_content:
                content_parts.append(f"Components: {component_content}")

            # Add attachment content if attachments exist
            attachment_content = self._extract_attachment_content(message)
            if attachment_content:
                content_parts.append(attachment_content)

            # Combine all content
            combined_content = "\n\n".join(content_parts)

            # If no content at all, skip storage
            if not combined_content.strip():
                print(f"No content found in message from {message.author}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO messages
                    (message_id, author_id, author_name, content, timestamp, channel_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(message.id),
                        str(message.author.id),
                        str(message.author.name),
                        combined_content,
                        message.created_at.isoformat(),
                        message.channel.id,
                    ),
                )

                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error storing message: {e}")
            return False

    def get_messages_since(self, timestamp: datetime) -> List[Dict[str, Any]]:
        """Get messages since a specific timestamp"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT message_id, author_id, author_name, content, timestamp, channel_id
                    FROM messages
                    WHERE timestamp >= ?
                    ORDER BY timestamp ASC
                """,
                    (timestamp.isoformat(),),
                )

                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []

    def get_last_24h_messages(self) -> List[Dict[str, Any]]:
        """Get messages from the last 24 hours"""
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        return self.get_messages_since(twenty_four_hours_ago)

    def get_last_processed_id(self) -> Optional[str]:
        """Get the last processed message ID from bot state"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT value FROM bot_state WHERE key = 'last_processed_id'
                """)

                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error getting last processed ID: {e}")
            return None

    def set_last_processed_id(self, message_id: str) -> bool:
        """Set the last processed message ID in bot state"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO bot_state (key, value)
                    VALUES (?, ?)
                """,
                    ("last_processed_id", message_id),
                )

                conn.commit()
                return True
        except Exception as e:
            print(f"Error setting last processed ID: {e}")
            return False

    def get_message_count_by_user(
        self, since_timestamp: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Get message count by user (for placeholder summary)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if since_timestamp:
                    cursor.execute(
                        """
                        SELECT author_name, COUNT(*) as count
                        FROM messages
                        WHERE timestamp >= ?
                        GROUP BY author_name
                        ORDER BY count DESC
                    """,
                        (since_timestamp.isoformat(),),
                    )
                else:
                    cursor.execute("""
                        SELECT author_name, COUNT(*) as count
                        FROM messages
                        GROUP BY author_name
                        ORDER BY count DESC
                    """)

                return dict(cursor.fetchall())
        except Exception as e:
            print(f"Error getting message counts: {e}")
            return {}

    def recover_missed_messages(
        self, channel_id: int, last_message_id: Optional[str] = None
    ) -> int:
        """Recover missed messages from Discord API"""
        # This would need a Discord client to fetch messages
        # For now, this is a placeholder that will be implemented when we integrate with the bot
        print(
            f"Recovery would fetch messages from channel {channel_id} since {last_message_id}"
        )
        return 0
