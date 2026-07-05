from fastapi import APIRouter
import requests

from app.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "support-ticket-ai"
    }


@router.get("/ollama")
def ollama_health_check():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()

        models = response.json().get("models", [])
        model_names = [model.get("name") for model in models]

        return {
            "status": "ok",
            "ollama_url": OLLAMA_BASE_URL,
            "chat_model": OLLAMA_CHAT_MODEL,
            "embed_model": OLLAMA_EMBED_MODEL,
            "available_models": model_names
        }

    except requests.RequestException as error:
        return {
            "status": "error",
            "ollama_url": OLLAMA_BASE_URL,
            "message": str(error)
        }