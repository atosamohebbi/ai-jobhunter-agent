import re
import requests

def extract_years(text: str):
    """
    Returns a list of numbers found near 'year/years/yrs' patterns.
    Examples matched:
      - "3+ years"
      - "2 years"
      - "1-2 years"
      - "1 to 5 years"
    """
    t = text.lower()

    patterns = [
        r"(\d+)\s*\+\s*(?:years|year|yrs|yr)",
        r"(\d+)\s*-\s*(\d+)\s*(?:years|year|yrs|yr)",
        r"(\d+)\s*to\s*(\d+)\s*(?:years|year|yrs|yr)",
        r"(\d+)\s*(?:years|year|yrs|yr)"
    ]

    found = []
    for p in patterns:
        for m in re.finditer(p, t):
            nums = [int(x) for x in m.groups() if x is not None]
            found.append(nums)
    return found


def experience_in_range(text: str, min_years: int = 1, max_years: int = 5) -> bool:
    """
    Keep job if it mentions experience within 1–5 years.
    - Keep if any number between 1 and 5 (inclusive) is found near year/years/yrs.
    - If no years mentioned, keep for now (AI will refine later).
    - Reject if only numbers are > 5.
    """
    years = extract_years(text)

    if not years:
        # If no years mentioned, keep the job for now
        return True

    # Flatten all numbers
    nums = [n for group in years for n in group]

    # Keep if any number is within range
    if any(min_years <= n <= max_years for n in nums):
        return True

    # Otherwise reject
    return False

def fetch_jobs():
    url = "https://remotive.com/api/remote-jobs"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    jobs = data["jobs"]
    filtered_jobs = []

    keywords = [
        "product designer",
        "ux designer",
        "ui designer",
        "ux/ui",
        "interaction designer",
        "experience designer",
        "ux researcher",
        "product design"
    ]

    for job in jobs:
        title = (job.get("title") or "").lower()
        description = (job.get("description") or "").lower()

        # Title relevance
        if not any(keyword in title for keyword in keywords):
            continue

        # Experience filter based on description text
        if not experience_in_range(description, 1, 5):
            continue

        filtered_jobs.append({
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "url": job.get("url", "")
        })

    return filtered_jobs

if __name__ == "__main__":
    print("JobHunter AI Agent starting...")

    jobs = fetch_jobs()

    print(f"Jobs found: {len(jobs)}")

    for job in jobs[:20]:  # prints up to 20 jobs so logs stay readable
        print(f"- {job['title']} — {job['company']}")
        print(job["url"])
        print("")

if __name__ == "__main__":
    print("JobHunter AI Agent starting...")

    jobs = fetch_jobs()

    print(f"Jobs found: {len(jobs)}")

    for job in jobs[:20]:  # print up to 20 so logs stay readable
        print(f"- {job['title']} — {job['company']}")
        print(job["url"])
        print("")
