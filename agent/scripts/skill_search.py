#!/usr/bin/env python3
"""
skill_search.py - Fast Runtime Skill Lookup
============================================
Replaces model-driven using-capabilities for 90 skills.
Uses pre-built registry from build_skill_registry.py.

At runtime, this is what gets called INSTEAD of the model
reasoning about which skills to invoke.

Usage:
  python agent/scripts/skill_search.py "build a react dashboard"
  python agent/scripts/skill_search.py --domain frontend
  python agent/scripts/skill_search.py --name "react-best-practices"
  python agent/scripts/skill_search.py --list-domains
  python agent/scripts/skill_search.py --tldr "systematic-debugging"

Output: JSON with ranked skill list + load instructions
"""

import sys
import json
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Add current directory to path for local imports
sys.path.append(str(Path(__file__).resolve().parent))
import utils
from utils import AGENT_ROOT, SCRIPTS_DIR, SKILLS_DIR

REGISTRY_PATH = SCRIPTS_DIR / "skill_registry.json"
SEARCH_INDEX_PATH = SCRIPTS_DIR / "skill_search_index.json"


# ─── MODEL TIER LIMITS ────────────────────────────────────────────────────────
# Controls how many skills can be loaded and how much content per skill.

MODEL_LIMITS = {
    "low": {
        "max_skills": 1,
        "content_mode": "tldr_only",    # Read only TL;DR section
        "max_chars_per_skill": 500,
    },
    "mid": {
        "max_skills": 2,
        "content_mode": "summary",      # Read first 1000 chars of SKILL.md
        "max_chars_per_skill": 1000,
    },
    "high": {
        "max_skills": 4,
        "content_mode": "full",         # Read complete SKILL.md
        "max_chars_per_skill": -1,      # No limit
    }
}


def load_registry() -> Optional[Dict]:
    if not os.path.exists(REGISTRY_PATH):
        return None
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def load_search_index() -> Optional[Dict]:
    if not os.path.exists(SEARCH_INDEX_PATH):
        return None
    with open(SEARCH_INDEX_PATH) as f:
        return json.load(f)


