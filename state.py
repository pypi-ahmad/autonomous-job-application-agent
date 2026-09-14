"""LangGraph state schema for the job application agent."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict


class GeneratedContent(TypedDict):
    job_id: str
    cover_letter: str
    screening_answers: dict[str, str]
    # Status lifecycle driven by the UI: "pending" on creation, then "approved"
    # or "rejected" by the human-approval step.
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
    # operator.add is the LangGraph reducer for this field: each node appends to the
    # existing list instead of overwriting it. Every other field is fully replaced by
    # the partial dict a node returns.
    log: Annotated[list[str], operator.add]
