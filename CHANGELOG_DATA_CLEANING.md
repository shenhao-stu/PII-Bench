# Data Cleaning Changelog & ACL 2026 Reproduction Verification (v1.1)

This release provides two aligned core data variants across GitHub, HuggingFace (`shenhao/PII-Bench`), and ModelScope (`shenhao23/PII-Bench`):
- **`data/cleaned/` (identical to HuggingFace & ModelScope `default` + `privacy_utility`):** schema-verified **v1.1** benchmark (recommended; will be iteratively updated in future versions).
- **`data/paper_exact/` (identical to HuggingFace & ModelScope `paper_exact`):** permanently frozen bit-exact ACL 2026 ground truth reproducing Tables 3–26 with **0.0000** drift.

## Exact Cleaning Rules Applied in v1.1 (474 Audited Events)

1. **Removed leaked `'predict'` field (`hard`: 200 rows)** — Applied to **both** `cleaned` and `paper_exact`. Zero impact (`0.0000`) on any metric or table.
2. **Removed annotation-UI ghost entity `'Asia-Pacific Economic Cooperation '` (`single`: 10 rows, `distract`: 4 rows, `pii_masked_200`: 1 row) & fixed dangling `'A'` in `total_subjects` (`single`: 8 rows)** — Resolved all 18 array-length mismatches in `single` and all 4 `'UNKNOWN'` `total_types` in `distract`.
3. **Removed 3 entities completely absent from `usr_desc` (`single`: 5 rows, `distract`: 2 rows, `pii_masked_200`: 1 row)** — Specifically `'Asia'` in `single[632]` (already absent from its twin `single[633]`) and `'Shibuya'` in `single[662..665]` / `distract[12,89]`. None were in `most_related`.
4. **Stripped leading/trailing whitespace (`single`: 6 entities + 2 `usr_desc`, `hard`: 2 entities, `distract`: 3 entities, `pii_masked_200`: 1 entity)** — Cleaned `' LGBTQ+ community'`, `' Buenos Aires'`, and `'Asia-Pacific Economic Cooperation '`.
5. **Deduplicated identical within-subject entity entries (`single`: 10 rows, `multi`: 10 rows, `distract`: 17 rows)** — Kept the last `(type, tag)` to match `PUB_eval.py`'s Python `dict` override semantics (also resolving `'University of Paris'` previously duplicated under both `DEM` and `ORG` in `single[476,477]` and `distract[118]`).
6. **Fixed single unambiguous coarse-type click-slip (`single`: 2 rows `[980,981]`, `pii_masked_200`: 1 row `[127]`)** — Reclassified `'Christian'` (`"devoted Christian"`) from `ORG / Public Institution Name` to `DEM / Faith` (the only coarse-type mislabeling found across all 37,475 entities).
7. **Restored 100.0% twin-description entity symmetry (`single`: 4 rows `[858,859,1048,1049]`, `hard`: 1 row `[20]`, `distract`: 1 row `[128]`, `pii_masked_200`: 1 row `[96]`)** — Synchronized complementary human annotations on the 2 identical-text description pairs (`extra_431`: `Asia-Pacific Economic Cooperation` + `International Economic Policy Organization`; `origin_26`: `Buenos Aires` + `Paris`), ensuring `same usr_desc => same entities` holds for **1,221/1,221 (100%)** pairs.
8. **Canonicalized 8 rare annotator synonym tags (20 occurrences across all splits)** — Mapped to 54 canonical subcategories documented in `metadata/pii_taxonomy.json`. Zero metric impact (`0.0000`).
9. **Rebuilt span-safe, case-insensitive, `most_related`-protected masking on `pii_masked_200.jsonl` (`privacy_utility`: 81 full-mask & 63 adaptive-mask rows)** — Fixed 3 corrupted/erased `most_related` entities (`row[127]` `'Christianity'` → `<Public Institution Name>ity`, `row[140]` `'20th Floor, No. 500, Sukhumvit Road, Bangkok'`, `row[147]` `"Beilin District, Xi'an"`), 89 case-mismatch leaks in `mask_usr_desc`, and 63 case-mismatch leaks in `adaptive_mask_usr_desc`. Verbatim Section 4.5 raw prompts are preserved in `data/paper_exact/PII_masked.jsonl`.
10. **Unified schema & globally unique IDs** — Added `sample_id`, `split`, `num_subjects`, and precomputed `query_unrelated` while preserving original `id`, `from_id`, and realistic synthetic formats (including common email domains and Chinese license plates).

## Verified Empirical Metric Parity (ACL 2026 Saved Predictions, `single`)

| Model (Task / Prompt) | `paper_exact` (ACL 2026) | `cleaned` / `default` (v1.1) | $\Delta$ |
|---|---:|---:|---:|
| GPT-5 (Task 1 PII Detection, Strict-F1) | `0.88008` | `0.88128` | `+0.00120` |
| DeepSeek-V3.2 (Task 1 PII Detection, Strict-F1) | `0.88857` | `0.88981` | `+0.00124` |
| Qwen3-30B-Instruct (Task 1 PII Detection, Strict-F1) | `0.82231` | `0.82359` | `+0.00127` |
| GPT-5 (Task 3 Query-Unrelated, `Self-CoT` F1) | `0.83977` (Paper Table 26: `0.840`) | `0.84120` | `+0.00143` |
| GPT-5 (Task 3 Query-Unrelated, `Naive` F1) | `0.83196` (Paper Table 26: `0.832`) | `0.83342` | `+0.00145` |
| Qwen3-30B-Instruct (Task 3 Query-Unrelated, `Auto-CoT` F1) | `0.81530` (Paper Table 26: `0.815`) | `0.81624` | `+0.00094` |
