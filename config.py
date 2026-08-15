"""Environment-driven configuration. No secrets hardcoded here."""

from __future__ import annotations

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

AGNES_API_KEY = os.environ.get("AGNES_API_KEY")
AGNES_BASE_URL = "https://apihub.agnes-ai.com/v1"
AGNES_MODEL = "agnes-2.5-flash"

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

OPENAI_MODELS = ["gpt-5.6-luna", "gpt-5.6-terra"]
GEMINI_MODELS = ["gemini-3.5-flash-lite", "gemini-3.7-flash"]

DEFAULT_SCREENING_QUESTIONS = [
    "Why are you interested in this role?",
    "What is your notice period / earliest start date?",
    "What are your salary expectations?",
]

SUPPORTED_JOB_SITES = ["linkedin", "indeed", "naukri", "zip_recruiter", "glassdoor", "wellfound"]
COVER_LETTER_TONES = ["Professional", "Enthusiastic", "Concise", "Story-driven"]


def list_ollama_models() -> list[str]:
    """Query the local Ollama server for installed models. Empty list if unreachable."""
    try:
        resp = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return []
