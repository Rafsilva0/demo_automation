# Ada SC Tools

Claude Code plugin for the SC (Solutions Consulting) team at Ada. Provisions full Ada AI agent demos in ~10 minutes from a company name and website.

## Install

```
/plugin marketplace add AdaSupport/build_ada_agent
```

Restart Claude Code. Skills are available as `/sc:<skill-name>`.

## Available Skills

| Skill | Invocation | Description |
|-------|-----------|-------------|
| build-ada-agent | `/sc:build-ada-agent` | Provision a full Ada AI agent demo from a company name + website |

## Usage

```
/sc:build-ada-agent Acme Corp https://www.acme.com
```

## What Gets Provisioned

1. Bot cloned from `scteam-demo.ada.support` template
2. API key auto-retrieved via Playwright
3. Beeceptor mock API endpoints + Ada actions
4. AI-generated knowledge articles
5. Customer questions + conversations seeded
6. Website knowledge source

## CLI (advanced)

```bash
git clone https://github.com/AdaSupport/build_ada_agent ~/Documents/GitHub/build_ada_agent
cd ~/Documents/GitHub/build_ada_agent && pip install -r requirements.txt
python3 provision.py --company "Company Name" --auto --website "https://company.com" --actions 2
```

### CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--company` | required | Company name |
| `--auto` | — | Auto-retrieve API key via Playwright |
| `--website` | — | Website URL to scrape for knowledge source |
| `--articles` | 10 | Number of KB articles to generate |
| `--questions` | 70 | Number of customer questions |
| `--conversations` | same as questions | Number of seeded conversations |
| `--actions` | 2 | Number of Beeceptor mock API actions to create |
| `--dry-run` | — | Validate without making changes |

## Bot Handle Pattern

`{companyname}-ai-agent-demo` (e.g., `acmecorp-ai-agent-demo`)
Bot URL: `https://{handle}.ada.support`

## Project Structure

```
build_ada_agent/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace registration
├── plugins/sc/
│   ├── .claude-plugin/
│   │   └── plugin.json           # Plugin manifest + version
│   └── skills/
│       ├── _template/            # Copy this when adding a new skill
│       │   └── SKILL.md
│       └── build-ada-agent/
│           └── SKILL.md
├── provision.py                  # Main provisioning script
├── requirements.txt
└── CLAUDE.md                     # LLM instructions for contributors
```

## Adding a New Skill

See `CLAUDE.md` for step-by-step instructions (written for LLM agents).

## Notes

- Credentials are auto-fetched from a shared Notion page on first skill run
- Bot cloning returns HTTP 500 if bot already exists — expected, safe to continue
- Beeceptor dashboard: https://app.beeceptor.com/console/ada-demo
