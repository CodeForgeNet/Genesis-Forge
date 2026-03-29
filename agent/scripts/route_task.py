#!/usr/bin/env python3
"""
route_task.py v3 - Deterministic Task Router (90 Skills Edition)
===============================================================
Version 3 uses dynamic routing rules from routing_rules.json.
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
RULES_PATH = SCRIPTS_DIR / "routing_rules.json"

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

MODEL_LIMITS = {
    "low":  {"max_skills": 1, "content_mode": "tldr_only"},
    "mid":  {"max_skills": 2, "content_mode": "summary"},
    "high": {"max_skills": 4, "content_mode": "full"},
}

def load_json(path: Path) -> Optional[Dict]:
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[route_task] Warning: {path.name} load failed — {e}", file=sys.stderr)
    return None

def build_load_instruction(skill: Dict, content_mode: str) -> str:
    skill_path = Path(skill["path"])
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

def route_with_registry(task: str, registry: Dict, search_index: Dict, rules: Dict, tier: str) -> Optional[RouteResult]:
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
    top_skills = [skill_lookup[sn] for sn, score in ranked if sn in skill_lookup and score > 0.5]
    top_skills = top_skills[:limits["max_skills"]]

    if not top_skills:
        return None

    agents = []
    domain_map = rules.get("domain_agent_map", {})
    for skill in top_skills:
        for agent in domain_map.get(skill.get("domain", "general"), ["implementer-agent"]):
            if agent not in agents:
                agents.append(agent)

    complexity = "complex" if len(agents) >= 4 else "medium" if len(agents) >= 2 else "simple"
    
    # Calculate parallel groups
    parallel_groups = [[a] for a in agents]
    for p_map in rules.get("parallel_map", []):
        if set(p_map["agents"]).issubset(set(agents)):
            parallel_groups = p_map["groups"]
            break

    return RouteResult(
        agents=agents, skills=[s["name"] for s in top_skills], 
        skill_paths=[s["path"] for s in top_skills],
        workflow="orchestrate" if complexity == "complex" else "create",
        complexity=complexity, parallel_groups=parallel_groups,
        requires_plan=complexity in ("medium", "complex"),
        estimated_steps=len(agents),
        rationale=f"Registry match (90 skills indexed). Top: {top_skills[0]['name']}. Tier: {tier}",
        model_tier=tier, load_instructions=[build_load_instruction(s, limits["content_mode"]) for s in top_skills],
    )

def route_fallback(task: str, rules: Dict, tier: str) -> RouteResult:
    task_lower = task.lower()
    routing_table = rules.get("routing_rules", [])
    
    scored = sorted(
        [(sum(1 for kw in r["keywords"] if kw in task_lower), r)
         for r in routing_table if any(kw in task_lower for kw in r["keywords"])],
        key=lambda x: x[0], reverse=True
    )

    limits = MODEL_LIMITS[tier]
    fallback_skill_path = str(SKILLS_DIR / "clean-code" / "SKILL.md")

    if not scored:
        return RouteResult(
            agents=["implementer-agent"], skills=["clean-code"],
            skill_paths=[fallback_skill_path], workflow="create",
            complexity="simple", parallel_groups=[["implementer-agent"]],
            requires_plan=False, estimated_steps=1,
            rationale="No match. Fallback to clean-code defaults.",
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
    complexity = "complex" if len(agents) >= 4 else "medium" if len(agents) >= 2 else "simple"

    return RouteResult(
        agents=agents, skills=skills, skill_paths=skill_paths,
        workflow=scored[0][1]["workflow"], complexity=complexity,
        parallel_groups=[[a] for a in agents],
        requires_plan=complexity in ("medium", "complex"),
        estimated_steps=len(agents),
        rationale="Dynamic JSON rule match. Fallback from registry.",
        model_tier=tier, load_instructions=[f"READ {p}" for p in skill_paths],
    )

def route(task: str, tier: str = "mid") -> RouteResult:
    registry = load_json(REGISTRY_PATH)
    search_index = load_json(SEARCH_INDEX_PATH)
    rules = load_json(RULES_PATH) or {"routing_rules": [], "domain_agent_map": {}, "parallel_map": []}
    
    if registry and search_index:
        result = route_with_registry(task, registry, search_index, rules, tier)
        if result:
            return result
    return route_fallback(task, rules, tier)

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
