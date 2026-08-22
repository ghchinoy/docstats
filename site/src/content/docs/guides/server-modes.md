---
title: Server Modes
description: The three ways to run docstats — MCP STDIO, FastAPI REST, and MCP streamable HTTP — with launch commands and guidance on when to use each.
sidebar:
  order: 1
---

docstats supports three execution modes from a single entry point. All three expose the same analysis engine, so the two-axis results are identical regardless of transport.

## Architecture

```
                  +--------------------------------+
                  |         Text Sources           |
                  |  (Direct Text / URL / GCS PDF) |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |      Extraction Pipeline       |
                  |  (BeautifulSoup4 / PyPDF / GCS)|
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |         Analysis Engine        |
                  | (Axis A: Metrics / Axis B: AI) |
                  +---------------+----------------+
                                  |
        +-------------------------+-------------------------+
        |                         |                         |
        v                         v                         v
+---------------+         +---------------+         +---------------+
|  FastAPI REST |         |   MCP STDIO   |         | MCP HTTP / SSE|
| (Port 8000)   |         | (Agent Subproc|         | (Port 8001)   |
+---------------+         +---------------+         +---------------+
```

## Which mode should I use?

| Mode | Best for | Transport |
|---|---|---|
| **MCP STDIO** | AI agent runtimes running docstats as a subprocess (Claude Code, Gemini CLI, Cursor, Antigravity). | JSON-RPC over stdin/stdout |
| **FastAPI REST** | Local development, scripts, CI pipelines, and anything that speaks HTTP + JSON. | HTTP with Swagger docs |
| **MCP Streamable HTTP** | Remote or shared MCP deployments where a subprocess is not practical. | HTTP with SSE or plain JSON |

## MCP STDIO server

The primary interface for AI agent runtimes. Communicates over standard input/output using JSON-RPC.

```bash
uv run python main.py --server-type mcp
```

See [MCP & Agent Plugins](/docstats/integrations/mcp/) for client configuration.

## FastAPI REST server

A standard RESTful API with interactive Swagger / OpenAPI docs. Recommended for development with auto-reload:

```bash
uv run uvicorn fastapi_app:fastapi_app --host 127.0.0.1 --port 8000 --reload
```

Interactive Swagger UI opens at `http://127.0.0.1:8000/docs`. See the [REST API](/docstats/integrations/rest-api/) reference for endpoints and payloads.

## MCP streamable HTTP server

Exposes the MCP server over HTTP using Server-Sent Events (SSE) or plain JSON responses.

```bash
# SSE streaming
uv run python main.py --server-type mcp-http --host 127.0.0.1 --port 8001

# Plain JSON responses
uv run python main.py --server-type mcp-http --mcp-http-json-response --host 127.0.0.1 --port 8001
```
