# Usage

A step-by-step walkthrough of the Streamlit app, plus troubleshooting. For
setup instructions, see the [README](README.md#installation--setup) first.

## Starting the app

- Windows one-click: double-click `run.cmd` (runs `uv sync`, then launches).
- Manual (any OS): `uv sync --frozen` once, then `uv run streamlit run app.py`.

Either way, open the URL Streamlit prints — `http://localhost:8843` (the
port `run.cmd` and the project both use; Streamlit's own default is 8501 if
you launch it a different way).

## Sidebar: Model configuration

- **Local model (Ollama)** — used for resume parsing, job matching, and the
  first-pass draft of cover letters/screening answers. The dropdown lists
  whatever models `ollama serve` reports on `OLLAMA_HOST`
  (`config.list_ollama_models()`). If it shows "No Ollama models found",
  start Ollama and pull at least one model (`ollama pull llama3.1`), then
  reload the page.
- **Final polish provider** — one of OpenAI-compatible, Agnes AI, or Google
  Gemini. This model only runs the final polish pass on drafted content; it
  never touches resume parsing or job matching. Pick a provider and the app
  tells you immediately if the matching API key isn't set in your `.env`.

## Sidebar: Generation & safety settings

- **Cover letter tone** — Professional, Enthusiastic, Concise, or
  Story-driven.
- **Location preference** — fed into the location-match scoring factor.
- **Dry run** (default **on**) — generates and records everything, but
  never opens a browser tab or marks an application "Submitted."
- **Delay between requests** — pause used between career-page fetches and
  between opening approved job pages, to avoid hammering a site.
- **Company career page URLs** — optional, one per line. Alongside the
  selected job boards, the agent will also try to extract postings from
  each URL via LLM-based page parsing.

Turning dry run **off** shows a warning: approved applications will open in
your browser for you to submit yourself. The app never fills in or submits
a third-party form on your behalf.

## Pipeline tab

### 1. Resume & job search

1. Upload a resume (PDF or DOCX). It's saved locally to
   `data/uploads/<original filename>`.
2. Enter keywords and a location.
3. Pick job boards (`linkedin`, `indeed`, `naukri`, `zip_recruiter`,
   `glassdoor`, `wellfound`) and an experience level.
4. Set how many results you want per board (5–50).
5. Edit the screening questions if the defaults don't fit
   (`config.DEFAULT_SCREENING_QUESTIONS`).
6. Click **Run: parse resume -> scrape jobs -> match**. This is the first
   LangGraph invocation — it parses the resume, scrapes/aggregates jobs
   from every selected source concurrently, deduplicates them, and scores
   every match. The graph pauses immediately after (`interrupt_before`),
   so nothing downstream runs until you act in the next section.

### 2. Matched jobs

Each match shows the overall score, a six-factor breakdown (skills,
experience, domain, keywords, seniority, location), pros/cons, skill gaps,
and resume improvement suggestions. An expander above the list shows your
parsed resume profile (total experience, role count, quantified
achievements, categorized skills).

Check the jobs you want drafted content for (pre-checked when overall score
is ≥70), then click **Generate cover letters & answers for selected jobs**.
This resumes the graph: it fetches/caches a company research brief per
company, drafts locally, then polishes with your configured provider. The
graph pauses again before the approval step.

### 3. Review & approve

For each generated application, you get the original job description and
company research side by side with the drafted cover letter and screening
answers. You can:

- edit the cover letter or any answer inline;
- click **Regenerate letter** to redraft just that one;
- add a reviewer comment;
- **Approve**, **Save edit** (keeps status pending), or **Reject** —
  individually, or **Approve all pending** in one click.

When you're done reviewing:

- **Dry run on**: click **Finalize (dry run)** — this just records the
  outcome; nothing opens or gets marked "Submitted."
- **Dry run off**: type `SUBMIT` in the confirmation box, then click
  **Finalize: open approved applications for submission**. Each approved
  job's listing opens in your browser, and its tracker status becomes
  "Submitted." You still submit the actual application yourself.

After finalizing, click **Start a new run** to begin a fresh
resume/search cycle with a new session thread.

## Application Tracker tab

Every generated application is tracked through Draft → Approved →
Submitted → Interview → Rejected → Offer (`tools/tracker.py`,
`data/tracker.json`).

- Filter the table by status.
- Select an application to update its status, add a note, or set a
  follow-up reminder date.
- Expand **Timeline** to see every status change with its timestamp and
  note.
- Click **Export to CSV** to write `data/application_history.csv`.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| "No Ollama models found" in the sidebar | `ollama serve` isn't running, or no model has been pulled. Run `ollama pull llama3.1` (or any model), confirm `ollama serve` is up, then reload the page. |
| Sidebar shows "`<PROVIDER>_API_KEY` not set in environment" | Add the key to `.env` (copy from `.env.example` if you haven't) and restart the app — `.env` is only loaded at process start. |
| `uv sync` fails on `python-jobspy` / numpy | Shouldn't happen — `pyproject.toml`'s `[tool.uv].override-dependencies` resolves this automatically. If it does, check that override is still present and re-run `uv lock`. |
| No jobs come back from a run | Try broadening keywords/location, adding more boards, or raising "Results per board." Some boards occasionally return zero results for narrow searches. |
| Wellfound or a career-page URL returns nothing | Both paths are best-effort scraping (no official API for Wellfound; career pages vary in structure). Try a different URL or rely on the job-board sources instead. |
| Live mode did nothing after clicking Finalize | Confirm you typed `SUBMIT` exactly (case-sensitive) in the confirmation box — the button stays disabled otherwise. |
| Uploaded resume fields look wrong in the profile expander | Resume parsing quality depends on your selected local model and the resume's own formatting. Try a different local model, or simplify the resume's layout. |

For anything not covered here, see [SUPPORT.md](SUPPORT.md).
