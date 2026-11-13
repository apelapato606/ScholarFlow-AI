"""Central Groq model configuration and LCEL invocation helpers."""
import os

DEFAULT_MODEL_ID = "openai/gpt-oss-120b"


def get_api_key():
    """Read the Groq key from environment or Streamlit secrets without logging it."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st
        return str(st.secrets.get("GROQ_API_KEY", "")).strip()
    except Exception:
        return ""


def get_model_name():
    """Resolve one configured model for every agent, defaulting to GPT-OSS 120B."""
    model = os.getenv("GROQ_MODEL", "").strip()
    if model:
        return model
    try:
        import streamlit as st
        return str(st.secrets.get("GROQ_MODEL", DEFAULT_MODEL_ID)).strip() or DEFAULT_MODEL_ID
    except Exception:
        return DEFAULT_MODEL_ID


def get_llm(temperature=0.2):
    """Build the shared LangChain ChatGroq client with supported Groq settings."""
    key = get_api_key()
    if not key:
        raise RuntimeError("Groq API key is missing. Add GROQ_API_KEY to .streamlit/secrets.toml or set it in the environment.")
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=key,
            model=get_model_name(),
            temperature=temperature,
            reasoning_format="hidden",
            reasoning_effort="medium",
            max_retries=2,
        )
    except ImportError as exc:
        raise RuntimeError("LangChain Groq integration is unavailable. Install the project dependencies with `pip install -r requirements.txt`.") from exc
    except Exception as exc:
        raise RuntimeError(format_groq_error(exc)) from exc


def format_groq_error(exc):
    """Convert common Groq failures into useful messages without exposing credentials."""
    status = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if status is None and response is not None:
        status = getattr(response, "status_code", None)
    text = str(exc).lower()
    name = type(exc).__name__.lower()

    if status in (401, 403) or "authentication" in name or "invalid_api_key" in text:
        return "Groq rejected the API key. Check that GROQ_API_KEY in .streamlit/secrets.toml is valid and active."
    if status == 404 or "model_not_found" in text or "model not found" in text:
        return "Groq could not find or access model '{}'. Confirm GROQ_MODEL is an active model available to your account.".format(get_model_name())
    if status == 429 or "ratelimit" in name or "rate limit" in text or "quota" in text:
        return "Groq rate limit reached. Wait briefly or review your account's model quota, then retry."
    if status is not None and status >= 500:
        return "Groq is temporarily unavailable (HTTP {}). Try again shortly.".format(status)
    if any(token in name for token in ("connection", "timeout")) or any(token in text for token in ("connection error", "timed out", "name resolution", "network is unreachable", "dns")):
        return "Could not reach Groq. Check your internet connection, proxy, and firewall, then retry."
    if status == 400:
        return "Groq rejected the request parameters or prompt (HTTP 400). Check the model configuration and retry."
    return "Groq request failed ({}). Check the model settings and network, then retry.".format(type(exc).__name__)


def invoke_lcel(prompt, values, temperature=0.2):
    """Run a LangChain Expression Language prompt/model chain and normalize API errors."""
    try:
        return (prompt | get_llm(temperature=temperature)).invoke(values).content
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError(format_groq_error(exc)) from exc


def test_groq_connection():
    """Make a real, minimal generation request using the currently configured model."""
    llm = get_llm(temperature=0.2)
    try:
        result = llm.invoke("Reply with exactly: ScholarFlow Groq connection OK")
        content = str(result.content).strip()
        if not content:
            raise RuntimeError("Groq returned an empty response. Check model availability and retry.")
        return content
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError(format_groq_error(exc)) from exc
