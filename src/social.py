"""
social.py — Posts newsletter announcements to Reddit after each publish.

Targets:
  r/rugbycoaches  — primary (coaching-focused audience, high relevance)
  r/rugbyunion    — secondary (larger general audience)

Required env vars (set as GitHub Secrets):
  REDDIT_CLIENT_ID      — from reddit.com/prefs/apps (string under app name)
  REDDIT_CLIENT_SECRET  — from reddit.com/prefs/apps
  REDDIT_USERNAME       — Reddit account username
  REDDIT_PASSWORD       — Reddit account password
"""

import os
import time
import requests


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_token(client_id: str, client_secret: str,
               username: str, password: str) -> str:
    """Exchange credentials for a Reddit OAuth bearer token."""
    resp = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=(client_id, client_secret),
        data={
            "grant_type": "password",
            "username":   username,
            "password":   password,
        },
        headers={"User-Agent": "TheBreakdownBot/1.0 (rugby coaching newsletter)"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _submit_link(token: str, subreddit: str,
                 title: str, url: str) -> dict:
    """Submit a link post to a subreddit."""
    resp = requests.post(
        "https://oauth.reddit.com/api/submit",
        headers={
            "Authorization": f"bearer {token}",
            "User-Agent":    "TheBreakdownBot/1.0 (rugby coaching newsletter)",
        },
        data={
            "sr":      subreddit,
            "kind":    "link",
            "title":   title,
            "url":     url,
            "nsfw":    False,
            "spoiler": False,
            "resubmit": True,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

SUBREDDITS = [
    ("rugbycoaches", True),   # (name, required)
    ("rugbyunion",   False),  # optional — larger community, more forgiving of failures
]


def post_to_reddit(newsletter: dict, post_url: str) -> None:
    """
    Post a newsletter announcement to Reddit.

    Args:
        newsletter: dict returned by generate_newsletter()
                    must contain 'subject' and 'week' keys
        post_url:   public URL of the published Substack post
    """
    client_id     = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
    username      = os.environ.get("REDDIT_USERNAME", "")
    password      = os.environ.get("REDDIT_PASSWORD", "")

    if not all([client_id, client_secret, username, password]):
        print("  ⚠  Reddit credentials not set — skipping social post.")
        return

    # Build the post title — short, no clickbait
    week    = newsletter.get("week", "This Week")
    subject = newsletter.get("subject", "The Breakdown — Rugby Coaching Newsletter")
    title   = f"[Newsletter] The Breakdown | {week} — {subject}"
    # Cap at Reddit's 300-char title limit
    if len(title) > 295:
        title = title[:292] + "..."

    try:
        token = _get_token(client_id, client_secret, username, password)
    except Exception as e:
        print(f"  ✗ Reddit auth failed: {e}")
        return

    for subreddit, required in SUBREDDITS:
        try:
            result = _submit_link(token, subreddit, title, post_url)
            submitted_url = (
                result.get("json", {})
                      .get("data", {})
                      .get("url", "unknown")
            )
            print(f"  ✓ Posted to r/{subreddit}: {submitted_url}")
        except Exception as e:
            if required:
                print(f"  ✗ Failed to post to r/{subreddit}: {e}")
            else:
                print(f"  ⚠  Optional r/{subreddit} post skipped: {e}")

        # Be polite to Reddit's rate limiter
        time.sleep(2)
