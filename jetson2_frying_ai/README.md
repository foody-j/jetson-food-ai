# Jetson #2 - AI Monitoring System

**4-Camera AI 모니터링 시스템** (Jetson Orin Nano용)

---

## 📋 개요

### 🍤 Frying AI (튀김 AI)
- **카메라**: video0 (왼쪽), video1 (오른쪽)
- **GPU 가속**: 백그라운드 스레드 + frame skip으로 CPU 절약
- **기능**:
  - 튀김유 색상 segmentation (HSV 기반)
  - 실시간 색상 특징 추출
    - Brown ratio: 갈색 비율 (익음 정도)
    - Golden ratio: 황금색 비율 (완벽한 튀김)
    - Food area: 음식 영역 비율
  - MQTT로 튀김유 온도 수신 및 표시

### 🥘 Observe_add (바켓 감지)
- **카메라**: video2 (왼쪽), video3 (오른쪽)
- **GPU 가속**: YOLO 모델을 CUDA에서 실행 + frame skip (5프레임)
- **기능**:
  - 바켓 segmentation (YOLO)
  - Empty/Filled 분류
  - 다수결 투표 (7프레임) 안정화
  - 상태 변화 감지 → MQTT 전송

---

## 🚀 실행 방법

```bash
cd ~/jetson-camera-monitor/jetson2_ai
python3 JETSON2_INTEGRATED.py
```

---

## ⚙️ 설정 파일

### config_jetson2.json

```json
{
  "// Frying AI (video0, video1)": "",
  "frying_left_camera_index": 0,
  "frying_right_camera_index": 1,

  "// Observe_add (video2, video3)": "",
  "observe_left_camera_index": 2,
  "observe_right_camera_index": 3,
  "observe_seg_model": "../observe_add/besta.pt",
  "observe_cls_model": "../observe_add/bestb.pt",

  "// MQTT Settings": "",
  "mqtt_enabled": false,
  "mqtt_broker": "localhost",
  "mqtt_port": 1883,
  "mqtt_topic_oil_temp_left": "frying/oil_temp/left",
  "mqtt_topic_oil_temp_right": "frying/oil_temp/right"
}
```

---

## 🎮 사용법

### 상단 헤더 버튼
- **PC 상태**: CPU/GPU/메모리/디스크/온도 모니터링
- **진동 체크**: 진동 센서 상태 (향후 구현)
- **설정**: 설정 메뉴 (현재는 config.json 수정)

### 제어 버튼
- **튀김 AI 시작**: 튀김유 색상 분석 시작
- **튀김 AI 중지**: 분석 중지
- **바켓 감지 시작**: 바켓 empty/filled 감지 시작
- **바켓 감지 중지**: 감지 중지
- **종료**: 프로그램 종료

### 키보드 단축키
- **F11**: Fullscreen 토글
- **ESC**: Fullscreen 종료

---

## 📡 MQTT 통신

### 구독 (Subscribe)
튀김유 온도 수신:
- **Topic**: `frying/oil_temp/left`
  - Payload 예시: `170.5` (float)
- **Topic**: `frying/oil_temp/right`
  - Payload 예시: `172.3` (float)

### 발행 (Publish)
바켓 상태 전송:
- **Topic**: `observe/status`
  - Payload 예시:
    - `LEFT:FILLED` - 왼쪽 바켓에 음식 있음
    - `LEFT:EMPTY` - 왼쪽 바켓 비어있음
    - `LEFT:NO_BASKET` - 왼쪽 바켓 감지 안됨
    - `RIGHT:FILLED` - 오른쪽 바켓에 음식 있음
    - `RIGHT:EMPTY` - 오른쪽 바켓 비어있음
    - `RIGHT:NO_BASKET` - 오른쪽 바켓 감지 안됨

---

## 📁 파일 구조

```
jetson2_ai/
├── JETSON2_INTEGRATED.py    # 메인 프로그램
├── config_jetson2.json        # 설정 파일
├── gst_camera.py              # GStreamer 카메라 래퍼
├── frying_segmenter.py        # 튀김유 색상 segmentation
└── README.md                  # 이 파일
```

---

## 🔧 의존성

