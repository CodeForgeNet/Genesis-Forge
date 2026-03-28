#!/usr/bin/env python3
"""
retry_handler.py - Agent Failure Recovery
==========================================
Handles agent failures, partial outputs, and dead-end chains.
Provides retry strategies based on failure type and model tier.

Usage:
  python agent/scripts/retry_handler.py check output.json
  python agent/scripts/retry_handler.py strategy "frontend-specialist" "failed"
"""

import sys
import json
from typing import Dict, Any, Optional


# ─── FAILURE PATTERNS & RECOVERY STRATEGIES ───────────────────────────────────

RECOVERY_STRATEGIES = {

    # Agent returned status=failed
    "agent_failed": {
        "max_retries": 2,
        "strategy": "simplify_and_retry",
        "actions": [
            "Strip the task to ONE atomic action only",
            "Remove all context except: file path + exact change required",
            "If retry 2 fails: route to implementer-agent as fallback",
        ],
        "fallback_agent": "implementer-agent"
    },

    # Agent returned status=partial (did some work, not all)
    "agent_partial": {
        "max_retries": 1,
        "strategy": "continue_from_checkpoint",
        "actions": [
            "Read files_changed from partial output",
            "Build new task: 'Complete the remaining work. Already done: {files_changed}'",
            "Pass structured outputs from partial as context",
            "Invoke same agent with narrowed task"
        ],
        "fallback_agent": None  # Same agent, narrowed task
    },

    # Agent output failed schema validation
    "schema_invalid": {
        "max_retries": 1,
        "strategy": "force_json_output",
        "actions": [
            "Prepend to task: 'CRITICAL: Your response MUST be valid JSON only. No prose.'",
            "Append schema template to prompt",
            "Set max_tokens lower to prevent rambling"
        ],
        "fallback_agent": None
    },

    # Agent crossed domain boundary (wrote files it shouldn't)
    "boundary_violation": {
        "max_retries": 0,  # Don't retry violator
        "strategy": "reroute",
        "actions": [
            "Identify violated files",
            "Route violated files to correct domain agent",
            "Do NOT re-invoke the violating agent for those files"
        ],
        "fallback_agent": "route_by_file_type"
    },

    # Agent produced no files_changed and no outputs
    "empty_output": {
        "max_retries": 2,
        "strategy": "inject_example",
        "actions": [
            "Retry 1: Add example of expected output to prompt",
            "Retry 2: Break task into single-file subtask",
            "If still empty: mark as blocked, notify orchestrator"
        ],
        "fallback_agent": "implementer-agent"
    },

    # Verification scripts failed after agent work
    "verification_failed": {
        "max_retries": 2,
        "strategy": "targeted_fix",
        "actions": [
            "Extract exact errors from verification script output",
            "Route errors to debugger agent with: error message + file + line",
            "Re-run verification after fix",
        ],
        "fallback_agent": "debugger"
    }
}


# ─── FILE TYPE TO AGENT MAPPING (for boundary violation rerouting) ─────────────

FILE_TYPE_AGENT_MAP = {
    r".*\.test\.(ts|tsx|js|jsx)$": "test-engineer",
    r".*/__tests__/.*": "test-engineer",
    r".*/components/.*": "frontend-specialist",
    r".*/pages/.*": "frontend-specialist",
    r".*/app/.*\.(tsx|jsx)$": "frontend-specialist",
    r".*/api/.*": "backend-specialist",
    r".*/server/.*": "backend-specialist",
    r".*/routes/.*": "backend-specialist",
    r".*/prisma/.*": "database-architect",
    r".*/migrations/.*": "database-architect",
    r".*/drizzle/.*": "database-architect",
    r".*/docker.*": "devops-engineer",
    r".*Dockerfile.*": "devops-engineer",
    r".*\.yml$": "devops-engineer",
    r".*\.yaml$": "devops-engineer",
    r".*/mobile/.*": "mobile-developer",
    r".*\.swift$": "mobile-developer",
    r".*\.kt$": "mobile-developer",
}


