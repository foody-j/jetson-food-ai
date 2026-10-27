#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.offsetbox import AnnotationBbox, OffsetImage  # noqa: E402


def setup_korean_font():
    candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    chosen = None
    for p in candidates:
        if Path(p).exists():
            chosen = p
            break
    if chosen is None:
        for f in font_manager.findSystemFonts():
            n = Path(f).name.lower()
            if "nanum" in n or "noto" in n:
                chosen = f
                break
    if chosen:
        font_manager.fontManager.addfont(chosen)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=chosen).get_name()
    plt.rcParams["axes.unicode_minus"] = False


def parse_frame_clock_seconds(name: str) -> Optional[float]:
    m = re.search(r"(\d{6})_(\d{3})", name)
    if not m:
        return None
    hhmmss, ms = m.group(1), m.group(2)
    hh = int(hhmmss[0:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:6])
    return hh * 3600 + mm * 60 + ss + int(ms) / 1000.0


def build_frame_timeline(image_paths: List[Path]) -> List[Tuple[float, Path]]:
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
        rel = cur - first
        timeline.append((rel, p))
        prev = cur
    return timeline


def find_nearest_frame(timeline: List[Tuple[float, Path]], target: float) -> Optional[Path]:
    if not timeline:
        return None
    return min(timeline, key=lambda x: abs(x[0] - target))[1]


def load_rows(events_csv: Path):
    rows = []
    with events_csv.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["running_time_sec"] = float(row.get("running_time_sec") or 0.0)
            row["color_delta"] = float(row.get("color_delta") or 0.0)
            row["brown_ratio"] = float(row.get("brown_ratio") or 0.0)
            row["golden_ratio"] = float(row.get("golden_ratio") or 0.0)
            rows.append(row)
    return rows


def load_target_time_map(summary_csv: Path) -> Dict[Tuple[str, str, str], int]:
    out: Dict[Tuple[str, str, str], int] = {}
    if not summary_csv.exists():
        return out
    with summary_csv.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            pot = str(row.get("pot", "")).strip()
            session_id = str(row.get("session_id", "")).strip()
            food_type = str(row.get("food_type", "")).strip()
            try:
                target = int(float(row.get("target_time_sec", 0) or 0))
            except Exception:
                target = 0
            if pot and session_id and food_type:
                out[(pot, session_id, food_type)] = target
    return out


