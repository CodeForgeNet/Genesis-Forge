export interface SkillMetadata {
  name: string;
  description: string;
  domain?: string;
  source?: string;
  risk?: string;
  isValid: boolean;
  errors?: any;
}

export interface SkillEntry {
  name: string;
  path: string;
  description: string;
  domain: string;
  sourceType: 'personal' | 'capabilities';
  skillFile: string;
  [key: string]: any;
}

export function extractFrontmatter(filePath: string): SkillMetadata;

export function findSkillsInDir(dir: string | null, sourceType: 'personal' | 'capabilities'): SkillEntry[];

export function resolveSkillPath(skillName: string): {
  skillFile: string;
  sourceType: string;
  skillPath: string;
} | null;

export function checkForUpdates(repoDir: string): boolean;

export function stripFrontmatter(content: string): string;
