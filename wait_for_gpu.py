import time
import subprocess
import os

GPU_ID = 0
MEMORY_THRESHOLD_MB = 2000  # If usage < 2GB, assume free
POLL_INTERVAL = 30  # Check every 30 seconds

def get_gpu_memory_usage():
    """Returns the memory usage of the GPU in MB."""
    try:
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader", f"--id={GPU_ID}"],
            encoding="utf-8"
        )
        return int(result.strip())
    except Exception as e:
        print(f"⚠️ Error checking GPU: {e}")
        return 99999  # Assume full if error

def run_training():
    """Launches the training script."""
    print("\n🚀 GPU is FREE! Launching training...")
    cmd = "nohup python train_tinycorrector.py --data_path correction_train.jsonl > training.log 2>&1 &"
    os.system(cmd)
    print(f"✅ Training started! Check logs with: tail -f training.log")

def main():
    print(f"🛡️ Guard Mode Active")
    print(f"👀 Watching GPU {GPU_ID} for Basanta to finish...")
    print(f"   (Waiting for memory usage to drop below {MEMORY_THRESHOLD_MB} MB)")

    # Run loop
    while True:
        mem_used = get_gpu_memory_usage()
        timestamp = time.strftime("%H:%M:%S")
        
        if mem_used < MEMORY_THRESHOLD_MB:
            print(f"[{timestamp}] Memory: {mem_used} MB -> Free!")
            run_training()
            break
        else:
            print(f"[{timestamp}] Memory: {mem_used} MB -> Busy... checking in {POLL_INTERVAL}s")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
