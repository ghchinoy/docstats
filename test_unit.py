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

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_patterns import (
    TECHNICAL_ADVERBS,
    analyze_adverbs,
    count_em_dashes_in_prose,
    detect_ai_patterns,
    strip_code_and_tables,
)
from extraction import get_processed_text
from fastapi_app import fastapi_app
from fastapi.testclient import TestClient
from mcp_server import (
    InMemoryEventStore,
    call_tool_generic,
    call_tool_http,
    execute_ai_patterns_tool,
    execute_analyze_document_tool,
    execute_readability_tool,
    list_tools_generic,
    list_tools_http,
)
from metrics import (
    analyze_document_logic,
    calculate_ai_patterns_logic,
    calculate_readability_metrics_logic,
)
from models import (
    AIPatternScoresModel,
    DocumentAnalysisModel,
    ReadabilityScoresModel,
    TextSourceModel,
)


@pytest.mark.asyncio
async def test_get_processed_text_direct():
    """Verifies direct text extraction without external calls."""
    source = TextSourceModel(text="Hello world test.")
    text, desc = await get_processed_text(source)
    assert text == "Hello world test."
    assert desc == "direct text"


@pytest.mark.asyncio
async def test_get_processed_text_web_mock(mocker):
    """Verifies web extraction logic using mocks."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = (
        b"<html><body><article>Mocked Article Content</article></body></html>"
    )
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.raise_for_status = MagicMock()

    # Mock the httpx AsyncClient.get
    mock_get = mocker.patch("httpx.AsyncClient.get", new_callable=AsyncMock)
    mock_get.return_value = mock_response

    source = TextSourceModel(web_url="http://mock-url.com")
    text, desc = await get_processed_text(source)

    assert "Mocked Article Content" in text
    assert "URL: http://mock-url.com" == desc
    mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_processed_text_gcs_mock(mocker):
    """Verifies GCS extraction logic using mocks."""
    mock_blob = MagicMock()
    mock_blob.download_as_bytes = MagicMock(return_value=b"mock pdf bytes")

    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket

    mocker.patch("extraction.get_storage_client", return_value=mock_client)

    # Mock pypdf reader to avoid binary parsing of "mock pdf bytes"
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Extracted PDF Text"

    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]
    mocker.patch("pypdf.PdfReader", return_value=mock_reader)

    source = TextSourceModel(gcs_pdf_uri="gs://mock-bucket/file.pdf")
    text, desc = await get_processed_text(source)

    assert text == "Extracted PDF Text"
    assert "GCS: gs://mock-bucket/file.pdf" == desc


@pytest.mark.asyncio
async def test_get_processed_text_invalid_gcs_uri():
    """Verifies that malformed GCS URIs raise an appropriate ValueError."""
    source = TextSourceModel(gcs_pdf_uri="gs://bucket-without-path")
    with pytest.raises(ValueError, match="Invalid GCS PDF URI"):
        await get_processed_text(source)


@pytest.mark.asyncio
async def test_metrics_empty_text():
    """Verifies that calculating metrics on empty text raises ValueError."""
    with pytest.raises(ValueError, match="Empty text"):
        await calculate_readability_metrics_logic("", "test")


@pytest.mark.asyncio
async def test_metrics_short_text():
    """Verifies metric calculation on short text."""
    scores = await calculate_readability_metrics_logic(
        "The quick brown fox jumps over the lazy dog.", "test"
    )
    assert scores.word_count == 9
    assert scores.spache is None
    assert isinstance(scores.flesch_reading_ease, float)


@pytest.mark.asyncio
async def test_execute_readability_tool_mock(mocker):
    """Verifies the MCP tool execution with mocked logic."""
    mocker.patch(
        "mcp_server.get_processed_text",
        return_value=("Sample text for tool test.", "mock source"),
    )

    mock_scores = ReadabilityScoresModel(
        syllable_count=5,
        word_count=5,
        sentence_count=1,
        flesch_reading_ease=100.0,
        flesch_kincaid_grade=1.0,
        spache=1.0,
    )
    mocker.patch(
        "mcp_server.calculate_readability_metrics_logic",
        return_value=mock_scores,
    )

    arguments = {"text": "This is a test."}
    result = await execute_readability_tool(arguments, ctx=None)

    assert len(result) == 1
    assert result[0].type == "text"
    assert "flesch_reading_ease" in result[0].text
    assert "100.0" in result[0].text


@pytest.mark.asyncio
async def test_execute_readability_tool_validation_error():
    """Verifies that tool execution handles validation errors with error JSON."""
    arguments = {}  # Missing required exclusive source
    result = await execute_readability_tool(arguments, ctx=None)
    assert len(result) == 1
    assert result[0].type == "text"
    assert "ValueError" in result[0].text


@pytest.mark.asyncio
async def test_mcp_tool_listing_and_calling(mocker):
    """Verifies MCP server tool listing and dispatch."""
    tools_generic = await list_tools_generic()
    tool_names_generic = [t.name for t in tools_generic]
    assert "get_readability_scores" in tool_names_generic
    assert "get_ai_pattern_scores" in tool_names_generic
    assert "analyze_document" in tool_names_generic

    tools_http = await list_tools_http()
    tool_names_http = [t.name for t in tools_http]
    assert "get_readability_scores" in tool_names_http
    assert "get_ai_pattern_scores" in tool_names_http
    assert "analyze_document" in tool_names_http

    with pytest.raises(NotImplementedError):
        await call_tool_generic("unknown_tool", {})

    with pytest.raises(NotImplementedError):
        await call_tool_http("unknown_tool", {})


@pytest.mark.asyncio
async def test_in_memory_event_store():
    """Verifies event storage and retrieval in InMemoryEventStore."""
    store = InMemoryEventStore(max_events_per_stream=5)
    stream_id = "test-stream"
    msg = {"jsonrpc": "2.0", "method": "test"}

    eid = await store.store_event(stream_id, msg)
    assert eid is not None
    assert stream_id in store.streams
    assert len(store.streams[stream_id]) == 1

    received_events = []

    async def callback(evt):
        received_events.append(evt)

    # Replaying unknown event returns None
    result = await store.replay_events_after("non-existent-id", callback)
    assert result is None


# --- AI Pattern Detection Tests ---


def test_strip_code_and_tables():
    """Verifies that code blocks, inline code, and tables are stripped."""
    text = (
        "Here is some text.\n"
        "```python\n"
        "# Notably, this is code with — em dash\n"
        "def foo(): pass\n"
        "```\n"
        "And inline `code_block — with em-dash` here.\n"
        "| Col1 | Col2 |\n"
        "|---|---|\n"
        "| Cell 1 — notably | Cell 2 |\n"
        "Final clean line."
    )
    stripped = strip_code_and_tables(text)
    assert "def foo" not in stripped
    assert "Col1" not in stripped
    assert "Final clean line." in stripped


def test_em_dash_softening_and_detection():
    """Verifies em dash detection and softening for reasonable usage."""
    # 1. Clean text with 1 reasonable em dash in a ~100 word paragraph (should have 0 or minor penalty)
    reasonable_text = (
        "We configured the database engine to run in server mode — a necessary step "
        "for multi-agent concurrent operations. Each worker connects directly to the port "
        "and coordinates state through Dolt transactions. This architecture isolates the locks "
        "and guarantees data persistence across sessions without rollbacks or corruption. "
        "The team verified this in automated integration tests over the past three releases."
    )
    patterns = detect_ai_patterns(reasonable_text, 65)
    assert patterns.em_dash_count == 1
    # 1 em dash in 65 words is rate ~1.54, but ai_tell_score should remain high (> 7.0)
    assert patterns.ai_tell_score >= 7.0

    # 2. Heavy AI tell: 4 em dashes in 40 words
    slop_text = (
        "The migration is loud — it tells us what broke — because the system isn't just software — "
        "it's behavior — and that changes everything."
    )
    slop_patterns = detect_ai_patterns(slop_text, 25)
    assert slop_patterns.em_dash_count == 4
    assert slop_patterns.ai_tell_score < 7.0


def test_technical_adverb_allowlist():
    """Verifies that technical adverbs (atomically, recursively) are not penalized."""
    tech_text = (
        "The system commits transactions atomically and traverses the tree recursively "
        "while polling asynchronously and updating nodes programmatically."
    )
    count, found, offenders = analyze_adverbs(tech_text)
    assert count == 0
    assert len(offenders) == 0

    # Offender adverbs
    slop_text = "This is fundamentally and deeply flawed, and truly genuinely slow."
    count, found, offenders = analyze_adverbs(slop_text)
    assert count == 4
    assert "fundamentally" in offenders
    assert "deeply" in offenders
    assert "genuinely" in offenders


def test_throat_clearing_and_binary_contrasts():
    """Verifies throat-clearing openers and binary contrast framing detection."""
    text = (
        "Here's the thing: we noticed an issue. It's worth noting that the cache was cold. "
        "Not `click_at`, just `click`. Environment isn't documentation, it's behavior. "
        "The implications are significant. That's it."
    )
    patterns = detect_ai_patterns(text, 35)
    assert patterns.throat_clearing_count >= 2
    assert patterns.binary_contrast_count >= 2
    assert patterns.vague_declarative_count >= 1
    assert patterns.fragment_count >= 1
    assert patterns.ai_tell_score < 6.0
    assert len(patterns.flags) > 0


@pytest.mark.asyncio
async def test_calculate_ai_patterns_logic_direct():
    """Verifies async wrapper for AI pattern detection."""
    sample = "We updated the configuration to enable server mode."
    patterns = await calculate_ai_patterns_logic(sample, "test")
    assert isinstance(patterns, AIPatternScoresModel)
    assert patterns.ai_tell_score == 10.0
    assert patterns.confidence == "low"  # < 100 words


@pytest.mark.asyncio
async def test_analyze_document_logic_combined():
    """Verifies combined two-axis analysis async wrapper."""
    sample = (
        "This is a sample text designed to be of medium length, specifically aiming "
        "for over one hundred words to thoroughly test the readability metrics, "
        "including the Spache score which has particular requirements regarding "
        "text length. We hope that by providing a text of this nature, we can ensure "
        "that all calculations are performed correctly and that the system behaves "
        "as expected under various conditions. This paragraph continues to add a few "
        "more words just to be certain that the one hundred word count threshold "
        "is definitely met and exceeded, providing a good basis for comprehensive "
        "testing of the application's scoring capabilities."
    )
    analysis = await analyze_document_logic(sample, "test")
    assert isinstance(analysis, DocumentAnalysisModel)
    assert isinstance(analysis.readability, ReadabilityScoresModel)
    assert isinstance(analysis.ai_patterns, AIPatternScoresModel)
    assert analysis.readability.word_count == 101
    assert analysis.ai_patterns.confidence == "high"


@pytest.mark.asyncio
async def test_execute_ai_patterns_tool_and_analyze_tool(mocker):
    """Verifies MCP executors for AI patterns and combined document analysis."""
    mocker.patch(
        "mcp_server.get_processed_text",
        return_value=("Sample text for tool test.", "mock source"),
    )

    # 1. AI Patterns Tool
    res_patterns = await execute_ai_patterns_tool({"text": "Hello world"}, ctx=None)
    assert len(res_patterns) == 1
    assert "ai_tell_score" in res_patterns[0].text

    # 2. Analyze Document Tool
    res_analyze = await execute_analyze_document_tool({"text": "Hello world"}, ctx=None)
    assert len(res_analyze) == 1
    assert "readability" in res_analyze[0].text
    assert "ai_patterns" in res_analyze[0].text


def test_fastapi_patterns_and_analyze_endpoints():
    """Verifies FastAPI /patterns/ and /analyze/ endpoints."""
    client = TestClient(fastapi_app)

    # Test /patterns/
    resp_patterns = client.post("/patterns/", json={"text": "Clean direct text."})
    assert resp_patterns.status_code == 200
    data_patterns = resp_patterns.json()
    assert "ai_tell_score" in data_patterns
    assert "em_dash_count" in data_patterns

    # Test /analyze/
    resp_analyze = client.post("/analyze/", json={"text": "Clean direct text."})
    assert resp_analyze.status_code == 200
    data_analyze = resp_analyze.json()
    assert "readability" in data_analyze
    assert "ai_patterns" in data_analyze
    assert "flesch_reading_ease" in data_analyze["readability"]
    assert "ai_tell_score" in data_analyze["ai_patterns"]
