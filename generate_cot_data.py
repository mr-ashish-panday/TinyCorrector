"""
TinyCorrector-500M: Chain-of-Thought Data Generator
====================================================
Generates corrections WITH reasoning steps.
Example:
  Query: What is 47 * 3?
  Hallucination: The answer is 140.
  Correction: Let me think step by step. 47 * 3 = (40 * 3) + (7 * 3) = 120 + 21 = 141. The answer is 141.
"""

import json
import random

OUTPUT_FILE = "correction_train_cot.jsonl"
TARGET_COUNT = 10000  # Smaller for ablation

def generate_arithmetic_cot(n=4000):
    """Arithmetic with step-by-step reasoning."""
    examples = []
    
    for _ in range(n):
        a = random.randint(10, 99)
        b = random.randint(2, 12)
        op = random.choice(["+", "-", "*"])
        
        if op == "+":
            correct = a + b
            wrong = correct + random.choice([-1, 1, 10])
            reasoning = f"Let me calculate: {a} + {b} = {correct}."
            txt_op = "plus"
        elif op == "-":
            correct = a - b
            wrong = correct + random.choice([-1, 1, 2])
            reasoning = f"Let me calculate: {a} - {b} = {correct}."
            txt_op = "minus"
        else:
            correct = a * b
            wrong = correct + random.choice([-1, 1, a])
            # Break down multiplication for CoT
            tens = (a // 10) * 10
            ones = a % 10
            reasoning = f"Let me break it down: {a} × {b} = ({tens} × {b}) + ({ones} × {b}) = {tens*b} + {ones*b} = {correct}."
            txt_op = "multiplied by"
            
        examples.append({
            "query": f"What is {a} {txt_op} {b}?",
            "hallucination": f"The answer is {wrong}.",
            "hallucination_type": "math_error",
            "correction": f"{reasoning} The answer is {correct}."
        })
    return examples

def generate_comparison_cot(n=3000):
    """Comparisons with reasoning."""
    examples = []
    
    for _ in range(n):
        a = random.randint(100, 500)
        b = random.randint(100, 500)
        if a == b: continue
        
        correct_rel = "greater than" if a > b else "less than"
        wrong_rel = "less than" if a > b else "greater than"
        
        if a > b:
            reasoning = f"Comparing the two numbers: {a} is larger because {a} > {b}."
        else:
            reasoning = f"Comparing the two numbers: {a} is smaller because {a} < {b}."
        
        examples.append({
            "query": f"Compare {a} and {b}.",
            "hallucination": f"{a} is {wrong_rel} {b}.",
            "hallucination_type": "logic_error",
            "correction": f"{reasoning} So {a} is {correct_rel} {b}."
        })
    return examples

def generate_conversion_cot(n=3000):
    """Unit conversions with reasoning."""
    examples = []
    conversions = [
        ("hours", "minutes", 60, "multiply by 60"),
        ("minutes", "seconds", 60, "multiply by 60"),
        ("kilometers", "meters", 1000, "multiply by 1000"),
    ]
    
    for _ in range(n):
        unit_from, unit_to, factor, method = random.choice(conversions)
        val = random.randint(5, 50)
        correct = val * factor
        wrong = correct + factor
        
        reasoning = f"To convert {unit_from} to {unit_to}, {method}. So {val} × {factor} = {correct}."
        
        examples.append({
            "query": f"How many {unit_to} are in {val} {unit_from}?",
            "hallucination": f"There are {wrong} {unit_to} in {val} {unit_from}.",
            "hallucination_type": "math_error",
            "correction": f"{reasoning} There are {correct} {unit_to} in {val} {unit_from}."
        })
    return examples

def main():
    print(f"🧠 Generating Chain-of-Thought Dataset (Target: {TARGET_COUNT})...")
    
    all_examples = []
    all_examples.extend(generate_arithmetic_cot())
    all_examples.extend(generate_comparison_cot())
    all_examples.extend(generate_conversion_cot())
    
    random.shuffle(all_examples)
    final = all_examples[:TARGET_COUNT]
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ex in final:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            
    print(f"✅ Saved {len(final)} CoT examples to {OUTPUT_FILE}")
    print("   Each correction includes step-by-step reasoning!")

if __name__ == "__main__":
    main()
