# -*- coding: utf-8 -*-
"""
모듈화된 도움말 시스템 패키지

이 패키지는 완전히 모듈화된 도움말 시스템을 제공합니다.
다른 프로젝트에서 쉽게 재사용할 수 있도록 설계되었습니다.
"""

from .core.app_info import AppInfo, RevisionInfo
from .core.help_service import HelpDataService, HelpSection, UserGuideData
from .ui.help_manager import HelpUIManager

__all__ = [
    'AppInfo', 
    'RevisionInfo',
    'HelpDataService',
    'HelpSection',
    'UserGuideData',
    'HelpUIManager'
]