#!/usr/bin/env node
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const KIT_ROOT = resolve(__dirname, '..');
const AGENT_DIR = join(KIT_ROOT, 'agent');
const SCRIPTS_DIR = join(AGENT_DIR, 'scripts');
const pkg = JSON.parse(readFileSync(join(KIT_ROOT, 'package.json'), 'utf8'));

const args = process.argv.slice(2);
const command = args[0];

if (command === '--version' || command === '-v') {
    console.log(`${pkg.name} v${pkg.version}`);
    process.exit(0);
}

if (command === '--help' || command === '-h' || !command) {
    console.log(`Usage: npx genesis-forge setup [args] or npx genesis-forge [command] [args]`);
    console.log('\nCommands:');
    console.log('  setup          Automates the integration.');
    console.log('  list-agents    List available specialist agents.');
    console.log('  list-workflows List available slash-command workflows.');
    console.log('  memory inject  Inject session memory from state.');
    console.log('  --version, -v  Show version.');
    process.exit(0);
}

if (command === 'list-agents') {
    const agentsDir = join(AGENT_DIR, 'agents');
    if (existsSync(agentsDir)) {
        const agents = readdirSync(agentsDir)
            .filter(f => f.endsWith('.md'))
            .map(f => f.replace('.md', ''));
        console.log('Available Agents:');
        agents.forEach(a => console.log(`  - ${a}`));
    }
    process.exit(0);
}

if (command === 'list-workflows') {
    const workflowsDir = join(AGENT_DIR, 'workflows');
    if (existsSync(workflowsDir)) {
        const workflows = readdirSync(workflowsDir)
            .filter(f => f.endsWith('.md'))
            .map(f => `/${f.replace('.md', '')}`);
        console.log('Available Workflows:');
        workflows.forEach(w => console.log(`  - ${w}`));
    }
    process.exit(0);
}

if (command === 'memory') {
    const sub = args[1];
    if (sub === 'inject') {
        const stateFile = join(process.env.HOME || '', '.gemini', 'genesis-forge', 'session.json');
        if (!existsSync(stateFile)) {
            console.log('No session memory found. Start with fresh state.');
        } else {
            console.log(`Injecting memory from ${stateFile}...`);
        }
        process.exit(0);
    }
}

console.error(`Unknown command: ${command}`);
process.exit(1);
