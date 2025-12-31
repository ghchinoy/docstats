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

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator


class TextSourceModel(BaseModel):
    """Model for text source input.

    Supports direct text, web URLs, or GCS PDF URIs.
    """

    text: Optional[str] = Field(None, min_length=1)
    web_url: Optional[str] = Field(None)
    gcs_pdf_uri: Optional[str] = Field(None)

    @model_validator(mode="before")
    @classmethod
    def check_exclusive_source(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validates that exactly one source is provided.

        Also ensures the source is correctly formatted.
        """
        sources = ["text", "web_url", "gcs_pdf_uri"]
        provided_sources = [s for s in sources if values.get(s)]
        if len(provided_sources) != 1:
            raise ValueError(
                "Exactly one of text, web_url, or gcs_pdf_uri must be provided."
            )
        gcs_uri = values.get("gcs_pdf_uri")
        if gcs_uri and not gcs_uri.startswith("gs://"):
            raise ValueError("gcs_pdf_uri must be a valid gs:// URI.")
        return values

class ReadabilityScoresModel(BaseModel):
    """Model for the comprehensive set of readability scores and text statistics."""
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
