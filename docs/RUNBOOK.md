# Runbook

## Start

**Windows (one-click):**
```
run.cmd
```
Runs `uv sync`, copies `.env.example` → `.env` on first run, and launches the Streamlit app.

**Any OS (manual):**
```bash
uv sync --frozen
uv run streamlit run app.py
```

Open the URL Streamlit prints in the terminal.

Ollama must also be running if you want to use local models (required for parsing, matching, and drafting):
```
ollama serve
```

## Stop

Ctrl+C in the terminal running Streamlit. Ollama can be stopped with Ctrl+C in its own terminal, or left running between sessions.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| Sidebar: "No Ollama models found" | `ollama serve` not running, or no model has been pulled | Start Ollama; run `ollama pull <model-name>` if no models are installed; reload the page |
| Sidebar: "`<PROVIDER>_API_KEY` not set" | Key missing from `.env` | Add the key to `.env` and **restart the app** — `.env` is read only at process start |
| `uv sync` fails on `numpy` / `python-jobspy` | Corrupted lock or environment | Delete `.venv`, re-run `uv sync --frozen` |
| No jobs returned from a run | Search too narrow, or a job board temporarily returned zero | Broaden keywords/location; add more boards; raise "Results per board" |
| Wellfound or career-page URL returns nothing | No stable scraping contract; page structure varies | Use the main job-board sources; Wellfound scraping is documented as best-effort |
| "Finalize" button did nothing in live mode | `SUBMIT` was not typed exactly (case-sensitive) in the confirmation box | Type `SUBMIT` exactly |
| Resume profile fields look wrong | Parsing quality depends on the local model and the resume's layout | Try a different Ollama model; simplify the resume's layout |
| `json.JSONDecodeError` in logs | LLM returned non-JSON or wrapped JSON in markdown fences | Handled automatically by `utils.strip_code_fences()` + fallback to an empty result; no user action needed |
| `FileNotFoundError: data/tracker.json` | App was not run from the repo root | `cd` to the repo root before running |
| Job score is 0 for all factors | LLM response failed to parse; all scores defaulted to 0 | Check Ollama is running and the selected model responds; retry the run |

## Logs

`utils.setup_logging()` configures the `"job_agent"` logger at `INFO` level to stdout. Logs are also visible in the Streamlit sidebar under the **Logs** expander (last 50 lines, `app.py:384-390`).

No log files are written to disk by default. To capture logs:
```bash
uv run streamlit run app.py 2>&1 | tee app.log
```

## Data files

| File | Contents | Notes |
|---|---|---|
| `data/tracker.json` | All tracked applications and their status timelines | Created on first run; not committed to git |
| `data/uploads/` | Uploaded resume files | Created on first upload; files accumulate; delete manually if needed |
| `data/application_history.csv` | CSV export | Written only when "Export to CSV" is clicked in the Tracker tab |

## Resetting state

To clear the application tracker:
1. Delete `data/tracker.json`.

To start a fresh pipeline session without clearing the tracker:
1. Click **Start a new run** in the app UI.

These are independent operations. A new run allocates a new `thread_id` (UUID) for the LangGraph checkpointer, so the old session's graph state is abandoned in-memory but the tracker entries it created remain in `data/tracker.json`.
