# Python 디버그 출력 활성화 가이드

## 문제
- journalctl로 진동센서 등 자식 프로세스의 print() 메시지가 안 보임
- 파이썬 출력 버퍼링 때문에 실시간 로그가 표시되지 않음

## 해결 방법
서비스 파일에 `PYTHONUNBUFFERED=1` 환경변수 추가

---

## 젯슨 1번 수정

### 파일 위치
실제 설치된 서비스 파일을 확인하세요:
```bash
systemctl status jetson1-ai
# 또는
systemctl status jetson-monitor
```

위 명령어로 나온 서비스 파일 경로를 찾아서 수정합니다.

### 수정 내용
**Environment 섹션에 한 줄 추가:**

```ini
[Service]
Type=simple
User=dkuyj
WorkingDirectory=/home/dkuyj/jetson-camera-monitor/autostart_autodown
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/dkuyj/.Xauthority"
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONUNBUFFERED=1"          ← 이 줄 추가!
ExecStart=/usr/bin/python3 /home/dkuyj/jetson-camera-monitor/autostart_autodown/JETSON1_INTEGRATED.py
...
```

---

## 젯슨 2번 수정

### 파일 위치
실제 설치된 서비스 파일을 확인하세요:
```bash
systemctl status jetson2-ai
```

위 명령어로 나온 서비스 파일 경로를 찾아서 수정합니다.

### 수정 내용
**Environment 섹션에 한 줄 추가:**

```ini
[Service]
Type=simple
User=yjk
WorkingDirectory=/home/yjk/jetson-food-ai/jetson2_frying_ai
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/yjk/.Xauthority"
Environment="PYTHONUNBUFFERED=1"          ← 이 줄 추가!
ExecStart=/usr/bin/python3 /home/yjk/jetson-food-ai/jetson2_frying_ai/JETSON2_INTEGRATED.py
...
```

---

## 적용 방법

### 1. 서비스 파일 수정 (각 젯슨 PC에서)
```bash
# 서비스 파일 경로 확인
systemctl status jetson1-ai  # 또는 jetson2-ai

# 실제 경로 예시 (출력에서 확인)
sudo nano /etc/systemd/system/jetson1-ai.service
# 또는
sudo nano /etc/systemd/system/jetson2-ai.service
```

### 2. systemd 재시작
```bash
sudo systemctl daemon-reload
sudo systemctl restart jetson1-ai  # 또는 jetson2-ai
```

### 3. 확인
```bash
# 실시간 로그 확인 (진동센서 출력 포함)
sudo journalctl -u jetson1-ai -f
# 또는
sudo journalctl -u jetson2-ai -f
```

---

## 결과
- ✅ 진동센서 print() 메시지가 journalctl에 실시간으로 표시됨
- ✅ 직접 실행할 때와 동일한 디버그 메시지 출력
- ✅ 버퍼링 없이 즉시 로그 확인 가능

---

## 주의사항
- 서비스 파일 수정 시 **sudo 권한 필요**
- 수정 후 반드시 **daemon-reload** 실행
- 재시작 후 **로그 확인**으로 정상 동작 확인
