### Context
- Hostname: sandbox (Jetson backup workspace)
- Working directory: /home/youngjin/jetson_backup/jetson-food-ai
- Project: jetson-food-ai
- Device / server role: Jetson relay and GMSL camera control workspace
- Date: 2026-10-26 10:08 KST

### Goal
GMSL 카메라 디시리얼라이저(MAX96712 보드)가 반드시 먼저 켜진 뒤 젯슨(커널 드라이버/시스템)이 초기화되도록 보장하는 USB 릴레이 연동 초기화 스크립트를 작성한다.

### Commands Run
- `grep -rn -iE "relay|deser|max9296|max96712|gpio|power|reset" .`
- `chmod +x /home/youngjin/jetson_backup/jetson-food-ai/reset_deser_and_init_cameras.sh`
- `bash -n /home/youngjin/jetson_backup/jetson-food-ai/reset_deser_and_init_cameras.sh`
- `/home/youngjin/jetson_backup/jetson-food-ai/reset_deser_and_init_cameras.sh --help`

### Files Changed
- `GMSL_CAMERA_DESERIALIZER_TROUBLESHOOTING.md`: 흩어져 있던 GMSL 카메라/디시리얼라이저/USB 릴레이 관련 에러 로그, 원인 분석, 하드웨어 배선/전원 특성 및 `[실측 2026-10-27]` 결과를 하나로 통합 정리.
- `reset_deser_and_init_cameras.sh`: 기존 카메라 서비스/프로세스 정리 및 모듈(`sgx_yuv_gmsl2`, `max96712`) 언로드 -> `test_usb_relay.py`를 통한 12V 전원 차단 -> CSI 역전원 유입 시 `MAX96712` I2C `RESET_ALL`(`0x0013 = 0x40`) 수행 및 레지스터(`0x08A0`, `0x040B`, `0x090B`) 초기화 검증 -> 12V 전원 복구 -> 커널 드라이버 재로드 및 서비스 복구(실패 시 자동 롤백 포함) 스크립트로 업데이트.

### Findings
- 디시리얼라이저 전원 제어는 CH340 USB 시리얼 릴레이(`test_usb_relay.py`, 기본 포트 `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`)를 사용하며 기본 배선은 `NC`(릴레이 ON=전원 OFF, 릴레이 OFF=전원 ON)이다.
- **[실측 2026-10-27 핵심 발견]**: 릴레이로 외부 12V 어댑터만 차단하면 보드 LED와 카메라 PoC 전원은 꺼지지만, `MAX96712` 칩 자체는 Jetson CSI 커넥터를 통해 전원이 유지되어 I2C(`0x6b` reg `0x000d` = `0xa0`)가 살아 있고 기존 설정 레지스터가 초기화되지 않는다.
- 따라서 12V 차단 상태에서 `i2ctransfer -f -y 9 w3@0x6b 0x00 0x13 0x40`(`RESET_ALL`)을 전송해야 설정 레지스터(`0x08A0`, `0x040B`, `0x090B`)가 `[0x84 0x42 0x07]`에서 `[0x04 0x02 0x00]`으로 완전 초기화된다.

### Resolution
- `[0/5]~[5/5]` 단계로 구성된 `reset_deser_and_init_cameras.sh` 스크립트를 업데이트하고 문법 검증을 완료했다:
  0. USB 릴레이 포트 및 `--mode status` 사전 점검
  1. 카메라 점유 서비스(`collector.service` 등) 중지, `/dev/video*` 점유 프로세스 종료 후 `sgx_yuv_gmsl2`, `max96712` 언로드
  2. 릴레이로 12V 차단 후 CSI 역전원 생존 시 I2C `RESET_ALL`(`0x0013 = 0x40`) 실행 및 레지스터 초기화 확인
  3. 릴레이로 12V 복구 및 안정화 대기 (`--reboot` 옵션 시 디시리얼라이저 ON 유지 상태에서 즉시 재부팅)
  4. `max96712.ko` 및 `sgx-yuv-gmsl2.ko` 로드 (중간 실패 시 전원/드라이버/서비스 자동 롤백)
  5. `clock_config.sh`, `v4l2-ctl` 초기화 및 중지했던 서비스 재시작

### Follow-up
- 실제 현장 Jetson 장비에서 `./reset_deser_and_init_cameras.sh` 로 드라이버 재로드만으로 4채널 모두 정상 인식되는지 확인.
- 만약 CSI/I2C 버스 레벨에서 콜드 부트 시퀀스가 필요하면 `./reset_deser_and_init_cameras.sh --reboot` 방식으로 동작 확인 후 `gmsl-driver-load.service` 연동 여부 결정.

### Sensitive Data Policy
- 비밀정보, 토큰, 비밀번호, 개인 데이터는 기록하지 않았다.
