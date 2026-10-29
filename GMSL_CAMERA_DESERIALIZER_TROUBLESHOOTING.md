# GMSL2 카메라 & 디시리얼라이저(MAX96712) 에러 로그 및 트러블슈팅 통합 문서

> **작성일**: 2026-10-27  
> **대상 시스템**: Jetson #1 (볶음/사람감지, 카메라 3대), Jetson #2 (튀김/바켓 AI, 카메라 4대)  
> **환경**: NVIDIA Jetson Orin Nano / JetPack 6.2 (L4T R36.4.3, Kernel `5.15.148-tegra`)  
> **카메라 보드**: SENSING `SG4A-NONX-G2Y-A1` (MAX96712 GMSL2 4-Ch Deserializer)  
> **2026-10-27 실측 보강**: 국물 자동화 젯슨(SG4A 보드, 카메라 1대·포트 0)에서 릴레이 전원 차단 / I2C 칩 리셋을 직접 측정한 결과를 2장·장애 유형 1·7·8·4장에 반영함. 표시: **[실측 2026-10-27]**

---

## 1. 하드웨어 & 통신 구조 요약

| 구성 요소 | 상세 사양 / 주소 | 역할 및 비고 |
| :--- | :--- | :--- |
| **Deserializer 보드** | `SG4A-NONX-G2Y-A1` (`MAX96712`) | GMSL2 4채널 동축 입력 ➔ MIPI CSI 4-lane 변환 (`I2C Bus 9`, 주소 `0x6b`) |
| **Serializer (카메라 내장)** | `MAX9295` / `MAX96717` | 카메라 센서 데이터 직렬화 및 PoC(동축 전원) 수신 (주소 `0x44` 등 — 장비마다 다름. 국물 젯슨 버스 9에서는 `0x42`, `0x50`이 보임) |
| **카메라 센서 드라이버** | `sgx-yuv-gmsl2.ko` | `I2C Bus 9` (`9-001a`~`9-001d`) ➔ `/dev/video0` ~ `/dev/video3` 매핑 |
| **지원 포맷 / 해상도** | `UYVY`, `1920x1536 @ 30fps` | `sensor_mode=1`, `GMSLMODE_1=2,2,2,2` (GMSL2 3Gbps 모드) |
| **디시리얼라이저 전원 릴레이** | CH340 USB-Serial (`1a86:7523`) | 고정 경로: `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` (`9600 8N1`) |

---

## 2. 핵심 전원 법칙 (Power Sequence Rule)

> **[황금 법칙]**  
> **무조건 디시리얼라이저(SG4A 보드 12V)가 먼저 켜져서 안정화된 후 ➔ 젯슨(커널 드라이버/시스템)이 켜져서 초기화해야 한다.**

### 왜 이 순서가 어겨지면 먹통이 되는가?
1. **CSI/I2C 역류(Back-feeding) 및 POR(Power-On Reset) 실패**:
   * 디시리얼라이저 외부 12V 전원이 꺼진 상태에서 젯슨이 먼저 켜지면, 젯슨 CSI 커넥터의 3.3V I2C 풀업/GPIO 신호가 먼저 인가되어 `MAX96712` 칩이 불완전하게 깨어나거나 내부 상태 머신이 꼬입니다.
2. **PoC(Power over Coax) 카메라 부팅 시간 부족**:
   * 디시리얼라이저에 전원이 들어가야 동축케이블을 통해 카메라 4대(Serializer + 센서)로 전원이 공급됩니다. 전원이 동시에 들어가거나 늦게 들어가면 커널 드라이버가 I2C(`0x6b`, `0x1a~0x1d`)를 프로빙할 때 응답하지 못합니다.
3. **USB 릴레이 배선(`NC`) 주의사항**:
   * 기본 배선이 **NC (Normally Closed, 평상시 접점 붙음)** 이므로 명령 의미가 반대입니다.
     * `test_usb_relay.py --mode on --wiring nc` ➔ 접점 단선 ➔ **디시리얼라이저 전원 OFF (차단)**
     * `test_usb_relay.py --mode off --wiring nc` ➔ 접점 도통 ➔ **디시리얼라이저 전원 ON (인가)**
   * **NC 배선의 장점**: 디시리얼라이저를 릴레이로 한 번 리셋해 켜둔 뒤 `sudo reboot`으로 젯슨만 재부팅하면, 젯슨이 재부팅되는 동안에도 디시리얼라이저 전원은 끊기지 않고 계속 켜져 있어 **"디시리얼라이저 먼저 ON ➔ 젯슨 부팅"** 법칙이 성립합니다.
   * **릴레이는 반드시 +선(12V)을 스위칭**: 전원 어댑터 `+` ➔ 릴레이 `COM`, 릴레이 `NC` ➔ 보드 `+` 입력, GND는 직결. GND를 끊으면 MIPI/CSI 케이블의 GND로 전류가 우회해서 **전원이 꺼지지 않습니다**(LED 계속 켜짐) **[실측 2026-10-27]**.

### ⚠️ [실측 2026-10-27] 릴레이 12V 차단으로는 MAX96712 칩이 꺼지지 않는다
* 릴레이로 12V를 차단하면 보드 LED는 꺼지지만, 그 상태에서도 `MAX96712`는 I2C로 계속 응답했습니다 (`i2ctransfer -f -y 9 w2@0x6b 0x00 0x0d r1` ➔ `0xa0`).
* 즉 **12V는 카메라 쪽(PoC) 전원**이고, **칩은 젯슨 CSI 커넥터 쪽 전원으로 계속 살아 있습니다**(위 1번 역류 설명과 같은 경로로 추정).
* 따라서 릴레이 전원 리셋만으로는 **카메라만 리셋되고 디시리얼라이저 칩 내부 상태는 그대로 남습니다.**
* 칩까지 리셋하려면 **I2C 소프트웨어 리셋(RESET_ALL, 레지스터 `0x0013` bit6)** 을 해야 합니다. `reset_deser_and_init_cameras.sh`에 반영 완료(장애 유형 1 참고).
* 같은 이유로 `--reboot` 모드에서 젯슨이 재부팅되면 칩 전원도 함께 흔들릴 수 있으므로, "디시리얼라이저 먼저 ON" 법칙이 기대대로 성립하는지는 장비별로 확인이 필요합니다.

