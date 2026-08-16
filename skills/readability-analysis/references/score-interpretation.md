# Score Interpretation — Worked Examples

This reference anchors the readability scores to docstats' own **golden set**
(`samples/`), so you can calibrate what a given number "feels" like. The values
below are the committed baseline (`samples/baseline_results.json`); regenerate
with `uv run python baseline_analysis.py`.

## The four reference texts

| Sample | Intended audience | `text_standard` (consensus grade) | `flesch_reading_ease` |
|---|---|---|---|
| `level_primary.txt` | Early primary readers | **-1.0** (below grade 1) | 106.9 (extremely easy) |
| `level_middle.txt` | Middle / high school | **15.0** | 35.3 (difficult) |
| `level_academic.txt` | University / research | **23.0** | -29.8 (very difficult) |
| `level_legal.txt` | Legal / specialist | **25.0** | 14.0 (very difficult) |

Key takeaways:

- **`flesch_reading_ease` runs opposite to the grade scores.** The primary text
  scores ~107 (higher = easier) while its grade level is negative; the academic
  text scores negative on ease while its grade level is 22+. Always state which
  direction you mean.
- **The consensus `text_standard` is the most robust single number.** Individual
  formulas disagree — for the legal sample `coleman_liau_index` (14.7) is far
  lower than `linsear_write_formula` (25.0) — because each weights sentence
  length vs. word difficulty differently. Report `text_standard` first, then
  explain notable outliers.
- **Legal ≠ hardest on every axis.** The academic sample has the lowest
  (hardest) `flesch_reading_ease`, but the legal sample has the highest
  consensus grade, driven by very long sentences (109 words / 3 sentences ≈ 36
  words per sentence).

## Reading the raw statistics

`word_count`, `sentence_count`, and `syllable_count` explain *why* a score
landed where it did:

- **Long sentences inflate grade level.** The legal sample averages ~36
  words/sentence; shortening sentences is usually the fastest way to lower the
  grade.
- **Syllable density drives Flesch/SMOG.** The academic sample packs 358
  syllables into 140 words (~2.56 syllables/word); swapping multi-syllable
  jargon for plain words lowers these fast.
- **Below ~100 words, trust nothing precisely.** The legal sample (109 words) is
  near the floor; `spache` can be `null` and all formulas get noisier.

## Turning scores into edits

1. Report `text_standard` and `flesch_reading_ease`, then the audience fit
   (see the audience-target table in `SKILL.md`).
2. If the text is above target, look at `word_count / sentence_count` (average
   sentence length) and syllable density to pick the lever:
   - Long sentences → split them.
   - High syllables/word → replace jargon with common words.
   - High `dale_chall_readability_score` → too many unfamiliar words; simplify
     vocabulary.
3. Re-run `get_readability_scores` on the revision and confirm the consensus
   grade dropped toward the target.
