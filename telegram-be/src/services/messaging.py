# telegram-be/src/services/messaging.py - UPDATE handle_incoming_message

"""Service for handling core messaging logic."""
import logging
from src.database import db
from src.api.websocket import connection_manager
from src.services.agent import process_agent_actions

logger = logging.getLogger(__name__)

async def handle_incoming_message(message_data: dict) -> None:
    """
    Handle incoming Telegram messages.
    1. Save to Local DB
    2. Broadcast to Dashboard
    3. Trigger Agent Logic
    """
    try:
        # ✅ Extract customer data from message_data
        customer_data = message_data.get("customer_data", {})
        
        # 1. Save to LOCAL Database with customer details
        await db.get_or_create_conversation(
            telegram_account_id=message_data["account_id"],
            chat_id=message_data["chat_id"],
            chat_name=message_data.get("sender_name"),
            customer_data=customer_data  # ✅ PASS customer data
        )
        
        saved_id = await db.save_message(
            telegram_account_id=message_data["account_id"],
            chat_id=message_data["chat_id"],
            message_id=message_data["message_id"],
            direction="incoming",
            text=message_data["text"],
            status="received"
        )
        
        if saved_id:
            # 2. Broadcast to WebSocket
            await connection_manager.broadcast({
                "type": "message_received",
                "data": {
                    **message_data,
                    "id": saved_id
                }
            })
            logger.info(f"Received message from {message_data.get('sender_name', 'Unknown')}")

            # 3. Trigger Agent / Ticket Automation
            await process_agent_actions(message_data)

    except Exception as e:
        logger.error(f"Error handling incoming message: {e}", exc_info=True)