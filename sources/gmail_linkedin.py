"""
Reads LinkedIn job URLs from dated staging files that Make.com writes to Drive.
Make.com creates one file per Gmail alert, named linkedin_<date>.txt, with one
URL per line. This module reads all linkedin_*.txt files in the output folder,
collects every URL, then deletes each file after processing.
"""

import requests
from bs4 import BeautifulSoup

import drive_handler
from config import DRIVE_OUTPUT_FOLDER_ID, STAGING_FILE_PREFIX


def get_linkedin_jobs(dry_run: bool = False) -> list[dict]:
    """Read all linkedin_*.txt staging files from Drive, return jobs, delete files."""
    staging_files = drive_handler.list_staging_files(DRIVE_OUTPUT_FOLDER_ID, STAGING_FILE_PREFIX)
    if not staging_files:
        print("[linkedin] No staging files found.")
        return []

    print(f"[linkedin] {len(staging_files)} staging file(s) found.")
    all_urls: list[str] = []
    for f in staging_files:
        raw = drive_handler.read_file_by_id(f["id"])
        urls = [line.strip() for line in raw.splitlines() if line.strip()]
        print(f"[linkedin]   {f['name']}: {len(urls)} URL(s)")
        all_urls.extend(urls)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_urls = [u for u in all_urls if not (u in seen or seen.add(u))]

    jobs = []
    for url in unique_urls:
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
        for f in staging_files:
            drive_handler.delete_file(f["id"])
        print(f"[linkedin] Deleted {len(staging_files)} staging file(s).")

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
