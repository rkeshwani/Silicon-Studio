import os
import json
from pathlib import Path
from typing import Optional
from app.engine.base import BaseEngineService

class EngineFactory:
    _instance: Optional[BaseEngineService] = None
    _config_path = Path("engine_config.json")

    @classmethod
    def get_engine_config(cls):
        if cls._config_path.exists():
            try:
                with open(cls._config_path, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @classmethod
    def set_engine_config(cls, engine: str):
        with open(cls._config_path, "w") as f:
            json.dump({"engine": engine}, f, indent=4)
        # Reset instance to force reload on next get
        cls._instance = None

    @classmethod
    def get_hardware_capabilities(cls):
        capabilities = {
            "mlx": False,
            "cuda": False,
            "recommended": None
        }

        try:
            import mlx.core
            capabilities["mlx"] = True
        except ImportError:
            pass

        try:
            import torch
            if torch.cuda.is_available():
                capabilities["cuda"] = True
        except ImportError:
            pass

        return capabilities

    @classmethod
    def get_service(cls) -> Optional[BaseEngineService]:
        if cls._instance:
            return cls._instance

        # 1. Load Config
        config = cls.get_engine_config()
        selected_engine = config.get("engine")

        caps = cls.get_hardware_capabilities()

        # 2. Validation & Fallback
        if selected_engine == "unsloth":
            if not caps["cuda"]:
                print("WARNING: Unsloth selected but CUDA not found.")
                if caps["mlx"]:
                    print("Fallback to MLX.")
                    selected_engine = "mlx"
                else:
                    print("CRITICAL: No compatible hardware found.")
                    return None

        elif selected_engine == "mlx":
            if not caps["mlx"]:
                print("WARNING: MLX selected but not found.")
                # Fallback?
                if caps["cuda"]:
                    selected_engine = "unsloth"
                else:
                    return None

        elif selected_engine is None:
            # Auto-detect defaults if no config
            if caps["mlx"]:
                selected_engine = "mlx"
            elif caps["cuda"]:
                selected_engine = "unsloth"
            else:
                return None

        # 3. Instantiate
        if selected_engine == "mlx":
            from app.engine.mlx_service import MLXEngineService
            cls._instance = MLXEngineService()
            print("Engine Factory: Initialized MLX Engine")

        elif selected_engine == "unsloth":
            from app.engine.unsloth_service import UnslothEngineService
            cls._instance = UnslothEngineService()
            print("Engine Factory: Initialized Unsloth Engine")
        else:
            print(f"Engine Factory: Unknown engine {selected_engine}")
            return None

        return cls._instance

# Global helper
def get_engine():
    return EngineFactory.get_service()
