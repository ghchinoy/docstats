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
from main import fastapi_app  # Import your FastAPI application instance

client = TestClient(fastapi_app)

# --- Test Data ---
SHORT_TEXT = "long black cat so nice and fat"
MEDIUM_TEXT = """This is a sample text designed to be of medium length, specifically aiming for over one hundred words \\
to thoroughly test the readability metrics, including the Spache score which has particular requirements regarding \\
text length. We hope that by providing a text of this nature, we can ensure that all calculations are performed \\
correctly and that the system behaves as expected under various conditions. This paragraph continues to add a few \\
more words just to be certain that the one hundred word count threshold is definitely met and exceeded, providing a \\
good basis for comprehensive testing of the application\\'s scoring capabilities.""" # 101 words

STABLE_WEB_URL = "https://www.gutenberg.org/files/1342/1342-h/1342-h.htm" # Pride and Prejudice

# Using your provided GCS URIs
GCS_PDF_URIS = [
    "gs://genai-blackbelt-fishfooding-fabulae/sources/google_cloud_ai_trends.pdf",
    "gs://genai-blackbelt-fishfooding-fabulae/sources/hai_ai_index_report_2025.pdf",
    "gs://genai-blackbelt-fishfooding-fabulae/sources/is_mercury.pdf"
]

# --- Helper for Assertions ---
def assert_valid_scores(response_data: dict, expect_spache_null: bool = False):
    assert "flesch_reading_ease" in response_data
    assert "flesch_kincaid_grade" in response_data
    assert "gunning_fog" in response_data
    assert "smog_index" in response_data
    assert "automated_readability_index" in response_data
    assert "coleman_liau_index" in response_data
    assert "linsear_write_formula" in response_data
    assert "dale_chall_readability_score" in response_data
    assert "text_standard" in response_data
    assert "spache" in response_data
    assert "syllable_count" in response_data
    assert "word_count" in response_data
    assert "sentence_count" in response_data

    assert isinstance(response_data["syllable_count"], int)
    assert isinstance(response_data["word_count"], int)
    assert isinstance(response_data["sentence_count"], int)
    
    if response_data["word_count"] > 0: # Scores can be None or 0 for empty/very short texts
        assert isinstance(response_data["flesch_reading_ease"], float)
        assert isinstance(response_data["flesch_kincaid_grade"], float)

    # Spache score assertions
    if expect_spache_null:
        # If we explicitly expect Spache to be null (e.g., for very short texts < 100 words)
        assert response_data["spache"] is None, \
            f"Spache score should be null for short texts (wc={response_data['word_count']}), but got {response_data['spache']}"
    elif response_data["word_count"] >= 100:
        # For texts >= 100 words, Spache can be a float or None (if lib decides not to score it)
        # but it should not be our specific error marker string.
        assert response_data["spache"] != "UNEXPECTED_SPACHE_ERROR", \
            f"Spache calculation hit an internal, unexpected error for word_count {response_data['word_count']}. Check server logs."
        assert response_data["spache"] is None or isinstance(response_data["spache"], float), \
            f"Spache score should be a float or None for texts >= 100 words (wc={response_data['word_count']}), but got type: {type(response_data['spache'])}"
    else: # This case covers word_count < 100 AND expect_spache_null is False
          # This implies we didn't expect spache to be null, but word count is low.
          # Spache should be None due to word count, not an unexpected error.
        assert response_data["spache"] is None, \
            f"Spache for wc < 100 (wc={response_data['word_count']}) should be None, not '{response_data['spache']}' (expect_spache_null was False)"

    assert response_data["word_count"] >= 0
    if response_data["word_count"] > 0 : 
      assert response_data["sentence_count"] >= 0

# --- Test Cases ---
def test_read_scores_short_text():
    response = client.post("/scores/", json={"text": SHORT_TEXT})
    assert response.status_code == 200
    data = response.json()
    assert_valid_scores(data, expect_spache_null=True)
    assert data["word_count"] < 100

def test_read_scores_medium_text():
    response = client.post("/scores/", json={"text": MEDIUM_TEXT})
    assert response.status_code == 200
    data = response.json()
    assert_valid_scores(data) # expect_spache_null is False by default, so checks >=100 logic
    assert data["word_count"] >= 100

@pytest.mark.slow
def test_read_scores_web_url():
    response = client.post("/scores/", json={"web_url": STABLE_WEB_URL})
    assert response.status_code == 200
    data = response.json()
    assert_valid_scores(data, expect_spache_null=(data.get("word_count", 0) < 100))
    assert data["word_count"] > 0 

@pytest.mark.slow
@pytest.mark.parametrize("gcs_uri", GCS_PDF_URIS)
def test_read_scores_gcs_pdf(gcs_uri: str):
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
        pytest.fail(f"Unexpected status code {response.status_code} for {gcs_uri}. Response: {response.text}")

# --- Test Cases for Invalid Inputs ---
def check_error_detail(detail: list | str , expected_message: str):
    if isinstance(detail, str):
        assert expected_message in detail, f"Expected message '{expected_message}' not found in error detail string: {detail}"
        return
    assert isinstance(detail, list), "Error detail should be a list or string"
    found = False
    for error_item in detail:
        if isinstance(error_item, dict) and "msg" in error_item and expected_message in error_item["msg"]:
            found = True
            break
    assert found, f"Expected message '{expected_message}' not found in error details: {detail}"

def test_read_scores_invalid_multiple_sources():
    response = client.post("/scores/", json={"text": "hello", "web_url": "http://example.com"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    check_error_detail(data["detail"], "Exactly one of text, web_url, or gcs_pdf_uri must be provided")

def test_read_scores_invalid_no_sources():
    response = client.post("/scores/", json={})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    check_error_detail(data["detail"], "Exactly one of text, web_url, or gcs_pdf_uri must be provided")

def test_read_scores_invalid_gcs_uri_format():
    response = client.post("/scores/", json={"gcs_pdf_uri": "invalid-uri-format"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    check_error_detail(data["detail"], "gcs_pdf_uri must be a valid gs:// URI")

\
def test_read_scores_empty_text_source():
    response = client.post("/scores/", json={"text": ""})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # As per current main.py logic, an empty text string leads to the 'Exactly one source' error
    # because `values.get('text')` (which is `""`) evaluates to False in the `check_exclusive_source` validator.
    check_error_detail(data["detail"], "Exactly one of text, web_url, or gcs_pdf_uri must be provided")

@pytest.mark.slow
def test_read_scores_non_existent_web_url():
    response = client.post("/scores/", json={"web_url": "http://thissitedefinitelydoesnotexist12345.com"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    check_error_detail(data["detail"], "Web URL error")

@pytest.mark.slow
def test_read_scores_gcs_pdf_not_found():
    response = client.post("/scores/", json={"gcs_pdf_uri": "gs://non-existent-bucket-12345/non-existent-file.pdf"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    check_error_detail(data["detail"], "GCS PDF error")