---

## 3. 장애 유형별 에러 로그 원문 및 해결 방법

### 장애 유형 1: 디시리얼라이저 I2C 쓰기 실패 및 GMSL 링크 미형성 (`link:0x00`)

#### 증상
* 부팅 후 또는 운영 중 특정 채널(또는 전체 채널) 카메라 영상이 안 들어오거나 `v4l2-ctl` 스트리밍이 멈춤.
* 소프트 재시작이나 단순 `sudo reboot` 만으로는 복구되지 않음.

#### 실제 에러 로그 (`camera_logs/20260518_154724/dmesg-ramoops-0` 및 현장 `dmesg`)
```text
[2251967.282576] sgx-yuv-gmsl2 9-001a: sensor_set_mode set_mode enter
[2251967.282587] sgx-yuv-gmsl2 9-001a: sensor_set_mode mode_prop_idx= 1/n
[2251967.285732] sgx-yuv-gmsl2 9-001a: link_num = 4 ,lane_rate = 0xf6
[2251967.288084] sgx-yuv-gmsl2 9-001a: sensor_start_streaming enter 11111
[2251967.288957] max96712 9-006b: i2c-w, write failed
[2251967.504755] sgx-yuv-gmsl2 9-001b: sensor_set_mode set_mode enter
[2251967.505983] sgx-yuv-gmsl2 9-001b: link_num = 4 ,lane_rate = 0xf6
[2251967.506758] sgx-yuv-gmsl2 9-001b: sensor_start_streaming enter 11111
[2251967.507206] max96712 9-006b: i2c-w, write failed
[2251967.857032] max96712 9-006b: i2c-w, write failed
[2251968.146457] max96712 9-006b: i2c-w, write failed
```
* 드라이버 로드 시점 링크 트레이닝 실패 시에는 아래 로그가 함께 나타남:
  * `link:0x00`
  * `sensor_probe ... detect error`

> ⚠️ **[실측 2026-10-27] 위 로그만으로 고장을 판단하지 말 것**
> * 카메라가 정상 동작하던 국물 젯슨에서도 5일 동안 `max96712 9-006b: i2c-w, write failed` **1,047건**, `corr_err: discarding frame` **17,922건**이 찍혔습니다(스트림 시작 때마다 발생하는 노이즈).
> * `link:0x00` / `detect error`는 **카메라가 꽂혀 있지 않은 포트에서는 정상**입니다(카메라 1대면 포트 1~3은 항상 이렇게 나옴).
> * 판단 기준은 **실제 프레임 수신 여부**입니다(4장 3) 스트림 검증 명령).

#### 원인
* 디시리얼라이저(`MAX96712`, `9-006b`) 내부 레지스터/I2C 상태가 꼬였거나, 전원 인가 타이밍 문제로 GMSL 링크 트레이닝이 깨진 상태.
* 전원 차단 시간이 짧으면(3초 미만) 보드 내부 캐패시터가 완전 방전되지 않아 리셋이 안 되고, 전원 인가 후 대기 시간이 짧으면(5초 미만) PoC 카메라가 다 올라오기 전에 드라이버가 접근해 다시 꼬임.

#### 해결 방법
* 디시리얼라이저 전원을 **최소 5~8초 완전 차단(방전)** 후 **재인가하고 8~12초 대기**한 뒤 드라이버를 초기화합니다.
* **[실측 2026-10-27]** 릴레이 차단만으로는 칩이 리셋되지 않으므로(2장 ⚠️), 스크립트가 차단 중에 칩 응답을 확인하고 **응답하면 I2C 소프트웨어 리셋(RESET_ALL)** 을 자동 수행합니다.
* 자동화 스크립트 실행 (**sudo 필수** — 릴레이 시리얼 포트·I2C·insmod 권한):
  ```bash
  # [0] 릴레이 응답 점검 -> [1] collector 중지·드라이버 언로드
  # -> [2] 릴레이 12V 차단(5초) + 칩 응답 시 I2C RESET_ALL -> [3] 12V 인가(8초)·칩 응답 확인
  # -> [4] 드라이버 로드 -> [5] 클럭·센서 모드 설정 -> collector 재시작
  sudo ./reset_deser_and_init_cameras.sh

  # 만약 젯슨 본체까지 새로 부팅해야 할 때 (디시리얼라이저 ON 유지한 채 젯슨만 재부팅)
  sudo ./reset_deser_and_init_cameras.sh --reboot
  ```
* **칩 리셋 성공 판정** — 출력에서 아래 줄 확인 (드라이버 설정값 ➔ 기본값으로 돌아가면 리셋된 것):
  ```text
    - 디시리얼라이저 칩은 별도 전원으로 동작 중 → I2C 소프트웨어 리셋(RESET_ALL) 수행
      설정 레지스터(0x08A0 0x040B 0x090B): 리셋 전 [0x84 0x42 0x07] → 리셋 후 [0x04 0x02 0x00]
  ```
  값이 그대로면 `[WARN] 칩 리셋이 적용되지 않았을 수 있습니다`가 출력됩니다.
* 스크립트 안전장치: 릴레이 무응답이면 아무것도 건드리지 않고 종료(`--skip-relay-check`로 무시 가능 — 장애 유형 9 참고) / `/dev/video*` 사용 중 프로세스가 있으면 중단 / `rmmod` 실패·중간 실패 시 드라이버 재로드 + collector 재시작 후 종료.
* ⚠️ 마지막의 `성공 채널: 4/4`는 **v4l2 제어값 설정 성공 개수**일 뿐 영상 수신 여부가 아닙니다. 반드시 4장 3) 스트림 검증으로 확인하세요.

---

### 장애 유형 2: VI 캡처 타임아웃 (`uncorr_err`) 및 에러 복구 중 커널 패닉 (`Oops`)