def search_by_query(
    query: str,
    registry: Dict,
    search_index: Dict,
    model_tier: str = "mid",
    max_results: int = 3
) -> List[Dict]:
    """
    Find most relevant skills for a task query.
    Returns ranked list of skill entries.
    """
    query_lower = query.lower()

    # 1. Extract query tokens
    tokens = set(re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#]{2,}\b', query_lower))

    # 2. Score each skill by keyword overlap
    scores: Dict[str, int] = defaultdict(int)

    for token in tokens:
        if token in search_index:
            for skill_name in search_index[token]:
                scores[skill_name] += 1
        # Partial match (e.g. "react" matches "react-best-practices")
        for indexed_kw in search_index:
            if token in indexed_kw or indexed_kw in token:
                for skill_name in search_index[indexed_kw]:
                    scores[skill_name] += 0.5

    # 3. Boost canonical/official skills from priority map
    priority_map = registry.get("priority_map", {})
    canonical_skills = set(priority_map.values())
    for skill_name in canonical_skills:
        if skill_name in scores:
            scores[skill_name] += 2  # Boost canonical

    # 4. Sort by score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # 5. Map back to full skill entries
    skill_lookup = {s["name"]: s for s in registry["skills"]}
    limits = MODEL_LIMITS[model_tier]
    results = []

    for skill_name, score in ranked[:max_results * 2]:
        if skill_name not in skill_lookup:
            continue
        skill = skill_lookup[skill_name]
        result = {
            "name": skill["name"],
            "path": skill["path"],
            "description": skill["description"],
            "domain": skill["domain"],
            "score": round(score, 1),
            "line_count": skill["line_count"],
            "has_tldr": skill["has_tldr"],
            "load_instruction": build_load_instruction(skill, limits),
        }
        results.append(result)
        if len(results) >= limits["max_skills"]:
            break

    return results


def build_load_instruction(skill: Dict, limits: Dict) -> str:
    """Build the exact instruction for loading this skill."""
    path = skill["path"]
    mode = limits["content_mode"]
    max_chars = limits["max_chars_per_skill"]

    if mode == "tldr_only":
        if skill["has_tldr"]:
            return f"READ first 500 chars of {path} (TL;DR section only)"
        else:
            return f"READ first 300 chars of {path} (no TL;DR, use opening summary)"

    elif mode == "summary":
        return f"READ first 1000 chars of {path}"

    else:  # full
        return f"READ {path} (full content)"


def get_skill_by_name(name: str, registry: Dict) -> Optional[Dict]:
    """Find a skill by exact or partial name."""
    skill_lookup = {s["name"]: s for s in registry["skills"]}
    if name in skill_lookup:
        return skill_lookup[name]
    # Partial match
    matches = [s for s in registry["skills"] if name in s["name"]]
    return matches[0] if matches else None


def get_tldr(skill_name: str) -> str:
    """Read just the TL;DR section from a skill file."""
    skill_path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
    if not os.path.exists(skill_path):
        return f"Skill file not found: {skill_path}"

    content = Path(skill_path).read_text(encoding="utf-8", errors="ignore")

    # Try to find TL;DR section
    match = re.search(r"##\s+TL;DR.*?\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # No TL;DR - return description + first 300 chars
    lines = content.splitlines()
    # Skip frontmatter
    start = 0
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            start = content.count("\n", 0, end) + 2

    relevant = "\n".join(lines[start:start+10]).strip()
    return f"[No TL;DR found]\n{relevant[:400]}"


def list_domains(registry: Dict) -> List[Dict]:
    """List all domains with skill counts and canonical skill."""
    from collections import Counter
    domain_counts = Counter(s["domain"] for s in registry["skills"])
    priority_map = registry.get("priority_map", {})

    return [
        {
            "domain": domain,
            "skill_count": count,
            "canonical_skill": priority_map.get(domain, "none"),
        }
        for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
    ]


def build_using_capabilities_replacement(query: str, registry: Dict, search_index: Dict, model_tier: str) -> Dict:
    """
    Complete replacement for using-capabilities skill.
    Returns everything needed to load and use the right skills.
    No model reasoning required.
    """
    skills = search_by_query(query, registry, search_index, model_tier)

    return {
        "query": query,
        "model_tier": model_tier,
        "skill_count": len(skills),
        "skills": skills,
        "instructions": [
            f"STEP 1: {s['load_instruction']}"
            for s in skills
        ],
        "rule": "Execute skills in order. Do not invoke more skills than listed above. Do not reason about which skills to use -- this output IS the skill selection."
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  skill_search.py '<query>' [--tier low|mid|high]")
        print("  skill_search.py --domain <domain>")
        print("  skill_search.py --name <skill-name>")
        print("  skill_search.py --list-domains")
        print("  skill_search.py --tldr <skill-name>")
        sys.exit(1)

    # Parse tier flag
    tier = "mid"
    if "--tier" in sys.argv:
        idx = sys.argv.index("--tier")
        tier = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "mid"
        sys.argv = [a for a in sys.argv if a not in ("--tier", tier)]

    registry = load_registry()
    search_index = load_search_index()

    if registry is None:
        print(json.dumps({
            "error": "skill_registry.json not found.",
            "fix": "Run: python agent/scripts/build_skill_registry.py"
        }, indent=2))
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "--list-domains":
        print(json.dumps(list_domains(registry), indent=2))

    elif cmd == "--name":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        skill = get_skill_by_name(name, registry)
        if skill:
            print(json.dumps(skill, indent=2))
        else:
            print(json.dumps({"error": f"Skill not found: {name}"}, indent=2))

    elif cmd == "--domain":
        domain = sys.argv[2] if len(sys.argv) > 2 else ""
        skills = [s for s in registry["skills"] if s["domain"] == domain]
        print(json.dumps(skills, indent=2))

    elif cmd == "--tldr":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        print(get_tldr(name))

    else:
        # Default: search by query
        query = " ".join(sys.argv[1:])
        if search_index is None:
            # Fallback without search index
            result = {"error": "search index not built", "fix": "Run build_skill_registry.py"}
        else:
            result = build_using_capabilities_replacement(query, registry, search_index, tier)
        print(json.dumps(result, indent=2))
