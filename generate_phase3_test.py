"""
TinyCorrector-500M: Phase 3 Test Data Generator
===============================================
Generates a HELD-OUT test set of 500 Math/Logic/Reasoning examples.
These will be used to prove the model generalizes to new numbers.
"""

import json
import random

OUTPUT_FILE = "correction_test_phase3.jsonl"
TEST_COUNT = 500

def generate_arithmetic_test(n=200):
    examples = []
    # Use larger numbers to avoid overlap with training
    for _ in range(n):
        a = random.randint(51, 150)
        b = random.randint(2, 20)
        op = random.choice(["+", "-"]) # keep simple for test, or add *
        
        if op == "+":
            correct = a + b
            wrong = correct + random.choice([10, -10])
            txt_op = "plus"
        else:
            correct = a - b
            wrong = correct + random.choice([10, -10])
            txt_op = "minus"
            
        examples.append({
            "query": f"What is {a} {txt_op} {b}?",
            "hallucination": f"The answer is {wrong}.",
            "correction": f"The answer is {correct}."
        })
    return examples

def generate_logic_test(n=150):
    examples = []
    # Comparisons with different range
    for _ in range(n):
        a = random.randint(200, 500)
        b = random.randint(200, 500)
        if a == b: continue
        
        correct_rel = "greater than" if a > b else "less than"
        wrong_rel = "less than" if a > b else "greater than"
        
        examples.append({
            "query": f"Compare {a} and {b}.",
            "hallucination": f"{a} is {wrong_rel} {b}.",
            "correction": f"{a} is {correct_rel} {b}."
        })
    return examples

def generate_reasoning_test(n=150):
    # Unit conversions unseen in training? Or just different values.
    examples = []
    conversions = [("hours", "minutes", 60)]
    for _ in range(n):
        val = random.randint(10, 50) # training was 1-20
        correct = val * 60
        wrong = correct + 60
        examples.append({
            "query": f"How many minutes are in {val} hours?",
            "hallucination": f"There are {wrong} minutes in {val} hours.",
            "correction": f"There are {correct} minutes in {val} hours."
        })
    return examples

def main():
    print(f"🧪 Generating Phase 3 Test Set ({TEST_COUNT} examples)...")
    examples = []
    examples.extend(generate_arithmetic_test())
    examples.extend(generate_logic_test())
    examples.extend(generate_reasoning_test())
    
    random.shuffle(examples)
    examples = examples[:TEST_COUNT]
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            
    print(f"✅ Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
