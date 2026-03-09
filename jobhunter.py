import os
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from urllib.parse import urljoin

import requests
from dateutil import tz


REMOTIVE_API = "https://remotive.com/api/remote-jobs"

COMPANIES = [
    {"company": "Dapper Labs", "homepage": "https://dapperlabs.com"},
    {"company": "Sicore", "homepage": "http://sicore-tech.com/"},
    {"company": "LayerZero", "homepage": "https://layerzero.network/"},
    {"company": "Metaspectral", "homepage": "https://metaspectral.com"},
    {"company": "Trulioo", "homepage": "http://trulioo.com"},
    {"company": "Mimik", "homepage": "https://mimik.com"},
    {"company": "Increment", "homepage": "https://increment.fi"},
    {"company": "Inventys", "homepage": "https://inventysinc.com"},
    {"company": "Svante", "homepage": "https://svanteinc.com"},
    {"company": "Steelhead LNG", "homepage": "http://www.steelheadlng.com"},
    {"company": "SkyChain Technologies", "homepage": "https://skychaintechnologiesinc.com/"},
    {"company": "1QBit", "homepage": "http://1qbit.com"},
    {"company": "StartX", "homepage": "http://imstartx.com"},
    {"company": "Mojio", "homepage": "http://moj.io"},
    {"company": "Axiom Zen", "homepage": "https://axiomzen.com"},
    {"company": "Veritree", "homepage": "https://www.veritree.com/"},
    {"company": "Wisdom", "homepage": "https://getwisdom.io/"},
    {"company": "Bench", "homepage": "https://bench.co"},
    {"company": "Klue", "homepage": "https://klue.com"},
    {"company": "CounterPath", "homepage": "http://www.counterpath.com/"},
    {"company": "Hootsuite", "homepage": "http://hootsuite.com"},
    {"company": "Pathful", "homepage": "https://pathful.com"},
    {"company": "Venzee", "homepage": "https://venzee.com"},
    {"company": "Clio", "homepage": "https://clio.com"},
    {"company": "BuildDirect", "homepage": "http://www.builddirect.com"},
    {"company": "Pronai", "homepage": "http://pronai.com"},
    {"company": "Unbounce", "homepage": "http://unbounce.com"},
    {"company": "Swae", "homepage": "http://www.swae.io/"},
    {"company": "STEMCELL Technologies", "homepage": "http://stemcell.com"},
    {"company": "Monos", "homepage": "https://www.monos.com/"},
    {"company": "Proxxi", "homepage": "https://proxxi.co"},
    {"company": "Canalyst", "homepage": "https://canalyst.com/"},
    {"company": "PH7 Labs", "homepage": "https://phxlabs.ca"},
    {"company": "Fraction", "homepage": "https://fraction.com"},
    {"company": "Microbiome Insights", "homepage": "https://microbiomeinsights.com"},
    {"company": "Kabam", "homepage": "https://www.kabam.com/"},
    {"company": "Demand Curve", "homepage": "https://www.demandcurve.com/"},
    {"company": "Aspect Biosystems", "homepage": "https://aspectbiosystems.com"},
    {"company": "GeoComply", "homepage": "http://www.geocomply.com"},
    {"company": "Finning", "homepage": "http://www.finning.com/"},
    {"company": "Cascadia", "homepage": "http://www.cascadiacorp.com"},
    {"company": "LoginRadius", "homepage": "http://www.loginradius.com/"},
    {"company": "Finn AI", "homepage": "http://www.finn.ai"},
    {"company": "Lungpacer", "homepage": "http://lungpacer.com/"},
    {"company": "Thinkific", "homepage": "https://thinkific.com"},
    {"company": "TIMIA Capital", "homepage": "https://timiacapital.com"},
    {"company": "Visier", "homepage": "https://visier.com"},
    {"company": "Terramera", "homepage": "https://terramera.com"},
    {"company": "Adventure Bucket List", "homepage": "http://adventurebucketlist.com"},
    {"company": "Routific", "homepage": "https://routific.com/"},
    {"company": "SkyHive", "homepage": "https://skyhive.ai"},
    {"company": "PlaceSpeak", "homepage": "https://placespeak.com"},
    {"company": "Fitplan", "homepage": "http://www.fitplanapp.com"},
    {"company": "Battlefy", "homepage": "http://battlefy.com"},
    {"company": "Pagefreezer", "homepage": "https://pagefreezer.com"},
    {"company": "Mintent", "homepage": "https://getmintent.com"},
    {"company": "FTSY", "homepage": "http://ftsy.ai"},
    {"company": "Payfirma", "homepage": "https://payfirma.com"},
    {"company": "PAI Health", "homepage": "http://www.paihealth.com"},
    {"company": "Precision NanoSystems", "homepage": "https://precisionnanosystems.com"},
    {"company": "Replicel", "homepage": "https://replicel.com/"},
    {"company": "Vision Critical", "homepage": "https://visioncritical.com"},
    {"company": "Alida", "homepage": "https://alida.com"},
    {"company": "Nexii", "homepage": "https://www.nexii.com/"},
    {"company": "ThisFish", "homepage": "http://this.fish"},
    {"company": "Picatic", "homepage": "https://picatic.com"},
    {"company": "PayrollHero", "homepage": "http://payrollhero.com"},
    {"company": "Ad Auris", "homepage": "https://www.ad-auris.com/"},
    {"company": "Payday", "homepage": "https://usepayday.com"},
    {"company": "Actus", "homepage": "http://actus-software.com"},
    {"company": "VSBLTY", "homepage": "https://vsblty.net"},
    {"company": "Zafin", "homepage": "http://zafin.com"},
]

