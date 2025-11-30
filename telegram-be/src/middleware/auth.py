"""Authentication middleware for API protection."""
from fastapi import Header, HTTPException, status
from src.config import config

async def verify_secret_key(x_secret_key: str = Header(None, alias="X-Secret-Key")):
    """Verify the secret key from request header."""
    if not config.TELEGRAM_SECRET_KEY_SERVICE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Secret key not set"
        )
    
    if not x_secret_key or x_secret_key != config.TELEGRAM_SECRET_KEY_SERVICE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing secret key"
        )