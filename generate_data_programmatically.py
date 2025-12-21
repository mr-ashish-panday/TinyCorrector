"""
TinyCorrector-500M: Procedural Data Generator (Phase 3: Logic & Reasoning)
==========================================================================
Generates complex training data including:
1. Knowledge Hallucinations (Capitals, Authors)
2. Arithmetic Errors (wrong calculations)
3. Boolean Logic Errors (wrong truth tables)
4. Unit Conversion Errors (wrong physics)
Target: ~20,000 examples.
"""

import json
import random

OUTPUT_FILE = "correction_train_phase3.jsonl"
TARGET_COUNT = 20000

# ================= 1. KNOWLEDGE BASES (Static) =================
CAPITALS = {
    "France": "Paris", "Germany": "Berlin", "Italy": "Rome", "Spain": "Madrid", "United Kingdom": "London",
    "Japan": "Tokyo", "China": "Beijing", "India": "New Delhi", "Russia": "Moscow", "USA": "Washington, D.C.",
    "Canada": "Ottawa", "Brazil": "Brasília", "Australia": "Canberra", "Argentina": "Buenos Aires", "Egypt": "Cairo",
    "Nigeria": "Abuja", "South Africa": "Pretoria", "Kenya": "Nairobi", "Saudi Arabia": "Riyadh", "Turkey": "Ankara",
    "Thailand": "Bangkok", "Vietnam": "Hanoi", "Indonesia": "Jakarta", "South Korea": "Seoul", "Mexico": "Mexico City",
    "Peru": "Lima", "Chile": "Santiago", "Colombia": "Bogotá", "Sweden": "Stockholm", "Norway": "Oslo",
    "Finland": "Helsinki", "Denmark": "Copenhagen", "Poland": "Warsaw", "Ukraine": "Kyiv", "Greece": "Athens",
    "Portugal": "Lisbon", "Ireland": "Dublin", "Belgium": "Brussels", "Netherlands": "Amsterdam", "Switzerland": "Bern",
    "Austria": "Vienna", "Hungary": "Budapest", "Czech Republic": "Prague", "Romania": "Bucharest", "Israel": "Jerusalem",
    "Iran": "Tehran", "Iraq": "Baghdad", "Pakistan": "Islamabad", "Bangladesh": "Dhaka", "Philippines": "Manila"
}

AUTHORS = {
    "1984": "George Orwell", "To Kill a Mockingbird": "Harper Lee", "The Great Gatsby": "F. Scott Fitzgerald",
    "Pride and Prejudice": "Jane Austen", "Moby Dick": "Herman Melville", "War and Peace": "Leo Tolstoy",
    "Hamlet": "William Shakespeare", "The Catcher in the Rye": "J.D. Salinger", "The Hobbit": "J.R.R. Tolkien",
    "Harry Potter": "J.K. Rowling", "The Lord of the Rings": "J.R.R. Tolkien", "Jane Eyre": "Charlotte Brontë"
}

# ================= 2. PROCEDURAL GENERATORS (Dynamic) =================

def generate_arithmetic_data(n=5000):
    """Generates arithmetic errors: 5 * 5 = 24"""
    examples = []
    ops = ["+", "-", "*"]
    
    for _ in range(n):
        a = random.randint(2, 50)
        b = random.randint(2, 50)
        op = random.choice(ops)
        
        if op == "+":
            correct = a + b
            wrong = correct + random.choice([-1, 1, 10, -10])
            txt_op = "plus"
        elif op == "-":
            correct = a - b
            wrong = correct + random.choice([-1, 1, 2, -2])
            txt_op = "minus"
        else: # *
            correct = a * b
            wrong = correct + random.choice([-1, 1, a, -a]) # Off by one or off by one factor
            txt_op = "multiplied by"
            
        examples.append({
            "query": f"What is {a} {txt_op} {b}?",
            "hallucination": f"The answer is {wrong}.",
            "hallucination_type": "math_error",
            "correction": f"The answer is {correct}."
        })
    return examples

