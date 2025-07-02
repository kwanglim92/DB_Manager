# -*- coding: utf-8 -*-
"""
도움말 시스템 유틸리티 함수들 (새로운 HelpDataService 구조 호환)

간편한 도움말 시스템 설정을 위한 헬퍼 함수들을 제공합니다.
"""

import tkinter as tk
from typing import Optional
import logging

from ..core.app_info import AppInfo, RevisionInfo, AppInfoManager, create_db_manager_app_info
from ..core.help_service import HelpDataService, create_db_manager_help_service
from ..ui.help_manager import HelpUIManager


def create_db_manager_help_system(parent_window: tk.Tk, logger: Optional[logging.Logger] = None) -> HelpUIManager:
    """
    DB Manager 전용 도움말 시스템 생성
    
    Args:
        parent_window: 부모 윈도우
        logger: 로거
        
    Returns:
        HelpUIManager: DB Manager용 도움말 UI 관리자
    """
    logger = logger or logging.getLogger(__name__)
    
    try:
        # 애플리케이션 정보 관리자 생성
        app_info_manager = create_db_manager_app_info()
        
        # 도움말 데이터 서비스 생성
        help_data_service = create_db_manager_help_service()
        
        # 도움말 UI 관리자 생성
        help_ui_manager = HelpUIManager(
            parent_window,
            help_data_service,
            app_info_manager,
            logger
        )
        
        logger.info("DB Manager 도움말 시스템 생성 완료")
        return help_ui_manager
        
    except Exception as e:
        logger.error(f"DB Manager 도움말 시스템 생성 실패: {e}")
        raise


def setup_help_system_with_menu(
    parent_window: tk.Tk, 
    menubar: tk.Menu, 
    help_ui_manager: HelpUIManager,
    menu_name: str = "도움말"
):
    """
    도움말 시스템을 메뉴바에 통합
    
    Args:
        parent_window: 부모 윈도우
        menubar: 메뉴바
        help_ui_manager: 도움말 UI 관리자
        menu_name: 메뉴 이름
    """
    try:
        # 도움말 메뉴 추가
        help_ui_manager.setup_help_menu(menubar, menu_name)
        
        # 키보드 바인딩 설정
        help_ui_manager.setup_help_bindings()
        
        help_ui_manager.logger.info(f"도움말 시스템 메뉴 통합 완료: {menu_name}")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"도움말 시스템 메뉴 통합 실패: {e}")
        raise