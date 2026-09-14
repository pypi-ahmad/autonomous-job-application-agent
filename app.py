"""Streamlit UI wiring the LangGraph pipeline: resume -> scrape -> match -> draft -> approve -> submit."""

from __future__ import annotations

import uuid
from pathlib import Path

import streamlit as st

import config
import tools.tracker as tracker
from agents.resume_advisor import analyze_resume_profile
from agents.writer import draft_cover_letter, polish_text
from graph import build_graph
from tools.llm_factory import get_chat_model
from utils import setup_logging

setup_logging()

st.set_page_config(page_title="Autonomous Job Application Agent", layout="wide")

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Maps GeneratedContent.status (graph-internal vocabulary) to tracker CRM labels.
# The graph and tracker use different status vocabularies; this bridge keeps them in sync.
STATUS_MAP = {"pending": "Draft", "approved": "Approved", "rejected": "Rejected"}


def init_session() -> None:
    # build_graph() is called once per browser session, not on every Streamlit rerun.
    # thread_id is the MemorySaver checkpoint key; a new UUID means a fresh pipeline run.
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "graph" not in st.session_state:
        st.session_state.graph = build_graph()
    if "started" not in st.session_state:
        st.session_state.started = False


def rc() -> dict:
    # "run config" — the dict LangGraph requires to look up the correct checkpoint
    # in MemorySaver. Every graph.invoke / get_state / update_state call must pass this.
    return {"configurable": {"thread_id": st.session_state.thread_id}}


def sidebar_model_config() -> dict:
    st.sidebar.header("Model configuration")

    ollama_models = config.list_ollama_models()
    if not ollama_models:
        st.sidebar.warning("No Ollama models found. Is `ollama serve` running?")
    local_model = st.sidebar.selectbox(
        "Local model (Ollama) - parsing, matching, drafts",
        ollama_models or ["(none found)"],
    )

    st.sidebar.markdown("**Final polish** (cover letters, critical answers)")
    provider_label = st.sidebar.selectbox("Provider", ["OpenAI-compatible", "Agnes AI", "Google Gemini"])

    reasoning_effort = None
    if provider_label == "OpenAI-compatible":
        polish_model = st.sidebar.selectbox("Model", config.OPENAI_MODELS)
        reasoning_effort = "medium"
        if not config.OPENAI_API_KEY:
            st.sidebar.error("OPENAI_API_KEY not set in environment.")
    elif provider_label == "Agnes AI":
        st.sidebar.text_input("Model", value=config.AGNES_MODEL, disabled=True)
        polish_model = config.AGNES_MODEL
        if not config.AGNES_API_KEY:
            st.sidebar.error("AGNES_API_KEY not set in environment.")
    else:
        polish_model = st.sidebar.selectbox("Model", config.GEMINI_MODELS)
        if not config.GOOGLE_API_KEY:
            st.sidebar.error("GOOGLE_API_KEY not set in environment.")

    return {
        "local_model": local_model,
        "provider_label": provider_label,
        "polish_model": polish_model,
        "reasoning_effort": reasoning_effort,
    }


def sidebar_settings() -> dict:
    st.sidebar.header("Generation & safety settings")
    tone = st.sidebar.selectbox("Cover letter tone", config.COVER_LETTER_TONES)
    location_preference = st.sidebar.text_input("Location preference", value="Remote")
    dry_run = st.sidebar.checkbox("Dry run (generate only, never open or mark submitted)", value=True)
    min_delay_seconds = st.sidebar.slider("Delay between scrape/submit requests (sec)", 0.5, 5.0, 1.5, step=0.5)
    career_pages_text = st.sidebar.text_area("Company career page URLs (one per line, optional)", value="")
    career_page_urls = [u.strip() for u in career_pages_text.splitlines() if u.strip()]
    if not dry_run:
        st.sidebar.warning("Live mode: approved applications will open in your browser for you to submit.")
    return {
        "tone": tone,
        "location_preference": location_preference,
        "dry_run": dry_run,
        "min_delay_seconds": min_delay_seconds,
        "career_page_urls": career_page_urls,
    }


