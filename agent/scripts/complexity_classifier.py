#!/usr/bin/env python3
"""
complexity_classifier.py - Task Complexity Gate
================================================
Prevents simple tasks from going through full 3-agent orchestration.
Outputs one of: SIMPLE | MEDIUM | COMPLEX with execution path.

SIMPLE  → Direct agent, no PLAN.md, no orchestration overhead
MEDIUM  → 2-3 agents, lightweight plan, no full orchestration
COMPLEX → Full orchestration, PLAN.md required, swarm mode eligible

Usage:
  python agent/scripts/complexity_classifier.py "fix typo in readme"
  python agent/scripts/complexity_classifier.py "build full saas app"
"""

import sys
import json
from typing import Dict, Any


# ─── SIGNAL WEIGHTS ───────────────────────────────────────────────────────────

COMPLEXITY_SIGNALS = {
    "simple": {
        "keywords": [
            "fix typo", "rename", "update text", "change color", "add comment",
            "format", "lint", "single file", "one file", "quick", "small",
            "minor", "simple", "just", "only", "add a button", "fix spacing",
            "update import", "change variable", "add log", "print"
        ],
        "weight": -2   # reduces complexity score
    },
    "medium": {
        "keywords": [
            "add feature", "create component", "write test", "add endpoint",
            "implement", "build", "integrate", "connect", "setup", "configure",
            "refactor", "optimize", "improve", "add page", "create api"
        ],
        "weight": 1
    },
    "complex": {
        "keywords": [
            "entire", "full app", "full stack", "complete", "whole", "all",
            "saas", "mvp", "production", "deploy", "migrate", "rebuild",
            "rewrite", "architecture", "system", "platform", "multi",
            "orchestrate", "parallel", "swarm", "automated", "pipeline",
            "end to end", "e2e", "from scratch", "greenfield"
        ],
        "weight": 3
    }
}

DOMAIN_WEIGHTS = {
    # Each unique domain touched adds weight
    "frontend": 1,
    "backend": 1,
    "database": 1,
    "testing": 1,
    "devops": 1,
    "security": 1,
    "mobile": 1,
}

DOMAIN_KEYWORDS = {
    "frontend":  ["react", "vue", "svelte", "nextjs", "next.js", "nuxt", "css",
                  "tailwind", "html", "component", "ui", "frontend"],
    "backend":   ["api", "server", "express", "fastapi", "nestjs", "node",
                  "endpoint", "route", "middleware", "backend"],
    "database":  ["database", "schema", "sql", "prisma", "migration", "query",
                  "postgres", "mysql", "mongo", "orm"],
    "testing":   ["test", "spec", "coverage", "jest", "vitest", "playwright",
                  "e2e", "unit", "mock"],
    "devops":    ["docker", "deploy", "ci/cd", "pipeline", "kubernetes", "nginx",
                  "pm2", "cloud", "aws", "vercel"],
    "security":  ["auth", "security", "vulnerability", "owasp", "jwt", "oauth",
                  "pentest"],
    "mobile":    ["mobile", "ios", "android", "react native", "flutter", "expo"],
}


def score_task(task: str) -> Dict[str, Any]:
    task_lower = task.lower()
    score = 0
    matched_signals = []
    touched_domains = []

    # Score complexity signals
    for level, config in COMPLEXITY_SIGNALS.items():
        for kw in config["keywords"]:
            if kw in task_lower:
                score += config["weight"]
                matched_signals.append(f"{level}:{kw}")

    # Score domain coverage
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in task_lower for kw in keywords):
            score += DOMAIN_WEIGHTS[domain]
            touched_domains.append(domain)

    # Word count heuristic
    word_count = len(task.split())
    if word_count > 30:
        score += 2
    elif word_count < 8:
        score -= 1

    return {
        "score": score,
        "matched_signals": matched_signals[:5],
        "touched_domains": touched_domains
    }


def classify(task: str) -> Dict[str, Any]:
    result = score_task(task)
    score = result["score"]
    domains = result["touched_domains"]
    domain_count = len(domains)

    if score <= 0 or (score == 1 and domain_count <= 1):
        complexity = "SIMPLE"
        execution_path = "direct_agent"
        requires_plan = False
        min_agents = 1
        max_agents = 1
        use_orchestration = False
        description = "Execute with single direct agent. No PLAN.md. No orchestration overhead."

    elif score <= 3 or domain_count <= 2:
        complexity = "MEDIUM"
        execution_path = "lightweight_multi_agent"
        requires_plan = domain_count >= 2
        min_agents = 2
        max_agents = 3
        use_orchestration = False
        description = "2-3 agents, sequential. Lightweight plan if multi-domain. Skip full orchestration."

    else:
        complexity = "COMPLEX"
        execution_path = "full_orchestration"
        requires_plan = True
        min_agents = 3
        max_agents = len(domains) + 2
        use_orchestration = True
        description = "Full orchestration. PLAN.md required. Parallel agents eligible. Swarm mode available."

    return {
        "complexity": complexity,
        "execution_path": execution_path,
        "requires_plan": requires_plan,
        "min_agents": min_agents,
        "max_agents": max_agents,
        "use_orchestration": use_orchestration,
        "touched_domains": domains,
        "domain_count": domain_count,
        "score": score,
        "matched_signals": result["matched_signals"],
        "description": description
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: complexity_classifier.py '<task>'"}, indent=2))
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    output = classify(task)
    output["task"] = task
    print(json.dumps(output, indent=2))
