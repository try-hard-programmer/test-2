"""Additional utility routes and health checks."""
from fastapi import APIRouter
from src.database import db
from src.telegram import telegram_manager

health_router = APIRouter()


@health_router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        db_status = "connected" if db.conn else "disconnected"
        
        # Check active Telegram clients
        active_clients = len(telegram_manager.clients)
        
        return {
            "status": "healthy",
            "database": db_status,
            "telegram_clients": active_clients,
            "clients_connected": {
                account_id: telegram_manager.is_connected(account_id)
                for account_id in telegram_manager.clients.keys()
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@health_router.get("/accounts")
async def list_accounts():
    """List all active Telegram accounts."""
    try:
        from src.database.supabase_client import supabase_client
        accounts = await supabase_client.get_active_accounts()
        
        # Remove sensitive data
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
        return {"error": str(e)}
