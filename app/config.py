from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:7b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
try:
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    if OLLAMA_TIMEOUT <= 0:
        OLLAMA_TIMEOUT = 120
except ValueError:
    OLLAMA_TIMEOUT = 120

try:
    OLLAMA_MAX_RETRIES = int(os.getenv("OLLAMA_MAX_RETRIES", "3"))
    if OLLAMA_MAX_RETRIES <= 0:
        OLLAMA_MAX_RETRIES = 3
except ValueError:
    OLLAMA_MAX_RETRIES = 3

_data_dir_env = os.getenv("DATA_DIR", str(BASE_DIR / "app" / "data"))
DATA_DIR = Path(_data_dir_env)
if not DATA_DIR.is_absolute():
    DATA_DIR = BASE_DIR / DATA_DIR
DATA_DIR = DATA_DIR.resolve()

_db_path_env = os.getenv("DB_PATH", str(DATA_DIR / "tickets.db"))
DB_PATH = Path(_db_path_env)
if not DB_PATH.is_absolute():
    DB_PATH = BASE_DIR / DB_PATH
DB_PATH = DB_PATH.resolve()

_chroma_dir_env = os.getenv("CHROMA_DIR", str(DATA_DIR / "chroma"))
CHROMA_DIR = Path(_chroma_dir_env)
if not CHROMA_DIR.is_absolute():
    CHROMA_DIR = BASE_DIR / CHROMA_DIR
CHROMA_DIR = CHROMA_DIR.resolve()
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "support_tickets")

DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)