#!/usr/bin/env python3
"""
agent_output_schema.py - Structured Agent Handoff Schema
=========================================================
Defines and validates the JSON schema that every agent MUST output.
Eliminates free-form markdown parsing between agents.
Low models read clean structured data. High models stop wasting tokens parsing prose.

Usage (validation):
  python agent/scripts/agent_output_schema.py validate output.json
  python agent/scripts/agent_output_schema.py template frontend-specialist
"""

import sys
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field


# ─── AGENT OUTPUT SCHEMA ──────────────────────────────────────────────────────

@dataclass
class FileChange:
    path: str           # Relative file path
    action: str         # created | modified | deleted
    summary: str        # One-line description of what changed


@dataclass
class AgentIssue:
    severity: str       # critical | high | medium | low | info
    category: str       # security | bug | performance | style | missing
    message: str
    file: Optional[str] = None
    line: Optional[int] = None


@dataclass
class AgentOutput:
    # ── Identity ─────────────────────────────────────────────────────────────
    agent_name: str                     # e.g. "frontend-specialist"
    task_received: str                  # Exact task this agent was given
    status: str                         # success | partial | failed

    # ── Work Done ─────────────────────────────────────────────────────────────
    files_changed: List[FileChange]     # All files created/modified/deleted
    summary: str                        # 2-3 sentence summary of what was done

    # ── Handoff Data ──────────────────────────────────────────────────────────
    # Structured data the NEXT agent needs -- no parsing required
    outputs: Dict[str, Any]            # Domain-specific structured output

    # ── Issues Found ──────────────────────────────────────────────────────────
    issues: List[AgentIssue]           # Problems discovered during work

    # ── Next Steps ────────────────────────────────────────────────────────────
    requires_followup: bool            # Does next agent NEED to act?
    next_agent: Optional[str]          # Recommended next agent if any
    next_agent_task: Optional[str]     # Exact task to pass to next agent

    # ── Verification ──────────────────────────────────────────────────────────
    verification_passed: bool
    verification_notes: str


# ─── DOMAIN-SPECIFIC OUTPUT SCHEMAS ──────────────────────────────────────────
# These go into the `outputs` field above.

DOMAIN_OUTPUT_SCHEMAS = {

    "frontend-specialist": {
        "components_created": ["list of component names"],
        "routes_affected": ["list of routes"],
        "dependencies_added": ["npm packages added"],
        "props_interfaces": {"ComponentName": "TypeScript interface string"},
        "state_management": "none | useState | zustand | redux",
        "css_approach": "tailwind | css-modules | styled-components | other",
        "a11y_score": "pass | fail | not-checked",
    },

    "backend-specialist": {
        "endpoints_created": [{"method": "GET", "path": "/api/x", "auth_required": True}],
        "endpoints_modified": [],
        "request_schemas": {"EndpointName": "Zod/Pydantic schema string"},
        "response_schemas": {},
        "middleware_added": [],
        "env_vars_required": [],
        "breaking_changes": False,
    },

    "database-architect": {
        "tables_created": [],
        "tables_modified": [],
        "migrations_created": ["migration file paths"],
        "indexes_added": [],
        "relations": [{"from": "table.col", "to": "table.col", "type": "one-to-many"}],
        "seed_data_required": False,
    },

    "test-engineer": {
        "tests_written": [{"file": "path", "count": 0, "type": "unit|e2e|integration"}],
        "coverage_before": "0%",
        "coverage_after": "0%",
        "failing_tests": [],
        "mocks_created": [],
        "test_command": "npm test",
    },

    "security-auditor": {
        "vulnerabilities": [{"severity": "high", "type": "OWASP", "location": "file:line"}],
        "auth_reviewed": False,
        "secrets_exposed": False,
        "dependency_issues": [],
        "compliance_gaps": [],
        "overall_risk": "low | medium | high | critical",
    },

    "debugger": {
        "root_cause": "string",
        "hypothesis_tested": ["list of hypotheses"],
        "fix_applied": True,
        "files_fixed": [],
        "regression_risk": "none | low | medium | high",
        "reproduce_steps": [],
    },

    "devops-engineer": {
        "services_configured": [],
        "env_vars_set": [],
        "docker_changes": False,
        "ci_pipeline_updated": False,
        "deployment_url": None,
        "health_check_passing": False,
    },

    "performance-optimizer": {
        "lighthouse_before": {"performance": 0, "accessibility": 0, "seo": 0},
        "lighthouse_after": {"performance": 0, "accessibility": 0, "seo": 0},
        "bundle_size_before_kb": 0,
        "bundle_size_after_kb": 0,
        "optimizations_applied": [],
        "remaining_bottlenecks": [],
    },

    "project-planner": {
        "plan_file": "docs/PLAN.md",
        "phases": [{"name": "Phase 1", "tasks": [], "agents": [], "estimated_hours": 0}],
        "total_estimated_hours": 0,
        "dependencies": [],
        "risks": [],
    },
}


