import asyncio
import os
import threading
from typing import Dict, Any, List
from pathlib import Path
from mlx_lm import load, generate
from mlx_lm.tuner import train, TrainingArgs
from mlx_lm.utils import load_adapters

# Define a curated list of supported models for the UI
# Default curated list (MLX Community only, as requested)
DEFAULT_MODELS = [
    # --- TinyLlama ---
    {"id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "name": "TinyLlama 1.1B (Chat)", "size": "2.2GB", "family": "Llama"},
    
    # --- Llama 3.2 ---
    {"id": "mlx-community/Llama-3.2-1B-Instruct-4bit", "name": "Llama 3.2 1B Instruct (4-bit)", "size": "0.7GB", "family": "Llama"},
    {"id": "mlx-community/Llama-3.2-3B-Instruct-4bit", "name": "Llama 3.2 3B Instruct (4-bit)", "size": "1.9GB", "family": "Llama"},
    {"id": "mlx-community/Meta-Llama-3.1-70B-Instruct-4bit", "name": "Llama 3.1 70B Instruct (4-bit)", "size": "40GB", "family": "Llama"},

    # --- Qwen 2.5 ---
    {"id": "mlx-community/Qwen2.5-0.5B-Instruct-4bit", "name": "Qwen 2.5 0.5B Instruct (4-bit)", "size": "0.4GB", "family": "Qwen"},
    {"id": "mlx-community/Qwen2.5-1.5B-Instruct-4bit", "name": "Qwen 2.5 1.5B Instruct (4-bit)", "size": "1.0GB", "family": "Qwen"},
    {"id": "mlx-community/Qwen2.5-3B-Instruct-4bit", "name": "Qwen 2.5 3B Instruct (4-bit)", "size": "1.9GB", "family": "Qwen"},
    {"id": "mlx-community/Qwen2.5-7B-Instruct-4bit", "name": "Qwen 2.5 7B Instruct (4-bit)", "size": "4.5GB", "family": "Qwen"},
    {"id": "mlx-community/Qwen2.5-14B-Instruct-4bit", "name": "Qwen 2.5 14B Instruct (4-bit)", "size": "9.0GB", "family": "Qwen"},
    {"id": "mlx-community/Qwen2.5-32B-Instruct-4bit", "name": "Qwen 2.5 32B Instruct (4-bit)", "size": "19GB", "family": "Qwen"},
    {"id": "mlx-community/Qwen2.5-72B-Instruct-4bit", "name": "Qwen 2.5 72B Instruct (4-bit)", "size": "41GB", "family": "Qwen"},
    
    # --- Gemma 2 ---
    {"id": "mlx-community/gemma-2-2b-it-4bit", "name": "Gemma 2 2B Instruct (4-bit)", "size": "1.5GB", "family": "Gemma"},
    {"id": "mlx-community/gemma-2-9b-it-4bit", "name": "Gemma 2 9B Instruct (4-bit)", "size": "5.5GB", "family": "Gemma"},
    {"id": "mlx-community/gemma-2-27b-it-4bit", "name": "Gemma 2 27B Instruct (4-bit)", "size": "16GB", "family": "Gemma"},

    # --- Mistral / Mixtral ---
    {"id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit", "name": "Mistral 7B Instruct v0.3 (4-bit)", "size": "4.1GB", "family": "Mistral"},
    {"id": "mlx-community/Mixtral-8x7B-Instruct-v0.1-4bit", "name": "Mixtral 8x7B Instruct (4-bit)", "size": "24GB", "family": "Mistral"},
    {"id": "mlx-community/Mixtral-8x22B-Instruct-v0.1-4bit", "name": "Mixtral 8x22B Instruct (4-bit)", "size": "80GB", "family": "Mistral"},

    # --- DeepSeek ---
    {"id": "mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit", "name": "DeepSeek Coder V2 Lite (4-bit)", "size": "8.9GB", "family": "DeepSeek"},
    {"id": "mlx-community/DeepSeek-V3-4bit", "name": "DeepSeek V3 (4-bit)", "size": "300GB+", "family": "DeepSeek"}, 
]

class MLXEngineService:
    def __init__(self):
        self.active_jobs = {}
        self.active_downloads = set() # Track active downloads logic
        self.loaded_models = {}
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        self.adapters_dir = Path("adapters")
        self.adapters_dir.mkdir(exist_ok=True)
        self.models_config_path = Path("models.json")
        self.models_config = self._load_models_config()

    def _load_models_config(self):
        if self.models_config_path.exists():
            try:
                with open(self.models_config_path, "r") as f:
                    import json
                    return json.load(f)
            except Exception as e:
                print(f"Error loading models.json: {e}")
                return DEFAULT_MODELS
        else:
            return DEFAULT_MODELS

    def _save_models_config(self):
        with open(self.models_config_path, "w") as f:
            import json
            json.dump(self.models_config, f, indent=4)
            
    def get_supported_models(self):
        return self.models_config

    def register_model(self, name: str, path: str, url: str = ""):
        """
        Registers a custom model.
        Path should be the absolute path to the local model folder.
        """
        for m in self.models_config:
             if m['name'] == name:
                 raise ValueError(f"Model with name {name} already exists.")
        
        new_model = {
            "id": path, # Use absolute path as ID for local loading
            "name": name,
            "size": "Custom",
            "family": "Custom",
            "url": url,
            "external": False, 
            "is_custom": True
        }
        
        self.models_config.append(new_model)
        self._save_models_config()
        return new_model

    def list_models(self):
        # Kept for compatibility if used elsewhere, but internally we use models_config
        return self.models_config

    async def get_model_and_tokenizer(self, model_id: str):
        if model_id not in self.loaded_models:
            print(f"Loading model: {model_id}")
            
            path_to_load = model_id
            
            # 1. Is it an absolute path? (Custom Model)
            if Path(model_id).is_absolute() and Path(model_id).exists():
                 path_to_load = model_id
            else:
                # 2. Local standard cache
                sanitized_name = model_id.replace("/", "--")
                local_path = self.models_dir / sanitized_name
                # Only load if it's fully downloaded (marked completed)
                if (local_path / ".completed").exists():
                    path_to_load = str(local_path)
            
            print(f"Loading from: {path_to_load}")

            # This loads the model weights into memory. API calls might timeout if this takes too long.
            # ideally this should be async or backgrounded, but for MVP we wait.
            # Running in an executor to avoid blocking the event loop entirely
            loop = asyncio.get_running_loop()
            model, tokenizer = await loop.run_in_executor(None, load, path_to_load)
            self.loaded_models[model_id] = (model, tokenizer)
        return self.loaded_models[model_id]

    async def generate_response(self, model_id: str, messages: list):
        try:
            model, tokenizer = await self.get_model_and_tokenizer(model_id)
            
            # Simple prompt construction for MVP (chat template handling varies by model)
            # For simplicity, we just concatenate or use apply_chat_template if available.
            # Using tokenizer.apply_chat_template is preferred if supported.
            if hasattr(tokenizer, "apply_chat_template"):
                prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            else:
                 # Fallback for models without chat template config
                prompt = messages[-1]['content']

            # Run generation in executor
            loop = asyncio.get_running_loop()
            response_text = await loop.run_in_executor(
                None, 
                lambda: generate(model, tokenizer, prompt=prompt, max_tokens=200, verbose=True)
            )

            return {
                "role": "assistant",
                "content": response_text,
                "usage": {"total_tokens": len(response_text)} # Placeholder usage
            }
        except Exception as e:
            print(f"Generation error: {e}")
            return {"role": "assistant", "content": f"Error generating response: {str(e)}"}

    async def start_finetuning(self, job_id: str, config: Dict[str, Any]):
        job_name = config.get("job_name", "")
        self.active_jobs[job_id] = {
            "status": "starting", 
            "progress": 0, 
            "job_name": job_name,
            "job_id": job_id # Store ID as well for easy access
        }
        
        # Spawn a thread for training so we don't block the API
        thread = threading.Thread(target=self._run_training_job, args=(job_id, config))
        thread.start()
        
        return {"job_id": job_id, "status": "started", "job_name": job_name}

    def _run_training_job(self, job_id: str, config: Dict):
        """
        Executed in a separate thread.
        """
        try:
            self.active_jobs[job_id]["status"] = "training"
            model_id = config.get("model_id")
            dataset_path = config.get("dataset_path")
            epochs = int(config.get("epochs", 3))
            lr = float(config.get("learning_rate", 1e-4))
            
            # New Params
            batch_size = int(config.get("batch_size", 1))
            lora_rank = int(config.get("lora_rank", 8))
            lora_alpha = float(config.get("lora_alpha", 16))
            max_seq_length = int(config.get("max_seq_length", 512))
            lora_dropout = float(config.get("lora_dropout", 0.0))
            
            adapter_file = self.adapters_dir / f"{job_id}_adapters.safetensors"

            print(f"Starting training job {job_id} for model {model_id}...")
            print(f"Params: Epochs={epochs}, BS={batch_size}, Rank={lora_rank}, Alpha={lora_alpha}, LR={lr}, Dropout={lora_dropout}")

            # 1. Load Model (fresh load for training recommended to avoid state issues)
            # For efficiency we could reuse, but freezing/lora modification happens in-place.
            model, tokenizer, config = load(model_id, return_config=True)
            
            # Freeze the base model
            model.freeze()

            # 2. Setup Training Arguments
            from mlx_lm.tuner.datasets import load_local_dataset, CacheDataset
            
            # Use load_local_dataset
            data_dir = Path(os.path.dirname(dataset_path))
            
            # Note: load_local_dataset returns (train, val, test) tuple
            train_set, val_set, test_set = load_local_dataset(data_dir, tokenizer, config)
            
            # --- FIX FOR EMPTY VALIDATION SET ---
            # If user provides only train.jsonl, val_set is empty list. Train loop crashes.
            if len(val_set) == 0:
                print("Validation set empty. Splitting train set...")
                # Access raw data: load_local_dataset returns [ChatDataset(...), ...]
                # ChatDataset wraps a list in self._data
                if hasattr(train_set, "_data"):
                    raw_data = train_set._data
                else:
                    raw_data = train_set # Fallback if list
                
                # Split logic
                if len(raw_data) > 1:
                    split_idx = int(len(raw_data) * 0.9)
                    if split_idx == len(raw_data): split_idx = len(raw_data) - 1
                    
                    train_raw = raw_data[:split_idx]
                    val_raw = raw_data[split_idx:]
                    
                    # Re-create datasets
                    from mlx_lm.tuner.datasets import create_dataset
                    train_set = create_dataset(train_raw, tokenizer, config)
                    val_set = create_dataset(val_raw, tokenizer, config)
                else:
                    # Too small to split, duplicate
                    print("Train set too small (<=1). Duplicating for validation.")
                    # Note: Using same object might cause issues if modified? Safe to reuse for MVP
                    train_set = train_set
                    val_set = train_set 

            # IMPORTANT: ChatDataset returns raw dicts. Trainer expects processed tuples.
            # We must wrap them in CacheDataset which calls .process()
            train_set = CacheDataset(train_set)
            val_set = CacheDataset(val_set)
            
            # Calculate total iterations
            # Steps per epoch = len(train_set) / batch_size
            steps_per_epoch = len(train_set) // batch_size
            if steps_per_epoch < 1: steps_per_epoch = 1
            total_iters = steps_per_epoch * epochs
            
            print(f"Training Plan: {len(train_set)} samples, {steps_per_epoch} steps/epoch, {total_iters} total iters.")

            args = TrainingArgs(
                batch_size=batch_size, 
                iters=total_iters, 
                adapter_file=str(adapter_file),
                max_seq_length=max_seq_length
            )

            # Define a callback class to update progress
            class ProgressCallback:
                def on_train_loss_report(self_, train_info):
                    if "iteration" in train_info:
                        step = train_info["iteration"]
                        prog = int((step / args.iters) * 100)
                        self.active_jobs[job_id]["progress"] = prog

                def on_val_loss_report(self_, val_info):
                    # We can log validation loss if we want, or just ignore
                    pass

            progress_callback = ProgressCallback()

            # 3. Run Training
            # Note: mlx_lm.tuner.train signature: 
            # train(model, optimizer, train_dataset, val_dataset, args, training_callback=...)
            
            # We need to construction the optimizer
            import mlx.optimizers as optim
            optimizer = optim.Adam(learning_rate=lr)
            
            # We need to convert to LoRA
            from mlx_lm.tuner.utils import linear_to_lora_layers

            # Define LoRA config
            lora_config = {
                "rank": lora_rank,
                "alpha": lora_alpha,
                "scale": float(lora_alpha / lora_rank), # alpha / rank
                "dropout": lora_dropout,
                "keys": ["self_attn.q_proj", "self_attn.v_proj"] # Common keys for LoRA
            }
            
            # Note: num_layers=8 means adapt the last 8 layers
            # linear_to_lora_layers modifies model in-place and returns None!
            linear_to_lora_layers(model, 8, lora_config)
            
            # Print model to confirm
            print("Model converted to LoRA.")

            train(
                model=model,
                optimizer=optimizer,
                train_dataset=train_set,
                val_dataset=val_set,
                args=args,
                training_callback=progress_callback
            )

            self.active_jobs[job_id]["status"] = "completed"
            self.active_jobs[job_id]["model_path"] = str(adapter_file)
            self.active_jobs[job_id]["progress"] = 100
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Training failed: {e}")
            self.active_jobs[job_id]["status"] = "failed"
            self.active_jobs[job_id]["error"] = str(e)

    def get_job_status(self, job_id: str):
        return self.active_jobs.get(job_id, {"status": "not_found"})

    def get_models_status(self):
        """
        Returns the list of supported models with their local download status.
        Uses self.models_config which includes custom registered models.
        """
        models = []
        for m in self.models_config:
            # Check if model exists locally
            
            is_downloaded = False
            model_path = None
            is_downloading = m["id"] in self.active_downloads
            
            # 1. Custom Path?
            if Path(m["id"]).is_absolute():
                if Path(m["id"]).exists():
                    is_downloaded = True
                    model_path = str(Path(m["id"]))
            else:
                # 2. Standard Downloaded Model
                sanitized_name = m["id"].replace("/", "--")
                local_path = self.models_dir / sanitized_name
                # Only check for .completed file
                if (local_path / ".completed").exists():
                    is_downloaded = True
                    model_path = str(local_path)
            
            models.append({
                **m,
                "downloaded": is_downloaded,
                "downloading": is_downloading, 
                "local_path": model_path
            })
        return models

    def download_model(self, model_id: str):
        """
        Downloads a model to the local models directory.
        This is a blocking operation (run in Bg Task), handles markers.
        """
        if model_id in self.active_downloads:
            print(f"Model {model_id} already downloading.")
            return

        self.active_downloads.add(model_id)
        try:
            from huggingface_hub import snapshot_download
            
            print(f"Downloading {model_id} to {self.models_dir}...")
            sanitized_name = model_id.replace("/", "--")
            local_dir = self.models_dir / sanitized_name
            
            # Remove partial .completed if it exists (shouldn't, but safety)
            marker_file = local_dir / ".completed"
            if marker_file.exists():
                os.remove(marker_file)
            
            snapshot_download(
                repo_id=model_id,
                local_dir=local_dir,
                local_dir_use_symlinks=False,
                # Force allowing patterns if needed? Default is all.
            )
            
            # Write marker file
            with open(marker_file, 'w') as f:
                f.write("ok")
                
            print(f"Successfully downloaded {model_id}")
            return True
        except Exception as e:
            print(f"Failed to download {model_id}: {e}")
            raise e
        finally:
            self.active_downloads.discard(model_id)
            
    def delete_model(self, model_id: str):
        """
        Deletes a local model from disk.
        """
        try:
            sanitized_name = model_id.replace("/", "--")
            local_dir = self.models_dir / sanitized_name
            
            if local_dir.exists():
                print(f"Deleting model {model_id} at {local_dir}")
                import shutil
                shutil.rmtree(local_dir)
                return True
            else:
                print(f"Model {model_id} not found at {local_dir}")
                return False
        except Exception as e:
            print(f"Failed to delete {model_id}: {e}")
            raise e
