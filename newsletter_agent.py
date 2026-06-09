"""
newsletter_agent.py — Main entry point for The Breakdown newsletter agent.

Modes:
  GENERATE_ONLY=true  — Generate preview only, save to newsletter_preview.json
                        (runs automatically every Tuesday, awaits your approval)
  Normal              — Load saved preview and publish to Substack + social

Runs via: GitHub Actions two-job flow:
  1. generate  (automatic) — creates preview, posts summary for review
  2. publish   (requires your approval in GitHub Actions) — publishes after you approve
"""

import os
import sys
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.sources   import fetch_rugby_content
from src.generator import generate_newsletter
from src.publisher import publish_to_substack
from src.social    import post_to_reddit, post_to_bluesky

PREVIEW_FILE = "newsletter_preview.json"


def main():
    print("=" * 50)
    print("  THE BREAKDOWN — Newsletter Agent")
    print("=" * 50)

    generate_only = os.environ.get("GENERATE_ONLY", "false").lower() == "true"
    if generate_only:
        print("  Mode: GENERATE ONLY (awaiting your approval to publish)")

    # ── 1. Generate or load preview ───────────────────
    if generate_only or not os.path.exists(PREVIEW_FILE):
        print("\n[1/2] Fetching content from sources...")
        items = fetch_rugby_content(days_back=7)
        if not items:
            print("ERROR: No content fetched. Check network and sources.")
            sys.exit(1)

        print("\n[2/2] Generating newsletter with Claude...")
        newsletter = generate_newsletter(items)
        print(f"  Subject: {newsletter['subject']}")

        with open(PREVIEW_FILE, "w") as f:
            json.dump(newsletter, f, indent=2)
        print(f"  Preview saved to {PREVIEW_FILE}")

    else:
        print(f"\n[1/1] Loading saved preview from {PREVIEW_FILE}...")
        with open(PREVIEW_FILE) as f:
            newsletter = json.load(f)
        print(f"  Subject: {newsletter['subject']}")

    # ── Generate-only: write summary for review ───────
    if generate_only:
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
        if summary_path:
            with open(summary_path, "w") as f:
                f.write(f"## The Breakdown — Preview\n\n")
                f.write(f"**Subject:** {newsletter['subject']}\n\n")
                f.write(f"---\n\n")
                f.write(newsletter.get("body_text", "").replace("\n", "  \n"))
        print("\n✓ Preview ready.")
        print("  Go to GitHub Actions and approve the 'publish' job to send.")
        return

    # ── Publish ───────────────────────────────────────
    print("\n[Publishing to Substack...]")
    url = publish_to_substack(newsletter)
    print(f"  Published: {url}")

    print("\n[Posting to social media...]")
    post_to_reddit(newsletter, url)
    post_to_bluesky(newsletter, url)
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
