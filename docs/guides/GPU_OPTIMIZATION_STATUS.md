# 🎮 GPU 최적화 현황 및 체크리스트

**업데이트**: 2025-01-05

---

## 📊 시스템 개요

| 시스템 | PyTorch | CUDA | GPU 가속 | 상태 |
|--------|---------|------|---------|------|
| **Jetson #1** | 2.8.0 | 12.6 ✅ | ⚠️ 부분적 | 최적화 필요 |
| **Jetson #2** | 2.8.0 | 12.6 ✅ | ✅ 완전 | 최적화 완료 |

---

## 🔍 Jetson #1 - 상세 분석

### 현재 상태

#### ✅ GPU 환경 준비 완료
```bash
PyTorch: 2.8.0
CUDA: 12.6 available
GPU device: Orin
```

#### ⚠️ YOLO 모델 GPU 사용 미확인
**문제**: YOLO 모델이 `device` 파라미터 없이 실행

**현재 코드** (`JETSON1_INTEGRATED.py:770`):
```python
self.yolo_model = YOLO(MODEL_PATH)
```

**predict 호출** (`JETSON1_INTEGRATED.py:879, 938`):
```python
results = self.yolo_model.predict(frame, conf=YOLO_CONF, imgsz=YOLO_IMGSZ, verbose=False)
# ❌ device 파라미터 없음!
```

### 최적화 방안

#### 옵션 1: 모델 로드 시 GPU 지정 (추천)
```python
# JETSON1_INTEGRATED.py:770
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
self.yolo_model = YOLO(MODEL_PATH)
self.yolo_model.to(device)  # GPU로 이동
print(f"[YOLO] 모델을 {device.upper()}에 로드 완료")
```

#### 옵션 2: predict 호출 시 GPU 지정
```python
# JETSON1_INTEGRATED.py:879, 938
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
results = self.yolo_model.predict(
    frame,
    conf=YOLO_CONF,
    imgsz=YOLO_IMGSZ,
    verbose=False,
    device=device  # ✅ GPU 명시
)
```

### 예상 성능 개선

| 항목 | CPU 모드 | GPU 모드 | 개선 |
|------|----------|---------|------|
| YOLO 추론 속도 | ~100ms | ~20ms | **5배** |
| FPS | 10 FPS | 30+ FPS | **3배** |
| CPU 사용률 | 80-100% | 20-30% | **70% 감소** |

---

## ✅ Jetson #2 - 상세 분석

### 현재 상태

#### ✅ GPU 환경 완벽 구성
```bash
PyTorch: 2.8.0 (jetson-ai-lab)
CUDA: 12.6 available
NumPy: 1.26.x (호환 버전)
```

#### ✅ YOLO 모델 GPU 사용 확인됨
**올바른 코드** (`JETSON2_INTEGRATED.py`):

**모델 초기화** (line ~320):
```python
import torch
self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"[GPU] CUDA 사용 가능! GPU 가속 활성화")

self.observe_seg_model = YOLO(OBSERVE_SEG_MODEL)
self.observe_cls_model = YOLO(OBSERVE_CLS_MODEL)
# 모델을 GPU로 이동
```

**predict 호출** (line ~804, 923):
```python
r = self.observe_seg_model.predict(
    frame,
    imgsz=IMG_SIZE_SEG,
    conf=CONF_SEG,
    verbose=False,
    device=self.device  # ✅ GPU 명시!
)
```

#### ✅ CPU 최적화 완료
- 카메라 해상도: 1920x1536 → 1280x720
- Frame skip: 3→15 (튀김), 5→20 (바켓)
- YOLO 입력: 640→512, 224→160
- GUI 업데이트: 50ms→100ms

---

## 🛠️ GPU 사용 확인 방법

### 방법 1: 프로그램 실행 중 jtop으로 확인
```bash
# 터미널 1
sudo jtop

# 터미널 2
cd ~/jetson-camera-monitor/jetson1_monitoring
python3 JETSON1_INTEGRATED.py
```

**확인 사항**:
- GPU 사용률이 올라가는가? (목표: 30-50%)
- CPU 사용률이 낮아지는가? (목표: <50%)

