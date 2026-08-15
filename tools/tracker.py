"""Application tracker / CRM: lifecycle status, timeline, notes, follow-ups, CSV export."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

TRACKER_FILE = Path("data/tracker.json")
STATUSES = ["Draft", "Approved", "Submitted", "Interview", "Rejected", "Offer"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_applications() -> list[dict]:
    if not TRACKER_FILE.exists():
        return []
    return json.loads(TRACKER_FILE.read_text(encoding="utf-8"))


def _save(applications: list[dict]) -> None:
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(applications, indent=2), encoding="utf-8")


def upsert_application(job: dict, status: str, note: str = "") -> None:
    applications = load_applications()
    existing = next((a for a in applications if a["job_id"] == job["id"]), None)
    event = {"status": status, "timestamp": _now(), "note": note}
    if existing:
        existing["status"] = status
        existing["timeline"].append(event)
    else:
        applications.append(
            {
                "job_id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "url": job["url"],
                "status": status,
                "notes": "",
                "follow_up_date": None,
                "timeline": [event],
            }
        )
    _save(applications)


def update_status(job_id: str, status: str, note: str = "") -> None:
    applications = load_applications()
    for app in applications:
        if app["job_id"] == job_id:
            app["status"] = status
            app["timeline"].append({"status": status, "timestamp": _now(), "note": note})
            break
    _save(applications)


def set_note(job_id: str, note: str) -> None:
    applications = load_applications()
    for app in applications:
        if app["job_id"] == job_id:
            app["notes"] = note
            break
    _save(applications)


def set_follow_up(job_id: str, date_str: str | None) -> None:
    applications = load_applications()
    for app in applications:
        if app["job_id"] == job_id:
            app["follow_up_date"] = date_str
            break
    _save(applications)


def export_csv(path: str = "data/application_history.csv") -> str:
    applications = load_applications()
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["job_id", "title", "company", "url", "status", "notes", "follow_up_date"])
        for app in applications:
            writer.writerow(
                [app["job_id"], app["title"], app["company"], app["url"], app["status"], app["notes"], app["follow_up_date"]]
            )
    return str(out_path)
