# Security

## Supported surface

This is a local, single-user Streamlit application. There is no hosted
deployment, no multi-tenant mode, and no remote API surface — it runs on
your own machine, reads your own `.env`, and talks outbound only to the
providers and job boards you configure.

## Where secrets live

- `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `AGNES_API_KEY`, `GOOGLE_API_KEY`,
  and `OLLAMA_HOST` are read from your local `.env` (via `python-dotenv`) —
  never hardcoded, never transmitted anywhere except to the provider each
  key belongs to.
- `.env` is not committed; keep it that way. `.env.example` holds
  placeholders only.
- Uploaded resumes, the CRM tracker (`data/tracker.json`), and CSV exports
  live under `data/`, created at runtime and not committed.

## Operator responsibility

You are responsible for:

- keeping your own API keys and `.env` file secure;
- the resume and job data you process — see [DISCLAIMER.md](DISCLAIMER.md);
- complying with each job board's terms of service when scraping or
  submitting through this tool;
- reviewing generated cover letters and screening answers before anything
  is sent to a real employer.

The maintainer does not receive your resumes, generated content, tracker
data, or credentials through this project.

## Submission safety

Dry-run mode is on by default — nothing is opened or marked "Submitted."
Live mode requires typing `SUBMIT` to confirm, and even then the agent only
opens the job listing in your browser for you to submit manually; it does
not auto-fill or auto-submit a third-party site's form. If you find a path
where that boundary can be bypassed, treat it as a security issue (see
below), not a feature request.

## Reporting a vulnerability

Please report security issues privately through this repository's
[GitHub private vulnerability reporting form](https://github.com/pypi-ahmad/autonomous-job-application-agent/security/advisories/new)
rather than a public issue. Include the affected file/flow, a minimal
reproduction, and the potential impact. Do not include real API keys,
resumes, or other personal data in the report — use synthetic examples.

There is no fixed response-time guarantee and no paid bug bounty — this is
a free, community-maintained project.
