# Architecture

Audited against local checkout `0d328db9d8dbbfaffe5104c19c1ae7732e3d81dd` on `main`
(remote `https://github.com/pypi-ahmad/autonomous-job-application-agent.git`), 2026-08-17.
Local license: MIT (`LICENSE`). This document is cited to files in this checkout;
see [Footnotes](#footnotes) for the full list.

> **Updated 2026-08-17 (same day, later commit):** [MODERNIZATION_PLAN.md](MODERNIZATION_PLAN.md)'s
> Phase 1 has since been executed. The tooling/CI sections below (Commands &
> Verification Inventory, Deployment & Runtime Surface, Data/APIs/CI/testing,
> Governance, Confidence assessment) have been corrected in place to reflect
> that; everything else in this document (pipeline, scraping/dedup, matching)
> is unaffected and unchanged.

## Part 1 — Whole-repo technical deep-dive

**What this is.** A local, single-user Streamlit application that runs a LangGraph
state-machine pipeline: parse a resume, scrape job boards, score matches, draft and
polish application content, pause twice for human review, then either log a dry-run
result or open approved listings in the browser for manual submission (README.md:3,
graph.py:129-149).

### Tech stack

| Layer | Technology | Evidence |
|---|---|---|
| UI | Streamlit | `app.py:8,20` |
| Orchestration | LangGraph `StateGraph` + `MemorySaver` checkpointer, 2 interrupt points | `graph.py:8-9,146-149` |
| LLM integration | LangChain (`langchain-core`, `-openai`, `-google-genai`, `-ollama`) | `tools/llm_factory.py:6-8`, `pyproject.toml` dependencies |
| Job scraping | `python-jobspy` (LinkedIn/Indeed/Naukri/ZipRecruiter/Glassdoor), custom Wellfound + career-page scrapers | `tools/job_scraper.py:9,17`, `tools/wellfound_scraper.py`, `tools/career_page_scraper.py` |
| Resume parsing | `pypdf`, `python-docx` | `parsers/resume_parser.py:13-15` |
| Persistence | flat JSON (`data/tracker.json`) + CSV export, no database | `tools/tracker.py:10,80` |
| Config | `python-dotenv`, plain `os.environ` reads | `config.py:8-21` |

### Entry point

`streamlit run app.py` (README.md:98) or `run.cmd` (Windows one-click: creates
`.venv`, installs deps, copies `.env.example` → `.env`, launches — README.md:75-80).
`app.py:392-422` is the only UI entry point; there is no CLI or API entry point.

### Commands & Verification Inventory

| Command | Purpose | Evidence |
|---|---|---|
| `uv sync --frozen` | Install every pinned dependency from `uv.lock`, including `python-jobspy` (numpy conflict resolved via `[tool.uv].override-dependencies`, no separate step) | `pyproject.toml`, `uv.lock` |
| `uv run streamlit run app.py` | Run the app | README.md |
| `run.cmd` | Windows one-click setup + launch (`uv sync` then `uv run streamlit`) | `run.cmd` |
| `uv run ruff check .` | Lint (scoped to `E`/`F` for this first pass — see `pyproject.toml` `[tool.ruff.lint]` comment) | `pyproject.toml`, `.github/workflows/ci.yml` |
| `uv run pytest -v` | Run the test suite | `tests/`, `.github/workflows/ci.yml` |

**CI now exists and is green:** `.github/workflows/ci.yml` runs `uv sync --frozen
--all-groups` → `ruff check .` → `pytest -v` on every push/PR to `main`, Python
3.13. First run succeeded 2026-08-17. **Not yet enforced**: turning it into a
required status check is a manual GitHub → Settings → Branches step, not done
by this pass (see MODERNIZATION_PLAN.md § 9).

**Test suite:** four `pytest` tests in `tests/` — `test_utils.py`,
`test_dedup.py`, `test_resume_advisor.py`, `test_matcher.py` — converted
verbatim from the project's original `demo()` self-checks (same assertions).
They cover deterministic logic only (dedup, resume-profile analytics, the
matcher's non-LLM keyword-overlap path via a stub LLM). LLM-integration paths
(resume parsing, drafting, company research, matcher's LLM-judged factors) and
live scraping are **not** covered by CI — deliberately, to avoid committing
test API keys or making live network calls from CI (see
MODERNIZATION_PLAN.md § 3, economic triage). Those paths are covered only by
the manual verification checklist in `CONTRIBUTING.md`.

### Directory layout

| Path | Purpose |
|---|---|
| `app.py` | Streamlit UI: sidebar config, 3-step pipeline tab, tracker tab |
| `graph.py` | LangGraph node functions + `build_graph()` |
| `state.py` | `AgentState`/`GeneratedContent` `TypedDict` schema |
| `config.py` | Env var reads, model/site constants, `list_ollama_models()` |
| `utils.py` | Logging setup, `strip_code_fences()` (LLMs sometimes wrap JSON in markdown fences) |
| `agents/matcher.py` | Multi-factor match scoring (5 LLM-judged factors + 1 deterministic) |
| `agents/writer.py` | Cover-letter/screening-answer drafting + polishing prompts |
| `agents/resume_advisor.py` | Pure-function resume-profile analytics (no LLM) |
| `parsers/resume_parser.py` | PDF/DOCX text extraction + LLM structuring |
| `tools/llm_factory.py` | Provider → `BaseChatModel` construction |
| `tools/job_scraper.py` | Parallel multi-source aggregation + dedup |
| `tools/wellfound_scraper.py` | Best-effort Wellfound SSR-payload scraping |
| `tools/career_page_scraper.py` | LLM-based career-page job extraction |
| `tools/dedup.py` | Cross-source near-duplicate merging (O(n²), by design at this scale) |
| `tools/company_research.py` | DuckDuckGo HTML scraping + LLM synthesis |
| `tools/tracker.py` | JSON-file CRM: status lifecycle, timeline, CSV export |
| `data/` | Runtime-only: uploads, `tracker.json`, CSV export. Not committed. |
| `tests/` | `pytest` suite: `test_utils.py`, `test_dedup.py`, `test_resume_advisor.py`, `test_matcher.py` |
| `pyproject.toml` / `uv.lock` | Project metadata, pinned dependencies (`uv`) |
| `.python-version` | Pins Python 3.13 for `uv` (local and CI) |
| `.github/workflows/ci.yml` | Lint (`ruff`) + test (`pytest`) on push/PR to `main` |

### Deployment & Runtime Surface

Local-only; no container, no deployed service. A CI runner image now exists:
`.github/workflows/ci.yml` runs on GitHub's `ubuntu-latest`, Python 3.13 only
(matrix widening to 3.11/3.12 deferred — see MODERNIZATION_PLAN.md § 9).
`README.md` badges Python 3.11+ as the floor; `.python-version` now pins the
dev/CI interpreter to 3.13 exactly, so the README's stated floor and the
enforced version are two different numbers by design (3.11 is the claimed
minimum, 3.13 is what's actually tested).

### EOL / dead-dependency scan

Nothing EOL. Dependencies are now version-pinned in `uv.lock`, so this can be
checked directly rather than inferred: LangGraph, LangChain, Streamlit, and the
provider SDKs all resolved to current-generation releases at lock time
(2026-08-17). The one known-fragile dependency is intentional and documented:
`python-jobspy` declares `numpy==1.26.3`, incompatible with modern Python on
Windows — resolved via `[tool.uv].override-dependencies = ["numpy>=2.1"]` in
`pyproject.toml`, which resolves to numpy 2.5.2 today (verified live,
2026-08-17) instead of the manual `--no-deps` step this document previously
described. `tools/wellfound_scraper.py:1-6` and `tools/career_page_scraper.py:1-6`
self-document as best-effort/fragile by design (scrape a JS SSR payload /
arbitrary page markup with no stable contract) — that remains true and
unaffected by the dependency-tooling change.

### Data, APIs, background jobs, CI/CD, testing

- **Data:** flat JSON file (`data/tracker.json`) is the only persistence; no
  database, no schema migrations possible or needed at this scale (`tools/tracker.py`).
- **APIs:** none exposed by this app; it is a client of four LLM provider APIs
  (OpenAI-compatible, Agnes AI, Google Gemini, local Ollama — `tools/llm_factory.py:13-36`)
  and scrapes public job-board/search HTML.
- **Background jobs:** none; `ThreadPoolExecutor` is used only for one-shot
  parallel fan-out within a single scrape call (`tools/job_scraper.py:79-89`), not
  a persistent worker.
- **CI/CD:** `.github/workflows/ci.yml` — lint + test on push/PR to `main`,
  green on first run; not yet an enforced required status check (see Commands
  inventory above).
- **Testing:** four `pytest` tests collected and passing in CI, covering
  deterministic logic only; LLM-integration and live-scraping paths remain
  manual-only (see Commands inventory above).

## Part 2 — Context & ecosystem

**Identity:** remote `pypi-ahmad/autonomous-job-application-agent`, branch `main`,
HEAD `0d328db9`, MIT-licensed, public.

**Repo-specific contributor docs (added this session, not by this pass):**
`CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, `DISCLAIMER.md`. `CONTRIBUTING.md`
already states the two rules any modernization work here must preserve: keep the
project local-first (no telemetry/hosted backend) and preserve the dry-run/`SUBMIT`
safety gate (`CONTRIBUTING.md`).

**Developer gotchas:**
- `python-jobspy`'s numpy conflict is now handled declaratively by `uv`'s
  dependency override (`pyproject.toml`) — a plain `uv sync` resolves it. If
  you ever add a `pip install`-based workflow alongside `uv`, the old
  `--no-deps python-jobspy` step would be needed again in that path only.
- `agents/matcher.py:13-15` and `tools/dedup.py:8-10` both carry `ponytail:`
  comments naming a known scaling ceiling (sequential per-job LLM calls;
  O(n²) dedup) that's fine at the app's current "hundreds of jobs" scale but
  would need revisiting if that scale changes materially.
- `tools/tracker.py:80` and `app.py:22-23` both hardcode `data/...` relative
  paths — the app must be run from the repo root.

**Ecosystem:** standalone; no sibling services, no shared package, no monorepo.

## Part 3 — Architectural blueprint

```mermaid
flowchart TD
    UI[Streamlit UI\napp.py] -->|invoke/update_state| G[LangGraph StateGraph\ngraph.py]
    G --> P[parse_resume]
    P --> S[scrape_jobs]
    S --> M[match_jobs]
    M -->|interrupt| SEL[UI: pick jobs to draft]
    SEL --> GC[generate_content]
    GC -->|interrupt| APP[UI: review/edit/approve]
    APP --> SUB[submit]
    SUB -->|dry_run| TR[(tracker.json)]
    SUB -->|live, approved| BR[Open listing in browser]
    BR --> TR
```

```mermaid
flowchart LR
    S[scrape_jobs] --> JS[python-jobspy\nLinkedIn/Indeed/Naukri/ZipRecruiter/Glassdoor]
    S --> WF[wellfound_scraper]
    S --> CP[career_page_scraper]
    JS & WF & CP --> DD[dedup.dedupe_jobs]
    DD --> OUT[list of unique jobs]
```

**Layering:** `app.py` (UI) → `graph.py` (orchestration) → `agents/` + `tools/` +
`parsers/` (domain logic) → `config.py` (env). Nothing in `agents/`, `tools/`, or
`parsers/` imports `app.py` or `graph.py` — the dependency direction is one-way,
enforced only by convention (no import-linter/architecture test exists).

**Cross-cutting concerns**

| Concern | Location | Evidence |
|---|---|---|
| Config/secrets | `.env` via `python-dotenv`, read once at import time | `config.py:8-21` |
| Logging | stdlib `logging`, one shared `"job_agent"` logger | `utils.py:8-10`, used across `tools/*.py` |
| Error handling | broad `except Exception` around every network call, logged and degraded to `[]`/empty dict | `tools/job_scraper.py:83-88`, `tools/wellfound_scraper.py:33-43`, `tools/career_page_scraper.py:37-42`, `tools/company_research.py:39-50` |
| Safety gate | dry-run default + typed `SUBMIT` confirmation + browser-open-only (never auto-fill/auto-submit) | `graph.py:102-126`, `app.py:310-322` |

**Inferred ADRs**

- **ADR: Draft locally, polish remotely.** *Context:* cover letters/answers need
  both cost control and quality. *Decision:* draft with a free local Ollama model,
  polish with one configured paid API model (`app.py:98-108`, `graph.py:52-95`).
  *Consequences:* quality depends on the local model's draft; failure of the local
  Ollama server blocks the whole `generate_content` step.
- **ADR: Never auto-submit.** *Context:* automating real submission needs per-site
  login + CAPTCHA handling and risks ToS violations. *Decision:* open the listing
  in the browser for the human to submit (`graph.py:117-120`, comment in source).
  *Consequences:* the tracker's "Submitted" status only ever means "opened," not
  "confirmed sent" — a known, documented limitation, not a bug.
- **ADR: Deterministic keyword score alongside LLM judgment.** *Context:* trusting
  an LLM for every match factor makes the score unauditable. *Decision:* compute
  `keywords` via Jaccard-style token overlap in code; let the LLM judge the other
  five factors (`agents/matcher.py:37-44,106-113`). *Consequences:* one factor is
  fully explainable/reproducible; the other five vary run-to-run.

**Governance:** `.github/workflows/ci.yml` exists and runs, but no CODEOWNERS
and no branch protection / required status check — CI runs on every push/PR
but does not yet block merges (manual step, see MODERNIZATION_PLAN.md § 9).

**How to add a feature:** add/modify a node function in `graph.py`, wire it into
`build_graph()`'s edges, extend `AgentState` in `state.py` if new fields are
needed, and update `README.md`'s "How It Works" pipeline diagram and project
structure tree in the same change (nothing currently enforces this — it's
convention only).

## Subsystem deep-dives

### 1. The LangGraph pipeline (`graph.py`)

Six nodes in a strict linear chain with two `interrupt_before` pause points
(`graph.py:129-149`). State is a single `TypedDict` (`state.py:18-29`) threaded
through every node and persisted by `MemorySaver`, keyed on a UUID `thread_id`
stored in `st.session_state` (`app.py:29-30,37-38`) — so state survives Streamlit's
rerun-on-every-interaction model. `log` is the one field with a reducer
(`operator.add`, `state.py:29`); every other field is fully overwritten by each
node's return dict. `node_human_approval` (`graph.py:98-99`) is a deliberate no-op
— it exists only to be an interrupt point the UI can detect via `graph.get_state(rc()).next`
(`app.py:403-407`).

### 2. Multi-source job aggregation + dedup (`tools/job_scraper.py`, `tools/dedup.py`)

Three independent sources run concurrently via `ThreadPoolExecutor`
(`tools/job_scraper.py:79-89`): `python-jobspy` for the five mainstream boards,
a custom Wellfound scraper, and an LLM-based career-page extractor. Each source
fails independently and silently degrades to `[]` on exception — one source
failing never blocks the others. Results merge into one list, then
`dedupe_jobs()` (`tools/dedup.py:16-40`) does company-exact-match +
title-fuzzy-match (`difflib.SequenceMatcher`, threshold 0.88) to merge
cross-source duplicates into a `sources: [...]` list on one surviving record.
This is O(n²) by construction — a documented, accepted ceiling at "hundreds of
jobs" scale (`tools/dedup.py:8-10`).

### 3. Multi-factor match scoring (`agents/matcher.py`)

One LLM call per job returns five 0-100 factor scores plus pros/cons/gaps/
suggestions as JSON (`agents/matcher.py:52-104`); a sixth factor (`keywords`) is
computed deterministically via token-overlap before the weighted sum
(`agents/matcher.py:37-44,106-114`, weights at lines 16-23). This hybrid — one
factor grounded in code, five in LLM judgment — trades full explainability for
judgment quality on the harder-to-formalize factors (domain fit, seniority fit).

## Confidence assessment

| Claim area | Confidence |
|---|---|
| Pipeline structure, node responsibilities, interrupt points | High — read directly from `graph.py` |
| CI exists and passed on its first run | High — `.github/workflows/ci.yml` authored this pass, observed green via `gh run list` 2026-08-17 |
| Matching formula and weights | High — read directly from `agents/matcher.py` |
| Dependency versions being "current" (no EOL) | High — `uv.lock` now pins exact versions; resolved clean against current PyPI at lock time |
| CI enforcement (required status check) status | Confirmed absent — not yet configured; this is a manual GitHub Settings step, not an agent task |
| Scale ceilings (O(n²) dedup, sequential LLM calls) being acceptable today | High — directly stated in source comments by the original author, re-confirmed by re-reading the code paths |

## Footnotes

- `README.md` — features, tech stack, setup, env vars, architecture narrative
- `graph.py` — LangGraph node functions and `build_graph()`
- `state.py` — `AgentState`/`GeneratedContent` schema
- `config.py` — env var reads and constants
- `app.py` — Streamlit UI and pipeline wiring
- `agents/matcher.py`, `agents/writer.py`, `agents/resume_advisor.py` — matching, drafting, resume analytics
- `parsers/resume_parser.py` — resume text extraction and structuring
- `tools/job_scraper.py`, `tools/wellfound_scraper.py`, `tools/career_page_scraper.py`, `tools/dedup.py`, `tools/company_research.py`, `tools/tracker.py`, `tools/llm_factory.py` — scraping, dedup, research, persistence, provider construction
- `utils.py` — logging setup and LLM-output cleanup
- `pyproject.toml`, `uv.lock` — pinned dependency list and lockfile
- `.github/workflows/ci.yml` — CI: lint + test on push/PR to `main`
- `tests/` — pytest suite converted from the original `demo()` self-checks
- `CONTRIBUTING.md` — safety-gate and local-first rules this plan must preserve
