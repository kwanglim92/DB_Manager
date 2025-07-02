# 모듈화된 도움말 시스템

DB Manager의 완전히 모듈화된 도움말 시스템입니다. 이 시스템은 다른 프로젝트에서도 쉽게 재사용할 수 있도록 설계되었습니다.

## 📁 구조

```
help_system/
├── __init__.py                 # 패키지 진입점
├── README.md                   # 이 파일
├── core/                       # 핵심 로직
│   ├── __init__.py
│   ├── app_info.py            # 애플리케이션 정보 관리
│   └── help_service.py        # 도움말 콘텐츠 관리
├── ui/                        # UI 컴포넌트
│   ├── __init__.py
│   ├── dialogs.py             # 도움말 다이얼로그들
│   └── help_manager.py        # UI 관리자
└── utils/                     # 유틸리티 함수
    ├── __init__.py
    └── help_utils.py          # 편의 함수들
```

## 🚀 빠른 시작

### 1. 간단한 사용법

```python
import tkinter as tk
from app.help_system.utils.help_utils import quick_setup_help_system, setup_help_system_with_menu

# 메인 윈도우 생성
window = tk.Tk()
window.title("내 애플리케이션")

# 도움말 시스템 빠른 설정
help_manager = quick_setup_help_system(
    parent_window=window,
    app_name="내 애플리케이션",
    version="1.0.0",
    developer="개발자 이름",
    shortcuts={"F1": "도움말", "Ctrl+O": "열기"},
    features=["기능1", "기능2", "기능3"]
)

# 메뉴바에 도움말 메뉴 추가
menubar = tk.Menu(window)
window.config(menu=menubar)

setup_help_system_with_menu(window, menubar, help_manager)

window.mainloop()
```

### 2. DB Manager 전용 설정

```python
from app.help_system.utils.help_utils import create_db_manager_help_system

# DB Manager 전용 도움말 시스템 (사전 구성된 콘텐츠 포함)
help_manager = create_db_manager_help_system(parent_window)
help_manager.setup_help_menu(menubar)
```

## 🔧 고급 사용법

### 커스텀 애플리케이션 정보

```python
from app.help_system.core.app_info import AppInfo, RevisionInfo, AppInfoManager

# 애플리케이션 정보 정의
app_info = AppInfo(
    name="고급 애플리케이션",
    version="2.1.0",
    release_date="2025-07-02",
    developer="개발팀",
    organization="회사명",
    contact="support@company.com",
    description="상세한 애플리케이션 설명...",
    website="https://company.com",
    license="MIT License"
)

# 리비전 히스토리 정의
revisions = [
    RevisionInfo(
        version="2.1.0",
        date="2025-07-02",
        summary="새로운 기능 추가",
        details={
            "New Features": ["기능 A", "기능 B"],
            "Improvements": ["성능 개선", "UI 개선"],
            "Bug Fixes": ["버그 수정 1", "버그 수정 2"]
        }
    )
]

app_info_manager = AppInfoManager(app_info, revisions)
```

### 커스텀 도움말 서비스

```python
from app.help_system.core.help_service import HelpService

help_service = HelpService("내 애플리케이션")

# 키보드 단축키 추가
help_service.add_shortcuts_dict({
    "Ctrl+N": "새 파일",
    "Ctrl+O": "파일 열기",
    "F1": "도움말"
}, category="파일 관리")

# 주요 기능 추가
help_service.add_features_list([
    "파일 관리",
    "텍스트 편집",
    "검색 기능"
], category="핵심 기능")

# FAQ 추가
help_service.add_faqs_list([
    {"Q": "파일을 어떻게 여나요?", "A": "Ctrl+O를 누르세요."},
    {"Q": "저장은 어떻게 하나요?", "A": "Ctrl+S를 누르세요."}
], category="기본 사용법")
```

### 완전한 도움말 시스템 구성

```python
from app.help_system.ui.help_manager import HelpUIManager

# 도움말 UI 관리자 생성
help_ui_manager = HelpUIManager(
    parent_window=window,
    help_service=help_service,
    app_info_manager=app_info_manager,
    logger=logger
)

# 메뉴 설정
help_ui_manager.setup_help_menu(menubar)
help_ui_manager.setup_help_bindings()

# 개별 다이얼로그 호출
help_ui_manager.show_about_dialog()
help_ui_manager.show_user_guide()
help_ui_manager.show_troubleshooting_guide()
```

