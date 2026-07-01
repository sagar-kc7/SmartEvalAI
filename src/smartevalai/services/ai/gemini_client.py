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


def generate_json(prompt: str) -> dict:
    """Send a prompt to Gemini and parse its response as JSON.

    The prompt is expected to instruct Gemini to return ONLY a JSON object
    (no markdown fences, no commentary) — see the prompt builders in
    `prompts.py` for the exact instructions used.

    Args:
        prompt: The full prompt text to send.

    Returns:
        The parsed JSON response as a dict.

    Raises:
        ValueError: If Gemini's response isn't valid JSON.
    """
    client = _get_client()
    response = client.models.generate_content(model=_MODEL_NAME, contents=prompt)
    raw_text = response.text.strip()

    # Defensive cleanup: occasionally models wrap JSON in markdown fences
    # even when instructed not to.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error(f"Gemini returned invalid JSON: {raw_text[:500]}")
        raise ValueError(f"Gemini response was not valid JSON: {exc}") from exc