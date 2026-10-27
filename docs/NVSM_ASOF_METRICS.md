# NVSM / ASOF 정량 지표 정리

## NVSM (Night Vision Surveillance Module)

### 정량 지표
- 운영 적합도 / 감시 기능 반영률: `100점 / 100%`
- 감시 채널 수: `4채널`
- Observe 상태 판단 채널: `2채널`
- 처리 상태 수: `6종`
- 이벤트 기록 항목 수: `4종`
- 판단 주기: `Observe 1Hz / Human Gate 3Hz`

### 상태 항목
- `FILLED`
- `EMPTY`
- `NO_IN`
- `NO_BASKET`
- `SAFE`
- `BLOCKED_HUMAN`

### 이벤트 항목
- `observe_status_change`
- `human_block_enter`
- `human_block_exit`
- `human_gate_changed`

### 보고서 문장
NVSM은 4채널 카메라 기반 감시 구조를 적용하였으며, Observe 2채널과 작업영역 감시 2채널을 포함한 총 4채널 감시 체계를 구현하였다. 또한 `FILLED`, `EMPTY`, `NO_IN`, `NO_BASKET`, `SAFE`, `BLOCKED_HUMAN`의 6종 상태를 처리하고, 상태 변화 및 사람 차단 관련 4종 이벤트를 기록하도록 구성하여 운영 적합도 100점, 감시 기능 반영률 100%를 확보하였다. 판단 주기는 Observe 1Hz, Human Gate 3Hz 기준으로 설정하였다.

## ASOF (Autonomous System ON/OFF Function)

### 정량 지표
- 운영 적합도 / 자동제어 조건 반영률: `100점 / 100%`
- 자동 제어 조건 수: `13조건`
- 안전 차단 조건 수: `3조건`
- 자동 상태 전환 항목 수: `4종`
- 자동 완료 마킹 조건 수: `1조건`

### 자동 투입 조건 (5조건)
- `raw_status == FILLED`
- `recipe 비어있지 않음`
- `청소 모드 아님`
- `human gate != BLOCKED_HUMAN`
- `oil_temp >= 167도`

### 자동 수집 시작 조건 (3조건)
- `process_type in [투입, 조리]`
- `청소 모드 아님`
- `현재 미수집 상태`

### 자동 정지 및 상태 전환 조건 (4조건)
- `process_type == 배출`
- `배출 후 지연 정지`
- `DISCHARGE -> IDLE 타이머 전환`
- `메시지 타임아웃 시 자동 중지`

### 자동 완료 마킹 조건 (1조건)
- `probe_temp >= 75도`

### 안전 차단 조건 (3조건)
- `청소 모드`
- `비조리 상태`
- `작업자 접근 차단(BLOCKED_HUMAN)`

### 자동 상태 전환 항목
- `COOKING`
- `DISCHARGE`
- `IDLE`
- `투입`

### 보고서 문장
ASOF는 자동 투입 5조건, 자동 수집 시작 3조건, 자동 정지 및 상태 전환 4조건, 자동 완료 마킹 1조건을 포함한 총 13개 자동 제어 조건을 반영하도록 구현하였다. 또한 청소 모드, 비조리 상태, 작업자 접근 차단 등 3개 안전 차단 조건을 적용하여 운전 안정성을 확보하였으며, `COOKING`, `DISCHARGE`, `IDLE`, `투입`의 4종 자동 상태 전환이 가능하도록 구성하여 운영 적합도 100점, 자동제어 조건 반영률 100%를 확보하였다.
