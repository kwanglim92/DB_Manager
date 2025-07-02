# -*- coding: utf-8 -*-
"""
유틸리티 모듈
"""

import sys
import os

# 기존 utils.py에서 필요한 함수들을 직접 import하기 위한 해결책
def _import_from_utils_module():
    """utils.py 모듈에서 함수들을 직접 import"""
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    utils_path = os.path.join(parent_dir, 'utils.py')
    
    # utils.py 모듈을 직접 로드
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_utils", utils_path)
    app_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_utils)
    
    return app_utils

# utils.py에서 함수들 가져오기
try:
    _utils_module = _import_from_utils_module()
    create_treeview_with_scrollbar = _utils_module.create_treeview_with_scrollbar
    create_label_entry_pair = _utils_module.create_label_entry_pair
    format_num_value = _utils_module.format_num_value
    verify_password = _utils_module.verify_password
    change_maintenance_password = _utils_module.change_maintenance_password
except Exception as e:
    # 폴백: 기본 구현으로 대체
    def create_treeview_with_scrollbar(*args, **kwargs):
        raise ImportError(f"utils 함수를 로드할 수 없습니다: {e}")
    def create_label_entry_pair(*args, **kwargs):
        raise ImportError(f"utils 함수를 로드할 수 없습니다: {e}")
    def format_num_value(*args, **kwargs):
        raise ImportError(f"utils 함수를 로드할 수 없습니다: {e}")
    def verify_password(*args, **kwargs):
        raise ImportError(f"utils 함수를 로드할 수 없습니다: {e}")
    def change_maintenance_password(*args, **kwargs):
        raise ImportError(f"utils 함수를 로드할 수 없습니다: {e}")

# 새로운 help_utils에서 함수들 import  
from .help_utils import (
    quick_setup_help_system,
    setup_help_system_with_menu,
    create_db_manager_help_system,
    get_default_icon_path
)

__all__ = [
    # 기존 utils.py 함수들
    'create_treeview_with_scrollbar',
    'create_label_entry_pair', 
    'format_num_value',
    'verify_password',
    'change_maintenance_password',
    # 새로운 help_utils 함수들
    'quick_setup_help_system',
    'setup_help_system_with_menu', 
    'create_db_manager_help_system',
    'get_default_icon_path'
]