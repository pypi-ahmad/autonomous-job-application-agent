# Disclaimer

Read this before you point the agent at real job boards or a real resume.

## No warranty

This software is MIT-licensed and provided **as is**, with no warranty of
any kind. See [LICENSE](LICENSE). The maintainer is not liable for damages
arising from using it, including a missed application, a rejected
application, or an account action taken by a job board.

## You run it, you own the data

This is not a hosted service. You run it on your own machine with your own
API keys. The maintainer never receives your resume, generated cover
letters, screening answers, job search results, or tracker data.

Everything the app reads or writes lives on your machine, under `data/`:
uploaded resumes (`data/uploads/`), the CRM tracker (`data/tracker.json`),
and CSV exports (`data/application_history.csv`). None of it is committed
to the repository, and none of it leaves your machine except:

- resume text and job descriptions sent to the local Ollama model you
  configure (stays on your machine unless you point `OLLAMA_HOST` at a
  remote server yourself);
- resume text, job descriptions, and drafted content sent to whichever
  cloud "polish" provider you configure (OpenAI-compatible, Agnes AI, or
  Google Gemini) — treat that exactly like sending the file to that
  provider yourself;
- search queries sent to DuckDuckGo's HTML endpoint for company research.

You decide what goes into a resume upload or a career-page URL, and you
are responsible for not including data you don't want reaching a
configured provider.

## Job-board scraping is your responsibility

This project scrapes LinkedIn, Indeed, Naukri, ZipRecruiter, Glassdoor
(via `python-jobspy`), and Wellfound, and can extract postings from
company career pages you paste in. Each of those sites has its own terms
of service governing automated access. Using this tool does not grant you
any exemption from those terms — **you are responsible for complying with
each site's terms of service**, rate limits, and any consequences of
scraping them, including account action against your own accounts.

## Submissions are never fully automatic

Dry-run mode is on by default. In live mode, the agent still requires you
to type `SUBMIT` to confirm, and even then it only opens the job listing in
your browser — it does not auto-fill or auto-submit a third-party site's
application form. You are the one who reviews and submits every
application. The agent's scoring, drafted cover letters, and screening
answers are starting points, not guaranteed-accurate or guaranteed-truthful
content — **you are responsible for reviewing everything before it goes to
a real employer.**

## No financial support wanted

This project does not want or accept donations, sponsorship, or paid
support. Testing, bug reports, and pull requests are the help that
matters — see [SUPPORT.md](SUPPORT.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

Do not use this disclaimer to report a vulnerability. Follow
[SECURITY.md](SECURITY.md) instead.
