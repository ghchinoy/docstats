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

"""MCP client wrapper for docstats STDIO server.

Provides programmatic client-side access to `analyze_document`,
`get_readability_scores`, and `get_ai_pattern_scores` via the official MCP SDK.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

DOCSTATS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class DocstatsMCPClient:
    """Manages an active MCP connection to the docstats STDIO server."""

    def __init__(self, server_root: str = DOCSTATS_ROOT):
        """Initializes the MCP client with the repository root path."""
        self.server_root = server_root
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "main.py", "--server-type", "mcp"],
            cwd=self.server_root,
        )

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Spawns an STDIO MCP session, calls tool, and parses JSON output."""
        async with stdio_client(self.server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                response = await session.call_tool(tool_name, arguments=arguments)

                if not response.content:
                    return {"error": "Empty response from MCP tool"}

                first_content = response.content[0]
                text_output = getattr(first_content, "text", "")
                try:
                    return json.loads(text_output)
                except json.JSONDecodeError:
                    return {"raw_text": text_output}

    async def analyze_document(
        self,
        text: Optional[str] = None,
        web_url: Optional[str] = None,
        gcs_pdf_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convenience method to invoke `analyze_document` on text/url/gcs."""
        args: Dict[str, Any] = {}
        if text:
            args["text"] = text
        elif web_url:
            args["web_url"] = web_url
        elif gcs_pdf_uri:
            args["gcs_pdf_uri"] = gcs_pdf_uri
        else:
            raise ValueError(
                "Must provide exactly one of text, web_url, or gcs_pdf_uri."
            )

        return await self.call_tool("analyze_document", args)

    async def get_readability_scores(
        self, text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convenience method to invoke `get_readability_scores`."""
        return await self.call_tool("get_readability_scores", {"text": text})

    async def get_ai_pattern_scores(self, text: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method to invoke `get_ai_pattern_scores`."""
        return await self.call_tool("get_ai_pattern_scores", {"text": text})
