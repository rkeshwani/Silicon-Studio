from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.studio.service import DataStudioService

router = APIRouter()
service = DataStudioService()

class PreviewRequest(BaseModel):
    file_path: str
    limit: int = 5

class ConversionRequest(BaseModel):
    file_path: str
    output_path: str
    instruction_col: str
    input_col: Optional[str] = None
    output_col: str

@router.post("/preview")
async def preview_csv(request: PreviewRequest):
    """
    Preview the first N rows of a CSV file.
    """
    try:
        data = service.preview_csv(request.file_path, request.limit)
        return {"data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/convert")
async def convert_to_jsonl(request: ConversionRequest):
    """
    Convert a CSV file to JSONL format for LLM fine-tuning.
    """
    try:
        result = service.convert_csv_to_jsonl(
            request.file_path,
            request.output_path,
            request.instruction_col,
            request.input_col,
            request.output_col
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
