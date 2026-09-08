import os
from pathlib import Path
from dotenv import load_dotenv

# Absolute base directory for StudyMate
BASE_DIR = Path("D:/StudyMate").resolve()

# Load .env file from D:\StudyMate\.env
load_dotenv(dotenv_path=BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
MAX_REVISIONS = int(os.getenv("MAX_REVISIONS", "2"))
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "studymate.db"


class ConfigurationError(RuntimeError):
    """Raised when critical configuration like GEMINI_API_KEY is missing."""
    pass


def check_gemini_key() -> str:
    """
    Validates that GEMINI_API_KEY is present and not a dummy placeholder.
    Fails clearly with a ConfigurationError if missing.
    """
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        raise ConfigurationError(
            "GEMINI_API_KEY is missing or invalid. "
            "Please configure a valid Gemini API key in D:\\StudyMate\\.env. "
            "Get a free key from Google AI Studio: https://aistudio.google.com/"
        )
    return key
