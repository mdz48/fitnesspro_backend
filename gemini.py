import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


try:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite", contents="Como datos necesito para diagnosticar la preclampsia en una mujer embarazada?"
    )
    print(response.text)
except Exception as e:
    print(f"Error loading Gemini API key: {e}")
    