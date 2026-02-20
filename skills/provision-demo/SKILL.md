---
name: provision-demo
description: Provision a full Ada AI agent demo from a company name and website. Researches the prospect via Glean and Granola, presents a customisable plan for the SC to approve, then provisions the bot and delivers a ready-to-use summary with chat link, API key, Beeceptor endpoints, and suggested questions.
require-tools:
  - Bash
  - mcp__22fd8384*
  - mcp__b64aba26*
  - mcp__729d2fa9*
---

# Provision Demo

Provision a fully-configured Ada AI agent demo for a prospect in ~10 minutes — from just a company name and website.

## Requirements

This skill requires:
- The **demo_automation** repo at `~/Documents/GitHub/demo_automation`
- Python 3 + dependencies installed (`pip install -r requirements.txt`)
- A valid `.env` file with `ADA_BOT_PASSWORD`, `ADA_CLONE_SECRET`, `ANTHROPIC_API_KEY`, `BEECEPTOR_AUTH_TOKEN`

The bootstrap step (Step 0) handles setup automatically on first run — no manual `.env` required.

## Parameters

- **Company name** (required): The prospect's company name (e.g. "Club Brugge", "Shopify", "Air Canada")
- **Website** (optional but recommended): The company's main website URL (e.g. "https://www.clubbrugge.be"). Used for live website knowledge scraping. Defaults to auto-discovery if omitted.

## Workflow

### Step 0 — Bootstrap (first run only)

Before doing anything else, check that the repo and credentials exist on this machine.

**Check repo:**

```bash
ls ~/Documents/GitHub/demo_automation/provision.py
```

If the file is missing, tell the user:
```
The demo_automation repo isn't set up on this machine yet. Run:
  git clone git@github.com:Rafsilva0/demo_automation.git ~/Documents/GitHub/demo_automation
  cd ~/Documents/GitHub/demo_automation && pip install -r requirements.txt
Then re-run this skill.
```
Stop here until resolved.

**Check credentials:**

```bash
ls ~/Documents/GitHub/demo_automation/.env
```

- **If the file exists:** skip silently and proceed to Step 1.
- **If the file is missing:**
  1. Fetch the shared credentials page from Notion using `mcp__729d2fa9-4409-4a97-838a-8eb8d2b766cf__notion-fetch` with ID `30d6162e53cd80a48ac0d1a50676a46e`
  2. Parse the `KEY=VALUE` lines from the code block in the page content
  3. Write them to `~/Documents/GitHub/demo_automation/.env` using Bash (one `KEY=VALUE` per line, no quotes)
  4. Tell the user: `✅ Credentials loaded from Notion — .env created. You're all set for future runs.`

---

### Step 1 — Research the Prospect

Spawn two parallel Task agents to gather intel on the prospect BEFORE building anything.

#### Agent 1 — Glean Search
Use `mcp__22fd8384-0cee-4806-b8a0-4ffa1ace36e6__search` and `mcp__22fd8384-0cee-4806-b8a0-4ffa1ace36e6__chat` to find:
- What industry/vertical is this company in?
- What products or services do they sell?
- Any known pain points, support challenges, or customer-facing workflows?
- Recent news or initiatives relevant to customer support / AI?

Search queries to try:
- `"{company name}" customer support`
- `"{company name}" products services`
- `"{company name}" AI automation`

#### Agent 2 — Granola Meeting Notes
Use `mcp__b64aba26-624b-471d-a4c9-bc9c8ca47541__query_granola_meetings` to find:
- Any discovery calls, demo prep notes, or sales meetings mentioning the company
- Key contacts, pain points, or specific use cases the SC has discussed with them
- Any commitments made (e.g. "they want to see order tracking")

Query: `"{company name}" demo OR discovery OR prospect OR meeting`

After both agents complete, synthesise findings into a **prospect brief** (3-5 bullet points):
- Industry & business model
- Likely top 2-3 customer support use cases
- Any specific features or workflows the SC should highlight
- Key contacts or context from past meetings

---

### Step 2 — Generate the Plan

Based on the prospect brief, generate a **demo plan** and present it to the SC for approval BEFORE provisioning.

Format the plan as follows:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖  DEMO PLAN — {COMPANY NAME}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 PROSPECT BRIEF
  • [Industry & business model in 1 line]
  • [Top use case 1 — e.g. "Fans frequently ask about ticket availability and match schedules"]
  • [Top use case 2 — e.g. "Order/subscription tracking is a high-volume support topic"]
  • [Any notes from past meetings, if found]

🛠️  WHAT WILL BE BUILT

  Bot handle:   {company-slug}-ai-agent-demo.ada.support
  Template:     scteam-demo.ada.support (Ada SC demo template)

  ACTIONS (2 mock API endpoints via Beeceptor):
    1. {Suggested Action 1 Name}
       → {What it does in 1 sentence}
       → Example question: "{Example customer question}"
    2. {Suggested Action 2 Name}
       → {What it does in 1 sentence}
       → Example question: "{Example customer question}"

  KNOWLEDGE BASE (10 AI-generated articles):
    Focus areas: {3-4 topic areas based on research, e.g. "Ticketing & memberships, Match day FAQs, Loyalty programme, Store & merchandise"}

  CONVERSATIONS (70 seeded Q&A pairs):
    Topics: {Based on the KB focus areas above}

  WEBSITE SCRAPE: {website URL} (live content → KB)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✏️  WANT TO CUSTOMISE?

  You can ask me to change:
    • "Swap action 1 for a returns/refund tracker"
    • "Add a loyalty points balance lookup"
    • "Focus the KB on enterprise B2B features"
    • "Use website https://... instead"

  Or just say "looks good" to start provisioning.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Wait for the SC's response before proceeding.**

