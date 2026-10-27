#!/usr/bin/env python3
"""
Preview reconstructed lift events with actual camera frames.

Keys:
  n / Right : next event
  p / Left  : previous event
  q / ESC   : quit
"""

import argparse
import glob
import json
import os
import re
from pathlib import Path

import cv2


def parse_frame_clock_seconds(name: str):
    # camera_1_105915_123.jpg / cam1_105915_123.jpg
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
    return best[1], best[0]


def resolve_lift_json(session_dir: Path):
    files = sorted(glob.glob(str(session_dir / "*_lift_events.json")))
    if not files:
        return None
    return Path(files[-1])


def resolve_camera_dir(session_dir: Path, pot: str):
    if pot == "pot1":
        return session_dir / "camera_0"
    return session_dir / "camera_1"


def draw_overlay(img, text_lines):
    out = img.copy()
    h, w = out.shape[:2]
    panel_h = min(190, h // 3)
    cv2.rectangle(out, (0, 0), (w, panel_h), (0, 0, 0), -1)
    y = 28
    for line in text_lines:
        cv2.putText(out, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
        y += 28
    return out


def main():
    parser = argparse.ArgumentParser(description="Preview lift events against session frames.")
    parser.add_argument("session_dir", help="Session folder (e.g. ~/AI_Data/pot2/session_xxx/food)")
    parser.add_argument("--pot", choices=["pot1", "pot2"], required=True)
    parser.add_argument("--width", type=int, default=1280)
    args = parser.parse_args()

    session_dir = Path(os.path.expanduser(args.session_dir)).resolve()
    if not session_dir.exists():
        raise SystemExit(f"[ERROR] session dir not found: {session_dir}")

    lift_json = resolve_lift_json(session_dir)
    if lift_json is None:
        raise SystemExit(f"[ERROR] no *_lift_events.json in {session_dir}")

    cam_dir = resolve_camera_dir(session_dir, args.pot)
    images = [Path(p) for p in sorted(glob.glob(str(cam_dir / "*.jpg")))]
    if not images:
        raise SystemExit(f"[ERROR] no jpg in {cam_dir}")

    with lift_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    events = data.get("lift_events", [])
    if not events:
        raise SystemExit("[ERROR] no lift_events in json")

    timeline = build_frame_timeline(images)
    if not timeline:
        raise SystemExit("[ERROR] could not parse frame timestamps from filenames")

    print(f"[INFO] session: {session_dir}")
    print(f"[INFO] lift json: {lift_json}")
    print(f"[INFO] camera dir: {cam_dir}")
    print(f"[INFO] events: {len(events)}")
    print("[INFO] keys: n/p/q")

    idx = 0
    win = "Lift Event Preview"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)

    while True:
        ev = events[idx]
        target = float(ev.get("running_time", 0.0))
        found = find_nearest_frame(timeline, target)
        if found is None:
            break
        frame_path, frame_sec = found
        img = cv2.imread(str(frame_path))
        if img is None:
            break

        # resize for easier viewing
        h, w = img.shape[:2]
        target_w = max(640, args.width)
        target_h = int(h * target_w / max(1, w))
        view = cv2.resize(img, (target_w, target_h))

        lines = [
            f"Event {idx + 1}/{len(events)} | file={frame_path.name}",
            f"running_time={target:.1f}s | nearest_frame={frame_sec:.1f}s",
            f"color_delta={ev.get('color_delta', 0):.1f}",
            f"brown={ev.get('brown_ratio', 0):.3f} | golden={ev.get('golden_ratio', 0):.3f}",
            "n/right: next, p/left: prev, q/esc: quit",
        ]
        view = draw_overlay(view, lines)
        cv2.imshow(win, view)

        key = cv2.waitKey(0) & 0xFF
        if key in (ord("q"), 27):
            break
        if key in (ord("n"), 83):  # right
            idx = min(len(events) - 1, idx + 1)
        elif key in (ord("p"), 81):  # left
            idx = max(0, idx - 1)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
