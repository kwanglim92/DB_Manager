#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
애플리케이션 정보 관리 모듈
프로그램 버전, 개발자 정보, 리비전 히스토리 등을 중앙 관리합니다.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import os


@dataclass
class AppInfo:
    """애플리케이션 기본 정보 클래스"""
    name: str
    version: str
    release_date: str
    developer: str
    organization: str
    contact: str
    description: str
    icon_path: str = ""


@dataclass
class RevisionInfo:
    """리비전 정보 클래스"""
    version: str
    date: str
    summary: str
    details: Dict[str, List[str]]


class AppInfoManager:
    """애플리케이션 정보 관리자 클래스"""
    
    def __init__(self, app_info: Optional[AppInfo] = None, revisions: Optional[List[RevisionInfo]] = None):
        """
        Args:
            app_info: 애플리케이션 기본 정보
            revisions: 리비전 히스토리 목록
        """
        self._app_info = app_info or self._get_default_app_info()
        self._revisions = revisions or self._get_default_revisions()
    
    @property
    def app_info(self) -> AppInfo:
        """애플리케이션 기본 정보 반환"""
        return self._app_info
    
    @property
    def revisions(self) -> List[RevisionInfo]:
        """리비전 히스토리 목록 반환"""
        return self._revisions
    
    def get_current_version(self) -> str:
        """현재 버전 반환"""
        return self._app_info.version
    
    def get_latest_revision(self) -> Optional[RevisionInfo]:
        """최신 리비전 정보 반환"""
        return self._revisions[0] if self._revisions else None
    
    def update_app_info(self, **kwargs):
        """애플리케이션 정보 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self._app_info, key):
                setattr(self._app_info, key, value)
    
    def add_revision(self, revision: RevisionInfo):
        """새 리비전 추가 (최신순으로 정렬)"""
        self._revisions.insert(0, revision)
    
    def get_formatted_app_info(self) -> str:
        """포맷된 애플리케이션 정보 문자열 반환"""
        lines = [
            f"애플리케이션: {self.app_info.name}",
            f"버전: {self.app_info.version}",
            f"릴리스 날짜: {self.app_info.release_date}",
            f"개발자: {self.app_info.developer}",
            f"조직: {self.app_info.organization}",
            f"연락처: {self.app_info.contact}",
            "",
            "설명:",
            self.app_info.description
        ]
        return "\n".join(lines)
    
    def _get_default_app_info(self) -> AppInfo:
        """기본 애플리케이션 정보 반환"""
        try:
            # 아이콘 경로 설정
            icon_path = ""
            if hasattr(__import__('sys'), 'frozen') and getattr(__import__('sys'), 'frozen', False):
                application_path = getattr(__import__('sys'), '_MEIPASS')
            else:
                application_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(application_path, "resources", "icons", "db_compare.ico")
        except Exception:
            icon_path = ""
        
        return AppInfo(
            name="DB Manager",
            version="1.1.0",
            release_date="2025-05-01",
            developer="Levi Beak / 백광림",
            organization="Quality Assurance Team",
            contact="levi.beak@parksystems.com",
            description="""이 프로그램은 XES 데이터베이스 비교 및 관리를 위한 프로그램입니다.
            주요 기능:
            • 다중 DB 파일 비교 분석
            • 차이점 자동 감지 및 하이라이트
            • 상세 비교 보고서 생성 (Excel)
            • 데이터 시각화 및 통계 분석
            • Default DB 관리 (유지보수 모드)
            • QC 검수 기능 (유지보수 모드, Default DB 기반)""",
            icon_path=icon_path
        )
    
    def _get_default_revisions(self) -> List[RevisionInfo]:
        """기본 리비전 히스토리 반환"""
        return [
            RevisionInfo(
                version="1.1.0",
                date="2025-05-01",
                summary="모듈화 리팩토링 및 기능 안정화",
                details={
                    "Features": [
                        "로깅 시스템 개선 (Python logging 모듈 도입)",
                        "Default DB 관리 기능 UI 개선 및 버그 수정",
                        "QC 검수 탭 기능 추가 (Default DB 연동)",
                        "보고서 생성 기능 강화 (차이점 상세 시트 추가)",
                        "도움말 시스템 모듈화 (재사용 가능한 컴포넌트)"
                    ],
                    "Improvements": [
                        "코드 모듈화 (Comparison, DefaultDB, QC, Report, UI utils)",
                        "오류 처리 및 유효성 검사 강화 (try-except 블록 추가)",
                        "불필요한 코드 및 파일 정리",
                        "도움말 기능 서비스 레이어 분리"
                    ],
                    "Bug Fixes": [
                        "Default DB 다중 항목 추가 시 1개만 저장되는 버그 수정",
                        "min_spec/max_spec 미정의 에러 수정 (min_val/max_val 통일)",
                        "DB_Manager.py 내 여러 UI 이벤트 핸들러 오류 수정"
                    ]
                }
            ),
            RevisionInfo(
                version="1.0.0",
                date="2025-02-04",
                summary="초기 버전 출시",
                details={
                    "Features": [
                        "다중 XES DB 파일 비교 분석 기능",
                        "자동 차이점 감지 및 하이라이트",
                        "상세 비교 보고서 생성"
                    ],
                    "Improvements": [
                        "데이터 시각화 도구 추가"
                    ],
                    "Bug Fixes": [
                        "파일 로드 시 인코딩 문제 수정",
                        "메모리 사용량 최적화"
                    ]
                }
            )
        ]


# 싱글톤 인스턴스 (전역 사용을 위한 기본 인스턴스)
_default_app_info_manager = AppInfoManager()

def get_app_info_manager() -> AppInfoManager:
    """기본 AppInfoManager 인스턴스 반환"""
    return _default_app_info_manager

def create_custom_app_info_manager(app_info: AppInfo, revisions: Optional[List[RevisionInfo]] = None) -> AppInfoManager:
    """커스텀 AppInfoManager 인스턴스 생성"""
    return AppInfoManager(app_info, revisions)

def create_db_manager_app_info() -> AppInfoManager:
    """DB Manager 전용 AppInfoManager 생성"""
    return _default_app_info_manager 