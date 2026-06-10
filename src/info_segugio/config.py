import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

class Config: 
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
    LLM_MODEL_LOW = os.getenv("LLM_MODEL_LOW", "gpt-4o-mini")
    AI_API_URL = os.getenv("AI_API_URL", "https://api.openai.com/v1")
    
    AI_API_KEY = os.getenv("OPENAI_API_KEY")  # Nota: l'SDK OpenAI cerca di default "OPENAI_API_KEY"
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")