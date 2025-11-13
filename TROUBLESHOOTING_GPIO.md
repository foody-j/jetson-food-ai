# GPIO 출력 문제 해결 가이드

## 문제 상황
Jetson Orin Nano Super Developer Kit에서 GPIO 핀으로 출력이 되지 않는 문제 발생

```python
import Jetson.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)
GPIO.output(7, GPIO.HIGH)  # 출력이 안됨!
```

## 원인
JetPack 6.2에서는 GPIO 핀이 기본적으로 **bidirectional(양방향)**로 설정되어 있지 않음.
Device Tree에서 해당 핀을 GPIO 모드로 명시적으로 활성화해야 함.

## 해결 방법

### 1단계: Device Tree Overlay 파일 준비
`jetson-orin-gpio-patch` 디렉토리에 Pin 7용 overlay 파일이 포함되어 있음:
- `pin7_as_gpio.dts` - Device Tree 소스 파일
- `pin7_as_gpio.dtbo` - 컴파일된 overlay 파일

### 2단계: Device Tree Overlay 컴파일 (이미 완료된 경우 스킵)
```bash
cd jetson-orin-gpio-patch
dtc -O dtb -o pin7_as_gpio.dtbo pin7_as_gpio.dts
```

### 3단계: Overlay 파일을 /boot에 복사
```bash
sudo cp pin7_as_gpio.dtbo /boot/
```

### 4단계: jetson-io.py로 Overlay 활성화
```bash
sudo /opt/nvidia/jetson-io/jetson-io.py
```

실행 후:
1. **Configure Jetson 40pin Header** 선택
2. **Pin 7 gpio bidirectional** 찾아서 활성화 (스페이스바로 선택)
3. **Save and reboot** 선택

### 5단계: 재부팅
```bash
sudo reboot
```

### 6단계: 테스트
재부팅 후 테스트 스크립트 실행:
```bash
cd jetson-food-ai
python3 gpio_test.py
```

멀티미터로 Pin 7 측정 시 3.3V 출력 확인!

## Jetson.GPIO 라이브러리 설치
```bash
sudo apt update
sudo apt install python3 python3-pip -y
sudo pip install --upgrade Jetson.GPIO
```

### GPIO 그룹 권한 설정 (sudo 없이 사용하려면)
```bash
sudo usermod -a -G gpio $USER
```
재부팅 또는 로그아웃/로그인 필요

### 라이브러리 확인
```bash
python3 -c "import Jetson.GPIO; print(Jetson.GPIO.__version__)"
```

## 참고 자료
- [GitHub Issue #120 - NVIDIA/jetson-gpio](https://github.com/NVIDIA/jetson-gpio/issues/120)
- [JetsonHacks - Device Tree Overlays on Jetson](https://jetsonhacks.com/2025/04/07/device-tree-overlays-on-jetson-scary-but-fun/)
- jetson-orin-gpio-patch 디렉토리의 README.md

## 문제 해결 팁
- overlay가 제대로 적용되었는지 확인: `cat /boot/extlinux/extlinux.conf`에서 `FDT` 줄에 overlay가 추가되었는지 확인
- GPIO 핀이 다른 장치와 충돌하지 않는지 확인
- 다른 핀을 사용하려면 해당 핀용 DTS 파일을 수정하여 새로운 overlay 생성 필요

---

## SSR 제어 구현

### 레벨 시프터/컨버터 문제
처음에 레벨 컨버터(ELB060214)를 사용했으나 다음 문제 발생:
- HV 측 풀업 저항 때문에 항상 5V 출력
- LV 측 풀다운 저항(10kΩ) 추가해도 해결 안 됨
- LOW 신호: 1.5V (0V가 되어야 함)
- HIGH 신호: 4.2V (5V가 되어야 함)

**결론: 레벨 컨버터는 GPIO 제어용으로 부적합!**

### 최종 해결 방법
**레벨 컨버터 없이 직접 연결** (대부분의 SSR은 3-32V DC 입력 지원)

```
Jetson Pin 7 (GPIO, 3.3V) ----직접---- SSR+
Jetson GND                ------------- SSR-
```

**주의사항:**
- GPIO Pin 7에 LED 같은 부하가 연결되면 전압 강하 발생 (정상 현상)
- SSR LED가 희미하게 켜지더라도 출력 릴레이가 작동하는지 확인 필요
- 전류 부족 시 저항 제거하거나 더 작은 값(220Ω, 100Ω)으로 변경

### JETSON1_INTEGRATED.py SSR 제어 로직
**출근시간(07:30) 이후 사람 감지 시:**
- YOLO로 사람 30초간 감지 → SSR ON (히터/장비 켜짐)
- 계속 켜진 상태 유지

**운영시간 종료(14:00) 이후:**
- 10분간 사람 미감지 시 → SSR OFF (히터/장비 꺼짐)

**설정 파일: `config.json`**
```json
"day_start": "07:30",
"day_end": "14:00",
"night_check_minutes": 10
```