#### 증상
* 카메라 프레임이 멈추면서 `dmesg`에 2.5초마다 `uncorr_err: request timed out after 2500 ms`가 무한 출력됨.
* 심한 경우 에러 복구(`vi5_channel_error_recover`) 도중 커널 패닉(`Internal error: Oops`)이 발생하며 시스템이 뻗음.

#### 실제 에러 로그 (`issues/2025-12-18_jetson2_camera_freezing.md`, `command.txt`, `dmesg-ramoops-0`)
```text
[  288.113935] tegra-camrtc-capture-vi tegra-capture-vi: uncorr_err: request timed out after 2500 ms
[  288.113952] tegra-camrtc-capture-vi tegra-capture-vi: err_rec: attempting to reset the capture channel
[  288.114043] tegra194-vi5 13e00000.host1x:vi1@14c00000: vi_capture_release: control failed, errno 1
[  288.114099] video4linux video0: vi capture release failed
[  288.114103] tegra-camrtc-capture-vi tegra-capture-vi: fatal: error recovery failed
```
* 장기 타임아웃 누적 후 커널 크래시 로그 (`camera_logs/20260518_154724/dmesg-ramoops-0`):
```text
[2252100.587571] CPU: 2 PID: 2479650 Comm: vi-output, sgx- Tainted: G           OE     5.15.148-tegra #1
[2252100.587670]  vi5_channel_error_recover+0x15c/0x250 [tegra_camera]
[2252100.587688]  tegra_channel_error_recover+0x80/0xa0 [tegra_camera]
[2252100.999795] tegra-camrtc-capture-vi tegra-capture-vi: fatal: error recovery failed
[2252101.027986] Internal error: Oops: 0000000096000047 [#1] PREEMPT SMP
```

#### 원인
1. `max96712`에서 MIPI CSI 프레임 공급이 끊기거나 4개 카메라가 동시에 초기화되면서 Camera RTCPU(IVC 채널)와 VI(Video Input) 사이에 타임아웃 발생.
2. NVIDIA `tegra_camera` 드라이버가 채널 리셋(`vi5_channel_error_recover`)을 시도하다가 이미 꼬인 하드웨어 상태와 충돌하여 `fatal: error recovery failed` 및 커널 스핀락/포인터 Oops 발생.

#### 해결 방법
1. 카메라 오픈 시 4대를 동시에 열지 않고 **초기화 딜레이(`CAMERA_INIT_DELAY = 4.0`초)** 적용 (`bb67d93`).
2. `NVCSI` 클럭 고정 확인 (`clock_config.sh`: `/sys/kernel/debug/bpmp/debug/clk/nvcsi/rate = 214300000`).
3. 일단 `fatal: error recovery failed`가 발생하면 소프트 재시작으로는 VI 채널이 살아나지 않으므로 **디시리얼라이저 전원 리셋 + 재부팅** 수행.

---

### 장애 유형 3: 48시간 이상 장기 구동 후 카메라 멈춤 (DMABUF `io-mode=4` vs MMAP `io-mode=2`)

#### 증상
* 부팅 직후에는 4채널 모두 완벽히 동작하나, 24~48시간 이상 연속 구동하면 GStreamer 파이프라인이 타임아웃을 내며 멈춤 (`work-notes/2026-04-20-jetson-camera-debug.md`).

#### 원인
* GStreamer `v4l2src`에서 `io-mode=4` (DMABUF)를 사용할 경우 커널 내부에서 `dma_alloc_coherent()`를 통해 **연속된 물리 메모리(CMA, 기본 약 256MB)**를 요구함.
* `1920x1536` 4채널을 며칠간 계속 돌리면 CMA 물리 메모리가 단편화(Fragmentation)되어 연속된 큰 블록 할당에 실패하고 드라이버가 멈춤.

#### 해결 방법
* `jetson1_monitoring/gst_camera.py` 및 `jetson2_frying_ai/gst_camera.py`에서 V4L2 버퍼 모드를 **`io-mode=2` (MMAP)**로 변경 (`17ab23a`).
* MMAP은 가상 메모리 매핑을 사용하므로 물리 메모리가 쪼개져 있어도 일반 RAM을 활용해 24/7 장기 구동 시 메모리 단편화로 죽지 않음.
  ```bash
  v4l2src device=/dev/video0 io-mode=2 ! video/x-raw,format=UYVY,width=1920,height=1536,framerate=30/1 ! ...
  ```

---

### 장애 유형 4: 커널 모듈 심볼 버전 불일치로 `/dev/video0~3` 미생성

#### 증상
* 앱 실행 시 모든 카메라가 5초 뒤 `no frames received`를 출력하며 재시도만 반복함.
* `ls -l /dev/video*` 실행 시 디바이스 노드가 아예 없음 (`/dev/media0`만 존재).

#### 실제 에러 로그 (`work-notes/2026-04-22-1005-gmsl-camera-dropout-root-cause.md`, `app_logs/app_2026-04-22.jsonl`)
* **앱 로그 (`app_2026-04-22.jsonl`)**:
  ```json
  {"timestamp": "2026-04-22 09:11:16.636", "level": "STDOUT", "message": "[GstCamera] Camera 0 - no frames received"}
  {"timestamp": "2026-04-22 09:11:16.943", "level": "STDOUT", "message": "[CAM0] Start failed (attempt 3/5)"}
  ```
* **커널 로그 (`journalctl -k`)**:
  ```text
  sgx_yuv_gmsl2: disagrees about version of symbol tegracam_v4l2subdev_unregister
  sgx_yuv_gmsl2: Unknown symbol tegracam_v4l2subdev_unregister (err -22)
  sgx_yuv_gmsl2: disagrees about version of symbol tegracam_get_sdata
  sgx_yuv_gmsl2: Unknown symbol tegracam_get_sdata (err -22)
  ```

#### 원인
* `sgx-yuv-gmsl2.ko` 드라이버와 현재 커널에 로드된 `tegra-camera.ko` 모듈의 ABI/심볼 버전이 맞지 않아 `insmod sgx-yuv-gmsl2.ko`가 실패함.
* 기존 `init_gmsl_cameras.sh`는 `insmod` 반환값을 체크하지 않고 무조건 `"로드 완료"`를 출력하는 버그가 있어 원인 파악이 늦어짐.

