"""Deterministic resume-profile helpers (deep resume intelligence)."""

from __future__ import annotations


def flatten_skills(resume_data: dict) -> list[str]:
    skills = resume_data.get("skills", [])
    if isinstance(skills, dict):
        flat: list[str] = []
        for category_skills in skills.values():
            flat.extend(category_skills)
        return flat
    return list(skills)


def estimate_total_experience_years(resume_data: dict) -> float:
    total_months = sum(int(exp.get("duration_months", 0) or 0) for exp in resume_data.get("experience", []))
    return round(total_months / 12, 1)


def analyze_resume_profile(resume_data: dict) -> dict:
    """Standalone resume-intelligence summary, independent of any specific job."""
    skills = resume_data.get("skills", {})
    skill_categories = skills if isinstance(skills, dict) else {"skills": list(skills)}
    return {
        "total_experience_years": estimate_total_experience_years(resume_data),
        "skill_categories": skill_categories,
        "num_roles": len(resume_data.get("experience", [])),
        "num_achievements": len(resume_data.get("achievements", [])),
    }


def demo() -> None:
    resume = {
        "skills": {"languages": ["python", "sql"], "tools": ["docker"]},
        "experience": [{"duration_months": 18}, {"duration_months": 30}],
        "achievements": ["Cut latency by 40%"],
    }
    assert flatten_skills(resume) == ["python", "sql", "docker"]
    assert estimate_total_experience_years(resume) == 4.0
    profile = analyze_resume_profile(resume)
    assert profile["num_roles"] == 2
    assert profile["num_achievements"] == 1
    print("resume_advisor.demo: all checks passed")


if __name__ == "__main__":
    demo()
