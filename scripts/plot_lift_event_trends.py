#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402


def fnum(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


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
        # fallback: scan for common names
        for f in font_manager.findSystemFonts():
            name = Path(f).name.lower()
            if "nanum" in name or "noto" in name:
                chosen = f
                break
    if chosen:
        font_manager.fontManager.addfont(chosen)
        font_name = font_manager.FontProperties(fname=chosen).get_name()
        plt.rcParams["font.family"] = font_name
    plt.rcParams["axes.unicode_minus"] = False


def load_events(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["running_time_sec"] = fnum(row.get("running_time_sec", 0.0))
            row["color_delta"] = fnum(row.get("color_delta", 0.0))
            row["brown_ratio"] = fnum(row.get("brown_ratio", 0.0))
            row["golden_ratio"] = fnum(row.get("golden_ratio", 0.0))
            rows.append(row)
    return rows


def load_summary(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["delta_gain"] = fnum(row.get("delta_gain", 0.0))
            row["brown_gain"] = fnum(row.get("brown_gain", 0.0))
            row["golden_gain"] = fnum(row.get("golden_gain", 0.0))
            row["lift_count"] = fnum(row.get("lift_count", 0.0))
            rows.append(row)
    return rows


def plot_scatter_all(events, out_dir: Path):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    x = [r["running_time_sec"] for r in events]
    y1 = [r["color_delta"] for r in events]
    y2 = [r["brown_ratio"] for r in events]
    y3 = [r["golden_ratio"] for r in events]

    axes[0].scatter(x, y1, s=10, alpha=0.6)
    axes[0].set_title("Running Time vs Color Delta")
    axes[0].set_xlabel("running_time_sec")
    axes[0].set_ylabel("color_delta")

    axes[1].scatter(x, y2, s=10, alpha=0.6, color="tab:brown")
    axes[1].set_title("Running Time vs Brown Ratio")
    axes[1].set_xlabel("running_time_sec")
    axes[1].set_ylabel("brown_ratio")

    axes[2].scatter(x, y3, s=10, alpha=0.6, color="goldenrod")
    axes[2].set_title("Running Time vs Golden Ratio")
    axes[2].set_xlabel("running_time_sec")
    axes[2].set_ylabel("golden_ratio")

    fig.tight_layout()
    out_path = out_dir / "scatter_all_events.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_food_median_trend(events, out_dir: Path):
    by_food = defaultdict(list)
    for r in events:
        by_food[r.get("food_type", "unknown")].append(r)

    foods = []
    med_delta = []
    med_brown = []
    med_golden = []
    for food, rows in sorted(by_food.items(), key=lambda kv: kv[0]):
        if not rows:
            continue
        rows_sorted = sorted(rows, key=lambda x: x["running_time_sec"])
        deltas = [x["color_delta"] for x in rows_sorted]
        browns = [x["brown_ratio"] for x in rows_sorted]
        goldens = [x["golden_ratio"] for x in rows_sorted]
        foods.append(food)
        med_delta.append(sorted(deltas)[len(deltas) // 2])
        med_brown.append(sorted(browns)[len(browns) // 2])
        med_golden.append(sorted(goldens)[len(goldens) // 2])

    if not foods:
        return

    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    xpos = list(range(len(foods)))

    axes[0].bar(xpos, med_delta, color="tab:blue")
    axes[0].set_title("Median Color Delta by Food")
    axes[0].set_ylabel("median_delta")

    axes[1].bar(xpos, med_brown, color="tab:brown")
    axes[1].set_title("Median Brown Ratio by Food")
    axes[1].set_ylabel("median_brown")

    axes[2].bar(xpos, med_golden, color="goldenrod")
    axes[2].set_title("Median Golden Ratio by Food")
    axes[2].set_ylabel("median_golden")
    axes[2].set_xticks(xpos)
    axes[2].set_xticklabels(foods, rotation=35, ha="right")

    fig.tight_layout()
    out_path = out_dir / "food_median_metrics.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_session_gain(summary, out_dir: Path):
    by_food = defaultdict(list)
    for r in summary:
        by_food[r.get("food_type", "unknown")].append(r)

    foods = []
    gain_delta = []
    gain_brown = []
    gain_golden = []
    for food, rows in sorted(by_food.items(), key=lambda kv: kv[0]):
        foods.append(food)
        d = sorted(x["delta_gain"] for x in rows)
        b = sorted(x["brown_gain"] for x in rows)
        g = sorted(x["golden_gain"] for x in rows)
        gain_delta.append(d[len(d) // 2] if d else 0.0)
        gain_brown.append(b[len(b) // 2] if b else 0.0)
        gain_golden.append(g[len(g) // 2] if g else 0.0)

    if not foods:
        return

    fig, ax = plt.subplots(figsize=(14, 6))
    x = list(range(len(foods)))
    w = 0.27
    ax.bar([i - w for i in x], gain_delta, width=w, label="delta_gain")
    ax.bar(x, gain_brown, width=w, label="brown_gain")
    ax.bar([i + w for i in x], gain_golden, width=w, label="golden_gain")
    ax.set_title("Median Session Gain by Food")
    ax.set_ylabel("gain")
    ax.set_xticks(x)
    ax.set_xticklabels(foods, rotation=35, ha="right")
    ax.legend()
    fig.tight_layout()
    out_path = out_dir / "food_session_gain.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description="Plot lift-event trend CSVs")
    ap.add_argument(
        "--input-dir",
        default="~/jetson-food-ai/reports/lift_event_trends",
        help="Directory containing lift_event_trends.csv and lift_event_session_summary.csv",
    )
    ap.add_argument("--output-dir", default="", help="Output plot dir (default: <input>/plots)")
    args = ap.parse_args()

    in_dir = Path(args.input_dir).expanduser()
    out_dir = Path(args.output_dir).expanduser() if args.output_dir else (in_dir / "plots")
    out_dir.mkdir(parents=True, exist_ok=True)

    events_csv = in_dir / "lift_event_trends.csv"
    summary_csv = in_dir / "lift_event_session_summary.csv"
    if not events_csv.exists() or not summary_csv.exists():
        print("[ERROR] missing input csv files")
        return 1

    events = load_events(events_csv)
    summary = load_summary(summary_csv)

    if not events:
        print("[ERROR] no events")
        return 1

    setup_korean_font()

    plot_scatter_all(events, out_dir)
    plot_food_median_trend(events, out_dir)
    plot_session_gain(summary, out_dir)

    print(f"[DONE] plots_dir={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
