# DB Manager 개발 도구 모음

이 디렉토리는 DB Manager 프로젝트의 개발, 테스트, 디버깅을 위한 도구들을 포함합니다.

## 📁 파일 구조

```
tools/
├── README.md                # 이 파일
├── debug_toolkit.py         # 통합 디버그 도구
├── test_runner.py          # 간단한 테스트 실행기
└── comprehensive_test.py   # 종합 테스트 스위트
```

## 🔧 도구 설명

### 1. debug_toolkit.py
**통합 디버그 및 진단 도구**

DB Manager의 각종 컴포넌트 상태를 진단하고 문제를 찾는 도구입니다.

**주요 기능:**
- 데이터베이스 연결 및 상태 확인
- 장비 유형 및 파라미터 데이터 검증
- 서비스 레이어 상태 진단
- 종합적인 시스템 헬스 체크

**사용법:**
```bash
# 종합 진단 (기본)
python tools/debug_toolkit.py

# 개별 진단
python tools/debug_toolkit.py health      # DB 상태만
python tools/debug_toolkit.py equipment  # 장비 유형만
python tools/debug_toolkit.py services   # 서비스 레이어만
python tools/debug_toolkit.py params [장비명]  # 특정 장비 파라미터
```

**출력 예시:**
```
🚀 DB Manager 종합 진단 시작
================================
⏰ 실행 시간: 2025-07-02 12:00:00

🔍 데이터베이스 상태 확인
================================
📋 테이블 목록: ['Equipment_Types', 'Default_DB_Values', ...]
  📊 Equipment_Types: 5개 레코드
  📊 Default_DB_Values: 1250개 레코드

📊 진단 결과 요약
================================
✅ 정상 데이터베이스 상태
✅ 정상 장비 유형
✅ 정상 서비스 레이어
✅ 정상 파라미터 조작
================================
전체 결과: 4/4 정상

🎉 모든 진단 항목이 정상입니다!
```

### 2. test_runner.py
**간단한 테스트 실행기**

빠른 테스트 실행을 위한 lightweight 도구입니다.

**주요 기능:**
- 모듈별 단위 테스트
- 통합 테스트 실행
- 빠른 검증을 위한 간소화된 출력

**사용법:**
```bash
# 전체 테스트 (기본)
python tools/test_runner.py

# 개별 모듈 테스트
python tools/test_runner.py data         # data_utils 모듈만
python tools/test_runner.py schema       # DB 스키마만
python tools/test_runner.py services     # 서비스 레이어만
python tools/test_runner.py integration  # 통합 테스트만
```

### 3. comprehensive_test.py
**종합 테스트 스위트**

unittest 기반의 체계적이고 완전한 테스트 도구입니다.

**주요 기능:**
- unittest 프레임워크 기반
- 성능 및 메모리 사용량 측정
- 상세한 테스트 리포팅
- 회귀 테스트 지원

**사용법:**
```bash
# 전체 테스트 스위트 (기본)
python tools/comprehensive_test.py

# 개별 테스트 클래스
python tools/comprehensive_test.py data         # TestDataUtils
python tools/comprehensive_test.py schema       # TestDatabaseSchema
python tools/comprehensive_test.py services     # TestServiceLayer
python tools/comprehensive_test.py integration  # TestIntegration
python tools/comprehensive_test.py performance  # PerformanceTestCase
```

**출력 예시:**
```
🚀 DB Manager 종합 테스트 스위트 시작
====================================
⏰ 시작 시간: 2025-07-02 12:00:00
🖥️ 시스템: 8CPU, 16GB RAM

📋 TestDataUtils 실행:
--------------------------------------------------
test_numeric_sort_key ... ok
test_calculate_string_similarity ... ok
test_safe_convert_functions ... ok
test_string_utilities ... ok

성능 측정 - 실행시간: 0.125초, 메모리 증가: 2.1MB

📊 종합 테스트 결과 요약
====================================
총 테스트: 24
✅ 성공: 24
❌ 실패: 0
🚫 오류: 0
📈 성공률: 100.0%

🎉 모든 테스트가 성공적으로 완료되었습니다!
```

## 🎯 사용 시나리오

### 개발 중 빠른 확인
```bash
python tools/test_runner.py data
```

### 문제 진단
```bash
python tools/debug_toolkit.py
```

### 배포 전 전체 검증
```bash
python tools/comprehensive_test.py
```

### 특정 장비 문제 확인
```bash
python tools/debug_toolkit.py params "NX-Mask"
```

## 📋 의존성

모든 도구는 프로젝트의 기본 의존성만 사용합니다:
- pandas
- sqlite3 (내장)
- psutil (성능 측정용)

## 🔄 통합된 파일들

이 도구들은 다음 기존 파일들을 대체합니다:
- `debug_db.py` → `debug_toolkit.py`
- `debug_params.py` → `debug_toolkit.py`
- `debug_schema.py` → `debug_toolkit.py`
- `debug_services.py` → `debug_toolkit.py`
- `test_comparison_cleanup.py` → `comprehensive_test.py`
- `test_data_utils.py` → `test_runner.py`, `comprehensive_test.py`
- `test_full_integration.py` → `comprehensive_test.py`
- `test_modularization.py` → `comprehensive_test.py`
- `test_suite.py` → `comprehensive_test.py`

## 📝 유지보수 가이드

### 새로운 테스트 추가
1. 단순한 테스트: `test_runner.py`에 추가
2. 체계적인 테스트: `comprehensive_test.py`에 새 TestCase 클래스 추가

### 새로운 진단 기능 추가
`debug_toolkit.py`의 DebugToolkit 클래스에 새 메서드 추가

### 성능 벤치마크 추가
`comprehensive_test.py`의 PerformanceTestCase에 새 테스트 추가

## ⚠️ 주의사항

1. **DB 상태**: 테스트 실행 시 기존 DB 데이터에 영향을 줄 수 있습니다
2. **임시 데이터**: comprehensive_test.py는 테스트 후 자동으로 정리합니다
3. **메모리 사용량**: 성능 테스트는 추가 메모리를 사용할 수 있습니다

## 📞 문제 해결

1. **Import 오류**: src/ 경로가 올바른지 확인
2. **DB 연결 실패**: data/local_db.sqlite 파일 존재 여부 확인
3. **서비스 테스트 실패**: 서비스 레이어가 비활성화된 경우 정상