"""
services/llm_client.py — Dual-Mode LLM Client Factory

Central LLM client that uses Ollama (offline/free) when no API key is set,
and Groq (online) when it is. All LLM calls in the backend must go through this file.
"""
from openai import OpenAI
import os
import logging
import requests
import json
import time

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

OLLAMA_MODELS_PRIORITY = [
    "mistral",
    "llama3.1:8b", 
    "llama3.2:3b",
    "llama3",
    "phi3",
]

GROQ_MODEL = "llama3-8b-8192"


def get_available_ollama_model() -> str | None:
    """Check which Ollama models are installed and return the best one"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            installed = [m["name"] for m in response.json().get("models", [])]
            for preferred in OLLAMA_MODELS_PRIORITY:
                for installed_name in installed:
                    if preferred in installed_name:
                        return installed_name
            # Return first available if none match priority list
            if installed:
                return installed[0]
    except Exception:
        pass
    return None


def get_llm_client() -> tuple:
    """Returns (client, model_name, provider) tuple.
    
    Priority:
    1. If GROQ_API_KEY is set AND FORCE_OLLAMA env var is not set → use Groq
    2. If Ollama is running locally → use Ollama  
    3. If ANTHROPIC_API_KEY is set → use Anthropic via openai-compatible shim
    4. Raise RuntimeError with helpful install instructions
    """
    force_ollama = os.getenv("FORCE_OLLAMA", "").lower() in ("1", "true", "yes")
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    
    # Try Groq first (unless forced to use Ollama)
    if groq_key and not force_ollama:
        logger.info("[LLM] Using Groq API")
        client = OpenAI(
            base_url=GROQ_BASE_URL,
            api_key=groq_key
        )
        return client, GROQ_MODEL, "groq"
    
    # Try Ollama
    ollama_model = get_available_ollama_model()
    if ollama_model:
        logger.info(f"[LLM] Using Ollama locally with model: {ollama_model}")
        client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama"
        )
        return client, ollama_model, "ollama"
    
    # Nothing available
    raise RuntimeError(
        "No LLM available. Either:\n"
        "  1. Set GROQ_API_KEY environment variable\n"
        "  2. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh\n"
        "     Then run: ollama pull mistral"
    )


def call_llm(
    prompt: str,
    system_prompt: str = "",
    expect_json: bool = True,
    temperature: float = 0.7,
    max_tokens: int = 800,
    retries: int = 2,  # Reduced retries for faster fallback
) -> dict | str:
    """Call the LLM with automatic retry on failure.
    
    If expect_json=True, retries up to 2 times if JSON parsing fails.
    Returns dict if expect_json=True, str otherwise.
    """
    client, model, provider = get_llm_client()
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    last_error = None
    
    for attempt in range(retries):
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Only add response_format for providers that support it
            # Ollama supports it for some models, Groq supports it
            if expect_json and provider in ("groq",):
                kwargs["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content.strip()
            
            if not expect_json:
                return content
            
            # Try to parse JSON — handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"[LLM] JSON parse failed attempt {attempt+1}: {e}")
            # Add explicit JSON reminder to prompt on retry
            if attempt < retries - 1:
                messages[-1]["content"] += "\n\nIMPORTANT: Reply with ONLY valid JSON, no markdown, no explanation."
            time.sleep(0.2 * (attempt + 1))  # Shorter sleep
            
        except Exception as e:
            last_error = e
            logger.error(f"[LLM] Call failed attempt {attempt+1}: {e}")
            if "rate" in str(e).lower():
                time.sleep(1 * (attempt + 1))  # Shorter sleep
            else:
                time.sleep(0.2)
    
    logger.error(f"[LLM] All {retries} attempts failed. Last error: {last_error}")
    if expect_json:
        return {}  # Return empty dict so callers don't crash
    return ""


def generate(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 800,
    timeout_seconds: int = 30  # NEW: Add timeout
) -> str:
    """
    Simple generate interface for LLM adaptive engine.
    Returns plain text response (not parsed as JSON).
    
    Includes timeout to prevent hanging on slow responses.
    """
    import signal
    
    class TimeoutError(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutError("LLM call timed out")
    
    # Set timeout (only works on Unix-like systems)
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
    except (AttributeError, ValueError):
        # Windows doesn't support SIGALRM, skip timeout
        pass
    
    try:
        result = call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            expect_json=False,  # Return raw text, let caller parse
            temperature=temperature,
            max_tokens=max_tokens,
            retries=1  # Reduced retries when using timeout
        )
        
        # Cancel alarm
        try:
            signal.alarm(0)
        except (AttributeError, ValueError):
            pass
        
        # call_llm returns str when expect_json=False
        return result if isinstance(result, str) else ""
        
    except TimeoutError:
        logger.error(f"[LLM] Call timed out after {timeout_seconds} seconds")
        return ""
    except Exception as e:
        logger.error(f"[LLM] Generate failed: {e}")
        return ""
    finally:
        # Ensure alarm is cancelled
        try:
            signal.alarm(0)
        except (AttributeError, ValueError):
            pass


def check_llm_health() -> dict:
    """Returns status of available LLM providers"""
    status = {
        "groq": False,
        "ollama": False,
        "ollama_model": None,
        "active_provider": None,
        "active_model": None
    }
    
    # Check Groq
    if os.getenv("GROQ_API_KEY"):
        status["groq"] = True
    
    # Check Ollama
    model = get_available_ollama_model()
    if model:
        status["ollama"] = True
        status["ollama_model"] = model
    
    # Determine active
    try:
        _, active_model, provider = get_llm_client()
        status["active_provider"] = provider
        status["active_model"] = active_model
    except RuntimeError:
        pass
    
    return status