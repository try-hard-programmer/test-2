"""API routes for the dashboard."""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect # type: ignore
from pydantic import BaseModel # type: ignore
from typing import Optional
import logging

from src.utils.priority_detector import PriorityDetector
from src.database import db
from src.database.supabase_client import supabase_client
from src.telegram import telegram_manager
from src.api.websocket import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# Request Models
class AddAccountRequest(BaseModel):
    api_id: int
    api_hash: str
    label: str
    phone: str


class UpdateAccountRequest(BaseModel):
    label: str


class ReplyRequest(BaseModel):
    text: str


class VerifyAccountRequest(BaseModel):
    phone: str
    code: str
    api_id: int
    api_hash: str
    label: str


class ToggleAccountRequest(BaseModel):  # <--- NEW MODEL
    is_active: bool

class TicketCreateRequest(BaseModel):
    account_id: str
    chat_id: str
    subject: str
    priority: Optional[str] = None  
    description: Optional[str] = None
    source: Optional[str] = "manual"

class TicketUpdateRequest(BaseModel):
    status: Optional[str] = None      
    priority: Optional[str] = None    
    subject: Optional[str] = None
    description: Optional[str] = None

class AgentAttributesRequest(BaseModel):
    persona: Optional[str] = None
    knowledge: Optional[str] = None
    schedule: Optional[dict] = None
    integration: Optional[dict] = None
    ticketing_settings: Optional[dict] = None

# Routes
@router.post("/accounts/add")
async def add_account(request: AddAccountRequest):
    """Add a new Telegram account."""
    try:
        from telethon import TelegramClient # type: ignore
        from telethon.sessions import StringSession # type: ignore
        
        temp_session = StringSession()
        temp_client = TelegramClient(
            temp_session,
            request.api_id,
            request.api_hash
        )
        
        await temp_client.connect()
        
        if await temp_client.is_user_authorized():
            session_string = temp_client.session.save()
            await temp_client.disconnect()
            
            account = await supabase_client.create_account(
                account_label=request.label,
                api_id=request.api_id,
                api_hash=request.api_hash,
                session_string=session_string
            )
            
            await telegram_manager.add_client(
                account_id=account["id"],
                api_id=request.api_id,
                api_hash=request.api_hash,
                session_string=session_string
            )
            
            await connection_manager.broadcast({
                "type": "account_status",
                "data": {
                    "account_id": account["id"],
                    "label": request.label,
                    "status": "connected"
                }
            })
            
            return {
                "status": "success",
                "account": account
            }
        
        sent_code = await temp_client.send_code_request(request.phone)
        temp_id = f"temp_{request.phone}"
        telegram_manager.clients[temp_id] = temp_client
        
        return {
            "status": "code_sent",
            "message": "Verification code sent to your phone",
            "phone": request.phone,
            "phone_code_hash": sent_code.phone_code_hash
        }
    
    except Exception as e:
        logger.error(f"Error adding account: {e}")
        if 'temp_client' in locals() and temp_client:
            try:
                await temp_client.disconnect()
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/accounts/verify")
async def verify_account(request: VerifyAccountRequest):
    """Verify phone code and complete account setup."""
    try:
        temp_id = f"temp_{request.phone}"
        temp_client = telegram_manager.clients.get(temp_id)
        
        if not temp_client:
            raise HTTPException(status_code=400, detail="No pending verification for this phone.")
        
        try:
            await temp_client.sign_in(request.phone, request.code)
        except Exception as e:
            if "password" in str(e).lower() or "2fa" in str(e).lower():
                raise HTTPException(status_code=400, detail="2FA password required. Not supported in Phase 1.")
            raise
        
        session_string = temp_client.session.save()
        await temp_client.disconnect()
        del telegram_manager.clients[temp_id]
        
        account = await supabase_client.create_account(
            account_label=request.label,
            api_id=request.api_id,
            api_hash=request.api_hash,
            session_string=session_string
        )
        
        await telegram_manager.add_client(
            account_id=account["id"],
            api_id=request.api_id,
            api_hash=request.api_hash,
            session_string=session_string
        )
        
        await connection_manager.broadcast({
            "type": "account_status",
            "data": {
                "account_id": account["id"],
                "label": request.label,
                "status": "connected"
            }
        })
        
        return {
            "status": "success",
            "account": account
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/accounts/{account_id}")
async def update_account(account_id: str, request: UpdateAccountRequest):
    """Update an account's label."""
    try:
        account = await supabase_client.update_account_label(account_id, request.label)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
            
        await connection_manager.broadcast({
            "type": "account_status",
            "data": {
                "account_id": account_id,
                "label": request.label,
                "status": "updated"
            }
        })
        return {"status": "success", "account": account}
    except Exception as e:
        logger.error(f"Error updating account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/accounts/{account_id}")
async def delete_account(account_id: str):
    """Delete an account."""
    try:
        # 1. Disconnect client from Telegram Manager if active
        if telegram_manager.is_connected(account_id):
            await telegram_manager.remove_client(account_id)
        
        # 2. Delete from Supabase
        await supabase_client.delete_account(account_id)
        
        # 3. Broadcast deletion
        await connection_manager.broadcast({
            "type": "account_status",
            "data": {
                "account_id": account_id,
                "status": "deleted"
            }
        })
        
        return {"status": "success", "message": "Account deleted"}
    
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")

@router.get("/conversations")
async def get_conversations():
    """Get all conversations."""
    try:
        conversations = await db.get_conversations()
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: int, limit: int = 100):
    """Get messages for a specific conversation."""
    try:
        messages = await db.get_messages(conversation_id, limit)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}/reply")
