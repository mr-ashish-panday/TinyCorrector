"""
TinyCorrector-500M: Evaluation Script
======================================
Tests how well the model corrects hallucinations.

Usage:
    python evaluate_tinycorrector.py --model_path ./tinycorrector-0.5b --test_data correction_test.jsonl
"""

import argparse
import json
import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# ============== CONFIG ==============
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
MAX_NEW_TOKENS = 256


def load_model(model_path: str, use_base: bool = False):
    """Load the fine-tuned model or base model."""
    print(f"📥 Loading model from {model_path if not use_base else BASE_MODEL}...")
    
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    
    if use_base:
        # Load base model for comparison
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
    else:
        # Load fine-tuned model
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        model = PeftModel.from_pretrained(base_model, model_path)
        model = model.merge_and_unload()  # Merge LoRA weights
    
    return model, tokenizer


def format_prompt(query: str, hallucination: str) -> str:
    """Format input for the model."""
    return f"""<|im_start|>system
You are a helpful assistant that corrects factual errors.<|im_end|>
<|im_start|>user
Question: {query}

Previous (incorrect) answer: {hallucination}

Please provide the corrected answer.<|im_end|>
<|im_start|>assistant
"""


def generate_correction(model, tokenizer, query: str, hallucination: str) -> str:
    """Generate a correction for the given hallucination."""
    prompt = format_prompt(query, hallucination)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract just the assistant's response
    if "<|im_start|>assistant" in response:
        response = response.split("<|im_start|>assistant")[-1].strip()
    
    return response


def evaluate_correction(prediction: str, ground_truth: str) -> dict:
    """Evaluate if the correction is successful."""
    pred_lower = prediction.lower().strip()
    truth_lower = ground_truth.lower().strip()
    
    # Exact match
    exact_match = pred_lower == truth_lower
    
    # Contains key info (relaxed metric)
    # Check if key words from ground truth appear in prediction
    truth_words = set(truth_lower.split())
    pred_words = set(pred_lower.split())
    overlap = len(truth_words & pred_words) / max(len(truth_words), 1)
    
    return {
        "exact_match": exact_match,
        "word_overlap": overlap,
        "contains_correction": overlap > 0.5,  # At least 50% word overlap
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default="./tinycorrector-0.5b")
    parser.add_argument("--test_data", type=str, default="correction_test.jsonl")
    parser.add_argument("--use_base", action="store_true", help="Use base model instead of fine-tuned")
    parser.add_argument("--num_samples", type=int, default=100, help="Number of samples to evaluate")
    args = parser.parse_args()
    
    print("=" * 60)
    print("TinyCorrector-500M: Evaluation")
    print("=" * 60)
    
    # Load model
    model, tokenizer = load_model(args.model_path, args.use_base)
    
    # Load test data
    test_examples = []
    with open(args.test_data, "r", encoding="utf-8") as f:
        for line in f:
            test_examples.append(json.loads(line))
    
    if args.num_samples < len(test_examples):
        test_examples = test_examples[:args.num_samples]
    
    print(f"📊 Evaluating on {len(test_examples)} examples...")
    
    # Evaluate
    results = {
        "exact_match": 0,
        "contains_correction": 0,
        "word_overlap_sum": 0,
    }
    
    predictions = []
    
    for ex in tqdm(test_examples, desc="Evaluating"):
        query = ex.get("query", "")
        hallucination = ex.get("hallucination", "")
        ground_truth = ex.get("correction", "")
        
        prediction = generate_correction(model, tokenizer, query, hallucination)
        
        eval_result = evaluate_correction(prediction, ground_truth)
        
        results["exact_match"] += int(eval_result["exact_match"])
        results["contains_correction"] += int(eval_result["contains_correction"])
        results["word_overlap_sum"] += eval_result["word_overlap"]
        
        predictions.append({
            "query": query,
            "hallucination": hallucination,
            "ground_truth": ground_truth,
            "prediction": prediction,
            **eval_result,
        })
    
    # Calculate metrics
    n = len(test_examples)
    metrics = {
        "Exact Match Rate": results["exact_match"] / n * 100,
        "Correction Success Rate": results["contains_correction"] / n * 100,
        "Avg Word Overlap": results["word_overlap_sum"] / n * 100,
    }
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for metric, value in metrics.items():
        print(f"{metric}: {value:.2f}%")
    
    # Save predictions
    output_file = "evaluation_results.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for pred in predictions:
            f.write(json.dumps(pred, ensure_ascii=False) + "\n")
    
    print(f"\n📁 Detailed results saved to: {output_file}")
    
    # Show some examples
    print("\n" + "=" * 60)
    print("SAMPLE PREDICTIONS")
    print("=" * 60)
    for i, pred in enumerate(predictions[:3]):
        print(f"\n--- Example {i+1} ---")
        print(f"Query: {pred['query']}")
        print(f"Hallucination: {pred['hallucination']}")
        print(f"Ground Truth: {pred['ground_truth']}")
        print(f"Prediction: {pred['prediction']}")
        print(f"Correct: {'✅' if pred['contains_correction'] else '❌'}")


if __name__ == "__main__":
    main()
