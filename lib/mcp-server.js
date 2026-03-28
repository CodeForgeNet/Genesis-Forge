#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { spawnSync } from "node:child_process";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { KIT_ROOT, SKILLS_DIR, WORKFLOWS_DIR, AGENT_DIR } from "./index.js";

const server = new McpServer({
  name: "genesis-forge-mcp",
  version: "1.0.0"
});

// Helper to run python scripts
function runPython(scriptName, args = []) {
  const scriptPath = join(AGENT_DIR, "scripts", scriptName);
  if (!existsSync(scriptPath)) {
    return { error: `Script not found: ${scriptPath}` };
  }
  const result = spawnSync("python3", [scriptPath, ...args], {
    encoding: "utf8",
    env: { ...process.env, AGENT_ROOT: KIT_ROOT },
  });
  if (result.error) return { error: result.error.message };
  return { stdout: result.stdout, stderr: result.stderr, status: result.status };
}

// 1. Tool: Search Skills
server.registerTool(
  "skill_search",
  {
    title: "Search Genesis Forge Skills",
    description: "Search for specific specialist skills among 950+ available knowledge modules.",
    inputSchema: z.object({
      query: z.string().describe("The task or keyword to search for (e.g., 'react performance', 'auth audit')")
    })
  },
  async ({ query }) => {
    const result = runPython("skill_search.py", [query]);
    if (result.error) return { content: [{ type: "text", text: result.error }] };
    return { content: [{ type: "text", text: result.stdout }] };
  }
);

// 2. Tool: Route Task
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
    const result = runPython("route_task.py", [task, "--tier", tier]);
    if (result.error) return { content: [{ type: "text", text: result.error }] };
    return { content: [{ type: "text", text: result.stdout }] };
  }
);

// 3. Tool: Get Registry
server.registerTool(
  "get_skill_registry",
  {
    title: "Get Full Skill Registry",
    description: "Retrieve the complete metadata for all 950+ skills in the kit.",
    inputSchema: z.object({})
  },
  async () => {
    const registryPath = join(AGENT_DIR, "scripts", "skill_registry.json");
    if (!existsSync(registryPath)) {
      return { content: [{ type: "text", text: "Registry not build. Run build_skill_registry.py first." }] };
    }
    const content = readFileSync(registryPath, "utf8");
    return { content: [{ type: "text", text: content }] };
  }
);

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Genesis Forge MCP server running via stdio");
}

main().catch(error => {
  console.error("Fatal error in MCP server:", error);
  process.exit(1);
});