async def send_reply(conversation_id: int, request: ReplyRequest):
    """Send a reply to a conversation."""
    try:
        conversation = await db.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        account_id = conversation["telegram_account_id"]
        chat_id = conversation["chat_id"]
        
        message_id = await telegram_manager.send_message(
            account_id=account_id,
            chat_id=chat_id,
            text=request.text
        )
        
        status = "sent" if message_id else "failed"
        msg_id_str = str(message_id) if message_id else f"failed_{conversation_id}_{hash(request.text)}"
        
        saved_id = await db.save_message(
            telegram_account_id=account_id,
            chat_id=chat_id,
            message_id=msg_id_str,
            direction="outgoing",
            text=request.text,
            status=status
        )
        
        await connection_manager.broadcast({
            "type": "message_sent",
            "data": {
                "conversation_id": conversation_id,
                "account_id": account_id,
                "chat_id": chat_id,
                "message_id": msg_id_str,
                "text": request.text,
                "status": status,
                "id": saved_id
            }
        })
        
        if status == "failed":
            raise HTTPException(status_code=500, detail="Failed to send message")
            
        return {"status": "success", "message_id": message_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts")
async def list_accounts():
    """List all Telegram accounts (active and inactive)."""
    try:
        from src.database.supabase_client import supabase_client
        # CHANGED: Now fetching ALL accounts so inactive ones show up in dashboard
        accounts = await supabase_client.get_all_accounts()
        
        safe_accounts = []
        for account in accounts:
            safe_accounts.append({
                "id": account["id"],
                "account_label": account["account_label"],
                "is_active": account["is_active"],
                "created_at": account["created_at"],
                "connected": telegram_manager.is_connected(account["id"])
            })
        
        return {"accounts": safe_accounts}
    except Exception as e:
        logger.error(f"Error listing accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/accounts/{account_id}/toggle")
async def toggle_account(account_id: str, request: ToggleAccountRequest):
    """Toggle account active status."""
    try:
        is_active = request.is_active
        
        if is_active:
            # Activate account
            account = await supabase_client.get_account_by_id(account_id)
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            
            # FIX: Use the helper method instead of direct client call
            await supabase_client.activate_account(account_id)
            
            await telegram_manager.add_client(
                account_id=account["id"],
                api_id=account["api_id"],
                api_hash=account["api_hash"],
                session_string=account.get("session_string")
            )
            
            status = "connected"
        else:
            # Deactivate account
            await supabase_client.deactivate_account(account_id)
            await telegram_manager.remove_client(account_id)
            status = "disconnected"
            
        await connection_manager.broadcast({
            "type": "account_status",
            "data": {
                "account_id": account_id,
                "status": status
            }
        })
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error toggling account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete a conversation."""
    try:
        success = await db.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"status": "success", "message": "Conversation deleted"}
    
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tickets/create")
async def create_ticket(request: TicketCreateRequest):
    """Create a new ticket with auto-priority detection"""
    try:
        # ✅ FIX: Always try auto-detect if priority not explicitly set to high/urgent/low
        # OR if priority is default "medium"
        should_auto_detect = (
            not hasattr(request, '_priority_explicitly_set') or 
            request.priority == "medium"
        )
        
        if should_auto_detect:
            try:
                # Collect text to analyze
                texts_to_analyze = []
                
                if request.subject:
                    texts_to_analyze.append(request.subject)
                
                if request.description:
                    texts_to_analyze.append(request.description)
                
                # Get recent messages from conversation
                conv = await supabase_client.get_conversation_by_chat(
                    request.account_id, 
                    request.chat_id
                )
                
                if conv:
                    messages_data = await supabase_client.get_messages(conv['id'])
                    recent_texts = [
                        msg['text'] for msg in messages_data[-5:]
                        if msg.get('text') and msg.get('direction') == 'incoming'
                    ]
                    texts_to_analyze.extend(recent_texts)
                
                # ✅ ALWAYS detect if we have texts
                if texts_to_analyze:
                    detected_priority = PriorityDetector.detect_from_messages(
                        texts_to_analyze,
                        limit=10,
                        use_ai=False
                    )
                    # ✅ ALWAYS override with detected priority
                    request.priority = detected_priority
                    logger.info(f"✅ Auto-detected priority: {detected_priority} from {len(texts_to_analyze)} texts")
                    logger.info(f"   Texts analyzed: {texts_to_analyze[:3]}")  # Log first 3 texts
                else:
                    logger.warning("⚠️ No texts to analyze, using default medium")
                    request.priority = "medium"
                    
            except Exception as e:
                logger.warning(f"❌ Priority auto-detection failed: {e}")
                import traceback
                logger.warning(traceback.format_exc())
                request.priority = "medium"
        else:
            logger.info(f"ℹ️ Using manually set priority: {request.priority}")
        
        # Create ticket
        new_ticket = await supabase_client.create_ticket({
            "account_id": request.account_id,
            "chat_id": request.chat_id,
            "subject": request.subject,
            "priority": request.priority,
            "description": request.description,
            "source": getattr(request, 'source', 'manual'),
            "status": "open"
        })
        
        await connection_manager.broadcast({
            "type": "ticket_created",
            "data": new_ticket
        })
        
        return {"status": "success", "ticket": new_ticket}
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets")
async def get_tickets(status: Optional[str] = None):
    """List all tickets (optional status filter)."""
    try:
        tickets = await supabase_client.list_all_tickets(status)
        return {"tickets": tickets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, request: TicketUpdateRequest):
    """Update a ticket's status or details."""
    try:
        updates = request.model_dump(exclude_unset=True) # Only take sent fields
        
        updated_ticket = await supabase_client.update_ticket(ticket_id, updates)
        
        if not updated_ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
            
        # Notify Dashboard
        await connection_manager.broadcast({
            "type": "ticket_updated",
            "data": updated_ticket
        })
        
        return {"status": "success", "ticket": updated_ticket}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tickets/{ticket_id}")
async def delete_ticket(ticket_id: str):
    """Delete a ticket permanently."""
    try:
        success = await supabase_client.delete_ticket(ticket_id)
        if not success:
            raise HTTPException(status_code=404, detail="Ticket not found or delete failed")
            
        # Notify Dashboard
        await connection_manager.broadcast({
            "type": "ticket_deleted",
            "data": {"ticket_id": ticket_id}
        })
        
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/tickets/summary")
async def get_ticket_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_id: Optional[str] = None
):
    """Get ticket summary/stats"""
    try:
        from datetime import datetime, timezone
        
        if not start_date:
            now = datetime.now(timezone.utc)
            start_date = now.replace(day=1).isoformat()
        if not end_date:
            end_date = datetime.now(timezone.utc).isoformat()
        
        summary = await supabase_client.get_ticket_summary(start_date, end_date, agent_id)
        
        return {
            "period": {"start": start_date, "end": end_date},
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting ticket summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets/by-status/{status}")
async def get_tickets_by_status(status: str, agent_id: Optional[str] = None):
    """Get tickets filtered by status"""
    try:
        valid_statuses = ["open", "in_progress", "resolved", "closed"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        tickets = await supabase_client.get_tickets_by_status(status, agent_id)
        
        return {"status": status, "tickets": tickets}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tickets by status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/{ticket_id}/history")
async def get_ticket_history(ticket_id: str):
    """Get audit history for a ticket"""
    try:
        history = await supabase_client.get_ticket_history(ticket_id)
        return {"status": "success", "history": history}
    except Exception as e:
        logger.error(f"Error getting ticket history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts/{account_id}/attributes")
async def get_agent_attributes(account_id: str):
    """Get agent attributes (persona, knowledge, schedule, integration, ticketing_settings)"""
    try:
        attributes = await supabase_client.get_agent_attributes(account_id)
        
        if not attributes:
            # Return empty attributes if not found (not an error, just not set yet)
            return {
                "status": "success", 
                "attributes": {
                    "persona": None,
                    "knowledge": None,
                    "schedule": None,
                    "integration": None,
                    "ticketing_settings": None
                }
            }
        
        return {"status": "success", "attributes": attributes}
    except Exception as e:
        logger.error(f"Error getting agent attributes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/accounts/{account_id}/attributes")
async def update_agent_attributes(account_id: str, request: AgentAttributesRequest):
    """Update agent attributes with validation"""
    try:
        # Collect only non-None values
        updates = request.model_dump(exclude_none=True)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No attributes provided")
        
        # ✅ VALIDATION: Persona length
        if "persona" in updates:
            if len(updates["persona"]) > 500:
                raise HTTPException(
                    status_code=400, 
                    detail="Persona must be less than 500 characters"
                )
        
        # ✅ VALIDATION: Knowledge length
        if "knowledge" in updates:
            if len(updates["knowledge"]) > 2000:
                raise HTTPException(
                    status_code=400, 
                    detail="Knowledge must be less than 2000 characters"
                )
        
        # ✅ VALIDATION: Schedule format
        if "schedule" in updates:
            schedule = updates["schedule"]
            if not isinstance(schedule, dict):
                raise HTTPException(status_code=400, detail="Schedule must be an object")
            
            required_keys = ["timezone", "work_hours", "days"]
            missing = [k for k in required_keys if k not in schedule]
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Schedule missing required fields: {missing}"
                )
            
            # Validate work_hours format (HH:MM-HH:MM)
            import re
            if not re.match(r'^\d{2}:\d{2}-\d{2}:\d{2}$', schedule["work_hours"]):
                raise HTTPException(
                    status_code=400,
                    detail="work_hours must be in format HH:MM-HH:MM (e.g., 09:00-17:00)"
                )
            
            # Validate days is a list
            if not isinstance(schedule["days"], list):
                raise HTTPException(
                    status_code=400,
                    detail="days must be an array of day names"
                )
        
        # ✅ VALIDATION: Integration format
        if "integration" in updates:
            integration = updates["integration"]
            if not isinstance(integration, dict):
                raise HTTPException(status_code=400, detail="Integration must be an object")
            
            valid_channels = ["telegram", "whatsapp", "email"]
            invalid = [k for k in integration.keys() if k not in valid_channels]
            if invalid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Integration contains invalid channels: {invalid}. Valid: {valid_channels}"
                )
            
            # All values must be boolean
            non_bool = [k for k, v in integration.items() if not isinstance(v, bool)]
            if non_bool:
                raise HTTPException(
                    status_code=400,
                    detail=f"Integration values must be boolean: {non_bool}"
                )
        
        # ✅ VALIDATION: Ticketing settings
        if "ticketing_settings" in updates:
            settings = updates["ticketing_settings"]
            if not isinstance(settings, dict):
                raise HTTPException(status_code=400, detail="ticketing_settings must be an object")
            
            # Validate auto_assign is boolean
            if "auto_assign" in settings and not isinstance(settings["auto_assign"], bool):
                raise HTTPException(
                    status_code=400,
                    detail="auto_assign must be boolean"
                )
            
            # Validate max_tickets is positive integer
            if "max_tickets" in settings:
                if not isinstance(settings["max_tickets"], int) or settings["max_tickets"] < 1:
                    raise HTTPException(
                        status_code=400,
                        detail="max_tickets must be a positive integer"
                    )
            
            # Validate priority_rules
            if "priority_rules" in settings:
                valid_rules = ["auto", "manual", "ai"]
                if settings["priority_rules"] not in valid_rules:
                    raise HTTPException(
                        status_code=400,
                        detail=f"priority_rules must be one of: {valid_rules}"
                    )
        
        # Update in database
        updated = await supabase_client.update_agent_attributes(account_id, updates)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Broadcast update to connected clients
        await connection_manager.broadcast({
            "type": "agent_attributes_updated",
            "data": {
                "account_id": account_id,
                "attributes": updated
            }
        })
        
        return {"status": "success", "attributes": updated}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent attributes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)