### Python 패키지
```bash
pip3 install ultralytics paho-mqtt Pillow numpy
```

### 시스템 패키지
```bash
sudo apt install python3-gi gstreamer1.0-tools v4l-utils
```

### GPU 가속 (선택사항 - 권장!)

**현재 상태**: CPU 모드로 실행 가능하지만, GPU를 사용하면 **3-5배 빠름**

Jetson에서 GPU 가속을 사용하려면 NVIDIA의 PyTorch가 필요합니다:

#### 1. 현재 PyTorch 확인
```bash
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

#### 2. CUDA 활성화된 PyTorch 설치 (JetPack 6.x)
```bash
# NVIDIA 제공 PyTorch 설치
pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://developer.download.nvidia.com/compute/redist/jp/v60
```

**참고**: JetPack 버전에 따라 URL이 다릅니다. 공식 문서 참조:
- https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048

#### 3. GPU 작동 확인
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
# True 나오면 성공!
```

### AI 모델
- Observe_add segmentation: `../observe_add/besta.pt`
- Observe_add classification: `../observe_add/bestb.pt`

---

## 📊 화면 구성

```
┌──────────────────────────────────────────────────────┐
│  시스템 정상  2025/11/05    현대자동차 울산점         │
│                           15:30:25                   │
│             [PC 상태] [진동 체크] [설정]              │
├──────────────────┬──────────────────────────────────┤
│  🍤 튀김 AI - 왼쪽 │  🍤 튀김 AI - 오른쪽             │
│  [카메라 영상]    │  [카메라 영상]                  │
│  온도: 170.5°C   │  온도: 172.3°C                  │
│  갈색: 45% 황금: 30% │  갈색: 52% 황금: 38%          │
├──────────────────┼──────────────────────────────────┤
│  🥘 바켓 감지 - 왼쪽 │  🥘 바켓 감지 - 오른쪽          │
│  [카메라 영상]    │  [카메라 영상]                  │
│  상태: FILLED    │  상태: EMPTY                    │
└──────────────────┴──────────────────────────────────┘
 [튀김 AI 시작] [튀김 AI 중지]
 [바켓 감지 시작] [바켓 감지 중지] [종료]
```

---

## ⚠️ 주의사항

1. **카메라 연결**: 4개의 GMSL 카메라가 video0~video3에 연결되어 있어야 함
2. **모델 파일**: observe_add 모델 파일이 상위 디렉토리에 있어야 함
3. **GMSL 드라이버**: 시스템 시작 시 자동 로드되어야 함
4. **MQTT**: 온도 데이터를 전송할 외부 시스템 필요 (선택사항)

---

## 🐛 문제 해결

### 카메라가 안 보임
```bash
# 카메라 디바이스 확인
ls -la /dev/video*

# GMSL 드라이버 확인
lsmod | grep gmsl
```

### 모델 파일 오류
```bash
# 모델 파일 경로 확인
ls -la ../observe_add/besta.pt
ls -la ../observe_add/bestb.pt
```

### MQTT 연결 실패
`config_jetson2.json`에서 `mqtt_enabled`를 `false`로 설정하면 MQTT 없이 실행 가능

---

## 📝 개발 노트

### 성능 최적화
- **GPU 가속**: YOLO 모델을 CUDA device에서 실행
- **Frame skip**:
  - 튀김 AI: 3프레임마다 처리 (CPU 절약)
  - 바켓 감지: 5프레임마다 처리 (YOLO는 무거움)
- **백그라운드 스레드**: AI 처리를 별도 스레드로 분리 → GUI 프리징 방지
- **결과 캐싱**: 이전 AI 결과 재사용으로 매 프레임 화면 업데이트

### UI/UX
- JETSON1과 동일한 WHITE MODE 테마
- 헤더 레이아웃: PC 상태, 진동 체크, 실시간 시계
- GStreamer 기반 UYVY 포맷 처리
- Fullscreen 지원 (F11/ESC)

---

## 📞 지원

문제 발생 시 로그 확인:
- 터미널 출력에서 `[카메라]`, `[모델]`, `[MQTT]` 태그 확인
- 에러 메시지 참고
