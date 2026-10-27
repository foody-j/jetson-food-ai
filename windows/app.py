#!/usr/bin/env python3
from __future__ import annotations

import queue
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from frying_toolkit import run_full_analysis, run_lift_audit


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Frying Data Analyzer (Windows)")
        self.root.geometry("980x680")

        self.base_dir_var = tk.StringVar()
        self.out_dir_var = tk.StringVar()
        self._busy = False
        self._q: "queue.Queue[str]" = queue.Queue()

        self._build_ui()
        self.root.after(100, self._poll_logs)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        src = ttk.LabelFrame(frame, text="Data Paths", padding=10)
        src.pack(fill="x")

        ttk.Label(src, text="AI_Data Root").grid(row=0, column=0, sticky="w")
        ttk.Entry(src, textvariable=self.base_dir_var, width=90).grid(row=0, column=1, padx=8, pady=4, sticky="we")
        ttk.Button(src, text="Browse", command=self._pick_base_dir).grid(row=0, column=2, padx=4)

        ttk.Label(src, text="Output Root").grid(row=1, column=0, sticky="w")
        ttk.Entry(src, textvariable=self.out_dir_var, width=90).grid(row=1, column=1, padx=8, pady=4, sticky="we")
        ttk.Button(src, text="Browse", command=self._pick_out_dir).grid(row=1, column=2, padx=4)

        actions = ttk.LabelFrame(frame, text="Actions", padding=10)
        actions.pack(fill="x", pady=(10, 0))

        self.btn_analyze = ttk.Button(actions, text="색변화 분석 실행", command=self._run_analyze)
        self.btn_analyze.pack(side="left", padx=4)
        self.btn_lift = ttk.Button(actions, text="리프트 점검 실행", command=self._run_lift_audit)
        self.btn_lift.pack(side="left", padx=4)

        tips = ttk.LabelFrame(frame, text="Output", padding=10)
        tips.pack(fill="x", pady=(10, 0))
        ttk.Label(
            tips,
            text="분석: lift_event_trends CSV + 세션 그래프(썸네일) + completion_suitability CSV\n리프트 점검: lift_audit_summary.csv + lift_audit_issues.csv",
        ).pack(anchor="w")

        self.log = tk.Text(frame, height=24)
        self.log.pack(fill="both", expand=True, pady=(10, 0))

        now = datetime.now().strftime("%Y%m%d")
        self.out_dir_var.set(str(Path.cwd() / f"reports_{now}"))

    def _pick_base_dir(self) -> None:
        p = filedialog.askdirectory(title="Select AI_Data Root")
        if p:
            self.base_dir_var.set(p)

    def _pick_out_dir(self) -> None:
        p = filedialog.askdirectory(title="Select Output Root")
        if p:
            self.out_dir_var.set(p)

    def _append_log(self, msg: str) -> None:
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def _enqueue_log(self, msg: str) -> None:
        self._q.put(msg)

    def _poll_logs(self) -> None:
        while True:
            try:
                msg = self._q.get_nowait()
            except queue.Empty:
                break
            self._append_log(msg)
        self.root.after(100, self._poll_logs)

    def _validate_paths(self) -> tuple[Path, Path] | None:
        base = Path(self.base_dir_var.get().strip())
        out = Path(self.out_dir_var.get().strip())
        if not base.exists():
            messagebox.showerror("Error", f"AI_Data 경로가 없습니다.\n{base}")
            return None
        if not out:
            messagebox.showerror("Error", "Output 경로를 입력하세요.")
            return None
        out.mkdir(parents=True, exist_ok=True)
        return base, out

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.btn_analyze.configure(state=state)
        self.btn_lift.configure(state=state)

    def _run_thread(self, fn, base: Path, out: Path, title: str) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self._append_log(f"[START] {title}")

        def worker() -> None:
            try:
                fn(base_dir=base, out_dir=out, log=self._enqueue_log)
                self._enqueue_log(f"[DONE] {title}")
            except Exception as e:
                self._enqueue_log(f"[ERROR] {title}: {e}")
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def _run_analyze(self) -> None:
        paths = self._validate_paths()
        if not paths:
            return
        base, out = paths
        self._run_thread(run_full_analysis, base, out, "색변화 분석")

    def _run_lift_audit(self) -> None:
        paths = self._validate_paths()
        if not paths:
            return
        base, out = paths
        self._run_thread(run_lift_audit, base, out, "리프트 점검")


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
