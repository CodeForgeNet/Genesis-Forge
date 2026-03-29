#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { readFileSync, existsSync } from "node:fs";
import { join, relative } from "node:path";
import { KIT_ROOT, SKILLS_DIR, AGENT_DIR } from "./index.js";

const server = new McpServer({
  name: "genesis-forge-mcp",
  version: "1.2.0"
});

// ─── DATA LOADING ────────────────────────────────────────────────────────────

const SCRIPTS_DIR = join(AGENT_DIR, "scripts");
const REGISTRY_PATH = join(SCRIPTS_DIR, "skill_registry.json");
const INDEX_PATH = join(SCRIPTS_DIR, "skill_search_index.json");
const RULES_PATH = join(SCRIPTS_DIR, "routing_rules.json");

let registry = { skills: [], priority_map: {} };
let searchIndex = {};
let routingRules = { routing_rules: [], domain_agent_map: {}, parallel_map: [] };

function loadData() {
  try {
    if (existsSync(REGISTRY_PATH)) registry = JSON.parse(readFileSync(REGISTRY_PATH, "utf8"));
    if (existsSync(INDEX_PATH)) searchIndex = JSON.parse(readFileSync(INDEX_PATH, "utf8"));
    if (existsSync(RULES_PATH)) routingRules = JSON.parse(readFileSync(RULES_PATH, "utf8"));
  } catch (e) {
    console.error("Failed to load Genesis Forge data:", e.message);
  }
}

// Initial load
loadData();

// ─── MODEL TIER CONFIG ───────────────────────────────────────────────────────

const MODEL_LIMITS = {
  low:  { max_skills: 1, content_mode: "tldr_only", max_chars: 500 },
  mid:  { max_skills: 2, content_mode: "summary",   max_chars: 1000 },
  high: { max_skills: 4, content_mode: "full",      max_chars: -1 }
};

// ─── CORE LOGIC (PORTED FROM PYTHON) ─────────────────────────────────────────

function getLoadInstruction(skill, tier) {
  const limits = MODEL_LIMITS[tier] || MODEL_LIMITS.mid;
  const relPath = relative(KIT_ROOT, skill.path);
  
  if (limits.content_mode === "tldr_only") {
    return skill.has_tldr 
      ? `READ first 500 chars of ${relPath} (TL;DR section only)`
      : `READ first 300 chars of ${relPath}`;
  } else if (limits.content_mode === "summary") {
    return `READ first 1000 chars of ${relPath}`;
  }
  return `READ ${relPath} (full content)`;
}