### 방법 2: 코드에서 직접 확인
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Current device: {next(model.parameters()).device}")
```

### 방법 3: YOLO verbose 출력 확인
```python
results = model.predict(frame, verbose=True, device='cuda')
# 출력에서 "Speed: 0.5ms preprocess, 5.2ms inference, 0.8ms postprocess per image at shape (1, 3, 416, 416)"
# inference 시간이 5-10ms면 GPU, 50-100ms면 CPU
```

---

## 📋 최적화 체크리스트

### Jetson #1
- [x] PyTorch CUDA 설치 확인
- [ ] YOLO 모델 GPU 이동 (`model.to('cuda')`)
- [ ] predict 호출 시 `device='cuda'` 추가
- [ ] jtop으로 GPU 사용률 확인
- [ ] CPU 사용률 측정 (목표: <50%)
- [ ] FPS 측정 (목표: 30 FPS)

### Jetson #2
- [x] PyTorch CUDA 설치 확인
- [x] YOLO 모델 GPU 이동
- [x] predict 호출 시 `device='cuda'` 추가
- [x] CPU 최적화 (해상도, frame skip, YOLO 입력 크기)
- [ ] 실제 환경 테스트 (모델 학습 후)
- [ ] 최종 CPU/GPU 사용률 측정

---

## 🚀 우선순위 작업

### 즉시 작업 (Jetson #1)
1. **YOLO GPU 강제 사용** 코드 수정
2. jtop으로 GPU 사용률 확인
3. CPU 사용률 측정

### 다음 단계 (Jetson #2)
1. 튀김 AI 모델 파라미터 조정
2. 바켓 감지 모델 학습 및 배포
3. 실제 환경 테스트

---

## 💡 성능 최적화 팁

### YOLO 최적화
```python
# 1. 모델 크기 선택
model = YOLO('yolov8n.pt')   # Nano - 가장 빠름 (추천)
model = YOLO('yolov8s.pt')   # Small
model = YOLO('yolov8m.pt')   # Medium - Jetson에는 무거움

# 2. 입력 크기 최적화
results = model.predict(frame, imgsz=416)  # Jetson #1 현재
results = model.predict(frame, imgsz=512)  # Jetson #2 현재
# 작을수록 빠름: 320, 416, 512, 640

# 3. Confidence threshold
results = model.predict(frame, conf=0.5)   # 기본값
results = model.predict(frame, conf=0.7)   # 높이면 false positive 감소

# 4. Half precision (FP16) - 2배 빠름
model.predict(frame, half=True, device='cuda')
```

### 카메라 최적화
```python
# 해상도 낮추기
# Jetson #1: 640x360 (현재)
# Jetson #2: 1280x720 (최적화 후)

# Frame skip 증가
if frame_count % FRAME_SKIP == 0:  # 매 N 프레임만 처리
    results = model.predict(frame)
```

---

## 📝 테스트 스크립트

### GPU 사용 확인 스크립트
```bash
#!/bin/bash
# test_gpu_usage.sh

echo "=== Jetson #1 GPU 테스트 ==="
cd ~/jetson-camera-monitor/jetson1_monitoring

python3 << EOF
import torch
from ultralytics import YOLO

print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    model = YOLO('yolo11n.pt')
    model.to('cuda')
    print(f"Model device: {next(model.parameters()).device}")
    print("✅ GPU 사용 준비 완료!")
else:
    print("❌ CUDA 사용 불가")
EOF

echo ""
echo "=== Jetson #2 GPU 테스트 ==="
cd ~/jetson-camera-monitor/jetson2_frying_ai

python3 << EOF
import torch
from ultralytics import YOLO

print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print("✅ GPU 사용 가능!")
else:
    print("❌ CUDA 사용 불가")
EOF
```

**실행**:
```bash
chmod +x test_gpu_usage.sh
./test_gpu_usage.sh
```

---

## 🎯 최종 목표

### Jetson #1
- **CPU 사용률**: <50% (현재: 80-100%?)
- **GPU 사용률**: 30-50%
- **FPS**: 30 FPS 안정적

### Jetson #2
- **CPU 사용률**: ~30% (AI 미실행 시 현재: 340%)
- **GPU 사용률**: 50-70% (YOLO 실행 시)
- **FPS**: 15 FPS 안정적 (4개 카메라)

---

## 📞 다음 작업

1. **Jetson #1 GPU 최적화 적용** (코드 수정 필요)
2. **실제 성능 측정** (jtop 모니터링)
3. **문서화** (성능 비교표 작성)

**Jetson #1 GPU 최적화 코드를 지금 적용할까요?**
