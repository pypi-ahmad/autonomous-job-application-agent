"""Build chat model clients for each configured provider."""

from __future__ import annotations

import config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

Provider = str  # "ollama" | "openai" | "agnes" | "gemini"


def get_chat_model(provider: Provider, model: str, reasoning_effort: str | None = None):
    if provider == "ollama":
        return ChatOllama(model=model, base_url=config.OLLAMA_HOST)

    if provider == "openai":
        kwargs = {"model_kwargs": {"reasoning_effort": reasoning_effort}} if reasoning_effort else {}
        return ChatOpenAI(
            model=model,
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
            **kwargs,
        )

    if provider == "agnes":
        # Agnes AI exposes an OpenAI-compatible endpoint, so ChatOpenAI is reused
        # with a different base_url and key rather than adding a new client class.
        # reasoning_effort is not forwarded here because Agnes does not support it.
        return ChatOpenAI(
            model=config.AGNES_MODEL,
            api_key=config.AGNES_API_KEY,
            base_url=config.AGNES_BASE_URL,
        )

    if provider == "gemini":
        return ChatGoogleGenerativeAI(model=model, google_api_key=config.GOOGLE_API_KEY)

    raise ValueError(f"Unknown provider: {provider}")
