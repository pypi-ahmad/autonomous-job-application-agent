"""Multi-factor job matching: deterministic groundings + LLM judgment, explainable output."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage

from agents.resume_advisor import estimate_total_experience_years, flatten_skills
from utils import strip_code_fences

# ponytail: one sequential LLM call per job, and the factor weights below are a
# fixed heuristic (not learned/tunable per user). Fine up to ~100 jobs; batch/
# async the calls and expose weights as settings if that ever falls short.
WEIGHTS = {
    "skills": 0.30,
    "experience": 0.20,
    "domain": 0.15,
    "keywords": 0.15,
    "seniority": 0.10,
    "location": 0.10,
}

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "with", "on", "is",
    "are", "as", "at", "by", "be", "will", "we", "you", "our", "your", "this",
    "that", "from", "have", "has", "job", "role", "team", "work", "who", "what",
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9+#.]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


def keyword_overlap_score(resume_text: str, description: str) -> int:
    """Deterministic Jaccard-style overlap - grounds one scoring factor instead of trusting the LLM for it."""
    job_tokens = _tokenize(description)
    if not job_tokens:
        return 0
    resume_tokens = _tokenize(resume_text)
    overlap = resume_tokens & job_tokens
    return round(100 * len(overlap) / len(job_tokens))


def extract_required_years(description: str) -> int | None:
    match = re.search(r"(\d+)\+?\s*(?:years|yrs)", description.lower())
    return int(match.group(1)) if match else None


MATCH_PROMPT = """You are a job-matching engine. Score this resume against the job on several
factors (0-100 each) and explain your reasoning. Use ONLY the facts given - do not invent resume
content or job requirements.

Return ONLY JSON in this exact shape:
{{
  "skills_score": <0-100>,
  "experience_score": <0-100>,
  "domain_score": <0-100>,
  "seniority_score": <0-100>,
  "location_score": <0-100>,
  "pros": [<2-4 short strings: why this job suits the candidate>],
  "cons": [<1-3 short strings: why it might not>],
  "reasons": [<3-5 short strings summarizing the overall verdict>],
  "skill_gaps": [<skills the job wants that are missing from the resume>],
  "resume_suggestions": [<2-4 concrete suggestions to improve THIS candidate's match for THIS job>]
}}

Resume summary: {summary}
Resume skills: {skills}
Total years of experience: {total_years}

Job title: {title}
Company: {company}
Job location: {job_location}
Candidate's location preference: {location_pref}
Required years mentioned in posting (if any): {required_years}
Job description: {description}
"""


def match_job(resume_data: dict, job: dict, llm, location_preference: str = "") -> dict:
    skills = flatten_skills(resume_data)
    total_years = estimate_total_experience_years(resume_data)
    required_years = extract_required_years(job["description"])

    prompt = MATCH_PROMPT.format(
        summary=resume_data.get("summary", ""),
        skills=", ".join(skills),
        total_years=total_years,
        title=job["title"],
        company=job["company"],
        job_location=job.get("location", ""),
        location_pref=location_preference or "no preference stated",
        required_years=required_years if required_years is not None else "not specified",
        description=job["description"][:4000],
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    cleaned = strip_code_fences(response.content)
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        result = {}

    scores = {
        "skills": int(result.get("skills_score", 0) or 0),
        "experience": int(result.get("experience_score", 0) or 0),
        "domain": int(result.get("domain_score", 0) or 0),
        "seniority": int(result.get("seniority_score", 0) or 0),
        "location": int(result.get("location_score", 0) or 0),
        "keywords": keyword_overlap_score(resume_data.get("raw_text", ""), job["description"]),
    }
    overall = round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS))

    return {
        "job": job,
        "overall": overall,
        "scores": scores,
        "pros": result.get("pros", []),
        "cons": result.get("cons", []),
        "reasons": result.get("reasons", []),
        "skill_gaps": result.get("skill_gaps", []),
        "resume_suggestions": result.get("resume_suggestions", []),
    }


def demo() -> None:
    class _StubLLM:
        def invoke(self, _messages):
            class _Resp:
                content = (
                    '```json\n{"skills_score": 90, "experience_score": 70, "domain_score": 80, '
                    '"seniority_score": 60, "location_score": 100, "pros": ["Strong python match"], '
                    '"cons": ["Less domain depth"], "reasons": ["Good overall fit"], '
                    '"skill_gaps": ["Kubernetes"], "resume_suggestions": ["Add a metric to your last role"]}\n```'
                )

            return _Resp()

    resume = {"summary": "Backend engineer", "skills": {"languages": ["python", "sql"]}, "raw_text": "python sql backend engineer"}
    job = {"title": "Backend Engineer", "company": "Acme", "location": "Remote", "description": "python backend role, 3+ years"}
    result = match_job(resume, job, _StubLLM(), location_preference="Remote")
    assert result["scores"]["skills"] == 90
    assert result["scores"]["keywords"] > 0
    assert 0 <= result["overall"] <= 100
    assert result["skill_gaps"] == ["Kubernetes"]
    assert extract_required_years(job["description"]) == 3
    print("matcher.demo: all checks passed")


if __name__ == "__main__":
    demo()
