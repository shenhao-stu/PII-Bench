# PII-Bench: Evaluating Query-Aware Privacy Protection Systems (ACL 2026)

[![Conference](https://img.shields.io/badge/ACL-2026-blue.svg)](#citation)
[![Dataset](https://img.shields.io/badge/Dataset-2%2C842%20Samples-green.svg)](#dataset-statistics)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-shenhao%2FPII--Bench-yellow.svg)](https://huggingface.co/datasets/shenhao/PII-Bench)
[![ModelScope](https://img.shields.io/badge/ModelScope-shenhao23%2FPII--Bench-purple.svg)](https://modelscope.cn/datasets/shenhao23/PII-Bench)
[![License: Data CC BY 4.0](https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey.svg)](LICENSE)
[![License: Code Apache 2.0](https://img.shields.io/badge/Code%20License-Apache%202.0-lightgrey.svg)](LICENSE)

English | **[中文](README_zh.md)**

Official dataset and evaluation repository for the ACL 2026 paper:

- **Paper:** *PII-Bench: Evaluating Query-Aware Privacy Protection Systems* (ACL 2026)
- **Authors:** Hao Shen<sup>1,2</sup>, Zhouhong Gu<sup>3</sup>, HaoKai Hong<sup>1</sup>, Weili Han<sup>1,2\*</sup>, Hongfeng Chai<sup>1</sup>
- **Affiliations:** <sup>1</sup>Institute of Fintech, Fudan University; <sup>2</sup>Laboratory of Data Analytics and Security, Fudan University; <sup>3</sup>Fudan University
- **Official Dataset Mirrors:**
  - **HuggingFace (Parquet):** https://huggingface.co/datasets/shenhao/PII-Bench
  - **ModelScope (Parquet, China Mirror):** https://modelscope.cn/datasets/shenhao23/PII-Bench

> **Iterative Updates Notice:** PII-Bench is actively maintained and **will be iteratively updated** with future refinements and potential additional splits (such as `PII-Real` in a future release). The **`data/paper_exact/`** directory (and `paper_exact` Hub config) remains permanently frozen to guarantee **0.0000** bit-exact reproducibility of all ACL 2026 paper results.

---

## Overview

Users interacting with Large Language Models (LLMs) frequently include Personally Identifiable Information (PII) in their prompts. Leaving all PII exposed (*No Masking*) risks privacy breaches, while redacting every PII entity (*All PII Masking*) destroys task utility.

**PII-Bench** evaluates **Query-Unrelated PII Masking** across **2,842 core test samples**, **7 coarse PII types** (`PER`, `CODE`, `LOC`, `ORG`, `DEM`, `DATETIME`, `QUANTITY`), and **55 fine-grained subcategories** through three tasks:

1. **Task 1 — PII Detection:** Extract minimal spans for all PII entities $E$, attribute each entity to its subject $s \in S$, and classify its PII type $t \in T$.
2. **Task 2 — Query-Related PII Detection:** Identify the minimal subset $E_q \subseteq E$ necessary to answer user query $q$.
3. **Task 3 — Query-Unrelated PII Masking:** Mask all query-unrelated PII entities $E \setminus E_q$ while preserving $E_q$ and prompt utility.

---

## Repository Structure

```text
.
├── data/
│   ├── cleaned/                         # Recommended v1.1 schema-verified JSONLs (== HF/MS `default` config)
│   │   ├── pii_single.jsonl             # 1,214 samples (607 single-subject descs × 2 queries)
│   │   ├── pii_multi.jsonl              # 1,228 samples (614 two-subject descs × 2 queries)
│   │   ├── pii_hard.jsonl               # 200 challenging samples (114 single + 86 multi)
│   │   ├── pii_distract.jsonl           # 200 multi-party dialogue samples (~7.5 subjects/sample)
│   │   └── pii_masked_200.jsonl         # 200 samples for Section 4.5 Privacy-Utility (span-safe v1.1; == `privacy_utility`)
│   └── paper_exact/                     # Frozen bit-exact ACL 2026 ground truth (Tables 3–26 parity; == `paper_exact`)
│       ├── PII_single_final.jsonl       # 1,214 samples
│       ├── PII_multi_final.jsonl        # 1,228 samples
│       ├── PII_hard.jsonl               # 200 samples (leaked 'predict' column removed)
│       ├── PII_distract.jsonl           # 200 samples
│       ├── PII_masked.jsonl             # 200 samples (verbatim Section 4.5 prompts)
│       └── hard_samples_line_numbers.json
├── metadata/
│   └── pii_taxonomy.json                # Complete 7-type / 54-observed-tag taxonomy & Table 11 map
├── eval/
│   ├── prompts.py                       # Official ACL 2026 Appendix F.6 prompts
│   ├── metrics.py                       # Exact Task 1 / Task 2 / Task 3 / Privacy metrics
│   ├── run_eval.py                      # OpenAI-compatible evaluation CLI (uses env vars, no secrets)
│   ├── aggregate_results.py             # Aggregation script for Tables 4, 6, 7, 9, 21, 23, 25, 26
│   └── verify_dataset.py                # Standalone integrity checker
├── scripts/
│   └── build_pii_final.py               # Reconstructs combined PII_final.jsonl (multi + single)
├── CHANGELOG_DATA_CLEANING.md           # Full transparency log of v1.1 cleaning & metric parity
├── requirements.txt
└── LICENSE
```

### Which Variant Should I Use? (`cleaned` vs. HF/MS `default` vs. `paper_exact`)

| GitHub Folder | HuggingFace / ModelScope Config | Difference & Intended Use |
|---|---|---|
| **`data/cleaned/`** *(recommended)* | **`default`** (and `privacy_utility`) | **Identical v1.1 cleaned data** (GitHub uses the descriptive name `cleaned`; HuggingFace & ModelScope use `default` so `load_dataset("shenhao/PII-Bench")` loads it automatically). Fixes 474 audited tooling/masking artifacts (4 `UNKNOWN` types, 18 array-length mismatches, 3 ungrounded ghost entities, 1 mislabeled coarse type, 2 twin-description asymmetries, whitespace padding, 8 rare tag synonyms, and span-safe masking on `pii_masked_200.jsonl`). Verified $\le +0.0015$ F1 delta with 100% preserved model rankings. |
| **`data/paper_exact/`** *(frozen)* | **`paper_exact`** | **Bit-exact ACL 2026 ground truth** (0.0000 drift against Tables 3–26; only strips the leaked `'predict'` field from `PII_hard.jsonl`). |

See [CHANGELOG_DATA_CLEANING.md](CHANGELOG_DATA_CLEANING.md) for the complete rule-by-rule audit and empirical metric verification.

---

## Dataset Statistics

| Split | #Samples | Unique Descs | Avg #Subjects | Avg #Chars (Desc) | Avg #PII (Desc) | Avg #Chars (Query) | Avg #PII (Query) | Entities (`cleaned` v1.1 / `paper_exact` Table 10) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **PII-Single** | 1,214 | 607 | 1.00 | 893.48 | 7.66 / 7.67 | 211.21 | 1.95 | 9,300 / 9,303 |
| **PII-Multi** | 1,228 | 614 | 2.00 | 652.65 | 13.14 | 236.21 | 2.06 | 16,136 / 16,136 |
| **PII-Hard**\* | 200 | 200 | 1.43 | 746.08 | 9.18 / 9.17 | 222.66 | 2.06 | 1,835 / 1,834 |
| **PII-Distract** | 200 | 200 | 7.47 | 4,403.64 | 51.05 / 51.08 | 859.68 / 859.69 | 5.82 | 10,210 / 10,211 |
| **All** | **2,842** | **1,421\*\*** | **1.92** | **1,026.07** | **13.19** | **268.45** | **2.28** | **37,481 / 37,484** |

- \* `PII-Hard` is an overlapping challenging subset drawn from `PII-Single` (114) and `PII-Multi` (86) via `data/paper_exact/hard_samples_line_numbers.json`.
- \*\* 607 (`single`) + 614 (`multi`) + 200 (`distract`) = 1,421 non-overlapping unique descriptions (`hard` reuses 200 of the 1,221 `single`+`multi` descriptions).

---

## Quickstart

### 1. Install & Verify Dataset Integrity

```bash
pip install -r requirements.txt
python eval/verify_dataset.py
```

### 2. Load via HuggingFace or ModelScope

```python
from datasets import load_dataset

# Recommended cleaned v1.1 release (identical to data/cleaned/)
ds = load_dataset("shenhao/PII-Bench")

# Frozen bit-exact ACL 2026 reproduction split (identical to data/paper_exact/)
ds_exact = load_dataset("shenhao/PII-Bench", "paper_exact")

# Section 4.5 Privacy-Utility subset
ds_pu = load_dataset("shenhao/PII-Bench", "privacy_utility", split="test")
```

Or via ModelScope (China mirror):
```bash
pip install modelscope
ms download shenhao23/PII-Bench --repo-type dataset --local_dir ./PII-Bench
```

### 3. Run Evaluation (OpenAI-Compatible API / Local vLLM)

```bash
export OPENAI_API_KEY="your-api-key"
# Optional for local vLLM or custom OpenAI-compatible gateway:
# export OPENAI_BASE_URL="http://127.0.0.1:8000/v1"

# Task 1: PII Detection (automatically deduplicates to unique user descriptions)
python -m eval.run_eval \
  --data data/cleaned/pii_single.jsonl \
  --task detection \
  --model gpt-4o \
  --output outputs/det_single_gpt4o.jsonl

# Task 2: Query-Related PII Detection (strategies: naive, choice, cot, auto_cot, self_consistency, plan_solve)
python -m eval.run_eval \
  --data data/cleaned/pii_single.jsonl \
  --task query_related \
  --prompt cot \
  --model gpt-4o \
  --output outputs/qrel_cot_single_gpt4o.jsonl

# Task 3: Aggregate Query-Unrelated PII Masking score from Task 1 + Task 2 outputs
python -m eval.aggregate_results \
  --task masking \
  --pred outputs/qrel_cot_single_gpt4o.jsonl \
  --recog-pred outputs/det_single_gpt4o.jsonl \
  --dataset data/cleaned/pii_single.jsonl
```

If you need the legacy combined `PII_final.jsonl` (`PII_multi + PII_single`, 2,442 rows):
```bash
python scripts/build_pii_final.py --variant paper_exact
```

---

## Key Benchmark Results (ACL 2026)

### Task 1: PII Detection (Strict-F1, Tables 6 & 23)

| Model | PII-Single | PII-Multi | PII-Hard | PII-Distract |
|---|---:|---:|---:|---:|
| Human Baseline (Table 2) | 0.972 | 0.954 | 0.913 | 0.928 |
| GPT-4o | 0.893 | **0.891** | 0.817 | 0.715 |
| Claude-3.5-Sonnet | 0.858 | 0.890 | 0.813 | **0.910** |
| DeepSeek-V3 | **0.903** | 0.884 | 0.838 | 0.658 |
| Llama-3.1-70B-Instruct | 0.881 | 0.883 | **0.840** | 0.834 |
| Qwen-2.5-72B-Instruct | 0.866 | 0.853 | 0.804 | 0.647 |
| GPT-5 (Table 23) | 0.871 | **0.884** | **0.840** | **0.832** |
| DeepSeek-V3.2 (Table 23) | 0.856 | 0.838 | 0.779 | 0.719 |
| DeepSeek-R1 (Table 23) | **0.876** | 0.879 | 0.835 | 0.826 |

### Task 2 & Task 3: Recent LLMs on PII-Single (Table 9, best non-oracle F1)

| Model | PII Detection (Strict-F1) | Query-Related Detection (F1) | Query-Unrelated Masking (F1) |
|---|---:|---:|---:|
| Human Baseline | 0.972 | 0.951 | — |
| GPT-5 | 0.871 | 0.733 | 0.840 |
| DeepSeek-V3.2 | 0.856 | **0.765** | **0.852** |
| DeepSeek-R1 | **0.876** | 0.745 | 0.850 |

---

## Realism & Maintenance

- All 2,842 core benchmark samples in `data/cleaned/` and `data/paper_exact/` are synthetic and intentionally preserve realistic formats (such as common email domains like `@163.com` / `@gmail.com` and regional license plates like `湘A-65225`, `黑A53975`, `鄂A·55978`) for authentic PII evaluation.
- PII-Bench will be iteratively updated over time; check the GitHub releases / changelog for future versions and newly added splits.

## Citation

```bibtex
@inproceedings{shen2026piibench,
  title     = {{PII-Bench}: Evaluating Query-Aware Privacy Protection Systems},
  author    = {Shen, Hao and Gu, Zhouhong and Hong, HaoKai and Han, Weili and Chai, Hongfeng},
  booktitle = {Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (ACL 2026)},
  year      = {2026}
}
```
