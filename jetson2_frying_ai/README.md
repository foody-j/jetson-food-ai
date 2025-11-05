# Jetson #2 - 튀김 AI 및 바켓 감지

GMSL 카메라 4대를 사용한 실시간 튀김 상태 AI 분석 및 바켓 감지 시스템

---

## 📖 시작하기

### 처음 사용하는 경우
**상위 디렉토리의 `배포가이드.md`를 먼저 읽으세요!**

```bash
cd ~/jetson-camera-monitor
cat 배포가이드.md
```

### 이미 설치된 경우
```bash
cd ~/jetson-camera-monitor/jetson2_frying_ai
python3 JETSON2_INTEGRATED.py
```

---

## 🎯 주요 기능

### 1. 튀김 AI (카메라 0, 1)
- **튀김유 색상 Segmentation** (HSV 기반)
- **실시간 특징 추출**:
  - Brown ratio: 갈색 비율 (익음 정도)
  - Golden ratio: 황금색 비율 (완벽한 튀김)
  - Food area: 음식 영역 비율
- **MQTT 온도 수신**: 튀김유 온도 실시간 표시
- **GPU 가속**: 백그라운드 처리 + frame skip

### 2. 바켓 감지 (카메라 2, 3)
- **YOLO Segmentation** (GPU 가속)
- **Empty/Filled 분류**
- **다수결 투표** (7프레임) 안정화
- **MQTT 상태 전송**: 바켓 상태 변화 알림

### 3. 데이터 수집 (수동 모드)
- **수집 간격**: 5초 (설정 가능)
- **저장 위치**: `~/AI_Data/FryingData/`, `~/AI_Data/BucketData/`
- **세션 관리**: 시작/종료 시간 자동 기록

---

## ⚙️ 설정 파일

### config_jetson2.json

```json
{
  "frying_left_camera_index": 0,
  "frying_right_camera_index": 1,
  "observe_left_camera_index": 2,
  "observe_right_camera_index": 3,

  "mqtt_enabled": false,
  "mqtt_broker": "localhost",
  "mqtt_port": 1883,

  "data_collection_interval": 5
}
```

---

## 📂 데이터 저장 위치

### 튀김 AI 데이터
```
~/AI_Data/FryingData/
└── session_YYYYMMDD_HHMMSS/
    ├── camera_0/
    │   ├── cam0_HHMMSS_mmm.jpg
    │   └── ...
    ├── camera_1/
    │   └── ...
    └── session_info.json
```

### 바켓 감지 데이터
```
~/AI_Data/BucketData/
└── session_YYYYMMDD_HHMMSS/
    ├── camera_2/
    ├── camera_3/
    └── session_info.json
```

---

## 🎮 사용법

### GUI 버튼
- **PC 상태**: CPU/GPU/메모리/디스크/온도
- **데이터 수집 시작**: 튀김 AI 데이터 수집 시작
- **데이터 수집 종료**: 수집 종료 및 세션 저장
- **종료**: 프로그램 종료

### 키보드 단축키
- **F11**: Fullscreen 토글
- **ESC**: Fullscreen 종료

---

## 📡 MQTT 통신

### 구독 (Subscribe)
- `frying/oil_temp/left`: 왼쪽 튀김유 온도
- `frying/oil_temp/right`: 오른쪽 튀김유 온도

### 발행 (Publish)
- `observe/status`: 바켓 상태 변화
  - 예: `LEFT:FILLED`, `RIGHT:EMPTY`, `LEFT:NO_BASKET`

---

## 🔧 문제 해결

### GPU가 사용되지 않음
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
# True가 나와야 함
```

### 카메라가 안 보임
```bash
ls -l /dev/video*
# video0, video1, video2, video3이 있어야 함
```

### 모델 파일 오류
```bash
ls -la ../observe_add/besta.pt
ls -la ../observe_add/bestb.pt
```

### 성능이 느림
```bash
sudo nvpmodel -q
# MAXN_SUPER (2) 모드 확인
cd ~/jetson-camera-monitor
./set_maxn_mode.sh
```

---

## 📚 추가 문서

| 문서 | 설명 |
|------|------|
| **DATA_COLLECTION_GUIDE_UPDATED.md** | 데이터 수집 상세 가이드 |
| `_archive/` | 이전 버전 문서 (참고용) |

---

## 💡 팁

1. **데이터 수집 확인**
   ```bash
   ls -lh ~/AI_Data/FryingData/
   ```

2. **세션 정보 확인**
   ```bash
   cat ~/AI_Data/FryingData/session_*/session_info.json
   ```

3. **프로그램 중지**
   - GUI에서 ESC 또는 '종료' 버튼
   - 또는 `Ctrl+C`

---

**문의**: GitHub Issues
