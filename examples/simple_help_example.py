#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
간단한 도움말 시스템 사용 예제

새로운 프로젝트에서 모듈화된 도움말 시스템을 사용하는 간단한 예제입니다.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import logging

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 모듈화된 도움말 시스템 임포트
from src.app.utils.help_utils import quick_setup_help_system, setup_help_system_with_menu


class SimpleApp:
    """간단한 예제 애플리케이션"""
    
    def __init__(self):
        self.setup_logging()
        self.create_window()
        self.setup_help()
        self.create_ui()
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def create_window(self):
        """윈도우 생성"""
        self.window = tk.Tk()
        self.window.title("간단한 도움말 예제")
        self.window.geometry("600x400")
    
    def setup_help(self):
        """도움말 시스템 설정"""
        self.help_manager = quick_setup_help_system(
            parent_window=self.window,
            app_name="간단한 예제",
            version="1.0.0",
            developer="개발자",
            shortcuts={"F1": "도움말", "Ctrl+O": "열기"},
            features=["파일 관리", "텍스트 편집"],
            logger=self.logger
        )
    
    def create_ui(self):
        """UI 생성"""
        # 메뉴바
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="열기", command=self.open_file)
        file_menu.add_command(label="종료", command=self.window.quit)
        
        # 도움말 메뉴 자동 설정
        setup_help_system_with_menu(self.window, menubar, self.help_manager)
        
        # 메인 컨텐츠
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="간단한 도움말 시스템 예제", 
                 font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        ttk.Label(main_frame, text="F1 키를 눌러 도움말을 확인하세요!").pack(pady=10)
        
        # 테스트 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="사용 설명서", 
                  command=self.help_manager.show_user_guide).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="프로그램 정보", 
                  command=self.help_manager.show_about_dialog).pack(side=tk.LEFT, padx=5)
    
    def open_file(self):
        """파일 열기"""
        self.logger.info("파일 열기 기능")
    
    def run(self):
        """앱 실행"""
        self.window.mainloop()


if __name__ == "__main__":
    app = SimpleApp()
    app.run() 