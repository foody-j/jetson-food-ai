#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.offsetbox import AnnotationBbox, OffsetImage  # noqa: E402


LogFn = Callable[[str], None]


def _default_log(msg: str) -> None:
    print(msg)


def parse_frame_clock_seconds(name: str) -> Optional[float]:
    m = re.search(r"(\d{6})_(\d{3})", name)
    if not m:
        return None
    hhmmss, ms = m.group(1), m.group(2)
    hh = int(hhmmss[0:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:6])
    return hh * 3600 + mm * 60 + ss + int(ms) / 1000.0


def build_frame_timeline(image_paths: Sequence[Path]) -> List[Tuple[float, Path]]:
    timeline: List[Tuple[float, Path]] = []
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
        timeline.append((cur - first, p))
        prev = cur
    return timeline


def find_nearest_frame(timeline: Sequence[Tuple[float, Path]], target: float) -> Optional[Path]:
    if not timeline:
        return None
    return min(timeline, key=lambda x: abs(x[0] - target))[1]


def setup_font() -> None:
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


def _safe_float(x: object, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _safe_int(x: object, default: int = 0) -> int:
    try:
        if x is None:
            return default
        return int(float(x))
    except Exception:
        return default


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_image_unicode(path: Path):
    # Windows Korean paths can fail with cv2.imread; use fromfile+imdecode.
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


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


def _infer_target_time_sec(food_dir: Path) -> int:
    info_path = food_dir / "session_info.json"
    if info_path.exists():
        try:
            info = _load_json(info_path)
            raw = info.get("target_time")
            if isinstance(raw, (int, float)):
                return int(raw)
            if isinstance(raw, str):
                parsed = parse_korean_time_to_sec(raw)
                if parsed is not None:
                    return parsed
        except Exception:
            pass

    meta_dir = food_dir / "meta"
    if meta_dir.exists():
        for mp in sorted(meta_dir.glob("meta_*.json"))[:20]:
            try:
                m = _load_json(mp)
            except Exception:
                continue
            parsed = parse_korean_time_to_sec(str(m.get("target_time", "")))
            if parsed is not None:
                return parsed
    return 0


def _compute_simple_features(img_bgr) -> Dict[str, float]:
    h, w = img_bgr.shape[:2]
    y1, y2 = h // 4, int(h * 0.9)
    x1, x2 = w // 5, int(w * 0.8)
    roi = img_bgr[y1:y2, x1:x2]
    if roi.size == 0:
        roi = img_bgr

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)

    h_ch = hsv[:, :, 0]
    s_ch = hsv[:, :, 1]
    v_ch = hsv[:, :, 2]
    valid = (v_ch > 40) & (s_ch > 25)
    valid_cnt = int(valid.sum())
    total = valid.size

    if total <= 0:
        return {
            "food_area_ratio": 0.0,
            "brown_ratio": 0.0,
            "golden_ratio": 0.0,
            "L": 0.0,
            "A": 0.0,
            "B": 0.0,
        }

    brown = valid & (h_ch >= 5) & (h_ch <= 25) & (s_ch >= 40) & (v_ch >= 30)
    golden = valid & (h_ch >= 15) & (h_ch <= 40) & (s_ch >= 35) & (v_ch >= 50)

    if valid_cnt > 0:
        brown_ratio = float(brown.sum()) / float(valid_cnt)
        golden_ratio = float(golden.sum()) / float(valid_cnt)
        lab_mean = cv2.mean(lab, valid.astype("uint8"))
        l_mean, a_mean, b_mean = float(lab_mean[0]), float(lab_mean[1]), float(lab_mean[2])
    else:
        brown_ratio = 0.0
        golden_ratio = 0.0
        l_mean = a_mean = b_mean = 0.0

    return {
        "food_area_ratio": float(valid_cnt) / float(total),
        "brown_ratio": brown_ratio,
        "golden_ratio": golden_ratio,
        "L": l_mean,
        "A": a_mean,
        "B": b_mean,
    }


