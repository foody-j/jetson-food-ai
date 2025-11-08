# 시스템 시간 설정 가이드

## 개요
Jetson Orin 시스템에서 시간 설정 및 동기화 방법을 설명합니다.

## 시간 확인

### 현재 시스템 시간 확인
```bash
date
timedatectl
```

### 타임존 확인
```bash
timedatectl | grep "Time zone"
```

## 오프라인 환경에서 시간 설정

### 1. 수동으로 날짜/시간 설정
```bash
# 형식: sudo date MMDDhhmmYYYY.ss
# MM = 월 (01-12)
# DD = 일 (01-31)
# hh = 시 (00-23)
# mm = 분 (00-59)
# YYYY = 연도
# ss = 초 (00-59)

# 예시: 2024년 11월 5일 14시 30분 00초
sudo date 110514302024.00
```

### 2. 타임존 설정 (서울)
```bash
sudo timedatectl set-timezone Asia/Seoul
```

### 3. 하드웨어 시계(RTC)에 현재 시간 저장
```bash
# 시스템 시간을 하드웨어 시계에 저장
sudo hwclock --systohc
```

### 4. 설정 확인
```bash
date
timedatectl
hwclock
```

## 온라인 환경에서 자동 시간 동기화

### 1. NTP 자동 동기화 활성화
```bash
sudo timedatectl set-ntp true
```

### 2. 동기화 상태 확인
```bash
timedatectl status
```

"System clock synchronized: yes" 가 표시되면 성공

### 3. NTP 서버 확인
```bash
systemctl status systemd-timesyncd
```

## 부팅 시 자동 시간 복원

시스템이 재부팅될 때 하드웨어 시계(RTC)에서 시간을 읽어옵니다.
따라서 **한 번만 올바른 시간을 설정하고 hwclock에 저장**하면 재부팅 후에도 시간이 유지됩니다.

## 프로그램 내 시간 처리

현재 Jetson #1, #2, 진동센서 프로그램은 모두 KST(UTC+9) 타임존을 명시적으로 사용하도록 수정되었습니다.

### 시간 함수
```python
from datetime import datetime, timezone, timedelta

# KST 타임존 정의
KST = timezone(timedelta(hours=9))

def get_current_time():
    """현재 한국 시간 반환 (KST)"""
    return datetime.now().replace(tzinfo=KST)
```

### 사용 예시
```python
# datetime.now() 대신 get_current_time() 사용
now = get_current_time()
timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
```

## 문제 해결

### RTC가 1970년으로 초기화된 경우
```bash
# 1. 현재 시간 수동 설정
sudo date 110514302024.00

# 2. RTC에 저장
sudo hwclock --systohc

# 3. 확인
hwclock
date
```

### 시간이 자꾸 리셋되는 경우
```bash
# RTC 배터리 상태 확인
dmesg | grep -i rtc

# RTC 읽기 테스트
sudo hwclock --verbose

# RTC에 시간 강제 저장
sudo hwclock --set --date="2024-11-05 14:30:00"
sudo hwclock --systohc
```

### NTP 동기화가 안 되는 경우 (오프라인)
오프라인 환경에서는 NTP 동기화를 사용할 수 없습니다.
다음 중 하나를 선택하세요:

1. **수동 설정**: 위의 "오프라인 환경에서 시간 설정" 참조
2. **외부 시간 소스**: GPS 모듈 또는 RTC 모듈 사용
3. **개발 PC 연결**: 배포 시 개발 PC의 시간을 복사

## 배포 시 시간 설정 절차

### 방법 1: 수동 설정 스크립트
```bash
#!/bin/bash
# set_time.sh

# 현재 시간을 입력받아 설정
echo "현재 시간을 입력하세요 (예: 2024-11-05 14:30:00)"
read -p "날짜 시간: " datetime

sudo date -s "$datetime"
sudo hwclock --systohc

echo "시간 설정 완료:"
date
```

### 방법 2: 개발 PC에서 시간 복사
```bash
# 개발 PC에서 실행
ssh jetson@192.168.x.x "sudo date -s '$(date '+%Y-%m-%d %H:%M:%S')' && sudo hwclock --systohc"
```

## 진동센서 프로그램 Y축 범위 설정

`vibration_config.json` 파일에서 Y축 범위를 설정할 수 있습니다:

```json
{
  "y_axis_limits": {
    "acc": {"min": -20, "max": 20},
    "vel": {"min": -100, "max": 100},
    "disp": {"min": -500, "max": 500},
    "fft": {"min": 0, "max": 1000}
  },
  "auto_scale": false
}
```

- `auto_scale: false` - Y축 범위 고정 (진동 비교 용이)
- `auto_scale: true` - Y축 자동 조정 (전체 범위 보기)

## 참고사항

1. **시스템 시간 vs 프로그램 시간**
   - 시스템 시간이 틀려도 프로그램은 KST 기준으로 동작
   - 로그 파일 타임스탬프는 프로그램에서 생성되므로 정확함

2. **타임존 설정 중요성**
   - 항상 `Asia/Seoul` 타임존 사용
   - 타임존이 잘못 설정되면 9시간 차이 발생

3. **RTC 백업 배터리**
   - Jetson Orin은 CR2032 배터리로 RTC 유지
   - 배터리 교체 시 시간 재설정 필요

4. **시간 점프 주의**
   - 시간을 크게 변경하면 일부 서비스가 오동작할 수 있음
   - 가능하면 시스템 재부팅 후 시간 설정
