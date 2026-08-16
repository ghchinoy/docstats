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

import logging
from collections import deque
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import mcp.types as mcp_sdk_types
from mcp.server.lowlevel import Server as MCPLowLevelServer
from mcp.server.streamable_http import (
    EventCallback,
    EventId,
    EventMessage,
    EventStore,
    StreamId,
)
from mcp.types import JSONRPCMessage

from extraction import get_processed_text
from metrics import (
    analyze_document_logic,
    calculate_ai_patterns_logic,
    calculate_readability_metrics_logic,
)
from models import TextSourceModel

logger = logging.getLogger(__name__)


def get_readability_tool_schema() -> mcp_sdk_types.Tool:
    """Returns the MCP tool schema for readability scores (Axis A)."""
    return mcp_sdk_types.Tool(
        name="get_readability_scores",
        description=(
            "Calculates readability scores (Axis A) for text from direct input, "
            "a web URL, or a GCS PDF URI."
        ),
        inputSchema=TextSourceModel.model_json_schema(),
    )


def get_ai_patterns_tool_schema() -> mcp_sdk_types.Tool:
    """Returns the MCP tool schema for AI writing pattern detection (Axis B)."""
    return mcp_sdk_types.Tool(
        name="get_ai_pattern_scores",
        description=(
            "Detects AI writing patterns and calculates Axis B editorial tell scores "
            "for text from direct input, a web URL, or a GCS PDF URI."
        ),
        inputSchema=TextSourceModel.model_json_schema(),
    )


def get_analyze_document_tool_schema() -> mcp_sdk_types.Tool:
    """Returns the MCP tool schema for two-axis analysis (Axis A + Axis B)."""
    return mcp_sdk_types.Tool(
        name="analyze_document",
        description=(
            "Performs comprehensive two-axis document assessment: Axis A "
            "readability scores and Axis B AI writing pattern detection for "
            "text from direct input, a web URL, or a GCS PDF URI."
        ),
        inputSchema=TextSourceModel.model_json_schema(),
    )


async def execute_readability_tool(
    arguments: dict, ctx: Any
) -> list[mcp_sdk_types.TextContent]:
    """Executes the readability tool logic for MCP."""
    try:
        input_data = TextSourceModel(**arguments)
        processed_text, source_desc = await get_processed_text(input_data)
        scores_model = await calculate_readability_metrics_logic(
            processed_text, source_desc
        )
        return [
            mcp_sdk_types.TextContent(type="text", text=scores_model.model_dump_json())
        ]
    except ValueError as e:
        logger.error(f"MCP Tool Error (ValueError): {e}", exc_info=True)
        return [
            mcp_sdk_types.TextContent(
                type="text", text=f'{{"error": "ValueError", "detail": "{str(e)}"}}'
            )
        ]
    except Exception as e:
        logger.error(f"MCP Tool Error (Exception): {e}", exc_info=True)
        return [
            mcp_sdk_types.TextContent(
                type="text",
                text=f'{{"error": "Internal Server Error", "detail": "{str(e)}"}}',
            )
        ]


async def execute_ai_patterns_tool(
    arguments: dict, ctx: Any
) -> list[mcp_sdk_types.TextContent]:
    """Executes the AI writing pattern detection tool logic for MCP."""
    try:
        input_data = TextSourceModel(**arguments)
        processed_text, source_desc = await get_processed_text(input_data)
        patterns_model = await calculate_ai_patterns_logic(processed_text, source_desc)
        return [
            mcp_sdk_types.TextContent(
                type="text", text=patterns_model.model_dump_json()
            )
        ]
    except ValueError as e:
        logger.error(f"MCP Tool Error (ValueError): {e}", exc_info=True)
        return [
            mcp_sdk_types.TextContent(
                type="text", text=f'{{"error": "ValueError", "detail": "{str(e)}"}}'
            )
        ]
    except Exception as e:
        logger.error(f"MCP Tool Error (Exception): {e}", exc_info=True)
        return [
            mcp_sdk_types.TextContent(
                type="text",
                text=f'{{"error": "Internal Server Error", "detail": "{str(e)}"}}',
            )
        ]


