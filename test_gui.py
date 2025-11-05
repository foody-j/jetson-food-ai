#!/usr/bin/env python3
import tkinter as tk
import time

print("Creating window...")
root = tk.Tk()
root.title("GUI Test")
root.geometry("800x600")

label = tk.Label(root, text="GUI WORKING!", font=("Arial", 48), bg="green", fg="white")
label.pack(expand=True, fill=tk.BOTH)

print("Window created, starting mainloop...")
print("Press Ctrl+C to exit")

def update_time():
    label.config(text=f"Time: {time.strftime('%H:%M:%S')}")
    root.after(1000, update_time)

update_time()
root.mainloop()
