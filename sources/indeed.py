"""
Searches Indeed using python-jobspy (no API key required).
Searches each target role in Toronto for the last 24 hours.
"""

import anthropic  # kept so agent.py import signature stays unchanged

from config import TARGET_ROLES

try:
    from jobspy import scrape_jobs
    _JOBSPY_AVAILABLE = True
except ImportError:
    _JOBSPY_AVAILABLE = False


def search_indeed(client: anthropic.Anthropic) -> list[dict]:
    """Search Indeed for all target roles. Returns deduplicated job list."""
    if not _JOBSPY_AVAILABLE:
        print("[indeed] python-jobspy not installed — skipping Indeed source.")
        return []

    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for role in TARGET_ROLES:
        try:
            results = scrape_jobs(
                site_name=["indeed"],
                search_term=role,
                location="Toronto, ON",
                country_indeed="Canada",
                results_wanted=25,
                hours_old=24,
                verbose=0,
            )
            if results is None or len(results) == 0:
                continue
            for _, row in results.iterrows():
                url = str(row.get("job_url") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                jobs.append({
                    "title": str(row.get("title") or ""),
                    "company": str(row.get("company") or ""),
                    "location": str(row.get("location") or ""),
                    "url": url,
                    "description": str(row.get("description") or "")[:4000],
                    "date_posted": row.get("date_posted"),
                    "source": "indeed",
                })
        except Exception as e:
            print(f"[indeed] Error searching '{role}': {e}")
            continue

    print(f"[indeed] {len(jobs)} unique jobs found.")
    return jobs
