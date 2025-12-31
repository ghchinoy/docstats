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
from fastapi.testclient import TestClient
import pypdf
import io
from fastapi_app import fastapi_app  # Import your FastAPI application instance
from mcp_server import execute_readability_tool

client = TestClient(fastapi_app)


# --- Mocking Helpers ---
def mock_pdf_content():
    """Generates a minimal valid PDF byte stream for mocking."""
    # We use a real pypdf-generated PDF to ensure compatibility with our reader
    out = io.BytesIO()
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=72, height=72)
    # Note: pypdf can't easily add text to a blank page without more complex logic
    # but our mock can return a mock reader instead of real bytes if needed.
    writer.write(out)
    return out.getvalue()


# --- Test Data ---
SHORT_TEXT = "long black cat so nice and fat"
MEDIUM_TEXT = (
    "This is a sample text designed to be of medium length, specifically aiming "
    "for over one hundred words to thoroughly test the readability metrics, "
    "including the Spache score which has particular requirements regarding "
    "text length. We hope that by providing a text of this nature, we can ensure "
    "that all calculations are performed correctly and that the system behaves "
    "as expected under various conditions. This paragraph continues to add a few "
    "more words just to be certain that the one hundred word count threshold "
    "is definitely met and exceeded, providing a good basis for comprehensive "
    "testing of the application's scoring capabilities."
)  # 101 words

STABLE_WEB_URL = (
    "https://www.gutenberg.org/files/1342/1342-h/1342-h.htm"  # Pride and Prejudice
)
WEB_PDF_URL = "https://arxiv.org/pdf/2503.05244"

# Using your provided GCS URIs
GCS_PDF_URIS = [
    "gs://genai-blackbelt-fishfooding-fabulae/sources/google_cloud_ai_trends.pdf",
    "gs://genai-blackbelt-fishfooding-fabulae/sources/hai_ai_index_report_2025.pdf",
    "gs://genai-blackbelt-fishfooding-fabulae/sources/is_mercury.pdf",
]


# --- Helper for Assertions ---
def assert_valid_scores(response_data: dict, expect_spache_null: bool = False):
    """Verifies that the response contains all expected readability scores."""
    fields = [
        "flesch_reading_ease",
        "flesch_kincaid_grade",
        "gunning_fog",
        "smog_index",
        "automated_readability_index",
        "coleman_liau_index",
        "linsear_write_formula",
        "dale_chall_readability_score",
        "text_standard",
        "spache",
        "syllable_count",
        "word_count",
        "sentence_count",
    ]
    for field in fields:
        assert field in response_data

    assert isinstance(response_data["syllable_count"], int)
    assert isinstance(response_data["word_count"], int)
    assert isinstance(response_data["sentence_count"], int)

    if response_data["word_count"] > 0:
        # Scores can be None or 0 for empty/very short texts
        assert isinstance(response_data["flesch_reading_ease"], float)
        assert isinstance(response_data["flesch_kincaid_grade"], float)

    # Spache score assertions
    if expect_spache_null:
        # If we explicitly expect Spache to be null (e.g., for very short texts)
        assert response_data["spache"] is None, (
            f"Spache score should be null for short texts "
            f"(wc={response_data['word_count']}), but got {response_data['spache']}"
        )
    elif response_data["word_count"] >= 100:
        # For texts >= 100 words, Spache MUST be a float now that the bug is fixed.
        assert isinstance(response_data["spache"], float), (
            f"Spache score should be a float for texts >= 100 words "
            f"(wc={response_data['word_count']}), but got {response_data['spache']}"
        )
        assert response_data["spache"] != "UNEXPECTED_SPACHE_ERROR", (
            f"Spache calculation hit an internal error for word_count "
            f"{response_data['word_count']}. Check server logs."
        )
    else:
        # This case covers word_count < 100 AND expect_spache_null is False
        # Spache should be None due to word count, not an unexpected error.
        assert response_data["spache"] is None, (
            f"Spache for wc < 100 (wc={response_data['word_count']}) should be None, "
            f"not '{response_data['spache']}' (expect_spache_null was False)"
        )

    assert response_data["word_count"] >= 0
    if response_data["word_count"] > 0:
        assert response_data["sentence_count"] >= 0


# --- Test Cases ---
def test_read_scores_short_text():
    """Verifies readability scores for a short text (<100 words)."""
    response = client.post("/scores/", json={"text": SHORT_TEXT})
    assert response.status_code == 200
    data = response.json()
    assert_valid_scores(data, expect_spache_null=True)
    assert data["word_count"] < 100


