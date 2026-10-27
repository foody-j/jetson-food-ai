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
#
# 결과 파일 (/run 은 재부팅 시 초기화됨):
#   /run/deser-control/state.json   마지막 작업 상태
#   /run/deser-control/<action>.log 마지막 작업 출력
# ==============================================================================

set -u

ACTION="${1:-}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
STATE_DIR="/run/deser-control"
STATE_FILE="$STATE_DIR/state.json"
LOCK_FILE="$STATE_DIR/lock"

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

write_state() {
    # $1=status $2=rc(null 가능) $3=finished(null 가능)
    local tmp="$STATE_FILE.tmp"
    printf '{"action":"%s","status":"%s","rc":%s,"started":%s,"finished":%s,"log":"%s"}\n' \
        "$ACTION" "$1" "$2" "$STARTED" "$3" "$LOG_FILE" > "$tmp"
    chmod 644 "$tmp"
    mv -f "$tmp" "$STATE_FILE"
}

# 동시에 두 작업이 돌지 않도록 잠금 (다른 인스턴스 실행 중이면 즉시 종료)
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "[ERROR] 다른 카메라 복구 작업이 실행 중입니다."
    exit 3
fi

STARTED="$(date +%s)"
: > "$LOG_FILE"
chmod 644 "$LOG_FILE"
write_state "running" null null

echo "[deser-control] $(date '+%F %T') 시작: $ACTION" | tee -a "$LOG_FILE"
"${CMD[@]}" 2>&1 | tee -a "$LOG_FILE"
RC="${PIPESTATUS[0]}"

# relay-status 는 종료코드 0이어도 무응답이면 실패로 기록
if [ "$ACTION" = "relay-status" ] && [ "$RC" -eq 0 ] && grep -q "(no response)" "$LOG_FILE"; then
    RC=4
fi

if [ "$RC" -eq 0 ]; then
    STATUS="success"
else
    STATUS="failed"
fi
echo "[deser-control] $(date '+%F %T') 종료: $ACTION ($STATUS, rc=$RC)" | tee -a "$LOG_FILE"
write_state "$STATUS" "$RC" "$(date +%s)"
exit "$RC"