## 🔄 기존 시스템과의 통합

### ConfigManager와의 통합

```python
from app.config_manager import ConfigManager

# parent_window 매개변수 추가
config_manager = ConfigManager(
    config=config,
    db_schema=db_schema,
    update_log_callback=update_log,
    parent_window=window  # 이 매개변수 추가
)

# 자동으로 모듈화된 도움말 시스템 사용
config_manager.show_about()
config_manager.show_user_guide()
config_manager.show_troubleshooting_guide()  # 새로운 기능
```

### 기존 함수 호환성

```python
from app.config_manager import show_about, show_user_guide, show_troubleshooting_guide

# 기존 방식대로 호출 가능 (자동으로 새 시스템 사용)
show_about(parent_window)
show_user_guide(parent_window=parent_window)
show_troubleshooting_guide(parent_window)
```

## 📋 주요 기능

### 1. 애플리케이션 정보 관리
- 기본 애플리케이션 메타데이터
- 상세한 리비전 히스토리
- 더블클릭으로 리비전 상세 내용 보기

### 2. 도움말 콘텐츠 관리
- 키보드 단축키 목록
- 주요 기능 설명
- FAQ 섹션
- 카테고리별 구분

### 3. UI 컴포넌트
- 프로그램 정보 다이얼로그
- 사용자 가이드 다이얼로그 (탭 구조)
- 문제 해결 가이드 다이얼로그
- 자동 메뉴 통합

### 4. 유틸리티 함수
- 빠른 설정 함수
- 메뉴 통합 함수
- 기존 시스템 호환 어댑터

## 🎨 사용자 인터페이스

### 프로그램 정보 다이얼로그
- 애플리케이션 기본 정보 표시
- 리비전 히스토리 목록
- 리비전 더블클릭으로 상세 내용 확인

### 사용자 가이드 다이얼로그
- **개요**: 전체 가이드 텍스트
- **단축키**: 키보드 단축키 표
- **기능**: 주요 기능 목록
- **FAQ**: 자주 묻는 질문

### 문제 해결 가이드
- 일반적인 문제 해결 방법
- 고급 문제 해결 가이드
- 지원 요청 방법

## 🔧 확장성

### 새로운 다이얼로그 추가

```python
from app.help_system.ui.dialogs import BaseHelpDialog

class CustomDialog(BaseHelpDialog):
    def __init__(self, parent, custom_data):
        super().__init__(parent, "커스텀 다이얼로그", (600, 400))
        self.custom_data = custom_data
        self._create_ui()
    
    def _create_ui(self):
        # 커스텀 UI 구현
        pass
```

### 새로운 콘텐츠 타입 추가

```python
from app.help_system.core.help_service import HelpService

# HelpService 확장
class ExtendedHelpService(HelpService):
    def __init__(self, app_name):
        super().__init__(app_name)
        self.tutorials = []
    
    def add_tutorial(self, title, content):
        self.tutorials.append({"title": title, "content": content})
```

## 📝 마이그레이션 가이드

### 기존 프로젝트에서 사용하기

1. **help_system 패키지 복사**
2. **기존 도움말 함수 교체**:
   ```python
   # 이전
   def show_about():
       messagebox.showinfo("정보", "애플리케이션 정보")
   
   # 이후
   from app.help_system.utils.help_utils import quick_setup_help_system
   help_manager = quick_setup_help_system(...)
   help_manager.show_about_dialog()
   ```

3. **메뉴 시스템 업데이트**:
   ```python
   # 이전
   help_menu.add_command(label="정보", command=show_about)
   
   # 이후
   help_manager.setup_help_menu(menubar)
   ```

## 🧪 테스트

```bash
# 도움말 시스템 테스트 실행
python tools/test_help_system.py
```

테스트 포함 항목:
- 모듈 import
- 기본 기능
- DB Manager 통합
- ConfigManager 통합
- UI 컴포넌트
- 빠른 설정

## 📦 의존성

- **필수**: `tkinter` (Python 표준 라이브러리)
- **선택**: `logging` (로깅 기능)

## 🤝 기여

새로운 기능이나 개선사항을 추가할 때:

1. 기존 인터페이스 호환성 유지
2. 적절한 테스트 케이스 추가
3. 문서 업데이트
4. 예제 코드 제공

## 📄 라이선스

이 모듈화된 도움말 시스템은 DB Manager 프로젝트의 일부로 MIT 라이선스 하에 제공됩니다.