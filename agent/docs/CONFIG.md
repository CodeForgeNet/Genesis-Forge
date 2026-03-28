# Genesis Forge — Configuration

## How It Works

Genesis Forge is a **pure data source** — it provides agents, skills, and workflows to your existing CLI (Gemini CLI, Claude CLI, or Genesis Forge CLI).

**No API keys needed.** Your CLI handles authentication separately.

---

## Gemini CLI Integration

The kit includes a rules file that Gemini CLI loads automatically:

```bash
cp agent/rules/GEMINI.md ~/.gemini/GEMINI.md
```

This enables:
- Task routing to the right agent
- Skill loading based on context
- Workflow automation

---

## Claude CLI / Cline Integration

Use the MCP server to expose skills as tools:

```bash
node lib/mcp-server.js
```

Add to your Claude/Cline MCP config:

```json
{
  "mcpServers": {
    "genesis": {
      "command": "node",
      "args": ["/path/to/genesis-forge/lib/mcp-server.js"]
    }
  }
}
```

---

## Session State Persistence

The kit can remember context across sessions.

**Default location:** `~/.genesis/state/session_memory.json`

**Override:** Set `GENESIS_STATE_DIR` environment variable.

---

## Kit Path Resolution

All scripts auto-detect the kit root via:
1. `$AGENT_ROOT` environment variable (explicit override)
2. Script file location (auto-detected)

---

## Rebuilding the Skill Registry

If you add or remove skills, regenerate the registry:

```bash
python3 agent/scripts/build_skill_registry.py
```
