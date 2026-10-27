#!/usr/bin/env bash
# ==============================================================================
# GMSL 디시리얼라이저(MAX96712) 릴레이 선(先)전원 인가 + I2C RESET_ALL 통합 초기화 스크립트
#
# 법칙 및 실측(2026-10-27) 반영:
#   - 12V 어댑터 전원을 릴레이로 끊어도 MAX96712 칩은 Jetson CSI 커넥터 전원으로 살아 있음.
#   - 따라서 12V 차단(카메라 PoC 리셋) 중 칩이 I2C(0x6b)에 응답하면,
#     반드시 I2C 소프트웨어 리셋(RESET_ALL: 0x0013 = 0x40)을 함께 수행해 칩 레지스터를 초기화함.
#
# 동작 순서:
#   [0/5] USB 릴레이 응답 점검 (무응답 시 안전 종료)
#   [1/5] 카메라 사용 서비스 임시 중지, 프로세스 정리 및 커널 모듈(sgx_yuv_gmsl2, max96712) 언로드
#   [2/5] 릴레이 12V 차단(기본 5초) + 칩 생존 시 I2C RESET_ALL 수행 및 레지스터 초기화 검증
#   [3/5] 릴레이 12V 인가(기본 8초) + 디시리얼라이저 칩(0x6b -> 0xa0) 응답 확인
#   [4/5] GMSL 커널 드라이버 로드 (max96712.ko -> sgx-yuv-gmsl2.ko)
#   [5/5] NVCSI 클럭 설정, V4L2 센서 모드 설정 및 중지했던 서비스 재시작
#
# 장비별 설정: /etc/default/deser-control (KEY=값, 대시보드 systemd 유닛과 같은 파일)
#   WIRING, RELAY_PORT, I2C_BUS, DESER_ADDR, OFF_DELAY_SEC, ON_DELAY_SEC, GMSL_MODE, SENSOR_MODE,
#   EXPECTED_CAMERAS — 우선순위: CLI 인자 > 환경변수 > 이 파일 > 기본값
#
# 종료 코드:
#   0            성공 (리셋 전에 있던 카메라 노드가 모두 다시 설정됨,
#                리셋 전 노드가 없었으면 EXPECTED_CAMERAS 개)
#   1            실패 (작업 중 오류 — 12V 인가/드라이버/서비스 복구를 시도한 뒤 종료)
#   10           사전 점검에서 중단, 아무것도 변경하지 않음 (웹 대시보드 쿨다운 미적용)
#   129/130/143  신호(HUP/INT/TERM)로 중단 — 12V 인가/드라이버/서비스 복구 후 종료
# ==============================================================================

set -u

EXIT_ABORTED=10

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RELAY_SCRIPT="${RELAY_SCRIPT:-$SCRIPT_DIR/test_usb_relay.py}"
if [ ! -f "$RELAY_SCRIPT" ] && [ -f "$HOME/test_usb_relay.py" ]; then
    RELAY_SCRIPT="$HOME/test_usb_relay.py"
fi

# 드라이버 폴더 자동 탐색 (하이픈/언더스코어 및 홈 디렉터리 모두 대응)
DRIVER_DIR=""
for cand in \
    "$SCRIPT_DIR/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3" \
    "$SCRIPT_DIR/SG4A_NONX_G2Y_A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3" \
    "$HOME/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3" \
    "$HOME/SG4A_NONX_G2Y_A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3"; do
    if [ -d "$cand" ]; then
        DRIVER_DIR="$cand"
        break
    fi
done

if [ -z "$DRIVER_DIR" ]; then
    echo "[ERROR] SG4A 드라이버 디렉토리를 찾을 수 없습니다."
    exit "$EXIT_ABORTED"
fi

KO_DIR="$DRIVER_DIR/ko"
CLOCK_SCRIPT="$DRIVER_DIR/clock_config.sh"

