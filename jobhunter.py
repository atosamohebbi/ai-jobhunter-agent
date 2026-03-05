print("JobHunter AI Agent starting...")

import requests

def fetch_jobs():
    url = "https://remotive.com/api/remote-jobs"
    response = requests.get(url)
    data = response.json()
    
    jobs = data["jobs"]
    
    filtered_jobs = []

    keywords = [
        "product designer",
        "ux designer",
        "ui designer",
        "ux/ui",
        "interaction designer"
    ]

    for job in jobs:
        title = job["title"].lower()

        if any(keyword in title for keyword in keywords):
            filtered_jobs.append({
                "title": job["title"],
                "company": job["company_name"],
                "url": job["url"]
            })

    return filtered_jobs


def main():
    jobs = fetch_jobs()

    print("Jobs found:")
    
    for job in jobs[:10]:
        print(job["title"], "-", job["company"])
        print(job["url"])
        print()


if __name__ == "__main__":
    main()
