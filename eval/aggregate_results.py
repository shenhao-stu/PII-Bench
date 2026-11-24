#!/usr/bin/env python3
"""
Aggregate Task 1 / Task 2 / Task 3 evaluation JSONLs and compute official PII-Bench scores.

Also fixes a subtle bug in the legacy analysis scripts (`query_pii_hard_id = 2 * pii_hard_id`,
which duplicated the Python list instead of indexing `2 * i`). Use `--legacy-hard-indexing`
only if you explicitly need to compare against the raw legacy script output.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from eval.metrics import cal_unrelated_masking_acc


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate PII-Bench evaluation JSONL outputs.")
    parser.add_argument("--task", choices=["detection", "query_related", "masking"], required=True)
    parser.add_argument("--pred", type=Path, required=True, help="Prediction JSONL (Task 1 or Task 2)")
    parser.add_argument("--recog-pred", type=Path, help="Task 1 detection JSONL (required for --task masking)")
    parser.add_argument("--dataset", type=Path, help="Reference dataset JSONL (required for --task masking if pred lacks entities)")
    parser.add_argument("--hard-indices", type=Path, default=Path("data/paper_exact/hard_samples_line_numbers.json"))
    parser.add_argument("--legacy-hard-indexing", action="store_true", help="Reproduce legacy `2 * list` indexing on PII_final")
    args = parser.parse_args()

    preds = load_jsonl(args.pred)
    if args.task == "detection":
        print(
            json.dumps(
                {
                    "n": len(preds),
                    "strict_f1": round(mean([r["exact_f1"] for r in preds]), 4),
                    "ent_f1": round(mean([r["overall_f1"] for r in preds]), 4),
                    "rougeL_f": round(mean([r["fuzzy_f1"] for r in preds]), 4),
                },
                indent=2,
            )
        )
    elif args.task == "query_related":
        out = {
            "n": len(preds),
            "exact_f1": round(mean([r["exact_f1"] for r in preds]), 4),
            "rougeL_f": round(mean([r["fuzzy_f1"] for r in preds]), 4),
        }
        if len(preds) == 2442 and args.hard_indices.exists():
            hl = json.loads(args.hard_indices.read_text(encoding="utf-8"))["line_numbers"]
            hard_idxs = set(hl) if args.legacy_hard_indexing else {2 * i for i in hl}
            out["multi_f1"] = round(mean([r["exact_f1"] for r in preds[:1228]]), 4)
            out["single_f1"] = round(mean([r["exact_f1"] for r in preds[1228:]]), 4)
            out["hard_f1"] = round(mean([preds[i]["exact_f1"] for i in sorted(hard_idxs)]), 4)
        print(json.dumps(out, indent=2))
    else:
        if not args.recog_pred:
            raise ValueError("--recog-pred is required for --task masking")
        recs = load_jsonl(args.recog_pred)
        ds = load_jsonl(args.dataset) if args.dataset else preds
        ratio = max(1, len(preds) // max(1, len(recs)))
        scores = []
        for idx, (p, ref) in enumerate(zip(preds, ds)):
            r_idx = idx // ratio
            if r_idx >= len(recs):
                break
            sc = cal_unrelated_masking_acc(
                all_pred_subjects=recs[r_idx].get("predict", []),
                related_pred=p.get("predict", []),
                gt_total=ref["entities"]["total"],
                gt_related=ref["most_related"],
                use_fuzzy=True,
            )
            scores.append(sc)
        print(
            json.dumps(
                {
                    "n": len(scores),
                    "query_unrelated_f1": round(mean([s["exact_f1_unrelated"] for s in scores]), 4),
                    "query_unrelated_rougeL_f": round(mean([s["fuzzy_f1_unrelated"] for s in scores]), 4),
                    "joint_avg_f1": round(mean([s["exact_f1"] for s in scores]), 4),
                    "joint_avg_rougeL_f": round(mean([s["fuzzy_f1"] for s in scores]), 4),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
