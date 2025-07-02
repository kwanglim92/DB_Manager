#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
도움말 서비스 모듈
사용 설명서 및 가이드 데이터를 관리하는 서비스 레이어입니다.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from ..core.app_info import AppInfoManager, get_app_info_manager


@dataclass
class HelpSection:
    """도움말 섹션 클래스"""
    title: str
    content: List[str]


@dataclass
class UserGuideData:
    """사용자 가이드 데이터 클래스"""
    title: str
    sections: List[HelpSection]


class HelpDataService:
    """도움말 데이터 서비스 클래스"""
    
    def __init__(self, app_info_manager: Optional[AppInfoManager] = None):
        """
        Args:
            app_info_manager: 애플리케이션 정보 관리자
        """
        self._app_info_manager = app_info_manager or get_app_info_manager()
        self._user_guide_data = self._get_default_user_guide_data()
    
    @property
    def app_info_manager(self) -> AppInfoManager:
        """애플리케이션 정보 관리자 반환"""
        return self._app_info_manager
    
    @property
    def user_guide_data(self) -> UserGuideData:
        """사용자 가이드 데이터 반환"""
        return self._user_guide_data
    
    def get_user_guide_sections(self) -> List[HelpSection]:
        """사용자 가이드 섹션 목록 반환"""
        return self._user_guide_data.sections
    
    def get_section_by_title(self, title: str) -> Optional[HelpSection]:
        """제목으로 섹션 찾기"""
        for section in self._user_guide_data.sections:
            if section.title == title:
                return section
        return None
    
    def update_user_guide_data(self, guide_data: UserGuideData):
        """사용자 가이드 데이터 업데이트"""
        self._user_guide_data = guide_data
    
    def add_section(self, section: HelpSection):
        """새 섹션 추가"""
        self._user_guide_data.sections.append(section)
    
    def remove_section(self, title: str) -> bool:
        """섹션 제거"""
        for i, section in enumerate(self._user_guide_data.sections):
            if section.title == title:
                del self._user_guide_data.sections[i]
                return True
        return False
    
    def _get_default_user_guide_data(self) -> UserGuideData:
        """기본 사용자 가이드 데이터 반환"""
        sections = [
            HelpSection(
                title="시작하기",
                content=[
                    "1. 프로그램 실행 후 '파일' 메뉴에서 '폴더 열기' 선택",
                    "2. DB Editor에서 Export한 .txt 파일이 있는 폴더 선택",
                    "3. 최대 6개의 DB 파일들을 선택하여 비교 분석 실행"
                ]
            ),
            HelpSection(
                title="주요 기능",
                content=[
                    "• DB 파일 비교 분석",
                    "  - 여러 DB 파일의 내용을 자동으로 비교",
                    "  - 차이점 자동 감지 및 하이라이트",
                    "  - 상세 비교 결과 제공",
                    "",
                    "• Default DB 관리 (유지보수 모드)",
                    "  - 장비 유형별 Default 파라미터 및 값 (기본, 최소, 최대) 관리",
                    "  - QC 필수 항목 지정",
                    "  - 파일로 가져오기/내보내기",
                    "",
                    "• QC 검수 기능 (유지보수 모드, Default DB 기반)",
                    "  - Default DB의 값 및 QC 필수 항목을 기준으로 로드된 파일 검증",
                    "  - Pass/Fail 자동 판정 및 상세 결과 표시",
                    "  - QC 검증 보고서 생성 (Excel)",
                    "",
                    "• 보고서 생성",
                    "  - DB 비교 결과 및 통계 요약 보고서 생성 (Excel)"
                ]
            ),
            HelpSection(
                title="단축키",
                content=[
                    "• Ctrl + O : 폴더 열기",
                    "• F1 : 사용 설명서 열기"
                ]
            ),
            HelpSection(
                title="자주 묻는 질문",
                content=[
                    "Q: 지원하는 파일 형식은 무엇인가요?",
                    "A: 주로 DB Editor에서 Export한 탭으로 구분된 .txt 파일을 지원하며, 일반 .csv 파일도 로드 가능합니다.",
                    "",
                    "Q: 한 번에 몇 개의 파일을 비교할 수 있나요?",
                    "A: 현재 UI상으로는 여러 파일 로드가 가능하지만, 비교 탭의 표시는 내부적으로 제한될 수 있습니다 (구현에 따라 다름).",
                    "",
                    "Q: 유지보수 모드는 어떻게 사용하나요?",
                    "A: 메뉴 > 도구 > Maintenance Mode 선택 후 비밀번호(기본값: 1234)를 입력하면 활성화됩니다."
                ]
            )
        ]
        
        return UserGuideData(
            title="DB 관리 프로그램 사용 설명서",
            sections=sections
        )


class CustomizableHelpService(HelpDataService):
    """커스터마이징 가능한 도움말 서비스 클래스"""
    
    def __init__(self, app_name: Optional[str] = None, shortcuts: Optional[Dict[str, str]] = None, 
                 features: Optional[List[str]] = None, faqs: Optional[List[Dict[str, str]]] = None):
        """
        Args:
            app_name: 애플리케이션 이름
            shortcuts: 단축키 딕셔너리 {'키': '설명'}
            features: 주요 기능 목록
            faqs: FAQ 목록 [{'Q': '질문', 'A': '답변'}]
        """
        super().__init__()
        if app_name or shortcuts or features or faqs:
            self._customize_guide(app_name, shortcuts, features, faqs)
    
    def _customize_guide(self, app_name: Optional[str] = None, shortcuts: Optional[Dict[str, str]] = None, 
                        features: Optional[List[str]] = None, faqs: Optional[List[Dict[str, str]]] = None):
        """가이드 커스터마이징"""
        if app_name:
            self._user_guide_data.title = f"{app_name} 사용 설명서"
        
        # 단축키 섹션 업데이트
        if shortcuts:
            shortcut_section = self.get_section_by_title("단축키")
            if shortcut_section:
                shortcut_section.content = [f"• {key} : {desc}" for key, desc in shortcuts.items()]
        
        # 주요 기능 섹션 업데이트
        if features:
            feature_section = self.get_section_by_title("주요 기능")
            if feature_section:
                feature_section.content = [f"• {feature}" for feature in features]
        
        # FAQ 섹션 업데이트
        if faqs:
            faq_section = self.get_section_by_title("자주 묻는 질문")
            if faq_section:
                faq_content = []
                for faq in faqs:
                    faq_content.extend([f"Q: {faq['Q']}", f"A: {faq['A']}", ""])
                faq_section.content = faq_content[:-1]  # 마지막 빈 줄 제거


# 기본 서비스 인스턴스
_default_help_service = HelpDataService()

def get_help_service() -> HelpDataService:
    """기본 도움말 서비스 인스턴스 반환"""
    return _default_help_service

def create_custom_help_service(app_name: Optional[str] = None, shortcuts: Optional[Dict[str, str]] = None, 
                              features: Optional[List[str]] = None, faqs: Optional[List[Dict[str, str]]] = None) -> CustomizableHelpService:
    """커스터마이징된 도움말 서비스 인스턴스 생성"""
    return CustomizableHelpService(app_name, shortcuts, features, faqs) 