# 장비별 설정 파일 — 터미널 수동 실행에도 적용 (sudo 는 환경변수를 넘기지 않으므로 직접 읽음)
# 환경변수로 이미 받은 값은 그대로 두고, 파일은 셸 코드로 실행하지 않고 KEY=값 만 읽음
DEFAULTS_FILE="/etc/default/deser-control"
if [ -r "$DEFAULTS_FILE" ]; then
    while IFS='=' read -r key val || [ -n "$key" ]; do
        key="${key//[[:space:]]/}"
        case "$key" in
            WIRING|RELAY_PORT|I2C_BUS|DESER_ADDR|OFF_DELAY_SEC|ON_DELAY_SEC|GMSL_MODE|SENSOR_MODE|EXPECTED_CAMERAS)
                val="${val#"${val%%[![:space:]]*}"}"   # 앞뒤 공백(CR 포함) 제거
                val="${val%"${val##*[![:space:]]}"}"
                val="${val%\"}"; val="${val#\"}"
                val="${val%\'}"; val="${val#\'}"
                [ -n "${!key:-}" ] || printf -v "$key" '%s' "$val"
                ;;
        esac
    done < "$DEFAULTS_FILE"
fi

# 기본 파라미터 (환경변수, 위 설정 파일 또는 CLI 인자로 변경 가능)
WIRING="${WIRING:-nc}"               # nc(기본): 릴레이 ON=전원차단, 릴레이 OFF=전원인가
RELAY_PORT="${RELAY_PORT:-/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0}"
I2C_BUS="${I2C_BUS:-9}"              # SG4A MAX96712 I2C 버스 번호 (기본: 9)
DESER_ADDR="${DESER_ADDR:-0x6b}"     # MAX96712 I2C 주소 (기본: 0x6b)
OFF_DELAY_SEC="${OFF_DELAY_SEC:-5}"  # 전원 차단 후 완전 방전 대기 시간(초)
ON_DELAY_SEC="${ON_DELAY_SEC:-8}"    # 전원 인가 후 디시리얼라이저 선(先)부팅 대기 시간(초)
GMSL_MODE="${GMSL_MODE:-2,2,2,2}"    # GMSL2/3G (2,2,2,2)
SENSOR_MODE="${SENSOR_MODE:-1}"      # 1 = 1920x1536
EXPECTED_CAMERAS="${EXPECTED_CAMERAS:-4}"  # 리셋 전 노드가 없을 때(드라이버 미로드) 성공 기준 카메라 수
case "$EXPECTED_CAMERAS" in ''|*[!0-9]*) EXPECTED_CAMERAS=4 ;; esac
DO_REBOOT=false
SKIP_RELAY_CHECK="${SKIP_RELAY_CHECK:-false}"  # true: 릴레이 무응답/사용 불가여도 I2C 리셋 진행

RELAY_USABLE=true   # false: 릴레이 포트/스크립트 사용 불가 (--skip-relay-check 에서만) → 릴레이 명령 생략
POWER_CUT=0         # 1: 12V 차단 명령을 보낸 상태 (복구 시 전원 인가 후 안정화 대기 필요)
EXPECTED_COUNT=0    # 리셋 전 존재하던 /dev/video0~3 개수 (리셋 후 모두 돌아와야 성공)
SUCCESS_COUNT=0
RELAY_POWER=unknown
# 신호로 중단될 때 복구 출력 기록 위치 (deser_control.sh 가 대시보드 로그 경로를 넘겨줌)
INTERRUPT_LOG="${DESER_LOG_FILE:-/tmp/deser_reset_interrupted.log}"

