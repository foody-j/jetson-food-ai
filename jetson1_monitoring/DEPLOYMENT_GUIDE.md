# Jetson Orin Nano 배포 가이드
## JETSON1_INTEGRATED.py - 3-Camera Monitoring System

---

## 📋 사전 준비

### 하드웨어 요구사항
- Jetson Orin Nano (JetPack 6.0+)
- GMSL 카메라 3개 (video0, video1, video2)
- GMSL 드라이버 (SG4A-NONX-G2Y-A1)

### 소프트웨어 요구사항
- Ubuntu 22.04 (Jetson 기본)
- Python 3.8+
- JetPack SDK

---

## 🚀 빠른 설치 (자동)

### 1단계: 프로젝트 복사
새로운 Jetson에 프로젝트 전체를 복사하세요:

```bash
# 방법 1: USB/외장 드라이브 사용
cp -r /media/usb/jetson-camera-monitor ~/

# 방법 2: SCP 사용 (네트워크)
scp -r user@source-jetson:/home/user/jetson-camera-monitor ~/

# 방법 3: Git 사용 (저장소가 있는 경우)
cd ~
git clone <repository-url> jetson-camera-monitor
```

### 2단계: 자동 설치 스크립트 실행

```bash
cd ~/jetson-camera-monitor/autostart_autodown
chmod +x DEPLOY_SETUP.sh
./DEPLOY_SETUP.sh
```

**이 스크립트는 다음을 자동으로 수행합니다:**
- ✅ 시스템 업데이트
- ✅ 한글 폰트 및 로케일 설치
- ✅ Python 패키지 설치
- ✅ GStreamer 설치
- ✅ MQTT 라이브러리 설치
- ✅ Ultralytics YOLO 설치
- ✅ 디렉토리 생성 및 권한 설정

### 3단계: YOLO 모델 다운로드

```bash
cd ~/jetson-camera-monitor/autostart_autodown
python3 -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
```

### 4단계: 설정 확인

`config.json` 파일을 확인하고 필요시 수정:

```json
{
  "camera_index": 2,              // 자동 ON/OFF 카메라 (video2)
  "stirfry_left_camera_index": 0, // 볶음 왼쪽 (video0)
  "stirfry_right_camera_index": 1 // 볶음 오른쪽 (video1)
}
```

### 5단계: 프로그램 실행

```bash
cd ~/jetson-camera-monitor/autostart_autodown
python3 JETSON1_INTEGRATED.py
```

---

## 🔧 수동 설치 (단계별)

자동 스크립트가 작동하지 않는 경우:

### 1. 시스템 업데이트
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. 한글 지원 설치
```bash
# 한글 폰트
sudo apt install -y fonts-nanum fonts-nanum-coding fonts-nanum-extra

# 한글 로케일
sudo apt install -y language-pack-ko
sudo locale-gen ko_KR.UTF-8
sudo update-locale LANG=ko_KR.UTF-8 LC_MESSAGES=POSIX

# 확인
locale | grep LANG
```

### 3. Python 및 GStreamer 패키지
```bash
# Python 기본
sudo apt install -y python3-pip python3-tk python3-pil python3-pil.imagetk

# GStreamer
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good
sudo apt install -y v4l-utils
```

### 4. Python 라이브러리
```bash
cd ~/jetson-camera-monitor/autostart_autodown

# requirements.txt 사용
pip3 install -r requirements.txt

# 또는 개별 설치
pip3 install paho-mqtt Pillow ultralytics numpy
```

### 5. 데이터 디렉토리 생성
```bash
mkdir -p ~/StirFry_Data/left
mkdir -p ~/StirFry_Data/right
mkdir -p ~/Detection
```

---

## 🎯 GMSL 드라이버 설정

### 드라이버 로드 (자동)
프로그램이 자동으로 드라이버를 로드합니다. `config.json`에서 경로 확인:

```json
{
  "gmsl_driver_dir": "/home/dkuyj/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3"
}
```

### 수동 드라이버 로드 (필요시)
```bash
cd ~/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/ko

sudo insmod max96712.ko
sudo insmod sgx-yuv-gmsl2.ko GMSLMODE_1=2,2,2,2

# 확인
lsmod | grep gmsl
ls -la /dev/video*
```

---

## ⚙️ 설정 파일 (config.json)

주요 설정 항목:

