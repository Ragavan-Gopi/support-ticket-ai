import logging
import time
from typing import Dict, Any, List, Optional
import requests

from app.config import (
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
    OLLAMA_EMBED_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_MAX_RETRIES
)

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Custom exception for Ollama/LLM related errors."""
    pass

def check_ollama_available() -> bool:
    """Checks if Ollama is running and accessible."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False

def generate_text(prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Calls the Ollama chat model to generate a text response.
    Returns the parsed JSON response dictionary.
    """
    if not prompt or not prompt.strip():
        logger.error("LLM_VAL_ERROR: Empty prompt provided to generate_text.")
        raise ValueError("Prompt cannot be empty.")

    payload = {
        "model": OLLAMA_CHAT_MODEL,
        "prompt": prompt,
        "stream": False
    }
    if system_prompt:
        payload["system"] = system_prompt

    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    for attempt in range(1, OLLAMA_MAX_RETRIES + 1):
        try:
            logger.info(f"LLM_GENERATE: Generating text with {OLLAMA_CHAT_MODEL} (Attempt {attempt}/{OLLAMA_MAX_RETRIES})")
            start_time = time.time()
            
            response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if "response" not in data:
                raise LLMError("LLM_FORMAT_ERROR: Missing 'response' field in Ollama output.")
                
            elapsed = time.time() - start_time
            logger.info(f"LLM_SUCCESS: Generation completed in {elapsed:.2f}s")
            return data
            
        except requests.RequestException as e:
            logger.warning(f"LLM_REQ_ERROR: Attempt {attempt} failed. Details: {e}")
            if attempt == OLLAMA_MAX_RETRIES:
                logger.error(f"LLM_FAIL: Generation failed after {OLLAMA_MAX_RETRIES} attempts.")
                raise LLMError(f"Ollama generation failed: {str(e)}")
            time.sleep(1) # simple backoff

    raise LLMError("Unexpected error during text generation.")

def generate_embedding(text: str) -> List[float]:
    """
    Calls the Ollama embedding model to generate embeddings for a given text.
    Returns the embedding list of floats.
    """
    if not text or not text.strip():
        logger.error("LLM_VAL_ERROR: Empty text provided to generate_embedding.")
        raise ValueError("Text to embed cannot be empty.")

    payload = {
        "model": OLLAMA_EMBED_MODEL,
        "prompt": text
    }
    
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    
    for attempt in range(1, OLLAMA_MAX_RETRIES + 1):
        try:
            logger.info(f"LLM_EMBED: Generating embedding with {OLLAMA_EMBED_MODEL} (Attempt {attempt}/{OLLAMA_MAX_RETRIES})")
            start_time = time.time()
            
            response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if "embedding" not in data:
                raise LLMError("LLM_FORMAT_ERROR: Missing 'embedding' field in Ollama output.")
                
            elapsed = time.time() - start_time
            logger.info(f"LLM_SUCCESS: Embedding completed in {elapsed:.2f}s")
            return data["embedding"]
            
        except requests.RequestException as e:
            logger.warning(f"LLM_REQ_ERROR: Attempt {attempt} failed. Details: {e}")
            if attempt == OLLAMA_MAX_RETRIES:
                logger.error(f"LLM_FAIL: Embedding generation failed after {OLLAMA_MAX_RETRIES} attempts.")
                raise LLMError(f"Ollama embedding failed: {str(e)}")
            time.sleep(1)

    raise LLMError("Unexpected error during embedding generation.")