def rebuild_missing_lift_jsons(
    base_dir: Path,
    log: LogFn = _default_log,
    area_threshold: float = 0.08,
    min_event_interval_sec: float = 8.0,
) -> int:
    synthesized = 0
    pruned = 0
    for pot in ("pot1", "pot2"):
        pot_dir = base_dir / pot
        if not pot_dir.exists():
            continue
        for session_dir in sorted(pot_dir.glob("session_*")):
            if not session_dir.is_dir():
                continue
            for food_dir in sorted([p for p in session_dir.iterdir() if p.is_dir()]):
                existing_jsons = sorted(food_dir.glob("*_lift_events.json"))
                keep_existing = False
                if existing_jsons:
                    # Auto-clean invalid prior synth outputs so user does not need manual delete.
                    for jp in existing_jsons:
                        try:
                            j = _load_json(jp)
                            is_synth = bool(j.get("synthesized", False)) or str(j.get("source", "")).startswith("frame_fallback")
                            lift_count = _safe_int(j.get("lift_count"), 0)
                            empty_events = len(j.get("lift_events", []) or []) == 0
                            should_prune = is_synth and (lift_count <= 0 or empty_events)
                            if should_prune:
                                try:
                                    jp.unlink()
                                    pruned += 1
                                    log(f"[CLEAN] remove stale synth json: {jp}")
                                except Exception as e:
                                    log(f"[WARN] failed to remove stale synth json: {jp} ({e})")
                            else:
                                keep_existing = True
                        except Exception:
                            # Invalid json is removed and rebuilt.
                            try:
                                jp.unlink()
                                pruned += 1
                                log(f"[CLEAN] remove invalid json: {jp}")
                            except Exception as e:
                                log(f"[WARN] failed to remove invalid json: {jp} ({e})")
                    if keep_existing:
                        continue

                cam_dir = food_dir / ("camera_0" if pot == "pot1" else "camera_1")
                if not cam_dir.exists():
                    continue
                images = [Path(p) for p in sorted(glob.glob(str(cam_dir / "*.jpg")))]
                if not images:
                    continue

                timeline = build_frame_timeline(images)
                if not timeline:
                    continue

                target_time = _infer_target_time_sec(food_dir)
                session_id = session_dir.name
                food_type = food_dir.name

                lift_events = []
                baseline = None
                last_event_rt = -1e9
                prev_above = False
                frame_rows = []
                edge_rows = []

                for rt, img_path in timeline:
                    img = read_image_unicode(img_path)
                    if img is None:
                        continue
                    feat = _compute_simple_features(img)
                    area = feat["food_area_ratio"]
                    above = area > area_threshold
                    edge = (not prev_above) and above
                    prev_above = above
                    if baseline is None:
                        baseline = (feat["L"], feat["A"], feat["B"])
                    dL = feat["L"] - baseline[0]
                    dA = feat["A"] - baseline[1]
                    dB = feat["B"] - baseline[2]
                    color_delta = (dL * dL + dA * dA + dB * dB) ** 0.5
                    row = {
                        "timestamp": float(rt),
                        "running_time": float(rt),
                        "color_delta": float(color_delta),
                        "food_area_ratio": float(area),
                        "brown_ratio": float(feat["brown_ratio"]),
                        "golden_ratio": float(feat["golden_ratio"]),
                    }
                    frame_rows.append((above, row))
                    if edge:
                        edge_rows.append(row)

                # 1) Primary: area edge rows with cooldown
                for row in edge_rows:
                    rt = float(row["running_time"])
                    if rt - last_event_rt < min_event_interval_sec:
                        continue
                    lift_events.append(row)
                    last_event_rt = rt

                # 2) Fallback A: if no edge events, periodic rows among area-above frames
                if not lift_events:
                    for above, row in frame_rows:
                        if not above:
                            continue
                        rt = float(row["running_time"])
                        if rt - last_event_rt < min_event_interval_sec:
                            continue
                        lift_events.append(row)
                        last_event_rt = rt

                # 3) Fallback B: if still empty, periodic rows over all frames
                if not lift_events:
                    last_event_rt = -1e9
                    for _above, row in frame_rows:
                        rt = float(row["running_time"])
                        if rt - last_event_rt < min_event_interval_sec:
                            continue
                        lift_events.append(row)
                        last_event_rt = rt

                # Guarantee at least one row when frame exists
                if not lift_events and frame_rows:
                    lift_events.append(frame_rows[0][1])
                if not frame_rows:
                    log(f"[WARN] no readable frames: {cam_dir}")

                out_path = food_dir / f"{session_id}_lift_events.json"
                payload = {
                    "session_id": session_id,
                    "food_type": food_type,
                    "pot_name": pot.upper(),
                    "target_time": int(target_time),
                    "lift_count": len(lift_events),
                    "completion_detected": False,
                    "lift_events": lift_events,
                    "synthesized": True,
                    "source": "frame_fallback_simple_v2",
                    "params": {
                        "area_threshold": area_threshold,
                        "min_event_interval_sec": min_event_interval_sec,
                    },
                }
                try:
                    with out_path.open("w", encoding="utf-8") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2)
                    synthesized += 1
                    log(f"[SYNTH] created: {out_path} (events={len(lift_events)})")
                except Exception as e:
                    log(f"[WARN] synth save failed: {out_path} ({e})")
    if pruned > 0:
        log(f"[DONE] pruned stale/invalid json count={pruned}")
    if synthesized > 0:
        log(f"[DONE] synthesized lift json count={synthesized}")
    return synthesized


