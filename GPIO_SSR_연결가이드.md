# GPIO SSR 릴레이 연결 가이드

## 1. 개요
Jetson Orin Nano의 GPIO를 사용하여 SSR(Solid State Relay) 릴레이를 제어해 로봇 PC의 전원을 ON/OFF합니다.

## 2. 하드웨어 연결

### 2.1 필요한 부품
- **SSR 릴레이 모듈** (예: Fotek SSR-25DA, OMRON G3MB 등)
  - 입력: 3-32V DC (5V 권장)
  - 출력: AC 240V or DC 24V (로봇 PC 전원 스위치 대체)
- **레벨 시프터 모듈** (3.3V ↔ 5V 양방향 변환)
  - 예: 4채널 레벨 시프터, TXS0108E 모듈
  - Jetson GPIO 3.3V를 5V로 변환하여 SSR 안정 구동
- **점퍼 와이어** (암-암 또는 암-수)
- **(선택) LED + 저항** (동작 확인용)

### 2.2 Jetson Orin Nano 40핀 헤더 핀맵
```
    3.3V  (1) (2)  5V
   GPIO2  (3) (4)  5V
   GPIO3  (5) (6)  GND  ◄─ 그라운드
  GPIO492 (7) (8)  TXD
     GND  (9) (10) RXD
  GPIO460 (11) ...
```

**추천 GPIO 핀:**
| 물리적 핀 | GPIO 번호 | 추천 이유 |
|---------|----------|---------|
| **7**   | GPIO492  | 기본 GPIO, 사용하기 쉬움 (추천) |
| **11**  | GPIO460  | UART 대체 가능 |
| **13**  | GPIO398  | SPI 대체 가능 |
| **15**  | GPIO433  | PWM 지원 (필요시) |

### 2.3 연결 방법 (레벨 시프터 사용)

#### 레벨 시프터 연결
```
Jetson                    레벨 시프터
────────────────────      ──────────────
3.3V 핀 (1번)      ────► LV (Low Voltage 전원)
5V 핀 (2번)        ────► HV (High Voltage 전원)
GND 핀 (6번)       ────► GND (공통 접지)
GPIO 핀 (7번)      ────► LV1 (3.3V 입력)
```

#### SSR 입력부 (제어부)
```
레벨 시프터               SSR 릴레이
──────────────           ────────────
HV1 (5V 출력)    ──────► SSR 입력 (+)
GND              ──────► SSR 입력 (-)
```

#### SSR 출력부 (로봇 PC 전원)
```
로봇 PC 전원 버튼의 두 선을 SSR 출력에 연결:
  PC 파워 스위치 선 1 ──────► SSR 출력 1
  PC 파워 스위치 선 2 ──────► SSR 출력 2
```

**로봇 PC 메인보드 전원 스위치 핀:**
- 메인보드에서 POWER SW (또는 PWR_BTN) 2핀 커넥터를 찾음
- 기존 케이스 전원 버튼 대신 SSR 출력 연결
- 극성 없음 (어느 방향이든 상관없음)

### 2.4 연결 다이어그램
```
┌─────────────────┐
│ Jetson Orin Nano│
│                 │
│  [1] 3.3V     ──┼──┐
│  [2] 5V       ──┼──┤
│  [6] GND      ──┼──┤
│  [7] GPIO492  ──┼──┤
└─────────────────┘  │
                     │
              ┌──────▼──────────┐
              │  레벨 시프터     │
              │  LV  HV  GND    │
              │  LV1 HV1        │
              └──────┬──────────┘
                     │ HV1 (5V)
                ┌────▼────┐
                │   SSR   │
                │ 입력 +-  │
                │         │
                │ 출력 1-2 │
                └────┬────┘
                     │
              ┌──────▼──────────┐
              │ 로봇 PC 메인보드  │
              │ PWR_BTN (2핀)   │
              └─────────────────┘
```

