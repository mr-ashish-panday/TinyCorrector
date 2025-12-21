import os
import subprocess

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
LOCAL_DIR = "Qwen-0.5B"
FILES = [
    "config.json",
    "generation_config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt"
]

def download_file(filename):
    url = f"https://huggingface.co/{MODEL_ID}/resolve/main/{filename}"
    output_path = os.path.join(LOCAL_DIR, filename)
    
    print(f"\n⬇️ Downloading {filename}...")
    # wget -c continues download if broken
    # -P specifies directory
    # -q --show-progress makes it look nice
    cmd = ["wget", "-c", url, "-O", output_path] 
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ {filename} saved.")
    except subprocess.CalledProcessError:
        print(f"⚠️ Failed to download {filename}. It might not exist (e.g. merges.txt for some models). This is usually fine.")

if __name__ == "__main__":
    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)
        
    print(f"🚀 Starting robust download via WGET for {MODEL_ID}")
    print(f"📂 Saving to: {LOCAL_DIR}")
    
    for f in FILES:
        download_file(f)
        
    print("\n✅ Download complete (or attempted)!")
    print("\nIMPORTANT: Update your training script to use the local folder:")
    print(f'MODEL_NAME = "./{LOCAL_DIR}"')