async def execute_analyze_document_tool(
    arguments: dict, ctx: Any
) -> list[mcp_sdk_types.TextContent]:
    """Executes the combined two-axis document analysis tool logic for MCP."""
    try:
        input_data = TextSourceModel(**arguments)
        processed_text, source_desc = await get_processed_text(input_data)
        analysis_model = await analyze_document_logic(processed_text, source_desc)
        return [
            mcp_sdk_types.TextContent(
                type="text", text=analysis_model.model_dump_json()
            )
        ]
    except ValueError as e:
        logger.error(f"MCP Tool Error (ValueError): {e}", exc_info=True)
        return [
            mcp_sdk_types.TextContent(
                type="text", text=f'{{"error": "ValueError", "detail": "{str(e)}"}}'
            )
        ]
    except Exception as e:
        logger.error(f"MCP Tool Error (Exception): {e}", exc_info=True)
        return [
            mcp_sdk_types.TextContent(
                type="text",
                text=f'{{"error": "Internal Server Error", "detail": "{str(e)}"}}',
            )
        ]


# --- MCP Generic Server ---
mcp_generic_app = MCPLowLevelServer("docstats-mcp-generic")


@mcp_generic_app.list_tools()
async def list_tools_generic(*args) -> list[mcp_sdk_types.Tool]:
    """Lists available tools for the generic MCP server."""
    return [
        get_readability_tool_schema(),
        get_ai_patterns_tool_schema(),
        get_analyze_document_tool_schema(),
    ]


@mcp_generic_app.call_tool()
async def call_tool_generic(
    name: str, args_dict: dict
) -> list[mcp_sdk_types.TextContent]:
    """Calls a specific tool for the generic MCP server."""
    try:
        ctx = mcp_generic_app.request_context
    except LookupError:
        ctx = None
    if name == "get_readability_scores":
        return await execute_readability_tool(args_dict, ctx)
    if name == "get_ai_pattern_scores":
        return await execute_ai_patterns_tool(args_dict, ctx)
    if name == "analyze_document":
        return await execute_analyze_document_tool(args_dict, ctx)
    raise NotImplementedError(f"Tool {name} not found.")


# --- MCP HTTP Server Components ---
@dataclass
class EventEntry:
    """Represents an entry in the MCP HTTP event stream."""

    event_id: EventId
    stream_id: StreamId
    message: JSONRPCMessage


class InMemoryEventStore(EventStore):
    """In-memory store for MCP HTTP events."""

    def __init__(self, max_events_per_stream: int = 100):
        """Initializes the in-memory event store with a max event limit."""
        self.max_events = max_events_per_stream
        self.streams: dict[StreamId, deque[EventEntry]] = {}
        self.event_map: dict[EventId, EventEntry] = {}

    async def store_event(
        self, stream_id: StreamId, message: JSONRPCMessage
    ) -> EventId:
        """Stores an event message in the given stream."""
        eid = str(uuid4())
        entry = EventEntry(event_id=eid, stream_id=stream_id, message=message)
        if stream_id not in self.streams:
            self.streams[stream_id] = deque(maxlen=self.max_events)
        self.streams[stream_id].append(entry)
        self.event_map[eid] = entry
        return eid

    async def replay_events_after(
        self,
        last_eid: EventId,
        cb: EventCallback,
    ) -> StreamId | None:
        """Replays all events in a stream that occurred after last_eid."""
        last_event = self.event_map.get(last_eid)
        if not last_event:
            return None
        found = False
        for event in self.streams.get(last_event.stream_id, deque()):
            if found:
                await cb(EventMessage(event.message, event.event_id))
            elif event.event_id == last_eid:
                found = True
        return last_event.stream_id


mcp_http_app = MCPLowLevelServer("docstats-mcp-http")


@mcp_http_app.list_tools()
async def list_tools_http(*args) -> list[mcp_sdk_types.Tool]:
    """Lists available tools for the HTTP MCP server."""
    return [
        get_readability_tool_schema(),
        get_ai_patterns_tool_schema(),
        get_analyze_document_tool_schema(),
    ]


@mcp_http_app.call_tool()
async def call_tool_http(name: str, args_dict: dict) -> list[mcp_sdk_types.TextContent]:
    """Calls a specific tool for the HTTP MCP server."""
    try:
        ctx = mcp_http_app.request_context
    except LookupError:
        ctx = None
    if name == "get_readability_scores":
        return await execute_readability_tool(args_dict, ctx)
    if name == "get_ai_pattern_scores":
        return await execute_ai_patterns_tool(args_dict, ctx)
    if name == "analyze_document":
        return await execute_analyze_document_tool(args_dict, ctx)
    raise NotImplementedError(f"Tool {name} not found.")
