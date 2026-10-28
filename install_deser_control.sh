#!/bin/bash
# 카메라 복구 버튼(웹 대시보드)용 systemd 서비스 + sudoers 설치 스크립트
#
# 설치 내용:
#   /etc/systemd/system/deser-control@.service   root로 deser_control.sh 실행
#   /etc/sudoers.d/deser-control                 웹 사용자에게 아래 3개 명령만 비밀번호 없이 허용
#       systemctl start --no-block deser-control@{reset,reset-skip-relay,relay-status}.service
#   /etc/systemd/system/<jetsonN>-web-restart.service.d/deser-reset.conf
#       새벽 웹 재시작 타이머가 있으면 웹 재시작 대신 칩 리셋(리셋 → 드라이버 재로드 → 웹 시작)으로 교체
#
# 사용법 (웹 서비스를 실행하는 사용자 계정으로):
#   cd ~/jetson-food-ai && ./install_deser_control.sh
# 제거:
#   ./install_deser_control.sh --uninstall

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_USER="$(id -un)"
WEB_HOME="$(getent passwd "$WEB_USER" | cut -d: -f6)"
UNIT_FILE="/etc/systemd/system/deser-control@.service"
SUDOERS_FILE="/etc/sudoers.d/deser-control"
SYSTEMCTL="/usr/bin/systemctl"  # web/camera_recovery.py 와 같은 경로여야 sudoers 가 일치함
ACTIONS=(reset reset-skip-relay relay-status)
RESTART_UNITS=(jetson1-web-restart.service jetson2-web-restart.service)
DROPIN_NAME="deser-reset.conf"

if [ "${1:-}" = "--uninstall" ]; then
    sudo rm -f "$UNIT_FILE" "$SUDOERS_FILE"
    for unit in "${RESTART_UNITS[@]}"; do
        sudo rm -f "/etc/systemd/system/$unit.d/$DROPIN_NAME"
    done
    sudo systemctl daemon-reload
    echo "제거 완료"
    exit 0
fi

if [ "$WEB_USER" = "root" ] || [ -z "$WEB_HOME" ]; then
    echo "[ERROR] 웹 서비스를 실행하는 일반 사용자 계정으로 실행하세요 (sudo 없이)."
    exit 1
fi

# 사용자 경로에만 설치된 pyserial 을 root 에서도 쓰기 위한 경로
USER_SITE="$(python3 -c 'import site; print(site.getusersitepackages())')"

echo "=========================================="
echo "카메라 복구 서비스 설치"
echo "=========================================="
echo "웹 사용자     : $WEB_USER"
echo "프로젝트 경로 : $SCRIPT_DIR"
echo "PYTHONPATH    : $USER_SITE"
echo "systemctl     : $SYSTEMCTL"
echo ""

chmod +x "$SCRIPT_DIR/deser_control.sh" "$SCRIPT_DIR/reset_deser_and_init_cameras.sh"

echo "[1] systemd 서비스 작성: $UNIT_FILE"
sudo tee "$UNIT_FILE" > /dev/null <<EOF
[Unit]
Description=GMSL camera recovery (%i)

[Service]
Type=oneshot
User=root
Environment="PYTHONPATH=$USER_SITE"
# 릴레이 스크립트 출력을 바로 로그에 기록 (대시보드 Log 에 진행 상황이 실시간으로 보이게)
Environment=PYTHONUNBUFFERED=1
# 장비별 릴레이 설정(WIRING, RELAY_PORT, I2C_BUS 등)은 이 파일에 KEY=값 형식으로 (없으면 기본값)
# 터미널에서 reset_deser_and_init_cameras.sh 를 직접 실행할 때도 같은 파일을 읽음
EnvironmentFile=-/etc/default/deser-control
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/deser_control.sh %i
# 타임아웃/강제 중지로 끝나도 상태를 기록하고, 신호로 끊긴 리셋 뒤 꺼진 jetson2-web 을 다시 시작
ExecStopPost=-$SCRIPT_DIR/deser_control.sh --post %i
TimeoutStartSec=300
StandardOutput=journal
StandardError=journal
EOF

