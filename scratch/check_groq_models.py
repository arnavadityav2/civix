import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

try:
    models = client.models.list()
    print("Available models:")
    for m in models.data:
        print(f" - {m.id}")
except Exception as e:
    print(f"Error fetching models: {e}")
