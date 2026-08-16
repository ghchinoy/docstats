# Corpus Document Schema

Every document in the evaluation corpus lives in a dedicated subfolder under `eval/corpus/<document-slug>/` containing:

1. `source.md`: The raw input markdown/prose document to be edited.
2. `meta.yaml`: Structured metadata describing the document's type, reading level target, baseline characteristics, and provenance.
3. `baseline.json` *(optional/generated)*: Pre-computed baseline `analyze_document` output capturing Axis A readability and Axis B AI pattern scores.

---

## Schema Definition (`meta.yaml`)

```yaml
# Unique slug matching folder name
id: "sample-migration"

# Title of the technical piece
title: "Engine Migration: Transitioning to Server Mode"

# Document type: developer_blog, migration_guide, readme, architecture_rfc, tutorial
doc_type: "migration_guide"

# Source tier:
# - generated_ai: Model-generated from technical briefs (authentic AI writing)
# - synthetic_curated: Hand-curated drafts with intentionally planted tell patterns
# - public_licensed: Real-world permissive open-source technical writing (over-correction test)
source_tier: "synthetic_curated"

# License governing the document (must allow evaluation and redistribution)
license: "Apache-2.0"

# Optional source URL (required for public_licensed documents)
source_url: null

# Optional generation brief (used for generated_ai documents)
generation_prompt: null

# Human-readable provenance description
provenance: "Realistic synthesis with natural AI writing patterns"

# Target audience and readability band
target:
  audience: "Distributed Systems Engineers"
  band: "Dense"               # Very Accessible, Accessible, Dense, Very Dense, Impenetrable
  expected_fk_grade_min: 10.0
  expected_fk_grade_max: 14.0

# Declared known tell characteristics (ground truth flags)
known_tells:
  em_dashes: true
  throat_clearing: true
  binary_contrasts: true
  high_adverb_density: true
  wh_starters: false
  fragments: true
  vague_declaratives: true
  metronomic_rhythm: false
```
