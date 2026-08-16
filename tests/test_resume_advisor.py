from agents.resume_advisor import (
    analyze_resume_profile,
    estimate_total_experience_years,
    flatten_skills,
)


def test_resume_profile_analytics():
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
