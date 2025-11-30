"""Test routes."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class TestPayload(BaseModel):
    session_id: str
    phone_number: str
    api_id: int
    api_hash: str
    session_string: str


@router.post("/test")
async def test_endpoint(payload: TestPayload):
    """Test endpoint that receives session payload."""
    
    logger.info(f"Received test payload for session_id: {payload.session_id}")
    
    return {
        "status": "success",
        "message": "Payload received successfully",
        "data": {
            "session_id": payload.session_id,
            "phone_number": payload.phone_number,
            "api_id": payload.api_id,
            "api_hash_preview": payload.api_hash[:10] + "...",
            "session_string_preview": payload.session_string[:20] + "..." if payload.session_string else None
        }
    }