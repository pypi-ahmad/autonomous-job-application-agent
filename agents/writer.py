"""Draft (local model) then polish (API model) cover letters and screening answers.

Supports tone selection and optional company-research context so generated
content can reference real, recent facts about the employer.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from agents.resume_advisor import flatten_skills

TONE_GUIDANCE = {
    "Professional": "formal, polished, achievement-focused",
    "Enthusiastic": "energetic, warm, genuinely excited about the role",
    "Concise": "brief, to the point, no filler, under 200 words",
    "Story-driven": "opens with a short relevant anecdote or concrete moment from the candidate's experience",
}

COVER_LETTER_DRAFT_PROMPT = """Write a tailored cover letter (3-4 paragraphs) for this job, based
only on facts in the resume. Do not invent experience, skills, or claims not present below.
Tone: {tone} ({tone_guidance}).
{company_context}

Resume summary: {summary}
Resume skills: {skills}
Resume experience: {experience}
Resume achievements: {achievements}

Job title: {title}
Company: {company}
Job description: {description}
"""

POLISH_PROMPT = """Polish this draft for tone, clarity, and impact. Keep it factually identical -
do not add any new claims, numbers, or experience. Return only the final text, no preamble.

Draft:
{draft}
"""

SCREENING_DRAFT_PROMPT = """Answer this job application screening question in 3-5 sentences,
based only on facts in the resume below. Do not invent anything.
{company_context}

Resume summary: {summary}
Resume experience: {experience}

Question: {question}
"""


def _company_context(company_research: dict | None) -> str:
    # Filters out "Unknown" values because _EMPTY_BRIEF uses that as its missing-data
    # sentinel; forwarding them to the LLM would instruct it to mention unknowns.
    if not company_research:
        return ""
    parts = [f"{k}: {v}" for k, v in company_research.items() if v and v != "Unknown"]
    if not parts:
        return ""
    return "Relevant company research (use only if it fits naturally, do not force it):\n" + "\n".join(parts)


def draft_cover_letter(
    resume_data: dict,
    job: dict,
    llm,
    tone: str = "Professional",
    company_research: dict | None = None,
) -> str:
    prompt = COVER_LETTER_DRAFT_PROMPT.format(
        tone=tone,
        tone_guidance=TONE_GUIDANCE.get(tone, TONE_GUIDANCE["Professional"]),
        company_context=_company_context(company_research),
        summary=resume_data.get("summary", ""),
        skills=", ".join(flatten_skills(resume_data)),
        experience=resume_data.get("experience", []),
        achievements=resume_data.get("achievements", []),
        title=job["title"],
        company=job["company"],
        description=job["description"][:4000],  # same cap as in matcher.py
    )
    return llm.invoke([HumanMessage(content=prompt)]).content.strip()


def polish_text(draft: str, llm) -> str:
    return llm.invoke([HumanMessage(content=POLISH_PROMPT.format(draft=draft))]).content.strip()


def draft_screening_answer(
    resume_data: dict,
    question: str,
    llm,
    company_research: dict | None = None,
) -> str:
    prompt = SCREENING_DRAFT_PROMPT.format(
        company_context=_company_context(company_research),
        summary=resume_data.get("summary", ""),
        experience=resume_data.get("experience", []),
        question=question,
    )
    return llm.invoke([HumanMessage(content=prompt)]).content.strip()
