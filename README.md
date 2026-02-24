# Ada Demo Automation

Automated Ada AI agent provisioning for sales demos. Provisions a full Ada agent in ~10 minutes from just a company name.

## Usage

### Via Claude Code skill (recommended)

```
/pd:build-ada-agent Acme Corp https://www.acme.com
```

See [`skills/README.md`](skills/README.md) for installation instructions.

### Via CLI

```bash
python3 provision.py --company "Company Name" --auto --website "https://company.com" --actions 2
```

## CLI Flags

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

## What Gets Provisioned

1. Bot cloned from `scteam-demo.ada.support` template
2. API key auto-retrieved via Playwright
3. N Beeceptor mock API endpoints (`--actions N`, default 2)
4. N Ada actions imported and activated
5. 10 AI-generated knowledge articles
6. 70 customer questions + conversations seeded
7. Website knowledge source (optional — may time out, non-critical)

## Bot Handle Pattern

`{companyname}-ai-agent-demo` (e.g., `acmecorp-ai-agent-demo`)
Bot URL: `https://{handle}.ada.support`

## Project Structure

```
demo_automation/
├── provision.py          # Main provisioning script
├── skills/               # Claude Code skills
│   ├── README.md         # SC team onboarding guide
│   └── build-ada-agent/
│       └── SKILL.md      # pd:build-ada-agent skill
├── requirements.txt
└── .env                  # Auto-created on first skill run
```

## Notes

- `.env` credentials are auto-fetched from a shared Notion page on first run (via the skill)
- Bot cloning returns HTTP 500 if bot already exists — expected and safe to continue
- Beeceptor dashboard: https://app.beeceptor.com/console/ada-demo
