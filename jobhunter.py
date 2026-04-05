import json
import os
from datetime import datetime

# 🔹 STEP 1 — Mock job data (replace later with real scraping)
def fetch_jobs():
    return [
        {
            "title": "Senior Product Designer",
            "company": "Stripe",
            "url": "https://stripe.com/jobs",
            "category": "product",
            "score": 85,
            "reasons": [
                "Matches your preferred role",
                "Strong product design focus",
                "B2B experience relevant"
            ]
        },
        {
            "title": "Product Designer",
            "company": "Linear",
            "url": "https://linear.app/jobs",
            "category": "product",
            "score": 95,
            "reasons": [
                "Perfect experience level",
                "Strong product culture",
                "Modern SaaS environment"
            ]
        },
        {
            "title": "UX/UI Designer",
            "company": "Vercel",
            "url": "https://vercel.com/careers",
            "category": "ux",
            "score": 80,
            "reasons": [
                "Strong UX alignment",
                "Frontend exposure",
                "Modern tooling"
            ]
        }
    ]

# 🔹 STEP 2 — Save to jobs.json
def save_jobs_to_json(jobs):
    with open("jobs.json", "w") as f:
        json.dump(jobs, f, indent=2)

# 🔹 STEP 3 — Push to GitHub
def push_to_github():
    os.system("git add jobs.json")
    os.system('git commit -m "update jobs"')
    os.system("git push")

# 🔹 MAIN RUN
def run():
    print("Fetching jobs...")
    jobs = fetch_jobs()

    print("Saving jobs.json...")
    save_jobs_to_json(jobs)

    print("Pushing to GitHub...")
    push_to_github()

    print("Done ✅")

if __name__ == "__main__":
    run()
