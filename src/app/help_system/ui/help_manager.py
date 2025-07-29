# -*- coding: utf-8 -*-
"""
도움말 UI 관리자

사용자 제공 코드와 동일한 구조로 구현된 도움말 UI 시스템
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import logging

from .dialogs import AboutDialog, UserGuideDialog  
from ..core.help_service import HelpDataService
from ..core.app_info import AppInfoManager


class HelpUIManager:
    """도움말 UI 관리자 - 제공된 코드와 동일한 구조"""
    
    def __init__(self, parent_window: tk.Tk, help_data_service: HelpDataService, 
                 app_info_manager: AppInfoManager, logger: Optional[logging.Logger] = None):
        """
        Args:
            parent_window: 부모 윈도우
            help_data_service: 도움말 데이터 서비스
            app_info_manager: 애플리케이션 정보 관리자
            logger: 로거
        """
        self.parent_window = parent_window
        self.help_data_service = help_data_service
        self.app_info_manager = app_info_manager
        self.logger = logger or logging.getLogger(__name__)
        
        # 다이얼로그 인스턴스 캐시
        self._about_dialog = None
        self._user_guide_dialog = None
        
    def setup_help_menu(self, menubar: tk.Menu, menu_name: str = "도움말"):
        """
        도움말 메뉴를 메뉴바에 추가
        
        Args:
            menubar: 메뉴바
            menu_name: 메뉴 이름 (기본: "도움말")
        """
        help_menu = tk.Menu(menubar, tearoff=0)
        
        # 사용 설명서
        help_menu.add_command(
            label="사용 설명서 (F1)", 
            command=self.show_user_guide,
            accelerator="F1"
        )
        
        help_menu.add_separator()
        
        # 프로그램 정보
        help_menu.add_command(
            label="프로그램 정보", 
            command=self.show_about_dialog
        )
        
        menubar.add_cascade(label=menu_name, menu=help_menu)
        
        self.logger.info(f"도움말 메뉴 '{menu_name}' 생성 완료")
        
    def setup_help_bindings(self):
        """키보드 바인딩 설정"""
        # F1 키로 사용자 가이드 열기
        self.parent_window.bind('<F1>', lambda e: self.show_user_guide())
        self.parent_window.bind('<Key-F1>', lambda e: self.show_user_guide())
        
        self.logger.info("도움말 키보드 바인딩 설정 완료")
        
    def show_about_dialog(self):
        """프로그램 정보 다이얼로그 표시"""
        try:
            if self._about_dialog is None or not self._about_dialog.dialog.winfo_exists():
                self._about_dialog = AboutDialog(
                    self.parent_window, 
                    self.app_info_manager, 
                    self.logger
                )
            
            self._about_dialog.show()
            self.logger.info("프로그램 정보 다이얼로그 표시")
            
        except Exception as e:
            self.logger.error(f"프로그램 정보 다이얼로그 표시 실패: {e}")
            # 폴백으로 기본 메시지박스 사용
            messagebox.showinfo(
                "프로그램 정보",
                "DB Manager\n버전: 1.2.0\n제작자: kwanglim92\n\n이 프로그램은 DB 파일 비교, 관리, 보고서 생성 등 다양한 기능을 제공합니다."
            )
            
    def show_user_guide(self, event=None):
        """사용자 가이드 다이얼로그 표시"""
        try:
            # HelpDataService를 사용하여 가이드 텍스트 생성
            guide_text = self.help_data_service.generate_user_guide_text()
            
            if self._user_guide_dialog is None or not self._user_guide_dialog.dialog.winfo_exists():
                # UserGuideDialog 생성시 guide_text 직접 전달
                self._user_guide_dialog = UserGuideDialog(
                    self.parent_window, 
                    guide_text,
                    self.logger
                )
            
            self._user_guide_dialog.show()
            self.logger.info("사용자 가이드 다이얼로그 표시")
            
        except Exception as e:
            self.logger.error(f"사용자 가이드 다이얼로그 표시 실패: {e}")
            # 폴백으로 기본 메시지박스 사용
            fallback_guide = (
                "[DB Manager 사용자 가이드]\n\n"
                "• 폴더 열기: 파일 > 폴더 열기 (Ctrl+O)\n"
                "• DB 비교: 여러 DB 파일을 불러와 값 차이, 격자 뷰, 보고서 등 다양한 탭에서 확인\n"
                "• 유지보수 모드: 도구 > Maintenance Mode (비밀번호 필요)\n"
                "• Default DB 관리, QC 검수 등은 유지보수 모드에서만 사용 가능\n"
                "• 각 탭에서 우클릭 및 버튼으로 항목 추가/삭제/내보내기 등 다양한 작업 지원\n"
                "• 문의: github.com/kwanglim92/DB_Manager\n\n"
                "= 사용자 역할 =\n"
                "• 장비 생산 엔지니어: DB 비교 기능 사용\n"
                "• QC 엔지니어: Maintenance Mode로 모든 기능 사용"
            )
            messagebox.showinfo("사용 설명서", fallback_guide)
            
    def get_help_data_service(self) -> HelpDataService:
        """도움말 데이터 서비스 반환"""
        return self.help_data_service
        
    def get_app_info_manager(self) -> AppInfoManager:
        """애플리케이션 정보 관리자 반환"""
        return self.app_info_manager
        
    def update_help_content(self, help_data_service: HelpDataService = None, 
                          app_info_manager: AppInfoManager = None):
        """도움말 콘텐츠 업데이트"""
        if help_data_service:
            self.help_data_service = help_data_service
            # 기존 다이얼로그 캐시 무효화
            self._user_guide_dialog = None
            
        if app_info_manager:
            self.app_info_manager = app_info_manager
            # 기존 다이얼로그 캐시 무효화
            self._about_dialog = None
            
        self.logger.info("도움말 콘텐츠 업데이트 완료")
        
    def cleanup(self):
        """리소스 정리"""
        try:
            if self._about_dialog and self._about_dialog.dialog.winfo_exists():
                self._about_dialog.close()
            if self._user_guide_dialog and self._user_guide_dialog.dialog.winfo_exists():
                self._user_guide_dialog.close()
                
            self.logger.info("도움말 UI 리소스 정리 완료")
            
        except Exception as e:
            self.logger.error(f"도움말 UI 리소스 정리 실패: {e}")


class LegacyHelpAdapter:
    """기존 도움말 시스템과의 호환성을 위한 어댑터"""
    
    def __init__(self, help_ui_manager: HelpUIManager):
        """
        Args:
            help_ui_manager: 도움말 UI 관리자
        """
        self.help_ui_manager = help_ui_manager
        
    def show_about(self):
        """기존 show_about 함수 호환성"""
        return self.help_ui_manager.show_about_dialog()
        
    def show_user_guide(self, event=None):
        """기존 show_user_guide 함수 호환성"""
        return self.help_ui_manager.show_user_guide(event)