#!/usr/bin/env bash
# ==============================================================================
# 카메라 복구 제어 래퍼 (deser-control@<action>.service 에서 root로 실행)
#
# 웹 대시보드는 이 스크립트를 직접 실행하지 않고
#   sudo -n systemctl start --no-block deser-control@<action>.service
# 로 시작만 요청한다. 리셋 중 jetson2-web 이 중지되어도 이 작업은 별도
# 서비스라서 끝까지 진행되고, 마지막에 웹 서비스가 다시 올라온다.
#
# 동작(action):
#   reset             릴레이 응답 확인 후 칩 리셋 (reset_deser_and_init_cameras.sh)
#   reset-skip-relay  릴레이 무응답이어도 칩 리셋 진행 (--skip-relay-check)
#   relay-status      USB 릴레이 상태 조회만 (전원 변경 없음)
#   --post <action>   systemd ExecStopPost 용: 타임아웃/강제 종료로 상태가 'running' 으로
#                     남았으면 실패로 기록하고, 신호로 끊긴 리셋 뒤 jetson2-web 이 꺼져 있으면 다시 시작
#
# 결과 파일 (/run 은 재부팅 시 초기화됨):
#   /run/deser-control/state.json       마지막 작업 상태 (running | success | failed | aborted)
#   /run/deser-control/last_reset.json  마지막으로 성공한 리셋 (웹 쿨다운 기준, relay-status 와 무관)
#   /run/deser-control/<action>.log     마지막 작업 출력
# ==============================================================================

set -u

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
STATE_DIR="/run/deser-control"
STATE_FILE="$STATE_DIR/state.json"
LAST_RESET_FILE="$STATE_DIR/last_reset.json"
LOCK_FILE="$STATE_DIR/lock"
EXIT_ABORTED=10  # reset_deser_and_init_cameras.sh: 사전 점검에서 중단 (아무것도 변경 안 함)

POST_MODE=false
if [ "${1:-}" = "--post" ]; then
    POST_MODE=true
    shift
fi
ACTION="${1:-}"

case "$ACTION" in
    reset)
        CMD=("$SCRIPT_DIR/reset_deser_and_init_cameras.sh")
        ;;
    reset-skip-relay)
        CMD=("$SCRIPT_DIR/reset_deser_and_init_cameras.sh" --skip-relay-check)
        ;;
    relay-status)
        CMD=(python3 "$SCRIPT_DIR/test_usb_relay.py" --mode status)
        ;;
    *)
        echo "[ERROR] 알 수 없는 동작: '$ACTION' (reset | reset-skip-relay | relay-status)"
        exit 2
        ;;
esac

mkdir -p "$STATE_DIR"
chmod 755 "$STATE_DIR"
LOG_FILE="$STATE_DIR/$ACTION.log"
STARTED="null"

write_state() {
    # $1=status $2=rc(null 가능) $3=finished(null 가능)
    local tmp="$STATE_FILE.tmp"
    printf '{"action":"%s","status":"%s","rc":%s,"started":%s,"finished":%s,"log":"%s"}\n' \
        "$ACTION" "$1" "$2" "$STARTED" "$3" "$LOG_FILE" > "$tmp"
    chmod 644 "$tmp"
    mv -f "$tmp" "$STATE_FILE"
}

