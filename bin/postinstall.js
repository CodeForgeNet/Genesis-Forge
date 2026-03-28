#!/usr/bin/env node
/**
 * postinstall.js — Runs after npm install
 * Checks for Python 3 availability and prints a welcome message.
 */

import { spawnSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const KIT_ROOT = resolve(__dirname, "..");

// Check Python 3
const py = spawnSync("python3", ["--version"], { encoding: "utf8" });
const hasPython = py.status === 0;

console.log(`
╔══════════════════════════════════════════════════════════╗
║             ✦ Genesis Forge Installed ✦              ║
╚══════════════════════════════════════════════════════════╝

  Run: npx genesis-forge setup --help

  Python 3: ${hasPython ? "✅ found (" + py.stdout.trim() + ")" : "❌ not found — install from https://python.org"}

  Next steps:
    1. Run \`npx genesis-forge setup\` to configure integration
    2. Check README.md for integration with Gemini/Claude CLIs.
    3. Build skill registry: npm run build-registry

  Docs: ${KIT_ROOT}/README.md
`);

