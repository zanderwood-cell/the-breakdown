"""
social.py — Posts newsletter announcements to Reddit and Bluesky after each publish.

Targets:
  r/rugbycoaches       — primary Reddit (coaching-focused, high relevance)
  r/rugbyunion         — secondary Reddit (larger general audience)
  @zanderwood.bsky.social — Bluesky (growing platform, open API)

Required env vars (set as GitHub Secrets):
  Reddit (optional — skipped if missing):
    REDDIT_CLIENT_ID      — from reddit.com/prefs/apps
    REDDIT_CLIENT_SECRET  — from reddit.com/prefs/apps
    REDDIT_USERNAME       — Reddit account username
    REDDIT_PASSWORD       — Reddit account password

  Bluesky (optional — skipped if missing):
    BLUESKY_HANDLE        — e.g. zanderwood.bsky.social
    BLUESKY_APP_PASSWORD  — app password from bsky.app/settings/app-passwords
"""

import os
import time
import datetime
import requests


# ---------------------------------------------------------------------------
# Reddit helpers
# ---------------------------------------------------------------------------

def _reddit_token(client_id, client_secret, username, password):
    resp = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=(client_id, client_secret),
        data={"grant_type": "password", "username": username, "password": password},
        headers={"User-Agent": "TheBreakdownBot/1.0 (rugby coaching newsletter)"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _reddit_submit(token, subreddit, title, url):
    resp = requests.post(
        "https://oauth.reddit.com/api/submit",
        headers={
            "Authorization": f"bearer {token}",
            "User-Agent": "TheBreakdownBot/1.0 (rugby coaching newsletter)",
        },
        data={
            "sr": subreddit, "kind": "link", "title": title,
            "url": url, "nsfw": False, "resubmit": True,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


SUBREDDITS = [
    ("rugbycoaches", True),
    ("rugbyunion",   False),
]


def post_to_reddit(newsletter, post_url):
    client_id     = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
    username      = os.environ.get("REDDIT_USERNAME", "")
    password      = os.environ.get("REDDIT_PASSWORD", "")

    if not all([client_id, client_secret, username, password]):
        print("  ⚠  Reddit credentials not set — skipping.")
        return

    week    = newsletter.get("week", "This Week")
    subject = newsletter.get("subject", "The Breakdown — Rugby Coaching Newsletter")
    title   = f"[Newsletter] The Breakdown | {week} — {subject}"
    if len(title) > 295:
        title = title[:292] + "..."

    try:
        token = _reddit_token(client_id, client_secret, username, password)
    except Exception as e:
        print(f"  ✗ Reddit auth failed: {e}")
        return

    for subreddit, required in SUBREDDITS:
        try:
            result = _reddit_submit(token, subreddit, title, post_url)
            submitted = result.get("json", {}).get("data", {}).get("url", "unknown")
            print(f"  ✓ Posted to r/{subreddit}: {submitted}")
        except Exception as e:
            level = "✗" if required else "⚠ "
            print(f"  {level} r/{subreddit}: {e}")
        time.sleep(2)


# ---------------------------------------------------------------------------
# Bluesky helpers
# ---------------------------------------------------------------------------

BSKY_API = "https://bsky.social/xrpc"


def _bsky_login(handle, app_password):
    resp = requests.post(
        f"{BSKY_API}/com.atproto.server.createSession",
        json={"identifier": handle, "password": app_password},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["accessJwt"], data["did"]


def _bsky_post(access_jwt, did, text, link_url):
    text_bytes = text.encode("utf-8")
    url_bytes  = link_url.encode("utf-8")
    start = text_bytes.find(url_bytes)
    end   = start + len(url_bytes)

    record = {
        "$type":     "app.bsky.feed.post",
        "text":      text,
        "createdAt": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "langs":     ["en"],
    }

    if start >= 0:
        record["facets"] = [{
            "index":    {"byteStart": start, "byteEnd": end},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": link_url}],
        }]

    resp = requests.post(
        f"{BSKY_API}/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {access_jwt}"},
        json={"repo": did, "collection": "app.bsky.feed.post", "record": record},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def post_to_bluesky(newsletter, post_url):
    handle       = os.environ.get("BLUESKY_HANDLE", "")
    app_password = os.environ.get("BLUESKY_APP_PASSWORD", "")

    if not all([handle, app_password]):
        print("  ⚠  Bluesky credentials not set — skipping.")
        return

    subject = newsletter.get("subject", "Rugby coaching insights")
    week    = newsletter.get("week", "This Week")

    text = f"🏉 The Breakdown is out — {week}\n\n{subject}\n\nFree weekly rugby coaching newsletter: {post_url}"
    if len(text) > 300:
        max_subject = 300 - len(f"🏉 The Breakdown is out — {week}\n\n\n\nFree weekly rugby coaching newsletter: {post_url}")
        subject = subject[:max_subject - 3] + "..."
        text = f"🏉 The Breakdown is out — {week}\n\n{subject}\n\nFree weekly rugby coaching newsletter: {post_url}"

    try:
        access_jwt, did = _bsky_login(handle, app_password)
        _bsky_post(access_jwt, did, text, post_url)
        print(f"  ✓ Posted to Bluesky (@{handle})")
    except Exception as e:
        print(f"  ✗ Bluesky post failed: {e}")
