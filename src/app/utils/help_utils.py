#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
도움말 유틸리티 모듈
도움말 시스템에서 공통으로 사용되는 유틸리티 함수들을 제공합니다.
"""

import tkinter as tk
from typing import Dict, List, Optional
import logging
import os
import sys

from app.help_system.core.app_info import AppInfo, AppInfoManager
from app.help_system.core.help_service import HelpDataService
from app.help_system.ui.help_manager import HelpUIManager


def quick_setup_help_system(parent_window: tk.Tk, app_name: Optional[str] = None, 
                           version: Optional[str] = None, developer: Optional[str] = None,
                           shortcuts: Optional[Dict[str, str]] = None, 
                           features: Optional[List[str]] = None,
                           logger: Optional[logging.Logger] = None) -> HelpUIManager:
    """
    간단한 설정으로 도움말 시스템을 빠르게 설정합니다.
    
    Args:
        parent_window: 부모 윈도우
        app_name: 애플리케이션 이름
        version: 버전 정보
        developer: 개발자 정보
        shortcuts: 단축키 딕셔너리
        features: 주요 기능 목록
        logger: 로거 인스턴스
    
    Returns:
        HelpUIManager: 설정된 도움말 UI 관리자
    """
    # 기본값 설정
    if not app_name:
        app_name = "애플리케이션"
    if not version:
        version = "1.0.0"
    if not developer:
        developer = "개발팀"
    
    # 애플리케이션 정보 생성
    app_info = AppInfo(
        name=app_name,
        version=version,
        release_date="2025-01-01",
        developer=developer,
        organization="개발팀",
        contact="info@company.com",
        description=f"{app_name}의 주요 기능을 제공합니다.",
        icon_path=get_default_icon_path()
    )
    
    # 앱 정보 매니저 생성
    app_info_manager = AppInfoManager(app_info)
    
    # 도움말 데이터 서비스 생성 (커스터마이즈 기능 포함)
    help_service = create_customizable_help_service(app_name, shortcuts, features)
    
    # 도움말 UI 매니저 생성
    return HelpUIManager(parent_window, help_service, app_info_manager, logger)


def create_customizable_help_service(app_name: str, shortcuts: Optional[Dict[str, str]] = None, 
                                    features: Optional[List[str]] = None) -> HelpDataService:
    """
    커스터마이즈 가능한 도움말 서비스를 생성합니다.
    
    Args:
        app_name: 애플리케이션 이름
        shortcuts: 단축키 딕셔너리
        features: 주요 기능 목록
    
    Returns:
        HelpDataService: 커스터마이즈된 도움말 서비스
    """
    from app.help_system.core.help_service import HelpSection, UserGuideData
    
    # 기본 섹션들
    sections = [
        HelpSection(
            title="개요",
            content=f"{app_name}는 사용자를 위한 다양한 기능을 제공합니다.",
            order=1
        ),
        HelpSection(
            title="시작하기",
            content="애플리케이션을 시작하려면 메뉴에서 원하는 기능을 선택하세요.",
            order=2
        )
    ]
    
    # 기본 단축키
    default_shortcuts = {
        "F1": "도움말",
        "Ctrl+Q": "종료"
    }
    if shortcuts:
        default_shortcuts.update(shortcuts)
    
    # 기본 기능
    default_features = [
        "사용자 친화적 인터페이스",
        "도움말 시스템"
    ]
    if features:
        default_features.extend(features)
    
    # 기본 FAQ
    faqs = [
        {
            "Q": "이 프로그램은 어떻게 사용하나요?",
            "A": "메뉴에서 원하는 기능을 선택하여 사용할 수 있습니다."
        },
        {
            "Q": "도움말은 어떻게 보나요?",
            "A": "F1 키를 누르거나 도움말 메뉴를 클릭하세요."
        }
    ]
    
    # 커스텀 가이드 데이터 생성
    guide_data = UserGuideData(
        app_name=app_name,
        sections=sections,
        shortcuts=default_shortcuts,
        features=default_features,
        faqs=faqs
    )
    
    # 커스텀 도움말 서비스 생성
    class CustomizableHelpService(HelpDataService):
        def __init__(self, custom_guide_data: UserGuideData):
            super().__init__()
            self._user_guide_data = custom_guide_data
        
        def get_user_guide_data(self, app_name: str = None) -> UserGuideData:
            # app_name은 인터페이스 호환성을 위해 유지하지만 사용하지 않음
            _ = app_name  # 사용하지 않음을 명시
            return self._user_guide_data
    
    return CustomizableHelpService(guide_data)


def get_default_icon_path() -> str:
    """기본 아이콘 경로를 반환합니다."""
    try:
        if getattr(sys, 'frozen', False):
            application_path = getattr(sys, '_MEIPASS', '')
        else:
            # 현재 파일에서 프로젝트 루트까지 올라가기
            current_dir = os.path.dirname(os.path.abspath(__file__))
            application_path = os.path.dirname(os.path.dirname(current_dir))
        
        icon_path = os.path.join(application_path, "resources", "icons", "db_compare.ico")
        return icon_path if os.path.exists(icon_path) else ""
    except Exception:
        return ""


def setup_help_system_with_menu(parent_window: tk.Tk, menubar: tk.Menu,
                               help_manager: Optional[HelpUIManager] = None) -> HelpUIManager:
    """
    메뉴와 함께 도움말 시스템을 설정합니다.
    
    Args:
        parent_window: 부모 윈도우
        menubar: 메뉴바
        help_manager: 도움말 매니저 (없으면 기본 생성)
    
    Returns:
        HelpUIManager: 설정된 도움말 UI 관리자
    """
    if not help_manager:
        help_manager = quick_setup_help_system(parent_window)
    
    # 도움말 메뉴 설정
    help_manager.setup_help_menu(menubar)
    
    # 키 바인딩 설정
    help_manager.setup_help_bindings()
    
    return help_manager


def create_db_manager_help_system(parent_window: tk.Tk, logger: Optional[logging.Logger] = None) -> HelpUIManager:
    """
    DB Manager 전용 도움말 시스템을 생성합니다.
    
    Args:
        parent_window: 부모 윈도우
        logger: 로거
        
    Returns:
        HelpUIManager: DB Manager용 도움말 UI 관리자
    """
    from app.help_system.utils.help_utils import create_db_manager_help_system as create_help
    return create_help(parent_window, logger)