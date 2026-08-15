"""LangGraph state schema for the job application agent."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict


class GeneratedContent(TypedDict):
    job_id: str
    cover_letter: str
    screening_answers: dict[str, str]
    status: Literal["pending", "approved", "rejected"]
    comment: str
    tone: str


class AgentState(TypedDict):
    resume_path: str
    resume_data: dict[str, Any]
    search_filters: dict[str, Any]
    settings: dict[str, Any]
    jobs: list[dict[str, Any]]
    matches: list[dict[str, Any]]
    selected_job_ids: list[str]
    generated: dict[str, GeneratedContent]
    company_research: dict[str, Any]
    model_config: dict[str, Any]
    log: Annotated[list[str], operator.add]
