from agents.matcher import extract_required_years, match_job


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


def test_match_job_combines_llm_scores_with_deterministic_keyword_overlap():
    resume = {
        "summary": "Backend engineer",
        "skills": {"languages": ["python", "sql"]},
        "raw_text": "python sql backend engineer",
    }
    job = {
        "title": "Backend Engineer",
        "company": "Acme",
        "location": "Remote",
        "description": "python backend role, 3+ years",
    }
    result = match_job(resume, job, _StubLLM(), location_preference="Remote")
    assert result["scores"]["skills"] == 90
    assert result["scores"]["keywords"] > 0
    assert 0 <= result["overall"] <= 100
    assert result["skill_gaps"] == ["Kubernetes"]
    assert extract_required_years(job["description"]) == 3