def export_lift_event_trends(base_dir: Path, out_dir: Path, log: LogFn = _default_log) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(base_dir / "pot*" / "session_*" / "*" / "*_lift_events.json")
    files = sorted(Path(p) for p in glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No *_lift_events.json found under {base_dir}")

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

    with events_csv.open("w", encoding="utf-8", newline="") as ef, summary_csv.open("w", encoding="utf-8", newline="") as sf:
        ew = csv.DictWriter(ef, fieldnames=event_fields)
        sw = csv.DictWriter(sf, fieldnames=summary_fields)
        ew.writeheader()
        sw.writeheader()

        for fp in files:
            session_count += 1
            try:
                data = _load_json(fp)
            except Exception as e:
                log(f"[WARN] skip invalid json: {fp} ({e})")
                continue

            events = data.get("lift_events", []) or []
            pot = str(data.get("pot_name", "")).lower().replace("pot", "pot")
            if pot not in ("pot1", "pot2"):
                pot = "pot1" if "pot1" in fp.parts else ("pot2" if "pot2" in fp.parts else "")
            session_id = str(data.get("session_id", ""))
            food_type = str(data.get("food_type", ""))
            target_time_sec = _safe_int(data.get("target_time"), 0)
            completion_detected = bool(data.get("completion_detected", False))

            if events:
                session_with_events += 1
                total_events += len(events)

            first = events[0] if events else None
            last = events[-1] if events else None
            max_delta = max((_safe_float(e.get("color_delta"), 0.0) for e in events), default=0.0)

            if events and first and last:
                first_delta = _safe_float(first.get("color_delta"), 0.0)
                last_delta = _safe_float(last.get("color_delta"), 0.0)
                first_brown = _safe_float(first.get("brown_ratio"), 0.0)
                last_brown = _safe_float(last.get("brown_ratio"), 0.0)
                first_golden = _safe_float(first.get("golden_ratio"), 0.0)
                last_golden = _safe_float(last.get("golden_ratio"), 0.0)
                first_rt = _safe_float(first.get("running_time"), 0.0)
                last_rt = _safe_float(last.get("running_time"), 0.0)
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
                        "running_time_sec": round(_safe_float(ev.get("running_time"), 0.0), 3),
                        "color_delta": round(_safe_float(ev.get("color_delta"), 0.0), 6),
                        "food_area_ratio": round(_safe_float(ev.get("food_area_ratio"), 0.0), 6),
                        "brown_ratio": round(_safe_float(ev.get("brown_ratio"), 0.0), 6),
                        "golden_ratio": round(_safe_float(ev.get("golden_ratio"), 0.0), 6),
                    }
                )

    log(f"[DONE] sessions={session_count}, with_events={session_with_events}, total_events={total_events}")
    log(f"[DONE] {events_csv}")
    log(f"[DONE] {summary_csv}")
    return events_csv, summary_csv


