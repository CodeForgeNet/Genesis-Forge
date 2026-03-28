#!/usr/bin/env python3
"""
route_task.py v2 - Deterministic Task Router (800+ Skills Edition)
===================================================================
Version 2 integrates with skill_registry.json built by build_skill_registry.py.
Falls back to hardcoded routing table if registry not built yet.

Usage:
  python3 agent/scripts/route_task.py "fix the login api bug"
  python3 agent/scripts/route_task.py "build a react dashboard" --tier low
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict

# Add current directory to path for local imports
sys.path.append(str(Path(__file__).resolve().parent))
import utils
from utils import AGENT_ROOT, SCRIPTS_DIR, SKILLS_DIR

REGISTRY_PATH = SCRIPTS_DIR / "skill_registry.json"
SEARCH_INDEX_PATH = SCRIPTS_DIR / "skill_search_index.json"


@dataclass
class RouteResult:
    agents: List[str]
    skills: List[str]
    skill_paths: List[str]
    workflow: str
    complexity: str
    parallel_groups: List[List[str]]
    requires_plan: bool
    estimated_steps: int
    rationale: str
    model_tier: str = "mid"
    load_instructions: List[str] = field(default_factory=list)


ROUTING_TABLE = [
    {
        "keywords": ["pentest", "penetration", "exploit", "red team"],
        "agents": ["penetration-tester", "security-auditor"],
        "skills": ["red-team-tactics", "vulnerability-scanner"],
        "workflow": "orchestrate"
    },
    {
        "keywords": ["security", "vulnerability", "owasp", "auth", "authentication",
                     "authorization", "jwt", "oauth", "csrf", "xss", "injection"],
        "agents": ["security-auditor"],
        "skills": ["vulnerability-scanner"],
        "workflow": "orchestrate"
    },
    {
        "keywords": ["bug", "error", "crash", "fix", "broken", "not working",
                     "exception", "debug", "issue"],
        "agents": ["debugger", "explorer-agent"],
        "skills": ["systematic-debugging"],
        "workflow": "debug"
    },
    {
        "keywords": ["test", "spec", "coverage", "unit test", "e2e", "playwright",
                     "jest", "vitest", "tdd", "mock"],
        "agents": ["test-engineer"],
        "skills": ["testing-patterns", "webapp-testing"],
        "workflow": "test"
    },
    {
        "keywords": ["ui", "component", "react", "nextjs", "vue", "svelte",
                     "tailwind", "css", "html", "frontend"],
        "agents": ["frontend-specialist"],
        "skills": ["react-best-practices", "frontend-design"],
        "workflow": "create"
    },
    {
        "keywords": ["api", "endpoint", "route", "rest", "graphql", "server",
                     "backend", "express", "fastapi", "nestjs"],
        "agents": ["backend-specialist"],
        "skills": ["api-patterns", "nodejs-best-practices"],
        "workflow": "create"
    },
    {
        "keywords": ["database", "schema", "migration", "prisma", "sql",
                     "postgres", "mysql", "mongodb"],
        "agents": ["database-architect"],
        "skills": ["database-design", "prisma-expert"],
        "workflow": "create"
    },
    {
        "keywords": ["mobile", "ios", "android", "react native", "flutter", "expo"],
        "agents": ["mobile-developer"],
        "skills": ["mobile-design"],
        "workflow": "create"
    },
    {
        "keywords": ["deploy", "docker", "ci/cd", "pipeline", "kubernetes", "nginx"],
        "agents": ["devops-engineer"],
        "skills": ["deployment-procedures", "docker-expert"],
        "workflow": "deploy"
    },
    {
        "keywords": ["performance", "slow", "optimize", "lighthouse", "web vitals"],
        "agents": ["performance-optimizer"],
        "skills": ["performance-profiling"],
        "workflow": "enhance"
    },
    {
        "keywords": ["seo", "search engine", "meta tag", "ranking"],
        "agents": ["seo-specialist"],
        "skills": ["seo-fundamentals"],
        "workflow": "enhance"
    },
    {
        "keywords": ["game", "unity", "godot", "phaser"],
        "agents": ["game-developer"],
        "skills": ["game-development"],
        "workflow": "create"
    },
    {
        "keywords": ["plan", "roadmap", "brainstorm", "architecture"],
        "agents": ["project-planner"],
        "skills": ["plan-writing", "brainstorming"],
        "workflow": "write-plan"
    },
    {
        "keywords": ["review", "audit", "quality", "refactor"],
        "agents": ["code-reviewer"],
        "skills": ["code-review-checklist", "clean-code"],
        "workflow": "enhance"
    },
    {
        "keywords": ["full stack", "fullstack", "saas", "mvp", "entire app"],
        "agents": ["project-planner", "frontend-specialist", "backend-specialist",
                   "database-architect", "test-engineer", "devops-engineer"],
        "skills": ["architecture", "react-best-practices", "api-patterns",
                   "database-design", "testing-patterns"],
        "workflow": "orchestrate"
    },
]

PARALLEL_MAP = {
    frozenset(["frontend-specialist", "backend-specialist"]): [
        ["frontend-specialist", "backend-specialist"], ["test-engineer"]
    ],
    frozenset(["security-auditor", "penetration-tester"]): [
        ["security-auditor", "penetration-tester"]
    ],
}

MODEL_LIMITS = {
    "low":  {"max_skills": 1, "content_mode": "tldr_only"},
    "mid":  {"max_skills": 2, "content_mode": "summary"},
    "high": {"max_skills": 4, "content_mode": "full"},
}

DOMAIN_AGENT_MAP = {
    "frontend": ["frontend-specialist"],
    "backend":  ["backend-specialist"],
    "database": ["database-architect"],
    "testing":  ["test-engineer"],
    "security": ["security-auditor"],
    "devops":   ["devops-engineer"],
    "mobile":   ["mobile-developer"],
    "game":     ["game-developer"],
    "seo":      ["seo-specialist"],
    "ai_ml":    ["implementer-agent"],
    "azure":    ["devops-engineer"],
    "aws":      ["devops-engineer"],
    "shell":    ["implementer-agent"],
    "general":  ["implementer-agent"],
}


def load_registry():
    if REGISTRY_PATH.exists():
        try:
            with open(REGISTRY_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[route_task] Warning: registry load failed — {e}", file=sys.stderr)
    return None


def load_search_index():
    if SEARCH_INDEX_PATH.exists():
        try:
            with open(SEARCH_INDEX_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[route_task] Warning: search index load failed — {e}", file=sys.stderr)
    return None


def build_load_instruction(skill: Dict, content_mode: str) -> str:
    skill_path = Path(skill["path"])
    # Make path relative to AGENT_ROOT if it's absolute and inside the kit
    try:
        rel = skill_path.relative_to(AGENT_ROOT)
        display_path = str(rel)
    except ValueError:
        display_path = str(skill_path)

    if content_mode == "tldr_only":
        if skill.get("has_tldr"):
            return f"READ first 500 chars of {display_path} (TL;DR section only)"
        return f"READ first 300 chars of {display_path}"
    elif content_mode == "summary":
        return f"READ first 1000 chars of {display_path}"
    return f"READ {display_path} (full content)"


def route_with_registry(task: str, registry: Dict, search_index: Dict, tier: str) -> Optional[RouteResult]:
    task_lower = task.lower()
    tokens = set(re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#]{2,}\b', task_lower))
    scores = defaultdict(float)

    for token in tokens:
        if token in search_index:
            for sn in search_index[token]:
                scores[sn] += 1.0
        for kw in search_index:
            if token in kw:
                for sn in search_index[kw]:
                    scores[sn] += 0.3

    for canonical in registry.get("priority_map", {}).values():
        if canonical in scores:
            scores[canonical] += 2.0

    if not scores:
        return None

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    skill_lookup = {s["name"]: s for s in registry["skills"]}
    limits = MODEL_LIMITS[tier]
    top_skills = []

    for sn, score in ranked:
        if sn in skill_lookup and score > 0.5:
            top_skills.append(skill_lookup[sn])
        if len(top_skills) >= limits["max_skills"]:
            break

    if not top_skills:
        return None

    agents = []
    for skill in top_skills:
        for agent in DOMAIN_AGENT_MAP.get(skill.get("domain", "general"), ["implementer-agent"]):
            if agent not in agents:
                agents.append(agent)

    skills = [s["name"] for s in top_skills]
    skill_paths = [s["path"] for s in top_skills]
    load_instructions = [build_load_instruction(s, limits["content_mode"]) for s in top_skills]

    complexity = "complex" if len(agents) >= 4 else "medium" if len(agents) >= 2 else "simple"
    parallel_groups = [[a] for a in agents]
    for key, groups in PARALLEL_MAP.items():
        if key.issubset(set(agents)):
            parallel_groups = groups
            break

    return RouteResult(
        agents=agents, skills=skills, skill_paths=skill_paths,
        workflow="orchestrate" if complexity == "complex" else "create",
        complexity=complexity, parallel_groups=parallel_groups,
        requires_plan=complexity in ("medium", "complex"),
        estimated_steps=len(agents),
        rationale=f"Registry match ({len(registry['skills'])} skills indexed). Top: {skills[0]}. Tier: {tier}",
        model_tier=tier, load_instructions=load_instructions,
    )


def route_fallback(task: str, tier: str) -> RouteResult:
    task_lower = task.lower()
    scored = sorted(
        [(sum(1 for kw in r["keywords"] if kw in task_lower), r)
         for r in ROUTING_TABLE if any(kw in task_lower for kw in r["keywords"])],
        reverse=True
    )

    limits = MODEL_LIMITS[tier]
    fallback_skill_path = str(SKILLS_DIR / "clean-code" / "SKILL.md")

    if not scored:
        return RouteResult(
            agents=["implementer-agent"], skills=["clean-code"],
            skill_paths=[fallback_skill_path], workflow="create",
            complexity="simple", parallel_groups=[["implementer-agent"]],
            requires_plan=False, estimated_steps=1,
            rationale="No match. Fallback. Run build_skill_registry.py for full coverage.",
            model_tier=tier, load_instructions=[f"READ {fallback_skill_path}"],
        )

    agents, skills = [], []
    for _, rule in scored:
        for a in rule["agents"]:
            if a not in agents: agents.append(a)
        for s in rule["skills"]:
            if s not in skills: skills.append(s)

    skills = skills[:limits["max_skills"]]
    skill_paths = [str(SKILLS_DIR / s / "SKILL.md") for s in skills]
    load_instructions = [f"READ {p}" for p in skill_paths]
    complexity = "complex" if len(agents) >= 4 else "medium" if len(agents) >= 2 else "simple"

    return RouteResult(
        agents=agents, skills=skills, skill_paths=skill_paths,
        workflow=scored[0][1]["workflow"], complexity=complexity,
        parallel_groups=[[a] for a in agents],
        requires_plan=complexity in ("medium", "complex"),
        estimated_steps=len(agents),
        rationale="Hardcoded fallback. Run build_skill_registry.py for 800+ skill coverage.",
        model_tier=tier, load_instructions=load_instructions,
    )


def route(task: str, tier: str = "mid") -> RouteResult:
    registry = load_registry()
    search_index = load_search_index()
    if registry and search_index:
        result = route_with_registry(task, registry, search_index, tier)
        if result:
            return result
    return route_fallback(task, tier)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: route_task.py '<task>' [--tier low|mid|high]"}, indent=2))
        sys.exit(1)

    tier = "mid"
    args = list(sys.argv[1:])
    if "--tier" in args:
        idx = args.index("--tier")
        if idx + 1 < len(args):
            tier = args[idx + 1]
            args.pop(idx + 1)
        args.pop(idx)

    task = " ".join(args)
    result = route(task, tier)
    print(json.dumps(asdict(result), indent=2))