```json
{
  // 카메라 인덱스
  "camera_index": 2,                    // video2 (자동 ON/OFF)
  "stirfry_left_camera_index": 0,       // video0 (볶음 왼쪽)
  "stirfry_right_camera_index": 1,      // video1 (볶음 오른쪽)

  // GMSL 설정
  "gmsl_mode": 2,                       // GMSL2/3G
  "gmsl_resolution_mode": 1,            // 1920x1536

  // YOLO 설정
  "yolo_model": "yolo11n.pt",
  "yolo_confidence": 0.7,

  // MQTT 설정
  "mqtt_enabled": false,
  "mqtt_broker": "localhost",
  "mqtt_port": 1883,

  // 시간 설정
  "day_start": "07:30",
  "day_end": "19:00",

  // 저장 설정
  "stirfry_save_dir": "StirFry_Data",
  "snapshot_dir": "Detection",
  "snapshot_cooldown_sec": 10
}
```

---

## 🧪 테스트

### 카메라 테스트
```bash
# GStreamer로 직접 확인
gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw, format=UYVY, width=1920, height=1536, framerate=30/1 ! autovideosink
gst-launch-1.0 v4l2src device=/dev/video1 ! video/x-raw, format=UYVY, width=1920, height=1536, framerate=30/1 ! autovideosink
gst-launch-1.0 v4l2src device=/dev/video2 ! video/x-raw, format=UYVY, width=1920, height=1536, framerate=30/1 ! autovideosink
```

### 간단한 3-카메라 테스트
```bash
cd ~/jetson-camera-monitor/autostart_autodown
python3 JETSON1_INTEGRATED_v2.py  # 단순 버전
```

---

## 🔑 단축키

프로그램 실행 중:
- **F11**: Fullscreen 전환
- **ESC**: Fullscreen 종료

---

## 📂 디렉토리 구조

```
~/jetson-camera-monitor/
├── autostart_autodown/
│   ├── JETSON1_INTEGRATED.py      # 메인 프로그램
│   ├── JETSON1_INTEGRATED_v2.py   # 단순 3-카메라 테스트
│   ├── gst_camera.py               # GStreamer 카메라 래퍼
│   ├── config.json                 # 설정 파일
│   ├── requirements.txt            # Python 의존성
│   ├── DEPLOY_SETUP.sh             # 자동 설치 스크립트
│   └── DEPLOYMENT_GUIDE.md         # 이 문서
├── src/
│   ├── communication/
│   │   └── mqtt_client.py
│   ├── core/
│   │   └── system_info.py
│   └── monitoring/
│       └── camera/
│           └── camera_factory.py
└── SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/
    └── ko/
        ├── max96712.ko
        └── sgx-yuv-gmsl2.ko

~/StirFry_Data/              # 볶음 데이터 저장
├── left/YYYYMMDD/
└── right/YYYYMMDD/

~/Detection/YYYYMMDD/        # 스냅샷 저장
```

---

## ❗ 문제 해결

### 1. 한글이 깨져 보임
```bash
# 로케일 재설정
sudo locale-gen ko_KR.UTF-8
sudo update-locale LANG=ko_KR.UTF-8 LC_MESSAGES=POSIX

# 재부팅
sudo reboot
```

### 2. 카메라가 안 보임
```bash
# 드라이버 확인
lsmod | grep gmsl

# 디바이스 확인
ls -la /dev/video*

# 수동 로드
cd ~/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/ko
sudo insmod max96712.ko
sudo insmod sgx-yuv-gmsl2.ko GMSLMODE_1=2,2,2,2
```

### 3. MQTT 연결 실패
```bash
# paho-mqtt 재설치
pip3 install --upgrade paho-mqtt

# config.json에서 mqtt_enabled 확인
```

### 4. YOLO 모델 로딩 실패
```bash
# 모델 재다운로드
cd ~/jetson-camera-monitor/autostart_autodown
rm -f yolo11n.pt
python3 -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
```

### 5. 권한 오류
```bash
# 데이터 디렉토리 권한
chmod -R 755 ~/StirFry_Data
chmod -R 755 ~/Detection
```

---

## 📝 추가 정보

- **용량 절약**: 볶음 데이터는 960x768 해상도, 70% 품질로 저장됨 (~19KB/장)
- **FPS**: 볶음 녹화는 ~3 FPS로 저장 (6프레임당 1장)
- **스냅샷**: 모션 감지 시 10초마다 1장 저장

---

## 📞 지원

문제 발생 시:
1. 로그 확인 (터미널 출력)
2. `config.json` 설정 재확인
3. 카메라 디바이스 상태 확인 (`ls /dev/video*`)
4. GMSL 드라이버 로드 상태 확인 (`lsmod | grep gmsl`)