echo "[2] sudoers 작성: $SUDOERS_FILE"
TMP_SUDOERS="$(mktemp)"
{
    echo "# jetson-food-ai 웹 대시보드 카메라 복구 버튼 (install_deser_control.sh)"
    CMDS=()
    for a in "${ACTIONS[@]}"; do
        CMDS+=("$SYSTEMCTL start --no-block deser-control@$a.service")
    done
    (IFS=','; echo "$WEB_USER ALL=(root) NOPASSWD: ${CMDS[*]}" | sed 's/,/, /g')
} > "$TMP_SUDOERS"
if ! sudo visudo -cf "$TMP_SUDOERS" > /dev/null; then
    echo "[ERROR] sudoers 문법 오류 — 설치 중단"
    cat "$TMP_SUDOERS"
    rm -f "$TMP_SUDOERS"
    exit 1
fi
sudo install -m 440 -o root -g root "$TMP_SUDOERS" "$SUDOERS_FILE"
rm -f "$TMP_SUDOERS"

echo "[3] 새벽 재시작 타이머 → 칩 리셋으로 교체"
# 웹만 재시작하면 카메라를 다시 열 때 칩이 꼬여 아침까지 멈춘 적이 있음 (울산 2026-09-15~18, 매일 02:02 시작)
FOUND_RESTART=false
for unit in "${RESTART_UNITS[@]}"; do
    [ -f "/etc/systemd/system/$unit" ] || continue
    FOUND_RESTART=true
    sudo mkdir -p "/etc/systemd/system/$unit.d"
    sudo tee "/etc/systemd/system/$unit.d/$DROPIN_NAME" > /dev/null <<EOF
# install_deser_control.sh 가 작성 — 웹 재시작 대신 칩 리셋 (중지했던 웹은 리셋 스크립트가 다시 시작)
[Service]
ExecStart=
ExecStart=$SYSTEMCTL start deser-control@reset-skip-relay.service
TimeoutStartSec=420
EOF
    echo "  $unit → deser-control@reset-skip-relay"
done
[ "$FOUND_RESTART" = true ] || echo "  (새벽 재시작 타이머 없음 — 건너뜀)"

echo "[4] systemd 재로드"
sudo systemctl daemon-reload

echo "[5] 비밀번호 없이 실행되는지 확인 (릴레이 상태 조회 — 전원 변경 없음)"
sudo -k  # 캐시된 sudo 인증을 지워서 NOPASSWD 규칙만으로 실행되는지 확인
STATUS_LOG="/run/deser-control/relay-status.log"
T0="$(date +%s)"
if sudo -n "$SYSTEMCTL" start --no-block deser-control@relay-status.service; then
    # 릴레이가 무응답이면 조회 재시도로 6초 이상 걸림 → 고정 대기 대신 종료 줄이 기록될 때까지 대기
    for _ in $(seq 1 30); do
        sleep 1
        if [ "$(stat -c %Y "$STATUS_LOG" 2>/dev/null || echo 0)" -ge "$T0" ] \
            && grep -q '종료:' "$STATUS_LOG" 2>/dev/null; then
            break
        fi
    done
    cat "$STATUS_LOG" 2>/dev/null || true
    if grep -q '시작: relay-status' "$STATUS_LOG" 2>/dev/null; then
        echo "  ✓ 비밀번호 없이 복구 서비스 실행 확인"
        echo "    (릴레이가 '(no response)' / failed 여도 설치는 정상 — 상태 조회에 응답하지 않는 릴레이는"
        echo "     대시보드에서 '칩 리셋 (릴레이 무시)' 버튼 사용)"
    fi
else
    echo "[WARN] sudo -n 실행 실패 — $SUDOERS_FILE 확인 필요"
fi

echo ""
echo "설치 완료. jetson2-web 을 재시작하면 대시보드의 '카메라 복구' 버튼이 활성화됩니다:"
echo "  sudo systemctl restart jetson2-web"
echo "  (웹이 다시 뜬 뒤(약 1분) 이미 열려 있는 대시보드/키오스크 화면은 F5 로 새로고침)"
echo "릴레이 배선/포트가 기본값(nc, CH340 by-id, I2C bus 9)과 다르거나 카메라가 4대가 아니면"
echo "/etc/default/deser-control 에 WIRING=no / RELAY_PORT=/dev/serial/by-id/... / I2C_BUS=9 /"
echo "EXPECTED_CAMERAS=3 처럼 적어 두세요 (대시보드와 터미널 수동 실행 모두 적용)."