def generate_boolean_data(n=3000):
    """Generates logic errors: True AND False = True"""
    examples = []
    operators = ["AND", "OR"]
    
    for _ in range(n):
        op = random.choice(operators)
        val1 = random.choice([True, False])
        val2 = random.choice([True, False])
        
        if op == "AND":
            correct = val1 and val2
        else:
            correct = val1 or val2
            
        wrong = not correct
        
        examples.append({
             "query": f"What is the result of {val1} {op} {val2}?",
             "hallucination": f"The result is {wrong}.",
             "hallucination_type": "logic_error",
             "correction": f"The result is {correct}."
        })
    return examples

def generate_comparison_data(n=3000):
    """Generates comparison errors: 10 is greater than 50"""
    examples = []
    
    for _ in range(n):
        a = random.randint(1, 100)
        b = random.randint(1, 100)
        if a == b: continue
        
        correct_rel = "greater than" if a > b else "less than"
        wrong_rel = "less than" if a > b else "greater than"
        
        examples.append({
            "query": f"Compare {a} and {b}.",
            "hallucination": f"{a} is {wrong_rel} {b}.",
            "hallucination_type": "logic_error",
            "correction": f"{a} is {correct_rel} {b}."
        })
    return examples

def generate_unit_conversion(n=2000):
    """Convert km to m, etc."""
    examples = []
    conversions = [
        ("kilometers", "meters", 1000),
        ("meters", "centimeters", 100),
        ("kilograms", "grams", 1000),
        ("minutes", "seconds", 60),
        ("hours", "minutes", 60)
    ]
    
    for _ in range(n):
        unit_from, unit_to, factor = random.choice(conversions)
        val = random.randint(1, 20)
        correct = val * factor
        wrong = correct + random.choice([factor, factor//2, 10])
        
        examples.append({
            "query": f"How many {unit_to} are in {val} {unit_from}?",
            "hallucination": f"There are {wrong} {unit_to} in {val} {unit_from}.",
            "hallucination_type": "math_error",
            "correction": f"There are {correct} {unit_to} in {val} {unit_from}."
        })
    return examples

# ================= 3. STATIC GENERATORS (Legacy) =================
def generate_knowledge_data():
    examples = []
    # Capitals
    for c, cap in CAPITALS.items():
        wrong = random.choice([v for v in CAPITALS.values() if v != cap])
        examples.append({
            "query": f"What is the capital of {c}?",
            "hallucination": f"{wrong} is the capital of {c}.",
            "correction": f"{cap} is the capital of {c}."
        })
    # Authors
    for b, a in AUTHORS.items():
        wrong = random.choice([v for v in AUTHORS.values() if v != a])
        examples.append({
            "query": f"Who wrote {b}?",
            "hallucination": f"{wrong} wrote {b}.",
            "correction": f"{a} wrote {b}."
        })
    return examples

def main():
    print(f"🚀 Generating Phase 3 Dataset (Target: {TARGET_COUNT})...")
    
    all_examples = []
    
    # 1. Procedural Math & Logic (The "Heavy" Stuff) - ~13k total
    all_examples.extend(generate_arithmetic_data(5000))
    all_examples.extend(generate_boolean_data(3000))
    all_examples.extend(generate_comparison_data(3000))
    all_examples.extend(generate_unit_conversion(2000))
    
    # 2. Knowledge (Base Stuff) - ~7k (duplicated/augmented)
    knowledge = generate_knowledge_data()
    # Augment knowledge to fill the rest
    remaining = TARGET_COUNT - len(all_examples)
    multiplier = (remaining // len(knowledge)) + 1
    
    print(f"   Generated {len(all_examples)} logic examples.")
    print(f"   Augmenting {len(knowledge)} knowledge examples x {multiplier}...")
    
    for _ in range(multiplier):
        for k in knowledge:
            if len(all_examples) >= TARGET_COUNT: break
            all_examples.append(k)
            
    # Randomize
    random.shuffle(all_examples)
    final_dataset = all_examples[:TARGET_COUNT]
    
    # Write
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ex in final_dataset:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            
    print(f"✅ DONE! Saved {len(final_dataset)} examples to {OUTPUT_FILE}")
    print("   Includes: Math, Boolean Logic, Comparisons, Content Knowledge")

if __name__ == "__main__":
    main()
