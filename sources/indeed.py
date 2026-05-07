"""
Searches Indeed via the Indeed MCP using Claude API tool_use.

Note: the 'type: mcp' tool format only works within Claude.ai's connected
MCP environment. When called from a standalone Python script via the API,
the server_label approach is not supported — the agent logs a warning and
skips Indeed gracefully.
"""

import json

import anthropic

from config import SEARCH_LOCATIONS, TARGET_ROLES

_MCP_UNSUPPORTED_MSG = (
    "[indeed] Indeed MCP is not accessible via the standalone API "
    "(server_label requires a Claude.ai session). Skipping Indeed source.\n"
    "  → To enable Indeed: provide INDEED_MCP_URL in .env pointing to a "
    "publicly reachable Indeed MCP server endpoint."
)


def search_indeed(client: anthropic.Anthropic) -> list[dict]:
    """Search Indeed for all target roles across all locations. Returns deduplicated job list."""
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for role in TARGET_ROLES:
        for location in SEARCH_LOCATIONS:
            results, unsupported = _search_role(client, role, location)
            if unsupported:
                print(_MCP_UNSUPPORTED_MSG)
                return []
            for job in results:
                url = job.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    jobs.append(job)

    print(f"[indeed] {len(jobs)} unique jobs found.")
    return jobs


def _search_role(
    client: anthropic.Anthropic, role: str, location: str
) -> tuple[list[dict], bool]:
    """Returns (jobs, mcp_unsupported). mcp_unsupported=True means caller should abort."""
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
                    return raw, False

    except anthropic.BadRequestError as e:
        if "Input tag 'mcp'" in str(e):
            return [], True  # signal caller to abort all Indeed searches
        print(f"[indeed] Error searching '{role}' in '{location}': {e}")
    except Exception as e:
        print(f"[indeed] Error searching '{role}' in '{location}': {e}")

    return [], False
