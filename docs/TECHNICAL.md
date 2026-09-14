# Technical reference

## Stack

| Component | Library | Why it appears here |
|---|---|---|
| UI | `streamlit` | Single-file reactive UI that reruns on every interaction; LangGraph's `MemorySaver` + a `thread_id` in `st.session_state` is what makes state survive those reruns |
| Orchestration | `langgraph` (`StateGraph`, `MemorySaver`) | Linear state machine with a typed `TypedDict` state and built-in `interrupt_before` pause points for human-in-the-loop |
| LLM integration | `langchain-core`, `langchain-openai`, `langchain-google-genai`, `langchain-ollama` | Provider-agnostic `BaseChatModel`; `llm.invoke([HumanMessage(...)])` is the only call pattern used across the codebase |
| Job scraping | `python-jobspy` | Multi-board aggregation in one call; the numpy version it declares (`==1.26.3`) conflicts with modern Python — resolved by `[tool.uv].override-dependencies = ["numpy>=2.1"]` in `pyproject.toml` instead of a manual `--no-deps` step |
| Resume extraction | `pypdf`, `python-docx` | Text extraction only; structuring is done by the LLM |
| HTTP | `requests`, `httpx`, `beautifulsoup4` | `httpx` for the Ollama health check (`config.list_ollama_models`); `requests`+BS4 for Wellfound, career pages, and DuckDuckGo |
| Deduplication | `difflib.SequenceMatcher` (stdlib) | Fuzzy title matching at threshold 0.88; no external library |
| Config | `python-dotenv` | Reads `.env` at import time in `config.py`; all env vars have in-code defaults or are `None` |
| Dependency management | `uv` | Pinned lockfile (`uv.lock`), Python version pinned via `.python-version` (3.13 for dev and CI) |
| Lint | `ruff` (rules `E`, `F`) | First lint pass; broader rule families were deliberately excluded because they flag intentional patterns (broad excepts around network calls) — see `pyproject.toml` comment |
| Tests | `pytest` | Four tests in `tests/` covering deterministic logic only; LLM-integration and live-scraping paths are not in CI |

## Important invariants

- **Must run from repo root.** `tools/tracker.py:10` and the resume upload path both hardcode `data/...` relative paths. Running from a different directory breaks tracker persistence and resume saves.
- **Ollama must be running for parsing, matching, and drafting.** `build_graph()` succeeds without it, but `node_parse_resume`, `node_match_jobs`, and `node_generate_content` all fail at invocation time.
- **`data/` is runtime-only and not committed.** `tools/tracker.py:_save()` calls `mkdir(parents=True, exist_ok=True)` — the directory is created on first write.
- **`AgentState.log` accumulates across nodes** (`operator.add` reducer, `state.py:29`). All other fields are fully overwritten by each node's return dict.
- **`node_human_approval` is a deliberate no-op** (`graph.py:98-99`). It exists only as the second interrupt point; the UI detects it via `graph.get_state(rc()).next`.
- **Resume text is truncated to 12,000 characters** before being sent to the LLM (`parsers/resume_parser.py:60`).
- **Job descriptions are truncated to 4,000 characters** for matching (`agents/matcher.py:97`).
- **Match weights are fixed constants** in `agents/matcher.py:16-23`. They are not configurable from the UI.

## Error handling

The pattern throughout `tools/` is broad `except Exception` around every network call, logged at `WARNING` and degraded gracefully:

| File | What is swallowed | Degraded result |
|---|---|---|
| `tools/job_scraper.py:83-88` | Any exception from a source | That source contributes `[]`; others proceed |
| `tools/wellfound_scraper.py` | Any exception from the scrape | `[]` |
| `tools/career_page_scraper.py` | Any exception from the scrape | `[]` |
| `tools/company_research.py` | Any exception from search or LLM | Empty brief |
| `parsers/resume_parser.py:64-66` | `json.JSONDecodeError` from LLM response | `_EMPTY_RESULT` dict |
| `agents/matcher.py:100-104` | `json.JSONDecodeError` from LLM response | Empty dict (all scores 0) |
| `config.list_ollama_models():36-42` | Any exception reaching Ollama | `[]` (sidebar shows "No Ollama models found") |

There is no global error boundary in `app.py`; unhandled exceptions surface as Streamlit stack traces.

## Persistence

| Path | Created by | Format |
|---|---|---|
| `data/tracker.json` | `tools/tracker.py:_save()` on first `upsert_application()` | JSON array of application records; read and rewritten in full on every mutation |
| `data/uploads/<filename>` | `app.py` on resume upload | Copy of the uploaded resume file |
| `data/application_history.csv` | `tools/tracker.py:export_csv()` on demand | Flat CSV; not kept in sync automatically |

No database; no schema migrations. The tracker JSON is acceptable at "dozens of applications" scale.

## LLM call pattern

All LLM calls use `langchain_core.messages.HumanMessage` and `llm.invoke([HumanMessage(content=prompt)])`. Responses are `.content` strings. JSON is expected from most calls; `utils.strip_code_fences()` strips markdown fences that LLMs sometimes wrap JSON output in before `json.loads()` is called.

## Known scale ceilings

| Ceiling | Location | Comment |
|---|---|---|
| Sequential LLM call per job during matching | `agents/matcher.py:13-15` | Fine up to ~100 jobs |
| O(n²) fuzzy dedup | `tools/dedup.py:8-10` | Fine at "hundreds of jobs" scale |

Both are annotated with `ponytail:` comments in the source naming the ceiling and the upgrade path.
