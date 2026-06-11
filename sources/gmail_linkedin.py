"""
Reads LinkedIn job URLs from the Drive staging file that Make.com writes to.
Make.com watches Gmail for LinkedIn job alert emails, extracts URLs, and appends
them one per line to linkedin_staging.txt in the Drive output folder throughout
the day. This module reads and clears that file each morning during the agent run.
"""

import requests
from bs4 import BeautifulSoup

import drive_handler
from config import DRIVE_OUTPUT_FOLDER_ID, STAGING_FILE_NAME


def get_linkedin_jobs(dry_run: bool = False) -> list[dict]:
    """Read staged LinkedIn job URLs from Drive, fetch their descriptions, clear the file."""
    raw = drive_handler.read_text_file_in_folder(DRIVE_OUTPUT_FOLDER_ID, STAGING_FILE_NAME)
    urls = [line.strip() for line in raw.splitlines() if line.strip()]
    if not urls:
        print("[linkedin] No staged jobs found.")
        return []

    print(f"[linkedin] {len(urls)} staged URL(s) found.")
    jobs = []
    for url in urls:
        description = _fetch_job_description(url)
        jobs.append({
            "url": url,
            "title": "",
            "company": "",
            "location": "",
            "description": description,
            "source": "linkedin",
        })

    if not dry_run:
        drive_handler.write_text_file_in_folder(DRIVE_OUTPUT_FOLDER_ID, STAGING_FILE_NAME, "")
        print("[linkedin] Staging file cleared.")

    return jobs


def _fetch_job_description(url: str) -> str:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "lxml")
        # LinkedIn job description lives in a div with "description" in the class
        desc = soup.find("div", {"class": lambda c: c and "description" in c.lower()})
        if desc:
            return desc.get_text(separator="\n", strip=True)[:5000]
        # Fallback: strip all nav/header/footer and return body text
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:5000]
    except Exception:
        return ""