def pick_sample_indices(n: int, max_items: int) -> List[int]:
    if n <= 0:
        return []
    if n == 1:
        return [0]
    if max_items <= 1:
        return [0]
    if n <= max_items:
        return list(range(n))

    # Always include representative anchors (start/mid/end),
    # then fill the remaining slots with evenly spaced points.
    anchors = {0, n // 2, n - 1}
    remain = max_items - len(anchors)
    if remain > 0:
        extra = [round(i * (n - 1) / (remain - 1)) for i in range(remain)] if remain > 1 else [0]
        anchors.update(extra)
    out = sorted(anchors)
    if len(out) > max_items:
        out = out[:max_items]
    return out


def render_one_session(
    session_rows: List[dict],
    base_ai_data: Path,
    out_path: Path,
    max_thumbs: int,
    thumb_mode: str,
    target_time_sec: int = 0,
):
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

    # Completion guide lines: target-time based, 10-second interval marks
    if target_time_sec > 0:
        ready_time = max(0, target_time_sec - 60)
        candidate_time = max(ready_time, (x[-1] - 20.0) if x else ready_time)
        start_t = max(0, ready_time)
        end_t = max(target_time_sec + 60, int(max(x) + 1) if x else target_time_sec + 60)
        for t in range(start_t, end_t + 1, 10):
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

        # Last-20s candidate line
        ax_top.axvline(candidate_time, color="#2ecc71", alpha=0.85, linewidth=2.2, linestyle="-", zorder=1)
        ax_bot.axvline(candidate_time, color="#2ecc71", alpha=0.75, linewidth=2.0, linestyle="-", zorder=1)

        ax_top.text(
            ready_time,
            max(y_delta) * 0.96 if y_delta else 0.0,
            f"READY {ready_time}s",
            color="#f39c12",
            fontsize=9,
            ha="left",
            va="top",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#f39c12", alpha=0.7),
        )
        ax_top.text(
            target_time_sec,
            max(y_delta) * 0.88 if y_delta else 0.0,
            f"TARGET {target_time_sec}s",
            color="#e74c3c",
            fontsize=9,
            ha="left",
            va="top",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#e74c3c", alpha=0.7),
        )
        ax_top.text(
            candidate_time,
            max(y_delta) * 0.80 if y_delta else 0.0,
            f"CAND {candidate_time:.0f}s (last-20)",
            color="#27ae60",
            fontsize=9,
            ha="left",
            va="top",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#27ae60", alpha=0.75),
        )

    # bottom axis for thumbnails
    ax_bot.set_ylim(0, 1)
    ax_bot.set_yticks([])
    ax_bot.set_xlabel("running_time_sec")
    ax_bot.grid(alpha=0.2, axis="x")

    cam_dir = base_ai_data / pot / session_id / food / ("camera_0" if pot == "pot1" else "camera_1")
    images = [Path(p) for p in sorted(glob.glob(str(cam_dir / "*.jpg")))]
    timeline = build_frame_timeline(images)

    if thumb_mode == "all":
        sample_idxs = list(range(len(session_rows)))
    else:
        sample_idxs = pick_sample_indices(len(session_rows), max_thumbs)
    for idx in sample_idxs:
        row = session_rows[idx]
        rt = row["running_time_sec"]
        frame_path = find_nearest_frame(timeline, rt)
        if frame_path is None:
            continue
        img = cv2.imread(str(frame_path))
        if img is None:
            continue
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # small center crop for readability
        h, w = img.shape[:2]
        side = min(h, w)
        cx, cy = w // 2, h // 2
        hs = side // 2
        crop = img[cy - hs : cy + hs, cx - hs : cx + hs]
        thumb = cv2.resize(crop, (140, 140), interpolation=cv2.INTER_AREA)
        oi = OffsetImage(thumb, zoom=0.45)
        ab = AnnotationBbox(
            oi,
            (rt, 0.55),
            frameon=True,
            pad=0.15,
            bboxprops=dict(edgecolor="white", linewidth=1.0),
        )
        ax_bot.add_artist(ab)
        ax_bot.text(
            rt,
            0.06,
            f"{rt:.0f}s\nΔ{row['color_delta']:.1f}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="white",
            bbox=dict(boxstyle="round,pad=0.2", fc="black", ec="none", alpha=0.55),
        )

    # Guarantee that each session plot communicates thumbnail count explicitly.
    ax_bot.text(
        0.01,
        0.95,
        f"thumbs={len(sample_idxs)} mode={thumb_mode}",
        transform=ax_bot.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color="#2c3e50",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#95a5a6", alpha=0.8),
    )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description="Plot per-session flow with thumbnails")
    ap.add_argument(
        "--events-csv",
        default="~/jetson-food-ai/reports/lift_event_trends/lift_event_trends.csv",
        help="Path to lift_event_trends.csv",
    )
    ap.add_argument(
        "--summary-csv",
        default="~/jetson-food-ai/reports/lift_event_trends/lift_event_session_summary.csv",
        help="Path to lift_event_session_summary.csv",
    )
    ap.add_argument("--base-dir", default="~/AI_Data", help="AI_Data root")
    ap.add_argument(
        "--out-dir",
        default="~/jetson-food-ai/reports/lift_event_trends/plots/session_flows_with_thumbs",
        help="Output directory",
    )
    ap.add_argument("--max-thumbs", type=int, default=8, help="Max thumbnails per session")
    ap.add_argument(
        "--thumb-mode",
        choices=["sample", "all"],
        default="all",
        help="all: thumbnail for every event point, sample: limited thumbnails",
    )
    args = ap.parse_args()

    setup_korean_font()
    events_csv = Path(args.events_csv).expanduser()
    summary_csv = Path(args.summary_csv).expanduser()
    base_ai_data = Path(args.base_dir).expanduser()
    out_dir = Path(args.out_dir).expanduser()

    rows = load_rows(events_csv)
    target_time_map = load_target_time_map(summary_csv)
    if not rows:
        print("[ERROR] no rows in events csv")
        return 1

    by_session = defaultdict(list)
    for r in rows:
        key = (r["pot"], r["session_id"], r["food_type"])
        by_session[key].append(r)

    generated = 0
    for (pot, session_id, food), session_rows in sorted(by_session.items(), key=lambda kv: kv[0][1]):
        out_path = out_dir / pot / f"session_flow_{session_id}_{food}.png"
        render_one_session(
            session_rows,
            base_ai_data,
            out_path,
            max_thumbs=max(3, args.max_thumbs),
            thumb_mode=args.thumb_mode,
            target_time_sec=target_time_map.get((pot, session_id, food), 0),
        )
        generated += 1

    print(f"[DONE] generated={generated}")
    print(f"[DONE] out_dir={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
