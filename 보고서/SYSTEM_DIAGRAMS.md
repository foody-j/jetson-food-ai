# 시스템 다이어그램 모음

본 문서는 Jetson Food AI 시스템의 주요 다이어그램을 포함합니다.

---

## 1. 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "Jetson #1 - 사람감지/볶음"
        J1[Jetson Orin Nano #1]
        CAM1[GMSL 카메라 #1<br/>사람 감지]
        CAM2[GMSL 카메라 #2<br/>볶음 좌측]
        CAM3[GMSL 카메라 #3<br/>볶음 우측]
        YOLO1[YOLO 사람감지<br/>yolo12n.pt]
        GPIO1[GPIO Pin 29,31<br/>릴레이 제어]
        VIB1[진동센서<br/>USB-RS485]

        CAM1 --> YOLO1
        CAM2 --> J1
        CAM3 --> J1
        YOLO1 --> J1
        J1 --> GPIO1
        VIB1 --> J1
    end

    subgraph "Jetson #2 - 튀김/바켓"
        J2[Jetson Orin Nano #2]
        CAM4[GMSL 카메라 #1<br/>튀김 좌측]
        CAM5[GMSL 카메라 #2<br/>튀김 우측]
        CAM6[GMSL 카메라 #3<br/>바켓 좌측]
        CAM7[GMSL 카메라 #4<br/>바켓 우측]
        FRYING[튀김 AI<br/>frying_seg_v3.pt]
        OBSERVE[바켓 AI<br/>observe_add]
        GPIO2[GPIO Pin 29,31<br/>릴레이 제어]
        VIB2[진동센서<br/>USB-RS485]

        CAM4 --> FRYING
        CAM5 --> FRYING
        CAM6 --> OBSERVE
        CAM7 --> OBSERVE
        FRYING --> J2
        OBSERVE --> J2
        VIB2 --> J2
        J2 --> GPIO2
    end

    subgraph "중앙 시스템"
        MQTT[MQTT Broker<br/>192.168.0.100:1883]
        ROBOT[로봇 PC<br/>제어 시스템]
        RELAY[24V 릴레이<br/>Omron 자기유지형]

        MQTT <--> ROBOT
    end

    subgraph "데이터 저장"
        STORAGE1[~/AI_Data/<br/>PersonData<br/>StirFryData<br/>Detection]
        STORAGE2[~/AI_Data/<br/>FryingData]
    end

    J1 <-->|ON/OFF 신호<br/>상태 발행| MQTT
    J2 <-->|AI 분석 결과<br/>상태 구독| MQTT
    GPIO1 --> RELAY
    GPIO2 --> RELAY
    RELAY --> |전원 제어| ROBOT
    J1 --> STORAGE1
    J2 --> STORAGE2

    style J1 fill:#90EE90
    style J2 fill:#87CEEB
    style MQTT fill:#FFD700
    style ROBOT fill:#FFA500
    style RELAY fill:#FF6B6B
```

---

## 2. MQTT 통신 플로우

```mermaid
sequenceDiagram
    participant Robot as 로봇 PC
    participant MQTT as MQTT Broker
    participant J1 as Jetson #1
    participant J2 as Jetson #2
    participant Relay as 릴레이

    Note over J1,J2: 시스템 시작
    J1->>MQTT: 연결 (jetson1_ai)
    J2->>MQTT: 연결 (jetson2_ai)
    Robot->>MQTT: 연결 (robot_client)

    Note over J1: 주간 모드 - 사람 감지
    J1->>J1: YOLO 사람 감지 (2초 지속)
    J1->>MQTT: robot/control: "ON"
    MQTT->>Robot: ON 신호 전달
    J1->>MQTT: jetson1/relay/status: "ON"
    MQTT->>J2: 릴레이 상태 동기화
    J1->>Relay: GPIO HIGH (200ms 펄스)
    Relay->>Robot: 전원 ON

    Note over Robot,J2: 튀김 작업 시작
    Robot->>MQTT: frying/pot1/food_type: "chicken"
    MQTT->>J2: 음식 종류 수신
    Robot->>MQTT: frying/pot1/control: "투입"
    MQTT->>J2: 투입 신호 수신
    J2->>J2: 데이터 수집 시작

    loop 튀김 중
        Robot->>MQTT: frying/pot1/oil_temp: 180.5
        Robot->>MQTT: frying/pot1/probe_temp: 73.2
        Robot->>MQTT: HR/Status: {state: "cooking"}
        MQTT->>J2: 온도/상태 수신
        J2->>J2: 튀김 AI 분석 (탈탈 추적)
        J2->>MQTT: jetson2/status: {frying: "COOKING"}
        MQTT->>Robot: AI 분석 결과 전달
    end

    Note over J2: 완료 판정
    J2->>J2: Lift Tracker: 완료<br/>온도: 75°C<br/>시간: 목표 도달
    J2->>MQTT: jetson2/status: {frying: "DISCHARGE"}
    MQTT->>Robot: DISCHARGE 신호 전달
    Robot->>MQTT: frying/pot1/control: "배출"
    MQTT->>J2: 배출 신호 수신
    J2->>J2: 50초 추가 수집 후 종료

    Note over J1: 야간 모드 - 사람 미감지
    J1->>J1: 야간 모드 전환 (21:00)
    J1->>J1: N분간 사람 미감지 확인
    J1->>MQTT: robot/control: "OFF"
    MQTT->>Robot: OFF 신호 전달
    J1->>MQTT: jetson1/relay/status: "OFF"
    MQTT->>J2: 릴레이 상태 동기화
    J2->>J2: 3초 대기
    J1->>Relay: GPIO LOW
    Relay->>Robot: 전원 OFF

    loop 야간 모션 감지
        J1->>J1: MOG2 모션 감지
        J1->>J1: 스냅샷 저장 (~/Detection)
    end
```

---

## 3. 주야간 모드 상태 머신 (Jetson #1)

```mermaid
stateDiagram-v2
    [*] --> 초기화
    초기화 --> 시간대_확인

    시간대_확인 --> 주간모드 : 04:00 ~ 21:00
    시간대_확인 --> 야간모드 : 21:00 ~ 04:00

    state 주간모드 {
        [*] --> YOLO_감지
        YOLO_감지 --> 사람_미감지 : 사람 없음
        YOLO_감지 --> 사람_감지중 : 사람 있음
        사람_감지중 --> 홀드_타임_체크 : 지속 시간 확인
        홀드_타임_체크 --> 릴레이_ON : 2초 이상 지속
        홀드_타임_체크 --> 사람_감지중 : 2초 미만
        릴레이_ON --> YOLO_감지
        사람_미감지 --> YOLO_감지
    }

    state 야간모드 {
        [*] --> 야간_진입_체크
        야간_진입_체크 --> 사람_확인 : N분간 감시
        사람_확인 --> 릴레이_OFF : N분간 미감지
        사람_확인 --> 야간_진입_체크 : 사람 감지됨
        릴레이_OFF --> 모션_감지_모드
        모션_감지_모드 --> 스냅샷_저장 : 모션 감지
        모션_감지_모드 --> 대기 : 모션 없음
        스냅샷_저장 --> 쿨다운 : 15초 대기
        쿨다운 --> 모션_감지_모드
        대기 --> 모션_감지_모드
    }

    주간모드 --> 시간대_확인 : 21:00 도달
    야간모드 --> 시간대_확인 : 04:00 도달
    시간대_확인 --> [*] : 종료

    note right of 주간모드
        - YOLO 사람 감지 활성
        - 2초 홀드 타임
        - 릴레이 자동 ON
    end note

    note right of 야간모드
        - MOG2 모션 감지
        - 스냅샷 저장
        - 주기적 OFF 펄스
    end note
```

---

## 4. 튀김 AI 처리 파이프라인 (Jetson #2)

```mermaid
graph TB
    START[카메라 프레임<br/>1920x1536 @ 30fps] --> SKIP{프레임 스킵<br/>15프레임마다}
    SKIP -->|스킵| START
    SKIP -->|처리| PREPROCESS[전처리<br/>Letterbox 변환]

    PREPROCESS --> YOLO[YOLOv8-seg 추론<br/>frying_seg_v3.pt<br/>입력: 800x540]

    YOLO --> MASK[마스크 추출<br/>음식 영역 분리]
    MASK --> AREA[면적 계산<br/>현재 vs 이전]

    AREA --> LIFT_CHECK{면적 증가율<br/>>= 15%?}
    LIFT_CHECK -->|Yes| LIFT_EVENT[탈탈 이벤트 감지<br/>카운터 +1]
    LIFT_CHECK -->|No| COLOR

    LIFT_EVENT --> COOLDOWN{쿨다운 2초<br/>경과?}
    COOLDOWN -->|Yes| COLOR
    COOLDOWN -->|No| WAIT[대기]
    WAIT --> START

    COLOR[색상 특징 추출<br/>LAB 색공간]
    COLOR --> DELTA_E[델타 E 계산<br/>색상 변화량]

    DELTA_E --> COMPLETE_CHECK{델타 E<br/>>= 12.0?}
    COMPLETE_CHECK -->|Yes| TEMP_CHECK{온도 확인<br/>probe_temp<br/>>= 70°C?}
    COMPLETE_CHECK -->|No| STATE_UPDATE1[상태: COOKING]

    TEMP_CHECK -->|Yes| TIME_CHECK{시간 확인<br/>running_time<br/>>= target-5s?}
    TEMP_CHECK -->|No| STATE_UPDATE1

    TIME_CHECK -->|Yes| STATE_UPDATE2[상태: DISCHARGE]
    TIME_CHECK -->|No| STATE_UPDATE1

    STATE_UPDATE1 --> MQTT_PUB[MQTT 발행<br/>jetson2/status]
    STATE_UPDATE2 --> MQTT_PUB

    MQTT_PUB --> GUI[GUI 업데이트<br/>탈탈 횟수<br/>색변화량<br/>상태]

    GUI --> COLLECTION{데이터 수집<br/>활성화?}
    COLLECTION -->|Yes| SAVE[4-카메라<br/>동시 저장]
    COLLECTION -->|No| START
    SAVE --> START

    style YOLO fill:#FFD700
    style LIFT_EVENT fill:#90EE90
    style STATE_UPDATE2 fill:#FF6B6B
    style MQTT_PUB fill:#87CEEB
```

---

## 5. 데이터 저장 구조

```mermaid
graph TB
    subgraph "Jetson #1 데이터"
        ROOT1[~/AI_Data/]

        ROOT1 --> PERSON[PersonData/<br/>사람 감지 수집]
        ROOT1 --> STIRFRY[StirFryData/<br/>볶음 모니터링]
        ROOT1 --> DETECTION[Detection/<br/>야간 스냅샷]

        PERSON --> PERSON_DATE[20260202/]
        PERSON_DATE --> PERSON_IMG[083005.jpg<br/>083010.jpg<br/>...<br/>640x512, 50% quality]

        STIRFRY --> STIRFRY_SESSION[20260202_143055_chicken_pot1/]
        STIRFRY_SESSION --> STIRFRY_LEFT[left_000001.jpg<br/>left_000002.jpg<br/>...]
        STIRFRY_SESSION --> STIRFRY_RIGHT[right_000001.jpg<br/>right_000002.jpg<br/>...]
        STIRFRY_SESSION --> STIRFRY_INFO[session_info.json]

        DETECTION --> DETECT_DATE[20260202/]
        DETECT_DATE --> DETECT_IMG[213045.jpg<br/>213102.jpg<br/>...]
    end

    subgraph "Jetson #2 데이터"
        ROOT2[~/AI_Data/]

        ROOT2 --> FRYING[FryingData/<br/>튀김 AI 수집]

        FRYING --> FRYING_SESSION[20260202_143055_chicken_pot1/]
        FRYING_SESSION --> FRYING_LEFT[frying_left_000001.jpg<br/>frying_left_000002.jpg<br/>...]
        FRYING_SESSION --> FRYING_RIGHT[frying_right_000001.jpg<br/>frying_right_000002.jpg<br/>...]
        FRYING_SESSION --> OBSERVE_LEFT[observe_left_000001.jpg<br/>observe_left_000002.jpg<br/>...]
        FRYING_SESSION --> OBSERVE_RIGHT[observe_right_000001.jpg<br/>observe_right_000002.jpg<br/>...]
        FRYING_SESSION --> FRYING_INFO[session_info.json<br/>AI 분석 결과 포함]
    end

    subgraph "session_info.json 내용"
        INFO_CONTENT["<br/>{<br/>  device_id: jetson2<br/>  food_type: chicken<br/>  duration_sec: 565<br/>  frame_count: {<br/>    frying_left: 565<br/>    observe_left: 565<br/>  }<br/>  ai_results: {<br/>    lift_count: 12<br/>    color_change: 15.3<br/>    final_status: DISCHARGE<br/>  }<br/>}<br/>"]
    end

    FRYING_INFO -.->|포함| INFO_CONTENT
    STIRFRY_INFO -.->|유사| INFO_CONTENT

    style PERSON fill:#90EE90
    style STIRFRY fill:#FFD700
    style DETECTION fill:#FFA500
    style FRYING fill:#87CEEB
    style INFO_CONTENT fill:#E0E0E0
```

---

## 6. 릴레이 제어 시퀀스 (24V Omron 자기유지형)

```mermaid
sequenceDiagram
    participant J1 as Jetson #1
    participant GPIO as GPIO<br/>Pin 29,31
    participant ULN as ULN2803<br/>Driver
    participant Relay as 24V Relay<br/>Omron
    participant Robot as 로봇 PC

    Note over J1,Robot: ON 신호 (사람 감지)
    J1->>GPIO: Pin 29 HIGH<br/>Pin 31 HIGH
    GPIO->>ULN: 신호 증폭
    ULN->>Relay: 24V 공급 (200ms)
    activate Relay
    Relay->>Relay: 자기유지 ON 상태
    Note over Relay: 자기유지형이라<br/>전원 유지 불필요
    J1->>GPIO: Pin 29 LOW<br/>Pin 31 LOW
    GPIO->>ULN: 신호 차단
    ULN->>Relay: 전원 차단
    Note over Relay: 여전히 ON 상태<br/>(자기유지)
    Relay->>Robot: 전원 공급 유지
    deactivate Relay

    Note over J1,Robot: OFF 신호 (야간 미감지)
    J1->>GPIO: Pin 29 HIGH<br/>Pin 31 HIGH
    GPIO->>ULN: 신호 증폭
    ULN->>Relay: 24V 공급 (200ms)
    activate Relay
    Relay->>Relay: 자기유지 OFF 상태
    J1->>GPIO: Pin 29 LOW<br/>Pin 31 LOW
    GPIO->>ULN: 신호 차단
    ULN->>Relay: 전원 차단
    Note over Relay: OFF 상태 유지<br/>(자기유지)
    Relay->>Robot: 전원 차단
    deactivate Relay

    Note over J1,Robot: 주기적 OFF 펄스 (3초마다)
    loop 야간 모드 중
        J1->>J1: 3초 대기
        J1->>GPIO: Pin 29 HIGH + Pin 31 HIGH (200ms)
        GPIO->>Relay: OFF 펄스
        Note over Relay: 브로커 PC 상시전원<br/>유지를 위한 주기적 신호
    end
```

---

## 7. 진동센서 측정 플로우

```mermaid
graph TB
    START[로봇 PC] --> MQTT_REQ[MQTT 발행<br/>frying/pot1/control<br/>VibrationRequest]

    MQTT_REQ --> J1_RECV[Jetson #1<br/>MQTT 수신]

    J1_RECV --> TEST_MODE{테스트 모드?<br/>vibration_test_mode}

    TEST_MODE -->|true| INSTANT_RESP[즉시 응답<br/>NORMAL 반환]
    TEST_MODE -->|false| MODBUS_CONN[Modbus RTU 연결<br/>/dev/ttyUSB0<br/>9600 baud]

    MODBUS_CONN --> READ_LOOP[5초간 반복 읽기<br/>가속도 센서 값]

    READ_LOOP --> CALC_VEL[속도 변환<br/>vel = acc × 0.001]

    CALC_VEL --> CALC_MAG[크기 계산<br/>vel_mag = √(x²+y²+z²)]

    CALC_MAG --> UPDATE_MAX[최대값 업데이트<br/>vel_mag_max]

    UPDATE_MAX --> TIME_CHECK{5초 경과?}
    TIME_CHECK -->|No| READ_LOOP
    TIME_CHECK -->|Yes| THRESHOLD_CHECK{vel_mag_max<br/>>= threshold?}

    THRESHOLD_CHECK -->|Yes| ABNORMAL[상태: ABNORMAL]
    THRESHOLD_CHECK -->|No| NORMAL[상태: NORMAL]

    INSTANT_RESP --> MQTT_RESP[MQTT 발행<br/>응답 메시지]
    ABNORMAL --> MQTT_RESP
    NORMAL --> MQTT_RESP

    MQTT_RESP --> ROBOT_RECV[로봇 PC<br/>응답 수신]

    ROBOT_RECV --> DECISION{진동 상태}
    DECISION -->|NORMAL| PROCEED[작업 계속]
    DECISION -->|ABNORMAL| ALERT[경고 알림<br/>작업 중단]

    style TEST_MODE fill:#FFD700
    style ABNORMAL fill:#FF6B6B
    style NORMAL fill:#90EE90
    style MQTT_REQ fill:#87CEEB
    style MQTT_RESP fill:#87CEEB
```

---

## 8. 성능 최적화 구조

```mermaid
graph TB
    subgraph "카메라 입력 (30fps)"
        CAM1[튀김 좌측<br/>1920x1536]
        CAM2[튀김 우측<br/>1920x1536]
        CAM3[바켓 좌측<br/>1920x1536]
        CAM4[바켓 우측<br/>1920x1536]
    end

    subgraph "Frame Skip 레이어"
        SKIP1[프레임 카운터]
        SKIP1 --> DECISION1{15프레임마다?}
        SKIP1 --> DECISION2{20프레임마다?}
        SKIP1 --> DECISION3{2프레임마다?}
        SKIP1 --> DECISION4{6프레임마다?}
    end

    subgraph "AI 추론 (별도 스레드)"
        DECISION1 -->|Yes| FRYING_AI[튀김 AI<br/>~80ms/프레임<br/>~2fps]
        DECISION2 -->|Yes| OBSERVE_AI[바켓 AI<br/>~30ms/프레임<br/>~1.5fps]
    end

    subgraph "GUI 업데이트 (메인 스레드)"
        DECISION3 -->|Yes| GUI_FRYING[튀김 GUI 갱신<br/>~15fps]
        DECISION4 -->|Yes| GUI_OBSERVE[바켓 GUI 갱신<br/>~5fps]
    end

    subgraph "데이터 저장 (별도 스레드)"
        SAVE_THREAD[비동기 저장<br/>메인 루프 블로킹 없음]
        CAM1 --> SAVE_THREAD
        CAM2 --> SAVE_THREAD
        CAM3 --> SAVE_THREAD
        CAM4 --> SAVE_THREAD
    end

    CAM1 --> SKIP1
    CAM2 --> SKIP1
    CAM3 --> SKIP1
    CAM4 --> SKIP1

    FRYING_AI --> RESULT1[분석 결과<br/>Queue]
    OBSERVE_AI --> RESULT2[분석 결과<br/>Queue]

    RESULT1 --> MQTT[MQTT 발행<br/>jetson2/status]
    RESULT2 --> MQTT

    GUI_FRYING --> DISPLAY[화면 표시<br/>768x1024]
    GUI_OBSERVE --> DISPLAY

    style FRYING_AI fill:#FFD700
    style OBSERVE_AI fill:#87CEEB
    style SAVE_THREAD fill:#90EE90
    style MQTT fill:#FFA500

    note1[실제 처리량:<br/>- 튀김 AI: 2fps<br/>- 바켓 AI: 1.5fps<br/>- GUI 표시: 10fps<br/>- 데이터 수집: 30fps]
```

---

## 9. 사람 감지 데이터 수집 스케줄

```mermaid
gantt
    title 사람 감지 데이터 수집 스케줄 (평일 자동 동작)
    dateFormat HH:mm
    axisFormat %H:%M

    section 야간 모드
    야간 감시 (모션 스냅샷)    :done, night1, 00:00, 04:00

    section 주간 전환
    주간 모드 시작              :crit, daystart, 04:00, 08:30

    section 데이터 수집
    사람 감지 수집 활성화       :active, collection, 08:30, 12:00

    section 일반 모니터링
    일반 사람 감지 (릴레이 제어) :done, normal, 12:00, 21:00

    section 야간 전환
    야간 모드 전환              :crit, nightstart, 21:00, 21:05
    야간 감시 (모션 스냅샷)    :done, night2, 21:05, 24:00
```

---

## 다이어그램 사용 방법

### GitHub에서 보기
- 위 다이어그램은 Mermaid 형식으로 작성되었습니다
- GitHub, GitLab, VS Code (Markdown Preview Enhanced) 등에서 자동 렌더링됩니다

### 이미지로 변환
```bash
# Mermaid CLI 설치
npm install -g @mermaid-js/mermaid-cli

# PNG로 변환
mmdc -i SYSTEM_DIAGRAMS.md -o diagrams.png
```

### 온라인 편집
- https://mermaid.live/ 에서 실시간 편집 및 미리보기 가능
