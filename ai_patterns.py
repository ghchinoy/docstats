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

"""AI writing pattern detection and scoring for technical prose.

Implements objective detection of AI writing tells aligned with the
technical-post-editorial rules, while allowing grammatically appropriate
punctuation and technical vocabulary.
"""

import math
import re
from typing import List, Tuple

from models import AIPatternScoresModel

# Technical adverbs that carry precision in engineering contexts (SKILL.md:107)
TECHNICAL_ADVERBS = {
    "atomically",
    "asynchronously",
    "synchronously",
    "recursively",
    "concurrently",
    "programmatically",
    "dynamically",
    "linearly",
    "automatically",
    "explicitly",
    "implicitly",
    "cryptographically",
    "statically",
    "deterministically",
    "serially",
    "temporally",
    "spatially",
    "mutually",
    "conditionally",
    "declaratively",
    "idempotently",
    "polymorphically",
    "hermetically",
    "orthogonally",
}

# Common English words ending in -ly that are not adverbs (nouns, adjectives, verbs)
NON_ADVERBS_LY = {
    "early",
    "daily",
    "weekly",
    "monthly",
    "yearly",
    "hourly",
    "nightly",
    "friendly",
    "likely",
    "unlikely",
    "lonely",
    "lovely",
    "orderly",
    "timely",
    "costly",
    "deadly",
    "family",
    "assembly",
    "supply",
    "apply",
    "rely",
    "imply",
    "multiply",
    "ally",
    "anomaly",
    "monopoly",
    "belly",
    "jelly",
    "rally",
    "tally",
    "folly",
    "bully",
    "gully",
}

# Specific high-offender adverbs called out in SKILL.md:50
OFFENDER_ADVERBS = {
    "notably",
    "genuinely",
    "silently",
    "actually",
    "simply",
    "truly",
    "deeply",
    "fundamentally",
    "certainly",
    "basically",
    "essentially",
    "literally",
    "honestly",
    "clearly",
}

# Throat-clearing opener patterns (SKILL.md:54-63, 133-138)
THROAT_CLEARING_PATTERNS = [
    re.compile(r"\bhere['’]?s\s+the\s+thing\b", re.IGNORECASE),
    re.compile(r"\bhere\s+is\s+the\s+thing\b", re.IGNORECASE),
    re.compile(r"\bhere['’]?s\s+what\s+we\s+found\b", re.IGNORECASE),
    re.compile(r"\bhere\s+is\s+what\s+we\s+found\b", re.IGNORECASE),
    re.compile(r"\bit['’]?s\s+worth\s+noting(?:\s+that)?\b", re.IGNORECASE),
    re.compile(r"\bit\s+is\s+worth\s+noting(?:\s+that)?\b", re.IGNORECASE),
    re.compile(r"\bworth\s+noting(?:\s*:\s*|\s+that\b|\b)", re.IGNORECASE),
    re.compile(r"\bit\s+turns\s+out(?:\s+that)?\b", re.IGNORECASE),
    re.compile(r"\bat\s+the\s+end\s+of\s+the\s+day\b", re.IGNORECASE),
    re.compile(r"\bto\s+put\s+it\s+simply\b", re.IGNORECASE),
    re.compile(r"\bput\s+simply\b", re.IGNORECASE),
    re.compile(r"\bthe\s+payoff\s*:\s*", re.IGNORECASE),
    re.compile(r"\bthe\s+takeaway\s*:\s*", re.IGNORECASE),
    re.compile(r"\bthe\s+kicker\s*:\s*", re.IGNORECASE),
    re.compile(r"\bworth\s+confirming\s+rather\s+than\s+assuming\b", re.IGNORECASE),
    re.compile(r"\bcheap\s+insurance\s+against\b", re.IGNORECASE),
    re.compile(
        r"\bthe\s+obvious\s+fix\s+is\b.*?\bwe\s+did\s+something\s+better\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bit['’]?s\s+important\s+to\s+(?:remember|note|highlight|keep\s+in\s+mind)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bit\s+is\s+important\s+to\s+(?:remember|note|highlight|keep\s+in\s+mind)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bit['’]?s\s+crucial\s+to\s+(?:remember|note|highlight|understand)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bit\s+is\s+crucial\s+to\s+(?:remember|note|highlight|understand)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bneedless\s+to\s+say\b", re.IGNORECASE),
    re.compile(
        r"\blet['’]?s\s+(?:dive\s+in|unpack|explore|take\s+a\s+closer\s+look)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bdeep\s+dive\s+into\b", re.IGNORECASE),
]

