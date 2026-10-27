# Jetson2 최적화 플랜

**대상 시스템**: Jetson Orin Nano 8GB
**대상 파일**: `JETSON2_web.py` (Headless + FastAPI 버전)
**문제**: 카메라 뻗음, 전체적인 안정성/성능 이슈
**분석일**: 2026-02-06

---

## 🔴 현재 문제점 분석

### 1. 메모리 부족 (8GB 한계)

| 구성요소 | 예상 메모리 |
|---------|-----------|
| 카메라 4대 (1920x1536x3) | ~35MB/대 × 4 = **140MB** |
| YOLO 모델 4개 (seg×2, cls×2) | ~500MB~1GB |
| AI inference 버퍼 | ~200MB |
| 웹 스트림 버퍼 | ~50MB |
| GStreamer 버퍼 | ~200MB |
| **총계** | **~2GB+** (CUDA 메모리 별도) |

**문제**: CUDA 통합 메모리에서 시스템/GPU 경쟁으로 OOM 발생 가능

### 2. GStreamer 카메라 안정성 (gst_camera.py)

```python
# 현재 문제점
- subprocess로 gst-launch 실행 → 제어 어려움
- pipe 버퍼 overflow 시 무한 대기 가능
- select() 타임아웃이 0.1초로 짧음
- 카메라 복구(recover) 시 v4l2 장치 완전 해제 안됨
- 버퍼 크기 제한 없음 → 메모리 누수 가능
```

### 3. 스레드 과다 생성

| 스레드 | 개수 |
|-------|-----|
| CameraWorker | 4 |
| FryingAIWorker | 2 |
| ObserveAIWorker | 2 |
| collection_loop | 1 |
| camera_watchdog | 1 |
| uvicorn (web) | 1+ |
| MQTT | 1 |
| **총계** | **12+개** |

→ 8코어 Orin Nano에서 컨텍스트 스위칭 오버헤드 발생

### 4. 프레임 복사 과다

```python
# 매 프레임마다 복사 발생하는 위치
self.latest_frame = frame.copy()           # gst_camera._read_frames (L:154)
return True, self.latest_frame.copy()      # gst_camera.read (L:171)
self.latest_frame = frame.copy()           # CameraWorker.run (L:281)
return self.latest_frame.copy()            # CameraWorker.get_latest_frame (L:408)
frame.copy()                               # FryingAIWorker._update_snapshot (L:593)
frame.copy()                               # ObserveAIWorker._update_snapshot (L:896)
```

**한 프레임당 최소 3-4회 복사** → 1920×1536×3 = 8.8MB × 4회 = **~35MB/frame**

### 5. AI 추론 비효율

- 튀김 AI: 매번 개별 추론 (배치 없음)
- Observe AI: seg 후 cls 순차 실행 (GPU 유휴 시간)
- 동일 프레임을 web preview, AI, snapshot에서 중복 처리

### 6. 웹 스트리밍 부하

```python
# CameraWorker._update_web_frame (L:361-380)
- 매번 resize → imencode 실행
- 4개 카메라 × 5 FPS = 20회/초 JPEG 압축
```

---

## 🟢 최적화 방안

### Phase 1: 즉시 적용 가능 (설정 변경만)

#### 1-1. 해상도/FPS 조정 (메모리 44% 절감)

```json
{
  "camera_width": 1280,        // 1920 → 1280
  "camera_height": 1024,       // 1536 → 1024
  "camera_fps": 15,            // 30 → 15 (처리 부하 50% 감소)
}
```

**주의**: GMSL 카메라 드라이버가 지원하는 해상도 확인 필요
- 지원 안되면 카메라 해상도는 유지하고 AI/저장만 다운스케일

#### 1-2. AI FPS 조정

```json
{
  "frying_infer_fps": 2,       // 5 → 2 (튀김은 느린 변화)
  "observe_infer_fps": 1,      // 2 → 1 (바켓 상태 느림)
  "frying_log_interval_sec": 10 // 5 → 10
}
```

#### 1-3. AI 모델 크기 조정

```json
{
  "frying_seg_imgsz": 480,     // [800,544] → 480
  "observe_img_size_seg": 480, // 640 → 480
  "observe_img_size_cls": 160  // 224 → 160
}
```

#### 1-4. 웹 프리뷰 최적화

```json
{
  "web_preview_fps": 2,        // 5 → 2
  "web_preview_width": 480,    // 640 → 480
  "web_preview_quality": 50,   // 70 → 50
  "overlay_fps": 0.5           // 3 → 0.5 (2초에 1회)
}
```

