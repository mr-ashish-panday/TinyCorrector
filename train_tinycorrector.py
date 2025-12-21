"""
TinyCorrector-500M: QLoRA Training Script
==========================================
Fine-tunes Qwen-2.5-0.5B-Instruct to correct hallucinations.
Compatible with trl==0.8.6

Requirements:
    pip install torch transformers peft accelerate bitsandbytes datasets trl==0.8.6

Usage:
    python train_tinycorrector.py --data_path correction_train.jsonl

Hardware: RTX 3080 (12GB) or better
Memory: ~6-8GB VRAM with QLoRA
Time: ~2-4 hours for 10k examples
"""

import argparse
import json
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

# ============== CONFIG ==============
# Uses local model folder (downloaded via wget)
MODEL_NAME = "./Qwen-0.5B"
OUTPUT_DIR = "./tinycorrector-0.5b"
MAX_SEQ_LENGTH = 512

# QLoRA config (optimized for 12GB VRAM)
LORA_R = 16          # Rank
LORA_ALPHA = 32      # Alpha
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

# Training config
BATCH_SIZE = 4
GRADIENT_ACCUMULATION = 4  # Effective batch = 16
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
WARMUP_RATIO = 0.03


def load_data(data_path: str) -> Dataset:
    """Load the correction dataset from JSONL."""
    examples = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            ex = json.loads(line)
            # Format for training
            text = format_training_example(ex)
            examples.append({"text": text})
    
    print(f"✅ Loaded {len(examples)} training examples")
    return Dataset.from_list(examples)


def format_training_example(ex: dict) -> str:
    """Format a single example for training."""
    # Use Qwen's chat format
    return f"""<|im_start|>system
You are a helpful assistant that corrects factual errors.<|im_end|>
<|im_start|>user
Question: {ex.get('query', '')}

Previous (incorrect) answer: {ex.get('hallucination', '')}

Please provide the corrected answer.<|im_end|>
<|im_start|>assistant
{ex.get('correction', '')}<|im_end|>"""


def setup_model_and_tokenizer():
    """Load model with 4-bit quantization for memory efficiency."""
    print("📥 Loading Qwen-2.5-0.5B-Instruct with 4-bit quantization...")
    
    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        # device_map removed to let Accelerate handle placement
        trust_remote_code=True,
    )
    
    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)
    
    # Setup LoRA
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model, tokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", type=str, default="correction_train.jsonl")
    parser.add_argument("--output_dir", type=str, default=OUTPUT_DIR)
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS)
    args = parser.parse_args()
    
    print("=" * 60)
    print("TinyCorrector-500M: QLoRA Training")
    print("=" * 60)
    
    # Check CUDA
    if not torch.cuda.is_available():
        print("❌ CUDA not available! This script requires a GPU.")
        print("   Transfer to your college GPU and run again.")
        return
    
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Load data
    dataset = load_data(args.data_path)
    
    # Setup model
    model, tokenizer = setup_model_and_tokenizer()
    
    # Training arguments (Standard Transformers TrainingArguments)
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        warmup_ratio=WARMUP_RATIO,
        logging_steps=10,
        save_steps=500,
        save_total_limit=2,
        fp16=True,
        optim="paged_adamw_8bit",
        report_to="none",  # Disable wandb
        gradient_checkpointing=True,
        max_grad_norm=0.3,
    )
    
    # Trainer (Standard TRL < 0.13.0 API)
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        tokenizer=tokenizer,
        args=training_args,
        packing=False,
    )
    
    print("\n🚀 Starting training...")
    print(f"   Epochs: {args.epochs}")
    print(f"   Batch size: {BATCH_SIZE} x {GRADIENT_ACCUMULATION} = {BATCH_SIZE * GRADIENT_ACCUMULATION}")
    print(f"   Learning rate: {LEARNING_RATE}")
    print(f"   Output: {args.output_dir}")
    
    # Train!
    trainer.train()
    
    # Save final model
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    print(f"\n✅ Training complete!")
    print(f"📁 Model saved to: {args.output_dir}")
    print("\nNext step: Run evaluation with evaluate_tinycorrector.py")


if __name__ == "__main__":
    main()
