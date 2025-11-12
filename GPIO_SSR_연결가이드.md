# GPIO SSR 릴레이 연결 가이드

## 1. 개요
Jetson Orin Nano의 GPIO를 사용하여 SSR(Solid State Relay) 릴레이를 제어해 로봇 PC의 전원을 ON/OFF합니다.

## 2. 하드웨어 연결

### 2.1 필요한 부품
- **SSR 릴레이 모듈** (예: Fotek SSR-25DA, OMRON G3MB 등)
  - 입력: 3-32V DC (Jetson 3.3V GPIO로 제어 가능)
  - 출력: AC 240V or DC 24V (로봇 PC 전원 스위치 대체)
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

### 2.3 연결 방법

#### SSR 입력부 (제어부)
```
Jetson GPIO 핀 (7번)  ──────► SSR 입력 (+)
Jetson GND 핀 (6번)   ──────► SSR 입력 (-)
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
│  [7] GPIO492  ──┼──┐
│  [6] GND      ──┼──┤
└─────────────────┘  │
                     │
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

## 3. 소프트웨어 설정

### 3.1 GPIO 테스트
```bash
cd /home/yjk/jetson-food-ai

# 자동 테스트 (5번 ON/OFF)
sudo python3 test_gpio_relay.py 1

# 수동 제어 모드
sudo python3 test_gpio_relay.py 2
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
1. **주간 모드** (07:30 ~ 14:00)
   - 사람 감지 → GPIO HIGH (릴레이 ON) → 로봇 PC 켜짐
   - 30초간 사람 없음 → GPIO LOW (릴레이 OFF)

2. **야간 모드** (14:00 ~ 07:30)
   - GPIO 동작 안 함 (설정으로 변경 가능)

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

### 문제 1: "Permission denied" 오류
```bash
# 해결: sudo로 실행
sudo python3 test_gpio_relay.py
```

### 문제 2: 릴레이가 동작하지 않음
1. 멀티미터로 GPIO 핀 전압 측정 (HIGH: 3.3V, LOW: 0V)
2. SSR 입력 LED 확인 (켜지는지)
3. 와이어 연결 재확인

### 문제 3: 로봇 PC가 켜지지 않음
1. SSR 출력부 연결 확인
2. 메인보드 PWR_BTN 핀 위치 재확인
3. 케이스 전원 버튼으로 수동 테스트

### 문제 4: GPIO 충돌
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
