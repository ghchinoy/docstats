---
title: MCP & Agent Plugins
description: Wire docstats into AI agent runtimes as a Model Context Protocol server. Covers the Agent Plugins v1.0.0 manifest, the three MCP tools, and manual client configuration.
sidebar:
  order: 1
---

docstats ships as a Model Context Protocol (MCP) server so AI coding assistants can audit prose they generate or edit. It conforms to the [Agent Plugins v1.0.0 specification](https://github.com/agentplugins/agent-plugins-spec), so compliant runtimes discover it automatically.

## Plugin manifest files

Agent runtimes read these root-level files to find the plugin, its MCP server, and its skill:

| File | Purpose |
|---|---|
| `plugin.json` | Plugin metadata and version information. |
| `mcp.json` | MCP STDIO server declaration. |
| `skills/readability-analysis/SKILL.md` | Skill guidance for AI assistants. |

The `mcp.json` uses `${PLUGIN_ROOT}` so the path resolves wherever the plugin is installed:

```json
{
  "mcpServers": {
    "readability-docstats": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "${PLUGIN_ROOT}/main.py", "--server-type", "mcp"],
      "cwd": "${PLUGIN_ROOT}"
    }
  }
}
```

## The three MCP tools

The server `readability-docstats` exposes three tools. Each accepts the same input: **exactly one** of `text`, `web_url`, or `gcs_pdf_uri`.

### `analyze_document` (preferred)

Comprehensive two-axis assessment:

- **Axis A** — 10 grade-level and reading-ease formulas plus a consensus standard.
- **Axis B** — deterministic house-style lint counts and rates, plus the rolled-up `ai_tell_score` (0.0–10.0, floor ≥ 7.0).

```json
{
  "name": "analyze_document",
  "arguments": {
    "text": "Your draft content here..."
  }
}
```

### `get_readability_scores`

Axis A only — readability scores and raw text statistics (syllables, words, sentences).

### `get_ai_pattern_scores`

Axis B only — house-style lint counts, rates, diagnostic flags, and `ai_tell_score`.

## Manual client configuration

For clients that do not auto-discover plugin manifests, register the server yourself.

**Claude Code (`~/.claude/settings.json`) or Gemini CLI (`~/.gemini/settings.json`):**

```json
{
  "mcpServers": {
    "readability_docstats": {
      "command": "uv",
      "args": ["run", "python", "/ABSOLUTE/PATH/TO/docstats/main.py", "--server-type", "mcp"],
      "cwd": "/ABSOLUTE/PATH/TO/docstats"
    }
  }
}
```

Replace `/ABSOLUTE/PATH/TO/docstats` with your local clone path.

## Remote deployments

If a subprocess is not practical, run the MCP server over HTTP instead:

```bash
uv run python main.py --server-type mcp-http --host 127.0.0.1 --port 8001
```

See [Server Modes](/docstats/guides/server-modes/) for the SSE versus plain-JSON options.

## Next steps

- [Skills](/docstats/integrations/skills/) — the `readability-analysis` skill that guides the model in reading the scorecard.
- [Interpreting Scores](/docstats/guides/interpreting-scores/) — how to act on the tool output.
