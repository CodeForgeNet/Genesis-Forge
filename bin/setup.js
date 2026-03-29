#!/usr/bin/env node
import { existsSync, mkdirSync, symlinkSync, unlinkSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import os from 'node:os';

const __dirname = dirname(fileURLToPath(import.meta.url));
const KIT_ROOT = resolve(__dirname, '..');
const RULES_FILE = join(KIT_ROOT, 'agent', 'rules', 'GEMINI.md');
const MCP_CONFIG_TEMPLATE = join(KIT_ROOT, 'agent', 'mcp_config.json');

const HOME = process.env.HOME || process.env.USERPROFILE;
const GEMINI_DIR = join(HOME, '.gemini');
const GEMINI_TARGET = join(GEMINI_DIR, 'GEMINI.md');
const GENESIS_STATE_DIR = join(GEMINI_DIR, 'genesis-forge');

function setupGemini() {
  console.log('--- Setting up Gemini CLI integration ---');
  if (!existsSync(GEMINI_DIR)) {
    console.log(`Creating directory: ${GEMINI_DIR}`);
    mkdirSync(GEMINI_DIR, { recursive: true });
  }

  if (existsSync(GEMINI_TARGET)) {
    console.log(`Removing existing symlink: ${GEMINI_TARGET}`);
    try {
      unlinkSync(GEMINI_TARGET);
    } catch (e) {
      console.error(`Failed to remove existing file/symlink: ${GEMINI_TARGET}. Please remove it manually.`);
      return;
    }
  }

  try {
    console.log(`Creating symlink: ${GEMINI_TARGET} -> ${RULES_FILE}`);
    symlinkSync(RULES_FILE, GEMINI_TARGET);
    console.log('✅ Gemini CLI rules installed.');
  } catch (e) {
    console.error(`❌ Failed to create symlink: ${e.message}`);
    console.log(`Manual instruction: Copy ${RULES_FILE} to ${GEMINI_TARGET}`);
  }

  if (!existsSync(GENESIS_STATE_DIR)) {
    mkdirSync(GENESIS_STATE_DIR, { recursive: true });
  }
}

function setupClaude() {
  console.log('\n--- Setting up Claude CLI (Claude Code) integration ---');
  
  const CLAUDE_CONFIG = join(HOME, '.claude.json');
  const mcpEntry = {
    command: 'npx',
    args: ['-y', 'genesis-mcp']
  };

  let config = { mcpServers: {} };
  
  if (existsSync(CLAUDE_CONFIG)) {
    try {
      config = JSON.parse(readFileSync(CLAUDE_CONFIG, 'utf8'));
    } catch (e) {
      console.warn(`⚠️ Could not parse existing ${CLAUDE_CONFIG}. Starting fresh.`);
    }
  }

  if (!config.mcpServers) config.mcpServers = {};
  
  config.mcpServers['genesis-forge'] = mcpEntry;

  try {
    writeFileSync(CLAUDE_CONFIG, JSON.stringify(config, null, 2));
    console.log(`✅ Genesis Forge MCP server added to ${CLAUDE_CONFIG}`);
    console.log('You can now use search_skill and route_task in Claude Code.');
  } catch (e) {
    console.error(`❌ Failed to update ${CLAUDE_CONFIG}: ${e.message}`);
    console.log(`Manual setup: Add the following to your mcpServers config in ${CLAUDE_CONFIG}:`);
    console.log(JSON.stringify({ 'genesis-forge': mcpEntry }, null, 2));
  }
}

function removeGemini() {
  console.log('--- Removing Gemini CLI integration ---');
  if (existsSync(GEMINI_TARGET)) {
    try {
      unlinkSync(GEMINI_TARGET);
      console.log(`✅ Removed symlink: ${GEMINI_TARGET}`);
    } catch (e) {
      console.error(`❌ Failed to remove symlink at ${GEMINI_TARGET}: ${e.message}`);
    }
  } else {
    console.log('Gemini CLI symlink not found, skipping.');
  }
}

function removeClaude() {
  console.log('\n--- Removing Claude CLI integration ---');
  const CLAUDE_CONFIG = join(HOME, '.claude.json');
  if (existsSync(CLAUDE_CONFIG)) {
    try {
      const content = readFileSync(CLAUDE_CONFIG, 'utf8');
      const config = JSON.parse(content);
      if (config.mcpServers && config.mcpServers['genesis-forge']) {
        delete config.mcpServers['genesis-forge'];
        writeFileSync(CLAUDE_CONFIG, JSON.stringify(config, null, 2));
        console.log(`✅ Removed 'genesis-forge' from ${CLAUDE_CONFIG}`);
      } else {
        console.log("'genesis-forge' entry not found in Claude config.");
      }
    } catch (e) {
      console.error(`❌ Failed to update Claude config: ${e.message}`);
    }
  } else {
    console.log('Claude config not found, skipping.');
  }
}

const pkg = JSON.parse(readFileSync(join(KIT_ROOT, 'package.json'), 'utf8'));
const args = process.argv.slice(2);
const command = args[0] || 'setup';

if (command === 'setup') {
  setupGemini();
  setupClaude();
} else if (command === 'remove' || command === 'unsetup' || command === 'uninstall') {
  removeGemini();
  removeClaude();
} else if (command === '--version' || command === '-v') {
  console.log(`${pkg.name} v${pkg.version}`);
} else if (command === '--help' || command === '-h') {
  console.log('Usage: npx genesis-forge [setup|remove|--version]');
  console.log('\nCommands:');
  console.log('  setup          Automates the integration of Genesis Forge with Gemini and Claude CLIs.');
  console.log('  remove         Removes integrations (symlink and Claude MCP server) and cleans up config.');
  console.log('  --version, -v  Show the current version of Genesis Forge.');
} else {
  console.log(`Unknown command: ${command}`);
  console.log('Usage: npx genesis-forge [setup|remove|--version]');
}