#### 1-5. 카메라 선택적 비활성화 (최후 수단)

```json
{
  "observe_left_enabled": false,   // 한쪽만 사용
  // 또는
  "frying_right_enabled": false
}
```

---

### Phase 2: 코드 수정 (중간 난이도)

#### 2-1. GStreamer 안정화 (gst_camera.py)

```python
class GstCamera:
    def __init__(self, ...):
        self.MAX_BUFFER_SIZE = self.frame_size * 3  # 버퍼 제한
        self.STALL_TIMEOUT = 5.0  # 스톨 감지 타임아웃

    def _read_frames(self):
        buffer = b''
        last_frame_time = time.time()

        while self.is_running and self.process and self.process.poll() is None:
            # 타임아웃 늘림 (0.1 → 0.5초)
            readable, _, _ = select.select([self.process.stdout], [], [], 0.5)

            if not readable:
                # 스톨 감지
                if time.time() - last_frame_time > self.STALL_TIMEOUT:
                    print(f"[GstCamera] Stall detected ({self.STALL_TIMEOUT}s)")
                    break
                continue

            try:
                chunk = self.process.stdout.read(self.frame_size)
                if chunk:
                    buffer += chunk
                    last_frame_time = time.time()
            except BlockingIOError:
                continue

            # 버퍼 크기 제한 (메모리 누수 방지)
            if len(buffer) > self.MAX_BUFFER_SIZE:
                # 오래된 불완전 프레임 버림
                buffer = buffer[-self.frame_size:]

            # ... 나머지 동일
```

#### 2-2. 프레임 복사 최소화

```python
class CameraWorker(threading.Thread):
    def run(self):
        while self.running:
            # ...
            ret, frame = self.camera.read()
            # ...

            # 한 번만 복사, 참조로 전달
            with self.latest_frame_lock:
                self.latest_frame = frame  # copy() 제거

            # web frame도 같은 프레임 사용
            self._update_web_frame(frame)  # 복사 없이 참조

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """복사 필요시에만"""
        with self.latest_frame_lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy()  # 여기서만 복사

    def get_frame_ref(self) -> Tuple[Optional[np.ndarray], threading.Lock]:
        """참조 반환 (AI용 - 복사 없음)"""
        return self.latest_frame, self.latest_frame_lock
```

#### 2-3. AI 워커 프레임 큐 개선

```python
class FryingAIWorker(threading.Thread):
    def run(self):
        while self.running:
            # 프레임 큐 대신 직접 참조
            frame, lock = self.camera.get_frame_ref()
            if frame is None:
                time.sleep(0.01)
                continue

            with lock:
                # lock 내에서 처리 (복사 없이)
                seg_result = self.segmenter.segment(frame)

            # ... 나머지 처리
```

#### 2-4. 카메라 Watchdog 개선

```python
def _camera_watchdog_loop(self) -> None:
    # ...
    while not self.camera_watchdog_stop.is_set():
        now = time.time()

        for cam_id, cam in self.cameras.items():
            if cam is None or not cam.running:
                continue

            last_ts = cam.stats.get("last_frame_ts", 0) or 0
            if last_ts == 0:
                continue

            stall_time = now - last_ts
            if stall_time > stall_sec and not cam.is_recovering():
                self.camera_fail_counts[cam_id] = self.camera_fail_counts.get(cam_id, 0) + 1
                print(f"[CAM{cam_id}] Stall ({stall_time:.1f}s), count={self.camera_fail_counts[cam_id]}")

                # V4L2 강제 해제 추가
                if self.camera_fail_counts[cam_id] >= 2:
                    self._force_release_v4l2(f"/dev/video{cam.cam_index}")

                cam.request_recover()

        time.sleep(check_interval)

def _force_release_v4l2(self, device_path: str):
    """V4L2 장치 강제 해제"""
    try:
        subprocess.run(["fuser", "-k", device_path],
                      capture_output=True, timeout=3)
        time.sleep(0.5)
    except Exception as e:
        print(f"[V4L2] Force release failed: {e}")
```

---

### Phase 3: 구조적 개선 (장기)

#### 3-1. AI 배치 추론 (두 POT 동시 처리)

