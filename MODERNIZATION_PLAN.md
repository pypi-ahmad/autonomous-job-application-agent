# Modernization Plan — Autonomous Job Application Agent

Cites [ARCHITECTURE.md](ARCHITECTURE.md) for current-state detail; this document
is forward-looking only.

## 1. Executive summary

This is a young, single-file-per-concern Python project on a current stack
(LangGraph, Streamlit, LangChain, Python 3.13). The codebase has never had
dependency pinning, a test runner, or CI wired up — a gap the project's own
README already names under "Future Improvements." The plan is a single phase:
pin dependencies with `uv`, promote the four existing `demo()` self-checks into
a real `pytest` suite, and author a CI workflow. Everything else in the codebase
is current and gets no changes.

## 2. Current state assessment

See [ARCHITECTURE.md](ARCHITECTURE.md) in full. Key facts this plan depends on:
no `pyproject.toml`/lockfile, no test runner, no `.github/workflows/`
(ARCHITECTURE.md § Commands & Verification Inventory). Four `demo()` functions
with real `assert` statements already exist and pass today (`utils.py`,
`tools/dedup.py`, `agents/resume_advisor.py`, `agents/matcher.py`) — this is not
a codebase that needs tests invented from nothing, it needs the ones it already
has collected and run automatically.

## 3. Feasibility spike result & strategy

**Spike performed 2026-08-17**, not assumed:

