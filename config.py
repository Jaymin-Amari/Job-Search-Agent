import os

# ── Drive IDs ──────────────────────────────────────────────────────────────────
MASTER_RESUME_ID = "1rku_cK6stv7lc_CLQpgGQrNJBlQY6D04"
DRIVE_OUTPUT_FOLDER_ID = "13rj--5qMNRlUbxd4q6ZohyzxG3saHsIX"
STAGING_FILE_NAME = "linkedin_staging.json"
SEEN_JOBS_FILE_NAME = "seen_jobs.log"
DAILY_BRIEFING_DOC_NAME = "Daily Briefing"

# ── Target roles and location ──────────────────────────────────────────────────
SEARCH_LOCATIONS = ["Toronto", "GTA", "Remote"]

TARGET_ROLES = [
    "Product Manager",
    "Product Owner",
    "Product Owner Lead",
    "Head of Operations",
    "VP Operations",
    "Business Operations",
    "Strategic Enablement",
    "Systems Operations",
    "GTM Architect",
    "RevOps",
    "Program Manager",
    "Venture Architect",
    "Business Architect",
]

EXCLUDED_TITLES = ["Director", "Chief of Staff"]

# ── Network flags ──────────────────────────────────────────────────────────────
# Key = lowercase company name fragment; value = note for briefing
NETWORK_FLAGS = {
    "riipen": "Riipen — Tortise works here — reach out for referral before applying",
    "1password": "1Password — Luki is a connection — flag",
    "wealthsimple": "Wealthsimple — Lisa Dunford connection — flag",
}

# ── Watchlist: confirmed URLs ──────────────────────────────────────────────────
WATCHLIST_CONFIRMED = {
    "Blanka": "https://app.dover.com/dover/careers/c7ce686d-ec82-4176-9df3-583daa4d65eb",
    "PheedLoop": "https://pheedloop.com/more/careers#Job-Openings",
    "DealMaker": "https://www.dealmaker.tech/careers#open-positions",
    "Passage": "https://www.passage.com/about",
    "Rally Assets": "https://rallyassets.com/about/team/jobs/",
    "SWTCH Energy": "https://swtchenergy.com/careers/",
    "Yspace Job Board": "https://www.yorku.ca/yspace/startups/job-board/",
    "The Knowledge Society": "https://www.tks.world/team-and-careers",
    "VentureLAB": "https://www.venturelab.ca/job-board",
}

# ── Watchlist: auto-find companies ────────────────────────────────────────────
WATCHLIST_AUTO_FIND = [
    "MaRS Discovery District",
    "Communitech",
    "Ontario Centre of Innovation",
    "DMZ",
    "University of Toronto",
    "Toronto Metropolitan University",
    "OCAD University",
    "York University",
    "George Brown College",
    "Humber College",
    "Seneca College",
    "Centennial College",
    "Toronto Region Board of Trade",
    "NGen Canada",
    "Mitacs",
    "NRC IRAP",
    "Futurpreneur Canada",
    "Startup Canada",
    "Creative Destruction Lab",
    "OneEleven",
    "City of Toronto",
    "Owner.com",
    "Relay",
    "Fellow",
    "Float Financial",
    "Humi",
    "Properly",
    "Invest Toronto",
    "Toronto Global",
    "Platform Calgary",
    "District 3 Concordia",
]

# ── Queer-role detection: flag for manual handling, skip auto-cover-letter ─────
QUEER_ROLE_KEYWORDS = [
    "lgbtq",
    "2slgbtq",
    "queer",
    "trans ",
    "transgender",
    "pride",
    "rainbow",
    "two-spirit",
    "non-binary inclusion",
]

# ── Dry-run mode: set DRY_RUN=true to skip all Drive writes ───────────────────
DRY_RUN = os.environ.get("DRY_RUN", "").lower() == "true"
