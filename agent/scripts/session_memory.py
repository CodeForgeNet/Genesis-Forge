#!/usr/bin/env python3
"""
session_memory.py - Persistent Session Memory
=============================================
Persists decisions, context, and agent outputs across sessions.
Eliminates cold starts. Low models get pre-loaded context.
High models skip re-discovery and use cached decisions.

State persists to (in order of priority):
  1. $GENESIS_STATE_DIR (if set)
  2. ~/.genesis/state/   (global install default)
  3. ./.genesis/state/   (project-local fallback)

Usage:
  python3 agent/scripts/session_memory.py read
  python3 agent/scripts/session_memory.py write --key "tech_stack" --value "Next.js + FastAPI"
  python3 agent/scripts/session_memory.py append-output agent_output.json
  python3 agent/scripts/session_memory.py clear
  python3 agent/scripts/session_memory.py inject   # Outputs context block for prompt injection
  python3 agent/scripts/session_memory.py session-start
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add current directory to path for local imports
sys.path.append(str(Path(__file__).resolve().parent))
import utils
from utils import AGENT_ROOT, SHARED_DIR, get_state_dir

STATE_DIR = get_state_dir()
MEMORY_FILE = STATE_DIR / "session_memory.json"
CONTEXT_MD = SHARED_DIR / "CONTEXT.md"


def load_memory() -> Dict[str, Any]:
    if not MEMORY_FILE.exists():
        return _empty_memory()
    try:
        with open(MEMORY_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[session_memory] Warning: could not load memory ({e}). Starting fresh.", file=sys.stderr)
        return _empty_memory()


def save_memory(memory: Dict[str, Any]):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    memory["last_updated"] = datetime.now().isoformat()
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
        _sync_to_markdown(memory)
    except IOError as e:
        print(f"[session_memory] Error: could not save memory — {e}", file=sys.stderr)


def _empty_memory() -> Dict[str, Any]:
    return {
        "project": {
            "name": None,
            "type": None,          # web | mobile | backend | fullstack
            "tech_stack": [],
            "framework": None,
            "database": None,
            "auth_type": None,
        },
        "decisions": {},           # key-value: user decisions that should persist
        "agent_history": [],       # Last N agent outputs (summarized)
        "approved_plans": [],      # Paths to approved PLAN.md files
        "known_issues": [],        # Outstanding issues not yet fixed
        "env_vars": [],            # Required env vars discovered
        "file_ownership": {},      # file_path → last_agent_to_touch
        "session_count": 0,
        "last_updated": None
    }


def write_key(key: str, value: Any):
    memory = load_memory()
    # Support dot notation: project.tech_stack
    keys = key.split(".")
    target = memory
    for k in keys[:-1]:
        target = target.setdefault(k, {})
    target[keys[-1]] = value
    save_memory(memory)
    print(f"Saved: {key} = {value}")


def append_agent_output(output_path: str):
    """Summarize and append agent output to memory (keeps last 10)."""
    try:
        with open(output_path) as f:
            output = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[session_memory] Error reading agent output: {e}", file=sys.stderr)
        sys.exit(1)

    memory = load_memory()

    summary = {
        "agent": output.get("agent_name"),
        "status": output.get("status"),
        "summary": output.get("summary", ""),
        "files_changed": [c.get("path") for c in output.get("files_changed", [])],
        "issues_count": len(output.get("issues", [])),
        "requires_followup": output.get("requires_followup", False),
        "next_agent": output.get("next_agent"),
        "timestamp": datetime.now().isoformat()
    }

    memory["agent_history"].append(summary)
    memory["agent_history"] = memory["agent_history"][-10:]  # Keep last 10

    # Update file ownership
    for change in output.get("files_changed", []):
        path = change.get("path")
        if path:
            memory["file_ownership"][path] = output.get("agent_name")

    # Extract known issues
    for issue in output.get("issues", []):
        if issue.get("severity") in ("critical", "high"):
            entry = {
                "severity": issue["severity"],
                "message": issue["message"],
                "from_agent": output.get("agent_name"),
                "resolved": False
            }
            if entry not in memory["known_issues"]:
                memory["known_issues"].append(entry)

    save_memory(memory)
    print(f"Appended output from {output.get('agent_name')} to session memory.")


def inject_context() -> str:
    """Output context block for injection into agent prompts."""
    memory = load_memory()

    if not memory.get("last_updated"):
        return "# No session memory found. Fresh start.\n"

    lines = [
        "=" * 60,
        "SESSION MEMORY (persisted from previous sessions)",
        "=" * 60,
        ""
    ]

    proj = memory.get("project", {})
    if any(proj.values()):
        lines.append("PROJECT:")
        for k, v in proj.items():
            if v:
                lines.append(f"  {k}: {v}")
        lines.append("")

    decisions = memory.get("decisions", {})
    if decisions:
        lines.append("DECISIONS ALREADY MADE:")
        for k, v in decisions.items():
            lines.append(f"  {k}: {v}")
        lines.append("")

    history = memory.get("agent_history", [])
    if history:
        lines.append("RECENT AGENT WORK (last 5):")
        for h in history[-5:]:
            lines.append(f"  [{h['agent']}] {h['status']} - {h['summary'][:100]}")
            if h.get("files_changed"):
                lines.append(f"    Files: {', '.join(h['files_changed'][:3])}")
        lines.append("")

    issues = [i for i in memory.get("known_issues", []) if not i.get("resolved")]
    if issues:
        lines.append("OUTSTANDING ISSUES:")
        for issue in issues[:5]:
            lines.append(f"  [{issue['severity'].upper()}] {issue['message']}")
        lines.append("")

    env_vars = memory.get("env_vars", [])
    if env_vars:
        lines.append(f"ENV VARS REQUIRED: {', '.join(env_vars)}")
        lines.append("")

    approved = memory.get("approved_plans", [])
    if approved:
        lines.append(f"APPROVED PLANS: {', '.join(approved)}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("USE THE ABOVE. DO NOT re-discover what's already known.")
    lines.append("=" * 60)

    return "\n".join(lines)


def _sync_to_markdown(memory: Dict[str, Any]):
    """Sync memory to CONTEXT.md for agents that read markdown."""
    lines = [
        "# Session Context",
        f"> Last updated: {memory.get('last_updated', 'unknown')}",
        f"> Sessions: {memory.get('session_count', 0)}",
        "",
    ]

    proj = memory.get("project", {})
    if any(proj.values()):
        lines.append("## Project")
        for k, v in proj.items():
            if v:
                lines.append(f"- **{k}**: {v}")
        lines.append("")

    decisions = memory.get("decisions", {})
    if decisions:
        lines.append("## Decisions")
        for k, v in decisions.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

    history = memory.get("agent_history", [])
    if history:
        lines.append("## Recent Agent Work")
        for h in history[-5:]:
            lines.append(f"- **{h['agent']}** ({h['status']}): {h['summary'][:120]}")
        lines.append("")

    issues = [i for i in memory.get("known_issues", []) if not i.get("resolved")]
    if issues:
        lines.append("## Outstanding Issues")
        for issue in issues:
            lines.append(f"- `{issue['severity'].upper()}` {issue['message']}")
        lines.append("")

    try:
        CONTEXT_MD.parent.mkdir(parents=True, exist_ok=True)
        with open(CONTEXT_MD, "w") as f:
            f.write("\n".join(lines))
    except IOError as e:
        print(f"[session_memory] Warning: could not sync CONTEXT.md — {e}", file=sys.stderr)


def increment_session():
    memory = load_memory()
    memory["session_count"] = memory.get("session_count", 0) + 1
    save_memory(memory)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "read":
        memory = load_memory()
        print(json.dumps(memory, indent=2))

    elif cmd == "write":
        if "--key" not in sys.argv or "--value" not in sys.argv:
            print("Usage: session_memory.py write --key <key> --value <value>")
            sys.exit(1)
        key_idx = sys.argv.index("--key") + 1
        val_idx = sys.argv.index("--value") + 1
        write_key(sys.argv[key_idx], sys.argv[val_idx])

    elif cmd == "append-output":
        if len(sys.argv) < 3:
            print("Usage: session_memory.py append-output <output.json>")
            sys.exit(1)
        append_agent_output(sys.argv[2])

    elif cmd == "inject":
        print(inject_context())

    elif cmd == "clear":
        if MEMORY_FILE.exists():
            MEMORY_FILE.unlink()
        print("Session memory cleared.")

    elif cmd == "session-start":
        increment_session()
        print(inject_context())

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
