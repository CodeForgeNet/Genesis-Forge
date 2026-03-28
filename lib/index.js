import path from 'path';
import { fileURLToPath } from 'url';
import * as skillsCore from './skills-core.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Since index.js is now in /lib, KIT_ROOT is the parent directory (..)
export const KIT_ROOT = path.resolve(__dirname, '..');
export const AGENT_DIR = path.join(KIT_ROOT, 'agent');
export const SKILLS_DIR = path.join(AGENT_DIR, 'skills');
export const AGENTS_DIR = path.join(AGENT_DIR, 'agents');
export const WORKFLOWS_DIR = path.join(AGENT_DIR, 'workflows');

export { skillsCore };

/**
 * Get the path to a specific agent's definition file.
 * @param {string} agentName - The name of the agent.
 * @returns {string} - The absolute path to the agent's .md file.
 */
export function getAgentPath(agentName) {
  return path.join(AGENTS_DIR, `${agentName}.md`);
}

/**
 * Get the path to a specific skill's directory.
 * @param {string} skillName - The name of the skill.
 * @returns {string} - The absolute path to the skill's directory.
 */
export function getSkillPath(skillName) {
  return path.join(SKILLS_DIR, skillName);
}