#### 해결 방법
* 제조사 드라이버 폴더(`SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3`)의 `install.sh`가 복사하는 세트가 세트로 맞아야 함:
  ```bash
  cd ~/jetson-food-ai/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3
  sudo ./install.sh
  sudo depmod -a
  sudo reboot
  ```

---

### 장애 유형 5: 앱 내부 Camera Watchdog의 자동 재초기화(`gmsl_reinit`) 부작용

#### 증상
* 카메라 1대가 일시적으로 멈췄을 때 웹 앱(`JETSON1_web.py`, `JETSON2_web.py`)의 Watchdog 스레드가 자동으로 `init_gmsl_cameras.sh` 및 파이프라인 재시작을 호출하면서 오히려 나머지 정상 카메라까지 전부 죽어버림 (`work-notes/2026-04-24-0045-disable-camera-watchdog-jetson2.md`).

#### 해결 방법
* GMSL2 4채널은 공유 Deserializer(`MAX96712`)에 묶여 있으므로 런타임 소프트 재초기화 대신 Watchdog을 기본 비활성화 (`8f192fe`):
  * `config_jetson1_web.json` / `config_jetson2_web.json`: `"camera_watch_enabled": false`

---

### 장애 유형 6: USB 시리얼 릴레이(`test_usb_relay.py`) 첫 명령 씹힘 현상

#### 증상
* `test_usb_relay.py`를 실행했을 때 `[OK] Serial port opened`는 뜨지만 실제 릴레이가 딸깍거리지 않고 첫 명령이 유실됨 (`work-notes/2026-05-18-1613-usb-relay-init.md`).

#### 원인
* CH340 USB-Serial 포트를 여는 순간 DTR/RTS 신호 변화나 릴레이 보드 MCU 초기화 시간 때문에 포트 오픈 직후 바로 `ser.write()`를 호출하면 첫 패킷이 무시됨.

#### 해결 방법
* `test_usb_relay.py`에 포트 오픈 직후 DTR/RTS 비활성화, 초기 대기(`--init-delay 1.5~2.5`), 버퍼 초기화, 반복 전송(`--retries 3~5`) 적용 완료:
  * ON/OFF는 절대 상태 명령이라 `--retries` 횟수만큼 같은 프레임을 반복 전송 (2026-10-27부터. 이전에는 쓰기 예외 때만 재시도해 사실상 1회 전송이었음).
  * 상태 조회(`--mode status`)는 `CH1: ON/OFF` 형식 응답이 올 때까지 최대 `--retries`회 재질의, 잡음 바이트는 응답으로 인정하지 않음.
  * `--mode test`(기본값) ON 전송·대기 중 Ctrl-C/SIGTERM/SSH 끊김이 와도 릴레이 OFF를 보내고 종료 (NC 배선에서 12V 차단 상태로 남지 않음). `nohup` 등으로 무시(SIG_IGN)된 신호는 그대로 무시하고 명령을 끝까지 전송.
  ```bash
  python3 test_usb_relay.py --mode on --wiring nc --init-delay 2.0 --retries 5
  ```

---

### 장애 유형 7: USB 릴레이가 인식되지 않음 (`/dev/serial/by-id/` 없음) **[실측 2026-10-26]**

#### 증상
* `test_usb_relay.py` 실행 시 `could not open port ... No such file or directory`.
* `lsusb`에는 `1a86:7523 QinHeng Electronics CH340 serial converter`가 보이는데 `/dev/ttyUSB0`가 없거나, 잠깐 생겼다가 사라짐.

#### 원인 및 해결 (순서대로 확인)
| 원인 | 확인 방법 | 해결 |
| :--- | :--- | :--- |
| JetPack 6.2 커널에 **CH341 드라이버가 없음** (`# CONFIG_USB_SERIAL_CH341 is not set`) | `zcat /proc/config.gz \| grep CH341` | 같은 커널 버전 소스로 `ch341.ko` 빌드 후 설치 (아래) |
| **brltty**(점자 디스플레이 프로그램)가 CH340을 점자기기로 인식해 포트를 가로챔 | `ttyUSB0`가 생겼다 바로 사라짐, `pgrep brltty` | `sudo apt-get remove -y brltty` 후 릴레이 USB 재연결 |
| **pySerial 미설치** | `python3 -c "import serial"` | `sudo apt-get install -y python3-serial` |
| 시리얼 포트 권한 | `id -nG \| grep dialout` | `sudo usermod -aG dialout $USER` (재로그인) 또는 스크립트를 `sudo`로 실행 |
| I2C 도구 미설치 (칩 리셋에 필요) | `which i2ctransfer` | `sudo apt-get install -y i2c-tools` |

* `ch341.ko` 빌드·설치 (커널 헤더와 gcc는 JetPack에 포함, 인터넷 필요):
  ```bash
  mkdir -p ~/ch341-driver && cd ~/ch341-driver
  curl -fsSL -o ch341.c https://raw.githubusercontent.com/gregkh/linux/v5.15.148/drivers/usb/serial/ch341.c
  echo 'obj-m += ch341.o' > Makefile
  make -C /lib/modules/$(uname -r)/build M=$PWD modules
  sudo mkdir -p /lib/modules/$(uname -r)/extra
  sudo cp ch341.ko /lib/modules/$(uname -r)/extra/
  sudo depmod -a
  sudo modprobe ch341
  ls -l /dev/serial/by-id/      # usb-1a86_USB_Serial-if00-port0 -> ../../ttyUSB0
  ```
  * 커널 버전(`uname -r`)이 `5.15.148-tegra`로 같으면 빌드된 `ch341.ko`를 다른 젯슨에 그대로 복사해 써도 됩니다.
  * **커널 업데이트·재플래시 후에는 다시 빌드**해야 합니다. 서명 없는 모듈이라 `module verification failed` 경고가 나오지만 정상 로드됩니다.