### 2.5 GPIO 핀 변경 방법

**기본 핀:** 7번 (GPIO492)

**다른 사용 가능한 GPIO 핀:**
| 물리적 핀 | GPIO 번호 | 특징 |
|---------|----------|------|
| **11**  | GPIO460  | UART 대체 가능 |
| **13**  | GPIO398  | SPI 대체 가능 |
| **15**  | GPIO433  | PWM 지원 |
| **16**  | GPIO474  | 일반 GPIO |
| **18**  | GPIO473  | 일반 GPIO |
| **33**  | GPIO391  | PWM 지원 |

**⚠️ 절대 사용하면 안 되는 핀:**
- **1, 17번**: 3.3V 전원 (GPIO 아님)
- **2, 4번**: 5V 전원 (GPIO 아님)
- **6, 9, 14, 20, 25, 30, 34, 39번**: GND (GPIO 아님)
- **27, 28번**: I2C EEPROM 전용 (건드리면 부팅 불가)

**핀 번호 변경 방법:**
```python
# test_gpio_relay.py 파일에서
RELAY_PIN = 7  # 원하는 핀 번호로 변경 (예: 11, 13, 15 등)

# 또는 config.json에서
"gpio_relay_pin": 7  # 원하는 핀 번호로 변경
```

## 3. 소프트웨어 설정

### 3.1 GPIO 테스트

#### ⚠️ Jetson Orin Nano Super 사용자 필독
**Jetson Orin Nano Super** 모델은 환경 변수 설정이 필요합니다:

```bash
cd /home/yjk/jetson-food-ai

# 방법 1: 환경 변수 설정 스크립트 (권장)
./test_gpio_with_env.sh

# 방법 2: 수동으로 환경 변수 설정
export JETSON_MODEL_NAME=JETSON_ORIN_NANO
sudo -E python3 test_gpio_relay.py 1

# 방법 3: libgpiod 사용 (환경변수 불필요)
python3 check_gpio_with_gpiod.py
```

