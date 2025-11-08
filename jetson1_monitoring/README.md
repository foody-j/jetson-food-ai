# Jetson #1 - 사람 감지 및 볶음 모니터링

GMSL 카메라 3대를 사용한 실시간 사람 감지 및 볶음 과정 모니터링 시스템

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
cd ~/jetson-camera-monitor/jetson1_monitoring
python3 JETSON1_INTEGRATED.py
```

---

## 🎯 주요 기능

1. **사람 감지 (카메라 0)**
   - YOLO GPU 가속 (PyTorch CUDA)
   - 주야간 자동 전환 (07:30~19:00)
   - 감지 시 스냅샷 저장: `~/Detection/`

2. **볶음 모니터링 (카메라 1, 2)**
   - 볶음 좌/우 실시간 모니터링
   - 수동 시작/종료 버튼
   - 데이터 저장: `~/StirFry_Data/left/`, `~/StirFry_Data/right/`

3. **MQTT 통신**
   - 로봇 제어 메시지 전송 (선택)
   - 설정: `config.json`의 `mqtt_enabled`

---

## ⚙️ 설정 파일

### config.json

주요 설정:
```json
{
  "mode": "auto",                    // auto 또는 manual
  "day_start": "07:30",              // 주간 모드 시작 시각
  "day_end": "19:00",                // 주간 모드 종료 시각
  "camera_index": 2,                 // 사람 감지 카메라 (GMSL #2)
  "yolo_model": "yolo12n.pt",        // YOLO 모델
  "yolo_confidence": 0.7,            // 감지 신뢰도
  "snapshot_dir": "~/Detection",     // 스냅샷 저장 경로
  "stirfry_save_dir": "~/StirFry_Data",  // 볶음 데이터 경로
  "mqtt_enabled": false              // MQTT 활성화 여부
}
```

---

## 📂 데이터 저장 위치

**자세한 정보**: `../docs/DATA_STORAGE_MAP.md` 참고

### 사람 감지 스냅샷
```
~/Detection/
└── YYYYMMDD/
    ├── HHMMSS.jpg
    ├── HHMMSS.jpg
    └── ...
```

### 볶음 모니터링 데이터
```
~/StirFry_Data/
├── left/
│   └── YYYYMMDD_HHMMSS/
│       ├── 001.jpg
│       ├── 002.jpg
│       └── ...
└── right/
    └── YYYYMMDD_HHMMSS/
        ├── 001.jpg
        ├── 002.jpg
        └── ...
```

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
# video0, video1, video2가 있어야 함

# 카메라 드라이버 수동 로드
cd ~/jetson-camera-monitor/jetson1_monitoring/camera_autostart
sudo ./camera_driver_autoload.sh

# 카메라 드라이버 서비스 확인
sudo systemctl status sensing-camera.service
sudo journalctl -u sensing-camera.service -f
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
| **JETSON1_GUIDE.md** | 상세 설정 및 사용 가이드 |
| `_archive/` | 이전 버전 문서 (참고용) |

---

## 💡 팁

1. **자동 시작 설정**
   ```bash
   cd ~/jetson-camera-monitor/jetson1_monitoring
   ./install_autostart.sh
   ```

   이 스크립트는 다음을 자동으로 설정합니다:
   - GMSL 카메라 드라이버 자동 로드 (`sensing-camera.service`)
   - 모니터링 시스템 자동 시작 (`jetson-monitor.service`)
   - v4l-utils 설치 확인

2. **로그 확인**
   ```bash
   # 모니터링 시스템 로그
   sudo journalctl -u jetson-monitor.service -f

   # 카메라 드라이버 로그
   sudo journalctl -u sensing-camera.service -f
   ```

3. **프로그램 중지**
   - GUI에서 ESC 또는 'q' 키
   - 또는 `Ctrl+C`

4. **카메라 드라이버 설정**
   - 카메라 드라이버는 부팅 시 자동 로드됩니다
   - 설정 파일: `camera_autostart/camera_driver_autoload.sh`
   - 해상도, 카메라 타입 등 수정 가능
   - README: `camera_autostart/README.md`

5. **폰트 설정**
   - GUI는 **Noto Sans CJK KR** 폰트 사용
   - 폰트 미설치 시 `install_korean_fonts.sh` 실행

---

**문의**: GitHub Issues
