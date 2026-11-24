"""
Official evaluation metrics for PII-Bench (ACL 2026, Appendix F.1 & F.2).

Implements:
  - Task 1: PII Detection (`cal_recog_acc` with subject matching, Strict-F1, Ent-F1, RougeL-F,
    and optional `split_comma_loc=True` matching `get_stats_new_version.py` used for Table 23).
  - Task 2: Query-Related PII Detection (`cal_query_acc`: exact F1 & ROUGE-L fuzzy F1).
  - Task 3: Query-Unrelated PII Masking (`cal_unrelated_masking_acc`: matching `pii_no_related.py`).
  - Privacy-Utility Tradeoff (`calculate_privacy_score`: Equation 17 in Appendix F.2.1).
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any

try:
    from rouge import Rouge as _ThirdPartyRouge  # type: ignore

    _ROUGE_INST = _ThirdPartyRouge()
except Exception:
    _ROUGE_INST = None


def _lcs_length(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    dp = [0] * (len(b) + 1)
    for tok_a in a:
        prev = 0
        for j, tok_b in enumerate(b, 1):
            tmp = dp[j]
            if tok_a == tok_b:
                dp[j] = prev + 1
            elif dp[j - 1] > dp[j]:
                dp[j] = dp[j - 1]
            prev = tmp
    return dp[-1]


def calc_rouge_l(pred: str, gt: str) -> float:
    """Compute ROUGE-L F1 between two entity strings (matches `rouge` library when installed)."""
    if not pred or not gt:
        return 0.0
    if _ROUGE_INST is not None:
        try:
            return float(_ROUGE_INST.get_scores(pred, gt)[0]["rouge-l"]["f"])
        except Exception:
            return 0.0
    # Pure-Python token-level ROUGE-L fallback
    p_toks = pred.split()
    g_toks = gt.split()
    if not p_toks or not g_toks:
        return 0.0
    lcs = _lcs_length(p_toks, g_toks)
    if lcs == 0:
        return 0.0
    prec = lcs / len(p_toks)
    rec = lcs / len(g_toks)
    return 2.0 * prec * rec / (prec + rec)


def process_location(ent: str, pii_type: str) -> dict[str, str]:
    """Split comma-delimited LOC spans at the last comma (used in ACL 2026 Table 23)."""
    if pii_type == "LOC" and "," in ent:
        parts = [p.strip() for p in ent.rsplit(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            return {parts[0]: "LOC", parts[1]: "LOC"}
    return {ent: pii_type}


def build_gt_subjects(record: dict[str, Any], split_comma_loc: bool = False) -> list[dict[str, str]]:
    """Build per-subject ground-truth dicts `{entity: pii_type}` from a PII-Bench record."""
    gt_list: list[dict[str, str]] = []
    for values, types in zip(record["entities"]["values"], record["entities"]["types"]):
        gt: dict[str, str] = {}
        for ent, ty in zip(values, types):
            if split_comma_loc:
                gt.update(process_location(ent, ty))
            else:
                gt[ent] = ty
        gt_list.append(gt)
    return gt_list


def parse_recognition_result(response: str) -> list[dict[str, str]]:
    """Parse Task 1 model output (`Subject {N} {"ent": "TYPE", ...}`)."""
    try:
        subjects = re.findall(r"Subject\s*(?:\{?\d+\}?|\d+)\s*\{(.*?)\}", response, re.DOTALL)
        result_list: list[dict[str, str]] = []
        for subject in subjects:
            try:
                subject_dict = json.loads("{" + subject.strip() + "}")
                if not isinstance(subject_dict, dict):
                    continue
                normalized: dict[str, str] = {}
                if any(isinstance(v, list) for v in subject_dict.values()):
                    for type_key, entities in subject_dict.items():
                        if isinstance(entities, list):
                            for entity in entities:
                                normalized[str(entity)] = str(type_key)
                else:
                    normalized = {str(k): str(v) for k, v in subject_dict.items()}
                result_list.append(normalized)
            except json.JSONDecodeError:
                continue
        return result_list
    except Exception:
        return []


def parse_query_result(response: str) -> list[str]:
    """Parse Task 2 model output (`### Answer: ["ent1", "ent2"]`)."""
    text = response.strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            res = json.loads(text)
            if isinstance(res, list):
                return [str(x) for x in res if x is not Ellipsis]
        except json.JSONDecodeError:
            pass

    block = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if block:
        try:
            res = json.loads(block.group(1).strip())
            if isinstance(res, list):
                return [str(x) for x in res if x is not Ellipsis]
        except json.JSONDecodeError:
            pass

    ans = re.search(r"##+\s*Answer[:：]?\s*(\[.*?\])", text, re.DOTALL)
    if ans:
        raw = ans.group(1).strip()
        for parser in (json.loads, ast.literal_eval):
            try:
                res = parser(raw)
                if isinstance(res, list):
                    return [str(x) for x in res if x is not Ellipsis]
            except Exception:
                continue
    return []


def cal_pair_score(pred: dict[str, str], gt: dict[str, str], use_fuzzy: bool = True) -> tuple[float, ...]:
    """Compute Strict & ROUGE-L fuzzy Precision/Recall/F1 for a single (pred_subj, gt_subj) pair."""
    pred_l = {k.lower(): v.lower() for k, v in pred.items()}
    gt_l = {k.lower(): v.lower() for k, v in gt.items()}

    exact_correct = sum(1 for k, v in pred_l.items() if k in gt_l and gt_l[k] == v)
    exact_p = exact_correct / len(pred_l) if pred_l else 0.0
    exact_r = exact_correct / len(gt_l) if gt_l else 0.0
    exact_f1 = 2 * exact_p * exact_r / (exact_p + exact_r) if (exact_p + exact_r) else 0.0

    if not use_fuzzy:
        return exact_p, exact_r, exact_f1, 0.0, 0.0, 0.0, 0.0

    fuzzy_correct = 0
    rouge_scores: list[float] = []
    for pk, pv in pred_l.items():
        best_score = 0.0
        best_key = None
        for gk in gt_l:
            sc = calc_rouge_l(pk, gk)
            if sc > best_score:
                best_score = sc
                best_key = gk
        if best_key is not None and best_score > 0.8:
            val_score = calc_rouge_l(pv, gt_l[best_key])
            if val_score > 0.9:
                fuzzy_correct += 1
            rouge_scores.append((best_score + val_score) / 2.0)

    fuzzy_p = fuzzy_correct / len(pred_l) if pred_l else 0.0
    fuzzy_r = fuzzy_correct / len(gt_l) if gt_l else 0.0
    fuzzy_f1 = 2 * fuzzy_p * fuzzy_r / (fuzzy_p + fuzzy_r) if (fuzzy_p + fuzzy_r) else 0.0
    avg_rouge = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0.0
    return exact_p, exact_r, exact_f1, fuzzy_p, fuzzy_r, fuzzy_f1, avg_rouge


def find_best_matches(pred_list: list[dict[str, str]], gt_list: list[dict[str, str]]) -> list[tuple[int, int]]:
    """Greedy maximum-Strict-F1 one-to-one subject matching."""
    if not pred_list or not gt_list:
        return []
    scores = []
    for i, pred in enumerate(pred_list):
        for j, gt in enumerate(gt_list):
            _, _, exact_f1, *_ = cal_pair_score(pred, gt, use_fuzzy=False)
            scores.append((i, j, exact_f1))
    scores.sort(key=lambda x: x[2], reverse=True)
    used_p, used_g, matches = set(), set(), []
    for pi, gi, _ in scores:
        if pi not in used_p and gi not in used_g:
            matches.append((pi, gi))
            used_p.add(pi)
            used_g.add(gi)
            if len(matches) == min(len(pred_list), len(gt_list)):
                break
    return matches


def cal_recog_acc(pred_list: list[dict[str, str]], gt_list: list[dict[str, str]], use_fuzzy: bool = True) -> dict[str, float]:
    """Task 1 (PII Detection) metrics: Strict-F1 (`exact_f1`), Ent-F1 (`overall_f1`), RougeL-F (`fuzzy_f1`)."""
    if not pred_list or not gt_list:
        return {
            "exact_precision": 0.0,
            "exact_recall": 0.0,
            "exact_f1": 0.0,
            "fuzzy_precision": 0.0,
            "fuzzy_recall": 0.0,
            "fuzzy_f1": 0.0,
            "rouge_l": 0.0,
            "overall_precision": 0.0,
            "overall_recall": 0.0,
            "overall_f1": 0.0,
        }

    all_pred = {ent.lower() for subj in pred_list for ent in subj}
    all_gt = {ent.lower() for subj in gt_list for ent in subj}
    ov_correct = len(all_pred & all_gt)
    ov_p = ov_correct / len(all_pred) if all_pred else 0.0
    ov_r = ov_correct / len(all_gt) if all_gt else 0.0
    ov_f1 = 2 * ov_p * ov_r / (ov_p + ov_r) if (ov_p + ov_r) else 0.0

    matches = find_best_matches(pred_list, gt_list)
    sums = [0.0] * 7
    for pi, gi in matches:
        sc = cal_pair_score(pred_list[pi], gt_list[gi], use_fuzzy=use_fuzzy)
        for k in range(7):
            sums[k] += sc[k]

    n_pred, n_gt = len(pred_list), len(gt_list)
    denom = max(n_pred, n_gt)
    return {
        "exact_precision": sums[0] / n_pred,
        "exact_recall": sums[1] / n_gt,
        "exact_f1": sums[2] / denom,
        "fuzzy_precision": sums[3] / n_pred,
        "fuzzy_recall": sums[4] / n_gt,
        "fuzzy_f1": sums[5] / denom,
        "rouge_l": sums[6] / denom,
        "overall_precision": ov_p,
        "overall_recall": ov_r,
        "overall_f1": ov_f1,
    }


def cal_query_acc(pred: list[str], gt: list[str], use_fuzzy: bool = True) -> dict[str, float]:
    """Task 2 (Query-Related PII Detection) metrics: exact F1 & ROUGE-L fuzzy F1."""
    if not pred or not gt:
        return {
            "exact_precision": 0.0,
            "exact_recall": 0.0,
            "exact_f1": 0.0,
            "fuzzy_precision": 0.0,
            "fuzzy_recall": 0.0,
            "fuzzy_f1": 0.0,
            "rouge_l": 0.0,
        }
    pred_l = [x.lower() for x in pred if x is not Ellipsis]
    gt_l = [x.lower() for x in gt if x is not Ellipsis]

    exact_correct = len(set(pred_l) & set(gt_l))
    ep = exact_correct / len(pred_l) if pred_l else 0.0
    er = exact_correct / len(gt_l) if gt_l else 0.0
    ef1 = 2 * ep * er / (ep + er) if (ep + er) else 0.0

    if not use_fuzzy:
        return {
            "exact_precision": ep,
            "exact_recall": er,
            "exact_f1": ef1,
            "fuzzy_precision": 0.0,
            "fuzzy_recall": 0.0,
            "fuzzy_f1": 0.0,
            "rouge_l": 0.0,
        }

    matches = 0
    rouge_scores: list[float] = []
    for p in pred_l:
        best_sc = 0.0
        for g in gt_l:
            sc = calc_rouge_l(p, g)
            if sc > best_sc:
                best_sc = sc
        if best_sc > 0.8:
            matches += 1
            rouge_scores.append(best_sc)

    fp = matches / len(pred_l) if pred_l else 0.0
    fr = matches / len(gt_l) if gt_l else 0.0
    ff1 = 2 * fp * fr / (fp + fr) if (fp + fr) else 0.0
    avg_r = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0.0
    return {
        "exact_precision": ep,
        "exact_recall": er,
        "exact_f1": ef1,
        "fuzzy_precision": fp,
        "fuzzy_recall": fr,
        "fuzzy_f1": ff1,
        "rouge_l": avg_r,
    }


def cal_unrelated_masking_acc(
    all_pred_subjects: list[dict[str, str]],
    related_pred: list[str],
    gt_total: list[str],
    gt_related: list[str],
    use_fuzzy: bool = True,
) -> dict[str, float]:
    """Task 3 (Query-Unrelated PII Masking) metrics matching `analysis/ACL26/pii_no_related.py`."""
    all_piis_pred = [ent for subj in all_pred_subjects if isinstance(subj, dict) for ent in subj.keys()]
    unrelated_pred = [pii for pii in all_piis_pred if pii not in related_pred]
    related_pred_filtered = [pii for pii in all_piis_pred if pii in related_pred]
    gt_unrelated = [ent for ent in gt_total if ent not in gt_related]

    rel_m = cal_query_acc(related_pred_filtered, gt_related, use_fuzzy=use_fuzzy)
    unrel_m = cal_query_acc(unrelated_pred, gt_unrelated, use_fuzzy=use_fuzzy)
    return {
        "exact_f1": (rel_m["exact_f1"] + unrel_m["exact_f1"]) / 2.0,
        "fuzzy_f1": (rel_m["fuzzy_f1"] + unrel_m["fuzzy_f1"]) / 2.0,
        "exact_f1_related": rel_m["exact_f1"],
        "exact_f1_unrelated": unrel_m["exact_f1"],
        "fuzzy_f1_related": rel_m["fuzzy_f1"],
        "fuzzy_f1_unrelated": unrel_m["fuzzy_f1"],
    }


def calculate_privacy_score(original_desc: str, masked_desc: str, entities_total: list[str]) -> float:
    """Equation (17) in Appendix F.2.1: Privacy Protection Score P = 1 - leaked / total."""
    total_occ = sum(original_desc.count(e) for e in entities_total)
    leaked_occ = sum(masked_desc.count(e) for e in entities_total)
    return 1.0 - (leaked_occ / max(1, total_occ))
