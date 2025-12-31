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

import pytest
from unittest.mock import MagicMock, AsyncMock
from models import TextSourceModel
from extraction import get_processed_text
from mcp_server import execute_readability_tool

@pytest.mark.asyncio
async def test_get_processed_text_web_mock(mocker):
    """Verifies web extraction logic using mocks."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"<html><body><article>Mocked Article Content</article></body></html>"
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
async def test_execute_readability_tool_mock(mocker):
    """Verifies the MCP tool execution with mocked logic."""
    # Mock extraction and metrics so we only test the tool wrapper
    mocker.patch("mcp_server.get_processed_text", return_value=("Sample text for tool test.", "mock source"))
    
    # We want a real ReadabilityScoresModel but mock the logic function call
    from models import ReadabilityScoresModel
    mock_scores = ReadabilityScoresModel(
        syllable_count=5, word_count=5, sentence_count=1,
        flesch_reading_ease=100.0, flesch_kincaid_grade=1.0, spache=1.0
    )
    mocker.patch("mcp_server.calculate_readability_metrics_logic", return_value=mock_scores)

    arguments = {"text": "This is a test."}
    result = await execute_readability_tool(arguments, ctx=None)

    assert len(result) == 1
    assert result[0].type == "text"
    assert "flesch_reading_ease" in result[0].text
    assert "100.0" in result[0].text
