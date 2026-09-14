"""Deduplicate job postings scraped from multiple sources."""

from __future__ import annotations

import difflib
import re

# ponytail: O(n^2) pairwise comparison. Fine for the hundreds-of-jobs scale
# this app deals with; switch to a blocking/index approach if that ever grows.


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def dedupe_jobs(jobs: list[dict], similarity_threshold: float = 0.88) -> list[dict]:
    # 0.88 is empirically tuned: high enough to merge cross-site reposts of the same
    # role (minor title variation), low enough to keep "Junior" and "Senior" variants separate.
    deduped: list[dict] = []
    for job in jobs:
        key_company = _normalize(job.get("company", ""))
        key_title = _normalize(job.get("title", ""))
        match = None
        for existing in deduped:
            if _normalize(existing.get("company", "")) != key_company:
                continue
            ratio = difflib.SequenceMatcher(None, key_title, _normalize(existing.get("title", ""))).ratio()
            if ratio >= similarity_threshold:
                match = existing
                break
        if match:
            sources = set(match.get("sources", []))
            if match.get("site"):
                sources.add(match["site"])
            if job.get("site"):
                sources.add(job["site"])
            match["sources"] = sorted(sources)
        else:
            job = dict(job)
            job["sources"] = [job["site"]] if job.get("site") else []
            deduped.append(job)
    return deduped


def demo() -> None:
    jobs = [
        {"title": "Senior Python Developer", "company": "Acme Corp", "site": "linkedin", "id": "1"},
        {"title": "Senior Python Developer", "company": "Acme Corp.", "site": "indeed", "id": "2"},
        {"title": "Data Scientist", "company": "Acme Corp", "site": "indeed", "id": "3"},
    ]
    result = dedupe_jobs(jobs)
    assert len(result) == 2, result
    assert sorted(result[0]["sources"]) == ["indeed", "linkedin"]
    print("dedup.demo: all checks passed")


if __name__ == "__main__":
    demo()
