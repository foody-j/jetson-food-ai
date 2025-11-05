#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple 3-Camera Display
Clean minimal version for testing 3 GMSL cameras
"""

import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
from datetime import datetime
import time
import os
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import GStreamer camera wrapper
from gst_camera import GstCamera

# Load Configuration
def load_config(config_path="config.json"):
    """Load configuration from JSON file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, config_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

# Camera configurations from config.json
CAMERA_0_INDEX = config.get('camera_index', 0)
CAMERA_1_INDEX = config.get('stirfry_left_camera_index', 1)
CAMERA_2_INDEX = config.get('stirfry_right_camera_index', 2)
GMSL_MODE = config.get('gmsl_mode', 2)
GMSL_RESOLUTION_MODE = config.get('gmsl_resolution_mode', 1)
GMSL_DRIVER_DIR = config.get('gmsl_driver_dir',
    '/home/dkuyj/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3')

# Colors
COLOR_BG = "#1E1E1E"
COLOR_PANEL = "#2D2D2D"
COLOR_TEXT = "#FFFFFF"
COLOR_OK = "#00C853"
COLOR_ERROR = "#D32F2F"

print("[초기화] Simple 3-Camera Display 시작...")
print(f"[설정] 카메라 0: GMSL #{CAMERA_0_INDEX} @ 1920x1536")
print(f"[설정] 카메라 1: GMSL #{CAMERA_1_INDEX} @ 1920x1536")
print(f"[설정] 카메라 2: GMSL #{CAMERA_2_INDEX} @ 1920x1536")


class SimpleCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("3-Camera Display")
        self.running = True

        # Setup fullscreen
        self.root.configure(bg=COLOR_BG)
        self.root.attributes('-fullscreen', True)

        # Camera objects
        self.cap0 = None
        self.cap1 = None
        self.cap2 = None

        # Frame counters for debugging
        self.frame_count = [0, 0, 0]
        self.last_print_time = time.time()

        # Close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Build GUI
        self.create_gui()

        # Initialize cameras
        self.root.after(500, self.init_cameras)

    def create_gui(self):
        """Create simple 3-camera layout"""
        # Title bar
        title_frame = tk.Frame(self.root, bg=COLOR_PANEL, height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="3-Camera Display",
                font=("Arial", 24, "bold"), bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side=tk.LEFT, padx=20, pady=10)

        self.time_label = tk.Label(title_frame, text="--:--:--",
                                   font=("Arial", 20), bg=COLOR_PANEL, fg=COLOR_TEXT)
        self.time_label.pack(side=tk.RIGHT, padx=20, pady=10)

        # Exit button
        tk.Button(title_frame, text="EXIT", font=("Arial", 16, "bold"),
                 command=self.on_closing, bg=COLOR_ERROR, fg="white",
                 padx=20, pady=5).pack(side=tk.RIGHT, padx=10)

        # Main content - 3 cameras in vertical stack
        content = tk.Frame(self.root, bg=COLOR_BG)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure rows
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)
        content.rowconfigure(2, weight=1)
        content.columnconfigure(0, weight=1)

        # Camera 0
        panel0 = tk.LabelFrame(content, text=f"Camera 0 (GMSL #{CAMERA_0_INDEX})",
                              font=("Arial", 18, "bold"), bg=COLOR_PANEL, fg=COLOR_TEXT,
                              bd=2, relief=tk.GROOVE)
        panel0.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.preview0 = tk.Label(panel0, text="[Loading...]", bg="black", fg="white",
                                font=("Arial", 14))
        self.preview0.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status0 = tk.Label(panel0, text="Status: Initializing...",
                               font=("Arial", 12), bg=COLOR_PANEL, fg=COLOR_TEXT)
        self.status0.pack(pady=5)

        # Camera 1
        panel1 = tk.LabelFrame(content, text=f"Camera 1 (GMSL #{CAMERA_1_INDEX})",
                              font=("Arial", 18, "bold"), bg=COLOR_PANEL, fg=COLOR_TEXT,
                              bd=2, relief=tk.GROOVE)
        panel1.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.preview1 = tk.Label(panel1, text="[Loading...]", bg="black", fg="white",
                                font=("Arial", 14))
        self.preview1.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status1 = tk.Label(panel1, text="Status: Initializing...",
                               font=("Arial", 12), bg=COLOR_PANEL, fg=COLOR_TEXT)
        self.status1.pack(pady=5)

        # Camera 2
        panel2 = tk.LabelFrame(content, text=f"Camera 2 (GMSL #{CAMERA_2_INDEX})",
                              font=("Arial", 18, "bold"), bg=COLOR_PANEL, fg=COLOR_TEXT,
                              bd=2, relief=tk.GROOVE)
        panel2.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        self.preview2 = tk.Label(panel2, text="[Loading...]", bg="black", fg="white",
                                font=("Arial", 14))
        self.preview2.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status2 = tk.Label(panel2, text="Status: Initializing...",
                               font=("Arial", 12), bg=COLOR_PANEL, fg=COLOR_TEXT)
        self.status2.pack(pady=5)

        # Start clock
        self.update_clock()

    def init_cameras(self):
        """Initialize all 3 GMSL cameras using GStreamer"""
        print("[카메라] Initializing cameras with GStreamer...")

        # Camera 0
        try:
            print(f"[카메라] Starting Camera 0 (GMSL #{CAMERA_0_INDEX})...")
            self.cap0 = GstCamera(device_index=CAMERA_0_INDEX, width=1920, height=1536, fps=30)
            if self.cap0.start():
                print(f"[카메라] Camera 0 initialized ✓")
                self.status0.config(text="Status: Ready", fg=COLOR_OK)
            else:
                print(f"[오류] Camera 0 initialization failed")
                self.status0.config(text="Status: FAILED", fg=COLOR_ERROR)
                self.cap0 = None
        except Exception as e:
            print(f"[오류] Camera 0 error: {e}")
            self.status0.config(text=f"Status: ERROR - {e}", fg=COLOR_ERROR)
            self.cap0 = None

        # Camera 1
        try:
            print(f"[카메라] Starting Camera 1 (GMSL #{CAMERA_1_INDEX})...")
            self.cap1 = GstCamera(device_index=CAMERA_1_INDEX, width=1920, height=1536, fps=30)
            if self.cap1.start():
                print(f"[카메라] Camera 1 initialized ✓")
                self.status1.config(text="Status: Ready", fg=COLOR_OK)
            else:
                print(f"[오류] Camera 1 initialization failed")
                self.status1.config(text="Status: FAILED", fg=COLOR_ERROR)
                self.cap1 = None
        except Exception as e:
            print(f"[오류] Camera 1 error: {e}")
            self.status1.config(text=f"Status: ERROR - {e}", fg=COLOR_ERROR)
            self.cap1 = None

        # Camera 2
        try:
            print(f"[카메라] Starting Camera 2 (GMSL #{CAMERA_2_INDEX})...")
            self.cap2 = GstCamera(device_index=CAMERA_2_INDEX, width=1920, height=1536, fps=30)
            if self.cap2.start():
                print(f"[카메라] Camera 2 initialized ✓")
                self.status2.config(text="Status: Ready", fg=COLOR_OK)
            else:
                print(f"[오류] Camera 2 initialization failed")
                self.status2.config(text="Status: FAILED", fg=COLOR_ERROR)
                self.cap2 = None
        except Exception as e:
            print(f"[오류] Camera 2 error: {e}")
            self.status2.config(text=f"Status: ERROR - {e}", fg=COLOR_ERROR)
            self.cap2 = None

        # Start update loops
        print("[카메라] Starting update loops...")
        self.root.after(100, self.update_camera0)
        self.root.after(100, self.update_camera1)
        self.root.after(100, self.update_camera2)

        # Start FPS stats
        self.root.after(5000, self.print_fps_stats)

    def update_clock(self):
        """Update time display"""
        if not self.running:
            return
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.root.after(1000, self.update_clock)

    def update_camera0(self):
        """Update camera 0 display"""
        if not self.running:
            return

        try:
            if self.cap0 is not None and self.cap0.isOpened():
                ret, frame = self.cap0.read()
                if ret and frame is not None and frame.size > 0:
                    # Check if frame is valid (not all black)
                    if frame.mean() > 1.0:
                        self.frame_count[0] += 1
                        self.display_frame(frame, self.preview0)

                        # Update status periodically
                        if self.frame_count[0] % 30 == 0:
                            self.status0.config(text=f"Status: OK (Frame {self.frame_count[0]})", fg=COLOR_OK)
        except Exception as e:
            print(f"[Error] Camera 0 update error: {e}")

        self.root.after(50, self.update_camera0)  # 20 FPS for GUI (less CPU)

    def update_camera1(self):
        """Update camera 1 display"""
        if not self.running:
            return

        try:
            if self.cap1 is not None and self.cap1.isOpened():
                ret, frame = self.cap1.read()
                if ret and frame is not None and frame.size > 0:
                    if frame.mean() > 1.0:
                        self.frame_count[1] += 1
                        self.display_frame(frame, self.preview1)

                        if self.frame_count[1] % 30 == 0:
                            self.status1.config(text=f"Status: OK (Frame {self.frame_count[1]})", fg=COLOR_OK)
        except Exception as e:
            print(f"[Error] Camera 1 update error: {e}")

        self.root.after(50, self.update_camera1)

    def update_camera2(self):
        """Update camera 2 display"""
        if not self.running:
            return

        try:
            if self.cap2 is not None and self.cap2.isOpened():
                ret, frame = self.cap2.read()
                if ret and frame is not None and frame.size > 0:
                    if frame.mean() > 1.0:
                        self.frame_count[2] += 1
                        self.display_frame(frame, self.preview2)

                        if self.frame_count[2] % 30 == 0:
                            self.status2.config(text=f"Status: OK (Frame {self.frame_count[2]})", fg=COLOR_OK)
        except Exception as e:
            print(f"[Error] Camera 2 update error: {e}")

        self.root.after(50, self.update_camera2)

    def display_frame(self, frame, label):
        """Display frame in label with proper scaling"""
        try:
            # Resize to fit label while maintaining aspect ratio
            # Target: 640x512 (maintains 5:4 ratio from 1920x1536)
            # Use INTER_NEAREST for faster processing (less quality but much faster)
            preview = cv2.resize(frame, (640, 512), interpolation=cv2.INTER_NEAREST)
            preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)

            # Create PhotoImage directly from array (faster than PIL)
            img = Image.fromarray(preview_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            # Store reference to prevent garbage collection
            label.imgtk = imgtk
            label.configure(image=imgtk, text="")
        except Exception as e:
            pass  # Silently ignore display errors to avoid console spam

    def print_fps_stats(self):
        """Print FPS statistics periodically"""
        if not self.running:
            return

        current_time = time.time()
        elapsed = current_time - self.last_print_time

        if elapsed >= 5.0:  # Every 5 seconds
            fps0 = self.frame_count[0] / elapsed if elapsed > 0 else 0
            fps1 = self.frame_count[1] / elapsed if elapsed > 0 else 0
            fps2 = self.frame_count[2] / elapsed if elapsed > 0 else 0

            print(f"[FPS] Cam0: {fps0:.1f} | Cam1: {fps1:.1f} | Cam2: {fps2:.1f}")

            # Reset counters
            self.frame_count = [0, 0, 0]
            self.last_print_time = current_time

        self.root.after(5000, self.print_fps_stats)

    def on_closing(self):
        """Handle window close"""
        if messagebox.askokcancel("Exit", "Exit the program?"):
            print("[종료] Shutting down...")
            self.running = False

            # Release cameras (GstCamera has stop() method)
            if self.cap0 is not None:
                self.cap0.stop()
            if self.cap1 is not None:
                self.cap1.stop()
            if self.cap2 is not None:
                self.cap2.stop()

            self.root.destroy()
            print("[종료] Done")


if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleCameraApp(root)
    root.mainloop()
