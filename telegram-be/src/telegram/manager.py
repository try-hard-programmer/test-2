"""Telegram client manager implementation."""
import logging
from typing import Dict, Optional, Callable 
from telethon import TelegramClient, events # type: ignore
from telethon.sessions import StringSession # type: ignore
from telethon.tl.types import PeerUser, PeerChat, PeerChannel  # type: ignore

logger = logging.getLogger(__name__)

class TelegramClientManager:
    """Manage multiple Telegram clients."""
    
    def __init__(self):
        """Initialize client manager."""
        self.clients: Dict[str, TelegramClient] = {}
        self.message_handlers: list = []
    
    async def add_client(
        self,
        account_id: str,
        api_id: int,
        api_hash: str,
        session_string: Optional[str] = None
    ) -> TelegramClient:
        """Add and start a Telegram client."""
        if account_id in self.clients:
            return self.clients[account_id]
        
        session = StringSession(session_string) if session_string else StringSession()
        client = TelegramClient(session, api_id, api_hash)
        
        # Register message handler
        @client.on(events.NewMessage(incoming=True))
        async def handle_new_message(event):
            await self._handle_incoming_message(account_id, event)
        
        await client.start()
        self.clients[account_id] = client
        
        # Populate entity cache by getting recent dialogs
        try:
            await client.get_dialogs(limit=100)
            logger.info(f"Populated entity cache for account {account_id}")
        except Exception as e:
            logger.warning(f"Could not populate entity cache: {e}")
        
        logger.info(f"Started Telegram client for account {account_id}")
        return client
    
    async def _handle_incoming_message(self, account_id: str, event):
        """Handle incoming Telegram message."""
        try:
            # Get sender information
            sender = await event.get_sender()
            
            # Extract chat ID - use sender_id for private chats
            if event.is_private:
                chat_id = event.sender_id
            else:
                # For groups/channels
                peer = event.message.peer_id
                if isinstance(peer, PeerUser):
                    chat_id = peer.user_id
                elif isinstance(peer, PeerChat):
                    chat_id = peer.chat_id
                elif isinstance(peer, PeerChannel):
                    chat_id = peer.channel_id
                else:
                    chat_id = event.chat_id
            
            # ✅ NEW: Extract customer details
            customer_data = {}
            if sender:
                customer_data['user_id'] = sender.id if hasattr(sender, 'id') else None
                customer_data['first_name'] = getattr(sender, 'first_name', None)
                customer_data['last_name'] = getattr(sender, 'last_name', None)
                customer_data['username'] = getattr(sender, 'username', None)
                customer_data['phone'] = getattr(sender, 'phone', None)
            
            # Get sender name (for backward compatibility)
            sender_name = None
            if sender:
                if hasattr(sender, 'first_name'):
                    sender_name = sender.first_name
                    if hasattr(sender, 'last_name') and sender.last_name:
                        sender_name += f" {sender.last_name}"
                elif hasattr(sender, 'title'):
                    sender_name = sender.title
            
            message_data = {
                "account_id": account_id,
                "chat_id": str(chat_id),
                "message_id": str(event.message.id),
                "text": event.message.text or "",
                "timestamp": event.message.date.isoformat(),
                "sender_id": str(event.sender_id) if event.sender_id else None,
                "sender_name": sender_name,
                "customer_data": customer_data  # ✅ ADD customer data
            }
            
            # Call all registered handlers
            for handler in self.message_handlers:
                await handler(message_data)
        
        except Exception as e:
            logger.error(f"Error handling incoming message: {e}", exc_info=True)
    
    def register_message_handler(self, handler: Callable) -> None:
        """Register a message handler callback."""
        self.message_handlers.append(handler)
    
    async def send_message(
        self, account_id: str, chat_id: str, text: str
    ) -> Optional[int]:
        """Send a message using a specific account."""
        client = self.clients.get(account_id)
        if not client:
            logger.error(f"Client not found for account {account_id}")
            return None
        
        try:
            # Convert chat_id to integer
            chat_id_int = int(chat_id)
            
            # Get the entity first (this resolves the user/chat)
            try:
                entity = await client.get_entity(chat_id_int)
            except Exception as e:
                logger.error(f"Could not get entity for chat_id {chat_id_int}: {e}")
                # Try to get dialogs to populate entity cache
                await client.get_dialogs()
                # Retry getting entity
                entity = await client.get_entity(chat_id_int)
            
            # Send message using the resolved entity
            message = await client.send_message(entity, text)
            return message.id
        except ValueError as e:
            logger.error(f"Invalid chat_id format: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    async def get_session_string(self, account_id: str) -> Optional[str]:
        """Get session string for an account."""
        client = self.clients.get(account_id)
        if not client:
            return None
        
        return client.session.save()
    
    async def remove_client(self, account_id: str) -> None:
        """Remove and disconnect a client."""
        client = self.clients.get(account_id)
        if client:
            await client.disconnect()
            del self.clients[account_id]
            logger.info(f"Removed client for account {account_id}")
    
    async def disconnect_all(self) -> None:
        """Disconnect all clients."""
        for account_id in list(self.clients.keys()):
            await self.remove_client(account_id)
    
    def is_connected(self, account_id: str) -> bool:
        """Check if a client is connected."""
        client = self.clients.get(account_id)
        return client is not None and client.is_connected()