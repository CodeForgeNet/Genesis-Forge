# Loki Mode & Swarm Mode

> **Status:** This file defines what Loki Mode and Swarm Mode ARE and HOW they work.
> Previously these were referenced but never defined, making behavior model-dependent.
> This file makes them deterministic.

---

## Loki Mode

**What it is:** Auto-routing mode. Instead of the user specifying which agents to use,
Loki Mode runs `route_task.py` and `complexity_classifier.py` automatically, then
selects agents and skills without user input.

**When it activates:** Whenever the user does NOT explicitly name an agent or workflow.

**Execution protocol:**

```
Step 1: Run complexity_classifier.py on the raw user task
Step 2: Run route_task.py on the raw user task
Step 3: Read session_memory.py inject (get persistent context)
Step 4: Based on complexity output:
          SIMPLE  → Invoke single agent directly. No plan. No orchestration.
          MEDIUM  → Invoke 2-3 agents sequentially with context passing.
          COMPLEX → Trigger Swarm Mode (see below).
Step 5: Inject context block (from agent_output_schema.py build_context_block)
Step 6: Execute.
Step 7: Validate output against agent_output_schema.py
Step 8: If validation fails → retry_handler.py check <output>
Step 9: Append output to session_memory.py
```

**What Loki Mode does NOT do:**
- It does NOT ask the model to decide which agents to use
- It does NOT use free-form reasoning for skill selection
- It does NOT skip schema validation
- It does NOT bypass retry handling

**Model behavior difference:**

| Model Tier | Loki Mode Behavior |
|------------|--------------------|
| Low (Haiku) | Reads route_task.py JSON. Executes exactly. No deviation. |
| Mid (Sonnet) | Reads JSON. May add 1 supplementary skill if clearly relevant. |
| High (Opus) | Reads JSON. Can override routing with explicit justification in output. |

---

## Swarm Mode

**What it is:** Parallel multi-agent execution for COMPLEX tasks.
Triggered automatically when complexity_classifier returns COMPLEX.

**It is NOT:**
- Random parallel agent spawning
- "More agents = better"
- A way to bypass PLAN.md requirement

**Swarm execution protocol:**

```
PHASE 0: Pre-swarm gate (MANDATORY)
  [ ] PLAN.md exists AND user has approved it
  [ ] complexity = COMPLEX (from classifier)
  [ ] Agent count from route_task.py >= 3
  If any check fails → STOP. Do not enter swarm mode.

PHASE 1: Foundation agents (SEQUENTIAL, not parallel)
  - project-planner (if no PLAN.md)
  - explorer-agent (if codebase not yet mapped)
  - database-architect (if schema changes needed)
  WHY SEQUENTIAL: Later agents depend on these outputs.

PHASE 2: Core agents (PARALLEL)
  - backend-specialist + frontend-specialist (simultaneously)
  - mobile-developer (if mobile, replaces frontend-specialist)
  WHY PARALLEL: These are domain-independent within the plan.

PHASE 3: Quality agents (PARALLEL)
  - test-engineer + security-auditor (simultaneously)
  WHY PARALLEL: They review completed work, not each other.

PHASE 4: Finalization (SEQUENTIAL)
  - devops-engineer (deploys after all code is verified)
  - performance-optimizer (only if explicitly requested)
  WHY SEQUENTIAL: Depends on everything before it.

PHASE 5: Synthesis
  Orchestrator collects ALL agent outputs (JSON schema).
  Builds unified report. Runs full checklist.py verification.
```

**Parallel group rules:**
- Agents in the same parallel group CANNOT write to the same file
- Conflict detected → route_task.py resolves by file type ownership
- If conflict unresolvable → make sequential, not parallel

**Context passing in swarm:**
Every agent in EVERY phase receives:
1. Original user request (verbatim)
2. PLAN.md content (full)
3. session_memory.py inject output
4. JSON outputs from ALL preceding agents (not prose summaries)

**Swarm exit criteria:**
- All agents status = success OR partial (no failed allowed)
- mid_task_verify.py passes for each phase
- verification_passed = true in all agent outputs
- checklist.py runs clean

**What to do when swarm has a failed agent:**
```
IF agent_status == "failed":
  → retry_handler.py strategy <agent> "agent_failed" <retry_count>
  → Do NOT let other parallel agents wait
  → Run failed agent retry in background
  → If max_retries reached → use fallback_agent
  → Mark swarm phase as "degraded" not "failed"
  → Continue to next phase with degraded context noted
```

---

## Skill Loading in Loki/Swarm Mode

**Old behavior (broken for low models):**
```
User request → model guesses relevant skill → loads SKILL.md
```

**New behavior:**
```
User request → route_task.py → skills[] list → load exactly those SKILL.md files
```

**Skill compression for low models:**
Every SKILL.md should have a `## TL;DR` section at the top (max 5 bullet points).
Low models read ONLY the TL;DR. High models read the full file.

To add TL;DR to a skill:
```bash
# Add to top of any SKILL.md:
## TL;DR (Low Model Mode)
- What this skill does in one sentence
- The 3 most important rules
- The 1 command to run if applicable
- When NOT to use this skill
```

---

## Model Tier Detection

The system adapts behavior based on which model is running.

```python
# In route_task.py and orchestrator, detect tier by:
# (This is set by the runner - Claude Code, Gemini CLI, etc.)

MODEL_TIERS = {
    "haiku":   "low",    # Atomic tasks only. No meta-reasoning.
    "sonnet":  "mid",    # Can handle medium orchestration.
    "opus":    "high",   # Full orchestration. Can override routing.
    "flash":   "low",    # Treat like haiku.
    "pro":     "mid",    # Treat like sonnet.
    "unknown": "mid",    # Safe default.
}

# Low model constraints:
# - Max 1 skill loaded per agent invocation
# - Skill TL;DR only (not full SKILL.md)
# - Agent prompt max 500 words
# - Output schema strictly enforced (fail fast if violated)
# - No meta-reasoning ("decide what to do") - only execution

# High model capabilities:
# - Can load multiple skills
# - Full SKILL.md content
# - Can override routing with justification
# - Can compose skills dynamically
# - Can identify missing agents and self-add them
```

---

## Summary: What Changed

| Before | After |
|--------|-------|
| Skill selection: model guesses | Deterministic: route_task.py |
| Complexity: always full orchestration | Classified: simple/medium/complex |
| Context passing: instructional | Mechanical: JSON schema injection |
| Agent failure: chain dies | retry_handler.py recovery |
| Mid-task errors: found at end | mid_task_verify.py catches early |
| Session: always cold start | session_memory.py persists context |
| Swarm mode: undefined | Protocol defined above |
| Loki mode: model-dependent | Deterministic steps above |
| High model: same as low | Can override, compose, extend |
