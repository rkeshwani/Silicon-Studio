from app.engine.factory import get_engine

# Proxy class for backward compatibility if imported elsewhere
class MLXEngineService:
    def __init__(self):
        # Delegate everything to the factory service
        pass

    def __getattr__(self, name):
        service = get_engine()
        if service:
            return getattr(service, name)
        raise AttributeError(f"Engine service not initialized. Attribute {name} not found.")

# Define a curated list of supported models for the UI
# Default curated list (MLX Community only, as requested)
DEFAULT_MODELS = []

# Deprecated: Logic moved to mlx_service.py and unsloth_service.py
# This file is now just a placeholder or could be removed if we cleaned up all imports.
# For safety, we leave it as a stub or remove the old class implementation.
