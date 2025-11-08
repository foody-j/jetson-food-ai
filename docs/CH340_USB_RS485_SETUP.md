# 🔌 CH340 USB-RS485 변환기 설치 가이드

**작성일**: 2025-01-05
**대상**: Jetson Orin Nano (JetPack 6.2, Kernel 5.15.148-tegra)
**목적**: 진동 센서(USB2RS485) 통신을 위한 CH340 드라이버 설치

---

## 📋 목차

1. [문제 상황](#문제-상황)
2. [원인 분석](#원인-분석)
3. [해결 방법](#해결-방법)
4. [설치 과정](#설치-과정)
5. [검증](#검증)
6. [문제 해결](#문제-해결)

---

## 문제 상황

### 증상
```bash
$ ls /dev/ttyUSB*
ls: cannot access '/dev/ttyUSB*': No such file or directory
```

USB-RS485 변환기를 연결해도 `/dev/ttyUSB0` 장치가 생성되지 않음

### 장치 정보
```bash
$ lsusb
Bus 001 Device 005: ID 1a86:7523 QinHeng Electronics CH340 serial converter
```

USB 장치는 인식되지만, 시리얼 포트가 생성되지 않음

---

## 원인 분석

### 1차 원인: CH341 커널 모듈 누락

Jetson Orin Nano의 기본 커널에 CH340/CH341 드라이버가 포함되지 않음:

```bash
$ lsmod | grep ch341
# (아무것도 안 나옴)

$ modinfo ch341
modinfo: ERROR: Module ch341 not found.
```

### 2차 원인: **brltty 충돌** ⚠️

**brltty (Braille TTY)**: 시각 장애인을 위한 **점자 디스플레이** 지원 데몬

문제:
- brltty가 CH340 장치를 점자 디스플레이로 오인
- `/dev/ttyUSB0`를 선점하여 다른 프로그램이 사용 불가
- USB 연결 시 자동으로 장치를 독점

**확인 방법**:
```bash
$ systemctl status brltty
● brltty.service - Braille Device Support
   Loaded: loaded
   Active: active (running)

$ dmesg | grep -i brltty
[  123.456] brltty[1234]: detected CH340 device
```

---

## 해결 방법

### 방법 1: 간단한 방법 (brltty만 제거)

진동 센서만 사용하고 점자 디스플레이가 필요 없는 경우:

```bash
sudo systemctl stop brltty
sudo systemctl disable brltty
sudo apt-get remove -y brltty
```

### 방법 2: 완전한 방법 (권장)

CH341 드라이버 빌드 + brltty 제거 + udev 규칙 설정:

**한 번에 실행**:
```bash
cd ~/jetson-camera-monitor
sudo bash setup_ch340_complete.sh
```

---

## 설치 과정

### 자동 설치 (권장)

**`setup_ch340_complete.sh` 스크립트**:

```bash
cd ~/jetson-camera-monitor
sudo bash setup_ch340_complete.sh
```

**스크립트 내용**:
1. ✅ CH341 커널 모듈 빌드 및 설치
2. ✅ brltty 제거 (점자 디스플레이 충돌 해결)
3. ✅ udev 규칙 설정 (자동 인식)

**실행 결과**:
```
==================================================
  CH340 USB-RS485 변환기 설치 (Jetson Orin Nano)
==================================================

[1/3] CH341 커널 모듈 빌드 및 설치...
  - 드라이버 소스 다운로드...
  - 컴파일 중...
  - 모듈 설치...
  ✓ CH341 모듈 설치 완료

[2/3] brltty 충돌 해결...
  - brltty 패키지 제거 중...
  ✓ brltty 제거 완료

[3/3] udev 규칙 설정...
  ✓ udev 규칙 설정 완료

==================================================
  설치 완료!
==================================================

USB-RS485 변환기를 연결하세요.
장치: /dev/ttyUSB0 또는 /dev/ttyUSB_CH340

✓✓✓ USB 시리얼 장치 발견:
crw-rw-rw- 1 root dialout 188, 0 Jan  5 15:30 /dev/ttyUSB0
```

---

### 수동 설치 (상세)

#### Step 1: CH341 커널 모듈 빌드

```bash
# 빌드 도구 설치
sudo apt-get update
sudo apt-get install -y build-essential bc kmod wget

# 작업 디렉토리
cd /tmp
mkdir ch341_build
cd ch341_build

# 드라이버 소스 다운로드
wget https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/drivers/usb/serial/ch341.c?h=v5.15 -O ch341.c

# Makefile 생성
cat > Makefile << 'EOF'
obj-m := ch341.o
all:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
clean:
	rm -f *.o *.ko *.mod.c *.mod .*.cmd Module.symvers modules.order
	rm -rf .tmp_versions
EOF

# 컴파일
make

# 설치
sudo mkdir -p /lib/modules/$(uname -r)/kernel/drivers/usb/serial/
sudo cp ch341.ko /lib/modules/$(uname -r)/kernel/drivers/usb/serial/
sudo depmod -a

# 모듈 로드
sudo modprobe ch341

# 부팅 시 자동 로드
echo "ch341" | sudo tee -a /etc/modules
```

#### Step 2: brltty 제거

```bash
# 서비스 중지
sudo systemctl stop brltty
sudo systemctl disable brltty

# 프로세스 종료
sudo pkill -9 brltty

# 패키지 제거
sudo apt-get remove -y brltty
```

#### Step 3: udev 규칙 설정

```bash
# udev 규칙 생성
sudo tee /etc/udev/rules.d/99-ch340.rules << 'EOF'
# CH340/CH341 USB to Serial Converter
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", RUN+="/sbin/modprobe ch341"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", SYMLINK+="ttyUSB_CH340"
KERNEL=="ttyUSB*", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="dialout"
EOF

# udev 재로드
sudo udevadm control --reload-rules
sudo udevadm trigger

# dialout 그룹 추가
sudo usermod -a -G dialout $USER
```

---

## 검증

### 1. 모듈 확인
```bash
$ lsmod | grep ch341
ch341                  20480  0
usbserial             57344  1 ch341
```

### 2. 장치 확인
```bash
$ ls -l /dev/ttyUSB*
crw-rw-rw- 1 root dialout 188, 0 Jan  5 15:30 /dev/ttyUSB0
lrwxrwxrwx 1 root root         7 Jan  5 15:30 /dev/ttyUSB_CH340 -> ttyUSB0
```

### 3. Python 테스트
```bash
$ python3 << 'EOF'
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"포트: {port.device}")
    print(f"설명: {port.description}")
    print(f"제조사: {port.manufacturer}")
    print()
EOF
```

**출력 예시**:
```
포트: /dev/ttyUSB0
설명: USB2.0-Serial
제조사: 1a86:7523
```

### 4. 진동 센서 테스트
```bash
$ python3 vibration_sensor_simple.py
[연결] /dev/ttyUSB0 - 9600 baud
[읽기] UID: 50, X: 0.5, Y: 0.4, Z: 0.3
```

---

## 문제 해결

### 문제 1: 여전히 `/dev/ttyUSB0`가 안 보임

**확인 사항**:
```bash
# USB 연결 확인
lsusb | grep 1a86

# dmesg 로그 확인
sudo dmesg | tail -20

# brltty 완전 제거 확인
ps aux | grep brltty
systemctl status brltty
```

**해결**:
```bash
# USB 재연결
# 1. USB 뽑기
# 2. 5초 대기
# 3. USB 꽂기

# 또는 모듈 재로드
sudo rmmod ch341
sudo modprobe ch341
```

### 문제 2: 권한 거부 (Permission denied)

**증상**:
```python
serial.serialutil.SerialException: [Errno 13] Permission denied: '/dev/ttyUSB0'
```

**해결**:
```bash
# dialout 그룹 추가
sudo usermod -a -G dialout $USER

# 로그아웃 후 다시 로그인
# 또는 임시로:
newgrp dialout

# 또는 권한 직접 변경 (임시):
sudo chmod 666 /dev/ttyUSB0
```

### 문제 3: brltty가 자꾸 설치됨

**원인**: 다른 패키지 의존성으로 자동 설치

**해결**:
```bash
# brltty 설치 차단
sudo apt-mark hold brltty

# 확인
apt-mark showhold
```

### 문제 4: 부팅 후 장치가 안 보임

**원인**: 모듈이 자동 로드되지 않음

**해결**:
```bash
# /etc/modules 확인
cat /etc/modules | grep ch341

# 없으면 추가
echo "ch341" | sudo tee -a /etc/modules

# 재부팅
sudo reboot
```

---

## 📊 요약

### brltty란?
- **Braille TTY**: 시각 장애인용 점자 디스플레이 지원 데몬
- USB 시리얼 장치를 점자 디스플레이로 오인하여 선점
- 진동 센서에는 불필요하므로 제거 필요

### 설치 체크리스트

- [x] CH341 커널 모듈 빌드 및 설치
- [x] brltty 제거 (점자 디스플레이 충돌 해결)
- [x] udev 규칙 설정
- [x] dialout 그룹 추가
- [x] 부팅 시 자동 로드 설정
- [x] 장치 확인 (`/dev/ttyUSB0`)
- [x] Python 테스트 성공

### 관련 파일

| 파일 | 설명 |
|------|------|
| `setup_ch340_complete.sh` | **한 번에 설치 (권장)** |
| `build_ch341_final.sh` | CH341 모듈만 빌드 |
| `old_ch340_scripts/fix_brltty.sh` | brltty만 제거 |
| `vibration_sensor_simple.py` | 진동 센서 테스트 |
| `vibration_config.json` | 진동 센서 설정 |

---

## 🎯 Quick Start

**처음 설치하는 경우**:
```bash
cd ~/jetson-camera-monitor
sudo bash setup_ch340_complete.sh
```

**이미 설치했는데 안 되는 경우**:
```bash
# USB 뽑았다가 다시 꽂기
# 그래도 안 되면:
sudo bash old_ch340_scripts/fix_brltty.sh
```

**테스트**:
```bash
ls -l /dev/ttyUSB*
python3 vibration_sensor_simple.py
```

---

## 📞 문의

CH340 드라이버 관련 문의: GitHub Issues

---

**문서 업데이트**: 2025-01-05
**검증 완료**: Jetson Orin Nano, JetPack 6.2
