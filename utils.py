"""Shared helpers: logging and LLM-output cleanup. Application history lives in tools/tracker.py."""

from __future__ import annotations

import logging


def setup_logging() -> logging.Logger:
    # All tool/agent modules obtain this same logger via logging.getLogger("job_agent").
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return logging.getLogger("job_agent")


def strip_code_fences(text: str) -> str:
    """Strip ```json / ``` fences an LLM sometimes wraps JSON output in."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```")
    return cleaned.strip()


def demo() -> None:
    cases = [
        ('{"a": 1}', '{"a": 1}'),
        ('```json\n{"a": 1}\n```', '{"a": 1}'),
        ('```\n{"a": 1}\n```', '{"a": 1}'),
        ('  {"a": 1}  ', '{"a": 1}'),
    ]
    for raw, expected in cases:
        assert strip_code_fences(raw) == expected, f"failed for {raw!r}"
    print("utils.demo: all checks passed")


if __name__ == "__main__":
    demo()
