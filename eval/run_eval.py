#!/usr/bin/env python3
"""
Clean OpenAI-compatible evaluation runner for PII-Bench (ACL 2026).

Usage:
  export OPENAI_API_KEY="your-api-key"
  export OPENAI_BASE_URL="https://api.openai.com/v1"   # optional for OpenAI-compatible/vLLM endpoints

  # Task 1: PII Detection on PII-Single
  python -m eval.run_eval --data data/cleaned/pii_single.jsonl --task detection --model gpt-4o --output outputs/det_single_gpt4o.jsonl

  # Task 2: Query-Related PII Detection with Self-CoT
  python -m eval.run_eval --data data/cleaned/pii_single.jsonl --task query_related --prompt cot --model gpt-4o --output outputs/qrel_cot_single_gpt4o.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from eval.metrics import (
    build_gt_subjects,
    cal_query_acc,
    cal_recog_acc,
    parse_query_result,
    parse_recognition_result,
)
from eval.prompts import (
    COMPLEX_RECOGNITION_PROMPT,
    MULTI_RECOGNITION_PROMPT,
    PII_DEFINITION,
    QUERY_PROMPT_MAP,
    SINGLE_RECOGNITION_PROMPT,
)


def load_records(path: Path, deduplicate_desc: bool) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            rec = json.loads(s)
            if deduplicate_desc:
                if rec["usr_desc"] in seen:
                    continue
                seen.add(rec["usr_desc"])
            records.append(rec)
    return records


def build_detection_prompt(record: dict[str, Any]) -> str:
    n_subj = len(record["entities"]["values"])
    if n_subj > 2:
        tmpl = COMPLEX_RECOGNITION_PROMPT
    elif n_subj == 2:
        tmpl = MULTI_RECOGNITION_PROMPT
    else:
        tmpl = SINGLE_RECOGNITION_PROMPT
    return tmpl.format(user_desc=record["usr_desc"], pii_definition=PII_DEFINITION)


def build_query_prompt(record: dict[str, Any], prompt_type: str) -> str:
    tmpl = QUERY_PROMPT_MAP[prompt_type]
    if prompt_type == "choice":
        return tmpl.format(
            desc=record["usr_desc"],
            query=record["query"],
            choices=json.dumps(record["entities"]["total"], ensure_ascii=False),
        )
    return tmpl.format(desc=record["usr_desc"], query=record["query"])


def call_openai_compatible(client: Any, model: str, prompt: str, max_tokens: int, temperature: float, retries: int = 5) -> str:
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=1.0,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(min(10, 2 ** attempt))
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate an OpenAI-compatible LLM on PII-Bench.")
    parser.add_argument("--data", type=Path, required=True, help="Path to JSONL split (e.g., data/cleaned/pii_single.jsonl)")
    parser.add_argument("--task", choices=["detection", "query_related"], required=True)
    parser.add_argument("--prompt", choices=sorted(QUERY_PROMPT_MAP.keys()), default="naive", help="Prompt strategy for Task 2")
    parser.add_argument("--model", type=str, required=True, help="Model identifier")
    parser.add_argument("--output", type=Path, required=True, help="Output JSONL path")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--split-comma-loc", action="store_true", help="Apply comma-LOC splitting (ACL 2026 Table 23)")
    parser.add_argument("--limit", type=int, default=0, help="Optional cap on number of evaluated records (0 = all)")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required.")
    base_url = os.environ.get("OPENAI_BASE_URL")

    from openai import OpenAI  # imported lazily so metrics/prompts work without openai installed

    client = OpenAI(api_key=api_key, base_url=base_url)
    records = load_records(args.data, deduplicate_desc=(args.task == "detection"))
    if args.limit > 0:
        records = records[: args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    exact_f1s, fuzzy_f1s, ent_f1s = [], [], []

    with args.output.open("w", encoding="utf-8") as fout:
        for idx, rec in enumerate(records):
            if args.task == "detection":
                prompt = build_detection_prompt(rec)
                raw_out = call_openai_compatible(client, args.model, prompt, args.max_tokens, args.temperature)
                pred = parse_recognition_result(raw_out)
                gt = build_gt_subjects(rec, split_comma_loc=args.split_comma_loc)
                metrics = cal_recog_acc(pred, gt, use_fuzzy=True)
                ent_f1s.append(metrics["overall_f1"])
            else:
                prompt = build_query_prompt(rec, args.prompt)
                raw_out = call_openai_compatible(client, args.model, prompt, args.max_tokens, args.temperature)
                pred = parse_query_result(raw_out)
                metrics = cal_query_acc(pred, rec["most_related"], use_fuzzy=True)

            exact_f1s.append(metrics["exact_f1"])
            fuzzy_f1s.append(metrics["fuzzy_f1"])

            out_rec = {
                "sample_id": rec.get("sample_id", f"row_{idx:04d}"),
                "id": rec["id"],
                "from_id": rec["from_id"],
                "predict": pred,
                **metrics,
            }
            fout.write(json.dumps(out_rec, ensure_ascii=False) + "\n")
            if (idx + 1) % 50 == 0 or (idx + 1) == len(records):
                print(f"[{idx+1}/{len(records)}] mean exact_f1={sum(exact_f1s)/len(exact_f1s):.4f} fuzzy_f1={sum(fuzzy_f1s)/len(fuzzy_f1s):.4f}")

    summary = {
        "data": str(args.data),
        "task": args.task,
        "prompt": args.prompt if args.task == "query_related" else "detection",
        "model": args.model,
        "n": len(records),
        "mean_exact_f1": round(sum(exact_f1s) / max(1, len(exact_f1s)), 4),
        "mean_fuzzy_f1": round(sum(fuzzy_f1s) / max(1, len(fuzzy_f1s)), 4),
    }
    if ent_f1s:
        summary["mean_ent_f1"] = round(sum(ent_f1s) / len(ent_f1s), 4)
    print("SUMMARY:", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
