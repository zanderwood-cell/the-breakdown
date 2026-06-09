# The Breakdown — Setup Guide

Five steps. Takes about 20 minutes. After that, the agent runs itself every Tuesday.

---

## Step 1 — Create your Substack

1. Go to [substack.com](https://substack.com) and click **Start writing**
2. Sign up with your email
3. When asked for your publication name, use: **The Breakdown**
4. For the URL slug, use something like `thebreakdownrugby` → your newsletter will live at `thebreakdownrugby.substack.com`
5. Pick the free plan — you can add paid subscriptions later
6. **Note down your slug** (the part before `.substack.com`) — you'll need it in Step 4

Substack is free to use. They take a small cut only when you add paid subscriptions.

---

## Step 2 — Get a Claude API key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Click **API Keys** in the left sidebar → **Create Key**
4. Copy the key (starts with `sk-ant-...`) — you won't see it again
5. Add $5–10 of credit. Each newsletter issue costs roughly **$0.03–0.06** to generate (Claude Haiku pricing), so $5 covers ~100+ issues

---

## Step 3 — Fork the repo on GitHub

1. Go to [github.com](https://github.com) and create a free account if you don't have one
2. Create a **new repository** called `the-breakdown`
3. Upload all the files from this folder into that repo (drag and drop works in the GitHub UI)
   - Make sure the folder structure is preserved: `src/`, `.github/workflows/`, etc.

---

## Step 4 — Add your secrets to GitHub

Your credentials need to be stored as GitHub Secrets (encrypted — never visible in logs).

1. In your GitHub repo, go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret** for each of these:

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your key from Step 2 |
| `SUBSTACK_EMAIL` | The email you signed up to Substack with |
| `SUBSTACK_PASSWORD` | Your Substack password |
| `SUBSTACK_SUBDOMAIN` | Your slug from Step 1 (e.g. `thebreakdownrugby`) |

---

## Step 5 — Test it with a dry run

Before the first real issue goes out, test that everything works:

1. In your GitHub repo, go to **Actions** → **Publish Weekly Newsletter**
2. Click **Run workflow**
3. In the dropdown, set **Dry run** to `true`
4. Click **Run workflow**

After ~60 seconds, click into the run and check the logs. You should see the full newsletter printed out. If there are errors, the logs will tell you exactly what's wrong.

When you're happy, run it again with **Dry run = false** to publish your first issue.

---

## How it runs automatically

The agent runs every **Tuesday at 7:00 AM UTC** (8am UK time). It:

1. Fetches rugby content from 7 sources (BBC, Planet Rugby, RugbyPass, The Guardian, The Rugby Site, Rugby World, ESPN) plus Reddit coaching communities
2. Passes everything to Claude, which writes the full newsletter
3. Publishes directly to your Substack

You don't need to do anything. Check in once a week to see how it went.

---

## Growing the newsletter

- **Tell your club.** Start with 10 people who know you — coaches you've worked with, your own club, the local schools you've coached at. Personal asks convert much better than social posts.
- **Post on r/rugbycoaches.** Share each issue with a one-line summary of what's inside. The community is small but genuinely interested.
- **Add a paid tier when you hit ~200 subscribers.** Substack lets you set a paid tier in Settings → Subscriptions. Even £5/month from 5% of 200 readers = £50/month with zero extra work.
- **Sponsorships.** Once you're at 500+ subscribers, reach out to rugby equipment suppliers, GPS tracker companies (Catapult, STATSports), or coaching course providers. A modest "supported by" mention is worth £50–200 per issue to the right sponsor.

---

## Costs summary

| Item | Cost |
|---|---|
| Substack | Free (they take 10% of paid subscriptions) |
| Claude API | ~£0.04 per issue (roughly £2/year) |
| GitHub Actions | Free (within free tier limits) |
| **Total to run** | **~£2/year** |

---

## Troubleshooting

**"Substack login failed"** — Double-check your email and password secrets. Make sure there's no trailing space when you pasted them.

**"No content fetched"** — Some RSS feeds go down occasionally. The agent will still work with partial data. Check the logs to see which source failed.

**"Claude API error"** — Check your API credit balance at console.anthropic.com. Top up if needed.

**The agent ran but no email arrived** — Check your Substack dashboard. The post may have published but email delivery may need to be confirmed for first-time setup.