# Binary contrast framing patterns (SKILL.md:65-70)
BINARY_CONTRAST_PATTERNS = [
    re.compile(
        r"\bnot\s+([a-zA-Z0-9_`]+)\s*[,;]?\s*(?:it['’]?s|just)\s+([a-zA-Z0-9_`]+)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b([a-zA-Z0-9_`]+)\s+isn['’]?t\s+([a-zA-Z0-9_`\s]+?)\s*[,;]\s*(?:it['’]?s|([a-zA-Z0-9_`]+)\s+is)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b([a-zA-Z0-9_`]+)\s+is\s+not\s+([a-zA-Z0-9_`\s]+?)\s*[,;]\s*(?:it\s+is|([a-zA-Z0-9_`]+)\s+is)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bit['’]?s\s+not\s+about\s+[^,;]+[,;]\s*it['’]?s\s+about\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bit\s+is\s+not\s+about\s+[^,;]+[,;]\s*it\s+is\s+about\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bnot\s+only\s+(?:is|does|are|about)\s+[^,;]+[,;]?\s*but\s+(?:also\s+)?[^.]+\b",
        re.IGNORECASE,
    ),
]

# Vague declarative and hollow significance patterns (SKILL.md:88-93)
VAGUE_DECLARATIVE_PATTERNS = [
    re.compile(
        r"\bthe\s+implications\s+are\s+(?:significant|profound|immense|staggering|clear)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bthis\s+is\s+the\s+single\s+decision\s+that\s+made\b", re.IGNORECASE),
    re.compile(r"\bthis\s+changes\s+everything\b", re.IGNORECASE),
    re.compile(
        r"\bplays\s+a\s+(?:crucial|vital|pivotal|key|fundamental)\s+role\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bserves\s+as\s+a\s+testament\s+to\b", re.IGNORECASE),
    re.compile(
        r"\bin\s+today['’]?s\s+(?:fast-paced|rapidly\s+evolving|dynamic)\s+world\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bin\s+the\s+(?:fast-paced|rapidly\s+evolving)\s+landscape\b",
        re.IGNORECASE,
    ),
    re.compile(r"\ba\s+(?:myriad|tapestry|plethora)\s+of\b", re.IGNORECASE),
    re.compile(r"\bdelve\s+into\b", re.IGNORECASE),
]

# Staccato fragment patterns (SKILL.md:73-74)
FRAGMENT_PATTERNS = [
    re.compile(
        r"(?:^|[.?!]\s+)(?:That['’]?s\s+it|That['’]?s\s+the\s+thing|Full\s+stop|Period|Simple\s+as\s+that)\.(?:\s+|$)",
        re.IGNORECASE,
    ),
]


def strip_code_and_tables(text: str) -> str:
    """Removes fenced code blocks, inline code, and markdown tables.

    This ensures that technical syntax, table formatting, and code comments
    are not falsely flagged as prose violations.
    """
    # Remove fenced code blocks (``` ... ```)
    clean = re.sub(r"```[\s\S]*?```", " ", text)
    # Remove inline code (` ... `)
    clean = re.sub(r"`[^`\n]+`", "code_token", clean)
    # Remove markdown table rows (lines starting with | or having multiple |)
    lines = clean.split("\n")
    prose_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        if stripped.startswith("+---") or stripped.startswith("|---"):
            continue
        prose_lines.append(line)
    return "\n".join(prose_lines)


def split_sentences(text: str) -> List[str]:
    """Splits text into sentences using regex boundary detection."""
    # Normalize whitespace
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    # Split on sentence terminals followed by space and capital letter or end
    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'‘“])", normalized)
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return sentences


def count_em_dashes_in_prose(text: str) -> Tuple[int, List[str]]:
    """Counts em dashes in prose, excluding markdown list item separators.

    Allows markdown bullet list separators such as '* Item — description'.
    """
    lines = text.split("\n")
    count = 0
    matches = []
    for line in lines:
        stripped = line.strip()
        # If line is a markdown list item using em dash as separator, skip the separator
        if re.match(r"^[-*+]\s+[^\u2014—\-]+(?:\s*[\u2014—]|\s+--\s+)", stripped):
            # Strip the bullet prefix and first separator
            rest = re.sub(
                r"^[-*+]\s+[^\u2014—\-]+(?:\s*[\u2014—]|\s+--\s+)\s*",
                "",
                stripped,
            )
            found = re.findall(r"[\u2014—]|(?<=\S)--(?:(?=\S)|\s)", rest)
            count += len(found)
            if found:
                matches.extend(found)
        else:
            found = re.findall(r"[\u2014—]|(?<=\S)--(?:(?=\S)|\s)", stripped)
            count += len(found)
            if found:
                matches.extend(found)
    return count, matches


