# Getting Started with Genesis Forge

Welcome! This guide will get you up and running in 5 minutes.

## Prerequisites

- **Node.js** >= 18.0.0 ([download](https://nodejs.org))
- **Python 3** >= 3.8 ([download](https://python.org))
- **Gemini CLI or Claude CLI** (already authenticated)

---

## Step 1: Install

```bash
npm install -g genesis-forge
```

Or clone for local use:

```bash
git clone https://github.com/[user]/genesis-forge
cd genesis-forge
```

---

## Step 2: Connect to Your CLI

### Gemini CLI

```bash
cp agent/rules/GEMINI.md ~/.gemini/GEMINI.md
```

### Claude CLI / Cline

```bash
node lib/mcp-server.js
```

Add the MCP server to your Claude/Cline config.

---

## Step 3: Use It!

The CLI (Gemini/Claude) already handles authentication. Genesis Forge provides:
- **Agents** — Specialist agents (frontend, backend, security, etc.)
- **Skills** — 80+ production-ready skill modules
- **Workflows** — Automated workflows (/create, /debug, /deploy, etc.)

Just start using your CLI normally — it will automatically load agents and skills from Genesis Forge.

---

## Common Tasks

### Build Something
```
/create a react dashboard with charts
```

### Debug an Issue
```
/debug my auth middleware returning 401
```

### Security Audit
```
/audit my login system for vulnerabilities
```

### Deploy
```
/deploy to vercel production
```

---

## Optional: Build Full Skill Registry

For routing across all 900+ skills:

```bash
python3 agent/scripts/build_skill_registry.py
```

---

## Next Steps

- [`docs/WORKFLOWS.md`](./WORKFLOWS.md) — All 13 workflows explained
- [`ARCHITECTURE.md`](../ARCHITECTURE.md) — How the system works
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — Adding your own skills and agents
