import asyncio
import os
import threading
from typing import Dict, Any, List
from pathlib import Path
import torch
from app.engine.base import BaseEngineService

# Unsloth specific imports
try:
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import load_dataset
except (ImportError, NotImplementedError, RuntimeError) as e:
    # Allow import for factory even if deps missing (will be checked by factory)
    # Unsloth raises NotImplementedError/RuntimeError if no GPU found on import
    print(f"Warning: Unsloth imports failed (likely no GPU): {e}")
    FastLanguageModel = None
    SFTTrainer = None
    TrainingArguments = None
    load_dataset = None

class UnslothEngineService(BaseEngineService):
    def __init__(self):
        self.active_jobs = {}
        self.active_downloads = set()
        self.loaded_models = {}

        # Dedicated directories for Unsloth to avoid conflict with MLX
        self.models_dir = Path("models/unsloth")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.adapters_dir = Path("adapters/unsloth")
        self.adapters_dir.mkdir(parents=True, exist_ok=True)

        # Re-use models.json logic but might need differentiation?
        # User said "Switch engines", so we can probably reuse the main models.json
        # but filter/flag compatibility.
        # For simplicity, we share the config file but might ignore incompatible ones or show them.

        # PROD FIX: Check multiple locations for models.json
        possible_paths = [
            Path("models.json"),
            Path("_internal/models.json"),
        ]
        import sys
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
             possible_paths.append(Path(sys._MEIPASS) / "models.json")

        self.models_config_path = Path("models.json")
        for p in possible_paths:
            if p.exists():
                self.models_config_path = p
                break

        self.models_config = self._load_models_config()

    def _load_models_config(self):
        if self.models_config_path.exists():
            try:
                with open(self.models_config_path, "r") as f:
                    import json
                    return json.load(f)
            except Exception as e:
                print(f"Error loading models.json: {e}")
                return []
        else:
            return []

    def _save_models_config(self):
        with open(self.models_config_path, "w") as f:
            import json
            json.dump(self.models_config, f, indent=4)

    def get_supported_models(self):
        return self.models_config

    def _get_dir_size_str(self, path: Path):
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)

            gb = total_size / (1024 * 1024 * 1024)
            if gb < 1:
                return f"{gb:.2f}GB"
            return f"{gb:.1f}GB"
        except Exception as e:
            return "Unknown"

    def register_model(self, name: str, path: str, url: str = ""):
        for m in self.models_config:
             if m['name'] == name:
                 raise ValueError(f"Model with name {name} already exists.")

        size_str = self._get_dir_size_str(Path(path))

        new_model = {
            "id": path,
            "name": name,
            "size": size_str,
            "family": "Custom",
            "url": url,
            "external": False,
            "is_custom": True,
            "engine": "unsloth" # Mark as registered via unsloth if needed
        }

        self.models_config.append(new_model)
        self._save_models_config()
        return new_model

    def list_models(self):
        return self.models_config

    async def get_model_and_tokenizer(self, model_id: str):
        if model_id not in self.loaded_models:
            print(f"Loading Unsloth model: {model_id}")

            # 1. Determine path
            path_to_load = model_id

            # Check if local download exists
            sanitized_name = model_id.replace("/", "--")
            local_path = self.models_dir / sanitized_name
            if (local_path / ".completed").exists():
                path_to_load = str(local_path)

            # 2. Load using FastLanguageModel
            # Note: Unsloth loads model + tokenizer
            # Run in executor to avoid blocking
            loop = asyncio.get_running_loop()

            def load_unsloth():
                model, tokenizer = FastLanguageModel.from_pretrained(
                    model_name=path_to_load,
                    max_seq_length=2048, # Default max seq length
                    dtype=None,
                    load_in_4bit=True, # Default to 4bit for efficiency as requested
                )
                FastLanguageModel.for_inference(model) # Optimize for inference
                return model, tokenizer

            model, tokenizer = await loop.run_in_executor(None, load_unsloth)
            self.loaded_models[model_id] = (model, tokenizer)

        return self.loaded_models[model_id]

    async def generate_response(self, model_id: str, messages: list):
        try:
            model, tokenizer = await self.get_model_and_tokenizer(model_id)

            # Convert messages to prompt
            # Unsloth usually relies on tokenizer chat template
            if hasattr(tokenizer, "apply_chat_template"):
                prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            else:
                prompt = messages[-1]['content']

            loop = asyncio.get_running_loop()

            def run_gen():
                inputs = tokenizer([prompt], return_tensors="pt").to("cuda")
                outputs = model.generate(**inputs, max_new_tokens=200, use_cache=True)
                # Decode only the new tokens
                response = tokenizer.batch_decode(outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
                return response

            response_text = await loop.run_in_executor(None, run_gen)

            return {
                "role": "assistant",
                "content": response_text,
                "usage": {"total_tokens": len(response_text)}
            }
        except Exception as e:
            print(f"Unsloth Generation error: {e}")
            return {"role": "assistant", "content": f"Error generating response: {str(e)}"}

    async def start_finetuning(self, job_id: str, config: Dict[str, Any]):
        job_name = config.get("job_name", "")
        self.active_jobs[job_id] = {
            "status": "starting",
            "progress": 0,
            "job_name": job_name,
            "job_id": job_id
        }

        thread = threading.Thread(target=self._run_training_job, args=(job_id, config))
        thread.start()

        return {"job_id": job_id, "status": "started", "job_name": job_name}

    def _run_training_job(self, job_id: str, config: Dict):
        try:
            if FastLanguageModel is None:
                raise RuntimeError("Unsloth library not available. Please install 'unsloth' and compatible CUDA drivers.")

            self.active_jobs[job_id]["status"] = "training"
            model_id = config.get("model_id")
            dataset_path = config.get("dataset_path")

            # Params
            epochs = int(config.get("epochs", 3))
            lr = float(config.get("learning_rate", 2e-4))
            batch_size = int(config.get("batch_size", 2)) # Unsloth handles batching well
            lora_rank = int(config.get("lora_rank", 16))
            lora_alpha = float(config.get("lora_alpha", 16))
            max_seq_length = int(config.get("max_seq_length", 2048))
            lora_dropout = float(config.get("lora_dropout", 0.0))

            # Unsloth supports 4bit loading
            load_in_4bit = True

            job_adapter_dir = self.adapters_dir / job_id
            job_adapter_dir.mkdir(parents=True, exist_ok=True)

            print(f"Starting Unsloth training job {job_id}...")

            # 1. Load Model
            model, tokenizer = FastLanguageModel.from_pretrained(
                model_name = model_id,
                max_seq_length = max_seq_length,
                dtype = None,
                load_in_4bit = load_in_4bit,
            )

            # 2. Add LoRA
            model = FastLanguageModel.get_peft_model(
                model,
                r = lora_rank,
                target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                                "gate_proj", "up_proj", "down_proj",],
                lora_alpha = lora_alpha,
                lora_dropout = lora_dropout,
                bias = "none",
                use_gradient_checkpointing = "unsloth",
                random_state = 3407,
                use_rslora = False,
                loftq_config = None,
            )

            # 3. Load Dataset
            # Unsloth uses standard HF datasets.
            # If dataset_path is local jsonl
            if dataset_path.endswith(".jsonl") or dataset_path.endswith(".json"):
                 dataset = load_dataset("json", data_files={"train": dataset_path}, split="train")
            else:
                 # Fallback/Assuming HF path?
                 dataset = load_dataset(dataset_path, split="train")

            # Standardize formatting (Simple assume 'text' field or convert chat format?)
            # For MVP, assume the dataset has a "text" column or is chat format.
            # Unsloth has standardization tools but simple is better here.

            # 4. Trainer
            trainer = SFTTrainer(
                model = model,
                tokenizer = tokenizer,
                train_dataset = dataset,
                dataset_text_field = "text", # Assumption for MVP
                max_seq_length = max_seq_length,
                dataset_num_proc = 2,
                packing = False, # Can set True for speed
                args = TrainingArguments(
                    per_device_train_batch_size = batch_size,
                    gradient_accumulation_steps = 4,
                    warmup_steps = 5,
                    max_steps = 60, # Demo default? Or calculate from epochs
                    num_train_epochs = epochs,
                    learning_rate = lr,
                    fp16 = not torch.cuda.is_bf16_supported(),
                    bf16 = torch.cuda.is_bf16_supported(),
                    logging_steps = 1,
                    optim = "adamw_8bit",
                    weight_decay = 0.01,
                    lr_scheduler_type = "linear",
                    seed = 3407,
                    output_dir = str(job_adapter_dir),
                ),
            )

            # Progress Callback Hook?
            # Transformers callback is complex to inject into SFTTrainer simply without class definition.
            # For MVP we might skip detailed progress bar updates or use a simple callback.

            trainer.train()

            # Save
            model.save_pretrained(str(job_adapter_dir))
            tokenizer.save_pretrained(str(job_adapter_dir))

            self.active_jobs[job_id]["status"] = "completed"
            self.active_jobs[job_id]["progress"] = 100

            # Save Metadata
            metadata = {
                "job_name": config.get("job_name", f"Unsloth-FT-{job_id[:8]}"),
                "job_id": job_id,
                "base_model": model_id,
                "engine": "unsloth",
                "params": config
            }
            with open(job_adapter_dir / "metadata.json", "w") as f:
                import json
                json.dump(metadata, f, indent=4)

            # Register
            ft_model_entry = {
                "id": f"ft-unsloth-{job_id}",
                "name": metadata["job_name"],
                "base_model": model_id,
                "adapter_path": str(job_adapter_dir),
                "size": "Adapter",
                "family": "Custom",
                "is_custom": True,
                "is_finetuned": True,
                "engine": "unsloth"
            }
            self.models_config.append(ft_model_entry)
            self._save_models_config()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Unsloth Training failed: {e}")
            self.active_jobs[job_id]["status"] = "failed"
            self.active_jobs[job_id]["error"] = str(e)

    def get_job_status(self, job_id: str):
        return self.active_jobs.get(job_id, {"status": "not_found"})

    def get_models_status(self):
        models = []
        for m in self.models_config:
            # Filter? Or show all and mark engine compatibility?
            # For now show all, check download status in unsloth dir

            is_downloaded = False
            model_path = None
            is_downloading = m["id"] in self.active_downloads

            if "is_finetuned" in m and m.get("engine") == "unsloth":
                 is_downloaded = True
            elif Path(m["id"]).is_absolute():
                 if Path(m["id"]).exists(): is_downloaded = True
            else:
                sanitized_name = m["id"].replace("/", "--")
                local_path = self.models_dir / sanitized_name
                if (local_path / ".completed").exists():
                    is_downloaded = True
                    model_path = str(local_path)

            # Add engine-specific flag if needed
            entry = {**m, "downloaded": is_downloaded, "downloading": is_downloading, "local_path": model_path}
            models.append(entry)
        return models

    def download_model(self, model_id: str):
        if model_id in self.active_downloads: return
        self.active_downloads.add(model_id)
        try:
            from huggingface_hub import snapshot_download
            print(f"Downloading {model_id} to {self.models_dir} (Unsloth)...")
            sanitized_name = model_id.replace("/", "--")
            local_dir = self.models_dir / sanitized_name

            marker_file = local_dir / ".completed"
            if marker_file.exists(): os.remove(marker_file)

            # Download generic HF model (usually safetensors)
            snapshot_download(repo_id=model_id, local_dir=local_dir, local_dir_use_symlinks=False)

            with open(marker_file, 'w') as f: f.write("ok")
            print(f"Successfully downloaded {model_id}")
            return True
        except Exception as e:
            print(f"Failed to download {model_id}: {e}")
            raise e
        finally:
            self.active_downloads.discard(model_id)

    def delete_model(self, model_id: str):
        # Implementation similar to MLX but targeting unsloth dirs
        # For brevity, standard deletion logic
        sanitized_name = model_id.replace("/", "--")
        local_dir = self.models_dir / sanitized_name
        if local_dir.exists():
            import shutil
            shutil.rmtree(local_dir)
            return True
        return False