usage() {
    cat <<EOF
사용법: sudo $(basename "$0") [옵션]

옵션:
  --reboot             디시리얼라이저 리셋(ON 유지) 후 젯슨을 즉시 재부팅(sudo reboot)
  --skip-relay-check   릴레이가 무응답이거나 사용할 수 없어도 진행 (이때는 12V 차단 없이 I2C 리셋 + 드라이버 재로드만 수행됨)
  --wiring <nc|no>     릴레이 배선 방식 (기본값: $WIRING)
  --port <path>        USB 릴레이 시리얼 포트 경로 (기본값: $RELAY_PORT)
  --i2c-bus <num>      MAX96712 I2C 버스 번호 (기본값: $I2C_BUS)
  --off-delay <sec>    디시리얼라이저 전원 OFF 방전 대기 초 (기본값: $OFF_DELAY_SEC)
  --on-delay <sec>     디시리얼라이저 전원 ON 후 안정화 대기 초 (기본값: $ON_DELAY_SEC)
  -h, --help           도움말 출력

장비별 기본값은 $DEFAULTS_FILE 에 KEY=값 형식으로 (WIRING, RELAY_PORT, I2C_BUS, EXPECTED_CAMERAS 등)
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --reboot)
            DO_REBOOT=true
            shift
            ;;
        --skip-relay-check)
            SKIP_RELAY_CHECK=true
            shift
            ;;
        --wiring)
            WIRING="$2"
            shift 2
            ;;
        --port)
            RELAY_PORT="$2"
            shift 2
            ;;
        --i2c-bus)
            I2C_BUS="$2"
            shift 2
            ;;
        --off-delay)
            OFF_DELAY_SEC="$2"
            shift 2
            ;;
        --on-delay)
            ON_DELAY_SEC="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "[ERROR] 알 수 없는 옵션: $1"
            usage
            exit 1
            ;;
    esac
done

# 배선(NC/NO)에 따른 릴레이 명령 매핑
if [ "$WIRING" = "nc" ]; then
    RELAY_CMD_POWER_OFF="on"
    RELAY_CMD_POWER_ON="off"
else
    RELAY_CMD_POWER_OFF="off"
    RELAY_CMD_POWER_ON="on"
fi
# 12V 인가 상태일 때 릴레이 상태 조회 응답 (NC: "CH1: OFF")
# 보드/펌웨어마다 콜론 뒤 공백이 다를 수 있어("CH1:OFF") 비교는 정규식으로
RELAY_ON_WORD="$(echo "$RELAY_CMD_POWER_ON" | tr '[:lower:]' '[:upper:]')"
RELAY_IDLE_STATE="CH1: $RELAY_ON_WORD"
RELAY_IDLE_RE="CH1:[[:space:]]*${RELAY_ON_WORD}([^A-Za-z]|\$)"
RELAY_STATE_RE='CH1:[[:space:]]*(ON|OFF)'

# 중지한 systemd 서비스 목록 기록 (종료/실패 시 복구용)
STOPPED_SERVICES=()
CANDIDATE_SERVICES=(
    "collector.service"
    "soup-collector.service"
    "jetson1-web.service"
    "jetson2-web.service"
    "jetson1-monitor.service"
    "jetson2-monitor.service"
)

relay_cmd() {
    # $1=릴레이 동작(on|off|status) $2=init-delay(초) $3=반복 횟수
    python3 "$RELAY_SCRIPT" --port "$RELAY_PORT" --wiring "$WIRING" --mode "$1" --init-delay "$2" --retries "$3"
}

check_relay_power() {
    # 릴레이 상태 조회 → RELAY_POWER: on(12V 인가) / off(12V 차단) / unknown(무응답)
    local out
    out="$(relay_cmd status 1.5 3 2>&1)"
    echo "$out" | grep "Status response" | sed 's/^/    /'
    if echo "$out" | grep -Eq "$RELAY_IDLE_RE"; then
        RELAY_POWER=on
    elif echo "$out" | grep -Eq "$RELAY_STATE_RE"; then
        RELAY_POWER=off
    else
        RELAY_POWER=unknown
    fi
}

relay_unusable() {
    # 릴레이를 쓸 수 없을 때: 기본은 중단, --skip-relay-check 이면 릴레이 명령 없이 진행
    if [ "$SKIP_RELAY_CHECK" = true ]; then
        echo "  [WARN] $1 — --skip-relay-check 지정으로 릴레이 없이 진행합니다"
        echo "         (12V 차단 없이 I2C RESET_ALL + 드라이버 재로드만 수행)"
        RELAY_USABLE=false
    else
        echo "[ERROR] $1. 작업을 중단합니다."
        echo "        (릴레이 없이 칩 리셋만 하려면 --skip-relay-check 옵션 사용)"
        exit "$EXIT_ABORTED"
    fi
}

