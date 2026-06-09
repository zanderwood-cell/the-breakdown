"""
newsletter_agent.py — Main entry point for The Breakdown newsletter agent.

Run manually:   python newsletter_agent.py
Dry run:        DRY_RUN=true python newsletter_agent.py
Runs via:       GitHub Actions every Tuesday at 7:00 AM UTC

Required env vars (set as GitHub Secrets or in a local .env file):
  ANTHROPIC_API_KEY   — from console.anthropic.com
  SUBSTACK_EMAIL      — your Substack login email
  SUBSTACK_PASSWORD   — your Substack password
  SUBSTACK_SUBDOMAIN  — your Substack slug (e.g. "thebreakdown")
"""

import os
import sys

# Load .env file if present (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.sources   import fetch_rugby_content
from src.generator import generate_newsletter
from src.publisher import publish_to_substack
from src.social    import post_to_reddit


def main():
    print("=" * 50)
    print("  THE BREAKDOWN — Newsletter Agent")
    print("=" * 50)

    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    if dry_run:
        print("  Mode: DRY RUN (will not publish)")

    # ── 1. Fetch content ─────────────────────────────
    print("\n[1/3] Fetching content from sources...")
    items = fetch_rugby_content(days_back=7)

    if not items:
        print("ERROR: No content fetched. Check network and sources.")
        sys.exit(1)

    # ── 2. Generate newsletter ────────────────────────
    print("\n[2/3] Generating newsletter with Claude...")
    newsletter = generate_newsletter(items)
    print(f"  Subject: {newsletter['subject']}")

    # ── 3. Publish (or print) ─────────────────────────
    if dry_run:
        print("\n[3/3] DRY RUN — newsletter preview:\n")
        print("─" * 50)
        print(newsletter["body_text"])
        print("─" * 50)
        print("\nTo publish for real, run without DRY_RUN=true.")
    else:
        print("\n[3/3] Publishing to Substack...")
        url = publish_to_substack(newsletter)
        print(f"  Published: {url}")

        # ── 4. Announce on Reddit ─────────────────────
        print("\n[4/4] Posting to Reddit...")
        post_to_reddit(newsletter, url)
        print("\n✓ Done!")


if __name__ == "__main__":
    main()"""
newsletter_agent.py — Main entry point for The Breakdown newsletter agent.

Run manually:   python newsletter_agent.py
Dry run:        DRY_RUN=true python newsletter_agent.py
Runs via:       GitHub Actions every Tuesday at 7:00 AM UTC

Required env vars (set as GitHub Secrets or in a local .env file):
  ANTHROPIC_API_KEY   — from console.anthropic.com
  SUBSTACK_EMAIL      — your Substack login email
  SUBSTACK_PASSWORD   — your Substack password
  SUBSTACK_SUBDOMAIN  — your Substack slug (e.g. "thebreakdown")
"""

import os
import sys

# Load .env file if present (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.sources   import fetch_rugby_content
from src.generator import generate_newsletter
from src.publisher import publish_to_substack


def main():
    print("=" * 50)
    print("  THE BREAKDOWN — Newsletter Agent")
    print("=" * 50)

    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    if dry_run:
        print("  Mode: DRY RUN (will not publish)")

    # ── 1. Fetch content ─────────────────────────────
    print("\n[1/3] Fetching content from sources...")
    items = fetch_rugby_content(days_back=7)

    if not items:
        print("ERROR: No content fetched. Check network and sources.")
        sys.exit(1)

    # ── 2. Generate newsletter ────────────────────────
    print("\n[2/3] Generating newsletter with Claude...")
    newsletter = generate_newsletter(items)
    print(f"  Subject: {newsletter['subject']}")

    # ── 3. Publish (or print) ─────────────────────────
    if dry_run:
        print("\n[3/3] DRY RUN — newsletter preview:\n")
        print("─" * 50)
        print(newsletter["body_text"])
        print("─" * 50)
        print("\nTo publish for real, run without DRY_RUN=true.")
    else:
        print("\n[3/3] Publishing to Substack...")
        url = publish_to_substack(newsletter)
        print(f"\n✓ Done! Published: {url}")


if __name__ == "__main__":
    main()