def analyze_adverbs(prose_text: str) -> Tuple[int, List[str], List[str]]:
    """Detects -ly adverbs, filtering out technical terms and non-adverbs."""
    words = re.findall(r"\b[a-zA-Z]+(?:-[a-zA-Z]+)?\b", prose_text.lower())
    adverbs_found = []
    offenders_found = []

    for word in words:
        if word.endswith("ly") and len(word) > 3:
            if word in TECHNICAL_ADVERBS or word in NON_ADVERBS_LY:
                continue
            adverbs_found.append(word)
            if word in OFFENDER_ADVERBS:
                offenders_found.append(word)

    return len(adverbs_found), adverbs_found, offenders_found


def count_wh_declarative_starters(sentences: List[str]) -> Tuple[int, List[str]]:
    """Counts sentences starting with Wh- words that are assertions (not questions)."""
    wh_starters = ("what", "when", "where", "which", "who", "why", "how")
    count = 0
    examples = []

    for sentence in sentences:
        s_clean = sentence.strip()
        if not s_clean:
            continue
        # If it ends with a question mark, it is a legitimate inquiry,
        # not a rhetorical tell
        if s_clean.endswith("?"):
            continue
        first_word_match = re.match(r"^[A-Za-z]+", s_clean)
        if first_word_match:
            first_word = first_word_match.group(0).lower()
            if first_word in wh_starters:
                count += 1
                if len(examples) < 3:
                    examples.append(
                        s_clean[:60] + "..." if len(s_clean) > 60 else s_clean
                    )

    return count, examples


def count_passive_voice_hints(text: str) -> int:
    """Heuristic count of passive voice constructions without named actors."""
    pattern = re.compile(
        r"\b(?:is|are|was|were|be|been|being)\s+([a-z]+(?:ed|en)|written|done|built|made|seen|found|given|run|set)\b(?!\s+by\b)",
        re.IGNORECASE,
    )
    return len(pattern.findall(text))


def count_three_item_lists(text: str) -> int:
    """Heuristic count of rhetorical three-item parallel lists in prose."""
    pattern = re.compile(
        r"\b[a-zA-Z0-9_`]+(?:,\s+[a-zA-Z0-9_`]+){1},\s+(?:and|or)\s+[a-zA-Z0-9_`]+\b",
        re.IGNORECASE,
    )
    return len(pattern.findall(text))