restart_stopped_services() {
    if [ "${#STOPPED_SERVICES[@]}" -gt 0 ]; then
        echo ""
        echo "[복구] 임시 중지했던 서비스 재시작 중: ${STOPPED_SERVICES[*]}"
        for svc in "${STOPPED_SERVICES[@]}"; do
            sudo systemctl start "$svc" 2>/dev/null || echo "  [WARN] $svc 재시작 실패"
        done
    fi
}

init_cameras() {
    # NVCSI 클럭 + V4L2 센서 모드 설정 (설정 성공 채널 수 → SUCCESS_COUNT)
    if [ -f "$CLOCK_SCRIPT" ]; then
        chmod +x "$CLOCK_SCRIPT" 2>/dev/null || true
        sudo "$CLOCK_SCRIPT" 2>/dev/null || true
        echo "  ✓ 클럭 설정 완료"
    fi

    SUCCESS_COUNT=0
    for port in 0 1 2 3; do
        if [ -e "/dev/video${port}" ]; then
            if v4l2-ctl --set-ctrl "bypass_mode=0,sensor_mode=${SENSOR_MODE}" -d "/dev/video${port}" 2>/dev/null; then
                echo "  ✓ /dev/video${port} 제어값(sensor_mode=${SENSOR_MODE}) 설정 완료"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                echo "  ✗ /dev/video${port} v4l2-ctl 설정 실패"
            fi
        else
            echo "  ✗ /dev/video${port} 디바이스 노드 없음"
        fi
    done
}

reload_drivers_and_recover() {
    echo ""
    echo "[복구] 12V 인가 / 드라이버 재로드 / 서비스 복구를 시도합니다..."
    if [ "$RELAY_USABLE" = true ]; then
        # 12V 인가 명령은 반복해도 안전 — 결과를 로그에 남김
        relay_cmd "$RELAY_CMD_POWER_ON" 1.5 3 2>&1 | sed 's/^/  [복구] /'
        if [ "$POWER_CUT" = 1 ]; then
            echo "  [복구] 12V 인가 후 ${ON_DELAY_SEC}초 대기 (카메라가 먼저 부팅된 뒤 드라이버 로드)"
            sleep "$ON_DELAY_SEC"
            POWER_CUT=0
        fi
    fi
    if [ -d "$KO_DIR" ]; then
        (
            cd "$KO_DIR" || exit 0
            lsmod | grep -q "max96712" || sudo insmod max96712.ko 2>/dev/null || true
            lsmod | grep -q "sgx_yuv_gmsl2" || sudo insmod sgx-yuv-gmsl2.ko "GMSLMODE_1=${GMSL_MODE}" 2>/dev/null || true
        )
        sleep 2
        init_cameras
    fi
    restart_stopped_services
}

on_signal() {
    local code="$1"
    # 복구 중 추가 신호는 무시 (SSH 끊김은 HUP 가 여러 번 오고 Ctrl-C 를 다시 누를 수도 있음 — SIGKILL 로만 중단).
    # 무시 상태는 복구 중 실행하는 릴레이 명령에도 상속됨
    trap '' HUP INT TERM
    echo "[중단] 신호 수신 — 12V 인가/드라이버/서비스 복구 중 (약 30초, 추가 Ctrl-C 무시, 로그: $INTERRUPT_LOG)" 2>/dev/null
    # 터미널(SSH)이나 로그 파이프(tee)가 이미 끊겼을 수 있으므로 이후 출력은 파일로
    exec >>"$INTERRUPT_LOG" 2>&1 || exec >/dev/null 2>&1
    echo "[중단] $(date '+%F %T') 신호 수신 (종료코드 $code)"
    reload_drivers_and_recover
    echo "[중단] $(date '+%F %T') 복구 시도 완료"
    exit "$code"
}

read_deser_reg() {
    local reg_hi="$1"
    local reg_lo="$2"
    sudo i2ctransfer -f -y "$I2C_BUS" "w2@${DESER_ADDR}" "$reg_hi" "$reg_lo" r1 2>/dev/null | tr -d '\r\n '
}

read_deser_cfg_triple() {
    local r1 r2 r3
    r1="$(read_deser_reg 0x08 0xA0)"
    r2="$(read_deser_reg 0x04 0x0B)"
    r3="$(read_deser_reg 0x09 0x0B)"
    echo "${r1:-N/A} ${r2:-N/A} ${r3:-N/A}"
}

