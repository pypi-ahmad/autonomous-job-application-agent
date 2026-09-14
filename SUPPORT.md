# Support

This is a free, open-source, community-driven project. Support is
best-effort — there's no paid support tier, no SLA, and no dedicated team
behind it. Bug reports and feature ideas are the most useful contributions.

## No donations, please

This project does not accept or want donations, sponsorship, or any other
financial support. If you'd like to support it, use one of the options
below instead — they're worth more than money here.

## How to help

- Star and share the [GitHub repository](https://github.com/pypi-ahmad/autonomous-job-application-agent).
- Try it against a synthetic or your own real resume (dry-run mode is
  on by default, so it's safe to explore) and report what breaks.
- File a [bug report](https://github.com/pypi-ahmad/autonomous-job-application-agent/issues/new?template=bug_report.yml)
  with reproducible steps.
- Suggest an improvement via the [feature request form](https://github.com/pypi-ahmad/autonomous-job-application-agent/issues/new?template=feature_request.yml).
- Open a pull request — see [CONTRIBUTING.md](CONTRIBUTING.md). The project
  has no automated tests or CI yet, so adding either is an especially
  valuable contribution.

## Getting help

Search [existing issues](https://github.com/pypi-ahmad/autonomous-job-application-agent/issues)
before opening a new one. When reporting a problem, include:

- your OS and Python version;
- which job boards, providers, and models were involved;
- whether you were in dry-run or live mode;
- the exact error, with any API key values or personal resume content
  removed.

Never post an API key, a real resume, generated cover-letter content, or
tracker data in a public issue.

Report security vulnerabilities privately as described in
[SECURITY.md](SECURITY.md), not through a public issue.

## Out of scope

- Bugs in a third-party job board's own site, or that board's scraping
  countermeasures — report those upstream, not here, unless this project's
  scraper is clearly the cause.
- Provider-side model quality, pricing, or outage issues (OpenAI, Google,
  Agnes AI, Ollama) — those belong with the provider.
