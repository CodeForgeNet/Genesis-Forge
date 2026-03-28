#!/usr/bin/env python3
import os
from pathlib import Path

def resolve_agent_root() -> Path:
    """Resolve the agent kit root directory."""
    env_root = os.environ.get("AGENT_ROOT")
    if env_root:
        return Path(env_root)
    # This script lives at <root>/agent/scripts/utils.py
    return Path(__file__).resolve().parent.parent.parent

AGENT_ROOT = resolve_agent_root()
AGENT_DIR = AGENT_ROOT / "agent"
SCRIPTS_DIR = AGENT_DIR / "scripts"
SKILLS_DIR = AGENT_DIR / "skills"
AGENTS_DIR = AGENT_DIR / "agents"
WORKFLOWS_DIR = AGENT_DIR / "workflows"
RULES_DIR = AGENT_DIR / "rules"
SHARED_DIR = AGENT_DIR / "shared"
DOCS_DIR = AGENT_DIR / "docs"

def get_state_dir() -> Path:
    """Resolve the state directory for session memory."""
    env_state = os.environ.get("GENESIS_STATE_DIR")
    if env_state:
        return Path(env_state)
    
    # Default to ~/.genesis-forge/state/
    home_state = Path.home() / ".genesis-forge" / "state"
    try:
        home_state.mkdir(parents=True, exist_ok=True)
        return home_state
    except Exception:
        # Fallback to local .genesis-forge/state
        local_state = AGENT_ROOT / ".genesis-forge" / "state"
        local_state.mkdir(parents=True, exist_ok=True)
        return local_state

