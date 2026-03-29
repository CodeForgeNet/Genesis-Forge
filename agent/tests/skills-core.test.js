import test from 'node:test';
import assert from 'node:assert';
import { extractFrontmatter, stripFrontmatter } from '../../lib/skills-core.js';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { writeFileSync, unlinkSync } from 'node:fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEST_SKILL = join(__dirname, 'temp_skill.md');

test('SkillsCore: extractFrontmatter (Valid)', () => {
    const content = `---
name: "test-skill"
description: "A valid test skill."
---
# Content`;
    writeFileSync(TEST_SKILL, content);
    
    try {
        const fm = extractFrontmatter(TEST_SKILL);
        assert.ok(fm.isValid);
        assert.strictEqual(fm.name, "test-skill");
        assert.strictEqual(fm.description, "A valid test skill.");
    } finally {
        unlinkSync(TEST_SKILL);
    }
});

test('SkillsCore: extractFrontmatter (Invalid - missing name)', () => {
    const content = `---
description: "A skill without name."
---
# Content`;
    writeFileSync(TEST_SKILL, content);
    
    try {
        const fm = extractFrontmatter(TEST_SKILL);
        assert.strictEqual(fm.isValid, false);
    } finally {
        unlinkSync(TEST_SKILL);
    }
});

test('SkillsCore: stripFrontmatter', () => {
    const content = `---
name: test
---
Real content`;
    const stripped = stripFrontmatter(content);
    assert.strictEqual(stripped, "Real content");
});
