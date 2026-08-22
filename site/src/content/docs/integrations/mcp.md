---
title: MCP & Agent Plugins
description: Connect docstats to AI agent runtimes through the Model Context Protocol and the Agent Plugins v1.0.0 standard.
sidebar:
  order: 1
---

docstats provides a Model Context Protocol (MCP) server enabling AI coding assistants to evaluate prose quality. It conforms to the [Agent Plugins v1.0.0 specification](https://github.com/agentplugins/agent-plugins-spec), allowing compatible runtimes to discover the server and skill definitions automatically.

## Plugin Manifest Files

Agent runtimes locate the plugin, MCP server, and skill through root manifest files:

| File | Purpose |
|---|---|
| `plugin.json` | Plugin metadata and version information. |
| `mcp.json` | MCP STDIO server launch configuration. |
| `skills/readability-analysis/SKILL.md` | Model-facing analysis guidance. |

The `mcp.json` file uses `${PLUGIN_ROOT}` to resolve paths portably:

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

## MCP Tool Reference

The `readability-docstats` server registers three tools. Each tool accepts **exactly one** of `text`, `web_url`, or `gcs_pdf_uri`.

### `analyze_document`

Performs combined two-axis document evaluation:

- **Axis A**: Ten grade-level and reading-ease formulas with consensus grade level.
- **Axis B**: Deterministic house-style lint counts, rates, diagnostic flags, and the rolled-up `ai_tell_score` (0.0–10.0 scale, passing floor ≥ 7.0).

```json
{
  "name": "analyze_document",
  "arguments": {
    "text": "Your draft content here..."
  }
}
```

### `get_readability_scores`

Calculates Axis A readability metrics and raw structural counts (syllables, words, sentences).

### `get_ai_pattern_scores`

Calculates Axis B pattern counts, occurrence rates, diagnostic flags, and `ai_tell_score`.

## Manual Client Configuration

For agent environments without automatic plugin discovery, configure the server manually.

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

Replace `/ABSOLUTE/PATH/TO/docstats` with the path to your repository clone.

## Remote HTTP Deployment

To run the MCP server over HTTP rather than standard I/O:

```bash
uv run python main.py --server-type mcp-http --host 127.0.0.1 --port 8001
```

See [Server Modes](/docstats/guides/server-modes/) for configuration options.

## Next Steps

- [Skills](/docstats/integrations/skills/): Model-facing instructions for interpreting scorecard results.
- [Interpreting Scores](/docstats/guides/interpreting-scores/): Detailed score interpretations and target audience bands.
