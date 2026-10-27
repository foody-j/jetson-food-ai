#!/usr/bin/env python3
"""
Manual completion-time labeling GUI.

Flow:
1) Load sessions from completion_suitability CSV.
2) Open one session in OpenCV window.
3) Move frames with keyboard and mark GT completion frame.
4) Save labels to CSV for F1/MAE evaluation.

Run:
  python3 scripts/completion_labeling_gui.py
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import cv2


DEFAULT_INPUT_CSV = Path(
    "/home/yjk/jetson-food-ai/reports/2026-02-15/data/completion_suitability_20260215_155509.csv"
)
DEFAULT_LABEL_CSV = Path(
    "/home/yjk/jetson-food-ai/reports/2026-02-15/data/manual_completion_labels.csv"
)


def parse_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def parse_clock_seconds(name: str) -> float | None:
    m = re.search(r"(\d{6})_(\d{3})", name)
    if not m:
        return None
    hhmmss, ms = m.group(1), m.group(2)
    hh = int(hhmmss[0:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:6])
    return hh * 3600 + mm * 60 + ss + int(ms) / 1000.0


def parse_dt(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return dt.datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def build_timeline(image_paths: list[Path]) -> list[tuple[float, Path]]:
    timeline: list[tuple[float, Path]] = []
    day_offset = 0.0
    prev: float | None = None
    first: float | None = None
    for p in image_paths:
        sec = parse_clock_seconds(p.name)
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


def choose_frying_camera(pot: str, session_dir: Path) -> Path:
    preferred = "camera_0" if pot == "pot1" else "camera_1"
    candidate = session_dir / preferred
    if candidate.is_dir():
        return candidate
    for alt in ("camera_0", "camera_1"):
        d = session_dir / alt
        if d.is_dir():
            return d
    return candidate


def infer_ai_pred_offset_sec(lift_json_path: Path) -> tuple[bool, float | None]:
    if not lift_json_path.exists():
        return False, None
    try:
        data = json.loads(lift_json_path.read_text(encoding="utf-8"))
    except Exception:
        return False, None

    detected = parse_bool(data.get("completion_detected", False))
    if not detected:
        return False, None

    start_time = parse_dt(data.get("start_time"))
    completion_time = parse_dt(data.get("completion_time"))
    if start_time and completion_time:
        delta = (completion_time - start_time).total_seconds()
        if delta >= 0:
            return True, float(delta)

    events = data.get("lift_events", []) or []
    if events:
        try:
            return True, float(events[-1].get("running_time", 0.0))
        except Exception:
            pass
    return True, None


@dataclass
class SessionItem:
    pot: str
    session_id: str
    food_type: str
    session_dir: Path
    lift_json: Path
    suitability_score: float
    ai_detected: bool
    ai_pred_offset_sec: float | None


class App:
    def __init__(self, root: tk.Tk, input_csv: Path, output_csv: Path):
        self.root = root
        self.input_csv = input_csv
        self.output_csv = output_csv
        self.sessions: list[SessionItem] = []
        self.label_map: dict[str, dict[str, str]] = {}
        self.selected: SessionItem | None = None

        self.root.title("Completion Labeling GUI")
        self.root.geometry("1220x760")

        self._build_ui()
        self._load_sessions()
        self._load_existing_labels()
        self._refresh_table()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Input CSV").grid(row=0, column=0, sticky="w")
        self.input_var = tk.StringVar(value=str(self.input_csv))
        ttk.Entry(top, textvariable=self.input_var, width=95).grid(row=0, column=1, padx=8)

        ttk.Label(top, text="Label CSV").grid(row=1, column=0, sticky="w")
        self.output_var = tk.StringVar(value=str(self.output_csv))
        ttk.Entry(top, textvariable=self.output_var, width=95).grid(row=1, column=1, padx=8)

        ttk.Button(top, text="Reload", command=self._reload_all).grid(row=0, column=2, padx=6)
        ttk.Button(top, text="Open Viewer", command=self._open_viewer).grid(row=1, column=2, padx=6)

        mid = ttk.Frame(self.root, padding=(10, 0, 10, 0))
        mid.pack(fill="both", expand=True)

        cols = (
            "pot",
            "session_id",
            "food_type",
            "score",
            "ai_detected",
            "ai_pred_sec",
            "labeled",
            "gt_sec",
            "gt_image",
        )
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", height=26)
        for c in cols:
            self.tree.heading(c, text=c)
            width = 120
            if c in {"session_id", "gt_image"}:
                width = 220
            if c == "food_type":
                width = 180
            self.tree.column(c, width=width, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        scroll = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        bottom = ttk.LabelFrame(self.root, text="Selected Session", padding=10)
        bottom.pack(fill="x", padx=10, pady=10)
        self.selected_label = tk.StringVar(value="(none)")
        ttk.Label(bottom, textvariable=self.selected_label).pack(anchor="w")
        ttk.Label(
            bottom,
            text=(
                "Viewer keys: n/Right(next), p/Left(prev), j/k(+/-10), g(mark GT), "
                "u(unmark), s(save), q(quit)"
            ),
        ).pack(anchor="w", pady=(6, 0))

    def _reload_all(self) -> None:
        self.input_csv = Path(self.input_var.get().strip())
        self.output_csv = Path(self.output_var.get().strip())
        self._load_sessions()
        self._load_existing_labels()
        self._refresh_table()

    def _load_sessions(self) -> None:
        self.sessions = []
        if not self.input_csv.exists():
            messagebox.showerror("Error", f"Input CSV not found:\n{self.input_csv}")
            return
        with self.input_csv.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                lift_json = Path(row.get("lift_json", ""))
                session_dir = lift_json.parent if lift_json else Path("")
                ai_detected = parse_bool(row.get("tracker_completion_detected", False))
                _, ai_pred = infer_ai_pred_offset_sec(lift_json)
                try:
                    score = float(row.get("suitability_score", 0.0))
                except Exception:
                    score = 0.0
                self.sessions.append(
                    SessionItem(
                        pot=row.get("pot", ""),
                        session_id=row.get("session_id", ""),
                        food_type=row.get("food_type", ""),
                        session_dir=session_dir,
                        lift_json=lift_json,
                        suitability_score=score,
                        ai_detected=ai_detected,
                        ai_pred_offset_sec=ai_pred,
                    )
                )

    def _load_existing_labels(self) -> None:
        self.label_map = {}
        out = Path(self.output_var.get().strip())
        if not out.exists():
            return
        with out.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row.get('pot','')}::{row.get('session_id','')}"
                self.label_map[key] = row

    def _refresh_table(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for s in self.sessions:
            key = f"{s.pot}::{s.session_id}"
            labeled = key in self.label_map
            row = self.label_map.get(key, {})
            self.tree.insert(
                "",
                "end",
                values=(
                    s.pot,
                    s.session_id,
                    s.food_type,
                    f"{s.suitability_score:.2f}",
                    "Y" if s.ai_detected else "N",
                    f"{s.ai_pred_offset_sec:.3f}" if s.ai_pred_offset_sec is not None else "",
                    "Y" if labeled else "N",
                    row.get("gt_offset_sec", ""),
                    row.get("gt_image_name", ""),
                ),
            )

    def _on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            self.selected = None
            self.selected_label.set("(none)")
            return
        vals = self.tree.item(sel[0], "values")
        pot, session_id = vals[0], vals[1]
        for s in self.sessions:
            if s.pot == pot and s.session_id == session_id:
                self.selected = s
                self.selected_label.set(
                    f"{s.pot} / {s.session_id} / {s.food_type} / {s.session_dir}"
                )
                return

    def _open_viewer(self) -> None:
        if not self.selected:
            messagebox.showwarning("Warning", "Select a session first.")
            return
        try:
            self._run_viewer(self.selected)
        except Exception as exc:
            messagebox.showerror("Viewer Error", str(exc))

    def _run_viewer(self, s: SessionItem) -> None:
        cam_dir = choose_frying_camera(s.pot, s.session_dir)
        images = sorted(cam_dir.glob("*.jpg"))
        if not images:
            raise RuntimeError(f"No JPG frames in: {cam_dir}")
        timeline = build_timeline(images)
        if not timeline:
            raise RuntimeError(f"Could not parse timestamps from frames: {cam_dir}")

        key = f"{s.pot}::{s.session_id}"
        existing = self.label_map.get(key, {})
        idx = 0
        marked_idx: int | None = None

        if existing.get("gt_image_name"):
            target = existing.get("gt_image_name")
            for i, (_, p) in enumerate(timeline):
                if p.name == target:
                    idx = i
                    marked_idx = i
                    break

        win = f"Completion Labeling - {s.session_id}"
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)

        while True:
            sec, img_path = timeline[idx]
            img = cv2.imread(str(img_path))
            if img is None:
                break

            if img.shape[1] > 1600:
                scale = 1600.0 / img.shape[1]
                img = cv2.resize(img, (1600, int(img.shape[0] * scale)))

            overlay = img.copy()
            panel_h = min(230, overlay.shape[0] // 2)
            cv2.rectangle(overlay, (0, 0), (overlay.shape[1], panel_h), (0, 0, 0), -1)
            lines = [
                f"{s.pot} | {s.session_id} | {s.food_type}",
                f"frame {idx+1}/{len(timeline)} | t={sec:.3f}s | file={img_path.name}",
                f"AI detected={'Y' if s.ai_detected else 'N'} | AI pred={s.ai_pred_offset_sec if s.ai_pred_offset_sec is not None else 'NA'}s",
                f"GT mark={'YES' if marked_idx is not None else 'NO'}"
                + (f" (idx={marked_idx+1}, t={timeline[marked_idx][0]:.3f}s)" if marked_idx is not None else ""),
                "keys: n/p next/prev, j/k -10/+10, g mark GT, u unmark, s save, q quit",
            ]
            y = 28
            for line in lines:
                cv2.putText(
                    overlay,
                    line,
                    (12, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                y += 32

            if marked_idx is not None and marked_idx == idx:
                cv2.rectangle(overlay, (8, panel_h + 8), (overlay.shape[1] - 8, overlay.shape[0] - 8), (0, 255, 0), 4)

            cv2.imshow(win, overlay)
            keycode = cv2.waitKey(0) & 0xFF

            if keycode in (ord("q"), 27):
                break
            if keycode in (ord("n"), 83):
                idx = min(len(timeline) - 1, idx + 1)
            elif keycode in (ord("p"), 81):
                idx = max(0, idx - 1)
            elif keycode == ord("j"):
                idx = max(0, idx - 10)
            elif keycode == ord("k"):
                idx = min(len(timeline) - 1, idx + 10)
            elif keycode == ord("g"):
                marked_idx = idx
            elif keycode == ord("u"):
                marked_idx = None
            elif keycode == ord("s"):
                if marked_idx is None:
                    messagebox.showwarning("Warning", "Mark GT frame first (key: g).")
                    continue
                self._save_label(
                    session=s,
                    gt_sec=timeline[marked_idx][0],
                    gt_image_name=timeline[marked_idx][1].name,
                )
                self._load_existing_labels()
                self._refresh_table()
                print(f"[SAVED] {s.pot}/{s.session_id} gt={timeline[marked_idx][0]:.3f}s")
                break

        cv2.destroyWindow(win)

    def _save_label(self, session: SessionItem, gt_sec: float, gt_image_name: str) -> None:
        out = Path(self.output_var.get().strip())
        out.parent.mkdir(parents=True, exist_ok=True)

        rows: list[dict[str, str]] = []
        fields = [
            "pot",
            "session_id",
            "food_type",
            "session_dir",
            "lift_json",
            "ai_detected",
            "ai_pred_offset_sec",
            "gt_offset_sec",
            "gt_image_name",
            "labeled_at",
        ]

        if out.exists():
            with out.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append({k: row.get(k, "") for k in fields})

        key = f"{session.pot}::{session.session_id}"
        new_row = {
            "pot": session.pot,
            "session_id": session.session_id,
            "food_type": session.food_type,
            "session_dir": str(session.session_dir),
            "lift_json": str(session.lift_json),
            "ai_detected": "True" if session.ai_detected else "False",
            "ai_pred_offset_sec": "" if session.ai_pred_offset_sec is None else f"{session.ai_pred_offset_sec:.6f}",
            "gt_offset_sec": f"{gt_sec:.6f}",
            "gt_image_name": gt_image_name,
            "labeled_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        replaced = False
        for i, row in enumerate(rows):
            if f"{row.get('pot','')}::{row.get('session_id','')}" == key:
                rows[i] = new_row
                replaced = True
                break
        if not replaced:
            rows.append(new_row)

        with out.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    App(root, DEFAULT_INPUT_CSV, DEFAULT_LABEL_CSV)
    root.mainloop()


if __name__ == "__main__":
    main()
