import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { z } from 'zod';
import { KIT_ROOT, AGENT_DIR } from './index.js';

// ─── CACHE ───────────────────────────────────────────────────────────────────

let skillRegistryCache = null;

const SkillSchema = z.object({
    name: z.string().min(1, "Skill name is required"),
    description: z.string().min(5, "Description must be at least 5 characters"),
    domain: z.string().optional(),
    source: z.string().optional(),
    risk: z.string().optional(),
});

/**
 * Extract YAML frontmatter from a skill file.
 * Uses Zod for validation.
 *
 * @param {string} filePath - Path to SKILL.md file
 * @returns {{name: string, description: string}}
 */
function extractFrontmatter(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf8');
        const lines = content.split('\n');

        let inFrontmatter = false;
        let fm = {};

        for (const line of lines) {
            if (line.trim() === '---') {
                if (inFrontmatter) break;
                inFrontmatter = true;
                continue;
            }

            if (inFrontmatter) {
                const match = line.match(/^(\w+):\s*(.*)$/);
                if (match) {
                    const [, key, value] = match;
                    fm[key.trim()] = value.trim().replace(/^["'](.*)["']$/, '$1');
                }
            }
        }

        // Validate with Zod
        const result = SkillSchema.safeParse(fm);
        if (!result.success) {
            console.error(`[skills-core] Validation failed for ${filePath}:`, result.error.format());
            // Fallback to minimal data if possible, or throw
            return { 
                name: fm.name || path.basename(path.dirname(filePath)), 
                description: fm.description || '',
                isValid: false,
                errors: result.error.format()
            };
        }

        return { ...result.data, isValid: true };
    } catch (error) {
        return { name: '', description: '', isValid: false };
    }
}

/**
 * Find all skills, prioritizing the pre-built registry for performance.
 *
 * @param {string} dir - Directory to search (ignored if registry exists)
 * @param {string} sourceType - 'personal' or 'capabilities'
 * @returns {Array}
 */
function findSkillsInDir(dir, sourceType) {
    // 1. Check in-memory cache
    if (skillRegistryCache) {
        return skillRegistryCache.filter(s => s.sourceType === sourceType);
    }

    // 2. Try to load from pre-built registry
    const registryPath = path.join(AGENT_DIR, 'scripts', 'skill_registry.json');
    if (fs.existsSync(registryPath)) {
        try {
            const data = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
            if (data.skills) {
                // Initialize cache
                skillRegistryCache = data.skills.map(s => ({
                    ...s,
                    sourceType: 'capabilities', // Registry mostly contains core capabilities
                    skillFile: path.join(KIT_ROOT, s.path)
                }));
                return skillRegistryCache.filter(s => s.sourceType === sourceType);
            }
        } catch (e) {
            console.error('[skills-core] Failed to load skill_registry.json:', e.message);
        }
    }

    // 3. Fallback to filesystem scan (Cold startup / development)
    console.warn(`[skills-core] Registry not found at ${registryPath}. Falling back to filesystem scan.`);
    const skills = [];
    if (!fs.existsSync(dir)) return skills;

    function recurse(currentDir, depth) {
        if (depth > 3) return;
        const entries = fs.readdirSync(currentDir, { withFileTypes: true });

        for (const entry of entries) {
            const fullPath = path.join(currentDir, entry.name);
            if (entry.isDirectory()) {
                const skillFile = path.join(fullPath, 'SKILL.md');
                if (fs.existsSync(skillFile)) {
                    const fm = extractFrontmatter(skillFile);
                    skills.push({
                        path: fullPath,
                        skillFile: skillFile,
                        name: fm.name || entry.name,
                        description: fm.description || '',
                        sourceType: sourceType
                    });
                }
                recurse(fullPath, depth + 1);
            }
        }
    }

    recurse(dir, 0);
    return skills;
}

/**
 * Resolve a skill name to its file path, handling shadowing and registry lookup.
 *
 * @param {string} skillName - Name like "react-best-practices"
 * @returns {{skillFile: string, sourceType: string, skillPath: string} | null}
 */
function resolveSkillPath(skillName) {
    // Strip capabilities: prefix if present
    const forceCapabilities = skillName.startsWith('capabilities:');
    const name = forceCapabilities ? skillName.replace(/^capabilities:/, '') : skillName;

    // Use registry if available
    const skills = findSkillsInDir(null, 'capabilities');
    const match = skills.find(s => s.name === name);
    
    if (match) {
        return {
            skillFile: match.skillFile,
            sourceType: match.sourceType,
            skillPath: match.path
        };
    }

    return null;
}

/**
 * Check if a git repository has updates available.
 */
function checkForUpdates(repoDir) {
    try {
        const output = execSync('git fetch origin && git status --porcelain=v1 --branch', {
            cwd: repoDir,
            timeout: 3000,
            encoding: 'utf8',
            stdio: 'pipe'
        });

        return output.includes('[behind ');
    } catch (error) {
        return false;
    }
}

/**
 * Strip YAML frontmatter from skill content.
 */
function stripFrontmatter(content) {
    if (!content.startsWith('---')) return content.trim();
    const parts = content.split('---');
    if (parts.length < 3) return content.trim();
    return parts.slice(2).join('---').trim();
}

export {
    extractFrontmatter,
    findSkillsInDir,
    resolveSkillPath,
    checkForUpdates,
    stripFrontmatter
};