def _load_rows(events_csv: Path) -> List[dict]:
    rows: List[dict] = []
    with events_csv.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["running_time_sec"] = _safe_float(row.get("running_time_sec"), 0.0)
            row["color_delta"] = _safe_float(row.get("color_delta"), 0.0)
            row["brown_ratio"] = _safe_float(row.get("brown_ratio"), 0.0)
            row["golden_ratio"] = _safe_float(row.get("golden_ratio"), 0.0)
            rows.append(row)
    return rows


def _load_target_time_map(summary_csv: Path) -> Dict[Tuple[str, str, str], int]:
    out: Dict[Tuple[str, str, str], int] = {}
    if not summary_csv.exists():
        return out
    with summary_csv.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            pot = str(row.get("pot", "")).strip()
            session_id = str(row.get("session_id", "")).strip()
            food_type = str(row.get("food_type", "")).strip()
            target = _safe_int(row.get("target_time_sec"), 0)
            if pot and session_id and food_type:
                out[(pot, session_id, food_type)] = target
    return out


def _pick_sample_indices(n: int, max_items: int) -> List[int]:
    if n <= max_items:
        return list(range(n))
    return [round(i * (n - 1) / (max_items - 1)) for i in range(max_items)]


def _render_one_session(
    session_rows: List[dict],
    base_ai_data: Path,
    out_path: Path,
    max_thumbs: int,
    thumb_mode: str,
    target_time_sec: int,
) -> None:
    pot = session_rows[0]["pot"]
    session_id = session_rows[0]["session_id"]
    food = session_rows[0]["food_type"]
    session_rows = sorted(session_rows, key=lambda x: x["running_time_sec"])

    x = [r["running_time_sec"] for r in session_rows]
    y_delta = [r["color_delta"] for r in session_rows]
    y_brown = [r["brown_ratio"] for r in session_rows]
    y_golden = [r["golden_ratio"] for r in session_rows]

    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 2], hspace=0.15)
    ax_top = fig.add_subplot(gs[0, 0])
    ax_bot = fig.add_subplot(gs[1, 0], sharex=ax_top)

    ax_top.plot(x, y_delta, "-o", color="tab:blue", label="color_delta", markersize=4)
    ax_top.set_ylabel("color_delta", color="tab:blue")
    ax_top.tick_params(axis="y", labelcolor="tab:blue")
    ax2 = ax_top.twinx()
    ax2.plot(x, y_brown, "-s", color="tab:brown", label="brown_ratio", markersize=4)
    ax2.plot(x, y_golden, "-^", color="goldenrod", label="golden_ratio", markersize=4)
    ax2.set_ylabel("brown/golden ratio")
    l1, lb1 = ax_top.get_legend_handles_labels()
    l2, lb2 = ax2.get_legend_handles_labels()
    ax_top.legend(l1 + l2, lb1 + lb2, loc="upper left")
    ax_top.grid(alpha=0.25)
    ax_top.set_title(f"Session Flow + Thumbnails: {pot}/{session_id}/{food}")

    if target_time_sec > 0:
        ready_time = max(0, target_time_sec - 60)
        candidate_time = max(ready_time, (x[-1] - 20.0) if x else ready_time)
        end_t = max(target_time_sec + 60, int(max(x) + 1) if x else target_time_sec + 60)
        for t in range(ready_time, end_t + 1, 10):
            color = "#7f8c8d"
            alpha = 0.20
            lw = 0.8
            ls = "--"
            if t == ready_time:
                color = "#f39c12"
                alpha = 0.55
                lw = 1.6
                ls = "-."
            if t == target_time_sec:
                color = "#e74c3c"
                alpha = 0.70
                lw = 2.2
                ls = "-"
            ax_top.axvline(t, color=color, alpha=alpha, linewidth=lw, linestyle=ls, zorder=0)
            ax_bot.axvline(t, color=color, alpha=alpha * 0.9, linewidth=lw, linestyle=ls, zorder=0)
        ax_top.axvline(candidate_time, color="#2ecc71", alpha=0.85, linewidth=2.2, linestyle="-")
        ax_bot.axvline(candidate_time, color="#2ecc71", alpha=0.75, linewidth=2.0, linestyle="-")

    ax_bot.set_ylim(0, 1)
    ax_bot.set_yticks([])
    ax_bot.set_xlabel("running_time_sec")
    ax_bot.grid(alpha=0.2, axis="x")

    cam_dir = base_ai_data / pot / session_id / food / ("camera_0" if pot == "pot1" else "camera_1")
    images = [Path(p) for p in sorted(glob.glob(str(cam_dir / "*.jpg")))]
    timeline = build_frame_timeline(images)
    sample_idxs = list(range(len(session_rows))) if thumb_mode == "all" else _pick_sample_indices(len(session_rows), max_thumbs)

    for idx in sample_idxs:
        row = session_rows[idx]
        rt = row["running_time_sec"]
        frame_path = find_nearest_frame(timeline, rt)
        if frame_path is None:
            continue
        img = read_image_unicode(frame_path)
        if img is None:
            continue
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        side = min(h, w)
        cx, cy = w // 2, h // 2
        hs = side // 2
        crop = img[cy - hs : cy + hs, cx - hs : cx + hs]
        if crop.size == 0:
            continue
        thumb = cv2.resize(crop, (140, 140), interpolation=cv2.INTER_AREA)
        oi = OffsetImage(thumb, zoom=0.45)
        ab = AnnotationBbox(oi, (rt, 0.55), frameon=True, pad=0.15, bboxprops={"edgecolor": "white", "linewidth": 1.0})
        ax_bot.add_artist(ab)
        ax_bot.text(
            rt,
            0.06,
            f"{rt:.0f}s\nΔ{row['color_delta']:.1f}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="white",
            bbox={"boxstyle": "round,pad=0.2", "fc": "black", "ec": "none", "alpha": 0.55},
        )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_session_flows(
    events_csv: Path,
    summary_csv: Path,
    base_dir: Path,
    out_dir: Path,
    max_thumbs: int = 8,
    thumb_mode: str = "all",
    log: LogFn = _default_log,
) -> int:
    setup_font()
    rows = _load_rows(events_csv)
    if not rows:
        raise RuntimeError(f"No rows in {events_csv}")

    target_map = _load_target_time_map(summary_csv)
    by_session: Dict[Tuple[str, str, str], List[dict]] = defaultdict(list)
    for r in rows:
        by_session[(r["pot"], r["session_id"], r["food_type"])].append(r)

    generated = 0
    for (pot, session_id, food), session_rows in sorted(by_session.items(), key=lambda kv: kv[0][1]):
        out_path = out_dir / pot / f"session_flow_{session_id}_{food}.png"
        target_time = target_map.get((pot, session_id, food), 0)
        try:
            _render_one_session(session_rows, base_dir, out_path, max_thumbs, thumb_mode, target_time)
            generated += 1
        except Exception as e:
            log(f"[WARN] plot skip {pot}/{session_id}/{food}: {e}")
    log(f"[DONE] session flow plots: {generated}")
    return generated


