import os

GROQ_API = os.getenv("GROQ_API_KEY")
GROQ_FALLBACK_API = os.getenv("GROQ_FALLBACK_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")


MODEL_20B = "openai/gpt-oss-120b"
MODEL_120B = "openai/gpt-oss-20b"

