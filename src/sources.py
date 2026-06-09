"""
sources.py — Fetches rugby coaching content from RSS feeds and Reddit.
"""

import re
import time
import feedparser
import requests
from datetime import datetime, timedelta, timezone


RSS_FEEDS = [
    {"url": "https://feeds.bbci.co.uk/sport/rugby-union/rss.xml",        "name": "BBC Rugby"},
    {"url": "https://www.planetrugby.com/feed/",                          "name": "Planet Rugby"},
    {"url": "https://www.rugbypass.com/feed/",                            "name": "RugbyPass"},
    {"url": "https://www.theguardian.com/sport/rugby-union/rss",          "name": "The Guardian"},
    {"url": "https://therugbysite.com/blog/feed/",                        "name": "The Rugby Site"},
    {"url": "https://www.rugbyworld.com/feed/",                           "name": "Rugby World"},
    {"url": "https://www.espn.com/espn/rss/rugby/news",                   "name": "ESPN Rugby"},
]

# Keywords to keep from r/rugbyunion (it's a general fan sub, so we filter tightly)
COACHING_KEYWORDS = [
    "coach", "drill", "tactic", "training", "technique", "skill",
    "improve", "develop", "youth", "backline", "lineout", "scrum",
    "defence", "defense", "set piece", "attack", "ruck", "breakdown",
    "contact", "analysis", "structure", "player development", "session plan",
]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _parse_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def fetch_rss_items(days_back: int = 7) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    items = []

    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries:
                published = _parse_date(entry)
                if published and published < cutoff:
                    continue  # Too old

                summary = _strip_html(
                    entry.get("summary") or entry.get("description") or ""
                )[:400]

                items.append({
                    "title":     entry.get("title", "").strip(),
                    "url":       entry.get("link", ""),
                    "summary":   summary,
                    "source":    feed_info["name"],
                    "published": published.isoformat() if published else "",
                    "type":      "news",
                })
        except Exception as exc:
            print(f"  ⚠ RSS error ({feed_info['name']}): {exc}")

    return items


def fetch_reddit_items(days_back: int = 7) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    headers = {"User-Agent": "TheBreakdownNewsletter/1.0 (rugby coaching digest)"}
    items = []

    subreddits = {
        "rugbycoaches": False,   # False = don't keyword-filter (it's already coaching-specific)
        "rugbyunion":   True,    # True  = apply keyword filter
    }

    for subreddit, apply_filter in subreddits.items():
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=30"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()

            for post in resp.json()["data"]["children"]:
                d = post["data"]
                if d.get("stickied"):
                    continue

                created = datetime.fromtimestamp(d["created_utc"], tz=timezone.utc)
                if created < cutoff:
                    continue

                if apply_filter:
                    text = (d.get("title", "") + " " + d.get("selftext", "")).lower()
                    if not any(kw in text for kw in COACHING_KEYWORDS):
                        continue

                items.append({
                    "title":     d.get("title", "").strip(),
                    "url":       f"https://reddit.com{d.get('permalink', '')}",
                    "summary":   _strip_html(d.get("selftext", ""))[:400] or d.get("title", ""),
                    "source":    f"r/{subreddit}",
                    "published": created.isoformat(),
                    "score":     d.get("score", 0),
                    "type":      "discussion",
                })

            time.sleep(1.5)  # Polite pause between Reddit calls
        except Exception as exc:
            print(f"  ⚠ Reddit error (r/{subreddit}): {exc}")

    return items


def fetch_rugby_content(days_back: int = 7) -> list[dict]:
    print("  Fetching RSS feeds...")
    rss = fetch_rss_items(days_back)

    print("  Fetching Reddit...")
    reddit = fetch_reddit_items(days_back)

    all_items = rss + reddit
    print(f"  Got {len(rss)} RSS items + {len(reddit)} Reddit posts = {len(all_items)} total")
    return all_items
