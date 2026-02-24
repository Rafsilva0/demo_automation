# Claude Code Skills for Demo Automation

The `build-ada-agent` skill lets the SC team provision Ada demo bots directly from Claude Code — with automatic prospect research, a customisable plan, and a post-provision summary.

## Skill

| Skill | Description |
|-------|-------------|
| `pd:build-ada-agent` | Build a full Ada AI agent demo from a company name + website |

The skill lives in the `pd-claude-tools` plugin (same as all other `pd:` skills).

---

## Installation

### Option A — You have access to the `demo_automation` repo

Paste this into Claude Code:

> Copy `skills/build-ada-agent/SKILL.md` from `~/Documents/GitHub/demo_automation` to `~/.claude/plugins/cache/pd-claude-tools/pd/5.5/skills/build-ada-agent/SKILL.md`, creating the directory if needed. Then tell me to restart Claude Code.

### Option B — No GitHub access (share the install script)

Ask Raf to send you `skills/install.sh` from this repo, then run:

```bash
bash install.sh
```

No GitHub access needed — the script embeds the full skill inline and installs it directly.

After either option, restart Claude Code and type `/pd:build-ada-agent` to confirm it's loaded.

> **No `.env` setup needed.** On first run, the skill automatically fetches shared credentials from a private Notion page and writes the `.env` file for you.

> **Hit a blocker or error?** Reach out to Raf Silva on Slack.

---

## Keeping the skill up to date

Paste this into Claude Code:

> Re-copy `skills/build-ada-agent/SKILL.md` from `~/Documents/GitHub/demo_automation` to `~/.claude/plugins/cache/pd-claude-tools/pd/5.5/skills/build-ada-agent/SKILL.md`. Then tell me to restart Claude Code.

---

## Usage

```
/pd:build-ada-agent Club Brugge https://www.clubbrugge.be
/pd:build-ada-agent Shopify https://www.shopify.com
/pd:build-ada-agent Air Canada
```

Claude will:
1. **Research** the prospect via Glean + your Granola meeting notes
2. **Present a plan** — proposed actions, KB focus, conversation topics
3. **Wait for your approval** (you can swap actions, change focus, etc.)
4. **Provision** the bot (~10 min)
5. **Give you the summary** — chat link, API key, Beeceptor dashboard, and suggested questions to ask
