import os
from huggingface_hub import snapshot_download

# Force standard downloader (disable acceleration which causes CAS errors on weak nets)
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

print(f"======================================================")
print(f"⏳ Robust Downloader: {MODEL_NAME}")
print(f"======================================================")

try:
    # Attempt download with resume support
    path = snapshot_download(
        repo_id=MODEL_NAME,
        repo_type="model",
        # fast_download=False means we use the robust standard downloader
        resume_download=True,  
        ignore_patterns=["*.msgpack", "*.h5", "*.ot"], 
    )
    print(f"\n✅ SUCCESS! Model cached at:")
    print(f"{path}")
    print(f"\nNow you can run the training script again.")

except Exception as e:
    print(f"\n❌ FAILURE: {e}")
    print("\nTry running this script again. It will resume where it left off.")