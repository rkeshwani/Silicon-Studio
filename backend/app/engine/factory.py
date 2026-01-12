import os
import sys
import subprocess
import json
import re
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
    def _detect_best_cuda_tag(cls):
        try:
            # Check nvidia-smi for driver version
            output = subprocess.check_output(["nvidia-smi"], encoding="utf-8")
            match = re.search(r"CUDA Version:\s+(\d+\.\d+)", output)
            if match:
                version = float(match.group(1))
                if version >= 12.1: return "cu121"
                if version >= 11.8: return "cu118"
        except Exception:
            pass
        return "cu121" # Default fallback

    @classmethod
    def get_hardware_capabilities(cls):
        capabilities = {
            "mlx": False,
            "cuda": False,
            "cuda_installable": False,
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
            else:
                print(f"DEBUG: Torch found but CUDA not available. Version: {torch.__version__}")
                if "cpu" in torch.__version__:
                    tag = cls._detect_best_cuda_tag()
                    print("HINT: CPU-only PyTorch detected. To fix, run:")
                    print(f"      pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/{tag}")
                    capabilities["cuda_installable"] = True
        except (ImportError, OSError) as e:
            print(f"DEBUG: Torch detection failed: {e}")

        if capabilities["mlx"]:
            capabilities["recommended"] = "mlx"
        elif capabilities["cuda"]:
            capabilities["recommended"] = "unsloth"

        return capabilities

    @classmethod
    def install_cuda_torch(cls):
        tag = cls._detect_best_cuda_tag()
        print(f"Engine Factory: CPU-only Torch detected. Starting automatic fix for {tag}...")
        try:
            print("1/3 Uninstalling CPU torch...")
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "torch", "torchvision", "torchaudio", "-y"])
            print(f"2/3 Installing CUDA torch ({tag})...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", f"https://download.pytorch.org/whl/{tag}"])
            print("3/3 Installation complete. Restarting backend...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"CRITICAL: Failed to install CUDA torch: {e}")

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
                if caps["cuda_installable"]:
                    cls.install_cuda_torch()
                    return None

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
            try:
                from app.engine.unsloth_service import UnslothEngineService
                cls._instance = UnslothEngineService()
                print("Engine Factory: Initialized Unsloth Engine")
            except Exception as e:
                print(f"CRITICAL: Failed to load Unsloth service: {e}")
                return None
        else:
            print(f"Engine Factory: Unknown engine {selected_engine}")
            return None

        return cls._instance

# Global helper
def get_engine():
    return EngineFactory.get_service()
