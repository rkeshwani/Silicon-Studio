from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
from app.engine.factory import EngineFactory, get_engine

router = APIRouter()

# Helper to get service or raise error
def get_service_or_raise():
    service = get_engine()
    if not service:
        # Check if it's because no engine is selected vs no hardware
        caps = EngineFactory.get_hardware_capabilities()
        if not caps["mlx"] and not caps["cuda"]:
            raise HTTPException(status_code=503, detail="No compatible hardware (MLX or CUDA) found.")
        raise HTTPException(status_code=503, detail="Engine not initialized. Please select an engine.")
    return service

class FineTuneRequest(BaseModel):
    model_id: str
    dataset_path: str
    epochs: int = 3
    learning_rate: float = 1e-4
    batch_size: int = 1
    lora_rank: int = 8
    lora_alpha: float = 16.0
    max_seq_length: int = 512
    lora_dropout: float = 0.0
    lora_layers: int = 8
    job_name: str = "" # Optional user provided name

@router.post("/finetune")
async def start_finetune(request: FineTuneRequest):
    """
    Start a fine-tuning job.
    """
    service = get_service_or_raise()
    job_id = str(uuid.uuid4())
    print(f"DEBUG API: Received finetune request. Job Name: '{request.job_name}'")
    config = request.model_dump()
    print(f"DEBUG API: Config dump: {config}")
    result = await service.start_finetuning(job_id, config)
    return result

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status of a fine-tuning job.
    """
    service = get_service_or_raise()
    status = service.get_job_status(job_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@router.get("/models")
async def list_models():
    """
    List supported base models with their local download status.
    """
    service = get_service_or_raise()
    return service.get_models_status()

class DownloadRequest(BaseModel):
    model_id: str

@router.post("/models/download")
async def download_model(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Trigger a model download in the background.
    """
    service = get_service_or_raise()
    background_tasks.add_task(service.download_model, request.model_id)
    return {"status": "download_started", "model_id": request.model_id}

@router.post("/models/delete")
async def delete_model(request: DownloadRequest):
    """
    Delete a locally downloaded model.
    """
    service = get_service_or_raise()
    success = service.delete_model(request.model_id)
    if not success:
         raise HTTPException(status_code=404, detail="Model not found or could not be deleted")
    return {"status": "deleted", "model_id": request.model_id}

class RegisterRequest(BaseModel):
    name: str
    path: str
    url: str = ""

@router.post("/models/register")
async def register_model(request: RegisterRequest):
    """
    Register a custom model from a local path.
    """
    service = get_service_or_raise()
    try:
        new_model = service.register_model(request.name, request.path, request.url)
        return new_model
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    model_id: str
    messages: list
    temperature: float = 0.7

@router.post("/chat")
async def chat_generation(request: ChatRequest):
    """
    Generate a response from the model.
    """
    service = get_service_or_raise()
    response = await service.generate_response(request.model_id, request.messages)
    return response

# --- New Configuration Endpoints ---

class EngineSelectRequest(BaseModel):
    engine: str

@router.get("/status")
async def get_engine_status():
    """
    Returns current engine status and hardware capabilities.
    """
    config = EngineFactory.get_engine_config()
    caps = EngineFactory.get_hardware_capabilities()
    active_engine = "none"
    service = get_engine()
    if service:
        # Determine type by class name to avoid unsafe imports of backend libraries
        service_type = type(service).__name__
        if service_type == "MLXEngineService":
            active_engine = "mlx"
        elif service_type == "UnslothEngineService":
            active_engine = "unsloth"

    return {
        "engine": active_engine,
        "config_engine": config.get("engine", None),
        "hardware": caps
    }

@router.post("/select")
async def select_engine(request: EngineSelectRequest):
    """
    Selects the active engine.
    """
    if request.engine not in ["mlx", "unsloth"]:
        raise HTTPException(status_code=400, detail="Invalid engine selection. Must be 'mlx' or 'unsloth'.")

    # Check compatibility
    caps = EngineFactory.get_hardware_capabilities()
    if request.engine == "unsloth" and not caps["cuda"]:
        raise HTTPException(status_code=400, detail="CUDA not found. Cannot select Unsloth.")
    if request.engine == "mlx" and not caps["mlx"]:
        raise HTTPException(status_code=400, detail="MLX not found. Cannot select MLX.")

    EngineFactory.set_engine_config(request.engine)

    # Trigger factory re-init check
    new_service = get_engine()

    return {"status": "ok", "engine": request.engine}
