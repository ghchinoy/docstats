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
import ssl
from typing import Optional

import anyio
import certifi
import nltk
import textstat
from readability import Readability

from ai_patterns import detect_ai_patterns
from models import (
    AIPatternScoresModel,
    DocumentAnalysisModel,
    ReadabilityScoresModel,
)

logger = logging.getLogger(__name__)


def ensure_nltk_resources() -> None:
    """Ensures necessary NLTK tokenizer resources are downloaded and available."""
    for resource, path in [
        ("punkt_tab", "tokenizers/punkt_tab"),
        ("punkt", "tokenizers/punkt"),
    ]:
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                nltk.download(resource, quiet=True, ssl_context=ssl_context)
            except Exception:
                try:
                    nltk.download(resource, quiet=True)
                except Exception as exc:
                    logger.warning(
                        "Could not automatically download NLTK resource "
                        f"'{resource}': {exc}"
                    )


ensure_nltk_resources()


def _sync_calculate_metrics(text: str, src_desc: str) -> ReadabilityScoresModel:
    """Synchronous CPU-bound calculation of all readability metrics."""
    if not text.strip():
        raise ValueError("Empty text.")

    wc = textstat.lexicon_count(text)
    if wc == 0:
        raise ValueError("Zero words.")
    if wc < 100:
        logger.warning(f"{src_desc} <100 words.")

    spache_score: Optional[float] = None
    if wc > 0:
        try:
            spache_score = Readability(text).spache().score
        except Exception as e:
            err_msg = str(e).lower()
            if "100 words required" in err_msg or "100 words" in err_msg:
                logger.warning(
                    f"Spache score could not be calculated for '{src_desc}': {e}"
                )
            else:
                logger.error(
                    f"Unexpected Spache Error for '{src_desc}'. "
                    f"Type: {type(e)}, Msg: {str(e)}",
                    exc_info=True,
                )

    return ReadabilityScoresModel(
        syllable_count=textstat.syllable_count(text),
        word_count=wc,
        sentence_count=textstat.sentence_count(text),
        flesch_reading_ease=textstat.flesch_reading_ease(text),
        flesch_kincaid_grade=textstat.flesch_kincaid_grade(text),
        gunning_fog=textstat.gunning_fog(text),
        smog_index=textstat.smog_index(text),
        automated_readability_index=textstat.automated_readability_index(text),
        coleman_liau_index=textstat.coleman_liau_index(text),
        linsear_write_formula=textstat.linsear_write_formula(text),
        dale_chall_readability_score=textstat.dale_chall_readability_score(text),
        text_standard=str(textstat.text_standard(text, float_output=True)),
        spache=spache_score,
    )


def _sync_calculate_ai_patterns(text: str, src_desc: str) -> AIPatternScoresModel:
    """Synchronous CPU-bound calculation of AI writing pattern detection (Axis B)."""
    if not text.strip():
        raise ValueError("Empty text.")

    wc = textstat.lexicon_count(text)
    if wc == 0:
        raise ValueError("Zero words.")

    return detect_ai_patterns(text, wc)


def _sync_analyze_document(text: str, src_desc: str) -> DocumentAnalysisModel:
    """Synchronous calculation of both Readability (Axis A) and AI Patterns (Axis B)."""
    readability = _sync_calculate_metrics(text, src_desc)
    ai_patterns = detect_ai_patterns(text, readability.word_count)
    return DocumentAnalysisModel(readability=readability, ai_patterns=ai_patterns)


async def calculate_readability_metrics_logic(
    text: str, src_desc: str
) -> ReadabilityScoresModel:
    """Calculates all readability metrics asynchronously without event loop block."""
    return await anyio.to_thread.run_sync(_sync_calculate_metrics, text, src_desc)


async def calculate_ai_patterns_logic(text: str, src_desc: str) -> AIPatternScoresModel:
    """Calculates AI writing pattern metrics asynchronously without event loop block."""
    return await anyio.to_thread.run_sync(_sync_calculate_ai_patterns, text, src_desc)


async def analyze_document_logic(text: str, src_desc: str) -> DocumentAnalysisModel:
    """Calculates both Readability (Axis A) and AI Patterns (Axis B) asynchronously."""
    return await anyio.to_thread.run_sync(_sync_analyze_document, text, src_desc)
