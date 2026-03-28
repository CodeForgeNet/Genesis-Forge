# Attribution

This file documents the sources and licenses for skills, agents, and other content bundled with Genesis Forge.

---

## Core Kit (MIT)

All agents, workflows, scripts, and documentation authored by the Genesis Forge team are released under MIT.
See [LICENSE](./LICENSE).

---

## Skills Attribution

The `agent/skills/` directory contains **734 skill modules** from multiple sources:

| Source | Count | License |
|--------|-------|---------|
| Community (GitHub PRs) | 557 | MIT (per CONTRIBUTING.md) |
| Personal (team authored) | 31 | MIT |
| Self (core kit) | 15 | MIT |
| Vibeship Spawner Skills | 54 | Apache 2.0 / MIT |
| External GitHub repos | ~77 | Various (see individual skills) |

### Source Breakdown

**Community Skills (766)** — Contributed via GitHub PRs. Contributors agree to MIT license upon submission.

**Vibeship Spawner Skills (54)** — Sourced from `vibeship-spawner-skills`. License: Apache 2.0 / MIT (inherited).

**Personal Skills (34)** — Authored by team members for internal tooling. MIT licensed.

**Core/Self Skills (15)** — Essential skills directly maintained by Genesis Forge team.

**External Sources** — Individual skills from various GitHub repos. Each skill's frontmatter documents its source and license.

### Categorization by Domain

| Domain | Count | Description |
|--------|-------|-------------|
| frontend | 216 | React, Vue, Angular, CSS, UI/UX |
| testing | 88 | Jest, Playwright, unit/E2E |
| ai_ml | 85 | AI agents, machine learning |
| automation | 68 | Workflow automation |
| general | 48 | Multi-purpose, architecture |
| typescript | 46 | TypeScript patterns |
| azure | 46 | Microsoft Azure services |
| backend | 46 | Node.js, APIs, Express |
| security | 21 | OWASP, penetration testing |
| database | 17 | SQL, Prisma, migrations |
| Other (aws, seo, devops, game, mobile, etc.) | ~21 | Specialized domains |

---


## Special Categories

### Deprecated Skills
Currently none. Deprecated skills would be moved to `agent/skills/deprecated/`.

### Experimental Skills
Currently none tagged as experimental. If added, they should include `experimental: true` in frontmatter.

---

## Adding Attribution

If you add a skill from an external source, add a `source` field to its YAML frontmatter:

```yaml
---
name: your-skill
description: Use when [condition] — [what it does]
domain: frontend
source: "https://github.com/example/original-repo"
license: "MIT"
---
```

---

## Reporting Issues

If you find a skill that appears to have an incompatible license or missing attribution, please open an issue at:
https://github.com/CodeForgeNet/Genesis-Forge/issues
