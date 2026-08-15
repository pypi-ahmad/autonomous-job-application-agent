"""Company research agent: web snippets + LLM synthesis into a short brief.

ponytail: scrapes DuckDuckGo's HTML endpoint directly (no API key required)
rather than adding a search-API dependency. Markup changes upstream could
break this; swap in a real search API if one is available.
"""

from __future__ import annotations

import json
import logging

import requests
from bs4 import BeautifulSoup
from langchain_core.messages import HumanMessage

from utils import strip_code_fences

logger = logging.getLogger("job_agent")

_EMPTY_BRIEF = {
    "summary": "Unknown",
    "recent_news": "Unknown",
    "culture": "Unknown",
    "products": "Unknown",
    "funding": "Unknown",
}

RESEARCH_PROMPT = """Based on these web search snippets about "{company}", write a short company
research brief as JSON: {{"summary": "...", "recent_news": "...", "culture": "...",
"products": "...", "funding": "..."}}. Use "Unknown" for any field with no evidence in the
snippets. Do not invent facts.

Snippets:
{snippets}
"""


def _ddg_snippets(query: str, max_results: int = 5, timeout: int = 10) -> list[str]:
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (job-search-agent)"},
            timeout=timeout,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Company research search failed for %r: %s", query, e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    snippets = []
    for result in soup.select(".result__snippet")[:max_results]:
        text = result.get_text(" ", strip=True)
        if text:
            snippets.append(text)
    return snippets


def research_company(company: str, llm) -> dict:
    if not company:
        return dict(_EMPTY_BRIEF)

    snippets = _ddg_snippets(f"{company} company news culture products funding")
    if not snippets:
        return {**_EMPTY_BRIEF, "summary": "No web research available."}

    prompt = RESEARCH_PROMPT.format(company=company, snippets="\n".join(f"- {s}" for s in snippets))
    response = llm.invoke([HumanMessage(content=prompt)])
    cleaned = strip_code_fences(response.content)
    try:
        brief = json.loads(cleaned)
    except json.JSONDecodeError:
        brief = {**_EMPTY_BRIEF, "summary": snippets[0]}
    return brief
