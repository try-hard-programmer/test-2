"""Configuration management for the application."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    TELEGRAM_SECRET_KEY_SERVICE: str = os.getenv("TELEGRAM_SECRET_KEY_SERVICE", "")
    
    # Server
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8005"))
    
    # Database
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./data/messages.db")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        required = {
            "ENCRYPTION_KEY": cls.ENCRYPTION_KEY,
            "TELEGRAM_SECRET_KEY_SERVICE": cls.TELEGRAM_SECRET_KEY_SERVICE,
        }
        
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    @classmethod
    def ensure_data_dir(cls) -> None:
        """Ensure data directory exists."""
        db_path = Path(cls.SQLITE_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)


config = Config()