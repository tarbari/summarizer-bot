import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from discord import Message
import os


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

    def store_message(self, message: Message) -> bool:
        """Store a Discord message in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO messages 
                    (message_id, author_id, author_name, content, timestamp, channel_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(message.id),
                    str(message.author.id),
                    str(message.author.name),
                    message.content,
                    message.created_at.isoformat(),
                    message.channel.id
                ))
                
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
                
                cursor.execute("""
                    SELECT message_id, author_id, author_name, content, timestamp, channel_id
                    FROM messages
                    WHERE timestamp >= ?
                    ORDER BY timestamp ASC
                """, (timestamp.isoformat(),))
                
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
                
                cursor.execute("""
                    INSERT OR REPLACE INTO bot_state (key, value)
                    VALUES (?, ?)
                """, ('last_processed_id', message_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error setting last processed ID: {e}")
            return False

    def get_message_count_by_user(self, since_timestamp: Optional[datetime] = None) -> Dict[str, int]:
        """Get message count by user (for placeholder summary)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if since_timestamp:
                    cursor.execute("""
                        SELECT author_name, COUNT(*) as count
                        FROM messages
                        WHERE timestamp >= ?
                        GROUP BY author_name
                        ORDER BY count DESC
                    """, (since_timestamp.isoformat(),))
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

    def recover_missed_messages(self, channel_id: int, last_message_id: Optional[str] = None) -> int:
        """Recover missed messages from Discord API"""
        # This would need a Discord client to fetch messages
        # For now, this is a placeholder that will be implemented when we integrate with the bot
        print(f"Recovery would fetch messages from channel {channel_id} since {last_message_id}")
        return 0
