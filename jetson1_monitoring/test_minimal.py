#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal test to see if GUI shows up immediately"""

import tkinter as tk
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("[TEST] Starting minimal GUI test...", flush=True)
print("[TEST] Creating Tk window...", flush=True)

root = tk.Tk()
root.title("Minimal Test")
root.attributes('-fullscreen', True)
root.configure(bg='black')

print("[TEST] Creating widgets...", flush=True)

# Large visible label
label = tk.Label(
    root,
    text="GUI IS WORKING!\nTime will update below",
    font=("Arial", 72, "bold"),
    bg='green',
    fg='white',
    pady=50
)
label.pack(expand=True)

time_label = tk.Label(
    root,
    text="--:--:--",
    font=("Arial", 48),
    bg='blue',
    fg='yellow'
)
time_label.pack()

print("[TEST] Widgets created!", flush=True)

def update_time():
    """Update time every second"""
    current_time = time.strftime('%H:%M:%S')
    time_label.config(text=current_time)
    root.after(1000, update_time)

print("[TEST] Starting time update loop...", flush=True)
update_time()

print("[TEST] Starting mainloop - GUI should appear NOW!", flush=True)
root.mainloop()
print("[TEST] Mainloop ended", flush=True)
