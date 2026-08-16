# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Agent Plugin v1.0.0 packaging (additive, no runtime changes):
  - `plugin.json` — plugin manifest (`name: docstats`).
  - `mcp.json` — portable STDIO MCP server declaration for the existing
    `get_readability_scores` tool, using `${PLUGIN_ROOT}` instead of
    hard-coded paths.
  - `skills/readability-analysis/` — the `readability-analysis` Agent Skill,
    with a `references/score-interpretation.md` guide.
- README "Agent Plugin" section documenting the plugin, skill, and install.
