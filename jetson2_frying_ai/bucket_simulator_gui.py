#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple GUI launcher for offline bucket simulation.
- Select a saved session
- Run left(cam2) / right(cam3) / both checks
- Stream CLI logs in a text area
"""

import os
import sys
import glob
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_SCRIPT = os.path.join(SCRIPT_DIR, "test_bucket_detection_simulation.py")


def list_images(folder: str):
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    files = []
    for p in sorted(glob.glob(os.path.join(folder, "*"))):
        if os.path.splitext(p)[1].lower() in exts:
            files.append(p)
    return files


def count_camera_images(session_dir: str):
    cam2 = 0
    cam3 = 0

    d2 = os.path.join(session_dir, "camera_2")
    d3 = os.path.join(session_dir, "camera_3")
    if os.path.isdir(d2):
        cam2 += len(list_images(d2))
    if os.path.isdir(d3):
        cam3 += len(list_images(d3))

    if cam2 == 0 and cam3 == 0:
        for name in os.listdir(session_dir):
            child = os.path.join(session_dir, name)
            if not os.path.isdir(child):
                continue
            d2 = os.path.join(child, "camera_2")
            d3 = os.path.join(child, "camera_3")
            if os.path.isdir(d2):
                cam2 += len(list_images(d2))
            if os.path.isdir(d3):
                cam3 += len(list_images(d3))

    return cam2, cam3


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bucket Offline Simulator")
        self.root.geometry("1100x700")

        self.proc = None
        self.proc_lock = threading.Lock()
        self.session_paths = []
        self.stop_event = threading.Event()

        self._build_ui()
        self.refresh_sessions()

    def _build_ui(self):
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(top, text="Data roots (comma-separated):").grid(row=0, column=0, sticky="w")
        default_roots = ",".join([
            os.path.expanduser("~/AI_Data/pot1"),
            os.path.expanduser("~/AI_Data/pot2"),
            os.path.expanduser("~/AI_Data/BucketData"),
        ])
        self.roots_var = tk.StringVar(value=default_roots)
        ttk.Entry(top, textvariable=self.roots_var, width=110).grid(row=0, column=1, columnspan=6, sticky="we", padx=6)

        ttk.Label(top, text="Config:").grid(row=1, column=0, sticky="w")
        self.config_var = tk.StringVar(value=os.path.join(SCRIPT_DIR, "config_jetson2_web.json"))
        ttk.Entry(top, textvariable=self.config_var, width=70).grid(row=1, column=1, columnspan=3, sticky="we", padx=6)

        ttk.Label(top, text="Device:").grid(row=1, column=4, sticky="e")
        self.device_var = tk.StringVar(value="cuda")
        ttk.Combobox(top, textvariable=self.device_var, values=["cuda", "cpu", "0"], width=10, state="readonly").grid(row=1, column=5, sticky="w")

        self.display_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Display window", variable=self.display_var).grid(row=1, column=6, sticky="w")
        ttk.Label(top, text="Display FPS:").grid(row=1, column=7, sticky="e")
        self.display_fps_var = tk.StringVar(value="8")
        ttk.Entry(top, textvariable=self.display_fps_var, width=6).grid(row=1, column=8, sticky="w", padx=4)

        ttk.Label(top, text="Save vis dir:").grid(row=2, column=0, sticky="w")
        self.save_dir_var = tk.StringVar(value=os.path.join(SCRIPT_DIR, "sim_vis_output"))
        ttk.Entry(top, textvariable=self.save_dir_var, width=70).grid(row=2, column=1, columnspan=3, sticky="we", padx=6)

        self.save_vis_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Save visualized frames", variable=self.save_vis_var).grid(row=2, column=4, columnspan=2, sticky="w")

        ttk.Label(top, text="Max images (0=all):").grid(row=2, column=6, sticky="e")
        self.max_images_var = tk.StringVar(value="200")
        ttk.Entry(top, textvariable=self.max_images_var, width=8).grid(row=2, column=7, sticky="w", padx=4)

        btns = ttk.Frame(self.root)
        btns.pack(fill=tk.X, padx=10, pady=6)

        ttk.Button(btns, text="Refresh sessions", command=self.refresh_sessions).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Run Left (cam2)", command=lambda: self.run_selected("left")).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Run Right (cam3)", command=lambda: self.run_selected("right")).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Run Both", command=lambda: self.run_selected("both")).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Auto Run All", command=self.run_all_sessions).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Stop", command=self.stop_running).pack(side=tk.LEFT, padx=4)

        body = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=2)

        ttk.Label(left, text="Sessions").pack(anchor="w")
        self.listbox = tk.Listbox(left, height=25)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        ttk.Label(right, text="Run log").pack(anchor="w")
        self.log = tk.Text(right, wrap="none")
        self.log.pack(fill=tk.BOTH, expand=True)

    def append_log(self, text: str):
        self.log.insert(tk.END, text)
        self.log.see(tk.END)

    def refresh_sessions(self):
        self.listbox.delete(0, tk.END)
        self.session_paths = []

        roots = [x.strip() for x in self.roots_var.get().split(",") if x.strip()]
        sessions = []
        for root in roots:
            root = os.path.expanduser(root)
            if not os.path.isdir(root):
                continue
            for s in sorted(glob.glob(os.path.join(root, "session_*"))):
                if os.path.isdir(s):
                    sessions.append(s)

        sessions.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        for s in sessions:
            c2, c3 = count_camera_images(s)
            if c2 == 0 and c3 == 0:
                continue
            root_name = os.path.basename(os.path.dirname(s))
            label = f"{root_name} | {os.path.basename(s)} | cam2:{c2} cam3:{c3}"
            self.session_paths.append(s)
            self.listbox.insert(tk.END, label)

        self.append_log(f"[INFO] sessions loaded: {len(self.session_paths)}\n")

    def get_selected_session(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        if idx < 0 or idx >= len(self.session_paths):
            return None
        return self.session_paths[idx]

    def build_cmd(self, session_dir: str, side: str):
        cmd = [
            sys.executable,
            SIM_SCRIPT,
            session_dir,
            "--side", side,
            "--config", self.config_var.get().strip(),
            "--device", self.device_var.get().strip(),
        ]
        if self.display_var.get():
            cmd.append("--display")
            disp_fps = self.display_fps_var.get().strip()
            if disp_fps:
                cmd.extend(["--display-fps", disp_fps])
        max_images = self.max_images_var.get().strip()
        if max_images:
            cmd.extend(["--max-images", max_images])
        if self.save_vis_var.get():
            save_dir = self.save_dir_var.get().strip()
            if save_dir:
                target = os.path.join(save_dir, os.path.basename(session_dir), side)
                cmd.extend(["--save-vis", target])
        return cmd

    def run_selected(self, side: str):
        self.stop_event.clear()
        session_dir = self.get_selected_session()
        if not session_dir:
            messagebox.showwarning("No session", "세션을 먼저 선택하세요.")
            return

        if not os.path.isfile(SIM_SCRIPT):
            messagebox.showerror("Missing script", f"시뮬레이터 스크립트 없음:\n{SIM_SCRIPT}")
            return

        c2, c3 = count_camera_images(session_dir)
        has_left = c2 > 0
        has_right = c3 > 0

        if side == "both":
            sides = []
            if has_left:
                sides.append("left")
            if has_right:
                sides.append("right")
            if not sides:
                messagebox.showwarning("No camera data", "선택 세션에 camera_2/camera_3 이미지가 없습니다.")
                return
        elif side == "left":
            if not has_left:
                messagebox.showwarning("No cam2", "이 세션에는 camera_2 데이터가 없습니다. right(cam3)로 실행하세요.")
                return
            sides = ["left"]
        else:
            if not has_right:
                messagebox.showwarning("No cam3", "이 세션에는 camera_3 데이터가 없습니다. left(cam2)로 실행하세요.")
                return
            sides = ["right"]

        t = threading.Thread(target=self._run_sequence, args=(session_dir, sides), daemon=True)
        t.start()

    def run_all_sessions(self):
        self.stop_event.clear()
        if self.proc is not None:
            messagebox.showwarning("Busy", "이미 실행 중입니다. 먼저 Stop 하세요.")
            return
        if not self.session_paths:
            messagebox.showwarning("No sessions", "세션 목록이 비어 있습니다. Refresh 후 다시 시도하세요.")
            return
        t = threading.Thread(target=self._run_all_sequence, daemon=True)
        t.start()

    def _run_all_sequence(self):
        total_jobs = 0
        for session_dir in self.session_paths:
            c2, c3 = count_camera_images(session_dir)
            if c2 > 0:
                total_jobs += 1
            if c3 > 0:
                total_jobs += 1
        done_jobs = 0
        self.append_log(f"\n[AUTO] total jobs={total_jobs}\n")
        for session_dir in self.session_paths:
            if self.stop_event.is_set():
                break
            c2, c3 = count_camera_images(session_dir)
            sides = []
            if c2 > 0:
                sides.append("left")
            if c3 > 0:
                sides.append("right")
            if not sides:
                continue
            self.append_log(f"\n[AUTO] session={session_dir} sides={sides}\n")
            for side in sides:
                if self.stop_event.is_set():
                    break
                self._run_sequence(session_dir, [side])
                done_jobs += 1
                self.append_log(f"[AUTO] progress {done_jobs}/{total_jobs}\n")
        self.append_log("[AUTO] done\n")

    def _run_sequence(self, session_dir: str, sides):
        for side in sides:
            if self.stop_event.is_set():
                self.append_log("[INFO] stopped by user\n")
                return
            if self.proc is not None:
                self.append_log("[WARN] already running. stop first.\n")
                return

            cmd = self.build_cmd(session_dir, side)
            self.append_log("\n" + "=" * 80 + "\n")
            self.append_log(f"[RUN] {' '.join(cmd)}\n")

            with self.proc_lock:
                self.proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

            for line in self.proc.stdout:
                self.append_log(line)

            rc = self.proc.wait()
            self.append_log(f"[DONE] side={side}, return_code={rc}\n")
            with self.proc_lock:
                self.proc = None

    def stop_running(self):
        self.stop_event.set()
        with self.proc_lock:
            p = self.proc
        if p is None:
            self.append_log("[INFO] no running process\n")
            return
        try:
            p.terminate()
            self.append_log("[INFO] terminate signal sent\n")
        except Exception as e:
            self.append_log(f"[ERROR] stop failed: {e}\n")


def main():
    if not os.environ.get("DISPLAY"):
        print("[ERROR] GUI 실행 불가: DISPLAY 환경변수가 없습니다.")
        print(" - 로컬 모니터 세션에서 실행하거나")
        print(" - SSH라면 X11 forwarding(ssh -X/-Y) 설정이 필요합니다.")
        print(" - 대안: CLI 실행")
        print("   python3 test_bucket_detection_simulation.py <session_dir> --side left --display")
        sys.exit(1)
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
