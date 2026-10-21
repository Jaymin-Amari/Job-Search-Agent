#!/usr/bin/env python3
"""
Job Search Agent — discovery-only mode.

Fetches jobs from Indeed, LinkedIn staging files, and watchlist career pages,
deduplicates against seen_jobs, filters by title relevance, writes surviving
jobs to a "Daily Feed" Google Doc, and updates seen_jobs.

Run:
  python agent.py               # live run (reads/writes Drive)
  DRY_RUN=true python agent.py  # prints feed to stdout, no Drive writes
"""

import os
import re
import time
from datetime import datetime, timezone

import config
import drive_handler
from sources import gmail_linkedin, indeed, scraper


def main() -> None:
    dry_run = config.DRY_RUN
    if dry_run:
        print("[DRY RUN] Drive writes disabled — feed will print to stdout.")

    today = datetime.now(timezone.utc).strftime("%B %d, %Y").upper()
    date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── 1. Load seen_jobs from Drive ───────────────────────────────────────────
    print("Reading seen_jobs doc from Drive...")
    seen_doc_id = drive_handler.get_or_create_briefing_doc(
        config.DRIVE_OUTPUT_FOLDER_ID, config.SEEN_JOBS_DOC_NAME
    )
    seen_raw = drive_handler.read_doc_text(seen_doc_id)
    seen_urls: set[str] = {line.strip() for line in seen_raw.splitlines() if line.strip()}

    # ── 2. Fetch all jobs ──────────────────────────────────────────────────────
    print("Fetching LinkedIn jobs from Drive staging file...")
    linkedin_jobs = gmail_linkedin.get_linkedin_jobs(dry_run=dry_run)

    print("Searching Indeed...")
    indeed_jobs = indeed.search_indeed()

    print("Scraping watchlist career pages...")
    watchlist_jobs, scraper_notes = scraper.get_watchlist_jobs()

    all_jobs = linkedin_jobs + indeed_jobs + watchlist_jobs
    print(f"Total jobs fetched: {len(all_jobs)}")

    # ── 3. Deduplicate against seen_jobs ──────────────────────────────────────
    new_jobs: list[dict] = []
    for job in all_jobs:
        url = job.get("url", "").strip()
        if url and url not in seen_urls:
            new_jobs.append(job)
            seen_urls.add(url)

    print(f"New (unseen): {len(new_jobs)}")

    # ── 4. Filter: excluded titles ─────────────────────────────────────────────
    def _is_excluded(title: str) -> bool:
        t = title.lower()
        return any(ex.lower() in t for ex in config.EXCLUDED_TITLES)

    jobs_after_exclude = [j for j in new_jobs if not _is_excluded(j.get("title", ""))]
    excluded_count = len(new_jobs) - len(jobs_after_exclude)
    if excluded_count:
        print(f"Excluded (title filter): {excluded_count}")

    # ── 5. Filter: title relevance ────────────────────────────────────────────
    relevant_jobs = [j for j in jobs_after_exclude if _is_title_relevant(j.get("title", ""))]
    irrelevant_count = len(jobs_after_exclude) - len(relevant_jobs)
    if irrelevant_count:
        print(f"Skipped (title mismatch): {irrelevant_count}")

    print(f"Jobs in feed: {len(relevant_jobs)}")

    # ── 6. Build feed document ────────────────────────────────────────────────
    feed = _format_feed(today, relevant_jobs, scraper_notes)

    # ── 7. Write outputs ───────────────────────────────────────────────────────
    if dry_run:
        print("\n" + "=" * 60)
        print(feed)
        print("=" * 60)
    else:
        _drive_write_with_retry(feed, seen_urls, seen_doc_id)

    print(
        f"\nDone. {len(relevant_jobs)} job(s) written to Daily Feed. "
        f"{excluded_count + irrelevant_count} filtered out."
    )


# ── Feed formatter ─────────────────────────────────────────────────────────────

def _format_feed(today: str, jobs: list[dict], scraper_notes: list[str]) -> str:
    lines = [
        "═══════════════════════════════════════",
        f"📅 {today} — DAILY JOB FEED",
        f"New postings: {len(jobs)}",
        "═══════════════════════════════════════",
        "",
    ]

    if not jobs:
        lines.append("No new relevant jobs found today.")
    else:
        for job in jobs:
            title = job.get("title") or "Unknown Role"
            company = job.get("company") or "Unknown Company"
            url = job.get("url") or ""
            source = job.get("source") or "unknown"
            date_posted = job.get("date_posted")
            date_str = f"  Posted: {str(date_posted)[:10]}" if date_posted else ""

            lines += [
                f"### {title} — {company}",
                f"Source: {source}{date_str}",
                f"URL: {url}",
                "",
            ]

    if scraper_notes:
        lines += [
            "── ⚠ SCRAPER NOTES ──────────────────────",
        ]
        for note in scraper_notes:
            lines.append(f"  • {note}")
        lines.append("")

    return "\n".join(lines)


# ── Utility helpers ────────────────────────────────────────────────────────────

def _is_title_relevant(title: str) -> bool:
    """Return True if the title contains any TARGET_ROLES phrase (case-insensitive).
    Blank titles pass through so LinkedIn jobs with no title field reach the feed."""
    if not title or not title.strip():
        return True
    t = title.lower()
    return any(role.lower() in t for role in config.TARGET_ROLES)


def _drive_write_with_retry(feed: str, seen_urls: set[str], seen_doc_id: str) -> None:
    """Write Daily Feed doc and seen_jobs doc to Drive, retrying up to 3 times."""
    for attempt in range(1, 4):
        try:
            drive_handler.reset_services()

            print("Updating Daily Feed Google Doc...")
            feed_doc_id = drive_handler.get_or_create_briefing_doc(
                config.DRIVE_OUTPUT_FOLDER_ID, "Daily Feed"
            )
            drive_handler.prepend_to_doc(feed_doc_id, feed)

            print("Writing seen_jobs Google Doc...")
            drive_handler.overwrite_google_doc(seen_doc_id, "\n".join(sorted(seen_urls)))
            return
        except Exception as e:
            if attempt == 3:
                print(f"Drive write failed after 3 attempts: {e}")
                raise
            print(f"Drive write failed (attempt {attempt}/3): {e} — retrying in 5s")
            time.sleep(5)


if __name__ == "__main__":
    main()
