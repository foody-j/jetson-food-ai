#!/usr/bin/env python3
"""
Rebuild LiftEventTracker output from saved JPG frames.

This is for offline reconstruction when session had images but no lift-events json.
"""

import argparse
import glob
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import List, Optional, Tuple

import cv2


REPO_ROOT = Path(__file__).resolve().parents[1]
JETSON2_DIR = REPO_ROOT / "jetson2_frying_ai"
sys.path.insert(0, str(JETSON2_DIR))

from frying_segmenter import FoodSegmenter  # noqa: E402
from lift_event_tracker import LiftEventTracker  # noqa: E402


def parse_korean_time_to_sec(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"(\d+)\s*분", text)
    s = re.search(r"(\d+)\s*초", text)
    if not m and not s:
        return None
    minutes = int(m.group(1)) if m else 0
    seconds = int(s.group(1)) if s else 0
    return minutes * 60 + seconds


def infer_session_info(session_dir: Path) -> Tuple[str, str, int]:
    food_type = session_dir.name
    session_id = session_dir.parent.name if session_dir.parent.name.startswith("session_") else session_dir.name
    target_time = 180

    info_path = session_dir / "session_info.json"
    if info_path.exists():
        try:
            with info_path.open("r", encoding="utf-8") as f:
                info = json.load(f)
            food_type = info.get("food_type") or food_type
            raw_target = info.get("target_time")
            if isinstance(raw_target, (int, float)):
                target_time = int(raw_target)
            elif isinstance(raw_target, str):
                parsed = parse_korean_time_to_sec(raw_target)
                if parsed is not None:
                    target_time = parsed
        except Exception:
            pass

    # Fallback from meta when session_info is missing/insufficient.
    # Use all meta files (not a small prefix), prioritize cooking/discharge phase values.
    if target_time <= 0 or target_time == 180:
        meta_files = sorted(glob.glob(str(session_dir / "meta" / "meta_*.json")))
        preferred_vals: List[int] = []
        any_vals: List[int] = []
        for mpath in meta_files:
            try:
                with open(mpath, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                parsed = parse_korean_time_to_sec(str(meta.get("target_time", "")))
                if parsed is None or parsed <= 0:
                    continue
                any_vals.append(parsed)
                process_type = str(meta.get("process_type", "")).strip()
                if process_type in ("조리", "배출"):
                    preferred_vals.append(parsed)
            except Exception:
                continue

        vals = preferred_vals if preferred_vals else any_vals
        if vals:
            c = Counter(vals)
            # mode first, tie-break with larger target (safer upper bound for "max cook time")
            target_time = max(c.items(), key=lambda kv: (kv[1], kv[0]))[0]

    return session_id, food_type, target_time


def parse_frame_clock(file_name: str) -> Optional[float]:
    # ex) camera_0_143030_123.jpg, cam0_143030_123.jpg
    m = re.search(r"(\d{6})_(\d{3})", file_name)
    if not m:
        return None
    hhmmss, msec = m.group(1), m.group(2)
    hh = int(hhmmss[0:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:6])
    return hh * 3600 + mm * 60 + ss + int(msec) / 1000.0


def build_running_times(image_paths: List[Path], fallback_fps: float = 2.0) -> List[float]:
    clocks = [parse_frame_clock(p.name) for p in image_paths]
    if all(c is not None for c in clocks):
        rel = []
        base = clocks[0]
        prev = base
        day_offset = 0.0
        for c in clocks:
            # midnight rollover handling
            if c + day_offset < prev:
                day_offset += 24.0 * 3600.0
            cur = c + day_offset
            rel.append(cur - base)
            prev = cur
        return rel

    step = 1.0 / max(fallback_fps, 0.1)
    return [i * step for i in range(len(image_paths))]


def pick_camera_dir(session_dir: Path, pot: str, camera_index: Optional[int]) -> Path:
    if camera_index is not None:
        return session_dir / f"camera_{camera_index}"
    if pot == "pot1":
        return session_dir / "camera_0"
    if pot == "pot2":
        return session_dir / "camera_1"
    raise ValueError(f"invalid pot: {pot}")


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def rebuild(session_dir: Path, pot: str, camera_index: Optional[int], config: dict, device: str, output_dir: Path) -> int:
    camera_dir = pick_camera_dir(session_dir, pot, camera_index)
    if not camera_dir.exists():
        print(f"[ERROR] camera dir not found: {camera_dir}")
        return 1

    image_paths = [Path(p) for p in sorted(glob.glob(str(camera_dir / "*.jpg")))]
    if not image_paths:
        print(f"[ERROR] no jpg frames in: {camera_dir}")
        return 1

    session_id, food_type, target_time = infer_session_info(session_dir)
    pot_name = "POT1" if pot == "pot1" else "POT2"
    running_times = build_running_times(image_paths, fallback_fps=float(config.get("web_preview_fps", 2)))

    segmenter = FoodSegmenter(
        model_path=config.get("frying_seg_model", "frying_seg_v3.pt"),
        mode="auto",
        device=device,
        imgsz=config.get("frying_seg_imgsz", 640),
        conf=float(config.get("frying_seg_conf", 0.05)),
        mask_threshold=float(config.get("frying_seg_mask_thresh", 0.2)),
    )

    tracker = LiftEventTracker(pot_name, config)
    tracker.start_session(session_id=session_id, food_type=food_type, target_time=target_time)
    if running_times:
        tracker.start_time = time.time() - running_times[-1]

    processed = 0
    errors = 0
    lift_count = 0

    for img_path, run_t in zip(image_paths, running_times):
        image = cv2.imread(str(img_path))
        if image is None:
            errors += 1
            continue
        try:
            seg_result = segmenter.segment(image, visualize=False)
        except Exception as e:
            errors += 1
            print(f"[WARN] segment failed: {img_path.name} ({e})")
            continue

        processed += 1
        if seg_result.food_area_ratio <= tracker.lift_area_threshold:
            continue

        last_rt = tracker.lift_events[-1].running_time if tracker.lift_events else -1e9
        if run_t - last_rt <= tracker.lift_cooldown_sec:
            continue

        color_delta = tracker._calculate_color_change(seg_result.color_features)
        tracker._record_lift_event(run_t, color_delta, seg_result)
        lift_count += 1

        was_completed = tracker.completion_detected
        if not tracker.completion_detected:
            tracker._check_completion(run_t, color_delta)
        if not was_completed and tracker.completion_detected:
            tracker.completion_time = tracker.start_time + run_t

    tracker.stop_session()
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_path = tracker.save_session_data(str(output_dir))

    print("")
    print("=" * 70)
    print(f"session_dir   : {session_dir}")
    print(f"camera_dir    : {camera_dir}")
    print(f"images_total  : {len(image_paths)}")
    print(f"processed_ok  : {processed}")
    print(f"errors        : {errors}")
    print(f"lift_events   : {lift_count}")
    print(f"target_time_s : {target_time}")
    print(f"saved_file    : {saved_path}")
    print("=" * 70)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild lift events json from jpg frames.")
    parser.add_argument("session_dir", help="Session folder path (e.g., ~/AI_Data/pot1/session_xxx/food)")
    parser.add_argument("--pot", choices=["pot1", "pot2"], required=True, help="Pot side")
    parser.add_argument("--camera-index", type=int, default=None, help="Override camera index")
    parser.add_argument(
        "--config",
        default=str(JETSON2_DIR / "config_jetson2_web.json"),
        help="Config json path",
    )
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda", help="Inference device")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: session_dir)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    session_dir = Path(os.path.expanduser(args.session_dir)).resolve()
    if not session_dir.exists():
        print(f"[ERROR] session dir not found: {session_dir}")
        return 1

    config = load_config(Path(args.config))
    output_dir = Path(args.output_dir).resolve() if args.output_dir else session_dir
    return rebuild(
        session_dir=session_dir,
        pot=args.pot,
        camera_index=args.camera_index,
        config=config,
        device=args.device,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    sys.exit(main())