def extract_suitability(
    base_dir: Path,
    out_csv: Path,
    expected_lift: int = 3,
    color_threshold: float = 25.0,
    w_t: float = 0.4,
    w_c: float = 0.4,
    w_l: float = 0.2,
    log: LogFn = _default_log,
) -> Path:
    s = w_t + w_c + w_l
    if abs(s - 1.0) > 1e-8:
        w_t, w_c, w_l = w_t / s, w_c / s, w_l / s

    lift_files: List[Path] = []
    for pot in ("pot1", "pot2"):
        pattern = base_dir / pot / "session_*" / "*" / "*_lift_events.json"
        lift_files.extend(Path(p) for p in sorted(glob.glob(str(pattern))))
    if not lift_files:
        raise FileNotFoundError(f"No *_lift_events.json found under {base_dir}")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "pot",
        "session_id",
        "food_type",
        "target_time",
        "running_time",
        "color_delta",
        "lift_count",
        "T",
        "C",
        "L",
        "suitability_score",
        "completion_rule_pass",
        "tracker_completion_detected",
    ]

    rows = []
    for lf in lift_files:
        try:
            data = _load_json(lf)
        except Exception as e:
            log(f"[WARN] invalid json skip: {lf} ({e})")
            continue

        parent = lf.parent
        pot = parent.parent.parent.name if len(parent.parents) >= 3 else "unknown"
        session_id = str(data.get("session_id") or parent.parent.name)
        food_type = str(data.get("food_type") or parent.name)
        target_time = _safe_float(data.get("target_time"), 0.0)
        events = data.get("lift_events", []) or []
        lift_count = int(data.get("lift_count") or len(events))

        if events:
            running_time = _safe_float(events[-1].get("running_time"), 0.0)
            color_delta = _safe_float(events[-1].get("color_delta"), 0.0)
        else:
            running_time = 0.0
            color_delta = 0.0

        t = min(max(running_time / target_time, 0.0), 1.0) if target_time > 0 else 0.0
        c = min(max(color_delta / color_threshold, 0.0), 1.0) if color_threshold > 0 else 0.0
        l = min(max(lift_count / expected_lift, 0.0), 1.0) if expected_lift > 0 else 0.0
        score = 100.0 * (w_t * t + w_c * c + w_l * l)
        rule = (score >= 85.0) and (t >= 0.9) and (c >= 0.8)

        rows.append(
            {
                "pot": pot,
                "session_id": session_id,
                "food_type": food_type,
                "target_time": round(target_time, 3),
                "running_time": round(running_time, 3),
                "color_delta": round(color_delta, 6),
                "lift_count": lift_count,
                "T": round(t, 6),
                "C": round(c, 6),
                "L": round(l, 6),
                "suitability_score": round(score, 4),
                "completion_rule_pass": rule,
                "tracker_completion_detected": bool(data.get("completion_detected", False)),
            }
        )

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    log(f"[DONE] suitability rows={len(rows)}")
    log(f"[DONE] {out_csv}")
    return out_csv


