import google.generativeai as genai
import os

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Fallback to the key user provided
    os.environ["GOOGLE_API_KEY"] = "AIzaSyD7pFj1CoeuQ8qOQ2u3poaCvfucIY5cq5A"
    genai.configure(api_key="AIzaSyD7pFj1CoeuQ8qOQ2u3poaCvfucIY5cq5A")
else:
    genai.configure(api_key=api_key)

try:
    print("Listing available models...")
    with open("models.txt", "w") as f:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"{m.name}\n")
                print(m.name)
except Exception as e:
    print(f"Error: {e}")