echo "============================================================"
echo " GMSL 디시리얼라이저 선(先)전원 인가 + I2C 리셋 초기화 시작"
echo " - 드라이버 경로   : $DRIVER_DIR"
echo " - 배선 모드       : $WIRING (12V차단=$RELAY_CMD_POWER_OFF, 12V인가=$RELAY_CMD_POWER_ON)"
echo " - 릴레이 포트     : $RELAY_PORT"
echo " - I2C 버스/주소   : bus $I2C_BUS / $DESER_ADDR"
echo " - 방전 대기(OFF)  : ${OFF_DELAY_SEC}s"
echo " - 안정화 대기(ON) : ${ON_DELAY_SEC}s"
echo " - 동작 모드       : $( [ "$DO_REBOOT" = true ] && echo "디시리얼라이저 리셋 후 젯슨 재부팅(--reboot)" || echo "드라이버 재로드 및 카메라 초기화" )"
echo "============================================================"

# 대시보드(deser_control.sh)와 터미널 수동 실행이 겹치지 않도록 같은 잠금 사용
# (deser_control.sh 는 잠금을 잡은 뒤 DESER_LOCK_HELD=1 로 이 스크립트를 실행)
if [ -z "${DESER_LOCK_HELD:-}" ] && [ "$(id -u)" -eq 0 ]; then
    mkdir -p /run/deser-control
    exec 9>>/run/deser-control/lock
    if ! flock -n 9; then
        echo "[ERROR] 다른 카메라 복구 작업이 실행 중입니다 (대시보드 또는 다른 터미널). 작업을 중단합니다."
        exit "$EXIT_ABORTED"
    fi
fi

# ------------------------------------------------------------------------------
# [단계 0] 릴레이 포트 및 응답 사전 점검 (무응답 시 아무것도 건드리지 않고 종료)
# ------------------------------------------------------------------------------
echo ""
echo "[0/5] USB 릴레이 연결 및 응답 점검 중..."
if [ ! -f "$RELAY_SCRIPT" ]; then
    relay_unusable "릴레이 제어 스크립트가 없습니다: $RELAY_SCRIPT"
elif [ ! -e "$RELAY_PORT" ]; then
    relay_unusable "릴레이 시리얼 포트가 존재하지 않습니다: $RELAY_PORT (lsusb, ch341 드라이버, brltty 제거 여부 확인)"
else
    STATUS_OUT="$(relay_cmd status 1.5 3 2>&1)"
    STATUS_RC=$?
    echo "$STATUS_OUT" | sed 's/^/  /'
    if [ "$STATUS_RC" -ne 0 ]; then
        relay_unusable "USB 릴레이 제어 스크립트 실행 실패 (pySerial, 포트 권한 등 확인)"
    elif echo "$STATUS_OUT" | grep -q "(no response)"; then
        if [ "$SKIP_RELAY_CHECK" = true ]; then
            echo "  [WARN] USB 릴레이 상태 조회 무응답 — --skip-relay-check 지정으로 계속 진행합니다"
            echo "         (릴레이가 실제로 동작하지 않으면 12V 차단 없이 I2C RESET_ALL + 드라이버 재로드만 수행됨)"
        else
            echo "[ERROR] USB 릴레이가 상태 조회에 응답하지 않습니다. 안전을 위해 작업을 중단합니다."
            echo "        (응답 없이 진행하려면 --skip-relay-check 옵션 사용)"
            exit "$EXIT_ABORTED"
        fi
    else
        echo "  ✓ USB 릴레이 응답 정상"
        if ! echo "$STATUS_OUT" | grep -Eq "$RELAY_IDLE_RE"; then
            echo "  [WARN] 릴레이가 12V 인가 상태($RELAY_IDLE_STATE)가 아닙니다 — 이번 리셋 [3/5]에서 다시 인가합니다"
        fi
    fi
fi

