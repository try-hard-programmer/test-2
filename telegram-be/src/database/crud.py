"""Database CRUD Operations (Create, Read, Update, Delete)."""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseCRUDMixin:
    """Mixin class containing all business logic for the database."""

    # --- Write Operations (Using Queue) ---

    async def get_or_create_conversation(
    self, 
    telegram_account_id: str, 
    chat_id: str, 
    chat_name: str = None,
    customer_data: dict = None  # ✅ NEW PARAMETER
) -> int:
        """Get or create a conversation with customer details."""
        # 1. Read (Allowed concurrently)
        async with self.conn.execute(
            "SELECT id FROM conversations WHERE telegram_account_id = ? AND chat_id = ?",
            (telegram_account_id, chat_id)
        ) as cursor:
            row = await cursor.fetchone()
            
        timestamp = datetime.now(timezone.utc)
        
        if row:
            # 2. Update (Queued)
            update_fields = ["last_message_at = ?"]
            params = [timestamp]
            
            if chat_name:
                update_fields.append("chat_name = ?")
                params.append(chat_name)
            
            # ✅ Update customer details if provided
            if customer_data:
                if customer_data.get('first_name'):
                    update_fields.append("customer_first_name = ?")
                    params.append(customer_data['first_name'])
                if customer_data.get('last_name'):
                    update_fields.append("customer_last_name = ?")
                    params.append(customer_data['last_name'])
                if customer_data.get('username'):
                    update_fields.append("customer_username = ?")
                    params.append(customer_data['username'])
                if customer_data.get('phone'):
                    update_fields.append("customer_phone = ?")
                    params.append(customer_data['phone'])
                if customer_data.get('user_id'):
                    update_fields.append("customer_user_id = ?")
                    params.append(str(customer_data['user_id']))
            
            params.append(row[0])
            
            await self._execute_write(
                f"UPDATE conversations SET {', '.join(update_fields)} WHERE id = ?",
                tuple(params)
            )
            return row[0]
        else:
            # 2. Insert (Queued)
            columns = ["telegram_account_id", "chat_id", "chat_name", "last_message_at"]
            placeholders = ["?", "?", "?", "?"]
            values = [telegram_account_id, str(chat_id), chat_name, timestamp]
            
            # ✅ Add customer details if provided
            if customer_data:
                if customer_data.get('first_name'):
                    columns.append("customer_first_name")
                    placeholders.append("?")
                    values.append(customer_data['first_name'])
                if customer_data.get('last_name'):
                    columns.append("customer_last_name")
                    placeholders.append("?")
                    values.append(customer_data['last_name'])
                if customer_data.get('username'):
                    columns.append("customer_username")
                    placeholders.append("?")
                    values.append(customer_data['username'])
                if customer_data.get('phone'):
                    columns.append("customer_phone")
                    placeholders.append("?")
                    values.append(customer_data['phone'])
                if customer_data.get('user_id'):
                    columns.append("customer_user_id")
                    placeholders.append("?")
                    values.append(str(customer_data['user_id']))
            
            return await self._execute_write(
                f"INSERT INTO conversations ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                tuple(values)
            )

    async def save_message(
        self,
        telegram_account_id: str,
        chat_id: str,
        message_id: str,
        direction: str,
        text: str,
        status: str = "received"
    ) -> Optional[int]:
        """Save a message to the database."""
        try:
            # Check duplicate (Read)
            async with self.conn.execute(
                "SELECT id FROM messages WHERE telegram_account_id = ? AND chat_id = ? AND message_id = ?",
                (telegram_account_id, str(chat_id), str(message_id))
            ) as cursor:
                if await cursor.fetchone():
                    return None

            current_time = datetime.now(timezone.utc)

            return await self._execute_write(
                """
                INSERT INTO messages 
                (telegram_account_id, chat_id, message_id, direction, text, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (telegram_account_id, str(chat_id), str(message_id), direction, text, status, current_time)
            )
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    async def update_message_status(
        self, telegram_account_id: str, chat_id: str, message_id: str, status: str
    ) -> None:
        """Update message status."""
        await self._execute_write(
            """
            UPDATE messages 
            SET status = ?
            WHERE telegram_account_id = ? AND chat_id = ? AND message_id = ?
            """,
            (status, telegram_account_id, str(chat_id), str(message_id))
        )
    
    async def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation and its messages."""
        async with self.conn.execute(
            "SELECT telegram_account_id, chat_id FROM conversations WHERE id = ?",
            (conversation_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
        if not row:
            return False
            
        telegram_account_id, chat_id = row[0], row[1]
        
        await self._execute_write(
            "DELETE FROM messages WHERE telegram_account_id = ? AND chat_id = ?",
            (telegram_account_id, chat_id)
        )
        await self._execute_write(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        return True

    # --- Read Operations (Direct - WAL Allows Concurrency) ---
    
    async def get_conversations(self) -> List[Dict[str, Any]]:
        """Get all conversations."""
        async with self.conn.execute(
            """
            SELECT id, telegram_account_id, chat_id, chat_name, last_message_at
            FROM conversations
            ORDER BY last_message_at DESC
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_messages(
        self, conversation_id: int, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        async with self.conn.execute(
            """
            SELECT m.id, m.telegram_account_id, m.chat_id, m.message_id, 
                   m.direction, m.text, m.timestamp, m.status
            FROM messages m
            JOIN conversations c ON m.telegram_account_id = c.telegram_account_id 
                AND m.chat_id = c.chat_id
            WHERE c.id = ?
            ORDER BY m.timestamp ASC
            LIMIT ?
            """,
            (conversation_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_conversation_by_id(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        async with self.conn.execute(
            "SELECT id, telegram_account_id, chat_id, last_message_at FROM conversations WHERE id = ?",
            (conversation_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None