function searchSkills(query, tier = "mid", maxResults = 3) {
  const tokens = query.toLowerCase().match(/\b[a-zA-Z][a-zA-Z0-9+#]{2,}\b/g) || [];
  const scores = new Map();
  const limits = MODEL_LIMITS[tier] || MODEL_LIMITS.mid;

  for (const token of tokens) {
    if (searchIndex[token]) {
      for (const sn of searchIndex[token]) {
        scores.set(sn, (scores.get(sn) || 0) + 1.0);
      }
    }
    // Partial matches
    for (const kw in searchIndex) {
      if (kw !== token && (kw.includes(token) || token.includes(kw))) {
        for (const sn of searchIndex[kw]) {
          scores.set(sn, (scores.get(sn) || 0) + 0.5);
        }
      }
    }
  }

  // Boost canonical
  const priorityMap = registry.priority_map || {};
  for (const skillName of Object.values(priorityMap)) {
    if (scores.has(skillName)) scores.set(skillName, scores.get(skillName) + 2.0);
  }

  const skillLookup = new Map(registry.skills.map(s => [s.name, s]));
  const ranked = [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .filter(([name]) => skillLookup.has(name))
    .map(([name, score]) => {
      const s = skillLookup.get(name);
      return {
        name: s.name,
        path: s.path,
        description: s.description,
        domain: s.domain,
        score: Math.round(score * 10) / 10,
        load_instruction: getLoadInstruction(s, tier)
      };
    })
    .slice(0, Math.max(limits.max_skills, maxResults)); // Use the larger of the two

  return ranked.slice(0, limits.max_skills);
}

function routeTask(task, tier = "mid") {
  const taskLower = task.toLowerCase();
  const limits = MODEL_LIMITS[tier] || MODEL_LIMITS.mid;

  // 1. Try registry-based routing (high performance)
  const topSkills = searchSkills(task, tier);
  
  if (topSkills.length > 0) {
    const agents = [];
    const domainMap = routingRules.domain_agent_map || {};
    
    for (const skill of topSkills) {
      const skillAgents = domainMap[skill.domain] || ["implementer-agent"];
      for (const a of skillAgents) {
        if (!agents.includes(a)) agents.push(a);
      }
    }

    const complexity = agents.length >= 4 ? "complex" : agents.length >= 2 ? "medium" : "simple";
    
    return {
      agents,
      skills: topSkills.map(s => s.name),
      skill_paths: topSkills.map(s => s.path),
      workflow: complexity === "complex" ? "orchestrate" : "create",
      complexity,
      requires_plan: complexity !== "simple",
      estimated_steps: agents.length,
      rationale: `Registry match (79 skills indexed). Tier: ${tier}. Top: ${topSkills[0].name}`,
      load_instructions: topSkills.map(s => s.load_instruction)
    };
  }

  // 2. Fallback to hardcoded rules (now dynamic JSON)
  const matches = routingRules.routing_rules
    .map(rule => ({
      score: rule.keywords.filter(kw => taskLower.includes(kw)).length,
      rule
    }))
    .filter(m => m.score > 0)
    .sort((a, b) => b.score - a.score);

  if (matches.length > 0) {
    const bestMatch = matches[0].rule;
    const agents = [...new Set(matches.flatMap(m => m.rule.agents))];
    const skills = [...new Set(matches.flatMap(m => m.rule.skills))].slice(0, limits.max_skills);
    
    return {
      agents,
      skills,
      workflow: bestMatch.workflow,
      complexity: agents.length >= 4 ? "complex" : agents.length >= 2 ? "medium" : "simple",
      rationale: "Pattern match (routing rules). Fallback to known mapping.",
    };
  }

  // 3. Absolute fallback
  return {
    agents: ["implementer-agent"],
    skills: ["clean-code"],
    workflow: "create",
    complexity: "simple",
    rationale: "Final fallback. No specific matches found."
  };
}

// ─── TOOL REGISTRATION ──────────────────────────────────────────────────────

server.registerTool(
  "skill_search",
  {
    title: "Search Genesis Forge Skills",
    description: "Search for specific specialist skills among 79 available knowledge modules.",
    inputSchema: z.object({
      query: z.string().describe("The task or keyword to search for (e.g., 'react performance', 'auth audit')"),
      tier: z.enum(["low", "mid", "high"]).default("mid").describe("Model tier for detail level")
    })
  },
  async ({ query, tier }) => {
    // Reload data if needed (optional)
    if (!registry.skills.length) loadData();
    const results = searchSkills(query, tier);
    return { 
      content: [{ 
        type: "text", 
        text: JSON.stringify(results, null, 2) 
      }] 
    };
  }
);

server.registerTool(
  "route_task",
  {
    title: "Route Task to Agents",
    description: "Determine the best agents and set of skills required to complete a complex task.",
    inputSchema: z.object({
      task: z.string().describe("Detailed task description"),
      tier: z.enum(["low", "mid", "high"]).default("mid").describe("Model tier for detail level")
    })
  },
  async ({ task, tier }) => {
    if (!registry.skills.length) loadData();
    const result = routeTask(task, tier);
    return { 
      content: [{ 
        type: "text", 
        text: JSON.stringify(result, null, 2) 
      }] 
    };
  }
);

server.registerTool(
  "get_skill_registry",
  {
    title: "Get Full Skill Registry",
    description: "Retrieve the complete metadata for all 79 skills in the kit.",
    inputSchema: z.object({})
  },
  async () => {
    if (!registry.skills.length) loadData();
    return { 
      content: [{ 
        type: "text", 
        text: JSON.stringify(registry, null, 2) 
      }] 
    };
  }
);

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Genesis Forge MCP server running via JS (high-performance)");
}

main().catch(error => {
  console.error("Fatal error in MCP server:", error);
  process.exit(1);
});
