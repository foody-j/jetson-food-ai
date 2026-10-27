#!/usr/bin/env python3
"""
Export per-session completion candidates with labeled images.

What it does:
- Scans AI_Data sessions (pot1/pot2).
- Runs FoodSegmenter on camera frames.
- Uses first detected frame as baseline color.
- Computes color delta for detected frames.
- Picks completion candidate after (target_time - lead_sec) with max delta.
- Saves labeled image(s) and a summary CSV.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import re
import sys
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2


REPO_ROOT = Path(__file__).resolve().parents[1]
JETSON2_DIR = REPO_ROOT / "jetson2_frying_ai"
sys.path.insert(0, str(JETSON2_DIR))

from frying_segmenter import FoodSegmenter  # noqa: E402


def parse_korean_time_to_sec(text: str) -> Optional[int]:
    if not text:
        return None
    text = str(text).strip()
    mm_match = re.search(r"(\d+)\s*분", text)
    ss_match = re.search(r"(\d+)\s*초", text)
    if not mm_match and not ss_match:
        if text.isdigit():
            return int(text)
        return None
    mm = int(mm_match.group(1)) if mm_match else 0
    ss = int(ss_match.group(1)) if ss_match else 0
    return mm * 60 + ss


def parse_frame_clock_seconds(name: str) -> Optional[float]:
    m = re.search(r"(\d{6})_(\d{3})", name)
    if not m:
        return None
    hhmmss, ms = m.group(1), m.group(2)
    hh = int(hhmmss[0:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:6])
    return hh * 3600 + mm * 60 + ss + int(ms) / 1000.0


def build_running_times(image_paths: List[Path]) -> List[float]:
    clocks = [parse_frame_clock_seconds(p.name) for p in image_paths]
    if not clocks or any(c is None for c in clocks):
        # Fallback: 1 fps-like monotonic sequence
        return [float(i) for i in range(len(image_paths))]

    out: List[float] = []
    day_offset = 0.0
    prev = clocks[0]
    base = clocks[0]
    for c in clocks:
        if c + day_offset < prev:
            day_offset += 24 * 3600
        cur = c + day_offset
        out.append(cur - base)
        prev = cur
    return out


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_config(path: Path) -> dict:
    return load_json(path)


def get_session_info(session_food_dir: Path, default_target: int) -> Tuple[str, str, int]:
    # session_food_dir: .../potX/session_xxx/<food>
    food = session_food_dir.name
    session_id = session_food_dir.parent.name
    target_sec = default_target

    info_path = session_food_dir / "session_info.json"
    if info_path.exists():
        try:
            info = load_json(info_path)
            food = str(info.get("food_type") or food)
            raw_target = info.get("target_time")
            if isinstance(raw_target, (int, float)):
                target_sec = int(raw_target)
            elif isinstance(raw_target, str):
                parsed = parse_korean_time_to_sec(raw_target)
                if parsed is not None:
                    target_sec = parsed
        except Exception:
            pass

    if target_sec <= 0:
        target_sec = default_target
    return session_id, food, int(target_sec)


def color_delta(base_hsv: Tuple[float, float, float], cur_hsv: Tuple[float, float, float]) -> float:
    h1, s1, v1 = base_hsv
    h2, s2, v2 = cur_hsv
    h_diff = min(abs(h1 - h2), 360 - abs(h1 - h2))
    return math.sqrt((h_diff * 2.0) ** 2 + (s1 - s2) ** 2 + (v1 - v2) ** 2)


def overlay_text(img, lines: List[str]):
    out = img.copy()
    h, w = out.shape[:2]
    panel_h = min(220, max(120, h // 4))
    cv2.rectangle(out, (0, 0), (w, panel_h), (0, 0, 0), -1)
    y = 30
    for line in lines:
        cv2.putText(out, line, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (0, 255, 255), 2, cv2.LINE_AA)
        y += 28
    return out


def select_camera_dir(session_food_dir: Path, pot: str) -> Path:
    return session_food_dir / ("camera_0" if pot == "pot1" else "camera_1")


def process_session(
    session_food_dir: Path,
    pot: str,
    segmenter: FoodSegmenter,
    out_root: Path,
    area_threshold: float,
    lead_sec: float,
    default_target_sec: int,
    label_mode: str,
) -> Dict:
    session_id, food_type, target_sec = get_session_info(session_food_dir, default_target_sec)
    ready_sec = max(0.0, float(target_sec) - float(lead_sec))
    cam_dir = select_camera_dir(session_food_dir, pot)
    image_paths = [Path(p) for p in sorted(glob.glob(str(cam_dir / "*.jpg")))]
    if not image_paths:
        return {
            "pot": pot,
            "session_id": session_id,
            "food_type": food_type,
            "target_time_sec": target_sec,
            "ready_time_sec": round(ready_sec, 3),
            "total_frames": 0,
            "detected_frames": 0,
            "candidate_found": False,
            "candidate_frame": "",
            "running_time_sec": 0.0,
            "area_ratio": 0.0,
            "color_delta": 0.0,
            "brown_ratio": 0.0,
            "golden_ratio": 0.0,
            "mean_h": 0.0,
            "mean_s": 0.0,
            "mean_v": 0.0,
        }

    running_times = build_running_times(image_paths)
    detected_rows = []
    base_hsv = None

    for path, rt in zip(image_paths, running_times):
        img = cv2.imread(str(path))
        if img is None:
            continue
        res = segmenter.segment(img)
        area = float(res.food_area_ratio)
        if area <= area_threshold:
            continue
        hsv = tuple(float(x) for x in res.color_features.mean_hsv)
        if base_hsv is None:
            base_hsv = hsv
            delta = 0.0
        else:
            delta = color_delta(base_hsv, hsv)
        detected_rows.append(
            {
                "file": path.name,
                "full_path": str(path),
                "running_time_sec": float(rt),
                "area_ratio": area,
                "color_delta": delta,
                "brown_ratio": float(res.color_features.brown_ratio),
                "golden_ratio": float(res.color_features.golden_ratio),
                "mean_h": hsv[0],
                "mean_s": hsv[1],
                "mean_v": hsv[2],
            }
        )

    candidate = None
    after_ready = [r for r in detected_rows if r["running_time_sec"] >= ready_sec]
    if after_ready:
        candidate = max(after_ready, key=lambda r: r["color_delta"])

    session_out = out_root / pot / session_id / food_type
    session_out.mkdir(parents=True, exist_ok=True)

    if label_mode in ("candidate", "all") and candidate is not None:
        src = cv2.imread(candidate["full_path"])
        if src is not None:
            labeled = overlay_text(
                src,
                [
                    f"{pot} | {session_id} | {food_type}",
                    f"candidate={candidate['file']}",
                    f"rt={candidate['running_time_sec']:.1f}s | ready={ready_sec:.1f}s | target={target_sec}s",
                    f"area={candidate['area_ratio']:.4f} | delta={candidate['color_delta']:.2f}",
                    f"brown={candidate['brown_ratio']:.4f} | golden={candidate['golden_ratio']:.4f}",
                ],
            )
            cv2.imwrite(str(session_out / "candidate_labeled.jpg"), labeled)

    if label_mode == "all":
        all_dir = session_out / "labeled_all"
        all_dir.mkdir(exist_ok=True)
        for row in detected_rows:
            src = cv2.imread(row["full_path"])
            if src is None:
                continue
            labeled = overlay_text(
                src,
                [
                    f"{pot} | {session_id} | {food_type}",
                    f"{row['file']} | rt={row['running_time_sec']:.1f}s",
                    f"area={row['area_ratio']:.4f} | delta={row['color_delta']:.2f}",
                    f"brown={row['brown_ratio']:.4f} | golden={row['golden_ratio']:.4f}",
                    f"hsv=({row['mean_h']:.2f}, {row['mean_s']:.2f}, {row['mean_v']:.2f})",
                ],
            )
            cv2.imwrite(str(all_dir / row["file"]), labeled)

    baseline_row = detected_rows[0] if detected_rows else None
    end_row = detected_rows[-1] if detected_rows else None
    max_delta_row = max(detected_rows, key=lambda r: r["color_delta"]) if detected_rows else None
    ready_rows = [r for r in detected_rows if r["running_time_sec"] >= ready_sec]

    details = {
        "pot": pot,
        "session_id": session_id,
        "food_type": food_type,
        "target_time_sec": int(target_sec),
        "ready_time_sec": round(ready_sec, 3),
        "total_frames": len(image_paths),
        "detected_frames": len(detected_rows),
        "candidate_found": candidate is not None,
        "candidate_frame": candidate["file"] if candidate else "",
        "running_time_sec": round(candidate["running_time_sec"], 3) if candidate else 0.0,
        "area_ratio": round(candidate["area_ratio"], 6) if candidate else 0.0,
        "color_delta": round(candidate["color_delta"], 6) if candidate else 0.0,
        "brown_ratio": round(candidate["brown_ratio"], 6) if candidate else 0.0,
        "golden_ratio": round(candidate["golden_ratio"], 6) if candidate else 0.0,
        "mean_h": round(candidate["mean_h"], 6) if candidate else 0.0,
        "mean_s": round(candidate["mean_s"], 6) if candidate else 0.0,
        "mean_v": round(candidate["mean_v"], 6) if candidate else 0.0,
        "baseline_frame": baseline_row["file"] if baseline_row else "",
        "baseline_area_ratio": round(baseline_row["area_ratio"], 6) if baseline_row else 0.0,
        "baseline_brown_ratio": round(baseline_row["brown_ratio"], 6) if baseline_row else 0.0,
        "baseline_golden_ratio": round(baseline_row["golden_ratio"], 6) if baseline_row else 0.0,
        "end_frame": end_row["file"] if end_row else "",
        "end_running_time_sec": round(end_row["running_time_sec"], 3) if end_row else 0.0,
        "end_delta": round(end_row["color_delta"], 6) if end_row else 0.0,
        "end_area_ratio": round(end_row["area_ratio"], 6) if end_row else 0.0,
        "end_brown_ratio": round(end_row["brown_ratio"], 6) if end_row else 0.0,
        "end_golden_ratio": round(end_row["golden_ratio"], 6) if end_row else 0.0,
        "max_delta_frame": max_delta_row["file"] if max_delta_row else "",
        "max_delta": round(max_delta_row["color_delta"], 6) if max_delta_row else 0.0,
        "max_delta_rt_sec": round(max_delta_row["running_time_sec"], 3) if max_delta_row else 0.0,
        "delta_gain_end_vs_base": round((end_row["color_delta"] if end_row else 0.0), 6),
        "brown_gain_end_vs_base": round(
            (end_row["brown_ratio"] - baseline_row["brown_ratio"]) if (end_row and baseline_row) else 0.0,
            6,
        ),
        "golden_gain_end_vs_base": round(
            (end_row["golden_ratio"] - baseline_row["golden_ratio"]) if (end_row and baseline_row) else 0.0,
            6,
        ),
        "ready_detected_frames": len(ready_rows),
        "ready_delta_max": round(max((r["color_delta"] for r in ready_rows), default=0.0), 6),
        "ready_delta_mean": round(
            (sum(r["color_delta"] for r in ready_rows) / len(ready_rows)) if ready_rows else 0.0,
            6,
        ),
    }
    with (session_out / "candidate_summary.json").open("w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    return details


def write_csv(rows: List[Dict], out_csv: Path):
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "pot",
        "session_id",
        "food_type",
        "target_time_sec",
        "ready_time_sec",
        "total_frames",
        "detected_frames",
        "candidate_found",
        "candidate_frame",
        "running_time_sec",
        "area_ratio",
        "color_delta",
        "brown_ratio",
        "golden_ratio",
        "mean_h",
        "mean_s",
        "mean_v",
        "baseline_frame",
        "baseline_area_ratio",
        "baseline_brown_ratio",
        "baseline_golden_ratio",
        "end_frame",
        "end_running_time_sec",
        "end_delta",
        "end_area_ratio",
        "end_brown_ratio",
        "end_golden_ratio",
        "max_delta_frame",
        "max_delta",
        "max_delta_rt_sec",
        "delta_gain_end_vs_base",
        "brown_gain_end_vs_base",
        "golden_gain_end_vs_base",
        "ready_detected_frames",
        "ready_delta_max",
        "ready_delta_mean",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_food_aggregate_csv(rows: List[Dict], out_csv: Path):
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    groups: Dict[str, List[Dict]] = {}
    for r in rows:
        groups.setdefault(str(r.get("food_type", "")), []).append(r)

    fieldnames = [
        "food_type",
        "sessions",
        "candidate_found_sessions",
        "candidate_found_rate_pct",
        "median_candidate_delta",
        "median_end_delta",
        "median_max_delta",
        "median_brown_gain_end_vs_base",
        "median_golden_gain_end_vs_base",
        "median_ready_delta_max",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for food, items in sorted(groups.items(), key=lambda kv: kv[0]):
            n = len(items)
            found_items = [x for x in items if bool(x.get("candidate_found", False))]
            found_n = len(found_items)

            def med(key: str, source: List[Dict]) -> float:
                vals = [float(x.get(key, 0.0) or 0.0) for x in source]
                return float(statistics.median(vals)) if vals else 0.0

            row = {
                "food_type": food,
                "sessions": n,
                "candidate_found_sessions": found_n,
                "candidate_found_rate_pct": round((100.0 * found_n / n) if n else 0.0, 2),
                "median_candidate_delta": round(med("color_delta", found_items), 6),
                "median_end_delta": round(med("end_delta", items), 6),
                "median_max_delta": round(med("max_delta", items), 6),
                "median_brown_gain_end_vs_base": round(med("brown_gain_end_vs_base", items), 6),
                "median_golden_gain_end_vs_base": round(med("golden_gain_end_vs_base", items), 6),
                "median_ready_delta_max": round(med("ready_delta_max", items), 6),
            }
            writer.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser(description="Export completion candidates with labeled images from AI_Data.")
    ap.add_argument("--base-dir", default="~/AI_Data", help="AI_Data root (contains pot1/pot2)")
    ap.add_argument("--pots", default="pot1,pot2", help="Comma-separated pots to process")
    ap.add_argument(
        "--config",
        default=str(JETSON2_DIR / "config_jetson2_web.json"),
        help="Jetson2 config json path",
    )
    ap.add_argument("--out-dir", default="~/jetson-food-ai/reports/completion_candidates", help="Output root")
    ap.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="Inference device")
    ap.add_argument("--lead-sec", type=float, default=60.0, help="Candidate ready lead time from target")
    ap.add_argument("--area-threshold", type=float, default=None, help="Override area threshold")
    ap.add_argument("--label-mode", choices=["candidate", "all"], default="candidate", help="Label export mode")
    ap.add_argument("--limit-sessions", type=int, default=0, help="Max sessions per pot (0=all)")
    args = ap.parse_args()

    base_dir = Path(args.base_dir).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    cfg = load_config(Path(args.config).expanduser())

    area_threshold = float(args.area_threshold) if args.area_threshold is not None else float(cfg.get("lift_area_threshold", 0.08))
    default_target = int(cfg.get("default_target_time_sec", 180))

    model_path = cfg.get("frying_seg_model", "frying_seg_v3.pt")
    if not os.path.isabs(model_path):
        model_path = str((JETSON2_DIR / model_path).resolve())

    segmenter = FoodSegmenter(
        model_path=model_path,
        imgsz=cfg.get("frying_seg_imgsz", 640),
        conf=cfg.get("frying_seg_conf", 0.2),
        mask_threshold=cfg.get("frying_seg_mask_thresh", 0.3),
        device=args.device,
        frying_cpp_postprocess_enabled=False,
    )

    pots = [p.strip() for p in args.pots.split(",") if p.strip()]
    rows: List[Dict] = []
    for pot in pots:
        session_food_dirs = [Path(p) for p in sorted(glob.glob(str(base_dir / pot / "session_*" / "*")))]
        if args.limit_sessions > 0:
            session_food_dirs = session_food_dirs[: args.limit_sessions]
        for sdir in session_food_dirs:
            if not sdir.is_dir():
                continue
            details = process_session(
                session_food_dir=sdir,
                pot=pot,
                segmenter=segmenter,
                out_root=out_dir,
                area_threshold=area_threshold,
                lead_sec=args.lead_sec,
                default_target_sec=default_target,
                label_mode=args.label_mode,
            )
            rows.append(details)
            print(
                f"[OK] {pot}/{details['session_id']}/{details['food_type']} "
                f"det={details['detected_frames']} candidate={details['candidate_frame'] or '-'} "
                f"delta={details['color_delta']:.2f}"
            )

    csv_path = out_dir / "completion_candidates.csv"
    write_csv(rows, csv_path)
    agg_csv_path = out_dir / "completion_food_aggregate.csv"
    write_food_aggregate_csv(rows, agg_csv_path)
    print(f"[DONE] sessions={len(rows)}")
    print(f"[DONE] csv={csv_path}")
    print(f"[DONE] aggregate_csv={agg_csv_path}")
    print(f"[DONE] out={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
