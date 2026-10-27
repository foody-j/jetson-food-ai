#!/usr/bin/env python3
"""
Export lift-event preview images for all sessions.

For each *_lift_events.json:
- find nearest camera frame (pot1: camera_0, pot2: camera_1)
- draw event overlay text
- save image to output directory
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
from pathlib import Path

import cv2


def parse_frame_clock_seconds(name: str):
    m = re.search(r"(\d{6})_(\d{3})", name)
    if not m:
        return None
    hhmmss, ms = m.group(1), m.group(2)
    hh = int(hhmmss[0:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:6])
    return hh * 3600 + mm * 60 + ss + int(ms) / 1000.0


def build_frame_timeline(image_paths):
    timeline = []
    day_offset = 0.0
    prev = None
    first = None
    for p in image_paths:
        sec = parse_frame_clock_seconds(p.name)
        if sec is None:
            continue
        if prev is not None and sec + day_offset < prev:
            day_offset += 24 * 3600
        cur = sec + day_offset
        if first is None:
            first = cur
        rel = cur - first
        timeline.append((rel, p))
        prev = cur
    return timeline


def find_nearest_frame(timeline, target_sec):
    if not timeline:
        return None
    best = min(timeline, key=lambda x: abs(x[0] - target_sec))
    return best


def draw_overlay(img, text_lines):
    out = img.copy()
    h, w = out.shape[:2]
    panel_h = min(220, h // 3)
    cv2.rectangle(out, (0, 0), (w, panel_h), (0, 0, 0), -1)
    y = 28
    for line in text_lines:
        cv2.putText(out, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
        y += 28
    return out


def detect_pot_from_path(path: Path) -> str:
    parts = {p.lower() for p in path.parts}
    if "pot1" in parts:
        return "pot1"
    if "pot2" in parts:
        return "pot2"
    return "unknown"


def session_folder_of_lift_json(lift_json: Path) -> Path:
    return lift_json.parent


def export_one_session(lift_json: Path, out_root: Path, width: int, max_events: int):
    data = json.loads(lift_json.read_text(encoding="utf-8"))
    events = data.get("lift_events", []) or []
    if not events:
        return 0

    sess_dir = session_folder_of_lift_json(lift_json)
    pot = detect_pot_from_path(lift_json)
    cam_dir = sess_dir / ("camera_0" if pot == "pot1" else "camera_1")
    images = [Path(p) for p in sorted(glob.glob(str(cam_dir / "*.jpg")))]
    if not images:
        return 0

    timeline = build_frame_timeline(images)
    if not timeline:
        return 0

    session_id = str(data.get("session_id") or sess_dir.parent.name)
    food = str(data.get("food_type") or sess_dir.name)
    out_dir = out_root / pot / session_id / food
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    total_events = len(events) if max_events <= 0 else min(len(events), max_events)
    for idx, ev in enumerate(events[:total_events], start=1):
        target = float(ev.get("running_time", 0.0))
        found = find_nearest_frame(timeline, target)
        if found is None:
            continue
        frame_sec, frame_path = found[0], found[1]
        img = cv2.imread(str(frame_path))
        if img is None:
            continue

        h, w = img.shape[:2]
        target_w = max(640, width)
        target_h = int(h * target_w / max(1, w))
        view = cv2.resize(img, (target_w, target_h))

        lines = [
            f"session={session_id} | pot={pot} | food={food}",
            f"event {idx}/{len(events)} | frame={frame_path.name}",
            f"running_time={target:.1f}s | nearest_frame={frame_sec:.1f}s",
            f"color_delta={float(ev.get('color_delta', 0.0)):.1f}",
            f"brown={float(ev.get('brown_ratio', 0.0)):.3f} | golden={float(ev.get('golden_ratio', 0.0)):.3f}",
        ]
        view = draw_overlay(view, lines)

        out_name = f"event_{idx:03d}_{frame_path.stem}.jpg"
        out_path = out_dir / out_name
        cv2.imwrite(str(out_path), view)
        count += 1

    return count


def main():
    ap = argparse.ArgumentParser(description="Export lift-event images for all sessions.")
    ap.add_argument("--base-dir", default="~/AI_Data", help="Base directory containing pot1/pot2")
    ap.add_argument("--pots", default="pot1,pot2", help="Comma-separated pot folders")
    ap.add_argument("--output-dir", default="~/jetson-food-ai/reports/lift_event_images", help="Output root")
    ap.add_argument("--width", type=int, default=1280, help="Output width")
    ap.add_argument("--max-events", type=int, default=0, help="Max events per session (0=all)")
    args = ap.parse_args()

    base_dir = Path(args.base_dir).expanduser()
    out_root = Path(args.output_dir).expanduser()
    out_root.mkdir(parents=True, exist_ok=True)

    pots = [x.strip() for x in args.pots.split(",") if x.strip()]
    lift_files = []
    for pot in pots:
        pattern = base_dir / pot / "session_*" / "*" / "*_lift_events.json"
        lift_files.extend(sorted(Path(p) for p in glob.glob(str(pattern))))

    if not lift_files:
        print("[ERROR] no *_lift_events.json found")
        return 1

    total_saved = 0
    sessions_done = 0
    for lf in lift_files:
        saved = export_one_session(lf, out_root, args.width, args.max_events)
        if saved > 0:
            sessions_done += 1
            total_saved += saved
            print(f"[OK] {lf} -> {saved} images")
        else:
            print(f"[SKIP] {lf}")

    print(f"[DONE] sessions={sessions_done}, images={total_saved}")
    print(f"[DONE] output={out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

