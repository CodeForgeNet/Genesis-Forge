# Genesis Forge — Changelog

All notable changes to this project will be documented here.

Format: [Semantic Versioning](https://semver.org)

---

## [1.0.0] — 2026-03-29

### Added
- 24 specialist AI agents (frontend, backend, mobile, security, devops, and more)
- 80 skill modules organized by domain
- 13 slash-command workflows (`/debug`, `/create`, `/deploy`, `/orchestrate`, etc.)
- `bin/setup.js` — Full CLI with integration for Gemini and Claude CLIs
- `lib/mcp-server.js` — Native MCP server for Claude and Cline integration
- `package.json` — npm publishable package with bin entry
- Dynamic path resolution — works in global npm installs and outside the repo directory
- Session memory defaults to `~/.genesis-forge/state/` for global installs
- `AGENT_ROOT` and `GENESIS_STATE_DIR` env vars for custom path overrides
- `README.md`, `CONTRIBUTING.md`, `LICENSE` (MIT), `CHANGELOG.md`
- `docs/CONFIG.md` — Configuration and MCP setup docs
- `docs/GETTING_STARTED.md` — 5-minute onboarding guide
- `docs/WORKFLOWS.md` — All 13 workflows documented with examples
- `bin/postinstall.js` — Post-install welcome and Python check

### Changed
- `rules/GEMINI.md` — Gemini CLI integration is now optional; all hardcoded `.agent/` paths removed
- `scripts/session_memory.py` — Dynamic state dir resolution, full error handling
- `scripts/route_task.py` — Dynamic path resolution via `AGENT_ROOT`
- `shared/CONTEXT.md` — Self-contained
- `mcp_config.json` — Valid JSON (removed `//` comments), uses `${ENV_VAR}` placeholders

### Removed
- All hardcoded `.planning/` and legacy references from core scripts

---

## [Unreleased]

### Planned
- `tests/` — Minimal test suite for CLI and routing
- Skill organization: core vs. community vs. experimental tiers
- `ATTRIBUTION.md` — License and source attribution for bundled skills
- GitHub Actions CI workflow
- Docker support