def calculate_sentence_length_cv(sentences: List[str]) -> float:
    """Calculates coefficient of variation (std_dev / mean) of sentence word counts."""
    if not sentences:
        return 0.0
    lengths = [len(s.split()) for s in sentences if s.split()]
    if not lengths:
        return 0.0
    mean_len = sum(lengths) / len(lengths)
    if mean_len == 0:
        return 0.0
    variance = sum((x - mean_len) ** 2 for x in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    return round(std_dev / mean_len, 3)


def detect_ai_patterns(raw_text: str, total_word_count: int) -> AIPatternScoresModel:
    """Analyzes text for AI writing patterns and computes the Axis B scorecard."""
    prose = strip_code_and_tables(raw_text)
    sentences = split_sentences(prose)
    sentence_count = max(1, len(sentences))
    prose_words = len(prose.split())
    # Baseline word count for rate calculations (avoid divide by zero)
    effective_words = max(1, prose_words if prose_words > 0 else total_word_count)

    flags: List[str] = []

    # 1. Em dashes in prose
    em_dash_count, _ = count_em_dashes_in_prose(prose)
    em_dash_rate = round((em_dash_count / effective_words) * 100, 2)

    # 2. Adverbs (-ly)
    adverb_count, all_adverbs, offender_adverbs = analyze_adverbs(prose)
    adverb_rate = round((adverb_count / effective_words) * 100, 2)
    if offender_adverbs:
        unique_offenders = sorted(list(set(offender_adverbs)))
        flags.append(
            f"Detected {len(offender_adverbs)} high-offender adverb(s): "
            f"{', '.join(unique_offenders)}"
        )

    # 3. Throat-clearing openers
    throat_clearing_count = 0
    matched_throat_clearers = []
    for pattern in THROAT_CLEARING_PATTERNS:
        matches = pattern.findall(prose)
        if matches:
            throat_clearing_count += len(matches)
            matched_throat_clearers.append(pattern.pattern)
    if throat_clearing_count > 0:
        flags.append(
            f"Found {throat_clearing_count} throat-clearing opener(s) "
            "or announcement phrase(s)."
        )

    # 4. Binary contrasts
    binary_contrast_count = 0
    for pattern in BINARY_CONTRAST_PATTERNS:
        matches = pattern.findall(prose)
        if matches:
            binary_contrast_count += len(matches)
    if binary_contrast_count > 0:
        flags.append(
            f"Found {binary_contrast_count} binary contrast frame(s) "
            "('not X, it\\'s Y')."
        )

    # 5. Wh- sentence starters (declarative)
    wh_starter_count, wh_examples = count_wh_declarative_starters(sentences)
    wh_starter_rate = round((wh_starter_count / sentence_count) * 100, 2)
    if wh_starter_rate > 15.0 and wh_starter_count >= 2:
        flags.append(
            f"Elevated Wh- declarative starter rate: {wh_starter_rate}% of sentences."
        )

    # 6. Fragments
    fragment_count = 0
    for pattern in FRAGMENT_PATTERNS:
        matches = pattern.findall(prose)
        if matches:
            fragment_count += len(matches)
    if fragment_count > 0:
        flags.append(
            f"Found {fragment_count} staccato fragment(s) for manufactured emphasis."
        )

    # 7. Vague declaratives
    vague_declarative_count = 0
    for pattern in VAGUE_DECLARATIVE_PATTERNS:
        matches = pattern.findall(prose)
        if matches:
            vague_declarative_count += len(matches)
    if vague_declarative_count > 0:
        flags.append(
            f"Found {vague_declarative_count} vague declarative or "
            "significance-announcing phrase(s)."
        )

    # 8. Lists of three
    list_of_three_count = count_three_item_lists(prose)

    # 9. Rhythm (Sentence length variation)
    sentence_len_cv = calculate_sentence_length_cv(sentences)
    if sentence_count >= 5 and sentence_len_cv < 0.20:
        flags.append(
            f"Monotone sentence rhythm: sentence length CV is {sentence_len_cv} "
            "(< 0.20)."
        )

    # 10. Passive voice hints
    passive_hint_count = count_passive_voice_hints(prose)

    # --- Score Calculation (0.0 to 10.0 scale, floor >= 7.0 to pass) ---
    # We calibrate penalties to be balanced, with softened em dash tolerance
    # for grammatically appropriate usage.
    deductions = 0.0

    # Em dash penalty:
    # 1 em dash per 200 words (~0.5 per 100 words) is standard/reasonable human prose.
    if em_dash_rate > 0.5:
        if em_dash_rate <= 1.0:
            deductions += 0.3 + (em_dash_rate - 0.5) * 0.8
        else:
            deductions += min(
                4.0,
                0.7 + (em_dash_rate - 1.0) * 1.5 + max(0, em_dash_count - 2) * 0.5,
            )
        if em_dash_rate > 1.2 or em_dash_count >= 3:
            flags.append(
                f"Excessive em dash density in prose: {em_dash_count} "
                f"({em_dash_rate}/100w)."
            )

    # Adverb penalty:
    # Technical writing with reasonable adverbs (~1.5/100w) is acceptable
    if adverb_rate > 1.5:
        deductions += min(2.0, (adverb_rate - 1.5) * 0.8)
    if offender_adverbs:
        deductions += min(1.5, len(offender_adverbs) * 0.4)

    # Throat-clearing openers penalty (strong AI tell)
    deductions += min(2.5, throat_clearing_count * 0.75)

    # Binary contrast penalty (strong AI tell)
    deductions += min(2.0, binary_contrast_count * 0.6)

    # Wh- starter penalty
    if wh_starter_rate > 15.0 and wh_starter_count >= 2:
        deductions += min(1.2, (wh_starter_rate - 15.0) * 0.05)

    # Vague declaratives penalty
    deductions += min(2.0, vague_declarative_count * 0.6)

    # Fragment penalty
    deductions += min(1.2, fragment_count * 0.4)

    # Metronomic rhythm penalty (only if sufficient sample size)
    if sentence_count >= 5 and sentence_len_cv < 0.20:
        deductions += min(1.0, (0.20 - sentence_len_cv) * 3.0)

    ai_tell_score = max(0.0, round(10.0 - deductions, 2))

    # Total tells (count of distinct high-confidence flags)
    total_tells = (
        (em_dash_count if em_dash_rate > 0.5 else 0)
        + throat_clearing_count
        + binary_contrast_count
        + vague_declarative_count
        + fragment_count
        + len(offender_adverbs)
    )

    confidence = "high" if total_word_count >= 100 else "low"

    return AIPatternScoresModel(
        em_dash_count=em_dash_count,
        em_dash_rate=em_dash_rate,
        adverb_ly_count=adverb_count,
        adverb_ly_rate=adverb_rate,
        throat_clearing_count=throat_clearing_count,
        binary_contrast_count=binary_contrast_count,
        wh_starter_count=wh_starter_count,
        wh_starter_rate=wh_starter_rate,
        fragment_count=fragment_count,
        list_of_three_count=list_of_three_count,
        sentence_len_cv=sentence_len_cv,
        vague_declarative_count=vague_declarative_count,
        passive_hint_count=passive_hint_count,
        total_tells=total_tells,
        ai_tell_score=ai_tell_score,
        confidence=confidence,
        flags=flags,
    )