if [ "$POST_MODE" = true ]; then
    # 래퍼가 상태를 마무리하지 못하고 끝난 경우(타임아웃 후 SIGKILL, 커널에서 멈춘 자식 등)
    if grep -q "\"action\":\"$ACTION\",\"status\":\"running\"" "$STATE_FILE" 2>/dev/null; then
        STARTED="$(sed -n 's/.*"started":\([0-9][0-9]*\).*/\1/p' "$STATE_FILE")"
        [ -n "$STARTED" ] || STARTED="null"
        case "${EXIT_STATUS:-}" in
            ''|*[!0-9]*) RC=143 ;;
            *) RC="$EXIT_STATUS" ;;
        esac
        echo "[deser-control] $(date '+%F %T') 비정상 종료: $ACTION (${SERVICE_RESULT:-unknown}, rc=$RC)" | tee -a "$LOG_FILE"
        write_state "failed" "$RC" "$(date +%s)"
    fi
    # 신호/타임아웃으로 끊긴 리셋 뒤 웹이 꺼져 있으면 다시 띄움.
    # 정상 종료(0/1/3/10 등)는 리셋 스크립트가 중지한 서비스를 이미 되살렸으므로 건드리지 않음
    # (수동으로 띄운 앱이 카메라를 잡고 있거나 다른 리셋이 잠금을 잡은 경우에 웹을 띄우지 않도록)
    case "${EXIT_STATUS:-}" in
        0|1|2|3|4|10) INTERRUPTED=false ;;
        *) INTERRUPTED=true ;;
    esac
    case "$ACTION" in
        reset|reset-skip-relay)
            if [ "$INTERRUPTED" = true ] \
                && grep -q "\"action\":\"$ACTION\",\"status\":\"failed\"" "$STATE_FILE" 2>/dev/null \
                && ! systemctl is-active --quiet jetson2-web.service; then
                echo "[deser-control] $(date '+%F %T') jetson2-web 이 꺼져 있어 다시 시작합니다" | tee -a "$LOG_FILE"
                systemctl start --no-block jetson2-web.service
            fi
            ;;
    esac
    exit 0
fi

# 동시에 두 작업이 돌지 않도록 잠금 (다른 인스턴스 실행 중이면 즉시 종료)
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "[ERROR] 다른 카메라 복구 작업이 실행 중입니다."
    exit 3
fi
export DESER_LOCK_HELD=1           # 리셋 스크립트는 이 잠금을 그대로 사용 (수동 실행 시에만 직접 잠금)
export DESER_LOG_FILE="$LOG_FILE"  # 신호로 중단될 때 리셋 스크립트가 복구 출력을 남길 곳

STARTED="$(date +%s)"
: > "$LOG_FILE"
chmod 644 "$LOG_FILE"
write_state "running" null null

on_signal() {
    # systemd 중지/타임아웃으로 끝나도 상태가 'running' 으로 남지 않게
    # (bash 는 실행 중인 리셋 스크립트가 원상복구를 마치고 끝난 뒤에 이 트랩을 실행함)
    trap '' HUP INT TERM
    echo "[deser-control] $(date '+%F %T') 신호로 중단: $ACTION" >> "$LOG_FILE"
    write_state "failed" 143 "$(date +%s)"
    exit 143
}
trap on_signal HUP INT TERM

echo "[deser-control] $(date '+%F %T') 시작: $ACTION" | tee -a "$LOG_FILE"
# tee 는 중지 신호를 무시 → 리셋 스크립트가 원상복구를 마칠 때까지 로그 파이프가 살아 있음
"${CMD[@]}" 2>&1 | (trap '' HUP INT TERM; exec tee -a "$LOG_FILE")
RC="${PIPESTATUS[0]}"
trap - HUP INT TERM

# relay-status 는 종료코드 0이어도 무응답이면 실패로 기록
if [ "$ACTION" = "relay-status" ] && [ "$RC" -eq 0 ] && grep -q "(no response)" "$LOG_FILE"; then
    RC=4
fi

if [ "$RC" -eq 0 ]; then
    STATUS="success"
elif [ "$RC" -eq "$EXIT_ABORTED" ]; then
    STATUS="aborted"
else
    STATUS="failed"
fi
echo "[deser-control] $(date '+%F %T') 종료: $ACTION ($STATUS, rc=$RC)" | tee -a "$LOG_FILE"
write_state "$STATUS" "$RC" "$(date +%s)"

# 웹 쿨다운은 성공한 리셋 기준 (중단/실패한 리셋과 relay-status 는 쿨다운을 바꾸지 않음)
if [ "$STATUS" = "success" ] && [ "$ACTION" != "relay-status" ]; then
    cp -f "$STATE_FILE" "$LAST_RESET_FILE.tmp" && mv -f "$LAST_RESET_FILE.tmp" "$LAST_RESET_FILE"
fi
exit "$RC"