* 동작 확인: `sudo python3 test_usb_relay.py --mode status` ➔ `CH1: OFF` (NC 배선이면 전원 인가 상태)

---

### 장애 유형 8: 카메라 영상이 초록색으로 나옴 (울산 현장)

#### 증상
* 스트림은 열리고 프레임도 들어오지만 화면 전체(또는 대부분)가 초록색.

#### 원인 (추정)
* `UYVY` 포맷에서 데이터가 전부 `0`이면 초록색으로 보입니다. 즉 **링크·스트림은 살아 있으나 실제 영상 데이터가 비어 있는 상태**입니다.
* 디시리얼라이저 칩 내부 상태(MIPI 출력·영상 파이프 매핑)가 꼬였을 가능성이 큽니다. 릴레이 12V 리셋만으로는 칩이 리셋되지 않으므로(2장 ⚠️) 그동안 복구가 안 됐을 수 있습니다.
* 케이블·카메라·CSI 쪽 원인도 배제되지 않았습니다 — **현장 검증 전**.

#### 해결 방법 (현장 검증 절차)
1. 초록 화면 상태에서 `sudo ./reset_deser_and_init_cameras.sh` 실행.
2. 출력에 `리셋 후 [0x04 0x02 0x00]`이 나오는지 확인 ➔ 칩 리셋 확인.
3. 4장 3) 스트림 검증 + 실제 영상 확인 ➔ 초록색이 사라지면 칩 상태 문제로 확정.
4. 그래도 초록색이면 칩 문제가 아니므로 동축 케이블·커넥터·카메라 교체 순으로 점검.

---

### 장애 유형 9: 카메라 3대 `Frame stalled` 2시간 지속 — 릴레이 무응답 상태에서 I2C 칩 리셋만으로 복구 **[실측 2026-10-27, 울산 Jetson #2]**

#### 증상
* `jetson2-web` 로그에 CAM1~3 `Frame stalled`가 5초 간격으로 반복, 경과 시간이 계속 증가 (14:55 기준 약 7760초 → 12:46경부터 정지).
  ```text
  [CAM1] Frame stalled (7764.3s since last unique frame, same_count=5710)
  [CAM2] Frame stalled (7749.7s since last unique frame, same_count=5627)
  [CAM3] Frame stalled (7749.8s since last unique frame, same_count=5701)
  ```
* camera stall watchdog이 기본 비활성(장애 유형 5)이라 자동 복구 없이 로그만 쌓임.

#### 복구 중 만난 문제
1. **sudo에서 pySerial 미검출**: `[ERROR] pySerial import failed: No module named 'serial'`
   * 원인: pyserial이 사용자 경로(`~/.local/lib/python3.10/site-packages`)에만 설치되어 root에서 안 보임.
   * 해결(설치 없이): `sudo env PYTHONPATH=$HOME/.local/lib/python3.10/site-packages ...` — 스크립트 내부 `python3` 호출에도 상속됨. 영구 해결은 `sudo apt-get install -y python3-serial`.
2. **USB 릴레이 상태 조회 무응답**: 포트(`ttyUSB0`, CH340, USB 경로 `1-2.2`)는 열리지만 `Status response: (no response)`. `--init-delay 3`으로도 동일.
   * 다른 젯슨에서 같은 모델이 `CH1: OFF`로 응답하므로 모델 문제는 아님. 보드 MCU 멈춤/접촉 불량 의심, 현장 확인 필요.
   * 2026-10-29 현장 확인: USB는 정상 체결, `칩 리셋 (릴레이 무시)` 실행 중에도 **딸깍 소리 없음** → 차단/인가 명령도 동작하지 않음 (상태 응답만의 문제가 아님). USB 재체결로도 안 되면 릴레이 보드 교체 필요. 교체 전까지는 12V 차단 없이 I2C 칩 리셋만으로 운영 (NC 배선이라 12V는 계속 인가, 10-29 기준 칩 리셋만으로 복구 정상).
   * 진동센서는 FTDI(`ttyUSB1`)이며 `jetson2-web`이 사용 중 — 포트 충돌 없음.