def detect_failure_type(output: Dict[str, Any]) -> str:
    """Detect what kind of failure occurred from agent output."""
    status = output.get("status", "")

    if status == "failed":
        return "agent_failed"
    elif status == "partial":
        return "agent_partial"
    elif not output.get("files_changed") and not output.get("outputs"):
        return "empty_output"
    elif not output.get("verification_passed", True):
        return "verification_failed"
    else:
        return "unknown"


def check_boundary_violations(output: Dict[str, Any]) -> list:
    """Check if agent wrote files outside their domain."""
    import re
    agent = output.get("agent_name", "")
    violations = []

    for change in output.get("files_changed", []):
        path = change.get("path", "")
        for pattern, owner_agent in FILE_TYPE_AGENT_MAP.items():
            if re.match(pattern, path) and owner_agent != agent:
                violations.append({
                    "file": path,
                    "written_by": agent,
                    "should_be": owner_agent
                })

    return violations


def get_recovery_plan(failure_type: str, agent_name: str, retry_count: int) -> Dict[str, Any]:
    """Get recovery strategy for a given failure type and retry count."""
    strategy = RECOVERY_STRATEGIES.get(failure_type, RECOVERY_STRATEGIES["agent_failed"])

    if retry_count >= strategy["max_retries"]:
        return {
            "action": "use_fallback",
            "fallback_agent": strategy["fallback_agent"],
            "message": f"Max retries ({strategy['max_retries']}) reached for {agent_name}. Using fallback.",
            "abort": strategy["fallback_agent"] is None
        }

    return {
        "action": "retry",
        "strategy": strategy["strategy"],
        "steps": strategy["actions"],
        "next_retry": retry_count + 1,
        "max_retries": strategy["max_retries"],
        "message": f"Retry {retry_count + 1}/{strategy['max_retries']} for {agent_name}"
    }


def build_retry_prompt(original_task: str, failure_type: str, output: Dict[str, Any]) -> str:
    """Build a simplified retry prompt based on failure type."""
    if failure_type == "agent_failed":
        return f"""RETRY TASK (simplified):
{original_task}

CONSTRAINT: Do ONE thing only. Pick the single most important action.
OUTPUT: Valid JSON per agent_output_schema.py. Nothing else."""

    elif failure_type == "agent_partial":
        done = [c.get("path") for c in output.get("files_changed", [])]
        return f"""CONTINUE TASK (partial work exists):
Original: {original_task}
Already completed: {done}
DO: Complete only what's NOT in the above list.
OUTPUT: Valid JSON per agent_output_schema.py."""

    elif failure_type == "schema_invalid":
        return f"""CRITICAL: Previous response was invalid JSON.
TASK: {original_task}
RULES:
- Respond ONLY with valid JSON
- No prose, no markdown, no explanation
- Use exact schema from agent_output_schema.py
- Start your response with {{ and end with }}"""

    elif failure_type == "empty_output":
        return f"""TASK: {original_task}
REQUIREMENT: You MUST produce at least one file_changed entry.
If blocked, set status=failed and explain in verification_notes.
Do NOT return empty files_changed."""

    return original_task


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  retry_handler.py check <output.json>")
        print("  retry_handler.py strategy <agent> <failure_type> [retry_count]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "check":
        with open(sys.argv[2]) as f:
            output = json.load(f)

        failure = detect_failure_type(output)
        violations = check_boundary_violations(output)

        result = {
            "failure_type": failure,
            "boundary_violations": violations,
            "needs_recovery": failure != "unknown" or len(violations) > 0,
            "recovery_plan": get_recovery_plan(failure, output.get("agent_name", ""), 0)
        }
        print(json.dumps(result, indent=2))

    elif cmd == "strategy":
        agent = sys.argv[2]
        failure_type = sys.argv[3]
        retry_count = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        result = get_recovery_plan(failure_type, agent, retry_count)
        print(json.dumps(result, indent=2))