If the SC requests changes, update the plan and present it again. Repeat until they confirm.

---

### Step 3 — Provision the Agent

Once the SC approves (says "looks good", "go", "yes", "provision it", etc.):

**First, tell the SC what's about to happen:**
```
🚀 Kicking off provisioning for {Company Name}...
This takes about 10 minutes. I'll give you a live progress update at each stage.

  Phase 1 — Bot handle generation
  Phase 2 — Clone bot from Ada SC demo template
  Phase 3 — Beeceptor mock API endpoints
  Phase 4 — Playwright: API key retrieval + website scrape + action import
  Phase 5 — Knowledge base: 10 AI-generated articles
  Phase 6 — 70 customer questions generated
  Phase 7 — 70 conversations seeded
```

**Then run the provisioner:**

```bash
cd ~/Documents/GitHub/demo_automation && \
python3 provision.py --company "{COMPANY NAME}" --auto --website "{WEBSITE URL}" --actions {NUM_ACTIONS}
```

- If no website was provided: omit `--website` flag
- `--actions` defaults to 2; set to the number of actions in the approved plan
- The script will take **8–12 minutes**

**Stream progress milestones** as they appear in the output. After each one, post a brief update to the SC:

| Log pattern | Message to post |
|---|---|
| `✅ Bot handle:` | `✅ Phase 1 done — Bot handle: {handle}` |
| `Bot may already exist` or `✅ Bot cloned` | `✅ Phase 2 done — Bot cloned from template` (HTTP 500 = already exists, safe) |
| `✅ Created N Beeceptor endpoints` | `✅ Phase 3 done — {N} mock API endpoints live on Beeceptor` |
| `✅ API key retrieved` | `✅ Phase 4a done — API key retrieved automatically` |
| `Website source addition failed` | `⚠️ Phase 4b — Website scrape timed out (non-critical, KB articles still loading)` |
| `✅ Imported N actions` | `✅ Phase 4c done — {N} actions imported and activated` |
| `✅ Uploaded 10 articles` | `✅ Phase 5 done — 10 knowledge articles live` |
| `✅ Generated 70 questions` | `✅ Phase 6 done — 70 customer questions generated` |
| `✓ 70/70 conversations created` | `✅ Phase 7 done — 70 conversations seeded` |
| `🎉 PROVISIONING COMPLETE` | Present the full post-provision summary (Step 4) |

If the script exits with an error:
- HTTP 500 on clone = bot already exists, safe to continue
- Timeout on website scrape = non-critical, KB articles still loaded
- Missing env var = check `.env` file in the repo root

---

### Step 4 — Post-Provision Summary

After successful provisioning, parse the script output to extract:
- The bot handle (pattern: `{slug}-ai-agent-demo`)
- The API key (look for `API Key:` in output)
- The Beeceptor namespace (look for `beeceptor.com/console/` in output)
- The actual KB article titles generated
- The actual action names created

Then present the full **post-provision summary**:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  {COMPANY NAME} DEMO — READY TO USE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 CHAT LINK
   https://{bot-handle}.ada.support/chat

🔑 API KEY
   {api-key}
   (Use this for programmatic access or API demos)

🛠️  BEECEPTOR MOCK APIs
   Dashboard: https://app.beeceptor.com/console/ada-demo
   Endpoints are live and will auto-respond to action calls

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 SUGGESTED QUESTIONS TO ASK THE BOT

  Based on what was actually built:

  → Knowledge Base questions:
    [Generate 4-5 questions directly from the KB article titles that were created.
     Format: "Do you have [topic]?" or "Can you tell me about [article topic]?"
     Keep them natural, like a real customer would ask.]

  → Action-triggering questions:
    [Generate 2-3 questions that will trigger each of the 2 actions.
     Use the action name and inputs as a guide.
     Format: "Can I check [action topic]?" or "I want to [action verb]..."]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 WHAT WAS BUILT

  ✅ Bot cloned from Ada SC demo template
  ✅ API key auto-retrieved (no 28-day wait!)
  ✅ 10 knowledge articles: {list article titles}
  ✅ 2 actions: {action 1 name}, {action 2 name}
  ✅ 2 Beeceptor endpoints configured
  ✅ 70 conversations seeded
  ✅ Website scrape: {website URL}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Important:** The suggested questions MUST be generated dynamically from the actual article titles and action names in the provisioning output — not from generic templates. Read the logs to find what was actually created.

---

## Example Usage

- `/pd:provision-demo Club Brugge https://www.clubbrugge.be`
- `/pd:provision-demo Shopify https://www.shopify.com`
- `/pd:provision-demo Air Canada` (no website — will skip live scrape)
- `/pd:provision-demo Contabo GmbH https://contabo.com` → SC adds a 3rd action → script runs with `--actions 3`

---

## Notes

- **Bot already exists (HTTP 500):** Expected if you re-provision the same company. The script continues safely — remaining steps still run.
- **Website scrape timeout:** Non-critical. KB articles are uploaded regardless. The website scrape is best-effort.
- **API key retrieval:** Uses Playwright browser automation. If it fails, the SC can manually retrieve the key from the Ada dashboard.
- **Bot URL pattern:** `{company-slug}-ai-agent-demo.ada.support` — slug is lowercase, alphanumeric only, hyphens for spaces.
- **Credentials:** Stored in `~/Documents/GitHub/demo_automation/.env`. Auto-fetched from Notion on first run (Step 0).
- **Notion credentials page:** ID `30d6162e53cd80a48ac0d1a50676a46e` — shared with the SC team (comment access).
