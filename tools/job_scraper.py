"""Multi-source job aggregation: jobspy boards + Wellfound + career pages, in parallel, deduped."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from jobspy import scrape_jobs

from tools.career_page_scraper import fetch_career_page_jobs
from tools.dedup import dedupe_jobs
from tools.wellfound_scraper import search_wellfound

logger = logging.getLogger("job_agent")

JOBSPY_SITES = {"linkedin", "indeed", "naukri", "zip_recruiter", "glassdoor"}


def _scrape_jobspy(keywords: str, location: str, sites: list[str], results_wanted: int, hours_old: int) -> list[dict]:
    active = [s for s in sites if s in JOBSPY_SITES]
    if not active:
        return []
    df = scrape_jobs(
        site_name=active,
        search_term=keywords,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
    )
    if df is None or df.empty:
        return []
    df = df.fillna("")
    jobs = []
    for idx, row in df.iterrows():
        job_url = row.get("job_url", "") or str(idx)
        jobs.append(
            {
                "id": job_url,
                "title": row.get("title", ""),
                "company": row.get("company", ""),
                "location": str(row.get("location", "")),
                "site": row.get("site", ""),
                "url": row.get("job_url", ""),
                "description": row.get("description", "") or "",
                "date_posted": str(row.get("date_posted", "")),
            }
        )
    return jobs


def _scrape_career_pages(career_page_urls: list[str], llm, min_delay_seconds: float) -> list[dict]:
    jobs = []
    for url in career_page_urls:
        jobs.extend(fetch_career_page_jobs(url, llm))
        time.sleep(min_delay_seconds)  # ponytail: polite delay between our own custom fetches
    return jobs


def search_jobs(
    keywords: str,
    location: str,
    sites: list[str],
    results_wanted: int = 20,
    hours_old: int = 72,
    career_page_urls: list[str] | None = None,
    llm=None,
    min_delay_seconds: float = 1.5,
) -> list[dict]:
    career_page_urls = career_page_urls or []

    tasks: dict[str, tuple] = {"jobspy": (_scrape_jobspy, (keywords, location, sites, results_wanted, hours_old))}
    if "wellfound" in sites:
        tasks["wellfound"] = (search_wellfound, (keywords, location))
    if career_page_urls and llm is not None:
        tasks["career_pages"] = (_scrape_career_pages, (career_page_urls, llm, min_delay_seconds))

    all_jobs: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {executor.submit(fn, *args): name for name, (fn, args) in tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                all_jobs.extend(result)
                logger.info("%s: %d jobs", name, len(result))
            except Exception as e:
                logger.warning("%s scraping failed: %s", name, e)

    return dedupe_jobs(all_jobs)