# 여기부터 서비스/드라이버/12V 를 바꾸므로, 신호(SSH 끊김 HUP, Ctrl-C INT, systemd 중지 TERM)로
# 중단돼도 원래 상태로 되돌리도록 트랩 설치.
# SIGPIPE 는 무시: 출력 파이프(tee)가 먼저 죽으면 bash 가 'Terminated' 등을 쓰다가 트랩 실행 전에 죽음
trap '' PIPE
trap 'on_signal 129' HUP
trap 'on_signal 130' INT
trap 'on_signal 143' TERM

# ------------------------------------------------------------------------------
# [단계 1] 카메라 사용 서비스 중지, 점유 프로세스 확인 및 커널 모듈 언로드
# ------------------------------------------------------------------------------
echo ""
echo "[1/5] 카메라 서비스 임시 중지 및 GMSL 커널 모듈 언로드 중..."
for port in 0 1 2 3; do
    if [ -e "/dev/video${port}" ]; then
        EXPECTED_COUNT=$((EXPECTED_COUNT + 1))
    fi
done
echo "  - 리셋 전 카메라 노드: ${EXPECTED_COUNT}개"

for svc in "${CANDIDATE_SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        echo "  - 실행 중인 서비스 중지: $svc"
        STOPPED_SERVICES+=("$svc")  # 중지 도중 중단돼도 재시작 대상에 들어가도록 먼저 기록
        sudo systemctl stop "$svc"
    fi
done

pkill -f "gst-launch-1.0.*v4l2src" 2>/dev/null || true
sleep 1

# /dev/video* 점유 프로세스 확인
if compgen -G "/dev/video*" >/dev/null 2>&1; then
    BUSY_PIDS="$(sudo fuser /dev/video* 2>/dev/null | tr -s ' ')"
    if [ -n "$BUSY_PIDS" ]; then
        echo "[ERROR] /dev/video* 장치를 사용 중인 프로세스가 남아 있습니다 (PID: $BUSY_PIDS)."
        ps -fp $BUSY_PIDS 2>/dev/null || true
        restart_stopped_services
        exit 1
    fi
fi

if lsmod | grep -q "sgx_yuv_gmsl2"; then
    echo "  - sgx_yuv_gmsl2 모듈 제거 중..."
    if ! sudo rmmod sgx_yuv_gmsl2; then
        echo "[ERROR] sgx_yuv_gmsl2 언로드 실패!"
        reload_drivers_and_recover
        exit 1
    fi
fi

if lsmod | grep -q "max96712"; then
    echo "  - max96712 모듈 제거 중..."
    if ! sudo rmmod max96712; then
        echo "[ERROR] max96712 언로드 실패!"
        reload_drivers_and_recover
        exit 1
    fi
fi
echo "  ✓ 커널 모듈 언로드 완료"

# ------------------------------------------------------------------------------
# [단계 2] 디시리얼라이저 12V 차단 + 칩 생존 시 I2C RESET_ALL 수행
# ------------------------------------------------------------------------------
echo ""
echo "[2/5] 디시리얼라이저 12V 전원 차단 (${OFF_DELAY_SEC}초 대기)..."
if [ "$RELAY_USABLE" = true ]; then
    POWER_CUT=1
    if ! relay_cmd "$RELAY_CMD_POWER_OFF" 2.0 5; then
        if [ "$SKIP_RELAY_CHECK" = true ]; then
            echo "  [WARN] USB 릴레이 전원 차단 명령 실패 — 12V 차단 없이 I2C 리셋을 계속합니다"
        else
            echo "[ERROR] USB 릴레이 전원 차단 명령 실패!"
            reload_drivers_and_recover
            exit 1
        fi
    fi
else
    echo "  - 릴레이 사용 안 함 → 12V 차단 생략"
fi
sleep "$OFF_DELAY_SEC"

