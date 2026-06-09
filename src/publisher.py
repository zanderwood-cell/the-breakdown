"""
publisher.py — Authenticates with Substack and publishes the newsletter.

Uses Substack's unofficial internal API (same calls the web dashboard makes).
Credentials are read from environment variables — never hardcode them.

Required env vars:
  SUBSTACK_EMAIL       — your Substack login email
  SUBSTACK_PASSWORD    — your Substack login password
  SUBSTACK_SUBDOMAIN   — your publication slug (e.g. "thebreakdown" for thebreakdown.substack.com)
"""

import os
import json
import requests


def _get_session(email: str, password: str, subdomain: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent":   "Mozilla/5.0 (compatible; TheBreakdownAgent/1.0)",
        "Content-Type": "application/json",
        "Referer":      f"https://{subdomain}.substack.com",
    })

    resp = session.post(
        "https://substack.com/api/v1/login",
        json={
            "email":            email,
            "password":         password,
            "for_pub":          subdomain,
            "captcha_response": None,
        },
        timeout=15,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Substack login failed ({resp.status_code}): {resp.text[:300]}"
        )

    print("  Authenticated with Substack.")
    return session


def publish_to_substack(newsletter: dict, draft: bool = False) -> str:
    """
    Create and optionally publish a post on Substack.

    Args:
        newsletter: dict with keys subject, body_html, week
        draft:      if True, save as draft instead of publishing immediately

    Returns:
        URL of the published/draft post
    """
    email      = os.environ["SUBSTACK_EMAIL"]
    password   = os.environ["SUBSTACK_PASSWORD"]
    subdomain  = os.environ["SUBSTACK_SUBDOMAIN"]
    base_url   = f"https://{subdomain}.substack.com"

    session = _get_session(email, password, subdomain)

    post_payload = {
        "draft_title":      newsletter["subject"],
        "draft_subtitle":   f"Week of {newsletter['week']}",
        "draft_body":       newsletter["body_html"],
        "draft_section_id": None,
        "section_chosen":   True,
        "audience":         "everyone",
        "type":             "newsletter",
        "draft":            draft,
    }

    resp = session.post(
        f"{base_url}/api/v1/posts",
        json=post_payload,
        timeout=20,
    )

    if resp.status_code not in (200, 201):
        # Save content locally as fallback so we don't lose the issue
        _save_fallback(newsletter)
        raise RuntimeError(
            f"Substack post creation failed ({resp.status_code}): {resp.text[:500]}"
        )

    data  = resp.json()
    slug  = data.get("slug", "")
    url   = f"{base_url}/p/{slug}"
    state = "draft saved" if draft else "published"
    print(f"  Post {state}: {url}")
    return url


def _save_fallback(newsletter: dict) -> None:
    """Save newsletter content to a local file if publishing fails."""
    from datetime import datetime
    filename = f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, "w") as f:
        f.write(f"<h1>{newsletter['subject']}</h1>\n")
        f.write(newsletter["body_html"])
    print(f"  Fallback saved to: {filename}")
