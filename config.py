import os

from dotenv import load_dotenv
load_dotenv()

# ── Drive IDs ──────────────────────────────────────────────────────────────────
MASTER_RESUME_ID = "1Ak_C7oJUcNUESUYPX-Ux0IwlLynkfOTeg3cxl1GATN8"
DRIVE_OUTPUT_FOLDER_ID = "1tzVvQdZcgb_q1fcq_mhwjiCEMWTEunAv"
STAGING_FILE_PREFIX = "linkedin_"
SEEN_JOBS_DOC_NAME = "seen_jobs"
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

# ── Watchlist: all career page URLs (hardcoded) ───────────────────────────────
WATCHLIST_CONFIRMED = {
    # ── SOP confirmed URLs ────────────────────────────────────────────────────
    "Blanka": "https://app.dover.com/dover/careers/c7ce686d-ec82-4176-9df3-583daa4d65eb",
    "PheedLoop": "https://pheedloop.com/more/careers#Job-Openings",
    "DealMaker": "https://www.dealmaker.tech/careers#open-positions",
    "Passage": "https://www.passage.com/about",
    "Rally Assets": "https://rallyassets.com/about/team/jobs/",
    "SWTCH Energy": "https://swtchenergy.com/careers/",
    "Yspace Job Board": "https://www.yorku.ca/yspace/startups/job-board/",
    "The Knowledge Society": "https://www.tks.world/team-and-careers",
    "VentureLAB": "https://www.venturelab.ca/job-board",
    # ── Innovation hubs + ecosystem orgs ─────────────────────────────────────
    "MaRS Discovery District": "https://www.marsdd.com/careers/",
    "Communitech": "https://www.communitech.ca/about/careers.html",
    "Ontario Centre of Innovation": "https://www.oc-innovation.ca/about/careers/",
    "DMZ": "https://www.torontomu.ca/careers/search-available-career-opportunities/",
    "Creative Destruction Lab": "https://creativedestructionlab.com/jobs/",
    "OneEleven": "https://oneeleven.com/open-jobs/",
    "NGen Canada": "https://www.ngen.ca/careers",
    "Mitacs": "https://www.mitacs.ca/careers/",
    "NRC IRAP": "https://recruitment-recrutement.nrc-cnrc.gc.ca/go/All-Jobs/2320717/",
    "Futurpreneur Canada": "https://futurpreneur.ca/en/careers/",
    "Startup Canada": "https://www.startupcan.ca/careers-startup-canada-jobs/",
    "Invest Toronto": "https://www.investtoronto.ca/careers/",
    "Toronto Global": "https://torontoglobal.ca/careers/",
    "Toronto Region Board of Trade": "https://bot.com/About/Careers",
    "City of Toronto": "https://jobs.toronto.ca/jobsatcity/",
    "Platform Calgary": "https://www.platformcalgary.com/about/careers",
    "District 3 Concordia": "https://www.district3.co/jobs",
    # ── Post-secondary institutions ───────────────────────────────────────────
    "University of Toronto": "https://jobs.utoronto.ca/go/Staff-Opportunities/2607517/",
    "Toronto Metropolitan University": "https://www.torontomu.ca/careers/search-available-career-opportunities/",
    "OCAD University": "https://www.ocadu.ca/employment/job-opportunities",
    "York University": "https://hr.info.yorku.ca/viewopportunities/",
    "George Brown College": "https://gbcareers.georgebrown.ca/",
    "Humber College": "https://humber.ca/careers/",
    "Seneca College": "https://www.senecapolytechnic.ca/human-resources/careers.html",
    "Centennial College": "https://www.centennialcollege.ca/about-centennial/careers",
    # ── Toronto tech companies ────────────────────────────────────────────────
    "Owner.com": "https://www.owner.com/careers",
    "Relay": "https://relayfi.com/careers/",
    "Fellow": "https://fellow.ai/careers",
    "Float Financial": "https://floatcard.com/join-us",
    "Humi": "https://www.humi.ca/careers",
    # Properly wound down as an independent company in 2023 — no live careers page
}

# No auto-find needed — all companies are now hardcoded above
WATCHLIST_AUTO_FIND: list[str] = []

# ── Scoring cap ───────────────────────────────────────────────────────────────
# Process at most this many jobs per run (newest first). Prevents timeouts when
# the feed is unusually large after a holiday or weekend gap.
MAX_JOBS_PER_RUN = 50

# ── Queer-role detection: flag for manual handling, skip auto-cover-letter ─────
# Only checked against job title + company name — not description — to avoid
# false positives from diversity boilerplate in generic postings.
QUEER_ROLE_KEYWORDS = [
    "lgbtq",
    "2slgbtq",
    "queer",
    "trans ",
    "transgender",
    "pride",
    "two-spirit",
]

# ── Dry-run mode: set DRY_RUN=true to skip all Drive writes ───────────────────
DRY_RUN = os.environ.get("DRY_RUN", "").lower() == "true"
