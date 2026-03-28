---
description: Coordinate multiple agents for complex tasks.
---

# Orchestration Mode — $ARGUMENTS

## PHASE 0: ROUTE (run these, don't reason)
```bash
python agent/scripts/complexity_classifier.py "$TASK"
python agent/scripts/route_task.py "$TASK"
python agent/scripts/skill_search.py "$TASK"
python agent/scripts/session_memory.py inject
```
- SIMPLE → 1 agent direct
- MEDIUM → 2-3 sequential
- COMPLEX → swarm per `agent/docs/LOKI_SWARM_MODE.md`

## PHASE 1: PLAN
1. `project-planner` → create `docs/PLAN.md`
2. (optional) `explorer-agent` → codebase discovery

**STOP. Ask user: "Plan ready. Approve? (Y/N)"**

```bash
python agent/scripts/mid_task_verify.py after_plan docs/PLAN.md
```

## PHASE 2: IMPLEMENT (after approval)
Parallel: `database-architect` + `security-auditor`
Parallel: `backend-specialist` + `frontend-specialist`
Parallel: `test-engineer` + `devops-engineer`

```bash
python agent/scripts/mid_task_verify.py after_backend src/
python agent/scripts/mid_task_verify.py after_tests .
```

## CONTEXT PASSING (mandatory per agent)
Pass: original request + user decisions + previous agent JSON outputs + plan state + routing JSON

## BOUNDARIES
- `**/*.test.*` → test-engineer only
- `**/components/**` → frontend-specialist only
- `**/api/**` → backend-specialist only
- `**/prisma/**` → database-architect only

## EXIT GATE
- [ ] route_task.py JSON followed
- [ ] mid_task_verify.py ran between phases
- [ ] security_scan.py ran
- [ ] All outputs match agent_output_schema.py
