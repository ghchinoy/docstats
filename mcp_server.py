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
from metrics import calculate_readability_metrics_logic
from models import TextSourceModel

logger = logging.getLogger(__name__)

def get_readability_tool_schema() -> mcp_sdk_types.Tool:
    """Returns the MCP tool schema for readability scores."""
    return mcp_sdk_types.Tool(
        name="get_readability_scores",
        description=(
            "Calculates readability scores for text from direct input, "
            "a web URL, or a GCS PDF URI."
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


# --- MCP Generic Server ---
mcp_generic_app = MCPLowLevelServer("docstats-mcp-generic")


@mcp_generic_app.list_tools()
async def list_tools_generic(*args) -> list[mcp_sdk_types.Tool]:
    """Lists available tools for the generic MCP server."""
    return [get_readability_tool_schema()]


@mcp_generic_app.call_tool()
async def call_tool_generic(
    name: str, args_dict: dict
) -> list[mcp_sdk_types.TextContent]:
    """Calls a specific tool for the generic MCP server."""
    ctx = mcp_generic_app.request_context
    if name == "get_readability_scores":
        return await execute_readability_tool(args_dict, ctx)
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
        """Initializes the in-memory event store."""
        self.max_events_per_stream = max_events_per_stream
        self.streams: dict[StreamId, deque[EventEntry]] = {}
        self.event_index: dict[EventId, EventEntry] = {}

    async def store_event(self, stream_id: StreamId, msg: JSONRPCMessage) -> EventId:
        """Stores an event in the specified stream."""
        eid = str(uuid4())
        entry = EventEntry(eid, stream_id, msg)
        if stream_id not in self.streams:
            self.streams[stream_id] = deque(maxlen=self.max_events_per_stream)
        if len(self.streams[stream_id]) == self.max_events_per_stream:
            self.event_index.pop(self.streams[stream_id][0].event_id, None)
        self.streams[stream_id].append(entry)
        self.event_index[eid] = entry
        return eid

    async def replay_events_after(
        self, last_eid: EventId, cb: EventCallback
    ) -> StreamId | None:
        """Replays events in a stream after a specified event ID."""
        if last_eid not in self.event_index:
            return None
        last_event = self.event_index[last_eid]
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
    return [get_readability_tool_schema()]


@mcp_http_app.call_tool()
async def call_tool_http(name: str, args_dict: dict) -> list[mcp_sdk_types.TextContent]:
    """Calls a specific tool for the HTTP MCP server."""
    ctx = mcp_http_app.request_context
    if name == "get_readability_scores":
        return await execute_readability_tool(args_dict, ctx)
    raise NotImplementedError(f"Tool {name} not found.")
