"""Best-effort Wellfound (AngelList Talent) job search.

ponytail: Wellfound is a JS-rendered SPA with no public API. This scrapes the
Next.js SSR payload embedded in the page and heuristically finds job-shaped
entries within it. Fragile - if Wellfound changes its frontend this silently
returns []. Upgrade path: an official partner API, if Wellfound ever offers one.
"""

from __future__ import annotations

import json
import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("job_agent")

SEARCH_URL = "https://wellfound.com/jobs"


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def search_wellfound(keywords: str, location: str = "", timeout: int = 15) -> list[dict]:
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"q": keywords, "l": location},
            headers={"User-Agent": "Mozilla/5.0 (job-search-agent)"},
            timeout=timeout,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Wellfound fetch failed: %s", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        logger.info("Wellfound: no embedded data found (page structure may have changed)")
        return []

    try:
        data = json.loads(script.string)
    except json.JSONDecodeError:
        return []

    jobs = []
    seen_ids = set()
    for node in _walk(data):
        if not (isinstance(node, dict) and "title" in node and ("companyName" in node or "company" in node)):
            continue
        job_id = str(node.get("id") or node.get("slug") or node.get("title"))
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)
        jobs.append(
            {
                "id": job_id,
                "title": str(node.get("title", "")),
                "company": str(node.get("companyName") or node.get("company") or ""),
                "location": str(node.get("location", location)),
                "site": "wellfound",
                "url": node.get("url") or SEARCH_URL,
                "description": str(node.get("description", "")),
                "date_posted": str(node.get("liveStartAt", "")),
            }
        )
    return jobs
