# Corpus Document Schema

Every document in the evaluation corpus lives in a dedicated subfolder under `eval/corpus/<document-slug>/` containing two files:

1. `source.md`: The raw input markdown/prose document to be edited.
2. `meta.yaml`: Structured metadata describing the document's type, reading level target, baseline characteristics, and provenance.

---

## Schema Definition (`meta.yaml`)

```yaml
# Unique slug matching folder name
id: "sample-migration-guide"

# Title of the technical piece
title: "Migrating from V1 to V2 Storage Engines"

# Document type: developer_blog, migration_guide, readme, architecture_rfc, tutorial
doc_type: "migration_guide"

# Authoring / origin notes
provenance: "Realistic synthesis with natural AI writing patterns"

# Target audience and readability band
target:
  audience: "Senior Software Engineers"
  band: "Dense"               # Very Accessible, Accessible, Dense, Very Dense
  expected_fk_grade_min: 10.0
  expected_fk_grade_max: 15.0

# Known baseline flaws embedded in the draft
known_tells:
  - em_dashes: true
  - throat_clearing: true
  - binary_contrasts: true
  - high_adverb_density: false
```
