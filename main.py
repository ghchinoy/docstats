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


# main.py
# Description: A FastAPI and MCP application to calculate text readability scores.

import argparse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List, AsyncIterator
import uvicorn
import logging
import io
import asyncio
import textstat
from readability import Readability
from google.cloud import storage
import PyPDF2
import requests
from bs4 import BeautifulSoup
import contextlib
from collections import deque
from uuid import uuid4
from dataclasses import dataclass
import anyio # For MCP STDIO server

# MCP Imports
import mcp.types as mcp_sdk_types
from mcp.server.lowlevel import Server as MCPLowLevelServer
from mcp.server.stdio import stdio_server # For MCP STDIO server
from mcp.server.streamable_http import (
    EventCallback, EventId, EventMessage, EventStore, StreamId
)
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import JSONRPCMessage

# Starlette imports for MCP HTTP
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Pydantic Models ---
class TextSourceModel(BaseModel):
    text: Optional[str] = Field(None, min_length=1)
    web_url: Optional[str] = Field(None)
    gcs_pdf_uri: Optional[str] = Field(None)

    @model_validator(mode='before')
    @classmethod
    def check_exclusive_source(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        provided_sources = [s for s in ['text', 'web_url', 'gcs_pdf_uri'] if values.get(s)]
        if len(provided_sources) != 1: raise ValueError("Exactly one of text, web_url, or gcs_pdf_uri must be provided.")
        if values.get('gcs_pdf_uri') and not values['gcs_pdf_uri'].startswith('gs://'):
            raise ValueError("gcs_pdf_uri must be a valid gs:// URI.")
        return values

class ReadabilityScoresModel(BaseModel):
    flesch_reading_ease: Optional[float] = None
    flesch_kincaid_grade: Optional[float] = None
    gunning_fog: Optional[float] = None
    smog_index: Optional[float] = None
    automated_readability_index: Optional[float] = None
    coleman_liau_index: Optional[float] = None
    linsear_write_formula: Optional[float] = None
    dale_chall_readability_score: Optional[float] = None
    text_standard: Optional[str] = None
    spache: Optional[float] = None
    syllable_count: int
    word_count: int
    sentence_count: int

# --- Core Readability Logic ---
async def extract_text_from_gcs_pdf(gcs_uri: str) -> str:
    try:
        storage_client = storage.Client()
        bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
        blob = storage_client.bucket(bucket_name).blob(blob_name)
        pdf_bytes = await asyncio.to_thread(blob.download_as_bytes)
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = "".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip(): raise ValueError("No text in PDF.")
        return text
    except Exception as e: raise ValueError(f"GCS PDF error ({gcs_uri}): {e}")

async def get_processed_text(source: TextSourceModel) -> tuple[str, str]:
    if source.text: return source.text, "direct text"
    if source.web_url:
        try:
            response = await asyncio.to_thread(requests.get, source.web_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            article = soup.find('article') or soup.find('main')
            text = (article or soup.body).get_text(separator=' ', strip=True) if (article or soup.body) else ""
            if not text.strip(): raise ValueError("No text from URL.")
            return text, f"URL: {source.web_url}"
        except Exception as e: raise ValueError(f"Web URL error ({source.web_url}): {e}")
    if source.gcs_pdf_uri:
        text = await extract_text_from_gcs_pdf(source.gcs_pdf_uri)
        return text, f"GCS: {source.gcs_pdf_uri}"
    raise ValueError("Invalid source.")

async def calculate_readability_metrics_logic(text: str, src_desc: str) -> ReadabilityScoresModel:
    if not text.strip(): raise ValueError("Empty text.")
    wc = textstat.lexicon_count(text)
    if wc == 0: raise ValueError("Zero words.")
    if wc < 100: logger.warning(f"{src_desc} <100 words.")
    return ReadabilityScoresModel(
        syllable_count=textstat.syllable_count(text), word_count=wc, sentence_count=textstat.sentence_count(text),
        flesch_reading_ease=textstat.flesch_reading_ease(text), flesch_kincaid_grade=textstat.flesch_kincaid_grade(text),
        gunning_fog=textstat.gunning_fog(text), smog_index=textstat.smog_index(text),
        automated_readability_index=textstat.automated_readability_index(text),
        coleman_liau_index=textstat.coleman_liau_index(text), linsear_write_formula=textstat.linsear_write_formula(text),
        \
        dale_chall_readability_score=textstat.dale_chall_readability_score(text),
        text_standard=str(textstat.text_standard(text, float_output=True)),
        # spache=Readability(text).spache().score if wc > 0 else None
    )
    
    spache_score = None
    if wc > 0:
        try:
            spache_score = Readability(text).spache().score
        except Exception as e:
            if "100 words required" in str(e).lower():
                logger.warning(f"Spache score could not be calculated for '{src_desc}': {e}")
            \
            else:
                # If it's a different error, log it, but spache_score will remain None
                logger.error(f"Unexpected Spache Error for '{src_desc}'. Type: {type(e)}, Msg: {str(e)}", exc_info=True)
                spache_score = None # Ensure it's None on other errors too
    
    # Update the model with the (potentially None) spache_score
    # This assumes ReadabilityScoresModel can be updated or re-created.
    # A more robust way would be to build the dict of scores first, then create the model.
    # For simplicity here, let's assume we can create it then update, or pass spache_score at creation.
    # Let's refine the model creation to include spache_score directly.

    scores_dict = {
        "syllable_count": textstat.syllable_count(text), "word_count": wc, "sentence_count": textstat.sentence_count(text),
        "flesch_reading_ease": textstat.flesch_reading_ease(text), "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
        "gunning_fog": textstat.gunning_fog(text), "smog_index": textstat.smog_index(text),
        "automated_readability_index": textstat.automated_readability_index(text),
        "coleman_liau_index": textstat.coleman_liau_index(text), "linsear_write_formula": textstat.linsear_write_formula(text),
        "dale_chall_readability_score": textstat.dale_chall_readability_score(text),
        "text_standard": str(textstat.text_standard(text, float_output=True)),
        "spache": spache_score
    }
    return ReadabilityScoresModel(**scores_dict)

# --- FastAPI App ---
fastapi_app = FastAPI(title="Readability API", version="1.3.9") # Version bump
@fastapi_app.post("/scores/", response_model=ReadabilityScoresModel)
async def scores_fastapi(req: TextSourceModel):
    try:
        text, desc = await get_processed_text(req)
        return await calculate_readability_metrics_logic(text, desc)
    except ValueError as e: raise HTTPException(422, str(e))
    except Exception as e: logger.error(f"FastAPI error: {e}", exc_info=True); raise HTTPException(500, "Server error.")

# --- MCP Tool Definition Logic (shared by generic and http MCP servers) ---
def get_readability_tool_schema() -> mcp_sdk_types.Tool:
    return mcp_sdk_types.Tool(
        name="get_readability_scores",
        description="Calculates readability scores for text from direct input, a web URL, or a GCS PDF URI.",
        inputSchema=TextSourceModel.model_json_schema()
    )

async def execute_readability_tool(arguments: dict, ctx: Any) -> list[mcp_sdk_types.TextContent]:
    try:
        input_data = TextSourceModel(**arguments)
        processed_text, source_desc = await get_processed_text(input_data)
        scores_model = await calculate_readability_metrics_logic(processed_text, source_desc)
        return [mcp_sdk_types.TextContent(type="text", text=scores_model.model_dump_json())]
    except ValueError as e:
        logger.error(f"MCP Tool Error (ValueError): {e}", exc_info=True)
        return [mcp_sdk_types.TextContent(type="text", text=f'{{"error": "ValueError", "detail": "{str(e)}"}}')]
    except Exception as e:
        logger.error(f"MCP Tool Error (Exception): {e}", exc_info=True)
        return [mcp_sdk_types.TextContent(type="text", text=f'{{"error": "Internal Server Error", "detail": "{str(e)}"}}')]

# --- MCP Generic Server Instance (for STDIO mode or `mcp serve`) ---
mcp_generic_app = MCPLowLevelServer("docstats-mcp-generic")
@mcp_generic_app.list_tools()
async def list_tools_generic(*args) -> list[mcp_sdk_types.Tool]: 
    return [get_readability_tool_schema()]
\
@mcp_generic_app.call_tool()
async def call_tool_generic(name: str, args_dict: dict) -> list[mcp_sdk_types.TextContent]: 
    ctx = mcp_generic_app.request_context
    if name == "get_readability_scores": return await execute_readability_tool(args_dict, ctx)
    raise NotImplementedError(f"Tool {name} not found.")

# --- MCP Streamable HTTP Server Instance ---
@dataclass
class EventEntry: event_id: EventId; stream_id: StreamId; message: JSONRPCMessage

class InMemoryEventStore(EventStore):
    def __init__(self, max_events_per_stream: int = 100):
        self.max_events_per_stream = max_events_per_stream
        self.streams: dict[StreamId, deque[EventEntry]] = {}
        self.event_index: dict[EventId, EventEntry] = {}
    async def store_event(self, stream_id: StreamId, msg: JSONRPCMessage) -> EventId:
        eid = str(uuid4()); entry = EventEntry(eid, stream_id, msg)
        if stream_id not in self.streams: self.streams[stream_id] = deque(maxlen=self.max_events_per_stream)
        if len(self.streams[stream_id]) == self.max_events_per_stream:
            self.event_index.pop(self.streams[stream_id][0].event_id, None)
        self.streams[stream_id].append(entry); self.event_index[eid] = entry
        return eid
    async def replay_events_after(self, last_eid: EventId, cb: EventCallback) -> StreamId | None:
        if last_eid not in self.event_index: return None
        last_event = self.event_index[last_eid]; found = False
        for event in self.streams.get(last_event.stream_id, deque()):
            if found: await cb(EventMessage(event.message, event.event_id))
            elif event.event_id == last_eid: found = True
        return last_event.stream_id

mcp_http_app = MCPLowLevelServer("docstats-mcp-http")
@mcp_http_app.list_tools()
async def list_tools_http(*args) -> list[mcp_sdk_types.Tool]: 
    return [get_readability_tool_schema()]
\
@mcp_http_app.call_tool()
async def call_tool_http(name: str, args_dict: dict) -> list[mcp_sdk_types.TextContent]: 
    ctx = mcp_http_app.request_context
    if name == "get_readability_scores": return await execute_readability_tool(args_dict, ctx)
    raise NotImplementedError(f"Tool {name} not found.")

# --- Main Application Runner ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Docstats Server")
    
    parser.add_argument("--server-type", choices=["fastapi", "mcp", "mcp-http"], default="fastapi")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--mcp-http-json-response", action="store_true")
    
    cli_args = parser.parse_args()

    if cli_args.server_type == "fastapi":
        logger.info(f"Starting FastAPI server on {cli_args.host}:{cli_args.port}...")
        uvicorn.run(fastapi_app, host=cli_args.host, port=cli_args.port, reload=True, timeout_graceful_shutdown=2)
    
    elif cli_args.server_type == "mcp":
        logger.info("Starting MCP STDIO server...")
        async def run_mcp_stdio():
            logger.info("MCP STDIO server: Waiting for messages on stdin/stdout.")
            async with stdio_server() as streams:
                await mcp_generic_app.run(
                    streams[0], 
                    streams[1], 
                    mcp_generic_app.create_initialization_options()
                )
            logger.info("MCP STDIO server shut down.")
        try:
            anyio.run(run_mcp_stdio)
        except Exception as e:
            logger.error(f"Error running MCP STDIO server: {e}", exc_info=True)

    elif cli_args.server_type == "mcp-http":
        logger.info(f"Starting MCP Streamable HTTP server on {cli_args.host}:{cli_args.port}...")
        event_store = InMemoryEventStore()
        session_manager = StreamableHTTPSessionManager(mcp_http_app, event_store, cli_args.mcp_http_json_response)
        async def handle_asgi(scope: Scope, receive: Receive, send: Send): await session_manager.handle_request(scope, receive, send)
        @contextlib.asynccontextmanager
        async def lifespan(_app: Starlette) -> AsyncIterator[None]:
            async with session_manager.run(): yield
        starlette_app = Starlette(debug=True, routes=[Mount("/mcp", handle_asgi)], lifespan=lifespan)
        uvicorn.run(starlette_app, host=cli_args.host, port=cli_args.port, timeout_graceful_shutdown=2)
    else: 
        logger.error(f"Unknown server type: {cli_args.server_type}")