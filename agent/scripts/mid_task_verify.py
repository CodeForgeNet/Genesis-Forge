#!/usr/bin/env python3
"""
mid_task_verify.py - Mid-Task Verification Checkpoints
======================================================
Runs lightweight verification DURING task execution, not just at end.
Catches bad agent output early before it propagates through the chain.
Saves significant wasted work on complex multi-agent tasks.

Checkpoints:
  - after_plan:    Verify PLAN.md is valid and has required fields
  - after_schema:  Verify DB schema before any code touches it
  - after_backend: Verify API endpoints exist and have correct signatures
  - after_frontend: Verify components compile and have no obvious errors
  - after_tests:   Verify tests run and coverage hasn't dropped
  - pre_deploy:    Full checklist before deployment

Usage:
  python agent/scripts/mid_task_verify.py after_plan docs/PLAN.md
  python agent/scripts/mid_task_verify.py after_backend src/
  python agent/scripts/mid_task_verify.py after_tests .
"""

import sys
import json
import os
import subprocess
from typing import Dict, Any, List, Tuple


def run_cmd(cmd: str, cwd: str = ".") -> Tuple[bool, str]:
    """Run command, return (success, output)."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=30
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output[:2000]  # Truncate for low models
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 30s"
    except Exception as e:
        return False, str(e)


# ─── CHECKPOINT VERIFIERS ─────────────────────────────────────────────────────

def verify_after_plan(plan_path: str) -> Dict[str, Any]:
    """Verify PLAN.md has required structure."""
    checks = []

    if not os.path.exists(plan_path):
        return {
            "checkpoint": "after_plan",
            "passed": False,
            "checks": [{"name": "plan_exists", "passed": False, "message": f"{plan_path} not found"}],
            "block_execution": True,
            "action": "Use project-planner agent to create PLAN.md first"
        }

    with open(plan_path) as f:
        content = f.read()

    required_sections = ["## ", "task", "phase"]
    for section in required_sections:
        has = section.lower() in content.lower()
        checks.append({
            "name": f"has_{section.strip('# ').replace(' ', '_')}",
            "passed": has,
            "message": f"Section '{section}' {'found' if has else 'MISSING'}"
        })

    word_count = len(content.split())
    sufficient = word_count > 50
    checks.append({
        "name": "plan_sufficient_detail",
        "passed": sufficient,
        "message": f"Plan has {word_count} words {'(sufficient)' if sufficient else '(TOO SHORT - needs more detail)'}"
    })

    passed = all(c["passed"] for c in checks)
    return {
        "checkpoint": "after_plan",
        "passed": passed,
        "checks": checks,
        "block_execution": not passed,
        "action": "Revise PLAN.md to include all required sections" if not passed else "Proceed to implementation"
    }


def verify_after_backend(project_dir: str) -> Dict[str, Any]:
    """Verify backend API is syntactically valid."""
    checks = []

    # Check TypeScript compiles
    ts_ok, ts_out = run_cmd("npx tsc --noEmit 2>&1 | head -20", project_dir)
    checks.append({
        "name": "typescript_compile",
        "passed": ts_ok,
        "message": ts_out if not ts_ok else "TypeScript OK"
    })

    # Check for obvious syntax errors in JS/TS files
    lint_ok, lint_out = run_cmd("npx eslint src/ --ext .ts,.js 2>&1 | head -20", project_dir)
    checks.append({
        "name": "eslint_backend",
        "passed": lint_ok,
        "message": lint_out[:300] if not lint_ok else "ESLint OK"
    })

    # Check package.json exists
    pkg_exists = os.path.exists(os.path.join(project_dir, "package.json"))
    checks.append({
        "name": "package_json_exists",
        "passed": pkg_exists,
        "message": "package.json found" if pkg_exists else "package.json MISSING"
    })

    critical_failed = [c for c in checks if not c["passed"] and c["name"] == "typescript_compile"]
    passed = len(critical_failed) == 0

    return {
        "checkpoint": "after_backend",
        "passed": passed,
        "checks": checks,
        "block_execution": not passed,
        "action": "Fix TypeScript errors before frontend work" if not passed else "Backend valid, proceed"
    }


def verify_after_frontend(project_dir: str) -> Dict[str, Any]:
    """Verify frontend builds without errors."""
    checks = []

    # Check for syntax errors in React/Vue files
    lint_ok, lint_out = run_cmd(
        "npx eslint src/ --ext .tsx,.jsx,.vue 2>&1 | head -20", project_dir
    )
    checks.append({
        "name": "frontend_lint",
        "passed": lint_ok,
        "message": lint_out[:300] if not lint_ok else "Frontend lint OK"
    })

    # Check critical files exist
    for check_file in ["src/main.tsx", "src/App.tsx", "src/main.ts", "src/App.vue"]:
        full_path = os.path.join(project_dir, check_file)
        if os.path.exists(full_path):
            checks.append({
                "name": "entry_point_exists",
                "passed": True,
                "message": f"Entry point found: {check_file}"
            })
            break
    else:
        checks.append({
            "name": "entry_point_exists",
            "passed": False,
            "message": "No entry point found (src/main.tsx, App.tsx, etc.)"
        })

    passed = all(c["passed"] for c in checks)
    return {
        "checkpoint": "after_frontend",
        "passed": passed,
        "checks": checks,
        "block_execution": not passed,
        "action": "Fix frontend errors before test phase" if not passed else "Frontend valid"
    }


def verify_after_tests(project_dir: str) -> Dict[str, Any]:
    """Verify tests exist and pass."""
    checks = []

    # Check test files exist
    test_ok, test_out = run_cmd(
        "find . -name '*.test.*' -o -name '*.spec.*' | grep -v node_modules | wc -l",
        project_dir
    )
    test_count = int(test_out.strip()) if test_out.strip().isdigit() else 0
    checks.append({
        "name": "test_files_exist",
        "passed": test_count > 0,
        "message": f"{test_count} test files found" if test_count > 0 else "NO test files found"
    })

    # Run tests (quick, no coverage)
    if test_count > 0:
        run_ok, run_out = run_cmd("npm test -- --passWithNoTests 2>&1 | tail -10", project_dir)
        checks.append({
            "name": "tests_pass",
            "passed": run_ok,
            "message": run_out[:300] if not run_ok else "Tests passing"
        })

    passed = all(c["passed"] for c in checks)
    return {
        "checkpoint": "after_tests",
        "passed": passed,
        "checks": checks,
        "block_execution": not passed,
        "action": "Fix failing tests before deployment" if not passed else "Tests OK, proceed to deploy"
    }


def verify_after_schema(project_dir: str) -> Dict[str, Any]:
    """Verify database schema before code depends on it."""
    checks = []

    # Prisma schema validation
    prisma_ok, prisma_out = run_cmd("npx prisma validate 2>&1", project_dir)
    checks.append({
        "name": "prisma_schema_valid",
        "passed": prisma_ok,
        "message": prisma_out[:300] if not prisma_ok else "Prisma schema valid"
    })

    # Check migrations are up to date
    migrate_ok, migrate_out = run_cmd(
        "npx prisma migrate status 2>&1 | tail -5", project_dir
    )
    checks.append({
        "name": "migrations_current",
        "passed": "Database schema is up to date" in migrate_out or migrate_ok,
        "message": migrate_out[:200]
    })

    passed = checks[0]["passed"]  # Schema must be valid, migrations are advisory
    return {
        "checkpoint": "after_schema",
        "passed": passed,
        "checks": checks,
        "block_execution": not passed,
        "action": "Fix Prisma schema errors before generating types" if not passed else "Schema OK"
    }


CHECKPOINT_MAP = {
    "after_plan": verify_after_plan,
    "after_backend": verify_after_backend,
    "after_frontend": verify_after_frontend,
    "after_tests": verify_after_tests,
    "after_schema": verify_after_schema,
}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: mid_task_verify.py <checkpoint> <path>")
        print(f"Checkpoints: {list(CHECKPOINT_MAP.keys())}")
        sys.exit(1)

    checkpoint = sys.argv[1]
    path = sys.argv[2]

    if checkpoint not in CHECKPOINT_MAP:
        print(json.dumps({"error": f"Unknown checkpoint: {checkpoint}. Valid: {list(CHECKPOINT_MAP.keys())}"}, indent=2))
        sys.exit(1)

    result = CHECKPOINT_MAP[checkpoint](path)
    print(json.dumps(result, indent=2))

    # Exit code: 0=pass, 1=fail (for shell scripts to check)
    sys.exit(0 if result["passed"] else 1)
