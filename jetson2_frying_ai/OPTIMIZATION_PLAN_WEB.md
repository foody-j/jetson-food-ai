# Jetson2 웹버전 YOLOv7 최적화 플랜

**대상 시스템**: Jetson Orin Nano 8GB
**대상 파일**: `JETSON2_web.py`
**카메라**: GMSL 4대 (1920x1536 @ 30fps)
**작성일**: 2026-02-15
**참고**: 교수님 솔루션 (YOLOv7 4채널 최적화 가이드)

---

## 📊 현재 시스템 분석

### 사용 중인 AI 모델 (YOLO11 기반)

| 모델 | 용도 | 크기 | Task | 입력 해상도 |
|-----|------|------|------|------------|
| `frying_seg_v3.pt` | 튀김 segmentation | 6.5MB | segment | 800×544 |
| `observe_ai/best_io_l.pt` | 바켓 segmentation (좌) | 6.5MB | segment | 480 |
| `observe_ai/best_io_r.pt` | 바켓 segmentation (우) | 6.5MB | segment | 480 |
| `observe_ai/best_fe_l.pt` | 바켓 classification (좌) | 2.8MB | classify | 160 |
| `observe_ai/best_fe_r.pt` | 바켓 classification (우) | 2.8MB | classify | 160 |

### 현재 설정 (config_jetson2_web.json)

```
카메라: 1920×1536 @ 30fps × 4대
튀김 AI: 800×544 @ 2 FPS
바켓 AI: 480 seg / 160 cls @ 1 FPS
웹 프리뷰: 480px @ 1 FPS, JPEG 40%
```

### 시스템 리소스

```
RAM: 7.4GB (4GB 사용중, 3GB 가용)
GPU: Orin integrated (CUDA 12.6)
Swap: 3.7GB
```

---

## 🎯 교수님 솔루션 적용 방안

### 핵심 권장사항 요약

1. **인풋 사이즈**: 320×320 또는 416×416
2. **TensorRT 변환**: FP16 Half Precision
3. **YOLOv7-Tiny 모델**: 경량 모델 사용 (이미 6.5MB 소형 모델 사용 중 ✅)
4. **DeepStream SDK**: GStreamer 파이프라인 최적화
5. **MAXN 모드**: nvpmodel -m 0

---

## 🔧 최적화 단계별 플랜

### Phase 1: 즉시 적용 (설정 변경만)

#### 1-1. 인풋 사이즈 축소

**현재 → 권장**

| 모델 | 현재 | 권장 | 메모리 절감 |
|-----|------|------|------------|
| frying_seg | 800×544 | **416×416** | **65%↓** |
| observe_seg | 480 | **320×320** | **56%↓** |
| observe_cls | 160 | 160 (유지) | - |

```json
{
  "frying_seg_imgsz": 416,
  "observe_img_size_seg": 320,
  "observe_img_size_cls": 160
}
```

**예상 FPS 향상**: 기존 대비 **1.5~2배**

#### 1-2. 카메라 FPS 조정

```json
{
  "camera_fps": 15
}
```

- 처리 부하 **50% 감소**
- 튀김/바켓은 느린 변화 → 15fps로 충분

#### 1-3. MAXN 전원 모드 확인

```bash
sudo nvpmodel -m 0
sudo jetson_clocks
```

---

### Phase 2: TensorRT 변환 (가장 중요!)

#### 2-1. 튀김 Segmentation 모델

```bash
cd ~/jetson-food-ai/jetson2_frying_ai

# FP16 Half Precision으로 TensorRT 변환
yolo export model=frying_seg_v3.pt format=engine device=0 half=True imgsz=416
```

결과: `frying_seg_v3.engine` (2~3배 빠름)

#### 2-2. 바켓 Segmentation 모델

```bash
# 좌측
yolo export model=observe_ai/pt_left_final/best_io_l.pt format=engine device=0 half=True imgsz=320

# 우측
yolo export model=observe_ai/pt_right_final/best_io_r.pt format=engine device=0 half=True imgsz=320
```

#### 2-3. 바켓 Classification 모델

```bash
# 좌측
yolo export model=observe_ai/pt_left_final/best_fe_l.pt format=engine device=0 half=True imgsz=160

# 우측
yolo export model=observe_ai/pt_right_final/best_fe_r.pt format=engine device=0 half=True imgsz=160
```

#### 2-4. 설정 파일 수정

```json
{
  "frying_seg_model": "frying_seg_v3.engine",
  "observe_left_seg_model": "observe_ai/pt_left_final/best_io_l.engine",
  "observe_right_seg_model": "observe_ai/pt_right_final/best_io_r.engine",
  "observe_left_cls_model": "observe_ai/pt_left_final/best_fe_l.engine",
  "observe_right_cls_model": "observe_ai/pt_right_final/best_fe_r.engine"
}
```

---

### Phase 3: 코드 최적화

#### 3-1. 배치 추론 구현 (두 POT 동시 처리)