| Check | Result |
|---|---|
| Installs from a committed lockfile without hand-patching | **No lockfile exists.** `requirements.txt` has no version pins (except `numpy>=2.1`). The existing `.venv` has every dependency, including `python-jobspy`, already installed and importing cleanly. |
| Builds/compiles on a currently-supported toolchain | **Yes.** `python -m py_compile` on all 15 modules: clean, no errors. Python 3.13.15 (well within the README's stated 3.11+ floor). |
| Boots | **Yes.** `import app` and `graph.build_graph()` both succeed live; the only output is Streamlit's expected "no ScriptRunContext" warning (harmless outside `streamlit run`). |
| Test runner executes, ≥1 meaningful test passes | **No test runner is wired up**, but all four existing `demo()` scripts pass when invoked directly (`utils.demo`, `dedup.demo`, `resume_advisor.demo`, `matcher.demo` — all printed "all checks passed"). |

**Conclusion:** this system is **already at 3 of 4 Testability Milestone
conditions** (supported runtime, builds, boots) and has real assertions sitting
inches from the fourth. This is not Strategy A (freeze-then-lift a barely-alive
app) or Strategy B (walking-skeleton onto a dead corpse) — the app was never
dead. The gap is pure mechanical wiring: pin dependencies, collect the existing
checks under `pytest`, author CI. Call this **Strategy C (wire up what's already
there)** — not one of the skill's two named strategies, because neither fits.

**Testability Milestone:** reached in Phase 1 for the whole app (single
component — there's no monorepo split here). **CI Milestone:** also Phase 1,
since Phase 1 is the first (and only) lit phase.

**Safety-ladder rung chosen: L3 (partial gate), by deliberate choice, not by
inability to reach L4.** Economic triage (skill § 2f): this is a solo local
tool with no production users and no SLA. The
paths that would need L4 (live job-board scraping, live LLM provider calls)
require either committing test API keys (a security anti-pattern this project's
own SECURITY.md explicitly warns against) or hitting real job boards from CI
(a ToS risk DISCLAIMER.md already tells users to own themselves — CI should not
create that risk on the maintainer's behalf). L3 — pytest on the deterministic,
mockable logic (dedup, resume_advisor, matcher's non-LLM path, utils) plus lint,
green in CI — is the proportionate target. The LLM-integration and live-scraping
paths stay **quarantined from CI** as a named residual risk, closed only by
manual smoke-testing (already described in `CONTRIBUTING.md`'s "Manual
verification" section).

## 4. Target architecture

**Decision framework applied, per component:**

| Component | Verdict | Why |
|---|---|---|
| LangGraph pipeline, Streamlit UI, all `agents/`/`tools/`/`parsers/` logic | ✅ Keep as-is | Current stack, no EOL, no maintenance burden — the skill's own "don't gold-plate" rule applies directly |
| `requirements.txt` (pip, unpinned) | 🔄 Wrap/adapt → replace with `pyproject.toml` + `uv.lock` | Not a code migration — a packaging-tool swap. Least-disruptive path that actually produces a real lockfile (satisfies Testability Milestone condition 2). `uv` is a drop-in for the existing venv workflow; `run.cmd`/README's manual instructions get a mechanical update, not a rewrite. |
| Four `demo()` scripts | 🔄 Wrap/adapt → convert to `pytest` test functions | The assertions are already correct; this is a collection-mechanism change, not new test-writing from scratch |
| CI | 🗑️→➕ Add (none exists to remove) | Author `.github/workflows/ci.yml` (lint + the new pytest suite) |

No "Upgrade in place" or "Rewrite" work is needed anywhere — there is nothing
old enough to upgrade and nothing broken enough to rewrite.

#### ADR: Adopt `uv` + `pyproject.toml` over pinning `requirements.txt` in place

- **Context:** the Testability Milestone requires installing from a committed
  lockfile without hand-patching. `requirements.txt` today has no version pins
  and the `python-jobspy` install order is a manual, undocumented-to-tooling
  workaround (`pip install --no-deps python-jobspy` as a separate step).
- **Decision:** migrate to `pyproject.toml` + `uv.lock`. `uv`'s per-dependency
  `--no-deps`-equivalent (`tool.uv.dependency-metadata` override, or simply
  keeping `python-jobspy` as a `no-build-isolation`/override entry) can encode
  the numpy workaround declaratively instead of as a README-only manual step.
- **Alternatives considered:** (a) `pip freeze > requirements.lock.txt` — cheaper,
  but produces no hash verification and doesn't remove the manual `--no-deps`
  step; (b) `poetry` — heavier migration, no material benefit over `uv` for a
  project this size. Rejected both in favor of `uv`.
- **Consequences:** `run.cmd`, `README.md`'s Option A/B setup instructions, and
  `CONTRIBUTING.md`'s local-setup section all need a one-time mechanical update
  in the same phase (this is H8 — see § 6 hazard red-team below).

## 5. Per-feature migration analysis

Only one "feature" is actually migrating: the build/verification tooling itself.
Every product feature (scraping, matching, drafting, tracking) is unaffected —
✅ keep as-is, per § 4.

- **Current implementation:** pip + `requirements.txt`, no test runner, no CI.
- **Migration strategy:** Strategy C (wire up what's already there — see § 3),
  tactic: incremental refactor of tooling only.
- **Testability status:** crosses the Testability Milestone within this single
  phase; safety rung L3 (deterministic-logic tests + lint in CI; LLM/scraping
  paths quarantined, manual smoke test only).
- **Dependencies and coupling:** touches `requirements.txt` (removed), `run.cmd`
  (install commands updated), `README.md`/`CONTRIBUTING.md` (setup instructions
  updated) — nothing in `agents/`, `tools/`, `parsers/`, `graph.py`, or `app.py`
  changes.
- **Effort estimate:** S (small) — mechanical tooling swap + 4 test-function
  conversions + one CI YAML file, no logic changes.
- **Risk assessment:** low. Worst case is a `uv sync` failure from a
  Windows-specific wheel issue (the same class of problem `numpy`/`jobspy`
  already hit) — mitigated by testing the migration on the actual dev machine
  before merging, and keeping the git history of `requirements.txt` as a
  fallback reference.
- **Acceptance criteria:** `uv sync` installs cleanly from `uv.lock` on a clean
  clone; `uv run pytest` collects and passes all four converted tests; the new
  `ci.yml` runs and is green on the phase's own PR.

## 6. Phased implementation plan

**Phase gating is regime-aware.** This phase is **post-testability ("lit")**
from the moment `uv sync` succeeds — its own exit criteria are runnable
commands / green CI, not a safety-ladder snapshot, because nothing here is
"dark": the app already builds and boots today (§ 3).

**Hazard red-team (Phase 2.5), walked against every class:**

- **H1** (incomplete quarantine) — N/A, not applicable: nothing is being removed
  wholesale except `requirements.txt` itself, and its only consumer (`run.cmd`,
  README, CONTRIBUTING) is enumerated and updated in this same phase. Cleared.
- **H2** (framework-major codemod) — N/A: no framework major version bump.
  Cleared.
- **H3** (runtime/deployment lockstep) — N/A: no runtime version change, no
  deployment artifacts exist to drift. Cleared.
- **H4** (route-class enumeration) — N/A: no edge/gateway/auth rewrite. Cleared.
- **H5** (stateful data-store major) — N/A: `data/tracker.json` is untouched by
  this phase. Cleared.
- **H6** (transitional-insecure state) — N/A: this phase introduces no weakened
  security state. Cleared.
- **H7** (stacked-PR trunk drift) — N/A in practice: this is a single-phase plan,
  so there is no sibling phase to stack against. Still: branch from `main`, PR
  to `main`, do not create a second long-lived branch. Cleared by construction.
- **H8** (living-doc drift) — **Triggered.** This phase changes topology (new
  `pyproject.toml`/`uv.lock`, removed `requirements.txt`, new `tests/`, new
  `.github/workflows/ci.yml`). **Plan action, folded into this phase's tasks
  below:** update `README.md`'s Installation & Setup section, `CONTRIBUTING.md`'s
  Local setup section, and `run.cmd` in the same PR as the tooling migration.

### Phase 1: Pin dependencies, collect existing tests, stand up CI (T-shirt size: S)

**Goal:** Reach the Testability Milestone and CI Milestone in one phase — this
system was already three-quarters of the way there.
**Regime:** post-testability ("lit") — the whole app, one component.
**Safety rung:** L3 (partial gate) — deliberate, not a downgrade from failure
(see § 3 economic triage).
**Prerequisites:** none — this is the first and only phase.
**Duration estimate:** well under a sprint; this is tooling wiring, not feature work.

#### Tasks

| ID | Task | Component | Blocked by |
|----|------|-----------|------------|
| 1.1 | Author `pyproject.toml` (project metadata + the current `requirements.txt` deps as dependencies) | packaging | — |
| 1.2 | Encode the `python-jobspy` numpy workaround declaratively in `pyproject.toml` (dependency override/constraint) instead of a README-only manual step; verify with a clean `uv sync` | packaging | 1.1 |
| 1.3 | Run `uv lock` to produce `uv.lock`; remove `requirements.txt` | packaging | 1.2 |
| 1.4 | Add `pytest` as a dev dependency; convert the four `demo()` functions into `tests/test_utils.py`, `tests/test_dedup.py`, `tests/test_resume_advisor.py`, `tests/test_matcher.py` (same assertions, `def test_...` instead of `def demo()` + `if __name__`) | tests | 1.3 |
| 1.5 | Add `ruff` as a dev dependency and a minimal `pyproject.toml` lint config (or accept defaults) | lint | 1.3 |
| 1.6 | Author `.github/workflows/ci.yml`: `uv sync --frozen` → `uv run ruff check .` → `uv run pytest` on push/PR to `main`, Python 3.12–3.13 matrix (matching the README's 3.11+ floor as closely as CI images allow) | CI | 1.4, 1.5 |
| 1.7 | Update `README.md` Installation & Setup (Option A/B) and `CONTRIBUTING.md` Local setup to reference `uv sync` instead of `pip install -r requirements.txt` | docs (H8) | 1.3 |
| 1.8 | Update `run.cmd` to call `uv sync` instead of pip/venv bootstrapping | tooling (H8) | 1.3 |
| 1.9 | Update `README.md`'s "Future Improvements" list — remove "Automated tests / CI" once it's done | docs (H8) | 1.6 |

#### Risks & Mitigations

- **Risk:** `uv sync` hits a Windows-specific wheel resolution issue similar to
  the original numpy/jobspy conflict. → **Mitigation:** test the full migration
  on the actual Windows dev machine before merging; keep the git history of
  `requirements.txt` as a documented fallback if `uv` genuinely can't resolve it
  (in which case, fall back to a `pip-tools`-generated pinned `requirements.txt`
  instead — a smaller ask than abandoning pinning altogether).
- **Risk:** CI matrix Python version doesn't have a `python-jobspy`-compatible
  wheel set on the runner. → **Mitigation:** pin CI to the same Python minor
  version as the tested dev environment (3.13) first; widen the matrix only
  after that's green.
- **Risk:** converting `demo()` to `pytest` functions accidentally changes
  behavior (e.g. losing the stub-LLM pattern in `matcher.py`'s demo). →
  **Mitigation:** the task is a mechanical rename + assertion-to-`assert`-in-
  test-function conversion; no logic in the functions under test changes, and
  the existing stub-LLM class in `agents/matcher.py`'s `demo()` moves verbatim
  into the test file as a fixture/local class.

#### Decisions made

- **Dropped:** L4 (full e2e/live-provider gate) — not deferred, actually
  dropped as a goal for this project's current shape (solo local tool). If the
  project ever gains real users/SLA, this decision should be revisited (see
  § 3 economic triage) — but that's a future call, not an open item now.
- **Deferred:** widening the CI Python matrix beyond 3.13 — do it once Phase 1
  is green on 3.13, not in the same PR.
- **Resolved:** `uv` over `pip-tools`/`poetry` (§ 4 ADR) — no further discussion
  needed to execute.

#### Verification & Exit Criteria (Definition of Done)

- [x] `uv sync --frozen` installs cleanly on a fresh clone (no hand-patching) —
      verified twice on a deleted `.venv`.
- [x] `uv run pytest` collects and passes all four converted tests.
- [x] `uv run ruff check .` passes — scoped to `E`/`F` for this first pass
      (documented in `pyproject.toml`, not silently ignored); `line-length`
      raised to 140 to match the codebase's existing longest line rather than
      reformatting files this phase doesn't otherwise touch.
- [x] `.github/workflows/ci.yml` authored (push/PR to `main`, Python 3.13).
      **Not yet observed green on GitHub** — it will run on the push that
      lands this phase; not a local-checkout-verifiable item until then.
- [x] `README.md`, `CONTRIBUTING.md`, and `run.cmd` all reference `uv`, not
      `pip install -r requirements.txt` (H8 closed in the same commit).
- [x] No behavior change: `import app` + `graph.build_graph()` succeed
      identically before and after. Full interactive dry-run smoke test
      (upload → match → draft → approve → finalize) still pending — do this
      manually per `CONTRIBUTING.md`'s checklist before treating Phase 1 as
      fully closed.

**Status: ✅ complete**, pending the two manual items noted above (CI's
first real run on GitHub, and an interactive dry-run smoke test).

## 7. Execution governance

- **Branch per phase:** since this is a single-phase plan, one branch
  (e.g. `modernize/tooling-and-ci`) cut from `main`, one PR back to `main`. No
  stacking risk (H7 cleared by construction).
- **Trunk:** confirmed `main` is the only branch (no legacy `master` exists in
  this repo).
- **Gate:** green CI on the PR is authoritative (lit regime).
- **CI Milestone and enforcement:** Phase 1 authors `.github/workflows/ci.yml`.
  **Turning it into a required status check / branch-protection rule is a
  manual step in GitHub → Settings → Branches that this plan cannot perform.**
  Recorded as an open item in § 9.
- **Living docs:** README/CONTRIBUTING/run.cmd updates are tasks 1.7-1.9 in the
  same phase, not a follow-up (H8).
- **`.github/copilot-instructions.md`:** no prior file existed at the start of
  this pass — the companion file below is a fresh file, not a merge.

## 8. Migration safety net

- **Feature flags:** none needed — this phase changes no runtime behavior, only
  build/verification tooling.
- **Data migration:** none — `data/tracker.json`'s format is untouched.
- **Rollback plan:** revert the single PR. `requirements.txt`'s last committed
  version remains in git history as a manual fallback if `uv` is reverted.
- **Transitional-insecure-state register:** empty — this phase introduces none.
- **Oracle & seam contracts:** the four existing `demo()` assertions ARE the
  oracle for the converted tests — their pass/fail behavior must be byte-for-byte
  identical before and after conversion (same inputs, same assertions).
- **Testing strategy:** pytest covers the deterministic logic (dedup,
  resume_advisor, matcher's non-LLM keyword path, utils). LLM-integration paths
  (parse_resume, writer, company_research, matcher's LLM-judged factors) and
  live scraping (job_scraper, wellfound_scraper, career_page_scraper) stay
  quarantined from CI — no committed API keys, no live network calls in CI.
  These remain covered only by the manual verification checklist already in
  `CONTRIBUTING.md`. This is the named residual risk of choosing L3 over L4.
- **Observability:** N/A — no deployed service to observe.

## 9. Open questions / decisions needed from stakeholders

1. **Manual platform step the agent cannot perform:** after Phase 1's CI is
   green, a human must go to GitHub → Settings → Branches and add
   `.github/workflows/ci.yml`'s job as a required status check on `main` for it
   to actually block merges. Until that's done, CI runs but doesn't gate.
2. **`[DECISION NEEDED]`** Should the CI Python matrix eventually include 3.11
   (the README's stated floor) and 3.12, or is 3.13-only (the actual dev
   environment) acceptable long-term? Deferred per § 6, but the maintainer
   should pick a target before widening it.
3. If real users or an SLA ever attach to this project, the L3→L4 decision in
   § 3 should be revisited with mocked-provider e2e tests — not urgent today.
