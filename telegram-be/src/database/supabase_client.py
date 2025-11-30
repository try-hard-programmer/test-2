"""Supabase client for Telegram account management."""
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from src.config import config
from src.config.encryption import encryptor

import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Manage Telegram accounts in Supabase."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        # ✅ FIX: Define BOTH table names here
        self.table_name = "telegram_accounts" 
        self.tickets_table = "tickets"
    
    async def create_account(
        self,
        account_label: str,
        api_id: int,
        api_hash: str,
        session_string: str
    ) -> Dict[str, Any]:
        """Create a new Telegram account."""
        encrypted_session = encryptor.encrypt(session_string)
        
        response = self.client.table(self.table_name).insert({
            "account_label": account_label,
            "api_id": api_id,
            "api_hash": api_hash,
            "session_string": encrypted_session,
            "is_active": True
        }).execute()
        
        return response.data[0] if response.data else None
    
    async def get_active_accounts(self) -> List[Dict[str, Any]]:
        """Get ONLY active Telegram accounts (for backend startup)."""
        response = self.client.table(self.table_name).select("*").eq("is_active", True).execute()
        
        accounts = []
        for account in response.data:
            account_copy = account.copy()
            if account_copy.get("session_string"):
                try:
                    account_copy["session_string"] = encryptor.decrypt(account_copy["session_string"])
                except Exception:
                    pass
            accounts.append(account_copy)
        
        return accounts

    async def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get ALL accounts (active and inactive) for the dashboard."""
        response = self.client.table(self.table_name).select("*").order("created_at").execute()
        
        accounts = []
        for account in response.data:
            account_copy = account.copy()
            if account_copy.get("session_string"):
                try:
                    account_copy["session_string"] = encryptor.decrypt(account_copy["session_string"])
                except Exception:
                    pass
            accounts.append(account_copy)
        
        return accounts
    
    async def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account by ID."""
        response = self.client.table(self.table_name).select("*").eq("id", account_id).execute()
        
        if not response.data:
            return None
        
        account = response.data[0].copy()
        if account.get("session_string"):
            try:
                account["session_string"] = encryptor.decrypt(account["session_string"])
            except Exception:
                pass
        
        return account
    
    async def update_session_string(self, account_id: str, session_string: str) -> None:
        """Update session string for an account."""
        encrypted_session = encryptor.encrypt(session_string)
        
        self.client.table(self.table_name).update({
            "session_string": encrypted_session
        }).eq("id", account_id).execute()
    
    async def update_account_label(self, account_id: str, new_label: str) -> Optional[Dict[str, Any]]:
        """Update the label of an account."""
        response = self.client.table(self.table_name).update({
            "account_label": new_label
        }).eq("id", account_id).execute()
        
        return response.data[0] if response.data else None

    async def activate_account(self, account_id: str) -> bool:
        """Activate an account (set is_active=True)"""
        try:
            self.client.table('telegram_accounts')\
                .update({"is_active": True})\
                .eq("id", account_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error activating account: {e}")
            return False

    async def deactivate_account(self, account_id: str) -> bool:
        """Deactivate an account (set is_active=False)"""
        try:
            self.client.table('telegram_accounts')\
                .update({"is_active": False})\
                .eq("id", account_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error deactivating account: {e}")
            return False

    async def delete_account(self, account_id: str) -> None:
        """Permanently delete an account."""
        self.client.table(self.table_name).delete().eq("id", account_id).execute()

    async def create_ticket(self, ticket_data: dict) -> Dict[str, Any]:
        """Create a new ticket"""
        try:
            response = self.client.table(self.tickets_table)\
                .insert(ticket_data)\
                .execute()
            
            if not response.data:
                raise Exception("Failed to create ticket")
            
            # Fetch with account label
            ticket = self.client.table(self.tickets_table)\
                .select("*, telegram_accounts(account_label)")\
                .eq("id", response.data[0]['id'])\
                .single()\
                .execute()
            
            return ticket.data
            
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            raise

    async def get_active_ticket(self, account_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """Check if there is an open ticket for this account+chat combo."""
        try:
            # Filter for tickets that are NOT closed or resolved
            response = self.client.table(self.tickets_table)\
                .select("*")\
                .eq("account_id", account_id)\
                .eq("chat_id", chat_id)\
                .in_("status", ["open", "in_progress"])\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Supabase get ticket error: {e}")
            return None

    async def get_tickets_for_chat(self, account_id: str, chat_id: str) -> List[Dict[str, Any]]:
        """Get history of all tickets for a specific chat."""
        response = self.client.table(self.tickets_table)\
            .select("*")\
            .eq("account_id", account_id)\
            .eq("chat_id", chat_id)\
            .order("created_at", desc=True)\
            .execute()
        return response.data
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update ticket fields (status, priority, subject, etc).
        Usage: await update_ticket("uuid", {"status": "closed", "priority": "high"})
        """
        try:
            # Clean None values so we don't overwrite active data with null
            clean_updates = {k: v for k, v in updates.items() if v is not None}
            
            response = self.client.table(self.tickets_table)\
                .update(clean_updates)\
                .eq("id", ticket_id)\
                .execute()
                
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Supabase update ticket error: {e}")
            raise

    async def delete_ticket(self, ticket_id: str) -> bool:
        """Permanently delete a ticket."""
        try:
            self.client.table(self.tickets_table).delete().eq("id", ticket_id).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase delete ticket error: {e}")
            return False

    async def list_all_tickets(self, status_filter: str = None) -> List[Dict[str, Any]]:
        """Get all tickets, optionally filtered by status."""
        try:
            # We select related account info to display nicely in dashboard
            query = self.client.table(self.tickets_table)\
                .select("*, telegram_accounts(account_label)")\
                .order("created_at", desc=True)
                
            if status_filter:
                query = query.eq("status", status_filter)
                
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Supabase list tickets error: {e}")
            return []

    async def get_ticket_summary(self, start_date: str, end_date: str, agent_id: Optional[str] = None):
        """Get ticket count summary by status and priority"""
        try:
            query = self.client.table(self.tickets_table).select("status, priority")
            
            if start_date:
                query = query.gte("created_at", start_date)
            if end_date:
                query = query.lte("created_at", end_date)
            if agent_id:
                query = query.eq("account_id", agent_id)
            
            result = query.execute()
            tickets = result.data
            
            summary = {
                "total": len(tickets),
                "by_status": {
                    "open": len([t for t in tickets if t["status"] == "open"]),
                    "in_progress": len([t for t in tickets if t["status"] == "in_progress"]),
                    "resolved": len([t for t in tickets if t["status"] == "resolved"]),
                    "closed": len([t for t in tickets if t["status"] == "closed"])
                },
                "by_priority": {
                    "low": len([t for t in tickets if t["priority"] == "low"]),
                    "medium": len([t for t in tickets if t["priority"] == "medium"]),
                    "high": len([t for t in tickets if t["priority"] == "high"]),
                    "urgent": len([t for t in tickets if t["priority"] == "urgent"])
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting ticket summary: {e}")
            raise

    async def get_tickets_by_status(self, status: str, agent_id: Optional[str] = None):
        """Get all tickets with specific status"""
        try:
            query = self.client.table(self.tickets_table)\
                .select("*, telegram_accounts(account_label)")\
                .eq("status", status)\
                .order("updated_at", desc=True)
            
            if agent_id:
                query = query.eq("account_id", agent_id)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting tickets by status: {e}")
            raise
    
    async def get_conversation_by_chat(self, account_id: str, chat_id: str):
        """Get conversation by account_id and chat_id"""
        try:
            result = self.client.table(self.conversations_table)\
                .select("*")\
                .eq("telegram_account_id", account_id)\
                .eq("chat_id", chat_id)\
                .limit(1)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return None

    async def get_messages(self, conversation_id: int):
        """Get messages for a conversation"""
        try:
            result = self.client.table(self.messages_table)\
                .select("*")\
                .eq("conversation_id", conversation_id)\
                .order("timestamp", desc=False)\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []

    async def log_ticket_change(
        self, 
        ticket_id: str, 
        field: str, 
        old_val: str, 
        new_val: str, 
        changed_by: str = "agent"
    ):
        """Log ticket changes for audit trail (manual logging)"""
        try:
            self.client.table("ticket_history").insert({
                "ticket_id": ticket_id,
                "changed_by": changed_by,
                "field_changed": field,
                "old_value": str(old_val) if old_val else None,
                "new_value": str(new_val)
            }).execute()
            logger.info(f"✅ Logged change: {field} = {old_val} → {new_val}")
        except Exception as e:
            logger.error(f"Error logging ticket change: {e}")

    async def get_ticket_history(self, ticket_id: str):
        """Get change history for a ticket"""
        try:
            result = self.client.table("ticket_history")\
                .select("*")\
                .eq("ticket_id", ticket_id)\
                .order("changed_at", desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error getting ticket history: {e}")
            return []

    async def get_agent_attributes(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get agent attributes (persona, knowledge, schedule, etc)"""
        try:
            response = self.client.table('telegram_accounts')\
                .select("persona, knowledge, schedule, integration, ticketing_settings")\
                .eq("id", account_id)\
                .single()\
                .execute()
            
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error getting agent attributes: {e}")
            return None

    async def update_agent_attributes(
        self, 
        account_id: str, 
        attributes: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update agent attributes"""
        try:
            # Validate and clean attributes
            allowed_fields = [
                "persona", 
                "knowledge", 
                "schedule", 
                "integration", 
                "ticketing_settings"
            ]
            
            updates = {
                k: v for k, v in attributes.items() 
                if k in allowed_fields and v is not None
            }
            
            if not updates:
                raise ValueError("No valid attributes to update")
            
            response = self.client.table('telegram_accounts')\
                .update(updates)\
                .eq("id", account_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating agent attributes: {e}")
            raise

# Global Supabase client
supabase_client = SupabaseClient()