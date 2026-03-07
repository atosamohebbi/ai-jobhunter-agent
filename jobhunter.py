import os
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import requests
from dateutil import tz


REMOTIVE_API = "https://remotive.com/api/remote-jobs"

KEYWORDS = [
    "product designer",
    "ux designer",
    "ui designer",
    "ux/ui",
    "interaction designer",
    "experience designer",
    "ux researcher",
    "product design",
    "product design lead",
    "design lead",
]

# Runs only at these local hours (America/Los_Angeles)
RUN_HOURS_PT = {7, 13}  # 7am and 1pm
STATE_FILE = "state.json"


def now_pt() -> datetime:
    return datetime.now(tz=tz.gettz("America/Los_Angeles"))


def should_run_now() -> bool:
    dt = now_pt()
    return dt.hour in RUN_HOURS_PT


def extract_year_phrases(text: str):
    """
    Extract experience signals like:
      - "3+ years"
      - "2 years"
      - "1-2 years"
      - "1 to 5 years"
      - "minimum 3 years"
    Returns list of tuples:
      ("single", n) OR ("range", a, b) OR ("plus", n)
    """
    t = text.lower()

    patterns = [
        # range: 1-2 years, 1 – 2 yrs
        r"\b(\d{1,2})\s*[-–]\s*(\d{1,2})\s*(?:\+?\s*)?(?:years|year|yrs|yr)\b",
        # range: 1 to 5 years
        r"\b(\d{1,2})\s*(?:to)\s*(\d{1,2})\s*(?:\+?\s*)?(?:years|year|yrs|yr)\b",
        # plus: 3+ years
        r"\b(\d{1,2})\s*\+\s*(?:years|year|yrs|yr)\b",
        # "minimum 3 years", "at least 2 years"
        r"\b(?:minimum|at\s+least)\s*(\d{1,2})\s*(?:years|year|yrs|yr)\b",
        # single: 2 years
        r"\b(\d{1,2})\s*(?:years|year|yrs|yr)\b",
    ]

    found = []
    for p in patterns:
        for m in re.finditer(p, t):
            groups = [g for g in m.groups() if g is not None]
            if len(groups) == 2:
                a, b = int(groups[0]), int(groups[1])
                lo, hi = min(a, b), max(a, b)
                found.append(("range", lo, hi))
            elif len(groups) == 1:
                n = int(groups[0])
                if "+ " in m.group(0) or "+" in m.group(0) or "minimum" in m.group(0) or "at least" in m.group(0):
                    found.append(("plus", n))
                else:
                    found.append(("single", n))

    return found


def matches_experience_1_to_5(description: str) -> bool:
    """
    Keep jobs if:
      - any explicit experience requirement overlaps [1, 5]
      - OR no experience requirement is mentioned (keep for now)

    Reject only if:
      - experience is mentioned AND all mentions clearly imply > 5 (e.g., 7+ years, 10 years)
    """
    signals = extract_year_phrases(description)

    # If they didn't mention years at all, keep it (lots of postings omit exact years)
    if not signals:
        return True

    # If ANY signal overlaps 1..5, keep
    for s in signals:
        if s[0] == "single":
            n = s[1]
            if 1 <= n <= 5:
                return True
        elif s[0] == "plus":
            n = s[1]
            # "3+ years" is acceptable because it includes 3–5 range as realistic target
            if 1 <= n <= 5:
                return True
        elif s[0] == "range":
            lo, hi = s[1], s[2]
            # overlap check
            if not (hi < 1 or lo > 5):
                return True

    # Otherwise, all experience mentions are outside 1..5
    return False


def matches_title(title: str) -> bool:
    t = (title or "").lower()
    return any(k in t for k in KEYWORDS)


def fetch_jobs():
    r = requests.get(REMOTIVE_API, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("jobs", [])


def filter_jobs(jobs):
    kept = []
    for job in jobs:
        title = job.get("title", "") or ""
        desc = job.get("description", "") or ""

        if not matches_title(title):
            continue

        if not matches_experience_1_to_5(desc):
            continue

        kept.append(
            {
                "title": title.strip(),
                "company": (job.get("company_name", "") or "").strip(),
                "url": (job.get("url", "") or "").strip(),
            }
        )
    return kept


def build_email_body(jobs):
    dt = now_pt().strftime("%Y-%m-%d %I:%M %p PT")
    lines = []
    lines.append(f"JobHunter results — {dt}")
    lines.append("")
    lines.append(f"Jobs found: {len(jobs)}")
    lines.append("")

    if not jobs:
        lines.append("No matching jobs in this run.")
        return "\n".join(lines)

    # Limit to avoid huge emails
    jobs_to_send = jobs[:25]

    for i, j in enumerate(jobs_to_send, start=1):
        lines.append(f"{i}) {j['title']} — {j['company']}")
        lines.append(f"   {j['url']}")
        lines.append("")

    if len(jobs) > len(jobs_to_send):
        lines.append(f"(+ {len(jobs) - len(jobs_to_send)} more not shown)")

    return "\n".join(lines)


def send_email(subject: str, body: str):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    email_to = os.getenv("EMAIL_TO")

    missing = [k for k, v in {
        "GMAIL_USER": gmail_user,
        "GMAIL_APP_PASSWORD": gmail_app_password,
        "EMAIL_TO": email_to
    }.items() if not v]

    if missing:
        print(f"Missing required env vars: {', '.join(missing)}")
        return

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, [email_to], msg.as_string())


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_sent_slot": ""}
    except Exception:
        return {"last_sent_slot": ""}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_current_slot():
    dt = now_pt()

    if dt.hour == 7:
        return dt.strftime("%Y-%m-%d-07")

    if dt.hour == 13:
        return dt.strftime("%Y-%m-%d-13")

    return None


def main():
    print("JobHunter AI Agent starting...")

    current_slot = get_current_slot()
    state = load_state()

    if os.getenv("GITHUB_ACTIONS") == "true":
        if not should_run_now():
            dt = now_pt().strftime("%Y-%m-%d %I:%M %p PT")
            print(f"Not a send hour (7am/1pm PT). Current time: {dt}. Exiting.")
            return

        if current_slot and state.get("last_sent_slot") == current_slot:
            print(f"Already sent email for slot: {current_slot}. Exiting.")
            return

    jobs = fetch_jobs()
    filtered = filter_jobs(jobs)

    subject = f"JobHunter results — {now_pt().strftime('%a %b %d, %I:%M %p PT')}"
    body = build_email_body(filtered)

    print(body)
    send_email(subject, body)

    if current_slot:
        state["last_sent_slot"] = current_slot
        save_state(state)
        print(f"Saved sent slot: {current_slot}")

if __name__ == "__main__":
    main()
