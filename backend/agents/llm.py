import logging
from typing import Optional, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from ..config import check_gemini_key, GEMINI_MODEL

# Suppress harmless Google GenAI SDK AFC advisory warnings
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("google_genai.models").setLevel(logging.ERROR)
try:
    from google.genai.models import Models, AsyncModels
    Models._logged_afc_warning = True
    AsyncModels._logged_afc_warning = True
except Exception:
    pass

_TEST_LLM_OVERRIDE: Optional[Any] = None


def get_llm():
    """
    Returns the configured Gemini Chat model with automatic fallback.
    In normal runtime, validates that GEMINI_API_KEY is present and valid;
    otherwise raises ConfigurationError.
    In tests, _TEST_LLM_OVERRIDE can be injected.
    """
    global _TEST_LLM_OVERRIDE
    if _TEST_LLM_OVERRIDE is not None:
        return _TEST_LLM_OVERRIDE

    api_key = check_gemini_key()
    primary_model = GEMINI_MODEL or "gemini-3.1-flash-lite"
    fallback_model = "gemini-3.5-flash-lite" if "3.1" in primary_model else "gemini-3.1-flash-lite"

    try:
        primary = ChatGoogleGenerativeAI(
            model=primary_model,
            google_api_key=api_key,
            temperature=0.2,
            max_retries=2
        )
        fallback = ChatGoogleGenerativeAI(
            model=fallback_model,
            google_api_key=api_key,
            temperature=0.2,
            max_retries=2
        )
        return primary.with_fallbacks([fallback])
    except Exception:
        return ChatGoogleGenerativeAI(
            model=primary_model,
            google_api_key=api_key,
            temperature=0.2,
            max_retries=2
        )


def set_test_llm(mock_llm: Any) -> None:
    """Inject a test mock LLM to avoid external API calls during testing."""
    global _TEST_LLM_OVERRIDE
    _TEST_LLM_OVERRIDE = mock_llm


def reset_test_llm() -> None:
    """Reset any test mock LLM override."""
    global _TEST_LLM_OVERRIDE
    _TEST_LLM_OVERRIDE = None


def extract_text_content(content: Any) -> str:
    """
    Safely extract plain text from an AIMessage content.
    Handles both plain string content and list of chunks/dicts returned by modern Gemini models.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)