def build_model_config(choices: dict) -> dict:
    local_llm = get_chat_model("ollama", choices["local_model"])
    provider_map = {"OpenAI-compatible": "openai", "Agnes AI": "agnes", "Google Gemini": "gemini"}
    polish_provider = provider_map[choices["provider_label"]]
    polish_llm = get_chat_model(polish_provider, choices["polish_model"], choices.get("reasoning_effort"))
    # resume_llm / match_llm / draft_llm all point at the same local Ollama instance.
    # Four named slots exist so individual steps could be routed to different models
    # without changing callers; today they share one.
    return {
        "resume_llm": local_llm,
        "match_llm": local_llm,
        "draft_llm": local_llm,
        "polish_llm": polish_llm,
    }


def render_intake(choices: dict, settings: dict) -> None:
    st.header("1. Resume & job search")
    resume_file = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"])

    col1, col2 = st.columns(2)
    keywords = col1.text_input("Keywords", value="python developer")
    location = col2.text_input("Location", value="Remote")

    sites = st.multiselect("Job boards", config.SUPPORTED_JOB_SITES, default=["linkedin", "indeed"])
    experience_level = st.selectbox("Experience level", ["Any", "Entry level", "Mid level", "Senior"])
    results_wanted = st.slider("Results per board", 5, 50, 20)

    screening_text = st.text_area(
        "Screening questions (one per line)",
        value="\n".join(config.DEFAULT_SCREENING_QUESTIONS),
        height=100,
    )

    can_run = resume_file is not None and bool(sites)
    if st.button("Run: parse resume -> scrape jobs -> match", type="primary", disabled=not can_run):
        resume_path = UPLOAD_DIR / resume_file.name
        resume_path.write_bytes(resume_file.getvalue())

        search_term = keywords if experience_level == "Any" else f"{keywords} {experience_level}"
        questions = [q.strip() for q in screening_text.splitlines() if q.strip()]

        initial_state = {
            "resume_path": str(resume_path),
            "search_filters": {
                "keywords": search_term,
                "location": location,
                "sites": sites,
                "results_wanted": results_wanted,
                "hours_old": 72,  # hardcoded; not exposed in the sidebar
                "screening_questions": questions,
            },
            "settings": settings,
            "model_config": build_model_config(choices),
            "selected_job_ids": [],
            "generated": {},
            "company_research": {},
            "log": [],
        }
        with st.spinner("Parsing resume, scraping job boards, scoring matches..."):
            st.session_state.graph.invoke(initial_state, rc())
        st.session_state.started = True
        st.rerun()


