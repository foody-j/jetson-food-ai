#!/usr/bin/env python3
"""
Test UYVY camera capture with OpenCV V4L2
"""
import cv2
import numpy as np

print("Testing UYVY capture with OpenCV V4L2...")

# Try camera 0
device = "/dev/video0"
print(f"\nOpening {device}...")

cap = cv2.VideoCapture(device, cv2.CAP_V4L2)

if not cap.isOpened():
    print(f"ERROR: Failed to open {device}")
    exit(1)

print("Camera opened successfully!")

# Try to set UYVY format
fourcc = cv2.VideoWriter_fourcc(*'UYVY')
cap.set(cv2.CAP_PROP_FOURCC, fourcc)

# Set resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1536)

# Get actual settings
actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
actual_fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
fourcc_str = "".join([chr((actual_fourcc >> 8 * i) & 0xFF) for i in range(4)])

print(f"Resolution: {actual_width}x{actual_height}")
print(f"FOURCC: {fourcc_str}")

# Try to read 5 frames
print("\nReading frames...")
for i in range(5):
    ret, frame = cap.read()
    if ret:
        print(f"Frame {i+1}: OK - Shape: {frame.shape}, Mean: {frame.mean():.1f}, DType: {frame.dtype}")

        # Check if it's a valid frame (not all black/green)
        if frame.mean() > 10:
            print(f"  -> Frame looks valid! (mean > 10)")
        else:
            print(f"  -> WARNING: Frame might be black/corrupted (mean <= 10)")
    else:
        print(f"Frame {i+1}: FAILED to read")

cap.release()
print("\nTest complete!")
