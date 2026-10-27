#!/usr/bin/env python3
"""
Evaluate manual completion labels against AI completion predictions.

Metrics:
- MAE (seconds) on sessions with both GT and AI predicted time
- Precision/Recall/F1 using tolerance window (default: +-3s)

Run:
  python3 scripts/evaluate_completion_labels.py \
    --labels /home/yjk/jetson-food-ai/reports/2026-02-15/data/manual_completion_labels.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_LABELS = Path(
    "/home/yjk/jetson-food-ai/reports/2026-02-15/data/manual_completion_labels.csv"
)
DEFAULT_OUT = Path(
    "/home/yjk/jetson-food-ai/reports/2026-02-15/data/completion_accuracy_eval.csv"
)


def parse_bool(v: object) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes"}


def parse_float(v: object):
    try:
        if v is None or str(v).strip() == "":
            return None
        return float(v)
    except Exception:
        return None


def run(labels_csv: Path, out_csv: Path, tolerance_sec: float) -> int:
    if not labels_csv.exists():
        print(f"[ERROR] labels not found: {labels_csv}")
        return 1

    with labels_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("[ERROR] labels csv is empty")
        return 1

    detail_rows = []
    tp = fp = fn = 0
    abs_errs = []

    for r in rows:
        ai_detected = parse_bool(r.get("ai_detected"))
        ai_sec = parse_float(r.get("ai_pred_offset_sec"))
        gt_sec = parse_float(r.get("gt_offset_sec"))

        if gt_sec is None:
            status = "SKIP_NO_GT"
            abs_err = None
        else:
            if ai_detected:
                if ai_sec is None:
                    status = "FP_NO_TIME"
                    fp += 1
                    abs_err = None
                else:
                    abs_err = abs(ai_sec - gt_sec)
                    if abs_err <= tolerance_sec:
                        status = "TP"
                        tp += 1
                    else:
                        status = "FP_OUTSIDE_TOL"
                        fp += 1
                    abs_errs.append(abs_err)
            else:
                status = "FN_MISS"
                fn += 1
                abs_err = None

        detail_rows.append(
            {
                "pot": r.get("pot", ""),
                "session_id": r.get("session_id", ""),
                "food_type": r.get("food_type", ""),
                "ai_detected": str(ai_detected),
                "ai_pred_offset_sec": "" if ai_sec is None else f"{ai_sec:.6f}",
                "gt_offset_sec": "" if gt_sec is None else f"{gt_sec:.6f}",
                "abs_error_sec": "" if abs_err is None else f"{abs_err:.6f}",
                "status": status,
            }
        )

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    mae = (sum(abs_errs) / len(abs_errs)) if abs_errs else None

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "pot",
        "session_id",
        "food_type",
        "ai_detected",
        "ai_pred_offset_sec",
        "gt_offset_sec",
        "abs_error_sec",
        "status",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(detail_rows)

    print("=" * 80)
    print("Completion Label Evaluation")
    print("=" * 80)
    print(f"labels_csv: {labels_csv}")
    print(f"out_csv   : {out_csv}")
    print(f"tolerance : +/-{tolerance_sec:.3f}s")
    print("-" * 80)
    print(f"rows: {len(rows)}")
    print(f"TP={tp} FP={fp} FN={fn}")
    print(f"Precision={precision:.4f}")
    print(f"Recall   ={recall:.4f}")
    print(f"F1       ={f1:.4f}")
    print(f"MAE(sec) ={mae:.4f}" if mae is not None else "MAE(sec) =N/A (no paired GT/AI time)")
    print("=" * 80)
    return 0


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate completion labels (F1/MAE)")
    p.add_argument("--labels", type=Path, default=DEFAULT_LABELS, help=f"Label CSV path (default: {DEFAULT_LABELS})")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output detail CSV (default: {DEFAULT_OUT})")
    p.add_argument("--tolerance-sec", type=float, default=3.0, help="Tolerance window in seconds (default: 3.0)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    return run(args.labels, args.out, args.tolerance_sec)


if __name__ == "__main__":
    raise SystemExit(main())

