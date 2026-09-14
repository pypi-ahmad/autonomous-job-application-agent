# Autonomous Job Application Agent

A LangGraph-powered, human-in-the-loop agent that scrapes jobs from multiple sources, scores them against your resume, drafts tailored application content, and tracks every application through a CRM-style dashboard — all from a local Streamlit app.

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)
![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-1c3c3c)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

**Repository:** [github.com/pypi-ahmad/autonomous-job-application-agent](https://github.com/pypi-ahmad/autonomous-job-application-agent)

## Contents

- [Open source and community](#open-source-and-community)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [How It Works (Architecture)](#how-it-works-architecture)
- [Configuration Options](#configuration-options)
- [Future Improvements](#future-improvements)
- [Documentation](#documentation)
- [License](#license)

## Open source and community

This is a free, open-source (MIT), community-driven project. Cloning,
forking, testing, filing bugs, suggesting features, and sending pull
requests are all welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and
[SUPPORT.md](SUPPORT.md). This project does not want or accept donations,
sponsorship, or paid support of any kind; testing and patches are worth
more here than money.

You run this entirely on your own machine with your own API keys. Nobody
but you sees your resume, generated content, job search results, or
tracker data — and you are responsible for everything you process with it,
including compliance with each job board's terms of service. See
[DISCLAIMER.md](DISCLAIMER.md) for the full breakdown, and
[SECURITY.md](SECURITY.md) for how to report a vulnerability.

> [!IMPORTANT]
> Dry-run mode is on by default. Live mode still requires typing `SUBMIT`
> and only opens the job listing in your browser — this agent never
> auto-fills or auto-submits a third-party site's application form.

## Features

- **Multi-source job aggregation** — LinkedIn, Indeed, Naukri, ZipRecruiter, and Glassdoor via [`python-jobspy`](https://github.com/cullenwatson/JobSpy), plus best-effort Wellfound scraping and LLM-based extraction from any company careers page you paste in. All sources are fetched in parallel and cross-source duplicates are merged.
- **Deep resume intelligence** — PDF/DOCX parsing into a structured profile: categorized skills, an experience timeline with computed duration per role, and a separate list of quantified achievements.
- **Explainable multi-factor matching** — every job gets a 0–100 score built from six weighted, individually-visible factors (skills, experience, domain, keywords, seniority, location), plus pros/cons, skill gaps, and resume improvement suggestions.
- **Two-stage content generation** — a local Ollama model drafts cover letters and screening-question answers, then your chosen API model (OpenAI-compatible, Agnes AI, or Gemini) polishes the final version. Four selectable tones, and automatic company-research context injection.
- **Company research agent** — pulls a short brief (recent news, culture, products, funding) per company from web search and works it into generated content where relevant.
- **Human-in-the-loop approval** — the pipeline pauses twice: once to let you pick which matches to draft, and once to review. Side-by-side job description vs. generated letter, inline editing, reviewer comments, per-job regeneration, and batch approval.
- **Application tracker / CRM** — every generated application is tracked through Draft → Approved → Submitted → Interview → Rejected → Offer, with a timeline, notes, follow-up reminders, and CSV export.
- **Safety-first submission** — dry-run mode is on by default (nothing is opened or marked submitted). Live mode requires typing `SUBMIT` to confirm, and even then the agent only opens the job listing in your browser for you to submit — it never auto-fills or auto-submits a third-party site's form.
- **Fully local-first model routing** — dynamically lists whatever models you have installed in Ollama; cloud models are used only for the final polish step, and only the two you explicitly configure.

## Demo / Screenshots

_No screenshots included yet — add PDFs/GIFs of the Pipeline and Application Tracker tabs here._

## Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io/) |
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) (state machine + interrupt-based human-in-the-loop, `MemorySaver` checkpointer) |
| LLM integration | [LangChain](https://github.com/langchain-ai/langchain) (`langchain-openai`, `langchain-google-genai`, `langchain-ollama`) |
| Job scraping | [`python-jobspy`](https://github.com/cullenwatson/JobSpy), `requests` + `BeautifulSoup` (Wellfound, career pages, company research) |
| Resume parsing | `pypdf`, `python-docx` |
| Data handling | `pandas`, stdlib `json`/`csv` |
| Config | `python-dotenv` |
| Tooling | [`uv`](https://docs.astral.sh/uv/) (deps + lockfile), `pytest`, `ruff` (lint), GitHub Actions (CI) |

## Project Structure

```
Autonomous Job Application Agent/
├── app.py                       # Streamlit UI - entry point
├── graph.py                     # LangGraph state machine (nodes + interrupts)
├── state.py                     # Shared TypedDict state schema
├── config.py                    # Env-driven configuration & constants
├── utils.py                     # Logging + LLM-output cleanup helpers
├── pyproject.toml                # Project metadata + dependencies (uv)
├── uv.lock                       # Locked dependency versions
├── run.cmd                      # One-click Windows setup + launch
├── .env.example
├── agents/
│   ├── matcher.py                # Multi-factor job/resume match scoring
│   ├── writer.py                 # Cover letter / screening-answer generation
│   └── resume_advisor.py         # Resume profile analytics
├── parsers/
│   └── resume_parser.py          # PDF/DOCX -> structured resume profile
├── tools/
│   ├── llm_factory.py            # Builds a chat model per provider
│   ├── job_scraper.py            # Multi-source aggregation orchestrator
│   ├── wellfound_scraper.py      # Best-effort Wellfound scraping
│   ├── career_page_scraper.py    # LLM-based career-page job extraction
│   ├── dedup.py                  # Cross-source job deduplication
│   ├── company_research.py       # Company research brief generator
│   └── tracker.py                # Application CRM persistence
└── data/                         # Created at runtime, not committed
    ├── uploads/                   # Uploaded resumes
    ├── tracker.json                # CRM state
    └── application_history.csv     # CSV export (on demand)
```

## Installation & Setup

Requires [`uv`](https://docs.astral.sh/uv/) (installs and pins Python 3.13 automatically per `.python-version`).

### Option A — one-click (Windows)

1. Double-click **`run.cmd`**.
2. It will: run `uv sync` (installing Python 3.13 and every dependency from the locked `uv.lock` if needed), copy `.env.example` to `.env` on first run, and launch the app.
3. Open the URL Streamlit prints (`http://localhost:8843`).
4. Edit `.env` with your API keys, then re-run `run.cmd`.

### Option B — manual (any OS)

```bash
uv sync --frozen
cp .env.example .env   # then fill in your keys
uv run streamlit run app.py
```

`uv sync` resolves `python-jobspy`'s dependencies with a numpy override declared
in `pyproject.toml`'s `[tool.uv]` section — no separate `--no-deps` step needed.

> `run.cmd` is Windows-only. macOS/Linux users should follow Option B (only Windows has been tested for this project).

### Optional: local models

Install [Ollama](https://ollama.com/) and pull at least one model (e.g. `ollama pull llama3.1`) so the "Local model" dropdown has something to list. Ollama must be running (`ollama serve`) when you launch the app.

## Environment Variables

Set these in `.env` (copied from `.env.example`). All keys are read from the environment — none are hardcoded.

| Variable | Required for | Notes |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI-compatible polish models | Used with `gpt-5.6-luna` / `gpt-5.6-terra` |
| `OPENAI_BASE_URL` | OpenAI-compatible polish models | Defaults to `https://api.openai.com/v1`; point it at any OpenAI-compatible endpoint |
| `AGNES_API_KEY` | Agnes AI polish model | Fixed model `agnes-2.5-flash`, base URL `https://apihub.agnes-ai.com/v1` |
| `GOOGLE_API_KEY` | Google Gemini polish models | Used with `gemini-3.5-flash-lite` / `gemini-3.7-flash` |
| `OLLAMA_HOST` | Local models | Defaults to `http://localhost:11434`; only needed if Ollama runs elsewhere |

## Usage

See [USAGE.md](USAGE.md) for the full walkthrough with troubleshooting.
Short version:

1. **Configure models** (sidebar) — pick a local Ollama model for parsing/matching/drafting, and a provider + model for the final polish pass (OpenAI-compatible, Agnes AI, or Google Gemini).
2. **Configure generation & safety settings** (sidebar) — cover letter tone, location preference, dry-run toggle (on by default), delay between requests, and optional career page URLs.
3. **Pipeline tab → Resume & job search** — upload a PDF/DOCX resume, set keywords, location, job boards, experience level, results per board, and screening questions, then click **Run**. This parses your resume, scrapes/aggregates jobs, and scores every match.
4. **Matched jobs** — review each job's overall score and per-factor breakdown, pros/cons, skill gaps, and resume suggestions. Select which jobs to draft content for, then click **Generate**.
5. **Review & approve** — for each job, compare the original description and company research against the generated cover letter and screening answers side by side. Edit inline, add a reviewer comment, regenerate the letter, and Approve / Save edit / Reject — individually or via **Approve all pending**.
6. **Finalize** — in dry-run mode, this just records results. In live mode, you must type `SUBMIT` to confirm; approved jobs then open in your browser for you to submit manually.
7. **Application Tracker tab** — filter by status, update status/notes/follow-up dates, view each application's timeline, and export everything to CSV.

## How It Works (Architecture)

The pipeline is a single LangGraph `StateGraph` (`graph.py`) with a `MemorySaver` checkpointer, so state survives across Streamlit reruns via a `thread_id` stored in `st.session_state`:

```
parse_resume → scrape_jobs → match_jobs → [pause] → generate_content → [pause] → human_approval → submit
```

- **Pause 1** (`interrupt_before="generate_content"`): the UI shows scored matches; the user picks which ones to draft.
- **Pause 2** (`interrupt_before="human_approval"`): the UI shows generated content for review/edit/approval.

Node responsibilities:
- `parse_resume` — extracts resume text (`pypdf`/`python-docx`) and asks the local model to structure it (categorized skills, experience timeline, quantified achievements).
- `scrape_jobs` — runs jobspy, Wellfound, and career-page fetches concurrently, then deduplicates the combined results.
- `match_jobs` — scores every job (see below) and sorts by overall match.
- `generate_content` — for each selected job, fetches/caches a company research brief, drafts locally, then polishes with the configured API model.
- `human_approval` — no-op node; exists purely as the second interrupt point.
- `submit` — for approved jobs, either logs a dry-run record or opens the listing in your browser and marks it "Submitted" in the tracker.

**Matching formula**: `overall = 0.30·skills + 0.20·experience + 0.15·domain + 0.15·keywords + 0.10·seniority + 0.10·location`. The `keywords` factor is computed deterministically (token overlap between resume and job description); the rest come from a single structured LLM call per job that also returns pros/cons, skill gaps, and resume suggestions.

## Configuration Options

| Setting | Where | Effect |
|---|---|---|
| Local model | Sidebar | Any Ollama model detected on `OLLAMA_HOST`; used for parsing, matching, and drafting |
| Polish provider/model | Sidebar | OpenAI-compatible (`gpt-5.6-luna`/`gpt-5.6-terra`, reasoning effort = medium), Agnes AI (`agnes-2.5-flash`), or Gemini (`gemini-3.5-flash-lite`/`gemini-3.7-flash`) |
| Cover letter tone | Sidebar | Professional, Enthusiastic, Concise, Story-driven |
| Location preference | Sidebar | Fed into the location-match factor |
| Dry run | Sidebar | On by default — nothing is opened or marked "Submitted" until turned off |
| Delay between requests | Sidebar | Applied between career-page fetches and between opening approved job pages |
| Career page URLs | Sidebar | Optional list of company careers pages to scrape alongside job boards |
| Job boards | Pipeline tab | `linkedin`, `indeed`, `naukri`, `zip_recruiter`, `glassdoor`, `wellfound` |
| Screening questions | Pipeline tab | Editable, one per line; defaults are in `config.DEFAULT_SCREENING_QUESTIONS` |

## Examples

A filled-in `.env` for using OpenAI-compatible polish models plus a local Ollama model:

```
OPENAI_API_KEY=sk-...your-key...
OPENAI_BASE_URL=https://api.openai.com/v1
AGNES_API_KEY=
GOOGLE_API_KEY=
OLLAMA_HOST=http://localhost:11434
```

Example career-page URL input (sidebar, one per line):

```
https://www.example-startup.com/careers
https://jobs.another-company.com
```

## Future Improvements

- Official ATS API integrations (e.g. Greenhouse, Lever) for genuine one-click submission instead of "open in browser"
- Batched/async matching to handle very large result sets faster
- An official Wellfound API integration if/when one becomes available (current scraper is best-effort)
- A cross-platform launch script (`run.sh`) alongside `run.cmd`
- Wider CI Python matrix (currently 3.13 only; README's floor is 3.11)
- CI test coverage for the LLM-integration and live-scraping paths (currently
  quarantined from CI — manual smoke test only, see CONTRIBUTING.md)
- User-adjustable match-factor weights in the UI

## Documentation

| Document | What it is |
|---|---|
| [USAGE.md](USAGE.md) | Step-by-step walkthrough of every tab and setting, plus troubleshooting |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Cited technical deep-dive: pipeline, scraping/dedup, and matching subsystems |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Concise architecture reference: pipeline diagram, node responsibilities, external systems |
| [docs/TECHNICAL.md](docs/TECHNICAL.md) | Stack rationale, invariants, error-handling patterns, and persistence paths |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Start/stop commands, common failures and fixes, log locations |
| [MODERNIZATION_PLAN.md](MODERNIZATION_PLAN.md) | Tooling/CI modernization plan and its status |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to set up, test, and send a PR |
| [SUPPORT.md](SUPPORT.md) | How to get help and report bugs |
| [SECURITY.md](SECURITY.md) | How to report a vulnerability |
| [DISCLAIMER.md](DISCLAIMER.md) | No-warranty, data responsibility, and job-board terms-of-service notes |
| [LICENSE](LICENSE) | MIT license text |

This project does not want or accept donations, sponsorship, or paid
support of any kind.

## License

[MIT](LICENSE)

## Acknowledgements

- [LangGraph](https://github.com/langchain-ai/langgraph) and [LangChain](https://github.com/langchain-ai/langchain)
- [Streamlit](https://streamlit.io/)
- [python-jobspy](https://github.com/cullenwatson/JobSpy) by Cullen Watson
- [Ollama](https://ollama.com/)
- DuckDuckGo's HTML search endpoint (used, without an API key, for company research)

<p align="center">Made with ❤️ by Ahmad Mujtaba</p>