def test_read_scores_medium_text():
    """Verifies readability scores for a medium-length text (>=100 words)."""
    response = client.post("/scores/", json={"text": MEDIUM_TEXT})
    assert response.status_code == 200
    data = response.json()
    # expect_spache_null is False by default, so checks >=100 logic
    assert_valid_scores(data)
    assert data["word_count"] >= 100


@pytest.mark.slow
def test_read_scores_web_url():
    """Verifies readability scores for a publicly accessible web URL."""
    response = client.post("/scores/", json={"web_url": STABLE_WEB_URL})
    assert response.status_code == 200
    data = response.json()
    assert_valid_scores(data, expect_spache_null=(data.get("word_count", 0) < 100))
    assert data["word_count"] > 0


@pytest.mark.slow
def test_read_scores_web_pdf():
    """Verifies readability scores for a web-based PDF file."""
    response = client.post("/scores/", json={"web_url": WEB_PDF_URL})
    assert response.status_code == 200
    data = response.json()
    assert_valid_scores(data, expect_spache_null=(data.get("word_count", 0) < 100))
    assert data["word_count"] > 1000  # arXiv papers are usually long


@pytest.mark.slow
@pytest.mark.parametrize("gcs_uri", GCS_PDF_URIS)
def test_read_scores_gcs_pdf(gcs_uri: str):
    """Verifies readability scores for a PDF stored in Google Cloud Storage."""
    response = client.post("/scores/", json={"gcs_pdf_uri": gcs_uri})
    if response.status_code == 200:
        data = response.json()
        assert_valid_scores(data, expect_spache_null=(data.get("word_count", 0) < 100))
        assert data["word_count"] >= 0
    elif response.status_code == 422:
        data = response.json()
        assert "detail" in data
        error_found = False
        try:
            check_error_detail(data["detail"], "GCS PDF error")
            error_found = True
        except AssertionError:
            pass
        if not error_found:
            check_error_detail(data["detail"], "No text in PDF")
    else:
        pytest.fail(
            f"Unexpected status code {response.status_code} for {gcs_uri}. "
            f"Response: {response.text}"
        )


# --- Test Cases for Invalid Inputs ---
def check_error_detail(detail: list | str, expected_message: str):
    """Verifies that the error detail contains the expected message."""
    if isinstance(detail, str):
        assert expected_message in detail, (
            f"Expected message '{expected_message}' not found in "
            f"error detail string: {detail}"
        )
        return
    assert isinstance(detail, list), "Error detail should be a list or string"
    found = False
    for error_item in detail:
        if (
            isinstance(error_item, dict)
            and "msg" in error_item
            and expected_message in error_item["msg"]
        ):
            found = True
            break
    assert found, (
        f"Expected message '{expected_message}' not found in "
        f"error details: {detail}"
    )


def test_read_scores_invalid_multiple_sources():
    """Ensures that providing multiple sources returns a 422 error."""
    response = client.post(
        "/scores/", json={"text": "hello", "web_url": "http://example.com"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    check_error_detail(
        data["detail"], "Exactly one of text, web_url, or gcs_pdf_uri must be provided"
    )


def test_read_scores_invalid_no_sources():
    """Ensures that providing no source returns a 422 error."""
    response = client.post("/scores/", json={})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    check_error_detail(
        data["detail"], "Exactly one of text, web_url, or gcs_pdf_uri must be provided"
    )


def test_read_scores_invalid_gcs_uri_format():
    """Ensures that an invalid GCS URI format returns a 422 error."""
    response = client.post("/scores/", json={"gcs_pdf_uri": "invalid-uri-format"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    check_error_detail(data["detail"], "gcs_pdf_uri must be a valid gs:// URI")


def test_read_scores_empty_text_source():
    """Ensures that an empty text source returns a 422 error."""
    response = client.post("/scores/", json={"text": ""})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # As per current main.py logic, an empty text string leads to the
    # 'Exactly one source' error because values.get('text') evaluates to False.
    check_error_detail(
        data["detail"], "Exactly one of text, web_url, or gcs_pdf_uri must be provided"
    )


@pytest.mark.slow
def test_read_scores_non_existent_web_url():
    """Ensures that a non-existent web URL returns a 422 error."""
    response = client.post(
        "/scores/", json={"web_url": "http://thissitedefinitelydoesnotexist12345.com"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    check_error_detail(data["detail"], "Web URL error")


@pytest.mark.slow
def test_read_scores_gcs_pdf_not_found():
    """Ensures that a non-existent GCS PDF returns a 422 error."""
    response = client.post(
        "/scores/",
        json={"gcs_pdf_uri": "gs://non-existent-bucket-12345/non-existent-file.pdf"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    check_error_detail(data["detail"], "GCS PDF error")
