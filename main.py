# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import contextlib
import logging
from typing import AsyncIterator

import anyio
import uvicorn

# MCP Imports
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

# Starlette imports for MCP HTTP
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

# Local Imports
from mcp_server import InMemoryEventStore, mcp_generic_app, mcp_http_app

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Docstats Server")

    parser.add_argument(
        "--server-type", choices=["fastapi", "mcp", "mcp-http"], default="fastapi"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--mcp-http-json-response", action="store_true")

    cli_args = parser.parse_args()

    if cli_args.server_type == "fastapi":
        logger.info(f"Starting FastAPI server on {cli_args.host}:{cli_args.port}...")
        uvicorn.run(
            "fastapi_app:fastapi_app",
            host=cli_args.host,
            port=cli_args.port,
            reload=True,
            timeout_graceful_shutdown=2,
        )

    elif cli_args.server_type == "mcp":
        logger.info("Starting MCP STDIO server...")

        async def run_mcp_stdio():
            """Runs the MCP server using standard input/output streams."""
            logger.info("MCP STDIO server: Waiting for messages on stdin/stdout.")
            async with stdio_server() as streams:
                await mcp_generic_app.run(
                    streams[0],
                    streams[1],
                    mcp_generic_app.create_initialization_options(),
                )
            logger.info("MCP STDIO server shut down.")

        try:
            anyio.run(run_mcp_stdio)
        except Exception as e:
            logger.error(f"Error running MCP STDIO server: {e}", exc_info=True)

    elif cli_args.server_type == "mcp-http":
        logger.info(
            f"Starting MCP Streamable HTTP server on {cli_args.host}:{cli_args.port}..."
        )
        event_store = InMemoryEventStore()
        session_manager = StreamableHTTPSessionManager(
            mcp_http_app, event_store, cli_args.mcp_http_json_response
        )

        async def handle_asgi(scope: Scope, receive: Receive, send: Send):
            """Handles incoming ASGI requests for the MCP HTTP server."""
            await session_manager.handle_request(scope, receive, send)

        @contextlib.asynccontextmanager
        async def lifespan(_app: Starlette) -> AsyncIterator[None]:
            """Manages the lifecycle of the MCP HTTP server."""
            async with session_manager.run():
                yield

        starlette_app = Starlette(
            debug=True, routes=[Mount("/mcp", handle_asgi)], lifespan=lifespan
        )
        uvicorn.run(
            starlette_app,
            host=cli_args.host,
            port=cli_args.port,
            timeout_graceful_shutdown=2,
        )
    else:
        logger.error(f"Unknown server type: {cli_args.server_type}")
