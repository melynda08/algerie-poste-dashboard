## gemini.py
import os
import requests

# Load API key from environment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not set in environment variables.")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1/models/"
    "gemini-1.5-flash:generateContent?key={key}"
).format(key=GEMINI_API_KEY)

headers = {
    "Content-Type": "application/json"
}

def ask_gemini(question: str, user_id: str, conversation_id: str) -> str:
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"User ({user_id}) in conversation ({conversation_id}) asks: {question}"}
                ]
            }
        ]
    }
    response = requests.post(GEMINI_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    try:
        return data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError) as e:
        raise ValueError("Unexpected response format from Gemini API")
