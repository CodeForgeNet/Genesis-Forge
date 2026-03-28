#!/usr/bin/env node
/**
 * run-hook.js — Cross-platform hook runner (replaces run-hook.cmd)
 * 
 * Usage: node run-hook.js <hook-name> [args]
 * 
 * Currently supported hooks:
 *   session-start   — Injects session memory context
 */

import { spawnSync } from "node:child_process";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { existsSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const KIT_ROOT = process.env.AGENT_ROOT ?? resolve(__dirname, "..", "..");
const SCRIPTS_DIR = join(KIT_ROOT, "agent", "scripts");

const hookName = process.argv[2];

if (!hookName) {
  console.error("Usage: run-hook.js <hook-name>");
  process.exit(1);
}

switch (hookName) {
  case "session-start": {
    const script = join(SCRIPTS_DIR, "session_memory.py");
    if (!existsSync(script)) {
      process.exit(0); // Silently skip if not found
    }
    const result = spawnSync("python3", [script, "session-start"], {
      stdio: "inherit",
      env: { ...process.env, AGENT_ROOT: KIT_ROOT },
    });
    process.exit(result.status ?? 0);
    break;
  }

  default:
    console.warn(`[run-hook] Unknown hook: ${hookName}. Skipping.`);
    process.exit(0);
}
