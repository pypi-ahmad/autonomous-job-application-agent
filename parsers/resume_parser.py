"""PDF/DOCX text extraction + LLM-based structured extraction.

Produces a "deep" resume profile: skills grouped by category, an experience
timeline with computed duration_months per role, and a separate list of
quantified achievements.
"""

from __future__ import annotations

import json
from datetime import date

import docx
from langchain_core.messages import HumanMessage
from pypdf import PdfReader

from utils import strip_code_fences

EXTRACTION_PROMPT = """Extract structured data from this resume as JSON with exactly these keys:
- skills: an object grouping skills by category, e.g. {{"languages": [...], "frameworks": [...],
  "cloud_devops": [...], "tools": [...], "soft_skills": [...]}}. Only include categories that apply.
- experience: list of objects {{title, company, start_date, end_date, duration_months, highlights}}.
  duration_months is an integer you compute from start_date/end_date (today's date is {today} -
  use it to resolve "Present"/"Current").
- education: list of objects {{degree, institution, year}}
- projects: list of objects {{name, description}}
- achievements: list of short strings, ONLY quantified achievements (contain a number, %, or metric)
  pulled from experience or projects
- summary: 2-3 sentence professional summary

Return ONLY valid JSON. No markdown fences, no commentary.

Resume text:
{text}
"""

_EMPTY_RESULT = {
    "skills": {},
    "experience": [],
    "education": [],
    "projects": [],
    "achievements": [],
    "summary": "",
}


def extract_text(file_path: str) -> str:
    lower = file_path.lower()
    if lower.endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if lower.endswith(".docx"):
        document = docx.Document(file_path)
        return "\n".join(p.text for p in document.paragraphs)
    raise ValueError(f"Unsupported resume format: {file_path} (use PDF or DOCX)")


def parse_resume(file_path: str, llm) -> dict:
    text = extract_text(file_path)
    # 12,000-character cap keeps the prompt within typical local-model context windows.
    # Content beyond this limit is silently dropped; very long resumes may lose later sections.
    prompt = EXTRACTION_PROMPT.format(text=text[:12000], today=date.today().isoformat())
    response = llm.invoke([HumanMessage(content=prompt)])
    cleaned = strip_code_fences(response.content)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        data = dict(_EMPTY_RESULT)
    data["raw_text"] = text
    return data
