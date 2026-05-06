"""
Searches Indeed via the Indeed MCP server using Claude API tool_use.

The Indeed MCP is pre-connected to Jaymin's Anthropic account — no URL or
token env vars required. The server is referenced by its label only.
"""

import json

import anthropic

from config import SEARCH_LOCATIONS, TARGET_ROLES


def search_indeed(client: anthropic.Anthropic) -> list[dict]:
    """Search Indeed for all target roles across all locations. Returns deduplicated job list."""
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for role in TARGET_ROLES:
        for location in SEARCH_LOCATIONS:
            results = _search_role(client, role, location)
            for job in results:
                url = job.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    jobs.append(job)

    print(f"[indeed] {len(jobs)} unique jobs found.")
    return jobs


def _search_role(client: anthropic.Anthropic, role: str, location: str) -> list[dict]:
    try:
        response = client.beta.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=[{"type": "mcp", "server_label": "indeed"}],
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Search Indeed for '{role}' jobs in '{location}' posted in the last 24 hours. "
                        "Return a JSON array where each item has: "
                        "title, company, url, description, location, date_posted. "
                        "Only include postings from the last 24 hours. "
                        "Return only the JSON array, no other text."
                    ),
                }
            ],
            betas=["mcp-client-2025-04-04"],
        )

        for block in response.content:
            if hasattr(block, "text"):
                text = block.text.strip()
                start = text.find("[")
                end = text.rfind("]") + 1
                if start >= 0 and end > start:
                    raw = json.loads(text[start:end])
                    for job in raw:
                        job["source"] = "indeed"
                    return raw

    except Exception as e:
        print(f"[indeed] Error searching '{role}' in '{location}': {e}")

    return []