CAREERS_PATHS = [
    "/careers",
    "/jobs",
    "/about/careers",
    "/company/careers",
    "/work-with-us",
    "/join-us",
    "/careers/jobs",
]

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

RUN_HOURS_PT = {7, 8, 13, 14}
STATE_FILE = "state.json"

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobHunterAgent/1.0)"
}


def now_pt() -> datetime:
    return datetime.now(tz=tz.gettz("America/Los_Angeles"))


def should_run_now() -> bool:
    dt = now_pt()
    return dt.hour in RUN_HOURS_PT


def extract_year_phrases(text: str):
    t = text.lower()

    patterns = [
        r"\b(\d{1,2})\s*[-–]\s*(\d{1,2})\s*(?:years|year|yrs|yr)\b",
        r"\b(\d{1,2})\s*(?:to)\s*(\d{1,2})\s*(?:years|year|yrs|yr)\b",
        r"\b(\d{1,2})\s*\+\s*(?:years|year|yrs|yr)\b",
        r"\b(?:minimum|at\s+least)\s*(\d{1,2})\s*(?:years|year|yrs|yr)\b",
        r"\b(\d{1,2})\s*(?:years|year|yrs|yr)\b",
    ]

    found = []

    for pattern in patterns:
        for match in re.finditer(pattern, t):
            groups = [g for g in match.groups() if g is not None]

            if len(groups) == 2:
                a, b = int(groups[0]), int(groups[1])
                lo, hi = min(a, b), max(a, b)
                found.append(("range", lo, hi))
            elif len(groups) == 1:
                n = int(groups[0])
                if "+" in match.group(0) or "minimum" in match.group(0) or "at least" in match.group(0):
                    found.append(("plus", n))
                else:
                    found.append(("single", n))

    return found


def matches_experience_1_to_5(description: str) -> bool:
    signals = extract_year_phrases(description)

    if not signals:
        return True

    for signal in signals:
        if signal[0] == "single":
            n = signal[1]
            if 1 <= n <= 5:
                return True

        elif signal[0] == "plus":
            n = signal[1]
            if 1 <= n <= 5:
                return True

        elif signal[0] == "range":
            lo, hi = signal[1], signal[2]
            if not (hi < 1 or lo > 5):
                return True

    return False


