#!/usr/bin/env python3
"""
Extract cooking-completion suitability score from saved lift-event sessions.

Default scoring (no probe temperature):
  S = 100 * (0.4*T + 0.4*C + 0.2*L)
  T = min(running_time / target_time, 1)
  C = min(color_delta / color_threshold, 1)
  L = min(lift_count / expected_lift, 1)

Completion rule (ops-style):
  S >= 85 and T >= 0.9 and C >= 0.8
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SessionRow:
    pot: str
    session_id: str
    food_type: str
    lift_json: str
    session_info: str
    target_time: float
    running_time: float
    color_delta: float
    lift_count: int
    T: float
    C: float
    L: float
    suitability_score: float
    completion_rule_pass: bool
    tracker_completion_detected: bool
    completion_marked: Optional[bool]


def clamp01(x: float) -> float:
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return x


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_row(
    lift_path: Path,
    expected_lift: int,
    color_threshold: float,
    w_t: float,
    w_c: float,
    w_l: float,
) -> SessionRow:
    data = load_json(lift_path)
    parent = lift_path.parent
    session_info_path = parent / "session_info.json"
    session_info = load_json(session_info_path) if session_info_path.exists() else {}

    session_id = str(data.get("session_id", ""))
    pot = str(session_info.get("pot", parent.parent.parent.name if parent.parent.parent.name.startswith("pot") else "unknown"))
    food_type = str(data.get("food_type") or session_info.get("food_type") or parent.name)
    target_time = float(data.get("target_time") or 0.0)
    lift_count = int(data.get("lift_count") or 0)
    events = data.get("lift_events", []) or []

    if events:
        last_ev = events[-1]
        running_time = float(last_ev.get("running_time") or 0.0)
        color_delta = float(last_ev.get("color_delta") or 0.0)
    else:
        running_time = float(session_info.get("duration_sec") or 0.0)
        color_delta = 0.0

    t = clamp01(running_time / target_time) if target_time > 0 else 0.0
    c = clamp01(color_delta / color_threshold) if color_threshold > 0 else 0.0
    l = clamp01(lift_count / expected_lift) if expected_lift > 0 else 0.0
    score = 100.0 * (w_t * t + w_c * c + w_l * l)
    rule_pass = (score >= 85.0) and (t >= 0.9) and (c >= 0.8)

    tracker_completion_detected = bool(data.get("completion_detected", False))
    completion_marked = session_info.get("completion_marked", None)
    if completion_marked is not None:
        completion_marked = bool(completion_marked)

    return SessionRow(
        pot=pot,
        session_id=session_id,
        food_type=food_type,
        lift_json=str(lift_path),
        session_info=str(session_info_path) if session_info_path.exists() else "",
        target_time=target_time,
        running_time=running_time,
        color_delta=color_delta,
        lift_count=lift_count,
        T=t,
        C=c,
        L=l,
        suitability_score=score,
        completion_rule_pass=rule_pass,
        tracker_completion_detected=tracker_completion_detected,
        completion_marked=completion_marked,
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract cooking completion suitability from lift-events json.")
    p.add_argument("--base-dir", default="~/AI_Data", help="Base data directory (default: ~/AI_Data)")
    p.add_argument("--pots", default="pot1,pot2", help="Comma-separated pot folders under base-dir")
    p.add_argument("--expected-lift", type=int, default=3, help="Expected lift count for L term")
    p.add_argument("--color-threshold", type=float, default=25.0, help="Color delta threshold for C term")
    p.add_argument("--w-t", type=float, default=0.4, help="Weight of T term")
    p.add_argument("--w-c", type=float, default=0.4, help="Weight of C term")
    p.add_argument("--w-l", type=float, default=0.2, help="Weight of L term")
    p.add_argument("--output", default=None, help="Output CSV path")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    base_dir = Path(args.base_dir).expanduser()
    pots = [x.strip() for x in args.pots.split(",") if x.strip()]

    s = args.w_t + args.w_c + args.w_l
    if abs(s - 1.0) > 1e-6:
        print(f"[WARN] weights sum={s:.6f}, normalizing")
        args.w_t /= s
        args.w_c /= s
        args.w_l /= s

    lift_files: list[Path] = []
    for pot in pots:
        pattern = base_dir / pot / "session_*" / "*" / "*_lift_events.json"
        for p in sorted(glob.glob(str(pattern))):
            lift_files.append(Path(p))

    if not lift_files:
        print("[ERROR] no *_lift_events.json found")
        return 1

    rows: list[SessionRow] = []
    for lf in lift_files:
        try:
            row = extract_row(
                lf,
                expected_lift=args.expected_lift,
                color_threshold=args.color_threshold,
                w_t=args.w_t,
                w_c=args.w_c,
                w_l=args.w_l,
            )
            rows.append(row)
        except Exception as e:
            print(f"[WARN] skip {lf}: {e}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        out_path = Path(args.output).expanduser()
    else:
        out_path = Path.cwd() / "reports" / f"completion_suitability_{ts}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [f.name for f in SessionRow.__dataclass_fields__.values()]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r.__dict__)

    n = len(rows)
    avg_score = sum(r.suitability_score for r in rows) / n if n else 0.0
    rule_pass = sum(1 for r in rows if r.completion_rule_pass)
    tracker_pass = sum(1 for r in rows if r.tracker_completion_detected)
    marked_pass = sum(1 for r in rows if r.completion_marked is True)

    print(f"[OK] rows={n}")
    print(f"[OK] output={out_path}")
    print(f"[SUMMARY] avg_score={avg_score:.2f}")
    print(f"[SUMMARY] completion_rule_pass={rule_pass}/{n} ({(100.0*rule_pass/n):.1f}%)")
    print(f"[SUMMARY] tracker_completion_detected={tracker_pass}/{n} ({(100.0*tracker_pass/n):.1f}%)")
    print(f"[SUMMARY] completion_marked_true={marked_pass}/{n} ({(100.0*marked_pass/n):.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

