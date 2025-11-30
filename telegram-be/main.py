"""Main application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.api.test import router as test_router

from src.config import config
from src.database import db
from src.database.supabase_client import supabase_client
from src.telegram import telegram_manager
from src.api.routes import router
from src.api.health import health_router
from src.services.messaging import handle_incoming_message
from src.middleware.auth import verify_secret_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_database_if_needed():
    """Migrate database schema if needed (Simple check)."""
    try:
        # Check for customer columns presence
        if db.conn:
            cursor = await db.conn.execute("PRAGMA table_info(conversations)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # ✅ Migrate chat_name if missing
            if 'chat_name' not in column_names:
                logger.info("Migrating database: Adding chat_name column...")
                await db.conn.execute("ALTER TABLE conversations ADD COLUMN chat_name TEXT")
                await db.conn.commit()
                logger.info("Added chat_name column")
            
            # ✅ Migrate customer fields if missing
            customer_fields = [
                'customer_first_name',
                'customer_last_name', 
                'customer_username',
                'customer_phone',
                'customer_user_id'
            ]
            
            for field in customer_fields:
                if field not in column_names:
                    logger.info(f"Migrating database: Adding {field} column...")
                    await db.conn.execute(f"ALTER TABLE conversations ADD COLUMN {field} TEXT")
                    await db.conn.commit()
                    logger.info(f"Added {field} column")
            
            logger.info("✅ Database migration completed.")
    except Exception as e:
        logger.error(f"Database migration check failed: {e}")


async def initialize_telegram_clients():
    """Initialize active Telegram clients from Supabase."""
    try:
        accounts = await supabase_client.get_active_accounts()
        logger.info(f"Found {len(accounts)} active Telegram accounts")
        
        for account in accounts:
            try:
                await telegram_manager.add_client(
                    account_id=account["id"],
                    api_id=account["api_id"],
                    api_hash=account["api_hash"],
                    session_string=account.get("session_string")
                )
            except Exception as e:
                logger.error(f"Failed to init account {account.get('account_label')}: {e}")
        
        # Register the cleaned-up handler
        telegram_manager.register_message_handler(handle_incoming_message)
    
    except Exception as e:
        logger.error(f"Error initializing Telegram clients: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Telegram API backend...")
    
    # 1. Config & Data Setup
    config.validate()
    config.ensure_data_dir()
    await db.connect()
    await migrate_database_if_needed()
    
    # 2. Telegram Setup
    await initialize_telegram_clients()
    
    yield
    
    # 3. Shutdown
    logger.info("Shutting down...")
    await telegram_manager.disconnect_all()
    await db.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Telegram API",
    version="0.2.0",
    lifespan=lifespan
)

# Protected API routes
app.include_router(
    test_router,
    router, 
    prefix="/api",
    dependencies=[Depends(verify_secret_key)]
)

# Public health check
app.include_router(health_router, prefix="/api/health")

# Static files
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {
        "message": "Telegram API 1.0",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False
    )