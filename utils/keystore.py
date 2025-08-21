import json
import os
import uuid
import warnings
from typing import Optional, List

# Load environment variables from a local .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; ignore if unavailable
    pass

def get_from_env(key: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(key)
    return value if value is not None and value != "" else default


def get_any_from_env(keys: List[str], default: Optional[str] = None) -> Optional[str]:
    """Get the first non-empty value among several env var names."""
    for candidate in keys:
        value = os.getenv(candidate)
        if value:
            return value
    return default

def auth_litellm():
    """Populate provider API keys from env/.env.

    Behavior:
    - Prefer existing provider-specific keys if set
    - If a LiteLLM proxy key is provided (via LITE_LLM_API_KEY), use it to fill missing provider keys
    - Do not overwrite already-set env vars
    """

    def set_if_unset(name: str, value: Optional[str]):
        if value and not os.getenv(name):
            os.environ[name] = value

    # Accept both standard and legacy names for the proxy key
    litellm_key = get_any_from_env([
        "LITE_LLM_API_KEY",
    ])

    api_base = get_any_from_env([
        "LITE_LLM_API_BASE",
    ])

    # Ensure the proxy key itself is exported if present
    set_if_unset("LITE_LLM_API_KEY", litellm_key)

    # Fill common providers if not already present
    set_if_unset("OPENAI_API_KEY", get_any_from_env(["OPENAI_API_KEY", "LITE_LLM_API_KEY"]))
    set_if_unset("ANTHROPIC_API_KEY", get_any_from_env(["ANTHROPIC_API_KEY", "LITE_LLM_API_KEY"]))
    set_if_unset("LLAMA_API_KEY", get_any_from_env(["LLAMA_API_KEY", "LITE_LLM_API_KEY"]))
    set_if_unset("GEMINI_API_KEY", get_any_from_env(["GEMINI_API_KEY"]))

    return litellm_key, api_base

def auth_tools():
    """Populate tool-specific API keys from env/.env.

    Supports both standard and legacy variable names. Existing env vars are not
    overwritten.
    """

    def set_if_unset(name: str, value: Optional[str]):
        if value and not os.getenv(name):
            os.environ[name] = value

    set_if_unset('SEARCHAPI_API_KEY', get_any_from_env([
        'SEARCHAPI_API_KEY', 'RESEARCH_SEARCHAPI_API_KEY'
    ]))
    set_if_unset('ALPHA_VANTAGE_API_KEY', get_any_from_env([
        'ALPHA_VANTAGE_API_KEY', 'RESEARCH_ALPHA_VANTAGE_API_KEY'
    ]))
    set_if_unset('OPENWEATHER_API_KEY', get_any_from_env([
        'OPENWEATHER_API_KEY', 'RESEARCH_OPENWEATHER_API_KEY'
    ]))
    set_if_unset('WOLFRAM_ALPHA_API_KEY', get_any_from_env([
        'WOLFRAM_ALPHA_API_KEY', 'RESEARCH_WOLFRAM_ALPHA_API_KEY'
    ]))
