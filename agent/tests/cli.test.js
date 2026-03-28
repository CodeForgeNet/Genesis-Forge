import test from 'node:test';
import assert from 'node:assert';
import { spawnSync } from 'node:child_process';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const KIT_ROOT = resolve(__dirname, '../..');
const CLI_PATH = join(KIT_ROOT, 'bin/cli.js');

function runCLI(args) {
    return spawnSync('node', [CLI_PATH, ...args], {
        encoding: 'utf8',
        env: { ...process.env, AGENT_ROOT: KIT_ROOT }
    });
}

test('CLI: --version', () => {
    const result = runCLI(['--version']);
    assert.strictEqual(result.status, 0);
    assert.match(result.stdout, /genesis-forge v/);
});

test('CLI: help', () => {
    const result = runCLI(['--help']);
    assert.strictEqual(result.status, 0);
    assert.match(result.stdout, /Usage: npx genesis-forge setup/);
});

test('CLI: list-agents', () => {
    const result = runCLI(['list-agents']);
    assert.strictEqual(result.status, 0);
    assert.match(result.stdout, /backend-specialist/);
    assert.match(result.stdout, /frontend-specialist/);
});

test('CLI: list-workflows', () => {
    const result = runCLI(['list-workflows']);
    assert.strictEqual(result.status, 0);
    assert.match(result.stdout, /\/debug/);
    assert.match(result.stdout, /\/create/);
});

test('CLI: memory inject (cold)', () => {
    const result = runCLI(['memory', 'inject']);
    assert.strictEqual(result.status, 0);
    assert.match(result.stdout, /No session memory found/);
});
