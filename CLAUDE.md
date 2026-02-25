# Claude Code Context

This repo contains Claude Code plugins for the SC (Solutions Consulting) team at Ada.

## Plugin Structure

```
plugins/sc/skills/        ← all skills live here
plugins/sc/.claude-plugin/plugin.json  ← plugin manifest (version lives here)
.claude-plugin/marketplace.json        ← marketplace registration
```

## Installing as a Teammate

```
/plugin marketplace add AdaSupport/build_ada_agent
```

Restart Claude Code after installing. Skills will be available as `/sc:<skill-name>`.

## Testing Local Changes

```bash
claude --plugin-dir ./plugins/sc
```

## Adding a New Skill

When the user asks to create a new skill or add a tool for the SC team:

1. Create a new directory: `plugins/sc/skills/<skill-name>/`
2. Add a `SKILL.md` file with this frontmatter:
   ```yaml
   ---
   name: skill-name
   description: One sentence — what it does and when to use it.
   allowed-tools:
     - Bash
     - mcp__notion*    # add any MCP tools the skill needs
   ---
   ```
3. Write the skill instructions in markdown below the frontmatter.
   - Be explicit about prerequisites (repos, env vars, credentials)
   - Include step-by-step logic the LLM should follow
   - Include example invocations
4. Bump the version in `plugins/sc/.claude-plugin/plugin.json` (increment minor, e.g. `1.0` → `1.1`)
5. Update the **Available Skills** table in `README.md`
6. Commit and push to both remotes:
   ```bash
   git add plugins/ README.md
   git commit -m "feat(skills): add <skill-name> skill"
   git push origin main && git push public main
   ```

Teammates already have the plugin installed will get the new skill automatically on next Claude Code reload (or run `/plugin update sc`).

## Skill Template

Copy from `plugins/sc/skills/_template/SKILL.md` as a starting point.

## Available Skills

| Skill | Invocation | Description |
|-------|-----------|-------------|
| build-ada-agent | `/sc:build-ada-agent` | Provision a full Ada AI agent demo from a company name + website |
