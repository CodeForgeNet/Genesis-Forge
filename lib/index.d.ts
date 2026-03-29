export const KIT_ROOT: string;
export const AGENT_DIR: string;
export const SKILLS_DIR: string;
export const AGENTS_DIR: string;
export const WORKFLOWS_DIR: string;

export interface AgentPathResult {
  path: string;
}

export function getAgentPath(agentName: string): string;

export interface SkillPathResult {
  skillFile: string;
  sourceType: 'personal' | 'capabilities';
  skillPath: string;
}

export function getSkillPath(skillName: string): string;

import * as skillsCore from './skills-core.js';
export { skillsCore };
