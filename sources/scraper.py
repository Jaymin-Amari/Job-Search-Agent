"""
Scrapes company watchlist career pages for new job postings.
Handles confirmed URLs, auto-find URL discovery (pattern + Google Search fallback),
and ATS-specific parsing (Greenhouse JSON API, Lever JSON API, generic HTML).
"""

import os
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import TARGET_ROLES, WATCHLIST_CONFIRMED, WATCHLIST_AUTO_FIND

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

_CAREER_PATH_CANDIDATES = [
    "/careers",
    "/jobs",
    "/about/careers",
    "/about/jobs",
    "/work-with-us",
    "/join-us",
    "/join",
    "/opportunities",
    "/open-roles",
]

# Broad keyword set for relevance filtering
_ROLE_KEYWORDS = [r.lower() for r in TARGET_ROLES] + [
    "product",
    "operations",
    " ops",
    "gtm",
    "revops",
    "program manager",
    "venture",
    "architect",
    "enablement",
    "systems",
    "strategy",
    "business development",
]


def get_watchlist_jobs() -> tuple[list[dict], list[str]]:
    """Scrape all watchlist pages. Returns (jobs, notes_for_briefing)."""
    jobs = []
    notes = []

    # Build full source map: confirmed + auto-discovered
    sources: dict[str, str] = dict(WATCHLIST_CONFIRMED)
    for company in WATCHLIST_AUTO_FIND:
        url = _find_career_url(company)
        if url:
            sources[company] = url
        else:
            notes.append(f"{company} — no careers page found")

    for company, url in sources.items():
        found, note = _scrape_career_page(company, url)
        if note:
            notes.append(note)
        if found is not None:
            jobs.extend(found)
        elif note is None:
            # None return with no note means generic failure
            notes.append(f"{company} — career page blocked or unreachable")

    return jobs, notes


# ── URL discovery ──────────────────────────────────────────────────────────────

def _find_career_url(company: str) -> str | None:
    slug = _to_slug(company)
    base_candidates = [
        f"https://www.{slug}.com",
        f"https://{slug}.com",
        f"https://www.{slug}.ca",
        f"https://{slug}.ca",
        f"https://www.{slug}.org",
    ]
    for base in base_candidates:
        for path in _CAREER_PATH_CANDIDATES:
            try:
                url = base + path
                resp = requests.get(url, headers=_HEADERS, timeout=10, allow_redirects=True)
                if resp.status_code == 200 and _has_job_content(resp.text):
                    return url
            except Exception:
                continue

    return _google_search_career_url(company)


def _to_slug(company: str) -> str:
    """Convert company name to a plausible domain slug."""
    slug = company.lower()
    # Remove common suffixes that don't appear in domains
    for suffix in [" canada", " inc", " ltd", " corp", " discovery district",
                   " university", " college", " district", " concordia"]:
        slug = slug.replace(suffix, "")
    # Remove non-alphanumeric except dots
    slug = re.sub(r"[^a-z0-9]", "", slug)
    return slug


def _google_search_career_url(company: str) -> str | None:
    api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        return None
    try:
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": api_key,
                "cx": cse_id,
                "q": f"{company} careers jobs",
                "num": 5,
            },
            timeout=10,
        )
        for item in resp.json().get("items", []):
            link = item.get("link", "")
            if any(p in link.lower() for p in ["/careers", "/jobs", "/work-with", "/join", "/openings"]):
                return link
    except Exception:
        pass
    return None


def _has_job_content(html: str) -> bool:
    text = html.lower()
    markers = ["job opening", "open position", "apply now", "job listing",
               "we're hiring", "current openings", "join our team", "view openings"]
    return any(m in text for m in markers)


# ── Career page scraping ───────────────────────────────────────────────────────

def _scrape_career_page(company: str, url: str) -> tuple[list[dict] | None, str | None]:
    """Returns (jobs_or_None, optional_note)."""
    host = urlparse(url).netloc.lower()

    if "greenhouse.io" in host or "greenhouse.io" in url:
        return _scrape_greenhouse(company, url)
    if "lever.co" in host or "lever.co" in url:
        return _scrape_lever(company, url)

    # Blanka uses Dover (has Cloudflare-style verification)
    if "dover.com" in url or company.lower() == "blanka":
        result = _scrape_generic(company, url)
        if result is None:
            return None, "Blanka — career page has human verification, check manually"
        return result, None

    return _scrape_generic(company, url)


def _scrape_greenhouse(company: str, url: str) -> tuple[list[dict] | None, str | None]:
    try:
        match = re.search(r"greenhouse\.io/([^/?#]+)", url)
        if not match:
            return _scrape_generic(company, url)
        slug = match.group(1)
        api_url = f"https://boards.greenhouse.io/{slug}/jobs.json"
        resp = requests.get(api_url, headers=_HEADERS, timeout=12)
        if resp.status_code != 200:
            return _scrape_generic(company, url)
        jobs = []
        for item in resp.json().get("jobs", []):
            title = item.get("title", "")
            if not _is_relevant(title):
                continue
            jobs.append({
                "title": title,
                "company": company,
                "url": item.get("absolute_url", url),
                "description": item.get("content", "")[:4000],
                "location": item.get("location", {}).get("name", ""),
                "source": "watchlist",
            })
        return jobs, None
    except Exception:
        return _scrape_generic(company, url)


def _scrape_lever(company: str, url: str) -> tuple[list[dict] | None, str | None]:
    try:
        match = re.search(r"lever\.co/([^/?#]+)", url)
        if not match:
            return _scrape_generic(company, url)
        slug = match.group(1)
        api_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        resp = requests.get(api_url, headers=_HEADERS, timeout=12)
        if resp.status_code != 200:
            return _scrape_generic(company, url)
        jobs = []
        for item in resp.json():
            title = item.get("text", "")
            if not _is_relevant(title):
                continue
            jobs.append({
                "title": title,
                "company": company,
                "url": item.get("hostedUrl", url),
                "description": item.get("descriptionPlain", "")[:4000],
                "location": item.get("categories", {}).get("location", ""),
                "source": "watchlist",
            })
        return jobs, None
    except Exception:
        return _scrape_generic(company, url)


def _scrape_generic(company: str, url: str) -> list[dict] | None:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        jobs = []
        seen_urls: set[str] = set()
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if not text or len(text) < 4 or len(text) > 120:
                continue
            if not _is_relevant(text):
                continue
            href = a["href"]
            full_url = href if href.startswith("http") else urljoin(url, href)
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            jobs.append({
                "title": text,
                "company": company,
                "url": full_url,
                "description": "",  # fetched lazily during scoring in agent.py
                "location": "",
                "source": "watchlist",
            })
        return jobs
    except Exception:
        return None


def _is_relevant(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in _ROLE_KEYWORDS)


if __name__ == "__main__":
    # Quick scraper smoke test — scrapes first 5 confirmed watchlist pages
    from config import WATCHLIST_CONFIRMED
    sample = dict(list(WATCHLIST_CONFIRMED.items())[:5])
    for name, url in sample.items():
        result, note = _scrape_career_page(name, url)
        count = len(result) if result else 0
        print(f"{name}: {count} relevant jobs found" + (f" | {note}" if note else ""))
