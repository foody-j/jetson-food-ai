### Context
- Hostname: ubuntu
- Working directory: /home/yjk/jetson-food-ai
- Project: jetson-food-ai
- Device / server role: Jetson relay and camera control workspace
- Date: 2026-05-18 16:13 KST

### Goal
현장 USB 릴레이가 초기화 직후 첫 명령을 놓치는 문제를 줄이기 위해 테스트 스크립트의 초기화 타이밍과 재시도 동작을 보강한다.

### Commands Run
- `rg -n "relay|usb relay|USB relay|hid|initialize|init" -S .`
- `git status --short`
- `sed -n '1,220p' test_usb_relay.py`
- `sed -n '1,220p' test_relay_pulse.py`
- `rg -n "test_usb_relay|RELAY_PORT|CMD_ON|CMD_OFF|CH340|usb serial|serial/by-id" -S .`
- `python3 -m py_compile test_usb_relay.py`
- `hostname`
- `date '+%Y-%m-%d %H:%M %Z'`

### Files Changed
- `test_usb_relay.py`: 포트 오픈 후 초기 안정화 대기, DTR/RTS 비활성화 시도, 버퍼 정리, 명령 전송 재시도, 전송 후 짧은 지연, CLI 튜닝 옵션 추가.

### Findings
- 기존 스크립트는 시리얼 포트를 연 직후 바로 첫 릴레이 명령을 전송했다.
- 현장 장비처럼 USB-serial 컨트롤러나 릴레이 MCU가 느리게 살아나는 경우 첫 명령 유실 가능성이 있다.
- 응답 확인보다 전송 성공만 믿는 구조라 초기 타이밍 이슈를 완화할 수단이 부족했다.
- 로컬에서는 하드웨어 없이 문법 검증만 가능했고 `python3 -m py_compile test_usb_relay.py` 는 통과했다.

### Resolution
- 기본 `--init-delay 1.5`, `--retries 3`, `--retry-delay 0.35`, `--post-write-delay 0.1` 값을 추가했다.
- 포트 오픈 직후 DTR/RTS를 낮추도록 시도하고 안정화 대기 후 입출력 버퍼를 정리하도록 변경했다.
- ON/OFF/STATUS 명령을 공통 전송 함수로 묶어 현장 재시도 실험이 가능하게 했다.

### Follow-up
- 현장에서 `python3 test_usb_relay.py --mode on --init-delay 2.5 --retries 5` 로 먼저 확인.
- 여전히 첫 명령이 실패하면 USB 허브 전원 안정성, 케이블 길이, `/dev/serial/by-id/...` 고정 경로, 보드 전원 인가 직후 부팅 시간을 함께 점검.
- 릴레이 보드가 ACK 프로토콜을 지원하면 응답 기반 검증으로 추가 보강 필요.

### Sensitive Data Policy
- 비밀정보, 토큰, 비밀번호, 개인 데이터는 기록하지 않았다.
