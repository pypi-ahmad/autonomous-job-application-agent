# Contributing

Thanks for looking at this project. Contributions of any size are welcome —
a bug report, a feature idea, a doc fix, or a pull request all count. This is
a community-driven, free project with no company or funding behind it, so
outside testing and patches genuinely help.

Read the [README](README.md) first for what the agent does and how it's
structured. Read [DISCLAIMER.md](DISCLAIMER.md) for the responsibility that
comes with running it against real job boards and real resumes.

## Ground rules

- Keep the agent local-first: no telemetry, no hosted backend, no silently
  added network calls.
- Preserve the safety gate: dry-run stays the default, and live mode must
  still require typing `SUBMIT` and stop at "open the listing in the
  browser" — never add auto-fill or auto-submit against a third-party site.
- One focused change per pull request. Avoid drive-by refactors mixed into
  a feature or fix.
- Never commit `.env`, real resumes, `data/uploads/`, `data/tracker.json`,
  or `data/application_history.csv`. Use a synthetic or redacted resume for
  any fixture you add.
- Update `README.md` (features, env vars, project structure, or
  configuration tables) in the same PR when your change affects any of
  them.

## Local setup

Windows is the only platform this project has been tested on so far (the
README says so explicitly) — Option B below should work on macOS/Linux too,
but please call out in your PR if you've verified that.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
pip install --no-deps python-jobspy   # see requirements.txt for why
cp .env.example .env                  # fill in the keys you want to test with
streamlit run app.py
```

Install [Ollama](https://ollama.com/) and pull at least one model if you're
touching resume parsing, matching, or draft generation — those paths need a
local model configured.

## No automated tests or CI yet

This project doesn't have a test suite or CI pipeline yet — that's an open
item, not an oversight to route around. If you're fixing a bug, a small
regression check (even a standalone script under a `tests/` you create) is
appreciated but not required to get a PR reviewed. Adding the first real
test suite or a CI workflow is itself a very welcome contribution.

## Manual verification

Before opening a pull request for a UI-visible or pipeline-behavior change:

1. Run the app (`run.cmd` or `streamlit run app.py`).
2. Exercise the affected step with dry-run **on** — confirm nothing opens a
   browser tab or writes a "Submitted" tracker entry.
3. If your change touches content generation or submission, also verify
   live mode still requires the `SUBMIT` confirmation before anything opens.
4. Confirm no API key value, resume content, or generated cover-letter text
   ends up in a log line, screenshot, or committed fixture.

Describe what you tested (and with which providers/models) in the PR
description.

## Reporting bugs and suggesting features

Use the [bug report form](https://github.com/pypi-ahmad/autonomous-job-application-agent/issues/new?template=bug_report.yml)
or the [feature request form](https://github.com/pypi-ahmad/autonomous-job-application-agent/issues/new?template=feature_request.yml).
Search existing issues first. Include your OS, Python version, which job
boards and providers were involved, and dry-run vs. live mode.

Report security issues privately as described in [SECURITY.md](SECURITY.md),
not through a public issue.

## No financial support

This project does not want or accept donations, sponsorship, or paid
support. Time, testing, bug reports, and pull requests are the contributions
that help — see [SUPPORT.md](SUPPORT.md).

By contributing, you agree your contribution may be distributed under this
project's [MIT License](LICENSE).