def render_resume_profile() -> None:
    graph = st.session_state.graph
    snap = graph.get_state(rc())
    resume_data = snap.values.get("resume_data")
    if not resume_data:
        return
    profile = analyze_resume_profile(resume_data)
    with st.expander("Resume intelligence profile", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("Total experience (years)", profile["total_experience_years"])
        c2.metric("Roles", profile["num_roles"])
        c3.metric("Quantified achievements", profile["num_achievements"])
        for category, skills in profile["skill_categories"].items():
            st.caption(f"**{category}**: {', '.join(skills)}")


def render_selection() -> None:
    graph = st.session_state.graph
    snap = graph.get_state(rc())
    matches = snap.values.get("matches", [])

    st.header("2. Matched jobs")
    render_resume_profile()
    if not matches:
        st.warning("No jobs matched your filters. Start a new run with broader criteria.")
        return

    selected: list[str] = []
    for m in matches:
        job = m["job"]
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            sources = ", ".join(job.get("sources") or [job.get("site", "")])
            c1.markdown(f"**{job['title']}** @ {job['company']}  \n{sources} - {job['location']}")
            c2.metric("Match", f"{m['overall']}%")

            score_cols = st.columns(6)
            for col, (factor, value) in zip(score_cols, m["scores"].items()):
                col.caption(f"{factor}: {value}")

            if m["pros"]:
                st.markdown("**Why it fits:** " + " / ".join(m["pros"]))
            if m["cons"]:
                st.markdown("**Watch out for:** " + " / ".join(m["cons"]))
            if m["skill_gaps"]:
                st.markdown("**Skill gaps:** " + ", ".join(m["skill_gaps"]))
            if m["resume_suggestions"]:
                with st.expander("Resume improvement suggestions"):
                    for s in m["resume_suggestions"]:
                        st.markdown(f"- {s}")

            if st.checkbox("Draft content for this job", key=f"sel_{job['id']}", value=m["overall"] >= 70):
                selected.append(job["id"])

    if st.button("Generate cover letters & answers for selected jobs", type="primary", disabled=not selected):
        graph.update_state(rc(), {"selected_job_ids": selected})
        with st.spinner("Researching companies, drafting locally, polishing with the selected model..."):
            graph.invoke(None, rc())
        st.rerun()


def _apply_status(graph, job_id: str, letter: str, answers: dict, status: str, comment: str = "") -> None:
    # Two independent stores must be updated: the LangGraph checkpoint (in-memory,
    # drives pipeline logic) and the tracker JSON (on-disk, drives the Tracker tab).
    # Neither drives the other automatically.
    snap = graph.get_state(rc())
    generated = dict(snap.values["generated"])
    generated[job_id] = {**generated[job_id], "cover_letter": letter, "screening_answers": answers, "status": status, "comment": comment}
    graph.update_state(rc(), {"generated": generated})
    tracker.update_status(job_id, STATUS_MAP[status], note=comment)


def save_and_set_status(graph, job_id: str, letter: str, answers: dict, status: str, comment: str = "") -> None:
    _apply_status(graph, job_id, letter, answers, status, comment)
    st.rerun()


def regenerate_cover_letter(graph, job_id: str, settings: dict) -> None:
    snap = graph.get_state(rc())
    values = snap.values
    matches_by_id = {m["job"]["id"]: m["job"] for m in values["matches"]}
    job = matches_by_id[job_id]
    model_cfg = values["model_config"]
    brief = values.get("company_research", {}).get(job["company"])

    with st.spinner("Regenerating cover letter..."):
        draft = draft_cover_letter(values["resume_data"], job, model_cfg["draft_llm"], tone=settings["tone"], company_research=brief)
        final_letter = polish_text(draft, model_cfg["polish_llm"])

    generated = dict(values["generated"])
    generated[job_id] = {**generated[job_id], "cover_letter": final_letter, "status": "pending"}
    graph.update_state(rc(), {"generated": generated})
    st.rerun()


def render_approval(settings: dict) -> None:
    graph = st.session_state.graph
    snap = graph.get_state(rc())
    generated = snap.values.get("generated", {})
    matches_by_id = {m["job"]["id"]: m["job"] for m in snap.values.get("matches", [])}
    company_research = snap.values.get("company_research", {})

    st.header("3. Review & approve")
    if not generated:
        st.warning("Nothing was generated - go back and select at least one job.")
        return

    if st.button("Approve all pending"):
        for job_id, content in generated.items():
            if content["status"] == "pending":
                _apply_status(graph, job_id, content["cover_letter"], content["screening_answers"], "approved", content.get("comment", ""))
        st.rerun()

    for job_id, content in generated.items():
        job = matches_by_id[job_id]
        with st.expander(
            f"{job['title']} @ {job['company']} - status: {content['status']}",
            expanded=content["status"] == "pending",
        ):
            col_job, col_letter = st.columns(2)
            with col_job:
                st.markdown("**Original job description**")
                st.text_area("Job description", value=job["description"], height=250, disabled=True, key=f"jd_{job_id}")
                brief = company_research.get(job["company"])
                if brief:
                    st.markdown("**Company research**")
                    for k, v in brief.items():
                        if v and v != "Unknown":
                            st.caption(f"{k}: {v}")
            with col_letter:
                st.markdown(f"**Generated cover letter** (tone: {content.get('tone', 'Professional')})")
                letter = st.text_area("Cover letter", value=content["cover_letter"], key=f"letter_{job_id}", height=250)
                if st.button("Regenerate letter", key=f"regen_{job_id}"):
                    regenerate_cover_letter(graph, job_id, settings)

            answers = {}
            for q, a in content["screening_answers"].items():
                answers[q] = st.text_area(q, value=a, key=f"ans_{job_id}_{hash(q)}", height=80)

            comment = st.text_input("Reviewer comment", value=content.get("comment", ""), key=f"comment_{job_id}")

            c1, c2, c3 = st.columns(3)
            if c1.button("Approve", key=f"approve_{job_id}"):
                save_and_set_status(graph, job_id, letter, answers, "approved", comment)
            if c2.button("Save edit", key=f"edit_{job_id}"):
                save_and_set_status(graph, job_id, letter, answers, "pending", comment)
            if c3.button("Reject", key=f"reject_{job_id}"):
                save_and_set_status(graph, job_id, letter, answers, "rejected", comment)

    st.divider()
    approved_count = sum(1 for c in generated.values() if c["status"] == "approved")
    st.write(f"{approved_count} application(s) approved.")

    if settings["dry_run"]:
        if st.button("Finalize (dry run - nothing will be opened or marked submitted)", type="primary"):
            with st.spinner("Recording dry-run results..."):
                graph.invoke(None, rc())
            st.session_state.started = False
            st.rerun()
    else:
        confirm = st.text_input("Type SUBMIT to confirm you will personally complete these applications")
        if st.button("Finalize: open approved applications for submission", type="primary", disabled=confirm != "SUBMIT"):
            with st.spinner("Logging approved applications and opening job pages..."):
                graph.invoke(None, rc())
            st.session_state.started = False
            st.rerun()


def render_tracker() -> None:
    st.header("Application Tracker")
    applications = tracker.load_applications()
    if not applications:
        st.caption("No applications tracked yet.")
        return

    status_filter = st.multiselect("Filter by status", tracker.STATUSES, default=tracker.STATUSES)
    filtered = [a for a in applications if a["status"] in status_filter]

    st.dataframe(
        [
            {
                "Title": a["title"],
                "Company": a["company"],
                "Status": a["status"],
                "Follow-up": a.get("follow_up_date") or "-",
                "Notes": a.get("notes", ""),
            }
            for a in filtered
        ],
        use_container_width=True,
    )

    if st.button("Export to CSV"):
        path = tracker.export_csv()
        st.success(f"Exported to {path}")

    if not filtered:
        return

    st.subheader("Update an application")
    labels = [f"{a['title']} @ {a['company']}" for a in filtered]
    idx = st.selectbox("Application", range(len(filtered)), format_func=lambda i: labels[i])
    app_entry = filtered[idx]
    job_id = app_entry["job_id"]

    new_status = st.selectbox("Status", tracker.STATUSES, index=tracker.STATUSES.index(app_entry["status"]))
    note = st.text_input("Note for this status change", key=f"note_{job_id}")
    if st.button("Update status", key=f"update_status_{job_id}"):
        tracker.update_status(job_id, new_status, note)
        st.rerun()

    notes = st.text_area("Notes", value=app_entry.get("notes", ""), key=f"notes_{job_id}")
    if st.button("Save notes", key=f"save_notes_{job_id}"):
        tracker.set_note(job_id, notes)
        st.rerun()

    follow_up = st.date_input("Follow-up reminder date", value=None, key=f"followup_{job_id}")
    if st.button("Set follow-up", key=f"set_followup_{job_id}"):
        tracker.set_follow_up(job_id, follow_up.isoformat() if follow_up else None)
        st.rerun()

    with st.expander("Timeline"):
        for event in app_entry["timeline"]:
            note_suffix = f" ({event['note']})" if event.get("note") else ""
            st.write(f"{event['timestamp']} - {event['status']}{note_suffix}")


def render_logs() -> None:
    snap = st.session_state.graph.get_state(rc())
    log = snap.values.get("log", []) if snap.values else []
    with st.sidebar.expander("Logs", expanded=False):
        for line in log[-50:]:
            st.text(line)


def main() -> None:
    init_session()
    st.title("Autonomous Job Application Agent")
    choices = sidebar_model_config()
    settings = sidebar_settings()

    tab_pipeline, tab_tracker = st.tabs(["Pipeline", "Application Tracker"])

    with tab_pipeline:
        if st.session_state.started:
            render_logs()
            # LangGraph sets .next to the list of nodes the graph is paused before.
            # This is how the UI detects which of the two interrupt points was hit.
            next_nodes = st.session_state.graph.get_state(rc()).next
            if "generate_content" in next_nodes:
                render_selection()
            elif "human_approval" in next_nodes:
                render_approval(settings)
            else:
                st.success("Pipeline complete.")
                if st.button("Start a new run"):
                    # New UUID abandons the old LangGraph thread; MemorySaver retains
                    # its checkpoint in memory but it becomes unreachable. No explicit cleanup.
                    st.session_state.thread_id = str(uuid.uuid4())
                    st.session_state.started = False
                    st.rerun()
        else:
            render_intake(choices, settings)

    with tab_tracker:
        render_tracker()


if __name__ == "__main__":
    main()
