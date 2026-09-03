import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("FAIL: GEMINI_API_KEY not found in environment!")
    exit(1)

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents='Respond with a single word: SUCCESS.'
    )
    print(f"Connection OK. Gemini says: {response.text.strip()}")
except Exception as e:
    print(f"FAIL: {e}")
    exit(1)
