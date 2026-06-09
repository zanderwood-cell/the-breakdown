"""
generator.py — Uses Claude to turn raw content into a polished newsletter.
"""

import re
import anthropic
from datetime import datetime


SYSTEM_PROMPT = """You are the editor of "The Breakdown" — a weekly email newsletter for rugby coaches at club and school level.

Your readers are passionate, time-poor coaches (15s and 7s, amateur to semi-pro, youth to senior). They want actionable insights they can use at their next training session. They trust you to filter the noise.

NEWSLETTER FORMAT — follow this exactly every week:

---
**Subject line:** The Breakdown | [one compelling hook from this week's content]

Hey coaches,

[INTRO — 2-3 sentences max, warm, conversational. Sets up why this week's content matters.]

---

**🏉 TOP STORY**

[150 words. The most significant development for coaches this week. Be specific. If there's no obvious coaching story, find the coaching angle in a match result, player performance, or rugby science story. Always tie back to what a club coach can learn or do differently.]

---

**📋 DRILL OF THE WEEK**

[Name the drill. 2-sentence description of what it develops and why it works.]

• **Setup:** [Space, cones, equipment]
• **Players:** [Numbers and positions involved]
• **Coaching points:** [3 specific, actionable points]
• **Progression:** [How to increase intensity or complexity]

[Source this from the week's content if there's a relevant drill or training story. If not, create a genuinely useful drill relevant to the season or a theme from the news.]

---

**🧠 TACTICAL BREAKDOWN**

[150 words. One tactical concept from recent matches or discussions. Be specific — reference actual teams, matches, or situations if available in the content. What's the pattern? Why does it work? What can coaches implement at club level?]

---

**🔬 FROM THE RESEARCH**

[100 words. One evidence-based coaching insight — sports science, player development, psychology, load management, or skill acquisition. Keep it practical: what does this actually change about how you coach?]

---

**🔗 QUICK READS**

→ [Title](URL) — [One sentence: why a coach should read this]
→ [Title](URL) — [One sentence: why a coach should read this]
→ [Title](URL) — [One sentence: why a coach should read this]

[Use real URLs from the content provided. Only include links that are genuinely worth a coach's time.]

---

Train hard, coach smart.

The Breakdown
---

TONE: Knowledgeable but unpretentious. Like the best coach at your club — the one who actually reads the research and isn't impressed by jargon. Direct. No filler. No "This week we have some exciting content for you..."
"""


def _markdown_to_html(text: str) -> str:
    """Convert the newsletter markdown to clean HTML suitable for Substack."""
    lines = text.split("\n")
    html = []
    in_ul = False

    for line in lines:
        stripped = line.strip()

        # Section headings: **🏉 TOP STORY** etc.
        if re.match(r"^\*\*[^*]+\*\*$", stripped) and not stripped.startswith("•"):
            if in_ul:
                html.append("</ul>")
                in_ul = False
            heading = stripped.replace("**", "")
            html.append(f'<h3 style="margin-top:2em">{heading}</h3>')

        # Bullet/arrow list items
        elif stripped.startswith(("•", "→", "- ")):
            if not in_ul:
                html.append("<ul>")
                in_ul = True
            item = re.sub(r"^[•→\-]\s*", "", stripped)
            item = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", item)
            item = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', item)
            html.append(f"<li>{item}</li>")

        # Horizontal rule
        elif stripped == "---":
            if in_ul:
                html.append("</ul>")
                in_ul = False
            html.append("<hr>")

        # Empty line
        elif not stripped:
            if in_ul:
                html.append("</ul>")
                in_ul = False
            html.append("")

        # Regular paragraph
        else:
            if in_ul:
                html.append("</ul>")
                in_ul = False
            para = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", stripped)
            para = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", para)
            para = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', para)
            html.append(f"<p>{para}</p>")

    if in_ul:
        html.append("</ul>")

    return "\n".join(html)


def generate_newsletter(items: list[dict]) -> dict:
    client = anthropic.Anthropic()

    week_date = datetime.now().strftime("%B %d, %Y")

    # Build the content block for the prompt — cap at 35 items to stay within context
    content_block = "\n\n".join(
        f"SOURCE: {item['source']}\n"
        f"TITLE: {item['title']}\n"
        f"URL: {item['url']}\n"
        f"SUMMARY: {item['summary']}"
        for item in items[:35]
    )

    user_message = (
        f"Here is this week's content (week of {week_date}):\n\n"
        f"{content_block}\n\n"
        "Write the full newsletter. Use real URLs from the content above for Quick Reads. "
        "Return ONLY the newsletter — no meta-commentary, no preamble."
    )

    print("  Calling Claude API...")
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text.strip()

    # Pull out subject line
    subject = f"The Breakdown | Week of {week_date}"
    body_text = raw_text

    for line in raw_text.split("\n"):
        if "**Subject line:**" in line or "Subject line:" in line:
            subject = re.sub(r"\*?\*?Subject line:\*?\*?", "", line).strip()
            body_text = raw_text[raw_text.index(line) + len(line):].strip()
            break

    html_body = _markdown_to_html(body_text)

    return {
        "subject":   subject,
        "body_text": body_text,
        "body_html": html_body,
        "week":      week_date,
    }
