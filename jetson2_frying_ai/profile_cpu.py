#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU 사용량 프로파일링 테스트
각 작업별로 CPU 사용률 측정
"""

import cv2
import numpy as np
import time
import psutil
from gst_camera import GstCamera
from frying_segmenter import FoodSegmenter
from ultralytics import YOLO

# 카메라 설정
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1536
CAMERA_FPS = 30

def measure_cpu(func, name, iterations=30):
    """함수 실행 중 CPU 사용률 측정"""
    print(f"\n{'='*50}")
    print(f"테스트: {name}")
    print(f"{'='*50}")

    # CPU 사용률 초기화
    psutil.cpu_percent(interval=0.1)

    start_time = time.time()
    cpu_samples = []

    for i in range(iterations):
        func()
        cpu_samples.append(psutil.cpu_percent(interval=0.01))
        if i % 10 == 0:
            print(f"  진행: {i+1}/{iterations} - CPU: {cpu_samples[-1]:.1f}%")

    end_time = time.time()
    elapsed = end_time - start_time
    avg_cpu = np.mean(cpu_samples)
    fps = iterations / elapsed

    print(f"\n결과:")
    print(f"  평균 CPU: {avg_cpu:.1f}%")
    print(f"  처리 시간: {elapsed:.2f}초")
    print(f"  FPS: {fps:.1f}")

    return avg_cpu, fps

# 테스트 1: 카메라 프레임 읽기
print("\n" + "="*60)
print("🔬 CPU 사용량 프로파일링 시작")
print("="*60)

print("\n[준비] 카메라 초기화 중...")
cap = GstCamera(device_index=0, width=CAMERA_WIDTH, height=CAMERA_HEIGHT, fps=CAMERA_FPS)
cap.start()
time.sleep(2)  # 카메라 안정화

# 프레임 미리 읽기
ret, test_frame = cap.read()
if not ret:
    print("❌ 카메라 읽기 실패!")
    exit(1)

print(f"✓ 카메라 준비 완료 ({test_frame.shape})")

# 테스트 함수들
def test_camera_read():
    """카메라 읽기만"""
    ret, frame = cap.read()
    return frame

def test_camera_and_resize():
    """카메라 읽기 + 리사이징"""
    ret, frame = cap.read()
    if ret:
        resized = cv2.resize(frame, (600, 450), interpolation=cv2.INTER_NEAREST)
    return frame

def test_camera_resize_convert():
    """카메라 읽기 + 리사이징 + 색상 변환"""
    ret, frame = cap.read()
    if ret:
        resized = cv2.resize(frame, (600, 450), interpolation=cv2.INTER_NEAREST)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    return frame

def test_with_overlay():
    """카메라 + 리사이징 + 변환 + 오버레이"""
    ret, frame = cap.read()
    if ret:
        vis = frame.copy()
        # 오버레이 그리기
        green_overlay = np.zeros_like(vis)
        green_overlay[:, :] = (0, 255, 0)
        mask = np.ones((vis.shape[0], vis.shape[1]), dtype=np.uint8) * 255
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        vis = cv2.addWeighted(vis, 0.7, cv2.bitwise_and(green_overlay, mask_3ch), 0.3, 0)

        # 텍스트 그리기
        cv2.putText(vis, "Brown: 45%", (16, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (60, 120, 200), 2)
        cv2.putText(vis, "Golden: 30%", (16, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)

        resized = cv2.resize(vis, (600, 450), interpolation=cv2.INTER_NEAREST)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    return frame

# 튀김 AI 테스트
print("\n[준비] Frying AI 로딩 중...")
segmenter = FoodSegmenter(mode="auto")
print("✓ Frying AI 준비 완료")

def test_frying_ai():
    """튀김 AI segmentation"""
    ret, frame = cap.read()
    if ret:
        result = segmenter.segment(frame, visualize=False)
    return frame

# YOLO 테스트
print("\n[준비] YOLO 로딩 중...")
yolo_seg = YOLO("../observe_add/besta.pt")
yolo_cls = YOLO("../observe_add/bestb.pt")

# GPU로 전환
import torch
if torch.cuda.is_available():
    yolo_seg.to('cuda')
    yolo_cls.to('cuda')
    print("✓ YOLO GPU 모드")
else:
    print("⚠ YOLO CPU 모드")

def test_yolo_seg():
    """YOLO segmentation"""
    ret, frame = cap.read()
    if ret:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        r = yolo_seg.predict(frame, imgsz=640, conf=0.5, verbose=False, device=device)[0]
    return frame

def test_yolo_cls():
    """YOLO classification"""
    ret, frame = cap.read()
    if ret:
        # ROI 추출 (중앙 영역)
        h, w = frame.shape[:2]
        roi = frame[h//4:3*h//4, w//4:3*w//4]
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        r = yolo_cls.predict(roi, imgsz=224, conf=0.0, verbose=False, device=device)[0]
    return frame

# 측정 실행
results = {}

print("\n\n" + "🚀 테스트 시작 (각 30 프레임 처리)" + "\n")

results['카메라 읽기'] = measure_cpu(test_camera_read, "1️⃣ 카메라 읽기 (GStreamer)")
results['+ 리사이징'] = measure_cpu(test_camera_and_resize, "2️⃣ 카메라 + 리사이징 (600x450)")
results['+ 색상변환'] = measure_cpu(test_camera_resize_convert, "3️⃣ 카메라 + 리사이징 + BGR→RGB")
results['+ 오버레이'] = measure_cpu(test_with_overlay, "4️⃣ 카메라 + 리사이징 + 변환 + 오버레이")
results['튀김 AI'] = measure_cpu(test_frying_ai, "5️⃣ 튀김 AI (FoodSegmenter)")
results['YOLO Seg'] = measure_cpu(test_yolo_seg, "6️⃣ YOLO Segmentation (GPU)")
results['YOLO Cls'] = measure_cpu(test_yolo_cls, "7️⃣ YOLO Classification (GPU)")

# 정리
cap.stop()

# 결과 요약
print("\n\n" + "="*60)
print("📊 CPU 사용량 요약")
print("="*60)

print(f"\n{'작업':<25} {'평균 CPU':<12} {'FPS':<8}")
print("-" * 50)
for name, (cpu, fps) in results.items():
    print(f"{name:<25} {cpu:>6.1f}%      {fps:>6.1f}")

# 분석 및 권장사항
print("\n\n" + "="*60)
print("💡 최적화 권장사항")
print("="*60)

total_cpu = sum([cpu for cpu, fps in results.values()])
print(f"\n현재 추정 총 CPU 사용률: {total_cpu:.1f}%")
print("(4개 카메라 동시 실행 시 더 높아질 수 있음)")

print("\n🎯 최적화 우선순위:")

# CPU 사용량 순으로 정렬
sorted_results = sorted(results.items(), key=lambda x: x[1][0], reverse=True)

for i, (name, (cpu, fps)) in enumerate(sorted_results[:3], 1):
    print(f"\n{i}. {name}")
    print(f"   CPU: {cpu:.1f}% - 가장 큰 병목!")

    if '카메라' in name or '리사이징' in name:
        print(f"   → 해결: 카메라 해상도 낮추기 (1920x1536 → 1280x1024)")
    elif '오버레이' in name:
        print(f"   → 해결: 오버레이 간소화 또는 frame skip")
    elif '튀김' in name:
        print(f"   → 해결: frame skip 증가 (3 → 5)")
    elif 'YOLO' in name:
        print(f"   → 해결: frame skip 증가 (5 → 10) 또는 해상도 낮추기")

print("\n" + "="*60)
print("✅ 프로파일링 완료!")
print("="*60)
print("\n권장 설정:")
print("  - 카메라 해상도: 1280x1024 (현재: 1920x1536)")
print("  - 튀김 AI frame skip: 5 (현재: 3)")
print("  - 바켓 AI frame skip: 10 (현재: 5)")
print("  - GUI 업데이트: 100ms (현재: 50ms)")
print(f"\n예상 CPU 절감: {total_cpu * 0.5:.0f}% → {total_cpu * 0.25:.0f}%")
