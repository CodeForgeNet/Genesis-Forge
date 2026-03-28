# Contributing to Genesis Forge

Thank you for contributing! This guide explains how to add agents, skills, workflows, and bug fixes.

---

## Code of Conduct

Be excellent to each other. See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) if it exists.

---

## Development Setup

```bash
git clone https://github.com/[user]/genesis-forge
cd genesis-forge
node bin/setup.js --help
```

Requirements:
- Node.js >= 18
- Python 3 >= 3.8

---

## Adding a Skill

Skills live in `agent/skills/<skill-name>/SKILL.md`.

Use the template at `agent/skills/_SKILL_TEMPLATE/SKILL.md`:

```bash
cp -r agent/skills/_SKILL_TEMPLATE agent/skills/your-skill-name
# Edit agent/skills/your-skill-name/SKILL.md
```

### Skill File Format

```markdown
---
name: your-skill-name
description: Use when [condition] — [what it does]
domain: frontend|backend|database|testing|security|devops|mobile|general
---

## TL;DR
One paragraph summary for low-context models.

## When to Use
...

## Steps
...
```

### Requirements for Skills

- [ ] Must have YAML frontmatter with `name`, `description`, `domain`
- [ ] Must have a TL;DR section (first ~500 chars should be standalone)
- [ ] Must be in English (or have English TL;DR + translation note)
- [ ] License: by submitting, you agree to release under MIT
- [ ] Must not contain proprietary code or API keys

After adding, rebuild the registry:
```bash
python3 agent/scripts/build_skill_registry.py
```

---

## Adding an Agent

Agents live in `agent/agents/<agent-name>.md`.

```markdown
---
name: my-new-agent
description: Short description of the agent's domain
skills:
  - skill-one
  - skill-two
---

# My New Agent

## Domain
What this agent owns. Be specific about what file types / responsibilities it owns.

## When to Use
Versus other similar agents (e.g., vs. code-reviewer vs. code-quality-reviewer).

## Behavior
How the agent should behave, what it outputs.
```

---

## Adding a Workflow

Workflows live in `agent/workflows/<name>.md` and use the frontmatter format:

```markdown
---
description: Short description of when to use this workflow
---

# /workflow-name — $ARGUMENTS

## Steps
...
```

After adding, verify it shows up:
```bash
genesis-forge list-workflows
```

---

## Pull Request Process

1. Fork the repo and create a feature branch
2. Make your changes
3. Test locally: `node bin/setup.js route "test task"` (Note: route is actually a part of the MCP, not bin/setup.js, check implementation)
4. Run `python3 agent/scripts/build_skill_registry.py` if you changed skills
5. Open a PR with a clear description of what you added/changed
6. PRs for new skills must include: skill purpose, domain, and license confirmation

---

## Versioning

We use [Semantic Versioning](https://semver.org):

| Change | Bump |
|--------|------|
| Breaking changes to agent/skill API | MAJOR |
| New agents, skills, workflows | MINOR |
| Bug fixes, doc updates | PATCH |

---

## File Ownership

When you touch a file, the kit's session memory tracks it:
```bash
genesis-forge memory read | grep file_ownership
```

This helps the router know which agent last touched which file.

---

## Questions?

Open an [issue](https://github.com/[user]/genesis-forge/issues) and tag it `question`.
