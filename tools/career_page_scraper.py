"""Extract job postings from an arbitrary company careers page via LLM extraction.

ponytail: career pages have no common structure, so we hand the visible text
to the local model instead of writing a per-site parser. Best-effort - a page
with no visible listing text (pure client-side rendering) will just yield [].
"""

from __future__ import annotations

import json
import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain_core.messages import HumanMessage

from utils import strip_code_fences

logger = logging.getLogger("job_agent")

EXTRACTION_PROMPT = """This is the text content of a company careers page. Extract any job postings
visible as a JSON array of objects: {{"title": "...", "location": "...", "description": "..."}}.
Return ONLY a JSON array. Return [] if no postings are visible.

Page text:
{text}
"""


def _company_from_url(url: str) -> str:
    host = urlparse(url).netloc
    return host.replace("www.", "").split(".")[0].capitalize()


def fetch_career_page_jobs(url: str, llm, timeout: int = 15) -> list[dict]:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (job-search-agent)"})
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Career page fetch failed for %s: %s", url, e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text("\n", strip=True)[:8000]
    if not text:
        return []

    response = llm.invoke([HumanMessage(content=EXTRACTION_PROMPT.format(text=text))])
    cleaned = strip_code_fences(response.content)
    try:
        postings = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.info("Career page %s: could not parse extracted postings", url)
        return []

    company = _company_from_url(url)
    jobs = []
    for p in postings if isinstance(postings, list) else []:
        title = p.get("title", "")
        jobs.append(
            {
                "id": f"{url}::{title}",
                "title": title,
                "company": company,
                "location": p.get("location", ""),
                "site": "career_page",
                "url": url,
                "description": p.get("description", ""),
                "date_posted": "",
            }
        )
    return jobs
