#!/usr/bin/env python3
"""
GUI launcher for lift-event preview.

Run:
  python3 scripts/preview_lift_events_gui.py
"""

import glob
import json
import os
import re
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

import cv2


AI_DATA_ROOT = Path("/home/yjk/AI_Data")


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
        timeline.append((cur - first, p))
        prev = cur
    return timeline


def find_nearest_frame(timeline, target_sec):
    if not timeline:
        return None
    return min(timeline, key=lambda x: abs(x[0] - target_sec))


def draw_overlay(img, lines):
    out = img.copy()
    h, w = out.shape[:2]
    panel_h = min(190, h // 3)
    cv2.rectangle(out, (0, 0), (w, panel_h), (0, 0, 0), -1)
    y = 28
    for line in lines:
        cv2.putText(out, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
        y += 28
    return out


def run_preview(session_dir: Path, pot: str):
    lift_json_list = sorted(glob.glob(str(session_dir / "*_lift_events.json")))
    if not lift_json_list:
        messagebox.showerror("Error", f"No *_lift_events.json in\n{session_dir}")
        return
    lift_json = Path(lift_json_list[-1])

    cam_dir = session_dir / ("camera_0" if pot == "pot1" else "camera_1")
    images = [Path(p) for p in sorted(glob.glob(str(cam_dir / "*.jpg")))]
    if not images:
        messagebox.showerror("Error", f"No jpg frames in\n{cam_dir}")
        return

    with lift_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    events = data.get("lift_events", [])
    if not events:
        messagebox.showerror("Error", "No lift_events in json")
        return

    timeline = build_frame_timeline(images)
    if not timeline:
        messagebox.showerror("Error", "Could not parse frame timestamps")
        return

    idx = 0
    win = "Lift Event Preview"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    while True:
        ev = events[idx]
        target = float(ev.get("running_time", 0.0))
        frame_sec, frame_path = find_nearest_frame(timeline, target)
        img = cv2.imread(str(frame_path))
        if img is None:
            break
        h, w = img.shape[:2]
        target_w = 1280
        target_h = int(h * target_w / max(1, w))
        view = cv2.resize(img, (target_w, target_h))
        lines = [
            f"Event {idx + 1}/{len(events)} | {frame_path.name}",
            f"running_time={target:.1f}s | frame={frame_sec:.1f}s",
            f"color_delta={ev.get('color_delta', 0):.1f}",
            f"brown={ev.get('brown_ratio', 0):.3f} | golden={ev.get('golden_ratio', 0):.3f}",
            "n/right next, p/left prev, q/esc quit",
        ]
        view = draw_overlay(view, lines)
        cv2.imshow(win, view)
        key = cv2.waitKey(0) & 0xFF
        if key in (ord("q"), 27):
            break
        if key in (ord("n"), 83):
            idx = min(len(events) - 1, idx + 1)
        elif key in (ord("p"), 81):
            idx = max(0, idx - 1)
    cv2.destroyAllWindows()


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Lift Events Viewer")
        self.root.geometry("900x560")

        self.pot_var = tk.StringVar(value="pot2")
        self.session_var = tk.StringVar()
        self.food_var = tk.StringVar()

        self._build_ui()
        self.refresh_sessions()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        top = ttk.LabelFrame(frame, text="Select Session", padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Pot").grid(row=0, column=0, sticky="w")
        pot_cb = ttk.Combobox(top, textvariable=self.pot_var, values=["pot1", "pot2"], state="readonly", width=8)
        pot_cb.grid(row=0, column=1, padx=8)
        pot_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh_sessions())

        ttk.Label(top, text="Session").grid(row=0, column=2, sticky="w")
        self.session_cb = ttk.Combobox(top, textvariable=self.session_var, state="readonly", width=28)
        self.session_cb.grid(row=0, column=3, padx=8)
        self.session_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh_foods())

        ttk.Label(top, text="Food").grid(row=0, column=4, sticky="w")
        self.food_cb = ttk.Combobox(top, textvariable=self.food_var, state="readonly", width=22)
        self.food_cb.grid(row=0, column=5, padx=8)

        ttk.Button(top, text="Refresh", command=self.refresh_sessions).grid(row=0, column=6, padx=8)
        ttk.Button(top, text="Open Preview", command=self.open_preview).grid(row=0, column=7, padx=8)

        info = ttk.LabelFrame(frame, text="Tips", padding=10)
        info.pack(fill="x", pady=(10, 0))
        ttk.Label(
            info,
            text="Preview window keys: n/right(next), p/left(prev), q/esc(quit)",
        ).pack(anchor="w")

        self.log = tk.Text(frame, height=20)
        self.log.pack(fill="both", expand=True, pady=(10, 0))

    def _write(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def refresh_sessions(self):
        pot = self.pot_var.get()
        base = AI_DATA_ROOT / pot
        sessions = sorted([p.name for p in base.glob("session_*") if p.is_dir()])
        self.session_cb["values"] = sessions
        if sessions:
            self.session_var.set(sessions[-1])
        else:
            self.session_var.set("")
        self.refresh_foods()
        self._write(f"Loaded sessions: pot={pot}, count={len(sessions)}")

    def refresh_foods(self):
        pot = self.pot_var.get()
        sess = self.session_var.get()
        if not sess:
            self.food_cb["values"] = []
            self.food_var.set("")
            return
        sess_dir = AI_DATA_ROOT / pot / sess
        foods = sorted([p.name for p in sess_dir.iterdir() if p.is_dir()])
        self.food_cb["values"] = foods
        if foods:
            self.food_var.set(foods[0])
        else:
            self.food_var.set("")

    def open_preview(self):
        pot = self.pot_var.get()
        sess = self.session_var.get()
        food = self.food_var.get()
        if not (pot and sess and food):
            messagebox.showwarning("Warning", "Select pot/session/food first.")
            return
        session_dir = AI_DATA_ROOT / pot / sess / food
        if not session_dir.exists():
            messagebox.showerror("Error", f"Not found:\n{session_dir}")
            return
        self._write(f"Open preview: {session_dir}")
        run_preview(session_dir, pot)


def main():
    root = tk.Tk()
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
