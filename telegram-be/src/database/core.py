"""SQLite database core infrastructure."""
import aiosqlite # type: ignore
import asyncio
import logging
from typing import Any, Optional
from src.config import config
from src.database.schema import CREATE_CONVERSATIONS_TABLE, CREATE_MESSAGES_TABLE

logger = logging.getLogger(__name__)

class DatabaseCore:
    """Manage SQLite database connection and write queue."""
    
    def __init__(self):
        """Initialize database connection."""
        self.db_path = config.SQLITE_DB_PATH
        self.conn: Optional[aiosqlite.Connection] = None
        self.write_queue = asyncio.Queue()
        self.writer_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def connect(self) -> None:
        """Connect to SQLite database and start writer."""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        
        # Enable WAL (Write-Ahead Logging) for high concurrency
        await self.conn.execute("PRAGMA journal_mode=WAL;")
        await self.conn.execute("PRAGMA synchronous=NORMAL;")
        
        await self._create_tables()
        
        # Start the background writer task
        self._running = True
        self.writer_task = asyncio.create_task(self._process_write_queue())
        logger.info("Database writer task started (WAL mode)")
    
    async def close(self) -> None:
        """Close database connection and stop writer."""
        self._running = False
        if self.writer_task:
            await self.write_queue.join() # Wait for pending writes
            self.writer_task.cancel()
            try:
                await self.writer_task
            except asyncio.CancelledError:
                pass
        
        if self.conn:
            await self.conn.close()
    
    async def _create_tables(self) -> None:
        """Create database tables using schema."""
        await self.conn.execute(CREATE_CONVERSATIONS_TABLE)
        await self.conn.execute(CREATE_MESSAGES_TABLE)
        await self.conn.commit()

    async def _process_write_queue(self) -> None:
        """Background task to process write operations sequentially."""
        while self._running:
            try:
                # Get the next write operation
                query, args, future = await self.write_queue.get()
                
                try:
                    cursor = await self.conn.execute(query, args)
                    await self.conn.commit()
                    
                    # Return result to the caller
                    if not future.done():
                        if "INSERT" in query.upper():
                            future.set_result(cursor.lastrowid)
                        else:
                            future.set_result(True)
                except Exception as e:
                    logger.error(f"Database write error: {e}")
                    if not future.done():
                        future.set_exception(e)
                finally:
                    self.write_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Critical error in DB writer: {e}")
                await asyncio.sleep(1)

    async def _execute_write(self, query: str, args: tuple) -> Any:
        """Helper to push write op to queue and wait for result."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self.write_queue.put((query, args, future))
        return await future