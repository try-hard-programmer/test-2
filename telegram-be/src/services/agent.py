"""Agent service for handling automated interactions and tickets."""
import logging
from src.database.supabase_client import supabase_client
from src.telegram import telegram_manager
from src.api.websocket import connection_manager

logger = logging.getLogger(__name__)

async def process_agent_actions(message_data: dict) -> None:
    """Process message for agent triggers (commands, ticket creation)."""
    text_lower = message_data["text"].strip().lower()
    account_id = message_data["account_id"]
    chat_id = message_data["chat_id"]

    # 1. Trigger: User asks for ticket form
    if text_lower == "/ticket":
        response_text = (
            "🎫 **Create Support Ticket**\n\n"
            "To create a ticket, please **reply** to this message with the following format:\n\n"
            "Subject: [Your Title]\n"
            "Priority: [Low/Medium/High]\n"
            "Problem: [Description]"
        )
        await telegram_manager.send_message(account_id, chat_id, response_text)

    # 2. Action: User submits form (Basic Parsing)
    elif "subject:" in text_lower and "problem:" in text_lower:
        await _handle_ticket_submission(account_id, chat_id, message_data["text"])

    # 3. Action: User wants to close ticket
    elif text_lower == "/close":
        await _handle_ticket_closure(account_id, chat_id)


async def _handle_ticket_submission(account_id: str, chat_id: str, text: str) -> None:
    """Parse text and create a ticket if one doesn't exist."""
    # Check for existing active ticket
    active_ticket = await supabase_client.get_active_ticket(account_id, chat_id)
    
    if active_ticket:
        short_id = active_ticket['id'].split('-')[0]
        await telegram_manager.send_message(
            account_id, chat_id,
            f"⚠️ You already have an OPEN ticket (#{short_id}). Please wait for our team."
        )
        return

    # Parse the User's Text
    lines = text.split('\n')
    subject = "User Request"
    priority = "medium"
    description = text # Default to full text
    
    for line in lines:
        line_clean = line.strip()
        lower_line = line_clean.lower()
        if lower_line.startswith("subject:"):
            subject = line_clean.split(":", 1)[1].strip()
        elif lower_line.startswith("priority:"):
            p_val = line_clean.split(":", 1)[1].strip().lower()
            if p_val in ['low', 'medium', 'high', 'urgent']:
                priority = p_val
        elif lower_line.startswith("problem:"):
            description = line_clean.split(":", 1)[1].strip()

    ticket = await supabase_client.create_ticket({
        "account_id": account_id,
        "chat_id": chat_id,
        "source": "user_command",
        "priority": priority,
        "subject": subject,
        "description": description,
        "status": "open"
    })
    
    if ticket:
        short_id = ticket['id'].split('-')[0]
        # Confirm to User
        await telegram_manager.send_message(
            account_id, chat_id,
            f"✅ **Ticket #{short_id} Created**\n\nSubject: {subject}\nStatus: Open"
        )
        
        # Notify Dashboard
        await connection_manager.broadcast({
            "type": "ticket_created",
            "data": ticket
        })


async def _handle_ticket_closure(account_id: str, chat_id: str) -> None:
    """Close an active ticket if requested by user."""
    active_ticket = await supabase_client.get_active_ticket(account_id, chat_id)
    
    if active_ticket:
        await supabase_client.update_ticket(active_ticket['id'], {"status": "closed"})
        
        short_id = active_ticket['id'].split('-')[0]
        await telegram_manager.send_message(
            account_id, chat_id,
            f"✅ **Ticket #{short_id} Closed.**\nThanks for contacting support!"
        )
        
        await connection_manager.broadcast({
            "type": "ticket_updated",
            "data": {**active_ticket, "status": "closed"}
        })