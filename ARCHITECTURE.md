# Genesis Forge — Architecture

24 agents | 900+ skills | 13 workflows

## Agents

| Agent | Domain | Unique Responsibility |
|-------|--------|-----------------------|
| `orchestrator` | Multi-agent coordination | Breaks complex tasks into parallel sub-tasks, delegates to specialists |
| `project-planner` | Discovery & planning | Writes structured implementation plans, estimates complexity |
| `frontend-specialist` | Web UI/UX | React, Vue, Next.js, Svelte, CSS, HTML — **web only** |
| `backend-specialist` | API & business logic | REST/GraphQL APIs, Express, FastAPI, NestJS |
| `database-architect` | Schema & SQL | Schema design, migrations, Prisma, SQL optimization |
| `mobile-developer` | iOS, Android, RN | Flutter, React Native, Expo — **mobile only, not frontend-specialist** |
| `devops-engineer` | CI/CD & infra | Docker, Kubernetes, GitHub Actions, AWS/Azure/GCP |
| `security-auditor` | Compliance & defense | OWASP top 10, auth audits, threat modeling |
| `penetration-tester` | Offensive security | Red team tactics, exploit research, vuln scanning |
| `test-engineer` | Testing strategy | Unit, integration, E2E — test plan generation |
| `debugger` | Root cause analysis | Systematic diagnosis, stack trace reading |
| `performance-optimizer` | Speed & Web Vitals | Profiling, Lighthouse, bundle analysis |
| `seo-specialist` | Search ranking | Meta tags, structured data, Core Web Vitals for SEO |
| `documentation-writer` | Docs & manuals | READMEs, API docs, onboarding guides |
| `product-manager` | Requirements | User stories, acceptance criteria, feature specs |
| `product-owner` | Strategy & backlog | Roadmap, prioritization, stakeholder alignment |
| `qa-automation-engineer` | E2E automation | Playwright, Cypress, CI test pipelines |
| `code-archaeologist` | Legacy refactoring | Reads and reshapes old codebases |
| `explorer-agent` | Codebase analysis | Maps unknown codebases, identifies entry points |
| `code-reviewer` | Logic & quality audit | Business logic correctness, pattern compliance |
| `code-quality-reviewer-agent` | Code quality metrics | Style, complexity, duplication — distinct from logic review |
| `implementer-agent` | Task execution | General-purpose implementation, shell scripts, AI/ML tasks |
| `spec-reviewer-agent` | Requirement verification | Validates spec completeness before implementation |
| `game-developer` | Game logic | Unity, Godot, Phaser, game mechanics |

## Agent Selection Guide

| Scenario | Use This Agent |
|----------|---------------|
| Web UI bug | `frontend-specialist` |
| API endpoint | `backend-specialist` |
| Mobile screen | `mobile-developer` (never `frontend-specialist`) |
| SQL query slow | `database-architect` |
| Auth vulnerability | `security-auditor` |
| Red team / pentest | `penetration-tester` |
| Coverage gaps | `test-engineer` |
| Bug + unknown cause | `debugger` + `explorer-agent` |
| Logic audit | `code-reviewer` |
| Style/complexity audit | `code-quality-reviewer-agent` |
| Old codebase | `code-archaeologist` |
| Big feature | `orchestrator` → delegates to others |

## Workflows (Slash Commands)

`/brainstorm` `/write-plan` `/execute-plan` `/create` `/debug` `/deploy` `/enhance` `/orchestrate` `/preview` `/status` `/test` `/ui-ux-pro-max` `/write-plan`

See [`docs/WORKFLOWS.md`](./docs/WORKFLOWS.md) for full documentation.

## Skill Discovery

```bash
# Search skills
genesis-forge search "<task>"

# Rebuild index after adding skills
npm run build-registry

# Route a task
genesis-forge route "<task description>"
```

## Directory Structure

```
agent/
├── rules/GEMINI.md       # Always-on global rules (optional Gemini CLI integration)
├── agents/               # 24 specialist agent personas
├── skills/               # 900+ skill modules (SKILL.md per skill)
├── workflows/            # 13 slash-command workflow files
├── scripts/              # Routing, validation, session memory scripts
├── docs/                 # Reference docs (CONFIG, GETTING_STARTED, WORKFLOWS)
└── shared/CONTEXT.md     # Session state (auto-managed)

bin/
└── setup.js              # CLI entry point (genesis-forge command)

lib/
└── skills-core.js        # JS skill loading utilities

package.json              # npm package definition
README.md                 # Project overview
LICENSE                   # MIT
CONTRIBUTING.md           # Contribution guidelines
CHANGELOG.md              # Version history
ATTRIBUTION.md            # Skill sources and licenses
```

## Path Resolution

All scripts auto-detect the kit root via:
1. `$AGENT_ROOT` environment variable (explicit override)
2. Script file location (auto-detected relative path)

Session state resolves via:
1. `$GENESIS_STATE_DIR` env var
2. `~/.gemini/genesis-forge/` (default)
3. `./.genesis-forge/state/` (project-local fallback)