def matches_title(title: str) -> bool:
    t = (title or "").lower()
    return any(k in t for k in KEYWORDS)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_html(html: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return normalize_whitespace(text)


def fetch_remotive_jobs():
    r = requests.get(REMOTIVE_API, timeout=30, headers=REQUEST_HEADERS)
    r.raise_for_status()
    data = r.json()

    jobs = []

    for job in data.get("jobs", []):
        jobs.append(
            {
                "title": job.get("title", "") or "",
                "company": job.get("company_name", "") or "",
                "url": job.get("url", "") or "",
                "description": job.get("description", "") or "",
                "source": "Remotive",
            }
        )

    return jobs


def find_careers_url(homepage: str) -> str:
    base = homepage.rstrip("/")

    # Try likely careers pages first
    candidates = [urljoin(base + "/", path.lstrip("/")) for path in CAREERS_PATHS]

    # Fall back to homepage last
    candidates.append(base)

    for url in candidates:
        try:
            response = requests.get(url, timeout=20, allow_redirects=True, headers=REQUEST_HEADERS)
            if response.status_code == 200 and len(response.text) > 200:
                return response.url
        except Exception:
            continue

    return homepage


def extract_matching_titles_from_html(html: str):
    text = strip_html(html).lower()
    matches = []

    for keyword in KEYWORDS:
        if keyword in text:
            matches.append(keyword.title())

    return list(dict.fromkeys(matches))


def fetch_custom_careers_jobs():
    jobs = []

    for entry in COMPANIES:
        company = entry["company"]
        homepage = entry["homepage"]

        try:
            careers_url = find_careers_url(homepage)
            response = requests.get(careers_url, timeout=30, headers=REQUEST_HEADERS)
            response.raise_for_status()

            html = response.text
            matching_titles = extract_matching_titles_from_html(html)

            for title in matching_titles:
                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "url": careers_url,
                        "description": html,
                        "source": "Custom Careers Page",
                    }
                )

        except Exception as e:
            print(f"Failed careers fetch for {company}: {e}")

    return jobs


def dedupe_jobs(jobs):
    seen = set()
    unique_jobs = []

    for job in jobs:
        key = (
            (job.get("title", "") or "").strip().lower(),
            (job.get("company", "") or "").strip().lower(),
            (job.get("url", "") or "").strip().lower(),
        )

        if key in seen:
            continue

        seen.add(key)
        unique_jobs.append(job)

    return unique_jobs


def fetch_all_jobs():
    jobs = []
    jobs.extend(fetch_remotive_jobs())
    jobs.extend(fetch_custom_careers_jobs())
    return dedupe_jobs(jobs)


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
                "company": (job.get("company", "") or "").strip(),
                "url": (job.get("url", "") or "").strip(),
                "source": (job.get("source", "") or "").strip(),
            }
        )

    return kept


def build_email_body(jobs):
    dt = now_pt().strftime("%Y-%m-%d %I:%M %p PT")

    lines = [
        f"JobHunter results — {dt}",
        "",
        f"Jobs found: {len(jobs)}",
        "",
    ]

    if not jobs:
        lines.append("No matching jobs in this run.")
        return "\n".join(lines)

    jobs_to_send = jobs[:25]

    for i, job in enumerate(jobs_to_send, start=1):
        lines.append(f"{i}) {job['title']} — {job['company']}")
        lines.append(f"   Source: {job.get('source', 'Unknown')}")
        lines.append(f"   {job['url']}")
        lines.append("")

    if len(jobs) > len(jobs_to_send):
        lines.append(f"(+ {len(jobs) - len(jobs_to_send)} more not shown)")

    return "\n".join(lines)


def send_email(subject: str, body: str):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    email_to = os.getenv("EMAIL_TO")

    missing = [
        key
        for key, value in {
            "GMAIL_USER": gmail_user,
            "GMAIL_APP_PASSWORD": gmail_app_password,
            "EMAIL_TO": email_to,
        }.items()
        if not value
    ]

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

    jobs = fetch_all_jobs()
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