def run_lift_audit(base_dir: Path, out_dir: Path, log: LogFn = _default_log) -> Tuple[Path, Path]:
    rebuild_missing_lift_jsons(base_dir=base_dir, log=log)
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(base_dir / "pot*" / "session_*" / "*" / "*_lift_events.json")
    files = sorted(Path(p) for p in glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No *_lift_events.json found under {base_dir}")

    summary_csv = out_dir / "lift_audit_summary.csv"
    issues_csv = out_dir / "lift_audit_issues.csv"

    summary_fields = [
        "pot",
        "session_id",
        "food_type",
        "lift_json",
        "target_time_sec",
        "lift_count",
        "first_rt_sec",
        "last_rt_sec",
        "completion_detected",
        "monotonic_rt",
        "status",
        "issue_count",
    ]
    issue_fields = ["pot", "session_id", "food_type", "issue", "detail", "lift_json"]

    all_summary = []
    all_issues = []
    for fp in files:
        try:
            data = _load_json(fp)
        except Exception as e:
            all_issues.append({"pot": "", "session_id": "", "food_type": "", "issue": "JSON_PARSE_ERROR", "detail": str(e), "lift_json": str(fp)})
            continue

        pot = str(data.get("pot_name", "")).lower().replace("pot", "pot")
        if pot not in ("pot1", "pot2"):
            pot = "pot1" if "pot1" in fp.parts else ("pot2" if "pot2" in fp.parts else "")
        session_id = str(data.get("session_id", ""))
        food = str(data.get("food_type", ""))
        target = _safe_float(data.get("target_time"), 0.0)
        completion = bool(data.get("completion_detected", False))
        events = data.get("lift_events", []) or []
        rts = [_safe_float(e.get("running_time"), 0.0) for e in events]

        monotonic = True
        for i in range(1, len(rts)):
            if rts[i] < rts[i - 1]:
                monotonic = False
                break

        issues = []
        if not events:
            issues.append(("NO_LIFT_EVENTS", "lift_events is empty"))
        if not monotonic:
            issues.append(("NON_MONOTONIC_RT", "running_time goes backwards"))
        if completion and not events:
            issues.append(("COMPLETION_WITHOUT_EVENTS", "completion_detected=true but no events"))
        if events and target > 0 and rts[-1] < max(0.0, target * 0.4):
            issues.append(("VERY_EARLY_LAST_EVENT", f"last_rt={rts[-1]:.1f}s, target={target:.1f}s"))
        if events and target > 0 and rts[-1] > target * 1.5:
            issues.append(("VERY_LATE_LAST_EVENT", f"last_rt={rts[-1]:.1f}s, target={target:.1f}s"))

        status = "OK" if not issues else "CHECK_REQUIRED"
        all_summary.append(
            {
                "pot": pot,
                "session_id": session_id,
                "food_type": food,
                "lift_json": str(fp),
                "target_time_sec": round(target, 3),
                "lift_count": len(events),
                "first_rt_sec": round(rts[0], 3) if rts else 0.0,
                "last_rt_sec": round(rts[-1], 3) if rts else 0.0,
                "completion_detected": completion,
                "monotonic_rt": monotonic,
                "status": status,
                "issue_count": len(issues),
            }
        )
        for code, detail in issues:
            all_issues.append({"pot": pot, "session_id": session_id, "food_type": food, "issue": code, "detail": detail, "lift_json": str(fp)})

    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=summary_fields)
        w.writeheader()
        for row in all_summary:
            w.writerow(row)

    with issues_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=issue_fields)
        w.writeheader()
        for row in all_issues:
            w.writerow(row)

    ok_count = sum(1 for r in all_summary if r["status"] == "OK")
    log(f"[DONE] lift audit: total={len(all_summary)}, ok={ok_count}, check={len(all_summary) - ok_count}")
    log(f"[DONE] {summary_csv}")
    log(f"[DONE] {issues_csv}")
    return summary_csv, issues_csv


