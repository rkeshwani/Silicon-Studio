import psutil
import platform
import shutil
import subprocess
from app.engine.factory import EngineFactory

class SystemMonitor:
    @staticmethod
    def _get_nvidia_vram():
        try:
            kwargs = {}
            if platform.system() == "Windows":
                # CREATE_NO_WINDOW = 0x08000000 to prevent console popup
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

            # Query nvidia-smi for memory usage
            # Returns: total_mib, used_mib
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.total,memory.used", "--format=csv,noheader,nounits"],
                encoding="utf-8",
                **kwargs
            )
            # Take the first GPU found
            line = output.strip().split('\n')[0]
            total_mib, used_mib = map(float, line.split(','))
            
            total_bytes = int(total_mib * 1024 * 1024)
            used_bytes = int(used_mib * 1024 * 1024)
            percent = round((used_bytes / total_bytes) * 100) if total_bytes > 0 else 0
            
            return {
                "total": total_bytes,
                "used": used_bytes,
                "percent": percent
            }
        except Exception:
            return None

    @staticmethod
    def get_system_stats():
        # RAM Usage
        mem = psutil.virtual_memory()
        
        # Disk Usage (where the app runs)
        du = shutil.disk_usage(".")
        
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # GPU VRAM (NVIDIA)
        vram_stats = None
        if EngineFactory.get_engine_config().get("engine") == "unsloth":
            vram_stats = SystemMonitor._get_nvidia_vram()
        
        return {
            "memory": {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "percent": round((mem.used / mem.total) * 100)
            },
            "vram": vram_stats,
            "disk": {
                "total": du.total,
                "free": du.free,
                "used": du.used,
                "percent": (du.used / du.total) * 100
            },
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count(logical=True)
            },
            "platform": {
                "system": platform.system(),
                "processor": platform.processor(),
                "release": platform.release()
            }
        }
