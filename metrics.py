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

import textstat
from readability import Readability

from models import ReadabilityScoresModel

logger = logging.getLogger(__name__)

async def calculate_readability_metrics_logic(
    text: str, src_desc: str
) -> ReadabilityScoresModel:
    """Calculates all readability metrics for the given text."""
    if not text.strip():
        raise ValueError("Empty text.")

    wc = textstat.lexicon_count(text)
    if wc == 0:
        raise ValueError("Zero words.")
    if wc < 100:
        logger.warning(f"{src_desc} <100 words.")

    spache_score = None
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
        spache=spache_score
    )
