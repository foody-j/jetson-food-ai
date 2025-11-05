# 📀 USB로 Jetson 배포하기

**인터넷 없이 USB로만 배포하는 방법**

---

## 🎯 준비물

### 현재 Jetson (개발 PC)
- ✅ 인터넷 연결 (한 번만)
- ✅ USB 드라이브 (최소 2GB)

### 타겟 Jetson (새 보드)
- ✅ JetPack 6.2 설치됨
- ❌ 인터넷 불필요!

---

## 📦 단계 1: USB 패키지 생성 (현재 Jetson)

### 방법 1: 자동 스크립트 (추천)

```bash
cd ~/jetson-camera-monitor
./prepare_usb.sh
```

**출력:**
```
압축 완료: ~/jetson-camera-monitor-usb.tar.gz
파일 크기: 42M
```

**USB가 연결되어 있으면:** 자동으로 복사 여부 물어봄  
**USB가 없으면:** 수동으로 복사하라고 안내

---

### 방법 2: 수동 압축

```bash
cd ~
tar -czf jetson-camera-monitor-usb.tar.gz \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='Detection/*' \
    --exclude='StirFry_Data/*' \
    jetson-camera-monitor
```

---

## 💾 단계 2: USB에 복사

### USB 마운트 확인

```bash
ls -l /media/$USER/
# 또는
df -h | grep media
```

### 파일 복사

```bash
# USB 경로 확인 (예: /media/dkuyj/USB_DRIVE)
cp ~/jetson-camera-monitor-usb.tar.gz /media/$USER/USB_DRIVE/

# 또는 GUI로 복사
# 파일 탐색기에서 ~/jetson-camera-monitor-usb.tar.gz를 USB로 드래그
```

### USB 안전 제거

```bash
sync
umount /media/$USER/USB_DRIVE
# 또는 GUI에서 "안전하게 제거"
```

---

## 📥 단계 3: 타겟 Jetson에 설치

### 3-1. USB 마운트

타겟 Jetson에 USB 연결

```bash
ls -l /media/$USER/
# USB 자동 마운트 확인
```

---

### 3-2. 파일 복사 및 압축 해제

```bash
# 홈 디렉토리로 복사
cd ~
cp /media/$USER/USB_DRIVE/jetson-camera-monitor-usb.tar.gz ./

# 압축 해제
tar -xzf jetson-camera-monitor-usb.tar.gz

# 확인
ls -l jetson-camera-monitor/
```

---

### 3-3. 의존성 설치 (인터넷 필요!)

```bash
cd jetson-camera-monitor
./install.sh
```

**주의:** Python 패키지 설치에는 인터넷이 필요합니다!

**인터넷이 정말 없다면:** "오프라인 패키지" 섹션 참고

---

### 3-4. 성능 모드 설정

```bash
./set_maxn_mode.sh

# 부팅 시 자동 적용
./install_maxn_service.sh
sudo reboot
```

---

### 3-5. 카메라 드라이버 로드

```bash
cd camera_autostart
sudo ./camera_driver_autoload.sh

# 확인
ls -l /dev/video*
```

---

### 3-6. 시스템 검증

```bash
cd ~/jetson-camera-monitor
sudo ./시스템검증.sh
```

**정상:**
```
통과: 9 / 실패: 0
✅ 모든 검증 통과! 시스템 정상입니다.
```

---

### 3-7. 프로그램 실행

```bash
cd ~/jetson-camera-monitor/jetson1_monitoring
python3 JETSON1_INTEGRATED.py
```

---

## 🔌 완전 오프라인 배포 (인터넷 전혀 없음)

타겟 Jetson에 **인터넷이 전혀 없는** 경우:

### 사전 준비 (현재 Jetson, 인터넷 필요)

```bash
cd ~/jetson-camera-monitor

# 1. Python 패키지 다운로드
mkdir -p offline_packages
pip3 download -r requirements.txt -d offline_packages

# 2. 전체 압축 (오프라인 패키지 포함)
cd ~
tar -czf jetson-offline-complete.tar.gz \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='Detection/*' \
    --exclude='StirFry_Data/*' \
    jetson-camera-monitor

# USB로 복사
cp jetson-offline-complete.tar.gz /media/$USER/USB_DRIVE/
```

**크기:** 약 150MB~200MB (Python 패키지 포함)

---

### 타겟 Jetson 설치 (완전 오프라인)

```bash
# 1. USB에서 복사 및 압축 해제
cd ~
cp /media/$USER/USB_DRIVE/jetson-offline-complete.tar.gz ./
tar -xzf jetson-offline-complete.tar.gz

# 2. 오프라인 패키지 설치
cd jetson-camera-monitor/offline_packages
pip3 install --no-index --find-links=. *.whl

# 3. MAXN 모드
cd ~/jetson-camera-monitor
./set_maxn_mode.sh

# 4. 카메라 드라이버
cd camera_autostart
sudo ./camera_driver_autoload.sh

# 5. 검증
cd ~/jetson-camera-monitor
sudo ./시스템검증.sh

# 6. 실행
cd jetson1_monitoring
python3 JETSON1_INTEGRATED.py
```

---

## 📊 파일 크기 비교

| 패키지 | 크기 | 내용 | 인터넷 필요 |
|--------|------|------|-------------|
| `jetson-camera-monitor-usb.tar.gz` | 42MB | 프로젝트만 | ✅ 필요 (pip install) |
| `jetson-offline-complete.tar.gz` | 150~200MB | 프로젝트 + Python 패키지 | ❌ 불필요 |

---

## ✅ 체크리스트

### USB 패키지 생성
- [ ] `./prepare_usb.sh` 실행
- [ ] `~/jetson-camera-monitor-usb.tar.gz` 생성 확인 (42MB)
- [ ] USB에 복사
- [ ] USB 안전 제거

### 타겟 Jetson 설치
- [ ] USB 마운트 확인
- [ ] 파일 복사 및 압축 해제
- [ ] `./install.sh` 실행 (또는 오프라인 패키지 설치)
- [ ] `./set_maxn_mode.sh` 실행
- [ ] `./camera_driver_autoload.sh` 실행
- [ ] `sudo ./시스템검증.sh` 실행 (통과: 9)
- [ ] 프로그램 실행 확인

---

## 💡 팁

### USB 마운트 경로 찾기

```bash
# 방법 1
ls -l /media/$USER/

# 방법 2
df -h | grep media

# 방법 3
lsblk
```

### 압축 해제 확인

```bash
cd ~/jetson-camera-monitor
ls -l

# 확인할 파일:
# - 배포가이드.md
# - README.md
# - requirements.txt
# - install.sh
# - 시스템검증.sh
# - jetson1_monitoring/
# - jetson2_frying_ai/
```

### 용량 부족 시

```bash
# 불필요한 파일 제거
rm -rf Detection/*
rm -rf StirFry_Data/*
rm -rf AI_Data/*

# 재압축
cd ~
tar -czf jetson-camera-monitor-usb.tar.gz jetson-camera-monitor
```

---

## 🚀 요약

### 간단 버전 (인터넷 있음)
1. `./prepare_usb.sh` → USB 복사
2. 타겟 Jetson: 압축 해제 → `./install.sh`
3. MAXN 모드 → 카메라 드라이버 → 실행

### 완전 오프라인
1. `offline_packages/` 준비 → 전체 압축 → USB
2. 타겟 Jetson: 압축 해제 → 오프라인 설치
3. MAXN 모드 → 카메라 드라이버 → 실행

---

**USB로 배포 준비 완료!** 🎉

**다음:** USB 꽂고 `./prepare_usb.sh` 실행!
