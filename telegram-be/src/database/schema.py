"""SQL Table Definitions."""

CREATE_CONVERSATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_account_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chat_name TEXT,
    customer_first_name TEXT,
    customer_last_name TEXT,
    customer_username TEXT,
    customer_phone TEXT,
    customer_user_id TEXT,
    UNIQUE(telegram_account_id, chat_id)
);
"""

CREATE_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_account_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('incoming', 'outgoing')),
    text TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'received' CHECK(status IN ('received', 'sent', 'failed')),
    UNIQUE(telegram_account_id, chat_id, message_id)
);
"""