#!/bin/bash
# 카메라 복구 버튼(웹 대시보드)용 systemd 서비스 + sudoers 설치 스크립트
#
# 설치 내용:
#   /etc/systemd/system/deser-control@.service   root로 deser_control.sh 실행
#   /etc/sudoers.d/deser-control                 웹 사용자에게 아래 3개 명령만 비밀번호 없이 허용
#       systemctl start --no-block deser-control@{reset,reset-skip-relay,relay-status}.service
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

if [ "${1:-}" = "--uninstall" ]; then
    sudo rm -f "$UNIT_FILE" "$SUDOERS_FILE"
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
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/deser_control.sh %i
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

echo "[3] systemd 재로드"
sudo systemctl daemon-reload

echo "[4] 비밀번호 없이 실행되는지 확인 (릴레이 상태 조회 — 전원 변경 없음)"
sudo -k  # 캐시된 sudo 인증을 지워서 NOPASSWD 규칙만으로 실행되는지 확인
if sudo -n "$SYSTEMCTL" start --no-block deser-control@relay-status.service; then
    sleep 5
    cat /run/deser-control/relay-status.log 2>/dev/null || true
else
    echo "[WARN] sudo -n 실행 실패 — $SUDOERS_FILE 확인 필요"
fi

echo ""
echo "설치 완료. jetson2-web 을 재시작하면 대시보드에 'Camera Recovery' 버튼이 활성화됩니다:"
echo "  sudo systemctl restart jetson2-web"
