"""LangGraph state machine: parse -> scrape -> match -> [select] -> generate -> [approve] -> submit."""

from __future__ import annotations

import time
import webbrowser

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

import tools.tracker as tracker
from agents.matcher import match_job
from agents.writer import draft_cover_letter, draft_screening_answer, polish_text
from parsers.resume_parser import parse_resume
from state import AgentState
from tools.company_research import research_company
from tools.job_scraper import search_jobs


def node_parse_resume(state: AgentState) -> dict:
    llm = state["model_config"]["resume_llm"]
    data = parse_resume(state["resume_path"], llm)
    return {"resume_data": data, "log": [f"Parsed resume: {sum(len(v) for v in data.get('skills', {}).values())} skills found"]}


def node_scrape_jobs(state: AgentState) -> dict:
    f = state["search_filters"]
    settings = state["settings"]
    career_page_urls = settings.get("career_page_urls", [])
    jobs = search_jobs(
        f["keywords"],
        f["location"],
        f["sites"],
        f.get("results_wanted", 20),
        f.get("hours_old", 72),
        career_page_urls=career_page_urls,
        llm=state["model_config"]["match_llm"],
        min_delay_seconds=settings.get("min_delay_seconds", 1.5),
    )
    extra = f" + {len(career_page_urls)} career page(s)" if career_page_urls else ""
    return {"jobs": jobs, "log": [f"Scraped {len(jobs)} unique jobs from {', '.join(f['sites'])}{extra}"]}


def node_match_jobs(state: AgentState) -> dict:
    llm = state["model_config"]["match_llm"]
    location_pref = state["settings"].get("location_preference", "")
    matches = [match_job(state["resume_data"], job, llm, location_pref) for job in state["jobs"]]
    matches.sort(key=lambda m: m["overall"], reverse=True)
    return {"matches": matches, "log": [f"Matched and scored {len(matches)} jobs"]}


def node_generate_content(state: AgentState) -> dict:
    model_cfg = state["model_config"]
    draft_llm = model_cfg["draft_llm"]
    polish_llm = model_cfg["polish_llm"]
    settings = state["settings"]
    questions = state["search_filters"].get("screening_questions", [])
    selected_ids = set(state["selected_job_ids"])
    tone = settings.get("tone", "Professional")

    company_research = dict(state.get("company_research", {}))
    generated = {}
    for m in state["matches"]:
        job = m["job"]
        if job["id"] not in selected_ids:
            continue

        company = job["company"]
        if company and company not in company_research:
            company_research[company] = research_company(company, draft_llm)
        brief = company_research.get(company)

        draft = draft_cover_letter(state["resume_data"], job, draft_llm, tone=tone, company_research=brief)
        final_letter = polish_text(draft, polish_llm)

        answers = {}
        for q in questions:
            a_draft = draft_screening_answer(state["resume_data"], q, draft_llm, company_research=brief)
            answers[q] = polish_text(a_draft, polish_llm)

        generated[job["id"]] = {
            "job_id": job["id"],
            "cover_letter": final_letter,
            "screening_answers": answers,
            "status": "pending",
            "comment": "",
            "tone": tone,
        }
        tracker.upsert_application(job, "Draft", note="Content generated")

    return {
        "generated": generated,
        "company_research": company_research,
        "log": [f"Generated content for {len(generated)} jobs (tone: {tone})"],
    }


def node_human_approval(state: AgentState) -> dict:
    return {"log": ["Awaiting human approval"]}


def node_submit(state: AgentState) -> dict:
    matches_by_id = {m["job"]["id"]: m["job"] for m in state["matches"]}
    approved = [g for g in state["generated"].values() if g["status"] == "approved"]
    settings = state["settings"]
    dry_run = settings.get("dry_run", True)
    delay = settings.get("min_delay_seconds", 1.0)

    opened = 0
    for g in approved:
        job = matches_by_id[g["job_id"]]
        if dry_run:
            # ponytail: dry run stays at "Approved" in the tracker - nothing was
            # actually submitted, so "Submitted" would be a false record.
            tracker.update_status(job["id"], "Approved", note="Dry run - not submitted")
            continue
        # Opens the listing for the user to submit manually rather than auto-filling
        # the job board's form. Automating real submission needs per-site login +
        # CAPTCHA handling and risks ToS violations / account bans.
        webbrowser.open(job["url"])
        tracker.update_status(job["id"], "Submitted", note="Opened for manual submission")
        opened += 1
        time.sleep(delay)

    mode = "dry run (nothing opened)" if dry_run else f"opened {opened} page(s) for manual submission"
    return {"log": [f"Submit: {mode}"]}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("parse_resume", node_parse_resume)
    graph.add_node("scrape_jobs", node_scrape_jobs)
    graph.add_node("match_jobs", node_match_jobs)
    graph.add_node("generate_content", node_generate_content)
    graph.add_node("human_approval", node_human_approval)
    graph.add_node("submit", node_submit)

    graph.set_entry_point("parse_resume")
    graph.add_edge("parse_resume", "scrape_jobs")
    graph.add_edge("scrape_jobs", "match_jobs")
    graph.add_edge("match_jobs", "generate_content")
    graph.add_edge("generate_content", "human_approval")
    graph.add_edge("human_approval", "submit")
    graph.set_finish_point("submit")

    checkpointer = MemorySaver()
    # Pause before generate_content (user picks which matches to draft) and
    # before human_approval (user reviews/edits/comments/approves the content).
    return graph.compile(checkpointer=checkpointer, interrupt_before=["generate_content", "human_approval"])
