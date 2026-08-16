from tools.dedup import dedupe_jobs


def test_dedupe_jobs_merges_near_duplicate_titles_same_company():
    jobs = [
        {"title": "Senior Python Developer", "company": "Acme Corp", "site": "linkedin", "id": "1"},
        {"title": "Senior Python Developer", "company": "Acme Corp.", "site": "indeed", "id": "2"},
        {"title": "Data Scientist", "company": "Acme Corp", "site": "indeed", "id": "3"},
    ]
    result = dedupe_jobs(jobs)
    assert len(result) == 2, result
    assert sorted(result[0]["sources"]) == ["indeed", "linkedin"]
