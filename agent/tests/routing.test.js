import test from 'node:test';
import assert from 'node:assert';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const KIT_ROOT = resolve(__dirname, '../..');
const ROUTER_PATH = join(KIT_ROOT, 'agent/scripts/route_task.py');

function route(task) {
    return spawnSync('python3', [ROUTER_PATH, task], {
        encoding: 'utf8',
        env: { ...process.env, AGENT_ROOT: KIT_ROOT }
    });
}

test('Routing: react task follows frontend domain', () => {
    const res = route('build a react dashboard');
    assert.strictEqual(res.status, 0);
    const data = JSON.parse(res.stdout);
    assert.ok(data.agents.includes('frontend-specialist'));
    assert.ok(data.skills.includes('react-best-practices'));
});

test('Routing: security task follows security domain', () => {
    const res = route('penetration test the login api');
    assert.strictEqual(res.status, 0);
    const data = JSON.parse(res.stdout);
    assert.ok(data.agents.includes('security-auditor') || data.agents.includes('penetration-tester'));
});

test('Routing: unknown task falls back', () => {
    const res = route('bake a chocolate cake');
    assert.strictEqual(res.status, 0);
    const data = JSON.parse(res.stdout);
    assert.ok(data.agents.includes('implementer-agent'));
    assert.ok(data.skills.includes('clean-code'));
});