**배경**: Jetson Orin Nano Super는 `nvidia,p3768-0000+p3767-0005-super` 모델명을 사용하는데,
Jetson.GPIO 라이브러리(v2.1.7)가 `-super` 접미사를 인식하지 못합니다.
환경 변수로 모델을 명시하면 해결됩니다. ([NVIDIA Issue #120](https://github.com/NVIDIA/jetson-gpio/issues/120))

#### 일반 GPIO 릴레이 테스트
```bash
cd /home/yjk/jetson-food-ai

# 자동 테스트 (5번 ON/OFF)
sudo python3 test_gpio_relay.py 1

# 수동 제어 모드
sudo python3 test_gpio_relay.py 2

# 전체 GPIO 핀 상태 확인 (쇼트 점검용)
./test_gpio_with_env.sh
```

### 3.2 GPIO 권한 설정 (선택사항)
sudo 없이 사용하려면:
```bash
sudo groupadd -f gpio
sudo usermod -a -G gpio $USER
sudo chown root:gpio /sys/class/gpio/export /sys/class/gpio/unexport
sudo chmod 220 /sys/class/gpio/export /sys/class/gpio/unexport

# 재로그인 필요
```

## 4. JETSON1 통합 코드에 GPIO 제어 추가

### 4.1 config.json 설정
```json
{
  "_comment_gpio": "GPIO 릴레이 설정",
  "gpio_enabled": true,
  "gpio_relay_pin": 7,
  "gpio_relay_mode": "BOARD",
  "_comment_gpio_behavior": "사람 감지 시 릴레이 ON, 출근시간에만 동작",
  "gpio_auto_off_minutes": 0
}
```

### 4.2 동작 로직

**실제 구현된 로직:**

1. **주간 모드** (07:30 ~ 19:30, config.json의 day_start/day_end)
   - 사람 **2초 감지** (YOLO) → GPIO HIGH (SSR ON) → 로봇 PC 켜짐 + MQTT "ON" 전송
   - **야간 모드 전환까지 SSR 계속 ON 유지** (한 번 켜지면 야간까지 유지)

2. **야간 모드** (19:30 ~ 07:30)
   - **10분간 사람 없음** (config.json의 night_check_minutes) → GPIO LOW (SSR OFF) → 로봇 PC 꺼짐 + MQTT "OFF" 전송
   - 이후 모션 감지 시 스냅샷만 저장 (GPIO 제어 안 함)

## 5. 안전 주의사항

### 5.1 전기 안전
- ⚠️ SSR 출력부는 **절대 만지지 마세요** (감전 위험)
- SSR은 절연된 케이스에 넣어 사용 권장
- AC 전원 사용 시 반드시 접지 확인

### 5.2 GPIO 보호
- GPIO 최대 전류: **50mA** (초과 시 Jetson 손상)
- SSR 입력 전류: 일반적으로 10-20mA (안전)
- 직접 릴레이 코일 연결 금지 (SSR 사용 필수)

### 5.3 로봇 PC 보호
- 로봇 PC가 꺼진 상태에서만 GPIO로 켜기 가능
- 이미 켜진 PC에 GPIO 신호 보내면 → 강제 종료될 수 있음
- **해결책**:
  - 로봇 PC에서 네트워크 핑 체크
  - 응답 없을 때만 GPIO ON

## 6. 트러블슈팅

### 문제 1: "Could not determine Jetson model" 오류 (Orin Nano Super)
```
Exception: Could not determine Jetson model
```

**원인**: Jetson Orin Nano Super 모델명에 `-super` 접미사가 포함되어 라이브러리가 인식 못함

**해결 방법**:
```bash
# 방법 1: 환경 변수 설정 (권장)
export JETSON_MODEL_NAME=JETSON_ORIN_NANO
sudo -E python3 test_gpio_relay.py

# 방법 2: 스크립트 사용
./test_gpio_with_env.sh

# 방법 3: libgpiod 사용
python3 check_gpio_with_gpiod.py
```

**참고**: [NVIDIA Jetson GPIO Issue #120](https://github.com/NVIDIA/jetson-gpio/issues/120)

### 문제 2: "Permission denied" 오류
```bash
# 해결: sudo로 실행
sudo python3 test_gpio_relay.py
```

### 문제 3: 릴레이가 동작하지 않음
1. 멀티미터로 GPIO 핀 전압 측정 (HIGH: 3.3V, LOW: 0V)
2. SSR 입력 LED 확인 (켜지는지)
3. 와이어 연결 재확인

### 문제 4: 로봇 PC가 켜지지 않음
1. SSR 출력부 연결 확인
2. 메인보드 PWR_BTN 핀 위치 재확인
3. 케이스 전원 버튼으로 수동 테스트

### 문제 5: GPIO 충돌
```bash
# 사용 중인 GPIO 확인
ls /sys/class/gpio/
cat /sys/kernel/debug/gpio
```

## 7. 추가 기능 (선택사항)

### 7.1 로봇 PC 상태 모니터링
```python
import subprocess

def check_robot_pc_alive(robot_ip):
    """로봇 PC가 켜져 있는지 확인"""
    try:
        result = subprocess.run(['ping', '-c', '1', '-W', '1', robot_ip],
                               capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False
```

### 7.2 릴레이 ON 시간 제한
- 5초 ON → 자동 OFF (PC 전원 버튼 누름 시뮬레이션)
- 계속 ON 상태 유지하면 PC 강제 종료 위험

## 8. 참고 자료
- Jetson GPIO 공식 문서: https://github.com/NVIDIA/jetson-gpio
- JetsonHacks GPIO 가이드: https://jetsonhacks.com/
- SSR 릴레이 원리: https://en.wikipedia.org/wiki/Solid-state_relay
