#!/usr/bin/env python3
"""
Reconstruct legacy `PII_final.jsonl` (= PII_multi_final.jsonl + PII_single_final.jsonl, 2,442 rows)
for scripts that expect the combined file ordering used in ACL 2026 experiments.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["paper_exact", "cleaned"], default="paper_exact")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    if args.variant == "paper_exact":
        multi_p = root / "data" / "paper_exact" / "PII_multi_final.jsonl"
        single_p = root / "data" / "paper_exact" / "PII_single_final.jsonl"
        out_p = args.output or (root / "data" / "paper_exact" / "PII_final.jsonl")
    else:
        multi_p = root / "data" / "cleaned" / "pii_multi.jsonl"
        single_p = root / "data" / "cleaned" / "pii_single.jsonl"
        out_p = args.output or (root / "data" / "cleaned" / "pii_final.jsonl")

    multi_txt = multi_p.read_text(encoding="utf-8")
    single_txt = single_p.read_text(encoding="utf-8")
    out_p.write_text(multi_txt + single_txt, encoding="utf-8")
    n = sum(1 for l in out_p.read_text(encoding="utf-8").splitlines() if l.strip())
    print(f"Wrote {out_p} ({n} rows = 1,228 multi + 1,214 single)")


if __name__ == "__main__":
    main()
