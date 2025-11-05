# 📦 버전 관리 가이드

## 🎯 목적

다른 Jetson 보드에 배포할 때 **버전 불일치**로 인한 문제를 방지합니다.

---

## ⚠️ 문제 상황

```bash
# 개발 Jetson (현재)
pip3 install ultralytics  # 버전 8.3.224 설치됨

# 배포 Jetson (6개월 후)
pip3 install ultralytics  # 버전 8.5.0 설치됨 → 호환 문제 발생!
```

---

## ✅ 해결책: requirements.txt

### 1. 현재 작동하는 버전 기록

```bash
cd ~/jetson-camera-monitor
pip3 freeze | grep -E 'opencv|numpy|Pillow|ultralytics|paho-mqtt|psutil' > requirements.txt
```

**결과: `requirements.txt`**
```
numpy==1.26.4
opencv-python==4.12.0.88
Pillow==9.0.1
ultralytics==8.3.224
paho-mqtt==2.1.0
psutil==7.1.3
```

### 2. 버전 고정 설치

```bash
# requirements.txt가 있으면 자동으로 사용
./install.sh

# 또는 수동 설치
pip3 install -r requirements.txt
```

### 3. 설치 후 버전 확인

```bash
./check_versions.sh
```

**출력 예시:**
```
[Python 패키지 버전]
numpy:          1.26.4
opencv-python:  4.12.0.88
Pillow:         9.0.1
ultralytics:    8.3.224
paho-mqtt:      2.1.0
psutil:         7.1.3

[requirements.txt 비교]
  ✅ numpy: 1.26.4 (일치)
  ✅ opencv-python: 4.12.0.88 (일치)
  ✅ Pillow: 9.0.1 (일치)
  ✅ ultralytics: 8.3.224 (일치)
  ✅ paho-mqtt: 2.1.0 (일치)
  ✅ psutil: 7.1.3 (일치)
```

---

## 🔧 install.sh 동작 방식

```bash
# install.sh 내부 로직
if [ -f "requirements.txt" ]; then
    echo "버전 고정 설치 (requirements.txt 사용)"
    pip3 install -r requirements.txt
else
    echo "⚠️ WARNING: 최신 버전 설치 (버전 불일치 위험)"
    pip3 install ultralytics opencv-python ...
fi
```

**중요:** `requirements.txt`가 있으면 **자동으로** 버전 고정 설치!

---

## 📋 배포 체크리스트

### 새 Jetson 보드에 배포 시:

- [ ] 1. `requirements.txt` 파일이 프로젝트에 포함되어 있는가?
- [ ] 2. `./install.sh` 실행 시 "[INFO] requirements.txt 사용" 메시지 확인
- [ ] 3. `./check_versions.sh`로 버전 일치 확인
- [ ] 4. 프로그램 정상 동작 테스트

---

## 🆚 버전 관리 전/후 비교

### ❌ 버전 관리 없음 (위험)

```bash
# 6개월 전
pip3 install ultralytics  # 8.3.224

# 오늘
pip3 install ultralytics  # 8.5.0 → API 변경, 호환 불가!
```

### ✅ 버전 관리 있음 (안전)

```bash
# 6개월 전
pip3 install -r requirements.txt  # 8.3.224

# 오늘
pip3 install -r requirements.txt  # 8.3.224 (동일!)
```

---

## 🔍 버전 불일치 감지

### 증상:

```python
# ImportError: cannot import name 'YOLO' from 'ultralytics'
# AttributeError: 'YOLO' object has no attribute 'predict'
# RuntimeError: CUDA version mismatch
```

### 확인:

```bash
./check_versions.sh

# 출력:
  ⚠️  ultralytics: 8.5.0 (예상: 8.3.224)
```

### 해결:

```bash
pip3 uninstall ultralytics
pip3 install ultralytics==8.3.224
# 또는
pip3 install -r requirements.txt --force-reinstall
```

---

## 📝 버전 업데이트 절차

새 버전 테스트 후 업데이트하려면:

```bash
# 1. 새 버전 설치 및 테스트
pip3 install --upgrade ultralytics
python3 jetson1_monitoring/JETSON1_INTEGRATED.py  # 테스트

# 2. 정상 작동 확인 후 requirements.txt 업데이트
pip3 freeze | grep ultralytics > temp.txt
# requirements.txt 수동 편집

# 3. Git 커밋
git add requirements.txt
git commit -m "Update ultralytics to 8.5.0 (tested)"
```

---

## ⚙️ 고급: 오프라인 설치

인터넷 없는 환경에서 배포:

```bash
# 1. 개발 Jetson에서 (인터넷 있음)
cd ~/jetson-camera-monitor
mkdir -p offline_packages
pip3 download -r requirements.txt -d offline_packages

# 2. USB로 복사 후, 타겟 Jetson에서 (오프라인)
cd ~/jetson-camera-monitor
pip3 install --no-index --find-links=offline_packages -r requirements.txt
```

---

## 🎯 핵심 요약

1. ✅ **requirements.txt** 파일로 버전 고정
2. ✅ **install.sh** 자동으로 버전 고정 설치
3. ✅ **check_versions.sh** 설치 후 버전 확인
4. ✅ 동일한 JetPack 버전 (6.2) 사용
5. ✅ 인터넷 연결 시 자동 설치, 오프라인 설치 지원

**결과:** 언제 어디서 설치해도 **동일한 버전**으로 안정적 동작! 🚀

---

**작성일:** 2025-01-05
**테스트 환경:** JetPack 6.2 (L4T R36.4.3)
