# 🔧 최근 수정 사항

**날짜**: 2025-01-05

---

## ✅ 완료된 작업

### 1. Jetson #1 GPU 가속 활성화 ⭐

**파일**: `jetson1_monitoring/JETSON1_INTEGRATED.py`

**변경 사항**:
- YOLO 모델에 GPU 가속 명시적 적용
- PyTorch CUDA 체크로 변경 (OpenCV CUDA 체크에서)
- 모든 predict 호출에 `device='cuda'` 추가

**예상 성능 향상**: YOLO 추론 속도 5배 향상

**수정된 라인**:
- Line 125-133: GPU 감지 메시지 수정 (PyTorch CUDA 체크)
- Line 186: `self.device` 초기화
- Line 766-784: `init_yolo()` - GPU 디바이스 설정
- Line 889: Day mode predict with device
- Line 948: Night mode predict with device

---

### 2. MAXN_SUPER 모드 스크립트 수정 ⭐

**문제**: 초기 스크립트가 mode 0 (15W)를 사용 → 성능 저하
**해결**: mode 2 (MAXN_SUPER)로 수정

**수정된 파일**:
1. `set_maxn_mode.sh` - 즉시 MAXN 모드 적용
2. `jetson-maxn.service` - 부팅 시 자동 MAXN 모드
3. `install_maxn_service.sh` - 서비스 설치 스크립트

**모드 번호**:
- Mode 0: 15W (저전력)
- Mode 1: 25W (기본값)
- Mode 2: MAXN_SUPER (최대 성능) ⭐

**사용 방법**:
```bash
# 즉시 적용
./set_maxn_mode.sh

# 부팅 시 자동 적용 (추천)
./install_maxn_service.sh
sudo reboot

# 현재 모드 확인
sudo nvpmodel -q
# 출력: "NV Power Mode: MAXN_SUPER" 및 "2" 확인
```

---

### 3. GPU 디버그 메시지 수정

**문제**: "[GPU] CUDA 미지원, CPU 모드로 실행" 메시지가 잘못 표시됨
- PyTorch CUDA는 사용 가능했지만 OpenCV CUDA를 체크하고 있었음

**해결**:
```python
# Before
if cv2.cuda.getCudaEnabledDeviceCount() > 0:
    print("[GPU] CUDA 사용 가능!")
else:
    print("[GPU] CUDA 미지원, CPU 모드로 실행")

# After
import torch
if torch.cuda.is_available():
    print(f"[GPU] PyTorch CUDA 사용 가능! YOLO GPU 가속 활성화 ({torch.cuda.get_device_name(0)})")
else:
    print("[GPU] PyTorch CUDA 미지원 - YOLO는 CPU 모드로 실행")
```

---

### 4. 문서화 작업

**새로 생성된 문서**:
1. `QUICK_SETUP.md` - 빠른 설정 가이드
   - jtop 설치 방법
   - MAXN 모드 설정
   - GPU 사용 확인 방법

2. `GPU_OPTIMIZATION_STATUS.md` - GPU 최적화 상태
   - Jetson #1, #2 GPU 사용 현황
   - 수정 전/후 비교
   - 성능 예상치

3. `jetson2_frying_ai/DATA_COLLECTION_GUIDE.md` - 데이터 수집 가이드
   - 튀김 AI 테스트 방법
   - 바켓 감지 모델 개발 절차
   - Roboflow 라벨링 가이드

4. `OPTIMIZATION_SUMMARY.md` - 전체 최적화 요약

5. `jetson2_frying_ai/data_collector.py` - 데이터 수집 도구 (독립 실행형)

---

## 🧪 테스트 필요

### 1. MAXN 모드 확인
```bash
sudo nvpmodel -q
```
**예상 출력**: `NV Power Mode: MAXN_SUPER` 및 `2`

### 2. Jetson #1 GPU 사용 확인
```bash
# 터미널 1: jtop 실행
sudo jtop
# '3' 키를 눌러 GPU 페이지로 이동

# 터미널 2: 프로그램 실행
cd ~/jetson-camera-monitor/jetson1_monitoring
python3 JETSON1_INTEGRATED.py
```

**예상 결과**:
- 프로그램 출력: `[GPU] PyTorch CUDA 사용 가능! YOLO GPU 가속 활성화 (Orin)`
- jtop GPU 페이지: GPU 사용률 30-50%

