# Genesis Forge — Workflows Reference

All workflows are invoked via slash commands:

```bash
genesis route "/<workflow> <args>"
```

---

## /brainstorm

**Purpose:** Explore requirements and design before implementing anything.

**Use when:** Starting a new feature, unclear requirements, need to think through trade-offs.

```bash
genesis route "/brainstorm user authentication system with social login"
```

**What it does:** Invokes structured brainstorming to surface requirements, assumptions, and design options before any code is written.

---

## /create

**Purpose:** Build a new feature, component, or module.

**Use when:** You know what you want to build and have clear requirements.

```bash
genesis route "/create a REST API for user profiles with avatar upload"
```

---

## /debug

**Purpose:** Root-cause analysis and fix for bugs, errors, or unexpected behavior.

**Use when:** Something is broken and you need systematic diagnosis.

```bash
genesis route "/debug my JWT middleware returns 401 for valid tokens"
```

**Steps:** Reproduce → Isolate → Root cause → Fix → Verify

---

## /deploy

**Purpose:** Pre-flight production deployment with checks and verification.

**Sub-commands:**
```bash
/deploy           — Interactive deployment wizard
/deploy check     — Pre-deployment checks only
/deploy preview   — Deploy to staging
/deploy production — Deploy to production
/deploy rollback  — Rollback to previous version
```

---

## /enhance

**Purpose:** Performance, quality, SEO, or UX improvements to existing code.

```bash
genesis route "/enhance my product listing page is slow on mobile"
```

---

## /orchestrate

**Purpose:** Complex multi-agent task requiring coordination across domains.

**Use when:** Task spans frontend + backend + database + DevOps simultaneously.

```bash
genesis route "/orchestrate build a complete SaaS billing system"
```

---

## /plan

**Purpose:** Write a structured implementation plan before coding.

```bash
genesis route "/plan refactor our monolith into microservices"
```

**Output:** Phase-by-phase plan with agent assignments, risk flags, and timeline.

---

## /execute-plan

**Purpose:** Execute an existing implementation plan step by step.

```bash
genesis route "/execute-plan"
```

---

## /test

**Purpose:** Generate, run, and improve test coverage.

```bash
genesis route "/test my auth service has no unit tests"
```

---

## /preview

**Purpose:** Preview a component or UI before deployment.

```bash
genesis route "/preview the checkout flow component"
```

---

## /status

**Purpose:** Check current session status, active agents, and outstanding issues.

```bash
genesis route "/status"
```

---

## /ui-ux-pro-max

**Purpose:** Premium UI/UX review and redesign following professional design principles.

```bash
genesis route "/ui-ux-pro-max review my dashboard page"
```

---

## /write-plan

**Purpose:** Write a detailed plan file for a feature or system.

```bash
genesis route "/write-plan multi-tenant auth system"
```