def get_template(agent_name: str) -> Dict[str, Any]:
    """Return empty template for a specific agent."""
    base = asdict(AgentOutput(
        agent_name=agent_name,
        task_received="",
        status="success",
        files_changed=[],
        summary="",
        outputs=DOMAIN_OUTPUT_SCHEMAS.get(agent_name, {}),
        issues=[],
        requires_followup=False,
        next_agent=None,
        next_agent_task=None,
        verification_passed=False,
        verification_notes=""
    ))
    return base


def validate(output: Dict[str, Any]) -> Dict[str, Any]:
    """Validate an agent output JSON. Returns validation result."""
    required_fields = [
        "agent_name", "task_received", "status", "files_changed",
        "summary", "outputs", "issues", "requires_followup",
        "verification_passed", "verification_notes"
    ]
    errors = []
    warnings = []

    for field in required_fields:
        if field not in output:
            errors.append(f"Missing required field: {field}")

    if "status" in output and output["status"] not in ["success", "partial", "failed"]:
        errors.append(f"Invalid status: {output['status']}. Must be success|partial|failed")

    if "summary" in output and len(output["summary"]) > 500:
        warnings.append("Summary exceeds 500 chars. Keep it concise for low-model parsing.")

    if "requires_followup" in output and output["requires_followup"]:
        if not output.get("next_agent"):
            errors.append("requires_followup=true but next_agent not specified")
        if not output.get("next_agent_task"):
            errors.append("requires_followup=true but next_agent_task not specified")

    if "issues" in output:
        for i, issue in enumerate(output["issues"]):
            if "severity" not in issue:
                errors.append(f"Issue[{i}] missing severity")
            elif issue["severity"] not in ["critical", "high", "medium", "low", "info"]:
                errors.append(f"Issue[{i}] invalid severity: {issue['severity']}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


# ─── ORCHESTRATOR CONTEXT BLOCK BUILDER ───────────────────────────────────────

def build_context_block(
    user_request: str,
    previous_outputs: List[Dict[str, Any]],
    plan_content: Optional[str] = None,
    routing: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build the mandatory context block injected into every agent invocation.
    This is what makes low models work -- they receive structured facts, not prose.
    """
    block = ["=" * 60, "AGENT CONTEXT BLOCK (READ THIS FIRST)", "=" * 60]

    block.append(f"\nUSER REQUEST:\n{user_request}\n")

    if routing:
        block.append(f"ROUTING:\n{json.dumps(routing, indent=2)}\n")

    if plan_content:
        block.append(f"CURRENT PLAN:\n{plan_content[:2000]}\n")  # Truncate for low models

    if previous_outputs:
        block.append("PREVIOUS AGENT OUTPUTS:")
        for out in previous_outputs:
            block.append(f"\n[{out.get('agent_name', 'unknown')}] STATUS: {out.get('status')}")
            block.append(f"SUMMARY: {out.get('summary', '')}")
            # Only pass structured outputs, not full prose
            if out.get("outputs"):
                block.append(f"STRUCTURED OUTPUT:\n{json.dumps(out['outputs'], indent=2)}")
            if out.get("requires_followup") and out.get("next_agent_task"):
                block.append(f"YOUR TASK FROM PREVIOUS AGENT: {out['next_agent_task']}")

    block.append("\n" + "=" * 60)
    block.append("YOUR RESPONSE MUST BE VALID JSON matching agent_output_schema.py")
    block.append("=" * 60)

    return "\n".join(block)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  agent_output_schema.py template <agent-name>")
        print("  agent_output_schema.py validate <output.json>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "template":
        agent = sys.argv[2] if len(sys.argv) > 2 else "frontend-specialist"
        print(json.dumps(get_template(agent), indent=2))

    elif cmd == "validate":
        if len(sys.argv) < 3:
            print("Provide path to output JSON")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            data = json.load(f)
        result = validate(data)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["valid"] else 1)

    elif cmd == "context":
        # Demo: build a context block
        demo = build_context_block(
            user_request="Build a login API with JWT auth",
            previous_outputs=[],
            routing={"agents": ["backend-specialist", "security-auditor"], "complexity": "medium"}
        )
        print(demo)
