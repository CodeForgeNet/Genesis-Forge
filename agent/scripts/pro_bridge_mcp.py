from mcp.server.fastmcp import FastMCP
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("pro_bridge_mcp")

AGENT_ROOT = Path.cwd() / ".agent"
if not (AGENT_ROOT.exists() and AGENT_ROOT.is_dir()):
    AGENT_ROOT = Path(__file__).parent.parent.resolve()

SKILLS_DIR = AGENT_ROOT / "skills"
AGENTS_DIR = AGENT_ROOT / "agents"

@mcp.tool()
def search_skills(query: str) -> str:
    """
    Search for skills by name matching the given query string. 
    Use a broad keyword (like 'react', 'python', 'security', 'aws') to find relevant skills.
    Returns a list of matching skill folder names.
    """
    if not SKILLS_DIR.exists():
        return "Skills directory not found."
    
    matches = []
    for skill_path in SKILLS_DIR.iterdir():
        if skill_path.is_dir() and query.lower() in skill_path.name.lower():
            matches.append(skill_path.name)
            
    if not matches:
        return f"No skills found matching '{query}'. Try a different keyword."
    
    # Returning a maximum of 50 to avoid blowing up the context window
    res = matches[:50]
    return f"Found {len(matches)} matching skills (showing top {len(res)}):\n" + "\n".join(res)

@mcp.tool()
def fetch_skill(skill_name: str) -> str:
    """
    Fetch the full contents of the SKILL.md file for a specific skill.
    Pass the exact skill name retrieved from search_skills().
    """
    skill_md_path = SKILLS_DIR / skill_name / "SKILL.md"
    
    if not skill_md_path.exists():
        return f"Error: SKILL.md not found for skill '{skill_name}'"
        
    try:
        content = skill_md_path.read_text(encoding="utf-8")
        return f"--- CONTENT FOR SKILL: {skill_name} ---\n\n{content}"
    except Exception as e:
        return f"Error reading skill '{skill_name}': {str(e)}"

@mcp.tool()
def read_agent_role(agent_name: str) -> str:
    """
    Fetch the instructions for a specific agent persona from the agent/agents/ folder.
    Use this to get the persona rules (e.g., 'frontend-specialist', 'orchestrator' or 'project-planner').
    Do not add the '.md' extension to the agent_name.
    """
    agent_name = agent_name.replace(".md", "")
    agent_path = AGENTS_DIR / f"{agent_name}.md"
    
    if not agent_path.exists():
        return f"Error: Agent file not found for '{agent_name}'. Check if it exists."
        
    try:
        content = agent_path.read_text(encoding="utf-8")
        return f"--- ROLE INSTRUCTIONS FOR: {agent_name} ---\n\n{content}"
    except Exception as e:
        return f"Error reading agent '{agent_name}': {str(e)}"

if __name__ == "__main__":
    mcp.run()
