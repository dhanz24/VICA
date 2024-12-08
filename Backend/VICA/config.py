import os
import sys
from dotenv import load_dotenv
####################################
# OLLAMA_BASE_URL
####################################
OLLAMA_BASE_URLS = os.environ.get("OLLAMA_BASE_URLS", "http://localhost:11434").split(
    ";"
)
OLLAMA_API_BASE_URL = os.environ.get(
    "OLLAMA_API_BASE_URL", "http://localhost:11434/api"
)

# For production, you should only need one host as
# fastapi serves the svelte-kit built frontend and backend from the same host and port.
# To test CORS_ALLOW_ORIGIN locally, you can set something like
# CORS_ALLOW_ORIGIN=http://localhost:5173;http://localhost:8080
# in your .env file depending on your frontend port, 5173 in this case.
#CORS_ALLOW_ORIGIN = os.environ.get("CORS_ALLOW_ORIGIN", "*").split(";")

CORS_ALLOW_ORIGIN = ["http://localhost:5173", "http://localhost:8080"]


load_dotenv(".env")

LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY_2")
JINA_API_KEY = os.getenv("JINA_API_KEY")
