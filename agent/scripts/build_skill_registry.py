#!/usr/bin/env python3
"""
build_skill_registry.py - Index All 800+ Skills
================================================
Run this ONCE against your agent/skills/ directory.
It reads every SKILL.md, extracts metadata, and builds:
  1. skill_registry.json  - Full index of all skills
  2. skill_search_index.json - Fast keyword lookup table
  3. skill_duplicates.json - Skills covering same domain (dedup needed)

Run from your project root:
  python agent/scripts/build_skill_registry.py

Then use skill_search.py for fast lookups at runtime.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


def _resolve_agent_root() -> Path:
    """Resolve the agent kit root directory."""
    env_root = os.environ.get("AGENT_ROOT")
    if env_root:
        return Path(env_root)
    # This script lives at <root>/agent/scripts/build_skill_registry.py
    return Path(__file__).resolve().parent.parent.parent


AGENT_ROOT = _resolve_agent_root()
SCRIPTS_DIR = AGENT_ROOT / "agent" / "scripts"
SKILLS_DIR = AGENT_ROOT / "agent" / "skills"

OUTPUT_REGISTRY = SCRIPTS_DIR / "skill_registry.json"
OUTPUT_SEARCH = SCRIPTS_DIR / "skill_search_index.json"
OUTPUT_DUPLICATES = SCRIPTS_DIR / "skill_duplicates.json"


def extract_frontmatter(content: str) -> Dict[str, str]:
    """Extract YAML frontmatter from SKILL.md."""
    fm = {}
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            block = content[3:end]
            for line in block.strip().splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def extract_tldr(content: str) -> Optional[str]:
    """Extract TL;DR section if it exists."""
    match = re.search(r"##\s+TL;DR.*?\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()[:500]
    return None


def extract_description(content: str, fm: Dict) -> str:
    """Best-effort description extraction."""
    # 1. From frontmatter
    if fm.get("description"):
        return fm["description"][:200]

    # 2. From first paragraph after frontmatter
    clean = re.sub(r"^---.*?---\s*", "", content, flags=re.DOTALL)
    lines = [l.strip() for l in clean.splitlines() if l.strip() and not l.startswith("#")]
    if lines:
        return lines[0][:200]

    return ""


def extract_keywords(skill_name: str, description: str, content: str) -> List[str]:
    """Extract keywords from skill name + description for search index."""
    keywords = set()

    # From skill name (split by hyphens)
    parts = skill_name.replace("_", "-").split("-")
    keywords.update(p.lower() for p in parts if len(p) > 2)

    # From description
    desc_words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#]{2,}\b', description.lower())
    keywords.update(desc_words[:20])

    # Tech names and frameworks from content (first 500 chars)
    tech_pattern = r'\b(react|vue|angular|svelte|nextjs|next\.js|nuxt|tailwind|typescript|python|fastapi|django|flask|node|express|nestjs|prisma|postgres|mysql|mongodb|redis|docker|kubernetes|aws|azure|gcp|terraform|stripe|shopify|wordpress|flutter|swift|kotlin|rust|golang|java|spring|laravel|rails|graphql|trpc|langchain|openai|anthropic|langfuse|supabase|firebase|vercel|cloudflare|nginx|github|gitlab|jira|slack|notion|linear)\b'
    tech_matches = re.findall(tech_pattern, content[:500].lower())
    keywords.update(tech_matches)

    # Remove stop words
    stop = {"the", "and", "for", "with", "how", "use", "using", "best", "this", "that", "from", "into"}
    keywords -= stop

    return sorted(keywords)


def detect_domain(skill_name: str, description: str) -> str:
    """Assign primary domain to a skill for dedup detection."""
    name_lower = skill_name.lower()
    desc_lower = description.lower()
    combined = name_lower + " " + desc_lower

    domain_patterns = {
        "azure": ["azure"],
        "aws": ["aws", "amazon"],
        "frontend": ["react", "vue", "angular", "svelte", "nextjs", "frontend", "ui", "css", "tailwind", "html"],
        "backend": ["api", "server", "node", "express", "fastapi", "django", "flask", "nestjs", "backend"],
        "database": ["database", "sql", "postgres", "mysql", "mongodb", "redis", "prisma", "drizzle"],
        "testing": ["test", "spec", "jest", "vitest", "playwright", "tdd", "qa"],
        "security": ["security", "pentest", "vulnerability", "owasp", "hack", "exploit", "auth"],
        "devops": ["docker", "kubernetes", "ci/cd", "deploy", "terraform", "helm", "devops"],
        "mobile": ["mobile", "ios", "android", "flutter", "swift", "kotlin", "react native"],
        "ai_ml": ["ai", "ml", "llm", "langchain", "rag", "agent", "openai", "anthropic"],
        "automation": ["automation", "zapier", "make", "n8n", "workflow"],
        "game": ["game", "unity", "godot", "unreal", "phaser"],
        "seo": ["seo", "search engine", "ranking"],
        "agent_orchestration": ["agent", "orchestr", "swarm", "multi-agent"],
        "typescript": ["typescript", "ts"],
        "python": ["python", "py"],
        "rust": ["rust"],
        "golang": ["golang", "go-"],
        "java": ["java"],
        "csharp": ["csharp", "dotnet", "c#"],
        "shell": ["bash", "shell", "linux", "powershell"],
        "monitoring": ["monitoring", "observability", "grafana", "prometheus", "datadog"],
        "general": []
    }

    for domain, patterns in domain_patterns.items():
        if domain == "general":
            continue
        if any(p in combined for p in patterns):
            return domain

    return "general"


def scan_skills(skills_dir: Path) -> List[Dict[str, Any]]:
    """Scan all SKILL.md files and extract metadata."""
    skills = []

    if not skills_dir.exists():
        print(f"ERROR: {skills_dir} not found. Run from project root.")
        sys.exit(1)

    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        try:
            content = skill_md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Skill name from directory
        rel_path = skill_md.parent.relative_to(skills_dir)
        skill_name = str(rel_path).replace(os.sep, "/")

        fm = extract_frontmatter(content)
        description = extract_description(content, fm)
        keywords = extract_keywords(skill_name, description, content)
        domain = detect_domain(skill_name, description)
        tldr = extract_tldr(content)
        line_count = content.count("\n")

        skill_entry = {
            "name": skill_name,
            "path": str(skill_md.relative_to(AGENT_ROOT)),
            "description": description,
            "domain": domain,
            "keywords": keywords,
            "line_count": line_count,
            "has_tldr": tldr is not None,
            "tldr": tldr,
            "source": fm.get("source", "unknown"),
            "risk": fm.get("risk", "unknown"),
            "date_added": fm.get("date_added", ""),
            "frontmatter_name": fm.get("name", ""),
        }
        skills.append(skill_entry)

    return skills


def build_search_index(skills: List[Dict]) -> Dict[str, List[str]]:
    """Build inverted keyword index: keyword -> [skill_names]"""
    index = defaultdict(list)
    for skill in skills:
        for kw in skill["keywords"]:
            index[kw].append(skill["name"])
    # Sort for determinism
    return {k: sorted(v) for k, v in sorted(index.items())}


def find_duplicates(skills: List[Dict]) -> Dict[str, List[Dict]]:
    """Find skills covering the same domain -- dedup candidates."""
    by_domain = defaultdict(list)
    for skill in skills:
        by_domain[skill["domain"]].append({
            "name": skill["name"],
            "line_count": skill["line_count"],
            "description": skill["description"][:100]
        })

    # Only report domains with 3+ skills (real duplication problem)
    return {
        domain: sorted(entries, key=lambda x: x["line_count"], reverse=True)
        for domain, entries in by_domain.items()
        if len(entries) >= 3
    }


def build_priority_map(skills: List[Dict]) -> Dict[str, str]:
    """
    For each domain with duplicates, pick ONE canonical skill.
    Priority logic:
    1. Skills from agent/skills/ root (not subdirectory) are official
    2. Longer line_count = more complete
    3. skills matching agent/agents/*.md agent list are preferred
    """
    OFFICIAL_AGENT_SKILLS = {
        "frontend": "react-best-practices",
        "backend": "api-patterns",
        "database": "database-design",
        "testing": "testing-patterns",
        "security": "vulnerability-scanner",
        "devops": "deployment-procedures",
        "mobile": "mobile-design",
        "game": "game-development",
        "seo": "seo-fundamentals",
        "agent_orchestration": "parallel-agents",
        "shell": "bash-linux",
        "general": "clean-code",
    }

    # Build domain -> best skill map
    by_domain = defaultdict(list)
    for skill in skills:
        by_domain[skill["domain"]].append(skill)

    priority_map = {}
    for domain, domain_skills in by_domain.items():
        official = OFFICIAL_AGENT_SKILLS.get(domain)
        if official:
            match = next((s for s in domain_skills if s["name"] == official), None)
            if match:
                priority_map[domain] = match["name"]
                continue

        # Fallback: highest line count (most complete)
        best = max(domain_skills, key=lambda s: s["line_count"])
        priority_map[domain] = best["name"]

    return priority_map


if __name__ == "__main__":
    print(f"Scanning {SKILLS_DIR}...")
    skills = scan_skills(SKILLS_DIR)
    print(f"Found {len(skills)} skills")

    print("Building search index...")
    search_index = build_search_index(skills)
    print(f"Indexed {len(search_index)} keywords")

    print("Finding duplicates...")
    duplicates = find_duplicates(skills)
    print(f"Found {len(duplicates)} domains with 3+ skills (dedup candidates)")

    print("Building priority map...")
    priority_map = build_priority_map(skills)

    # Write outputs
    os.makedirs(os.path.dirname(OUTPUT_REGISTRY), exist_ok=True)

    registry_data = {
        "total_skills": len(skills),
        "domains": sorted(set(s["domain"] for s in skills)),
        "priority_map": priority_map,
        "skills": skills
    }

    with open(OUTPUT_REGISTRY, "w") as f:
        json.dump(registry_data, f, indent=2)
    print(f"Written: {OUTPUT_REGISTRY}")

    with open(OUTPUT_SEARCH, "w") as f:
        json.dump(search_index, f, indent=2)
    print(f"Written: {OUTPUT_SEARCH}")

    with open(OUTPUT_DUPLICATES, "w") as f:
        json.dump(duplicates, f, indent=2)
    print(f"Written: {OUTPUT_DUPLICATES}")

    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Total skills: {len(skills)}")
    print(f"Domains: {len(set(s['domain'] for s in skills))}")
    print(f"Skills without TL;DR: {sum(1 for s in skills if not s['has_tldr'])}")
    print(f"Skills > 500 lines: {sum(1 for s in skills if s['line_count'] > 500)}")
    print(f"Skills > 200 lines: {sum(1 for s in skills if s['line_count'] > 200)}")
    print("\nTop domains by skill count:")
    from collections import Counter
    domain_counts = Counter(s["domain"] for s in skills)
    for domain, count in domain_counts.most_common(10):
        canonical = priority_map.get(domain, "none")
        print(f"  {domain}: {count} skills (canonical: {canonical})")
    print("\nDuplicate domains needing cleanup:")
    for domain, entries in list(duplicates.items())[:5]:
        print(f"  {domain}: {len(entries)} skills")
        for e in entries[:3]:
            print(f"    - {e['name']} ({e['line_count']} lines)")