```python
class FryingAIBatchWorker(threading.Thread):
    """POT1 + POT2를 배치로 처리하여 GPU 효율 향상"""

    def run(self):
        while self.running:
            frames = []
            cam_ids = []

            for cam_id in [0, 1]:
                cam = self.cameras.get(cam_id)
                if cam:
                    frame = cam.get_latest_frame()
                    if frame is not None:
                        frames.append(frame)
                        cam_ids.append(cam_id)

            if not frames:
                time.sleep(0.05)
                continue

            # 배치 추론 (1회 GPU 호출로 2개 처리)
            results = self.segmenter.model.predict(
                frames,
                imgsz=self.imgsz,
                conf=self.conf,
                verbose=False,
                device=self.device
            )

            for i, result in enumerate(results):
                self._process_result(cam_ids[i], frames[i], result)
```

#### 3-2. CUDA 스트림 분리 (Observe AI)

```python
class ObserveAIWorker(threading.Thread):
    def __init__(self, ...):
        # ...
        if torch.cuda.is_available():
            self.stream_seg = torch.cuda.Stream()
            self.stream_cls = torch.cuda.Stream()

    def _infer_async(self, frame):
        # Segmentation
        with torch.cuda.stream(self.stream_seg):
            seg_result = self.seg_model.predict(frame, ...)

        self.stream_seg.synchronize()

        # Classification (seg 결과 기반)
        if has_detection:
            with torch.cuda.stream(self.stream_cls):
                cls_result = self.cls_model.predict(cropped, ...)
```

#### 3-3. TensorRT 변환

```bash
# YOLO 모델을 TensorRT로 변환 (2-3배 빠름)
yolo export model=frying_seg_v3.pt format=engine device=0 half=True imgsz=480

# config에서 사용
"frying_seg_model": "frying_seg_v3.engine"
```

---

## 📋 우선순위 실행 계획

### 즉시 (오늘) - 설정만 변경
1. ✅ config_jetson2_web.json 최적화 설정 적용
2. ✅ observe 카메라 한 쪽 비활성화 테스트

### 단기 (1-2일) - 코드 수정
3. gst_camera.py 버퍼/타임아웃 개선
4. 프레임 복사 최소화
5. V4L2 강제 해제 로직 추가

### 중기 (1주)
6. AI 배치 추론 구현
7. TensorRT 모델 변환
8. 메모리 프로파일링 및 튜닝

### 장기 (필요시)
9. 프로세스 분리 (카메라/AI/저장)
10. Jetson AGX Orin 업그레이드 고려

---

## 🔧 권장 즉시 적용 설정

```json
{
  "// === 카메라 최적화 ===": "",
  "camera_fps": 15,
  "camera_stall_sec": 5,
  "camera_watch_interval_sec": 2.0,
  "gmsl_reinit_after_failures": 1,

  "// === AI 최적화 ===": "",
  "frying_infer_fps": 2,
  "frying_seg_imgsz": 480,
  "frying_log_interval_sec": 10,
  "observe_infer_fps": 1,
  "observe_img_size_seg": 480,
  "observe_img_size_cls": 160,

  "// === 웹 최적화 ===": "",
  "web_preview_fps": 2,
  "web_preview_width": 480,
  "web_preview_quality": 50,
  "overlay_fps": 1,

  "// === 저장 최적화 ===": "",
  "jpeg_quality": 85,
  "data_collection_interval_normal": 2,

  "// === 선택적 비활성화 ===": "",
  "observe_left_enabled": false
}
```

---

## 📊 예상 효과

| 항목 | 현재 | 최적화 후 | 개선 |
|-----|------|----------|-----|
| 메모리 사용 | ~2GB+ | ~1.2GB | **40%↓** |
| CPU 사용률 | 70-90% | 40-60% | **30%↓** |
| GPU 메모리 | ~3GB | ~2GB | **33%↓** |
| 카메라 안정성 | 자주 뻗음 | 안정 | **✓** |
| AI 지연시간 | ~200ms | ~150ms | **25%↓** |

---

## ⚠️ 주의사항

1. **카메라 해상도 변경**: GMSL 드라이버가 지원하는 해상도인지 확인
   ```bash
   v4l2-ctl --device=/dev/video0 --list-formats-ext
   ```

2. **AI 정확도**: 모델 입력 크기 줄이면 정확도 영향 가능 → 테스트 필수

3. **테스트 순서**: 설정 변경 → 카메라 안정성 확인 → AI 최적화 순서

4. **롤백 준비**: 원본 config 백업 후 진행

---

*생성: Claude Code (2026-02-06)*
