#!/usr/bin/env python3
"""
add_tldr_to_skills.py - Bulk TL;DR Injection
=============================================
Reads every SKILL.md and generates a compressed TL;DR section
using pattern-based extraction (no AI needed).

This fixes Gap #8: Skills overload low models.
After running this, low models read ONLY the TL;DR.

Run once:
  python agent/scripts/add_tldr_to_skills.py --dry-run   # Preview changes
  python agent/scripts/add_tldr_to_skills.py              # Apply changes

Only modifies skills that don't already have a TL;DR section.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Optional, List, Tuple


def _resolve_agent_root() -> Path:
    env_root = os.environ.get("AGENT_ROOT")
    if env_root:
        return Path(env_root)
    return Path(__file__).resolve().parent.parent.parent


AGENT_ROOT = _resolve_agent_root()
SKILLS_DIR = AGENT_ROOT / "agent" / "skills"
TLDR_MARKER = "## TL;DR"

# Template for TL;DR generation
TLDR_TEMPLATE = """\
## TL;DR (Low-Model Mode)
{bullets}

---

"""


def already_has_tldr(content: str) -> bool:
    return TLDR_MARKER.lower() in content.lower()


def extract_name_from_frontmatter(content: str) -> Optional[str]:
    match = re.search(r'^name:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_description_from_frontmatter(content: str) -> Optional[str]:
    match = re.search(r'^description:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_first_heading(content: str) -> Optional[str]:
    """Get the first H1 or H2 heading content."""
    match = re.search(r'^#{1,2}\s+(.+)$', content, re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_use_when(content: str) -> Optional[str]:
    """Find 'when to use' or 'use when' section."""
    patterns = [
        r'(?:when to use|use when|trigger|invoke when)[^\n]*\n((?:[-*]\s+.+\n?){1,3})',
        r'(?:when to use|use when)[^\n]*\n(.{20,200})',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:150]
    return None


def extract_key_rules(content: str, max_rules: int = 3) -> List[str]:
    """Extract key rules/constraints from content."""
    rules = []

    # Look for bold/emphasized items that look like rules
    rule_patterns = [
        r'\*\*(?:Rule|RULE|Critical|CRITICAL|Important|IMPORTANT|Key|Never|Always)[^\*]+\*\*[^\n]*',
        r'>\s*(?:⚠️|🔴|❌|✅|CRITICAL|IMPORTANT)[^\n]+',
        r'^[-*]\s+(?:Never|Always|Must|Required|DO NOT|DO)[^\n]+',
    ]

    for pattern in rule_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for m in matches:
            clean = re.sub(r'[*>`#]', '', m).strip()
            if 10 < len(clean) < 150:
                rules.append(clean)
            if len(rules) >= max_rules:
                break
        if len(rules) >= max_rules:
            break

    return rules[:max_rules]


def extract_commands(content: str) -> Optional[str]:
    """Find the primary command to run."""
    # Look for code blocks with shell commands
    match = re.search(r'```(?:bash|sh|shell|cmd)?\n((?:python|npm|npx|node|pip|go|cargo|make)\s+[^\n]+)', content)
    if match:
        return match.group(1).strip()[:100]
    return None


def extract_dont_use_when(content: str) -> Optional[str]:
    """Find anti-patterns or when NOT to use."""
    match = re.search(
        r'(?:when not to use|do not use|don\'t use|avoid when|not for)[^\n]*\n(.{20,200})',
        content, re.IGNORECASE
    )
    if match:
        return match.group(1).strip()[:120]
    return None


def generate_tldr(skill_name: str, content: str) -> str:
    """Generate TL;DR from skill name and content."""
    bullets = []

    # 1. What it is
    desc = extract_description_from_frontmatter(content)
    heading = extract_first_heading(content)
    what = desc or heading or skill_name.replace("-", " ").title()
    bullets.append(f"- **What:** {what[:120]}")

    # 2. When to use
    use_when = extract_use_when(content)
    if use_when:
        # Condense to one line
        first_line = use_when.splitlines()[0].lstrip("- *").strip()
        bullets.append(f"- **Use when:** {first_line[:100]}")

    # 3. Key rules
    rules = extract_key_rules(content)
    for i, rule in enumerate(rules[:2], 1):
        bullets.append(f"- **Rule {i}:** {rule[:100]}")

    # 4. Don't use when (if found)
    dont = extract_dont_use_when(content)
    if dont and len(bullets) < 5:
        first_line = dont.splitlines()[0].lstrip("- *").strip()
        bullets.append(f"- **Skip when:** {first_line[:100]}")

    # 5. Primary command (if found)
    cmd = extract_commands(content)
    if cmd and len(bullets) < 5:
        bullets.append(f"- **Command:** `{cmd}`")

    # Pad to at least 3 bullets
    while len(bullets) < 3:
        bullets.append(f"- **Note:** See full SKILL.md for detailed instructions")

    return TLDR_TEMPLATE.format(bullets="\n".join(bullets))


def insert_tldr(content: str, tldr: str) -> str:
    """Insert TL;DR right after frontmatter (or at top if no frontmatter)."""
    if content.startswith("---"):
        # Find end of frontmatter
        second_dash = content.find("---", 3)
        if second_dash > 0:
            end_fm = second_dash + 3
            # Skip any whitespace after frontmatter
            rest = content[end_fm:].lstrip("\n")
            return content[:end_fm] + "\n\n" + tldr + rest

    # No frontmatter - insert at top
    return tldr + content


def process_skill(skill_path: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """Process a single SKILL.md. Returns (modified, reason)."""
    try:
        content = skill_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return False, f"Read error: {e}"

    if already_has_tldr(content):
        return False, "already has TL;DR"

    skill_name = skill_path.parent.name
    tldr = generate_tldr(skill_name, content)
    new_content = insert_tldr(content, tldr)

    if not dry_run:
        skill_path.write_text(new_content, encoding="utf-8")

    return True, "TL;DR added"


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx + 1])

    # Priority order: highest impact skills first
    PRIORITY_SKILLS = [
        "using-capabilities",
        "systematic-debugging",
        "react-best-practices",
        "web-design-guidelines",
        "executing-plans",
        "writing-plans",
        "plan-writing",
        "api-patterns",
        "clean-code",
        "testing-patterns",
        "vulnerability-scanner",
        "dispatching-parallel-agents",
        "parallel-agents",
        "subagent-driven-development",
    ]

    skills_path = Path(SKILLS_DIR)
    if not skills_path.exists():
        print(f"ERROR: {SKILLS_DIR} not found")
        sys.exit(1)

    all_skill_mds = list(skills_path.rglob("SKILL.md"))
    print(f"Found {len(all_skill_mds)} SKILL.md files")
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLY CHANGES'}")
    print()

    # Sort: priority skills first, then alphabetical
    def sort_key(p: Path):
        name = p.parent.name
        try:
            return (PRIORITY_SKILLS.index(name), name)
        except ValueError:
            return (len(PRIORITY_SKILLS), name)

    all_skill_mds.sort(key=sort_key)

    if limit:
        all_skill_mds = all_skill_mds[:limit]
        print(f"Limited to first {limit} skills")

    modified = 0
    skipped = 0
    errors = 0
    results = []

    for skill_md in all_skill_mds:
        skill_name = str(skill_md.parent.relative_to(skills_path))
        changed, reason = process_skill(skill_md, dry_run)

        if changed:
            modified += 1
            status = "WOULD ADD" if dry_run else "ADDED"
            results.append({"skill": skill_name, "status": status})
            if len(results) <= 20:  # Print first 20
                print(f"  {status} TL;DR: {skill_name}")
        else:
            skipped += 1
            if reason == "already has TL;DR":
                pass  # Don't print these
            else:
                errors += 1
                print(f"  ERROR {skill_name}: {reason}")

    print(f"\n{'=' * 40}")
    print(f"Skills processed: {len(all_skill_mds)}")
    print(f"TL;DR {'would be added' if dry_run else 'added'}: {modified}")
    print(f"Already had TL;DR: {skipped - errors}")
    print(f"Errors: {errors}")

    if dry_run:
        print(f"\nRun without --dry-run to apply {modified} changes")
