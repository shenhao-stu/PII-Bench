#!/usr/bin/env python3
"""Standalone integrity checker for local PII-Bench JSONL splits."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

VALID_TYPES = {"PER", "CODE", "LOC", "ORG", "DEM", "DATETIME", "QUANTITY"}


def verify_cleaned(data_dir: Path, taxonomy_path: Path) -> None:
    taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    valid_tags = {x["tag"] for x in taxonomy["subcategories"]}
    expected_counts = {
        "pii_single.jsonl": 1214,
        "pii_multi.jsonl": 1228,
        "pii_hard.jsonl": 200,
        "pii_distract.jsonl": 200,
        "pii_masked_200.jsonl": 200,
    }
    seen_sids = set()
    for fn, exp_n in expected_counts.items():
        rows = [json.loads(l) for l in (data_dir / fn).read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(rows) == exp_n, f"{fn}: expected {exp_n}, got {len(rows)}"
        tc = Counter()
        for i, r in enumerate(rows):
            assert "predict" not in r
            assert r["sample_id"] not in seen_sids
            seen_sids.add(r["sample_id"])
            e = r["entities"]
            assert len(e["total"]) == len(e["total_subjects"]) == len(e["total_types"]) == len(e["total_tags"])
            assert len(e["values"]) == len(e["types"]) == len(e["tags"]) == r["num_subjects"]
            assert len(r["most_related"]) == len(r["subjects"])
            desc_low = r["usr_desc"].lower()
            for ent, ty, tg in zip(e["total"], e["total_types"], e["total_tags"]):
                assert ent == ent.strip() and ent.lower() in desc_low, f"{fn}[{i}] bad entity {ent!r}"
                assert ty in VALID_TYPES and tg in valid_tags
                tc[ty] += 1
            for m in r["most_related"]:
                assert m in set(e["total"])
            if fn == "pii_masked_200.jsonl":
                assert r["privacy_score_masked"] == 1.0
                for m in r["most_related"]:
                    assert m.lower() in r["adaptive_mask_usr_desc"].lower(), f"{fn}[{i}] most_related masked: {m!r}"
        if fn in ("pii_single.jsonl", "pii_multi.jsonl"):
            for i in range(0, len(rows), 2):
                assert rows[i]["usr_desc"] == rows[i + 1]["usr_desc"]
                assert rows[i]["entities"] == rows[i + 1]["entities"]
        print(f"PASS {fn:22s}: n={len(rows):4d}, entities={sum(tc.values()):5d}, types={dict(tc)}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    verify_cleaned(root / "data" / "cleaned", root / "metadata" / "pii_taxonomy.json")
    print("ALL LOCAL DATASET INTEGRITY CHECKS PASSED!")