# 12V 차단 상태에서 MAX96712(0x6b) 생존 여부 확인 (레지스터 0x000D == 0xa0)
if command -v i2ctransfer >/dev/null 2>&1; then
    DEV_ID="$(read_deser_reg 0x00 0x0d)"
    if [ "$DEV_ID" = "0xa0" ]; then
        echo "  - 디시리얼라이저 칩은 별도 전원으로 동작 중 → I2C 소프트웨어 리셋(RESET_ALL) 수행"
        BEFORE_REGS="$(read_deser_cfg_triple)"
        # MAX96712 REG 0x0013 bit6 (0x40) = RESET_ALL (self-clearing)
        sudo i2ctransfer -f -y "$I2C_BUS" "w3@${DESER_ADDR}" 0x00 0x13 0x40 2>/dev/null || true
        sleep 0.5
        AFTER_REGS="$(read_deser_cfg_triple)"
        echo "    설정 레지스터(0x08A0 0x040B 0x090B): 리셋 전 [$BEFORE_REGS] → 리셋 후 [$AFTER_REGS]"
        if [ "$AFTER_REGS" != "0x04 0x02 0x00" ]; then
            echo "    [WARN] 칩 리셋이 적용되지 않았을 수 있습니다 (기대 기본값: [0x04 0x02 0x00])"
        fi
    else
        echo "  - 12V 차단 중 디시리얼라이저 I2C 무응답 확인 (완전 전원 차단됨)"
    fi
else
    echo "  [WARN] i2ctransfer 도구가 없어 I2C RESET_ALL을 건너뜁니다 (sudo apt-get install -y i2c-tools 권장)"
fi

# ------------------------------------------------------------------------------
# [단계 3] 디시리얼라이저 12V 전원 인가 및 칩 응답 확인
# ------------------------------------------------------------------------------
echo ""
echo "[3/5] 디시리얼라이저 12V 전원 인가 (안정화 ${ON_DELAY_SEC}초 대기)..."
POWER_ON_SENT=false
if [ "$RELAY_USABLE" = true ]; then
    for attempt in 1 2 3; do
        if relay_cmd "$RELAY_CMD_POWER_ON" 2.0 5; then
            POWER_ON_SENT=true
            break
        fi
        echo "  [WARN] USB 릴레이 전원 인가 명령 실패 (${attempt}/3)"
        [ "$attempt" -lt 3 ] && sleep 1
    done
    if [ "$POWER_ON_SENT" != true ]; then
        # 12V 차단 명령을 이미 보냈을 수 있으므로 --skip-relay-check 여도 그대로 진행하지 않음
        # (복구 함수가 한 번 더 인가하고 안정화 대기 후 드라이버를 올림)
        echo "[ERROR] USB 릴레이 전원 인가 명령 실패! (12V 차단 상태일 수 있음)"
        reload_drivers_and_recover
        exit 1
    fi
fi
sleep "$ON_DELAY_SEC"
if [ "$POWER_ON_SENT" = true ]; then
    POWER_CUT=0
fi

# 상태 조회가 되는 릴레이(기본 모드)면 12V 인가를 실제로 확인 — 명령 프레임 유실 대비
if [ "$POWER_ON_SENT" = true ] && [ "$SKIP_RELAY_CHECK" != true ]; then
    check_relay_power
    if [ "$RELAY_POWER" = off ]; then
        echo "  [WARN] 릴레이가 아직 12V 차단 상태로 응답 → 인가 명령 재전송"
        relay_cmd "$RELAY_CMD_POWER_ON" 1.5 5 2>&1 | sed 's/^/    /'
        sleep "$ON_DELAY_SEC"
        check_relay_power
        if [ "$RELAY_POWER" = off ]; then
            echo "[ERROR] 재전송 후에도 릴레이가 12V 차단 상태로 응답합니다 (기대: $RELAY_IDLE_STATE)"
            POWER_CUT=1
            reload_drivers_and_recover
            exit 1
        fi
    fi
    if [ "$RELAY_POWER" = on ]; then
        echo "  ✓ 릴레이 상태 확인: $RELAY_IDLE_STATE (12V 인가)"
    else
        echo "  [WARN] 릴레이 상태 조회 무응답 — 12V 인가 여부를 확인하지 못하고 계속 진행"
    fi
fi

if command -v i2ctransfer >/dev/null 2>&1; then
    DEV_ID_ON="$(read_deser_reg 0x00 0x0d)"
    if [ "$DEV_ID_ON" = "0xa0" ]; then
        echo "  ✓ 디시리얼라이저 칩(MAX96712, ID=${DEV_ID_ON}) 응답 및 선(先)부팅 완료"
    else
        echo "[ERROR] 전원 인가 후 디시리얼라이저(0x6b)가 응답하지 않습니다 (응답값: ${DEV_ID_ON:-없음})"
        reload_drivers_and_recover
        exit 1
    fi