```python
# 기존: POT1 추론 → POT2 추론 (순차)
# 변경: [POT1, POT2] 배치 추론 (1회 GPU 호출)

frames = [frame_pot1, frame_pot2]
results = model.predict(frames, imgsz=416, conf=0.05, device=0)
```

**GPU 효율 2배 향상**

#### 3-2. 프레임 복사 최소화

현재: 프레임당 3~4회 복사 (35MB/frame)

```python
# 변경: 참조 전달 + 필요시에만 복사
def get_frame_ref(self):
    return self.latest_frame, self.lock  # 복사 없음
```

#### 3-3. CUDA 스트림 분리

```python
# Segmentation과 Classification 병렬 실행
self.stream_seg = torch.cuda.Stream()
self.stream_cls = torch.cuda.Stream()
```

---

### Phase 4: GStreamer/DeepStream 최적화 (장기)

#### 4-1. DeepStream 파이프라인

DeepStream SDK 활용 시:
- 카메라 입력 → 디코딩 → 전처리 → 추론 → 렌더링
- **전체 GPU 파이프라인** (CPU 병목 제거)

```
[GMSL 카메라] → [HW Decoder] → [GPU Preprocess] → [TensorRT Infer] → [Overlay]
```

#### 4-2. 현재 GStreamer 개선

```bash
# 버퍼 최적화 파라미터 추가
... ! nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! appsink max-buffers=2 drop=true
```

---

## 📋 실행 순서 (체크리스트)

### 오늘 (즉시 적용)

- [ ] 1. MAXN 모드 확인: `sudo nvpmodel -q`
- [ ] 2. jetson_clocks 활성화: `sudo jetson_clocks`
- [ ] 3. config_jetson2_web.json 수정:
  ```json
  {
    "camera_fps": 15,
    "frying_seg_imgsz": 416,
    "observe_img_size_seg": 320
  }
  ```
- [ ] 4. 서비스 재시작 및 테스트

### 내일 (TensorRT 변환)

- [ ] 5. frying_seg_v3.pt → .engine 변환
- [ ] 6. observe 모델들 → .engine 변환
- [ ] 7. config에 .engine 경로 설정
- [ ] 8. 성능 테스트 (FPS 측정)

### 이번 주 (코드 수정)

- [ ] 9. 배치 추론 구현 (JETSON2_web.py)
- [ ] 10. 프레임 복사 최소화
- [ ] 11. 메모리 프로파일링

---

## 📊 예상 성능 비교

### 현재 vs 최적화 후

| 설정 | 인풋 사이즈 | 모델 포맷 | 예상 FPS (채널당) |
|-----|-----------|----------|------------------|
| **현재** | 800×544 | PyTorch (.pt) | ~2-3 FPS |
| **Phase 1** | 416×416 | PyTorch (.pt) | ~5-7 FPS |
| **Phase 2** | 416×416 | TensorRT (.engine) | **10-15 FPS** |
| **Phase 3** | 416×416 | TensorRT + 배치 | **15-20 FPS** |

### 리소스 사용

| 항목 | 현재 | 최적화 후 | 개선 |
|-----|------|----------|-----|
| GPU 메모리 | ~2GB | ~1GB | **50%↓** |
| CPU 사용률 | 70-90% | 40-50% | **30%↓** |
| 추론 지연 | ~200ms | ~50ms | **75%↓** |
| 카메라 안정성 | 가끔 뻗음 | 안정 | **✓** |

---

## ⚠️ 주의사항

### 1. TensorRT 변환 주의

```bash
# 변환 전 백업
cp frying_seg_v3.pt frying_seg_v3.pt.backup

# 변환 실패 시 원본 .pt 파일로 롤백
```

### 2. 인풋 사이즈 변경 시 정확도 테스트

- 416×416로 줄이면 작은 객체 탐지 성능 저하 가능
- 튀김 상태 분류에는 큰 영향 없을 것으로 예상 (POT 전체 촬영)
- **테스트 필수**: 기존 프레임으로 inference 비교

### 3. TensorRT 버전 호환성

```bash
# Jetson의 TensorRT 버전 확인
dpkg -l | grep tensorrt

# ultralytics와 호환 확인
python3 -c "from ultralytics import YOLO; print('OK')"
```

### 4. GMSL 카메라 해상도 제약

```bash
# 지원 해상도 확인
v4l2-ctl --device=/dev/video0 --list-formats-ext

# 카메라 해상도는 변경 어려울 수 있음
# → AI 입력 전에 resize로 해결
```

---

## 🔗 참고 자료

- [NVIDIA DeepStream SDK](https://developer.nvidia.com/deepstream-sdk)
- [Ultralytics TensorRT Export](https://docs.ultralytics.com/modes/export/#tensorrt)
- [Jetson Orin Nano 성능 튜닝](https://developer.nvidia.com/embedded/jetson-orin-nano-developer-kit)

---

*생성: Claude Code (2026-02-15)*
*참고: 교수님 YOLOv7 4채널 최적화 가이드*
