---
trigger: always_on
---

# Genesis Forge — Core Rules

## PATH RESOLUTION

All paths use the kit root. Set `AGENT_ROOT` env var if running outside the default location.
Default: the directory where `agent/` lives (auto-detected).

Scripts are at: `<AGENT_ROOT>/agent/scripts/`
Skills are at:  `<AGENT_ROOT>/agent/skills/`
Agents are at:  `<AGENT_ROOT>/agent/agents/`

> **Gemini CLI users:** Copy this file to `~/.gemini/GEMINI.md` or point your Gemini config to it.
> This is **optional** — the kit works standalone without Gemini CLI.

---

## PRIORITY: P0 (this file) > P1 (agent .md) > P2 (SKILL.md)

---

## STEP 1: CLASSIFY REQUEST (silent)

| Type | Keywords | Action |
|------|----------|--------|
| QUESTION | what/how/explain/why | Answer directly. No agents. |
| SIMPLE | fix/add/change (1 file) | 1 agent, no plan |
| BUILD | create/implement/build | Route via scripts |
| DESIGN | UI/page/dashboard | frontend-specialist or mobile-developer |
| SLASH | /create /debug /orchestrate | Follow workflow file |

---

## STEP 2: ROUTE (deterministic, not reasoning)

```
python3 agent/scripts/complexity_classifier.py "$TASK"
python3 agent/scripts/route_task.py "$TASK"
```

- SIMPLE → 1 agent direct
- MEDIUM → 2-3 agents sequential
- COMPLEX → swarm per `agent/docs/LOKI_SWARM_MODE.md`

Skill discovery: `python3 agent/scripts/skill_search.py "$TASK"`
Read ARCHITECTURE.md only if registry is missing.

---

## STEP 3: AGENT PROTOCOL

1. Read agent `.md` → check `skills:` frontmatter → load SKILL.md TL;DR only
2. Low model: TL;DR only, 1 skill max, strict JSON output
3. Mid model: first 1000 chars, 2 skills max
4. High model: full SKILL.md, 4 skills max
5. Announce: `🤖 Applying knowledge of @[agent-name]...`

**Mobile = mobile-developer ONLY. Never frontend-specialist for mobile.**

---

## STEP 4: CODE RULES

- Layered arch: Controller → Service → Repository
- Validate ALL input at API boundary
- No hardcoded secrets — env vars only
- Parameterized queries only
- Hash passwords: bcrypt/argon2

**Web:** frontend-specialist | **Backend:** backend-specialist | **Mobile:** mobile-developer

---

## STEP 5: SOCRATIC GATE

Only ask questions when:
- New feature with 0 context
- Request has conflicting signals
- Tech stack is unspecified for BUILD tasks

Skip gate for: bug fixes, single-file edits, questions, anything with clear context.
Max 2 questions. Never ask what user already stated.

---

## STEP 6: OUTPUT FORMAT

Every agent output = valid JSON per `agent/scripts/agent_output_schema.py`
Run `python3 agent/scripts/mid_task_verify.py` between phases on COMPLEX tasks.

---

## DEPLOY / FINAL CHECKS

Read `agent/docs/DEPLOY_CHECKLIST.md` — do not inline here.

---

## MODES

| Mode | Behavior |
|------|----------|
| plan | 4-phase: Analysis → Planning → Solutioning → Implementation |
| ask | Questions only. No code. |
| edit | Execute directly. Single file = proceed. Multi-file = offer plan first. |

---

## QUICK REF

**Agents:** orchestrator, project-planner, backend-specialist, frontend-specialist, mobile-developer, security-auditor, test-engineer, database-architect, devops-engineer, debugger

**Scripts:** `route_task.py`, `complexity_classifier.py`, `skill_search.py`, `session_memory.py`, `mid_task_verify.py`

---

## OPTIONAL INTEGRATIONS

- **Gemini CLI:** Place this file at `~/.gemini/GEMINI.md` for automatic loading.
- **Session memory:** `python3 agent/scripts/session_memory.py session-start` injects context.
- **MCP servers:** Configure at `~/.gemini/genesis-forge/mcp_config.json` (see `agent/mcp_config.json` for template).
