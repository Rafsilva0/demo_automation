# Claude Code Skills for Demo Automation

These skills let the SC team run the Ada demo provisioning directly from Claude Code — with automatic prospect research, a customisable plan, and a post-provision summary.

## Skills

| Skill | Description |
|-------|-------------|
| `sc:build-ada-agent` | Build a full Ada AI agent demo from a company name + website |

---

## Installation

Copy and paste the following prompt into Claude Code:

> Install the `sc:build-ada-agent` skill from `https://github.com/Rafsilva0/demo_automation`. Clone the repo to `~/Documents/GitHub/demo_automation` if it doesn't exist yet, install Python dependencies, copy `skills/build-ada-agent/SKILL.md` to `~/.claude/plugins/cache/sc-claude-tools/sc/5.5/skills/build-ada-agent/SKILL.md`, create `~/.claude/plugins/cache/sc-claude-tools/sc/5.5/.claude-plugin/plugin.json` with content `{"name":"sc","version":"5.5","description":"Claude Code tools for the SC team","repository":"https://github.com/Rafsilva0/demo_automation"}`, delete `~/.claude/plugins/cache/sc-claude-tools/sc/5.5/.orphaned_at` if it exists, and register `sc@sc-claude-tools` in `~/.claude/settings.json` under `enabledPlugins`. Then tell me to restart Claude Code.

That's it — Claude will handle everything. After restarting, type `/sc:build-ada-agent` to confirm it's loaded.

> **No `.env` setup needed.** On first run, the skill automatically fetches shared credentials from a private Notion page and writes the `.env` file for you.

> **Hit a blocker or error?** Reach out to Raf Silva on Slack.

---

## Usage

```
/sc:build-ada-agent Club Brugge https://www.clubbrugge.be
/sc:build-ada-agent Shopify https://www.shopify.com
/sc:build-ada-agent Air Canada
```

Claude will:
1. **Research** the prospect via Glean + your Granola meeting notes
2. **Present a plan** — proposed actions, KB focus, conversation topics
3. **Wait for your approval** (you can swap actions, change focus, etc.)
4. **Provision** the bot (~10 min)
5. **Give you the summary** — chat link, API key, Beeceptor dashboard, and suggested questions to ask

---

## Keeping the skill up to date

Paste this into Claude Code:

> Update the `sc:build-ada-agent` skill — pull the latest from `https://github.com/Rafsilva0/demo_automation` and re-copy `skills/build-ada-agent/SKILL.md` to `~/.claude/plugins/cache/sc-claude-tools/sc/5.5/skills/build-ada-agent/SKILL.md`. Then tell me to restart Claude Code.
