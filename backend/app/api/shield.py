from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.shield.service import PIIShieldService

router = APIRouter()
# Initialize service lazily or on import? Import is better for MVP simplicity
service = PIIShieldService()

class ScanRequest(BaseModel):
    text: str
    entities: Optional[List[str]] = None

@router.post("/scan")
async def scan_text(request: ScanRequest):
    """
    Scan text for PII.
    """
    results = service.analyze_text(request.text, request.entities)
    return {"results": results}

@router.post("/redact")
async def redact_text(request: ScanRequest):
    """
    Redact PII from text.
    """
    result = service.anonymize_text(request.text, request.entities)
    return result
