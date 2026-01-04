from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from app.api.monitor import router as monitor_router
from app.api.studio import router as studio_router
from app.api.engine import router as engine_router
from app.api.shield import router as shield_router

app = FastAPI(
    title="Perimeter.ai Backend",
    description="Local-first LLM fine-tuning engine",
    version="0.1.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "app://."],  # Vite default + Electron
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitor_router, prefix="/api/monitor", tags=["monitor"])
app.include_router(studio_router, prefix="/api/studio", tags=["studio"])
app.include_router(engine_router, prefix="/api/engine", tags=["engine"])
app.include_router(shield_router, prefix="/api/shield", tags=["shield"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "perimeter-engine"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
