---
title: Server Modes
description: Execution options for docstats, including MCP STDIO, FastAPI REST, and MCP streamable HTTP.
sidebar:
  order: 1
---

docstats supports three execution modes from a single entry point. Each mode exposes identical analysis engine logic, guaranteeing consistent metrics regardless of transport.

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

## Mode Comparison

| Mode | Target Use Case | Transport |
|---|---|---|
| **MCP STDIO** | AI agent subprocesses (Claude Code, Gemini CLI, Cursor, Antigravity). | JSON-RPC over stdin/stdout |
| **FastAPI REST** | Local development, scripts, CI pipelines, and HTTP integrations. | HTTP with OpenAPI/Swagger |
| **MCP Streamable HTTP** | Remote or shared agent deployments. | HTTP with SSE or JSON |

## MCP STDIO Server

Communicates over standard input and output using JSON-RPC. This is the default integration for local AI coding agents.

```bash
uv run python main.py --server-type mcp
```

See [MCP & Agent Plugins](/docstats/integrations/mcp/) for configuration details across client environments.

## FastAPI REST Server

Provides a REST API with OpenAPI documentation for web services and automated pipelines:

```bash
uv run uvicorn fastapi_app:fastapi_app --host 127.0.0.1 --port 8000 --reload
```

Interactive documentation is available at `http://127.0.0.1:8000/docs`. See the [REST API](/docstats/integrations/rest-api/) reference for endpoint specifications.

## MCP Streamable HTTP Server

Serves MCP requests over HTTP using Server-Sent Events (SSE) or standard JSON responses:

```bash
# SSE streaming mode
uv run python main.py --server-type mcp-http --host 127.0.0.1 --port 8001

# Standard JSON response mode
uv run python main.py --server-type mcp-http --mcp-http-json-response --host 127.0.0.1 --port 8001
```