### 3. Jetson #2 CPU 사용 확인
```bash
# jtop으로 CPU 사용률 모니터링
sudo jtop
# '2' 키를 눌러 CPU 페이지로 이동

cd ~/jetson-camera-monitor/jetson2_frying_ai
python3 JETSON2_INTEGRATED.py
# GUI에서 "튀김 AI 시작" 클릭
```

**예상 결과**: CPU 사용률 30-40% (기존 80%에서 감소)

---

## 📋 대기 중인 작업

### 1. GUI 통합 데이터 수집 (최우선) ⭐

**요구사항**:
- MQTT 조리 시작 신호 → 자동 캡처 시작
- MQTT 조리 종료 신호 → 캡처 중지
- GUI 프로그램 실행 중 백그라운드 동작
- 수동 스페이스바 캡처 아님!

**구현 계획**:
1. `JETSON2_INTEGRATED.py`에 데이터 수집 상태 변수 추가
2. MQTT 구독: `stirfry/cooking/start`, `stirfry/cooking/end`
3. 조리 중일 때 주기적 프레임 캡처 (예: 5초마다)
4. 타임스탬프 세션 디렉토리에 저장

**파일**: `jetson2_frying_ai/JETSON2_INTEGRATED.py` 수정 필요

---

### 2. 실제 환경 모델 개발

**튀김 AI** (쉬움, 1-2일):
- 실제 환경에서 샘플 이미지 10-20장 수집
- HSV 범위 파라미터 조정
- 학습 불필요 (이미 구현됨)

**바켓 감지** (중간, 1-2주):
- 데이터 수집: 200-300장 (MQTT 자동 캡처 사용)
- Roboflow 라벨링
- YOLO 학습 (Colab 또는 Roboflow)
- 모델 배포: `besta.pt`, `bestb.pt`

---

## 💡 권장 다음 단계

### 우선순위 1: MAXN 모드 확인 및 적용
```bash
cd ~/jetson-camera-monitor
./set_maxn_mode.sh
# 또는 부팅 시 자동 적용
./install_maxn_service.sh
```

### 우선순위 2: jtop 설치 (아직 안 했다면)
```bash
sudo pip3 install -U jetson-stats
sudo reboot
```

### 우선순위 3: 성능 측정
- jtop으로 Jetson #1 GPU 사용 확인 (30-50% 예상)
- jtop으로 Jetson #2 CPU 사용 확인 (30-40% 예상)

### 우선순위 4: GUI 데이터 수집 구현
- MQTT 기반 자동 캡처 시스템 개발

---

## 🔍 기본값 (Default Values)

### Jetson #2 Config (`jetson2_frying_ai/config_jetson2.json`)
```json
{
  "camera_width": 640,           // 기본: 1280 → 640 (50% 감소)
  "camera_height": 480,          // 기본: 720 → 480 (67% 감소)
  "frying_frame_skip": 20,       // 기본: 10 → 20 (2배 감소)
  "observe_frame_skip": 30,      // 기본: 15 → 30 (2배 감소)
  "frying_imgsz": 256,           // 기본: 512 → 256 (50% 감소)
  "observe_imgsz": 256,          // 기본: 512 → 256 (50% 감소)
  "frying_conf": 0.5,
  "observe_conf_seg": 0.5,
  "observe_conf_cls": 0.6
}
```

### Jetson #1 YOLO 설정 (`jetson1_monitoring/JETSON1_INTEGRATED.py`)
```python
MODEL_PATH = "../add_model/yolo_v8_nano.pt"
YOLO_CONF = 0.3                  // Confidence threshold
YOLO_IMGSZ = 416                 // Input image size
```

### MAXN 모드
```bash
# 기본 부팅 모드: 25W (mode 1)
# 권장 모드: MAXN_SUPER (mode 2)
sudo nvpmodel -m 2
sudo jetson_clocks
```

---

## 📚 관련 문서

- **빠른 시작**: `QUICK_SETUP.md`
- **GPU 최적화**: `GPU_OPTIMIZATION_STATUS.md`
- **전체 요약**: `OPTIMIZATION_SUMMARY.md`
- **데이터 수집**: `jetson2_frying_ai/DATA_COLLECTION_GUIDE.md`
- **설치 가이드**: `jetson2_frying_ai/INSTALL_GUIDE.md`

---

**모든 수정 사항 완료! 테스트 준비 완료!** ✅