#### 해결
```bash
cd ~/jetson-food-ai
sudo env PYTHONPATH=$HOME/.local/lib/python3.10/site-packages ./reset_deser_and_init_cameras.sh --skip-relay-check
```
* 출력: `리셋 전 [0x84 0x42 0x07] → 리셋 후 [0x04 0x02 0x00]`, 칩 ID `0xa0`, `/dev/video0~3` 설정 4/4.
* 서비스 재시작 후 `Camera 0~3 started successfully`, Observe AI `cam2/cam3 status_change (INIT → NO_BASKET)` → 프레임 수신 확인.
* 릴레이가 실제로 동작하지 않아도 위험 없음: 릴레이 명령은 시리얼 쓰기만 성공하고 넘어가며, 결과적으로 **12V 차단 없이 RESET_ALL + 드라이버 재로드**만 수행됨. NC 배선이라 릴레이가 멈추거나 USB를 뽑아도 12V는 인가 상태.
* `--skip-relay-check`는 릴레이 포트가 없거나 릴레이 스크립트가 실패해도(pySerial 없음 등) 릴레이 명령을 빼고 I2C 리셋을 계속함. 기본 모드는 이런 경우 아무것도 바꾸지 않고 종료코드 `10`으로 중단.
* 12V 차단 명령을 보낸 뒤 인가 명령이 실패하면 3회 재시도하고, 그래도 실패하면(`--skip-relay-check` 포함) 복구 경로에서 한 번 더 인가한 뒤 실패(`1`)로 종료 — 12V가 끊긴 채 끝나지 않게 함.
* 릴레이 상태 응답은 `CH1: OFF`/`CH1:OFF` 처럼 공백 유무와 관계없이 인식.
* 수동 실행 중 Ctrl-C나 SSH 끊김이 와도 12V 인가 → 드라이버 재로드 → 중지했던 서비스 재시작을 자동으로 수행함 (약 30초, 복구 중 추가 Ctrl-C·끊김 신호는 무시, 복구 출력: `/tmp/deser_reset_interrupted.log`). `nohup`으로 실행하면 SSH가 끊겨도 리셋이 끝까지 진행됨. `kill -9`로 강제 종료한 경우에는 다시 실행한 뒤 `systemctl is-active jetson2-web`으로 웹이 떠 있는지 확인.
* 대시보드 작업과 같은 잠금(`/run/deser-control/lock`)을 써서, 대시보드 리셋이 도는 중에는 수동 실행이 거부됨 (반대도 같음).
* 성공 판정: 리셋 전에 있던 `/dev/video*` 노드가 모두 다시 설정되어야 종료코드 `0`, 일부만 돌아오면 실패(`1`). 리셋 전 노드가 없었으면(드라이버 미로드) `EXPECTED_CAMERAS`(기본 4, Jetson #1은 3으로 설정) 기준. 노드 설정 기준이므로 실제 프레임 수신은 대시보드 상태(`정상 N fps`)나 스크립트 끝에 출력되는 `v4l2-ctl --stream-mmap` 명령으로 확인.
* 장비별 설정 파일 `/etc/default/deser-control`(`WIRING`, `RELAY_PORT`, `I2C_BUS`, `EXPECTED_CAMERAS` 등, `KEY=값`)은 대시보드와 수동 실행 모두 적용. 우선순위: CLI 인자 > 환경변수 > 설정 파일 > 기본값.

#### 웹 대시보드에서 실행 (Jetson #2, 2026-10-27 추가)
* 카메라 상태 표시: 새 프레임이 5초 이상 없으면 주황 `변화 없음`, 30초(`camera_stall_alert_sec`) 이상이면 빨강 `멈춤` + 상단 경고 줄에 리셋 버튼. 카메라 스레드가 시작 재시도에 모두 실패하면 `시작 실패`.
* 버튼: `칩 리셋` / `칩 리셋 (릴레이 무시)` / `릴레이 상태`. 리셋 중에는 경고 줄이 라벤더색 `카메라 복구 진행 중`으로 바뀌고, 웹이 재시작되면 카메라 영상이 자동으로 다시 연결됨 (다른 화면·키오스크 포함).
* 최초 1회 설치 (웹 서비스 사용자 계정으로, sudo 없이 실행 → 내부에서 sudo 비밀번호 요청). **이 스크립트가 바뀐 버전을 받은 뒤에도 한 번 다시 실행** (systemd 유닛 갱신):
  ```bash
  cd ~/jetson-food-ai
  git status -s            # 로컬 수정 확인 (vibration_config.json 같은 장비별 설정은 그대로 둠)
  git pull                 # 'local changes would be overwritten' 으로 멈추면: git stash && git pull && git stash pop
  ./install_deser_control.sh
  sudo systemctl restart jetson2-web     # 튀김/바켓 AI 약 1분 중단 → 조리가 없는 시간에
  until curl -fsS http://127.0.0.1:8000/ >/dev/null; do sleep 2; done; echo 웹 준비됨
  # 그다음 이미 열려 있는 대시보드/키오스크 화면을 F5 로 새로고침
  ```
  * `git checkout .` / `git reset --hard` 로 정리하지 말 것 — 장비별 `vibration_config.json` 튜닝이 지워짐.
  * pull → install → restart 를 바로 이어서 실행 (pull 과 restart 사이에는 옛 서버가 새 화면을 내보내 복구 버튼이 `미설치`로 보일 수 있음).
  * 설치 스크립트의 릴레이 확인에서 `(no response)` / `failed, rc=4` 가 나와도 설치는 정상 (`시작: relay-status` 줄이 있으면 sudo·서비스 동작 확인됨).
* 구조: 버튼 → `sudo -n systemctl start --no-block deser-control@<동작>.service` (sudoers 에 이 3개만 허용) → root 로 `deser_control.sh` 실행. 리셋이 `jetson2-web` 을 중지해도 별도 서비스라 끝까지 진행되고 웹은 자동 재시작됨.
* 결과 표시: `성공` / `중단 — 변경 없음`(사전 점검에서 멈춤, 릴레이 무응답·포트 없음·릴레이 스크립트 실패면 `칩 리셋 (릴레이 무시)` 사용 안내) / `실패` / `시작 실패`(유닛이 실행되지 못함 → `journalctl -u deser-control@<동작>`). 다른 화면·기기에서 시작한 작업도 따라가서 결과를 표시. 웹이 10분 넘게 돌아오지 않으면 `대시보드 서버 응답 없음` → SSH로 `jetson2-web` 확인.
* 쿨다운: **성공한 리셋** 후 300초(`camera_recovery_cooldown_sec`, 표시: `칩 리셋 재시도 N초 후`). 중단·실패한 리셋과 `릴레이 상태` 조회는 쿨다운을 만들거나 지우지 않음 → 릴레이 무응답으로 `칩 리셋`이 중단되면 바로 `칩 리셋 (릴레이 무시)` 가능. 시계가 뒤로 보정되면 쿨다운은 해제됨.
* 안전장치: 리셋이 중간에 끊겨도(systemd 중지·타임아웃) 리셋 스크립트가 12V 인가 → 드라이버 재로드 → 서비스 재시작을 수행하고, 그래도 상태가 `running`으로 남으면 `ExecStopPost`가 실패로 정리함. 신호·타임아웃으로 끊긴 리셋 뒤 `jetson2-web`이 꺼져 있으면 `ExecStopPost`가 다시 시작 (정상 종료한 실패는 리셋 스크립트가 이미 서비스를 되살리므로 건드리지 않음). 커널에서 멈춘 경우(SIGKILL)는 웹만 되살리고 드라이버·릴레이는 복구하지 못함 → SSH로 수동 리셋.
* 장비별 설정: 배선/포트/버스가 기본값(nc, CH340 by-id, I2C bus 9)과 다르거나 카메라가 4대가 아니면 `/etc/default/deser-control`에 `WIRING=no`, `RELAY_PORT=...`, `I2C_BUS=...`, `EXPECTED_CAMERAS=3` 형식으로 적어 둠 (터미널 수동 실행도 같은 파일을 읽음).
* 진행 로그: 대시보드 `Log` 버튼(카메라 복구 줄 바로 아래), 또는 `/run/deser-control/<동작>.log`. 상태 파일: `state.json`(마지막 작업), `last_reset.json`(마지막 성공 리셋, 쿨다운 기준).

#### 발생 기록과 자동 복구 (2026-10-28 추가, 울산 `app_logs` 분석)
* 멈춤은 **스스로 풀리지 않음** — 기록된 모든 건이 2~16시간 지속되다가 사람이 끄거나 칩 리셋할 때 끝남.
  | 날짜 | 시작 | 카메라 | 끝 |
  |---|---|---|---|
  | 2026-09-14 | (전날부터) | CAM1 | 18:20 |
  | 2026-09-15~18 | **매일 02:02~02:03** | CAM1~3 | 06:04 / 09:15 / 11:23 / 12:52 (재시작할 때까지) |
  | 2026-10-27 | 12:46 | CAM1~3 | 15:19 칩 리셋 |
  | 2026-10-28 | 10:33 | CAM1만 | 18:32 칩 리셋 → 정상 |
* 9월 패턴은 **새벽 2시 웹 재시작 타이머 직후** 시작 — 웹만 재시작하면서 카메라를 다시 열 때 칩이 꼬인 것으로 봄 (9/19 이후·10/28 02:00 재시작에서는 재현 안 됨).
* 10/28 멈춤 중 `same_count=0` (프레임 자체가 안 들어옴), `dmesg`에 `tegra-capture-vi: corr_err: discarding frame` 반복. 리셋 후 카메라는 정상이지만 `corr_err`는 가끔 계속 발생(어느 채널인지는 표시 안 됨) → 링크 신호 품질 계속 관찰.
* 울산 젯슨은 저널이 메모리에만 저장(`/var/log/journal` 없음)되어 지난 커널 로그가 남지 않음. 영구 저장: `sudo mkdir -p /var/log/journal && sudo systemctl restart systemd-journald`.
* 멈춤 기록 확인 명령 (`jetson2_frying_ai/app_logs`에서):
  ```bash
  grep -h 'Frame stalled ([5-9]\.' app_*.jsonl \
    | sed -E 's/^\{"timestamp": "([0-9-]+ [0-9:]{5}).*\[CAM([0-9])\].*/\1 CAM\2/' | uniq | tail -40
  ```
* **자동 복구** (`web/auto_recovery.py`, `config_jetson2_web.json`의 `camera_auto_recovery_*`):
  * 카메라 1대라도 내용이 바뀐 프레임이 `camera_auto_recovery_stall_sec`(60초) 넘게 없고, 같은 프레임도 초당 5장 미만이면 `camera_auto_recovery_action`(`reset-skip-relay`) 자동 실행. 불 꺼진 밤처럼 화면만 안 변하고 프레임은 들어오면 실행 안 함.
  * 웹 시작 후 30초 유예, 시작 재시도에 실패한 카메라(`시작 실패`)는 대상 아님.
  * 한도: 1시간 3회, 24시간 6회 (`~/.cache/jetson2_auto_recovery.json`에 기록, 웹 재시작 후에도 유지). 한도에 걸리면 자동 실행을 멈추고 대시보드에 `자동 복구 멈춤 … 수동 점검 필요` → 케이블·커넥터·카메라 점검.
  * 성공한 리셋 후 쿨다운(300초) 동안은 기다렸다가 다시 시도. 대시보드 `카메라 복구` 제목 옆에 상태 표시, 자동 리셋이 시작되면 진행 상황을 따라감.
  * 끄기: `"camera_auto_recovery_enabled": false`.
* **새벽 2시 타이머**: `install_deser_control.sh`가 `jetson2-web-restart.service`(또는 `jetson1-web-restart`)에 drop-in(`…service.d/deser-reset.conf`)을 넣어 웹 재시작 대신 `deser-control@reset-skip-relay`(웹 중지 → 칩 리셋 → 드라이버 재로드 → 웹 시작) 실행. 확인: `systemctl cat jetson2-web-restart.service`. 되돌리기: drop-in 삭제 후 `sudo systemctl daemon-reload`.

#### 미확정 사항
* 이번에 릴레이가 실제로 12V를 끊었는지 모름(칩은 12V 차단 중에도 응답하므로 출력으로 구분 불가). 따라서 "**칩 리셋만으로 stall 복구 가능**"은 유력하지만 확정 아님.
* 확정 방법: (1) 현장에서 실행 중 릴레이 딸깍 소리/보드 LED 소등 확인, (2) 12V 차단 중 I2C bus 9에서 시리얼라이저(`0x44`)·카메라(`0x1a~0x1d`) 소멸 여부 확인, (3) 다음 stall 때 릴레이 없이 RESET_ALL만 수행해 비교.
* 카메라 센서/시리얼라이저 자체가 멈춘 경우(VI `fatal: error recovery failed` 등)는 12V(PoC) 차단이 필요할 수 있음.

### 참고: I2C 칩 리셋(RESET_ALL) 원리
* 명령: `i2ctransfer -f -y 9 w3@0x6b 0x00 0x13 0x40` — 버스 9, 칩 주소 `0x6b`, 16비트 레지스터 `0x0013`에 `0x40`(bit6 = RESET_ALL) 쓰기. `-f`는 드라이버가 주소를 점유 중이어도 강제 접근.
* 칩이 모든 레지스터를 기본값으로 되돌리고 링크 상태 머신을 재시작하며, 비트는 자동 해제(self-clearing).
* 정상 설정까지 지워지므로 반드시 **드라이버 언로드 → RESET_ALL → 드라이버 재로드(링크·MIPI 재설정)** 순서로 수행.
* 12V 차단은 카메라(PoC)만 리셋하고 칩은 CSI 쪽 전원으로 살아 있음(2장 ⚠️). 칩 상태 꼬임에는 RESET_ALL이 핵심.

---

## 4. 현장 점검 및 복구 명령어 요약 (Cheatsheet)

### 1) 하드웨어 / 시리얼 / I2C 인식 확인
```bash
# 1. USB 릴레이(1a86) 및 진동센서(FTDI) 시리얼 고정 경로 확인
ls -l /dev/serial/by-id/

# 2. I2C Bus 9에서 디시리얼라이저(0x6b), 시리얼라이저(0x44), 카메라(0x1a~0x1d) 응답 확인
sudo i2cdetect -r -y 9

# 3. 커널 모듈 및 비디오 디바이스 확인
lsmod | grep -E "max96712|sgx_yuv_gmsl2|tegra_camera"
ls -l /dev/video*

# 4. 커널 카메라 에러 실시간 확인 (i2c-w write failed / corr_err 는 정상 동작 중에도 나옴 — 장애 유형 1 참고)
sudo dmesg -T | grep -iE "max96712|sgx|gmsl|uncorr_err|tegracam|link:" | tail -n 50

# 5. 디시리얼라이저 칩 응답 확인 (0xa0 = MAX96712 응답, 드라이버 로드 중에도 -f 로 읽기 가능)
sudo i2ctransfer -f -y 9 w2@0x6b 0x00 0x0d r1

# 6. 릴레이 상태 확인 (전원은 바꾸지 않음)
sudo python3 test_usb_relay.py --mode status
```

### 2) 디시리얼라이저 선(先)전원 인가 후 초기화 실행
```bash
cd ~/jetson-food-ai

# (국물 자동화 젯슨은 홈 디렉터리 ~/ 에 위치)

# 방법 A: 드라이버 언로드 -> 12V OFF(5초) + 칩 I2C 리셋 -> 12V ON(8초) -> 드라이버 로드 및 초기화
sudo ./reset_deser_and_init_cameras.sh

# 방법 B: 디시리얼라이저를 먼저 깨끗하게 켠 상태(ON 유지)로 만들고 젯슨만 재부팅
sudo ./reset_deser_and_init_cameras.sh --reboot
```

### 3) 개별 카메라 스트림 정상 여부 단독 검증 (`v4l2-ctl`)
> ⚠️ **[실측 2026-10-27]** `--set-fmt-video` 없이 `--stream-mmap`만 하면 정상 카메라에서도 프레임이 안 와서 타임아웃이 납니다. 포맷을 반드시 지정하세요. 다른 프로그램(collector, 웹 앱)이 카메라를 쓰고 있으면 먼저 중지해야 합니다.
```bash
for dev in 0 1 2 3; do
    echo "=== Testing /dev/video${dev} ==="
    v4l2-ctl -d /dev/video${dev} --set-ctrl bypass_mode=0,sensor_mode=1
    timeout 15 v4l2-ctl -d /dev/video${dev} \
        --set-fmt-video=width=1920,height=1536,pixelformat=UYVY \
        --stream-mmap=4 --stream-count=60 --stream-to=/dev/null
done
# '<<<<' 가 60개 찍히면 정상. 타임아웃(Terminated)이면 해당 포트 영상 없음.
```

* 국물 자동화 젯슨에서는 collector 점검 도구가 더 자세합니다 (프레임 수·빠진 프레임·오류 플래그·빈 프레임):
  ```bash
  cd ~/customfood-soup-automation/jetson/collector
  ~/collector-venv/bin/python tools/v4l2_check.py --device /dev/video0 --frames 90
  # 정상 기준: "frames": 90, "seq_gaps": 0, "timeouts": 0, "blank_frames": 0 (error_flags 0~2는 이 장비 평상시 수준)
  ```

---

## 5. 관련 원본 로그 및 문서 파일 색인

* **국물 자동화 젯슨 (2026-10-26~27 실측 작업)**
  * `~/reset_deser_and_init_cameras.sh` (릴레이 + I2C 칩 리셋 통합 스크립트, 원본 백업 `.bak.20261026`)
  * `~/test_usb_relay.py` (CH340 릴레이 제어)
  * `~/ch341-driver/` (`ch341.c`, `ch341.ko`, `Makefile` — 커널 `5.15.148-tegra`용)
  * `/etc/systemd/system/sensing-gmsl.service` (부팅 시 SG4A 드라이버 insmod + NVCSI 클럭 고정)

* **트러블슈팅 노트 (`work-notes/`)**
  * `/home/youngjin/jetson_backup/work-notes/2026-04-20-jetson-camera-debug.md` (DMABUF vs MMAP)
  * `/home/youngjin/jetson_backup/work-notes/2026-04-22-1005-gmsl-camera-dropout-root-cause.md` (`tegracam_*` 심볼 불일치 및 `no frames received`)
  * `/home/youngjin/jetson_backup/work-notes/2026-04-24-0045-disable-camera-watchdog-jetson2.md` (Watchdog 비활성화)
  * `/home/youngjin/jetson_backup/work-notes/2026-05-18-1613-usb-relay-init.md` (USB 릴레이 초기화 딜레이 보강)
* **프로젝트 이슈 문서 (`jetson-food-ai/`)**
  * `/home/youngjin/jetson_backup/jetson-food-ai/issues/2025-12-18_jetson2_camera_freezing.md` (VI 캡처 타임아웃 / IVC 과부하)
  * `/home/youngjin/jetson_backup/jetson-food-ai/CAMERA_FREEZING_ISSUE_2026-01-20.md` (GStreamer 다운스케일 타이밍 이슈)
  * `/home/youngjin/jetson_backup/jetson-food-ai/docs/GMSL_Camera_Architecture.md` (GMSL 아키텍처 전반)
* **원본 커널/앱 에러 로그**
  * `/home/youngjin/jetson_backup/camera_logs/20260518_154724/dmesg-ramoops-0` (`max96712 i2c-w write failed` 및 커널 패닉 로그)
  * `/home/youngjin/jetson_backup/dmesg_live.log` (실시간 커널 로그 백업)
  * `/home/youngjin/jetson_backup/dump_regs.log` (I2C 버스 및 레지스터 덤프)
  * `/home/youngjin/jetson_backup/jetson-food-ai/jetson2_frying_ai/app_logs/app_2026-04-22.jsonl` (웹 앱 카메라 시작 실패 로그)