else
    echo "  ✓ 디시리얼라이저 전원 인가 대기 완료"
fi

# ------------------------------------------------------------------------------
# [--reboot 옵션 사용 시] 디시리얼라이저가 켜진 상태에서 젯슨만 재부팅
# ------------------------------------------------------------------------------
if [ "$DO_REBOOT" = true ]; then
    echo ""
    echo "[REBOOT] 디시리얼라이저가 먼저 켜진 상태를 유지한 채 젯슨을 재부팅합니다..."
    trap - HUP INT TERM  # 재부팅 중 받는 TERM 으로 복구 동작이 돌지 않게
    sudo reboot
    exit 0
fi

# ------------------------------------------------------------------------------
# [단계 4] 젯슨 GMSL 커널 드라이버 로드 (max96712 -> sgx-yuv-gmsl2)
# ------------------------------------------------------------------------------
echo ""
echo "[4/5] 젯슨 GMSL 커널 드라이버 로드 중..."
cd "$KO_DIR" || {
    reload_drivers_and_recover
    exit 1
}

if ! lsmod | grep -q "max96712"; then
    if ! sudo insmod max96712.ko; then
        echo "[ERROR] max96712.ko 로드 실패!"
        reload_drivers_and_recover
        exit 1
    fi
    echo "  ✓ max96712.ko 로드 완료"
fi

if ! lsmod | grep -q "sgx_yuv_gmsl2"; then
    if ! sudo insmod sgx-yuv-gmsl2.ko "GMSLMODE_1=${GMSL_MODE}"; then
        echo "[ERROR] sgx-yuv-gmsl2.ko 로드 실패!"
        reload_drivers_and_recover
        exit 1
    fi
    echo "  ✓ sgx-yuv-gmsl2.ko 로드 완료 (GMSLMODE_1=${GMSL_MODE})"
fi

sleep 2

# ------------------------------------------------------------------------------
# [단계 5] 클럭 설정, V4L2 카메라 센서 모드 초기화 및 서비스 재시작
# ------------------------------------------------------------------------------
echo ""
echo "[5/5] NVCSI 클럭 및 카메라 센서 모드(mode=${SENSOR_MODE}) 초기화 중..."
init_cameras

restart_stopped_services
trap - HUP INT TERM

# 성공 기준: 리셋 전에 있던 노드 수. 드라이버가 안 올라가 있어 리셋 전 노드가 없었으면 EXPECTED_CAMERAS
REQUIRED_COUNT="$EXPECTED_COUNT"
[ "$EXPECTED_COUNT" -gt 0 ] || REQUIRED_COUNT="$EXPECTED_CAMERAS"

echo ""
echo "============================================================"
echo " 초기화 완료 (v4l2 제어 설정 성공 채널: ${SUCCESS_COUNT}/4, 기준 ${REQUIRED_COUNT}개 — 리셋 전 노드 ${EXPECTED_COUNT}개)"
echo " ※ 실제 프레임 수신 여부는 아래 명령으로 검증하세요:"
echo "   timeout 15 v4l2-ctl -d /dev/video0 --set-fmt-video=width=1920,height=1536,pixelformat=UYVY --stream-mmap=4 --stream-count=60 --stream-to=/dev/null"
ls -l /dev/video* 2>/dev/null || true
echo "============================================================"

if [ "$SUCCESS_COUNT" -eq 0 ] || [ "$SUCCESS_COUNT" -lt "$REQUIRED_COUNT" ]; then
    echo "[ERROR] 카메라 복구 불완전: 기준 ${REQUIRED_COUNT}개 → 설정 성공 ${SUCCESS_COUNT}개"
    if [ "$EXPECTED_COUNT" -eq 0 ]; then
        echo "        (리셋 전 노드가 없어 EXPECTED_CAMERAS=${EXPECTED_CAMERAS} 기준 — 카메라 수가 다르면 $DEFAULTS_FILE 에 설정)"
    fi
    exit 1
fi
exit 0
