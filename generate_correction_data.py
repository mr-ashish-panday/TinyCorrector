"""
TinyCorrector-500M: Data Generation Script v2 (FIXED)
======================================================
Fixed version with proper retry logic for rate limits.

Usage:
    1. Set key: $env:GOOGLE_API_KEY = "your_key"
    2. Run: python generate_correction_data.py
"""

import os
import json
import random
import time
from tqdm import tqdm

# ============== CONFIG ==============
# ============== CONFIG ==============
OUTPUT_FILE = "correction_train.jsonl"
NUM_EXAMPLES = 2000  
BATCH_SIZE = 5       # Smaller batches satisfy rate limits better
MAX_RETRIES = 5
BASE_DELAY = 10      # Safe buffer for 15 RPM


# ============== DOMAINS ==============
DOMAINS = [
    "World History",
    "Science",
    "Geography", 
    "Pop Culture",
    "Sports",
    "Technology",
    "Mathematics",
    "Literature",
]

GENERATION_PROMPT = """Generate {batch_size} examples for training an AI to correct factual errors.
Domain: {domain}

For each example provide:
- query: A factual question
- hallucination: A plausible but WRONG answer (subtle error)
- hallucination_type: One of [entity_swap, number_error, false_attribution, fabrication, temporal_error]
- correction: The CORRECT answer

Output as JSON with key "examples". Example:
{{"examples": [{{"query": "Who painted the Mona Lisa?", "hallucination": "Michelangelo painted it.", "hallucination_type": "entity_swap", "correction": "Leonardo da Vinci painted it."}}]}}
"""

TRAINING_FORMAT = """<|im_start|>user
{query}<|im_end|>
<|im_start|>assistant
{hallucination}<|im_end|>
<|im_start|>user
That answer contains an error. Please correct it.<|im_end|>
<|im_start|>assistant
{correction}<|im_end|>"""


def setup_gemini():
    """Setup Google Gemini client."""
    try:
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("\n❌ GOOGLE_API_KEY not set!")
            print("Set it: $env:GOOGLE_API_KEY = 'your_key'")
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-lite-preview-02-05')
        return model
    except ImportError:
        print("❌ Run: pip install google-generativeai")
        return None


def generate_batch_with_retry(model, domain: str, batch_size: int = 5) -> list[dict]:
    """Generate with exponential backoff retry."""
    prompt = GENERATION_PROMPT.format(domain=domain, batch_size=batch_size)
    
    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.9,
                    "max_output_tokens": 2048,
                }
            )
            
            text = response.text.strip()
            # Remove markdown if present
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            
            data = json.loads(text)
            examples = data.get("examples", [])
            
            # Add metadata
            for ex in examples:
                ex["domain"] = domain
                ex["formatted_input"] = TRAINING_FORMAT.format(
                    query=ex.get("query", ""),
                    hallucination=ex.get("hallucination", ""),
                    correction=ex.get("correction", "")
                )
            
            return examples
        
        except json.JSONDecodeError:
            print(f"⚠️ JSON error, retrying...")
            time.sleep(2)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                # Rate limited - exponential backoff
                wait_time = BASE_DELAY * (2 ** attempt) + random.uniform(0, 5)
                print(f"⏳ Rate limited. Waiting {wait_time:.0f}s...")
                time.sleep(wait_time)
            else:
                print(f"⚠️ Error: {e}")
                time.sleep(5)
    
    return []


def main():
    print("=" * 60)
    print("TinyCorrector-500M: Data Generation v2 (Fixed)")
    print("=" * 60)
    
    model = setup_gemini()
    if not model:
        return
    
    print(f"✅ Connected to Gemini!")
    print(f"📊 Target: {NUM_EXAMPLES} batches × {BATCH_SIZE} = ~{NUM_EXAMPLES * BATCH_SIZE} examples")
    print(f"📁 Output: {OUTPUT_FILE}\n")
    
    all_examples = []
    save_interval = 1  # Save every batch so we see progress immediately
    
    pbar = tqdm(total=NUM_EXAMPLES, desc="Generating")
    batch_idx = 0
    
    while batch_idx < NUM_EXAMPLES:
        domain = DOMAINS[batch_idx % len(DOMAINS)]
        
        examples = generate_batch_with_retry(model, domain, BATCH_SIZE)
        
        if examples:
            all_examples.extend(examples)
            batch_idx += 1
            pbar.update(1)
            
            # Save periodically
            if len(all_examples) % (save_interval * BATCH_SIZE) == 0:
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    for ex in all_examples:
                        f.write(json.dumps(ex, ensure_ascii=False) + "\n")
                print(f"\n💾 Saved {len(all_examples)} examples")
        
        # Rate limit safety (Free tier = 15 RPM = 1 req / 4 sec)
        time.sleep(5)
    
    pbar.close()
    
    # Final save
    random.shuffle(all_examples)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ex in all_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    
    print(f"\n✅ Done! Generated {len(all_examples)} examples")
    print(f"📁 Saved to: {OUTPUT_FILE}")
    
    if all_examples:
        print("\n--- Sample ---")
        s = all_examples[0]
        print(f"Q: {s.get('query')}")
        print(f"Wrong: {s.get('hallucination')}")
        print(f"Right: {s.get('correction')}")


if __name__ == "__main__":
    main()
