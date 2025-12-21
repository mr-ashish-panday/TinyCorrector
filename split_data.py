"""
Split training data into train and test sets.
"""
import json
import random

INPUT_FILE = "correction_train.jsonl"
TRAIN_FILE = "correction_train_split.jsonl"
TEST_FILE = "correction_test.jsonl"
TEST_SIZE = 200  # Number of examples for test set

# Load all data
examples = []
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            examples.append(json.loads(line))

print(f"Total examples: {len(examples)}")

# Shuffle
random.seed(42)  # For reproducibility
random.shuffle(examples)

# Split
test_examples = examples[:TEST_SIZE]
train_examples = examples[TEST_SIZE:]

print(f"Train: {len(train_examples)}")
print(f"Test: {len(test_examples)}")

# Save
with open(TRAIN_FILE, "w", encoding="utf-8") as f:
    for ex in train_examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

with open(TEST_FILE, "w", encoding="utf-8") as f:
    for ex in test_examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

# Replace original with split
import shutil
shutil.move(TRAIN_FILE, INPUT_FILE)

print(f"✅ Created {TEST_FILE} with {len(test_examples)} examples")
print(f"✅ Updated {INPUT_FILE} with {len(train_examples)} examples")
