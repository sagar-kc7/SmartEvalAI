"""Thin wrapper around the Google Gemini API for evaluation and feedback."""

import json

from google import genai
from loguru import logger

from smartevalai.core.config import get_settings

_client: genai.Client | None = None

# A fast, cost-effective model well-suited to structured evaluation tasks.
_MODEL_NAME = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    """Lazily construct the Gemini client using the configured API key."""
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def generate_json(prompt: str, retries: int = 3) -> dict:
    """Send a prompt to Gemini and parse its response as JSON."""
    import time

    client = _get_client()

    for attempt in range(retries):
        try:
            response = client.models.generate_content(model=_MODEL_NAME, contents=prompt)
            raw_text = response.text.strip()

            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`")
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            return json.loads(raw_text)

        except Exception as exc:
            is_last = attempt == retries - 1
            if "503" in str(exc) or "UNAVAILABLE" in str(exc):
                if is_last:
                    raise
                wait = 5 * (attempt + 1)
                logger.warning(f"Gemini 503, retrying in {wait}s (attempt {attempt + 1}/{retries})")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError("Gemini failed after all retries")