def run_full_analysis(base_dir: Path, out_dir: Path, log: LogFn = _default_log) -> Dict[str, Path]:
    rebuild_missing_lift_jsons(base_dir=base_dir, log=log)
    trend_dir = out_dir / "lift_event_trends"
    plot_dir = out_dir / "plots" / "session_flows_with_thumbs"
    suitability_csv = out_dir / f"completion_suitability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    events_csv, summary_csv = export_lift_event_trends(base_dir=base_dir, out_dir=trend_dir, log=log)
    plot_session_flows(events_csv=events_csv, summary_csv=summary_csv, base_dir=base_dir, out_dir=plot_dir, max_thumbs=8, thumb_mode="all", log=log)
    extract_suitability(base_dir=base_dir, out_csv=suitability_csv, log=log)
    return {"events_csv": events_csv, "summary_csv": summary_csv, "plots_dir": plot_dir, "suitability_csv": suitability_csv}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Windows frying analysis toolkit")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="Run color-trend analysis outputs")
    a.add_argument("--base-dir", required=True, help="AI_Data root path")
    a.add_argument("--out-dir", required=True, help="Output directory")

    l = sub.add_parser("lift-audit", help="Run lift-event consistency audit")
    l.add_argument("--base-dir", required=True, help="AI_Data root path")
    l.add_argument("--out-dir", required=True, help="Output directory")
    return p


def main() -> int:
    args = _build_parser().parse_args()
    base_dir = Path(args.base_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    if not base_dir.exists():
        print(f"[ERROR] base-dir not found: {base_dir}")
        return 1

    if args.command == "analyze":
        run_full_analysis(base_dir=base_dir, out_dir=out_dir)
        return 0
    if args.command == "lift-audit":
        run_lift_audit(base_dir=base_dir, out_dir=out_dir)
        return 0
    print("[ERROR] unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
