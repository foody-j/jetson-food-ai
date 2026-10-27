#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import json
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Export lift-event trend tables from *_lift_events.json")
    p.add_argument("--base-dir", default="~/AI_Data", help="AI_Data root")
    p.add_argument("--out-dir", default="~/jetson-food-ai/reports/lift_event_trends", help="Output folder")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    base_dir = Path(args.base_dir).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    pattern = str(base_dir / "pot*" / "session_*" / "*" / "*_lift_events.json")
    files = sorted(Path(p) for p in glob.glob(pattern))
    if not files:
        print("[ERROR] no *_lift_events.json found")
        return 1

    events_csv = out_dir / "lift_event_trends.csv"
    summary_csv = out_dir / "lift_event_session_summary.csv"

    event_fields = [
        "pot",
        "session_id",
        "food_type",
        "event_index",
        "running_time_sec",
        "color_delta",
        "food_area_ratio",
        "brown_ratio",
        "golden_ratio",
    ]
    summary_fields = [
        "pot",
        "session_id",
        "food_type",
        "lift_count",
        "target_time_sec",
        "completion_detected",
        "first_rt_sec",
        "last_rt_sec",
        "first_delta",
        "last_delta",
        "max_delta",
        "delta_gain",
        "brown_gain",
        "golden_gain",
    ]

    session_count = 0
    session_with_events = 0
    total_events = 0

    with events_csv.open("w", encoding="utf-8", newline="") as ef, summary_csv.open(
        "w", encoding="utf-8", newline=""
    ) as sf:
        ew = csv.DictWriter(ef, fieldnames=event_fields)
        sw = csv.DictWriter(sf, fieldnames=summary_fields)
        ew.writeheader()
        sw.writeheader()

        for fp in files:
            session_count += 1
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue

            events = data.get("lift_events", []) or []
            pot = str(data.get("pot_name", "")).lower().replace("pot", "pot")
            if pot not in ("pot1", "pot2"):
                # fallback from path
                pot = "pot1" if "pot1" in fp.parts else ("pot2" if "pot2" in fp.parts else "")
            session_id = str(data.get("session_id", ""))
            food_type = str(data.get("food_type", ""))
            target_time_sec = int(data.get("target_time", 0) or 0)
            completion_detected = bool(data.get("completion_detected", False))

            if events:
                session_with_events += 1
                total_events += len(events)

            first = events[0] if events else None
            last = events[-1] if events else None
            max_delta = max((float(e.get("color_delta", 0.0) or 0.0) for e in events), default=0.0)

            if events:
                first_delta = float(first.get("color_delta", 0.0) or 0.0)
                last_delta = float(last.get("color_delta", 0.0) or 0.0)
                first_brown = float(first.get("brown_ratio", 0.0) or 0.0)
                last_brown = float(last.get("brown_ratio", 0.0) or 0.0)
                first_golden = float(first.get("golden_ratio", 0.0) or 0.0)
                last_golden = float(last.get("golden_ratio", 0.0) or 0.0)
                first_rt = float(first.get("running_time", 0.0) or 0.0)
                last_rt = float(last.get("running_time", 0.0) or 0.0)
            else:
                first_delta = last_delta = first_brown = last_brown = first_golden = last_golden = 0.0
                first_rt = last_rt = 0.0

            sw.writerow(
                {
                    "pot": pot,
                    "session_id": session_id,
                    "food_type": food_type,
                    "lift_count": len(events),
                    "target_time_sec": target_time_sec,
                    "completion_detected": completion_detected,
                    "first_rt_sec": round(first_rt, 3),
                    "last_rt_sec": round(last_rt, 3),
                    "first_delta": round(first_delta, 6),
                    "last_delta": round(last_delta, 6),
                    "max_delta": round(max_delta, 6),
                    "delta_gain": round(last_delta - first_delta, 6),
                    "brown_gain": round(last_brown - first_brown, 6),
                    "golden_gain": round(last_golden - first_golden, 6),
                }
            )

            for i, ev in enumerate(events, start=1):
                ew.writerow(
                    {
                        "pot": pot,
                        "session_id": session_id,
                        "food_type": food_type,
                        "event_index": i,
                        "running_time_sec": round(float(ev.get("running_time", 0.0) or 0.0), 3),
                        "color_delta": round(float(ev.get("color_delta", 0.0) or 0.0), 6),
                        "food_area_ratio": round(float(ev.get("food_area_ratio", 0.0) or 0.0), 6),
                        "brown_ratio": round(float(ev.get("brown_ratio", 0.0) or 0.0), 6),
                        "golden_ratio": round(float(ev.get("golden_ratio", 0.0) or 0.0), 6),
                    }
                )

    print(f"[DONE] sessions={session_count}")
    print(f"[DONE] sessions_with_events={session_with_events}")
    print(f"[DONE] total_events={total_events}")
    print(f"[DONE] events_csv={events_csv}")
    print(f"[DONE] summary_csv={summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

