#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
모듈화된 도움말 시스템 사용 예제

이 예제는 새로운 모듈화된 도움말 시스템을 다른 프로젝트에서 
어떻게 사용할 수 있는지 보여줍니다.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import logging

# 프로젝트 루트를 sys.path에 추가 (예제 실행을 위해)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 모듈화된 도움말 시스템 임포트
from src.app.utils.help_utils import quick_setup_help_system, setup_help_system_with_menu
from src.app.core.app_info import AppInfo, RevisionInfo, create_custom_app_info_manager
from src.app.services.help_service import create_custom_help_service


class ExampleApp:
    """예제 애플리케이션"""
    
    def __init__(self):
        self.setup_logging()
        self.create_main_window()
        self.setup_help_system()
        self.create_ui()
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def create_main_window(self):
        """메인 윈도우 생성"""
        self.window = tk.Tk()
        self.window.title("도움말 시스템 예제")
        self.window.geometry("800x600")
    
    def setup_help_system(self):
        """도움말 시스템 설정"""
        # 방법 1: 간단한 설정으로 빠른 셋업
        self.help_manager = quick_setup_help_system(
            parent_window=self.window,
            app_name="예제 애플리케이션",
            version="1.0.0",
            developer="개발자",
            shortcuts={
                "Ctrl + N": "새 파일",
                "Ctrl + O": "파일 열기",
                "Ctrl + S": "파일 저장",
                "F1": "도움말"
            },
            features=[
                "파일 관리 기능",
                "텍스트 편집 기능",
                "검색 및 바꾸기",
                "플러그인 지원"
            ],
            logger=self.logger
        )
    
    def create_ui(self):
        """UI 생성"""
        # 메뉴바 생성
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="새 파일", command=self.new_file)
        file_menu.add_command(label="열기", command=self.open_file)
        file_menu.add_command(label="저장", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.window.quit)
        
        # 도움말 메뉴 설정 (모듈화된 시스템 사용)
        setup_help_system_with_menu(self.window, menubar, self.help_manager)
        
        # 메인 컨텐츠
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 제목
        title_label = ttk.Label(main_frame, text="모듈화된 도움말 시스템 예제", 
                               font=('Helvetica', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 설명
        desc_text = """
이 예제는 모듈화된 도움말 시스템의 사용법을 보여줍니다.

기능:
• F1 키를 눌러 사용 설명서 보기
• 도움말 > 프로그램 정보에서 버전 정보 확인
• 완전히 모듈화되어 다른 프로젝트에서 재사용 가능

아래 버튼들로 도움말 기능을 테스트해보세요.
        """
        
        desc_label = ttk.Label(main_frame, text=desc_text.strip(), justify=tk.LEFT)
        desc_label.pack(pady=(0, 20))
        
        # 버튼들
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="사용 설명서 보기 (F1)", 
                  command=self.show_user_guide).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="프로그램 정보 보기", 
                  command=self.show_about).pack(side=tk.LEFT, padx=5)
        
        # 상태바
        self.status_var = tk.StringVar()
        self.status_var.set("준비됨")
        status_bar = ttk.Label(self.window, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def new_file(self):
        """새 파일"""
        self.status_var.set("새 파일 생성됨")
        self.logger.info("새 파일 생성")
    
    def open_file(self):
        """파일 열기"""
        self.status_var.set("파일 열기 기능")
        self.logger.info("파일 열기")
    
    def save_file(self):
        """파일 저장"""
        self.status_var.set("파일 저장 기능")
        self.logger.info("파일 저장")
    
    def show_user_guide(self):
        """사용 설명서 표시"""
        self.help_manager.show_user_guide()
    
    def show_about(self):
        """프로그램 정보 표시"""
        self.help_manager.show_about_dialog()
    
    def run(self):
        """애플리케이션 실행"""
        self.logger.info("예제 애플리케이션 시작")
        self.window.mainloop()


class AdvancedExampleApp:
    """고급 사용법을 보여주는 예제 애플리케이션"""
    
    def __init__(self):
        self.setup_logging()
        self.create_main_window()
        self.setup_custom_help_system()
        self.create_ui()
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def create_main_window(self):
        """메인 윈도우 생성"""
        self.window = tk.Tk()
        self.window.title("고급 도움말 시스템 예제")
        self.window.geometry("900x700")
    
    def setup_custom_help_system(self):
        """커스텀 도움말 시스템 설정"""
        # 방법 2: 완전 커스텀 설정
        
        # 1. 커스텀 애플리케이션 정보 생성
        app_info = AppInfo(
            name="고급 예제 애플리케이션",
            version="2.0.1",
            release_date="2025-07-02",
            developer="고급 개발팀",
            organization="소프트웨어 회사",
            contact="support@company.com",
            description="""고급 기능을 제공하는 예제 애플리케이션입니다.
            
주요 특징:
• 완전 커스터마이징된 도움말 시스템
• 상세한 리비전 히스토리
• 전문적인 사용자 가이드
• 확장 가능한 아키텍처"""
        )
        
        # 2. 커스텀 리비전 히스토리 생성
        revisions = [
            RevisionInfo(
                version="2.0.1",
                date="2025-07-02",
                summary="모듈화된 도움말 시스템 적용",
                details={
                    "New Features": [
                        "완전 모듈화된 도움말 시스템",
                        "재사용 가능한 컴포넌트 구조",
                        "커스터마이징 가능한 UI"
                    ],
                    "Improvements": [
                        "성능 최적화",
                        "메모리 사용량 개선",
                        "사용자 경험 향상"
                    ],
                    "Bug Fixes": [
                        "창 크기 조정 문제 해결",
                        "메뉴 접근성 개선"
                    ]
                }
            ),
            RevisionInfo(
                version="2.0.0",
                date="2025-06-01",
                summary="메이저 업데이트",
                details={
                    "New Features": [
                        "새로운 UI 디자인",
                        "플러그인 시스템 도입"
                    ],
                    "Breaking Changes": [
                        "API 변경",
                        "설정 파일 형식 변경"
                    ]
                }
            ),
            RevisionInfo(
                version="1.5.0",
                date="2025-05-01",
                summary="안정성 개선",
                details={
                    "Improvements": [
                        "안정성 향상",
                        "버그 수정"
                    ]
                }
            )
        ]
        
        # 3. 앱 정보 매니저 생성
        app_info_manager = create_custom_app_info_manager(app_info, revisions)
        
        # 4. 커스텀 도움말 서비스 생성
        help_service = create_custom_help_service(
            app_name="고급 예제 애플리케이션",
            shortcuts={
                "Ctrl + N": "새 프로젝트",
                "Ctrl + O": "프로젝트 열기",
                "Ctrl + S": "프로젝트 저장",
                "Ctrl + Shift + S": "다른 이름으로 저장",
                "Ctrl + Z": "실행 취소",
                "Ctrl + Y": "다시 실행",
                "Ctrl + F": "찾기",
                "Ctrl + H": "바꾸기",
                "F5": "실행",
                "F9": "중단점 토글",
                "F10": "한 줄씩 실행",
                "F11": "한 단계씩 실행",
                "F1": "도움말"
            },
            features=[
                "프로젝트 관리",
                "코드 편집기",
                "디버깅 도구",
                "플러그인 시스템",
                "테마 지원",
                "다국어 지원",
                "클라우드 동기화",
                "실시간 협업"
            ],
            faqs=[
                {"Q": "프로젝트를 어떻게 생성하나요?", "A": "Ctrl+N을 누르거나 파일 > 새 프로젝트를 선택하세요."},
                {"Q": "플러그인은 어떻게 설치하나요?", "A": "도구 > 플러그인 관리자에서 원하는 플러그인을 검색하고 설치할 수 있습니다."},
                {"Q": "테마를 변경할 수 있나요?", "A": "설정 > 외관에서 다양한 테마 중 선택할 수 있습니다."},
                {"Q": "클라우드 동기화는 어떻게 사용하나요?", "A": "계정 > 클라우드 설정에서 계정을 연결하고 동기화를 활성화하세요."}
            ]
        )
        
        # 5. 도움말 UI 매니저 생성
        from src.app.ui.help_manager import HelpUIManager
        self.help_manager = HelpUIManager(
            parent_window=self.window,
            help_service=help_service,
            app_info_manager=app_info_manager,
            logger=self.logger
        )
    
    def create_ui(self):
        """UI 생성"""
        # 메뉴바 생성
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="새 프로젝트 (Ctrl+N)", command=self.new_project)
        file_menu.add_command(label="프로젝트 열기 (Ctrl+O)", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="저장 (Ctrl+S)", command=self.save_project)
        file_menu.add_command(label="다른 이름으로 저장", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.window.quit)
        
        # 편집 메뉴
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="편집", menu=edit_menu)
        edit_menu.add_command(label="실행 취소 (Ctrl+Z)", command=self.undo)
        edit_menu.add_command(label="다시 실행 (Ctrl+Y)", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="찾기 (Ctrl+F)", command=self.find)
        edit_menu.add_command(label="바꾸기 (Ctrl+H)", command=self.replace)
        
        # 도구 메뉴
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도구", menu=tools_menu)
        tools_menu.add_command(label="플러그인 관리자", command=self.plugin_manager)
        tools_menu.add_command(label="설정", command=self.settings)
        
        # 도움말 메뉴 설정 (모듈화된 시스템 사용)
        self.help_manager.setup_help_menu(menubar)
        
        # 키 바인딩 설정
        self.help_manager.setup_help_bindings()
        
        # 메인 컨텐츠
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 제목
        title_label = ttk.Label(main_frame, text="고급 도움말 시스템 예제", 
                               font=('Helvetica', 18, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 노트북 위젯
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 개요 탭
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="개요")
        
        overview_text = """
고급 도움말 시스템 예제

이 예제는 완전히 커스터마이징된 도움말 시스템을 보여줍니다.

특징:
• 완전한 커스터마이징
• 상세한 리비전 히스토리
• 풍부한 FAQ 섹션
• 전문적인 외관

테스트:
• F1 키로 사용 설명서 열기
• 도움말 > 프로그램 정보에서 상세 정보 확인
• 리비전 히스토리 더블클릭으로 상세 내용 보기
        """
        
        ttk.Label(overview_frame, text=overview_text.strip(), justify=tk.LEFT).pack(
            pady=20, padx=20, anchor=tk.NW)
        
        # 기능 탭
        features_frame = ttk.Frame(notebook)
        notebook.add(features_frame, text="기능")
        
        # 기능 리스트
        features_list = tk.Listbox(features_frame)
        features_list.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        features = [
            "프로젝트 관리",
            "코드 편집기",
            "디버깅 도구",
            "플러그인 시스템",
            "테마 지원",
            "다국어 지원",
            "클라우드 동기화",
            "실시간 협업"
        ]
        
        for feature in features:
            features_list.insert(tk.END, feature)
        
        # 상태바
        self.status_var = tk.StringVar()
        self.status_var.set("고급 예제 애플리케이션 준비됨")
        status_bar = ttk.Label(self.window, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # 메뉴 핸들러들
    def new_project(self):
        self.status_var.set("새 프로젝트 생성")
        self.logger.info("새 프로젝트 생성")
    
    def open_project(self):
        self.status_var.set("프로젝트 열기")
        self.logger.info("프로젝트 열기")
    
    def save_project(self):
        self.status_var.set("프로젝트 저장")
        self.logger.info("프로젝트 저장")
    
    def save_as(self):
        self.status_var.set("다른 이름으로 저장")
        self.logger.info("다른 이름으로 저장")
    
    def undo(self):
        self.status_var.set("실행 취소")
        self.logger.info("실행 취소")
    
    def redo(self):
        self.status_var.set("다시 실행")
        self.logger.info("다시 실행")
    
    def find(self):
        self.status_var.set("찾기")
        self.logger.info("찾기")
    
    def replace(self):
        self.status_var.set("바꾸기")
        self.logger.info("바꾸기")
    
    def plugin_manager(self):
        self.status_var.set("플러그인 관리자")
        self.logger.info("플러그인 관리자")
    
    def settings(self):
        self.status_var.set("설정")
        self.logger.info("설정")
    
    def run(self):
        """애플리케이션 실행"""
        self.logger.info("고급 예제 애플리케이션 시작")
        self.window.mainloop()


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="모듈화된 도움말 시스템 예제")
    parser.add_argument("--advanced", action="store_true", help="고급 예제 실행")
    args = parser.parse_args()
    
    if args.advanced:
        print("고급 예제 애플리케이션을 시작합니다...")
        app = AdvancedExampleApp()
    else:
        print("기본 예제 애플리케이션을 시작합니다...")
        app = ExampleApp()
    
    app.run()


if __name__ == "__main__":
    main() 