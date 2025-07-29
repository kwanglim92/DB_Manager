# -*- coding: utf-8 -*-
"""
도움말 데이터 서비스 클래스

사용자 제공 코드와 동일한 구조로 구현된 도움말 시스템
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

@dataclass
class HelpSection:
    """도움말 섹션 데이터 클래스"""
    title: str
    content: str
    order: int = 0

@dataclass
class UserGuideData:
    """사용자 가이드 데이터 클래스"""
    app_name: str
    sections: List[HelpSection]
    shortcuts: Dict[str, str]
    features: List[str]
    faqs: List[Dict[str, str]]

class HelpDataService:
    """도움말 데이터 서비스 - 제공된 코드와 동일한 구조"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._user_guide_data = None
    
    def get_user_guide_data(self, app_name: str = "DB Manager") -> UserGuideData:
        """사용자 가이드 데이터 반환"""
        if self._user_guide_data is None:
            self._user_guide_data = self._create_db_manager_guide_data(app_name)
        return self._user_guide_data
    
    def _create_db_manager_guide_data(self, app_name: str) -> UserGuideData:
        """DB Manager용 가이드 데이터 생성"""
        # 도움말 섹션들
        sections = [
            HelpSection(
                title="개요",
                content=f"{app_name}는 DB 파일 비교, 관리, 보고서 생성 등 다양한 기능을 제공하는 도구입니다.",
                order=1
            ),
            HelpSection(
                title="시작하기",
                content="1. 파일 > 폴더 열기를 통해 DB 파일들이 있는 폴더를 선택하세요.\n2. 자동으로 DB 파일들이 비교되어 결과가 표시됩니다.\n3. 각 탭에서 다양한 분석 결과를 확인할 수 있습니다.",
                order=2
            ),
            HelpSection(
                title="사용자 역할",
                content="• 장비 생산 엔지니어: DB 비교 기능 사용\n• QC 엔지니어: Maintenance Mode로 모든 기능 사용",
                order=3
            )
        ]
        
        # 키보드 단축키
        shortcuts = {
            "Ctrl+O": "폴더 열기",
            "F1": "사용자 가이드",
            "Ctrl+S": "현재 탭 내용 저장",
            "Ctrl+E": "Excel로 내보내기",
            "Ctrl+R": "새로고침",
            "Delete": "선택된 항목 삭제",
            "F5": "전체 새로고침"
        }
        
        # 주요 기능
        features = [
            "DB 파일 비교 및 차이점 분석",
            "격자 뷰를 통한 시각적 데이터 확인",
            "QC 검수 및 품질 관리",
            "다양한 형식으로 보고서 생성",
            "Excel/CSV 파일 내보내기",
            "유지보수 모드를 통한 고급 기능",
            "실시간 데이터 동기화"
        ]
        
        # FAQ
        faqs = [
            {
                "Q": "유지보수 모드는 어떻게 활성화하나요?",
                "A": "도구 메뉴에서 'Maintenance Mode'를 선택하고 비밀번호를 입력하세요."
            },
            {
                "Q": "DB 파일을 어떻게 비교하나요?",
                "A": "파일 > 폴더 열기로 DB 파일들이 있는 폴더를 선택하면 자동으로 비교됩니다."
            },
            {
                "Q": "보고서를 어떻게 생성하나요?",
                "A": "각 탭에서 '보고서 생성' 버튼을 클릭하거나 Ctrl+R을 누르세요."
            },
            {
                "Q": "데이터를 Excel로 내보내려면?",
                "A": "우클릭 메뉴에서 'Excel로 내보내기'를 선택하거나 Ctrl+E를 누르세요."
            },
            {
                "Q": "문제가 발생했을 때는 어떻게 하나요?",
                "A": "F5를 눌러 전체 새로고침을 시도하거나 프로그램을 재시작해보세요."
            }
        ]
        
        return UserGuideData(
            app_name=app_name,
            sections=sections,
            shortcuts=shortcuts,
            features=features,
            faqs=faqs
        )
    
    def generate_user_guide_text(self, app_name: str = "DB Manager") -> str:
        """사용자 가이드 텍스트 생성"""
        guide_data = self.get_user_guide_data(app_name)
        
        sections = []
        
        # 앱 제목
        sections.append(f"[{guide_data.app_name} 사용자 가이드]\n")
        
        # 도움말 섹션들
        for section in sorted(guide_data.sections, key=lambda x: x.order):
            sections.append(f"[{section.title}]")
            sections.append(section.content)
        
        # 키보드 단축키
        if guide_data.shortcuts:
            sections.append("[키보드 단축키]")
            for key, description in guide_data.shortcuts.items():
                sections.append(f"• {key}: {description}")
        
        # 주요 기능
        if guide_data.features:
            sections.append("[주요 기능]")
            for feature in guide_data.features:
                sections.append(f"• {feature}")
        
        # FAQ
        if guide_data.faqs:
            sections.append("[자주 묻는 질문]")
            for i, faq in enumerate(guide_data.faqs, 1):
                sections.append(f"\nQ{i}: {faq.get('Q', '질문 없음')}")
                sections.append(f"A{i}: {faq.get('A', '답변 없음')}")
        
        return "\n\n".join(sections)


# DB Manager 전용 도움말 데이터 서비스 생성 함수
def create_db_manager_help_service() -> HelpDataService:
    """DB Manager 전용 도움말 데이터 서비스 생성"""
    return HelpDataService()