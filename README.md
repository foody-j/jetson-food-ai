# 🤖 Jetson 카메라 모니터링 시스템

NVIDIA Jetson Orin Nano 기반 실시간 GMSL 카메라 모니터링 및 AI 분석 시스템

**버전**: 2.0  
**대상**: Jetson Orin Nano (JetPack 6.2)  
**업데이트**: 2025-01-05

---

## 📋 시스템 구성

### Jetson #1 - 사람 감지 및 볶음 모니터링
- **카메라**: 3대 (GMSL)
- **기능**: YOLO 사람 감지 (GPU 가속), 주야간 자동 전환, 볶음 모니터링, MQTT 전송

### Jetson #2 - 튀김 AI 및 바켓 감지
- **카메라**: 4대 (GMSL)
- **기능**: 튀김 상태 AI 분석, 바켓 감지, 데이터 수집, MQTT 통신

---

## 🚀 빠른 시작

### 1. 배포 가이드 읽기

```bash
cat 배포가이드.md
```

**이 문서 하나만 읽으면 배포 완료!**

### 2. 의존성 설치

```bash
cd ~/jetson-camera-monitor
./install.sh
```

### 3. 프로그램 실행

**Jetson #1:**
```bash
cd jetson1_monitoring
python3 JETSON1_INTEGRATED.py
```

**Jetson #2:**
```bash
cd jetson2_frying_ai
python3 JETSON2_INTEGRATED.py
```

---

## 📂 프로젝트 구조

```
jetson-camera-monitor/
├── 배포가이드.md                      # ⭐ 배포 시 필독!
├── README.md                          # 이 문서
├── requirements.txt                   # Python 패키지 버전 고정
├── system_check.sh                       # 전체 시스템 검증 (sudo 필요)
├── install.sh                         # 의존성 설치
├── check_versions.sh                  # 버전 확인
├── set_maxn_mode.sh                   # MAXN 성능 모드
├── install_autostart.sh               # 자동 시작 설정
├──
├── jetson1_monitoring/                # Jetson #1 프로그램
│   ├── JETSON1_INTEGRATED.py
│   └── config.json
├──
├── jetson2_frying_ai/                 # Jetson #2 프로그램
│   ├── JETSON2_INTEGRATED.py
│   └── config_jetson2.json
├──
├── camera_autostart/                  # GMSL 카메라 드라이버
│   └── camera_driver_autoload.sh
└──
└── docs/                              # 추가 문서
```

---

## ⚙️ 주요 설정

### Python 패키지 (버전 고정)
```
numpy==1.26.4
opencv-python==4.12.0.88
ultralytics==8.3.224
paho-mqtt==2.1.0
psutil==7.1.3
```

### 시스템 요구사항
- JetPack 6.2 (L4T R36.4.3)
- Python 3.10.12
- PyTorch 2.8.0 with CUDA 12.6

---

## 🔧 문제 해결

### GPU 사용 안 됨
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
```

### 카메라 안 보임
```bash
cd camera_autostart
sudo ./camera_driver_autoload.sh
ls -l /dev/video*
```

### 버전 확인
```bash
./check_versions.sh
```

### 성능 모드 확인
```bash
sudo nvpmodel -q
# NV Power Mode: MAXN_SUPER (2) ← 이게 나와야 함
```

---

## 📚 문서

### 필수
- **배포가이드.md** - 새 Jetson 배포 시 필독 ⭐

### 참고
- `docs/guides/QUICK_SETUP.md` - jtop, MAXN 모드
- `docs/guides/GPU_OPTIMIZATION_STATUS.md` - GPU 최적화 상태
- `jetson1_monitoring/JETSON1_GUIDE.md` - Jetson #1 상세 가이드
- `jetson2_frying_ai/DATA_COLLECTION_GUIDE_UPDATED.md` - 데이터 수집

---

## 🎯 성능 목표

### Jetson #1
- ✅ GPU 가속 활성화
- CPU 사용률: <50%
- FPS: 30

### Jetson #2
- ✅ GPU 가속 활성화
- ✅ CPU 최적화 완료
- CPU 사용률: ~30%
- FPS: 15 (4개 카메라)

---

## 📝 버전 관리

### 현재 버전 (2025-01-05)
- ✅ Jetson #1 GPU 가속 활성화
- ✅ Jetson #2 데이터 수집 기능 추가
- ✅ MAXN 모드 스크립트 추가
- ✅ 버전 고정 (requirements.txt)
- ✅ 폴더명 정리 (jetson1_monitoring, jetson2_frying_ai)

---

## 💡 핵심 포인트

1. ✅ **배포가이드.md** 하나만 읽으면 됨
2. ✅ **requirements.txt** 덕분에 버전 자동 고정
3. ✅ **install.sh** 한 번 실행으로 모든 설치 완료
4. ✅ WiFi는 처음에만 필요, 이후 완전 오프라인
5. ✅ GPU 가속 자동 활성화

---

**배포 시작하기:** `cat 배포가이드.md` 📖

**문의:** GitHub Issues
