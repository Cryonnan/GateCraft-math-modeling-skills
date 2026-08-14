/**
 * DeepSeek Harness (dsh) bundle entry: registers every packaged
 * `skills/<name>/SKILL.md` bundle in this package on `ctx.skills`, so the
 * math-modeling skills ship with the profile instead of having to be copied
 * into a project's `.agents/skills` directory.
 *
 * Pattern follows the ecosystem standard skill-pack bundle
 * (e.g. zhaiyateng/dsh-design-skills, MIT).
 * @module math-modeling-skills
 */

import { readdirSync, readFileSync } from 'node:fs'
import { readdir, readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { parse as parseYaml } from 'yaml'

/** Same rank as packaged dsh skill providers (`BUNDLED_SKILL_RANK` in `@deepseek-ai/dsh-skill`). */
const BUNDLED_SKILL_RANK = 600
const SKILL_NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
const PROVIDER_NAME = 'math-modeling-skills'
const SKILLS_ROOT = fileURLToPath(new URL('./skills/', import.meta.url))

export const name = 'math-modeling-skills'
export const inject = ['skills']

/**
 * Register the packaged skill directory as one `ctx.skills` provider.
 * @param {import('@deepseek-ai/cordis').Context} ctx
 */
export function apply(ctx) {
  if (loadSkillsSync().length === 0) {
    throw new Error(`math-modeling-skills: no SKILL.md bundles found under ${SKILLS_ROOT}`)
  }
  ctx.skills.registerProvider(() => ({
    name: PROVIDER_NAME,
    async list(options) {
      options?.signal?.throwIfAborted()
      const listed = await loadSkills(options?.signal)
      options?.signal?.throwIfAborted()
      return listed.map(toCandidate)
    },
    async get(candidate, options) {
      options?.signal?.throwIfAborted()
      const listed = await loadSkills(options?.signal)
      const skill = listed.find((entry) => entry.name === candidate.name)
      return skill === undefined ? undefined : toDefinition(skill)
    },
  }))
}

async function loadSkills(signal) {
  const entries = await readdir(SKILLS_ROOT, { withFileTypes: true })
  const skills = []
  for (const entry of entries) {
    if (!entry.isDirectory() && !entry.isSymbolicLink()) continue
    signal?.throwIfAborted()
    const directory = join(SKILLS_ROOT, entry.name)
    const skillFile = join(directory, 'SKILL.md')
    skills.push(parseSkill(readFileSync(skillFile, 'utf8'), directory, skillFile))
  }
  return sortSkills(skills)
}

function loadSkillsSync() {
  const entries = readdirSync(SKILLS_ROOT, { withFileTypes: true })
  const skills = []
  for (const entry of entries) {
    if (!entry.isDirectory() && !entry.isSymbolicLink()) continue
    const directory = join(SKILLS_ROOT, entry.name)
    const skillFile = join(directory, 'SKILL.md')
    skills.push(parseSkill(readFileSync(skillFile, 'utf8'), directory, skillFile))
  }
  return sortSkills(skills)
}

function parseSkill(raw, directory, skillFile) {
  const parsed = parseFrontmatter(raw)
  if (parsed === undefined) {
    throw new Error(`math-modeling-skills: ${skillFile} is missing YAML frontmatter`)
  }
  const skillName = stringField(parsed.data, 'name')
  const description = stringField(parsed.data, 'description')
  if (skillName === undefined || description === undefined) {
    throw new Error(`math-modeling-skills: ${skillFile} frontmatter requires name and description`)
  }
  if (!SKILL_NAME.test(skillName)) {
    throw new Error(`math-modeling-skills: invalid skill name "${skillName}"`)
  }
  return {
    name: skillName,
    description,
    invocation: {
      modelInvocable: parsed.data['disable-model-invocation'] !== true,
      userInvocable: parsed.data['user-invocable'] !== false,
    },
    provider: PROVIDER_NAME,
    source: 'bundled',
    resourceBase: { kind: 'directory', path: directory },
    rank: BUNDLED_SKILL_RANK,
    locator: skillFile,
    path: skillFile,
    content: parsed.body.trim(),
  }
}

function sortSkills(skills) {
  const names = new Set()
  for (const skill of skills) {
    if (names.has(skill.name)) {
      throw new Error(`math-modeling-skills: duplicate skill name "${skill.name}"`)
    }
    names.add(skill.name)
  }
  return [...skills].sort((left, right) => left.name.localeCompare(right.name))
}

function toCandidate(skill) {
  return {
    name: skill.name,
    description: skill.description,
    invocation: skill.invocation,
    provider: skill.provider,
    source: skill.source,
    resourceBase: skill.resourceBase,
    rank: skill.rank,
    locator: skill.locator,
    path: skill.path,
  }
}

function toDefinition(skill) {
  return {
    name: skill.name,
    description: skill.description,
    invocation: skill.invocation,
    provider: skill.provider,
    source: skill.source,
    resourceBase: skill.resourceBase,
    path: skill.path,
    content: skill.content,
  }
}

function parseFrontmatter(raw) {
  const firstLineEnd = raw.indexOf('\n')
  if (firstLineEnd < 0) return undefined
  if (raw.slice(0, firstLineEnd).replace(/\r$/, '') !== '---') return undefined
  const start = firstLineEnd + 1
  const closing = findClosingFrontmatter(raw, start)
  if (closing === undefined) return undefined
  const parsed = parseYaml(raw.slice(start, closing.start))
  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) return undefined
  return { data: parsed, body: raw.slice(closing.bodyStart) }
}

function findClosingFrontmatter(raw, start) {
  let lineStart = start
  while (lineStart <= raw.length) {
    const nextNewline = raw.indexOf('\n', lineStart)
    const lineEnd = nextNewline < 0 ? raw.length : nextNewline
    if (raw.slice(lineStart, lineEnd).replace(/\r$/, '') === '---') {
      return { start: lineStart, bodyStart: nextNewline < 0 ? raw.length : nextNewline + 1 }
    }
    if (nextNewline < 0) return undefined
    lineStart = nextNewline + 1
  }
}

function stringField(data, key) {
  const value = data[key]
  if (typeof value !== 'string') return undefined
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : undefined
}
