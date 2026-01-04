from huggingface_hub import list_repo_files

models = [
    "mlx-community/Llama-3.2-3B-Instruct-4bit",
    "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
]

for model in models:
    try:
        print(f"Checking {model}...")
        files = list_repo_files(model)
        has_safetensors = any(f.endswith(".safetensors") for f in files)
        if has_safetensors:
            print(f"✅ {model} verified (safetensors found)")
        else:
            print(f"❌ {model} MISSING safetensors")
            print(files)
    except Exception as e:
        print(f"❌ {model} Failed to list files: {e}")
