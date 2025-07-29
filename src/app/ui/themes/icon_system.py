"""
Professional Engineering Workbench 아이콘 시스템
일관된 시각적 표현을 위한 이모지 기반 아이콘 체계
"""

from typing import Dict, List
from enum import Enum


class IconCategory(Enum):
    """아이콘 카테고리"""
    GENERAL = "general"
    STATUS = "status"
    ACTION = "action"
    DATA = "data"
    QC = "qc"
    SYSTEM = "system"
    EQUIPMENT = "equipment"


class EngineeringIcons:
    """Professional Engineering Workbench 아이콘 시스템"""
    
    # === 일반 아이콘 ===
    GENERAL = {
        'app': '🔧',           # 애플리케이션 대표 아이콘
        'database': '🗄️',      # 데이터베이스
        'folder': '📁',        # 폴더
        'file': '📄',          # 파일
        'settings': '⚙️',      # 설정
        'help': '❓',          # 도움말
        'info': 'ℹ️',          # 정보
        'search': '🔍',        # 검색
        'filter': '🔽',        # 필터
        'refresh': '🔄',       # 새로고침
        'export': '📤',        # 내보내기
        'import': '📥',        # 가져오기
        'download': '⬇️',      # 다운로드
        'upload': '⬆️',        # 업로드
        'copy': '📋',          # 복사
        'edit': '✏️',          # 편집
        'delete': '🗑️',        # 삭제
        'add': '➕',           # 추가
        'remove': '➖',        # 제거
        'save': '💾',          # 저장
    }
    
    # === 상태 아이콘 ===
    STATUS = {
        'success': '✅',       # 성공
        'error': '❌',         # 오류
        'warning': '⚠️',       # 경고
        'pending': '⏳',       # 대기중
        'running': '🔄',       # 실행중
        'stopped': '⏹️',       # 정지
        'paused': '⏸️',        # 일시정지
        'completed': '🎉',     # 완료
        'failed': '💥',        # 실패
        'unknown': '❓',       # 알 수 없음
        'disabled': '🚫',      # 비활성화
        'enabled': '✓',        # 활성화
        'connected': '🔗',     # 연결됨
        'disconnected': '🔌',  # 연결 해제
        'loading': '⏳',       # 로딩
        'ready': '📋',         # 준비됨
    }
    
    # === 액션 아이콘 ===
    ACTION = {
        'execute': '🚀',       # 실행
        'start': '▶️',         # 시작
        'stop': '⏹️',          # 정지
        'restart': '🔄',       # 재시작
        'pause': '⏸️',         # 일시정지
        'resume': '▶️',        # 재개
        'cancel': '❌',        # 취소
        'confirm': '✅',       # 확인
        'apply': '✨',         # 적용
        'reset': '🔃',         # 리셋
        'clear': '🧹',         # 지우기
        'select': '👆',        # 선택
        'deselect': '👋',      # 선택 해제
        'expand': '📖',        # 펼치기
        'collapse': '📕',      # 접기
        'maximize': '🔳',      # 최대화
        'minimize': '🔲',      # 최소화
    }
    
    # === 데이터 아이콘 ===
    DATA = {
        'table': '📊',         # 테이블
        'chart': '📈',         # 차트
        'graph': '📉',         # 그래프
        'statistics': '📊',    # 통계
        'report': '📋',        # 보고서
        'log': '📝',           # 로그
        'history': '📜',       # 이력
        'backup': '💾',        # 백업
        'archive': '📦',       # 아카이브
        'sync': '🔄',          # 동기화
        'merge': '🔀',         # 병합
        'split': '🔂',         # 분할
        'compare': '⚖️',       # 비교
        'analyze': '🔬',       # 분석
        'validate': '✔️',      # 검증
        'process': '⚙️',       # 처리
    }
    
    # === QC 관련 아이콘 ===
    QC = {
        'inspection': '🔍',    # 검수
        'quality': '💎',       # 품질
        'test': '🧪',          # 테스트
        'check': '✅',         # 체크
        'verify': '🔍',        # 검증
        'approve': '👍',       # 승인
        'reject': '👎',        # 거부
        'review': '👀',        # 검토
        'measure': '📏',       # 측정
        'calibrate': '⚖️',     # 교정
        'standard': '📐',      # 표준
        'specification': '📋', # 사양
        'tolerance': '🎯',     # 공차
        'precision': '🔬',     # 정밀도
        'accuracy': '🎯',      # 정확도
        'checklist': '☑️',     # 체크리스트
        'passed': '✅',        # 통과
        'failed': '❌',        # 실패
        'critical': '🔴',      # 임계
        'major': '🟠',         # 주요
        'minor': '🟡',         # 경미
    }
    
    # === 시스템 아이콘 ===
    SYSTEM = {
        'user': '👤',          # 사용자
        'admin': '👑',         # 관리자
        'engineer': '👨‍💻',      # 엔지니어
        'operator': '👷',      # 운영자
        'guest': '👻',         # 게스트
        'lock': '🔒',          # 잠금
        'unlock': '🔓',        # 잠금해제
        'security': '🔐',      # 보안
        'permission': '🗝️',    # 권한
        'notification': '🔔',  # 알림
        'alert': '🚨',         # 경고
        'message': '💬',       # 메시지
        'email': '📧',         # 이메일
        'phone': '📞',         # 전화
        'printer': '🖨️',       # 프린터
        'monitor': '🖥️',       # 모니터
        'keyboard': '⌨️',      # 키보드
        'mouse': '🖱️',         # 마우스
    }
    
    # === 장비 아이콘 ===
    EQUIPMENT = {
        'equipment': '🏭',     # 장비
        'machine': '⚙️',       # 기계
        'tool': '🔧',          # 도구
        'instrument': '🔬',    # 계측기
        'sensor': '📡',        # 센서
        'controller': '🎛️',    # 컨트롤러
        'motor': '⚡',         # 모터
        'pump': '🔄',          # 펌프
        'valve': '🔧',         # 밸브
        'gauge': '📊',         # 게이지
        'meter': '📏',         # 계측기
        'switch': '🔘',        # 스위치
        'button': '🔴',        # 버튼
        'display': '📺',       # 디스플레이
        'cable': '🔌',         # 케이블
        'connector': '🔗',     # 커넥터
    }
    
    @classmethod
    def get_icon(cls, category: str, name: str, default: str = '•') -> str:
        """카테고리와 이름으로 아이콘 반환"""
        category_dict = getattr(cls, category.upper(), {})
        return category_dict.get(name, default)
    
    @classmethod
    def get_status_icon(cls, status: str) -> str:
        """상태 아이콘 반환"""
        return cls.STATUS.get(status, '❓')
    
    @classmethod
    def get_severity_icon(cls, severity: str) -> str:
        """QC 심각도 아이콘 반환"""
        severity_map = {
            '높음': cls.QC['critical'],      # 🔴
            '중간': cls.QC['major'],         # 🟠
            '낮음': cls.QC['minor'],         # 🟡
            '통과': cls.QC['passed'],        # ✅
            '실패': cls.QC['failed'],        # ❌
        }
        return severity_map.get(severity, '❓')
    
    @classmethod
    def get_action_icon(cls, action: str) -> str:
        """액션 아이콘 반환"""
        return cls.ACTION.get(action, '🔧')
    
    @classmethod
    def format_text_with_icon(cls, text: str, category: str, icon_name: str) -> str:
        """텍스트에 아이콘 추가"""
        icon = cls.get_icon(category, icon_name)
        return f"{icon} {text}"
    
    @classmethod
    def format_status_text(cls, text: str, status: str) -> str:
        """상태 텍스트 포맷팅"""
        icon = cls.get_status_icon(status)
        return f"{icon} {text}"
    
    @classmethod
    def format_qc_severity_text(cls, text: str, severity: str) -> str:
        """QC 심각도 텍스트 포맷팅"""
        icon = cls.get_severity_icon(severity)
        return f"{icon} {text}"
    
    @classmethod
    def get_all_icons(cls) -> Dict[str, Dict[str, str]]:
        """모든 아이콘 딕셔너리 반환"""
        return {
            'general': cls.GENERAL,
            'status': cls.STATUS,
            'action': cls.ACTION,
            'data': cls.DATA,
            'qc': cls.QC,
            'system': cls.SYSTEM,
            'equipment': cls.EQUIPMENT
        }
    
    @classmethod
    def search_icons(cls, keyword: str) -> List[Dict[str, str]]:
        """키워드로 아이콘 검색"""
        results = []
        all_icons = cls.get_all_icons()
        
        for category, icons in all_icons.items():
            for name, icon in icons.items():
                if keyword.lower() in name.lower():
                    results.append({
                        'category': category,
                        'name': name,
                        'icon': icon
                    })
        
        return results


# 편의를 위한 전역 함수들
def get_engineering_icon(category: str, name: str, default: str = '•') -> str:
    """Engineering 아이콘 반환"""
    return EngineeringIcons.get_icon(category, name, default)

def format_engineering_text(text: str, category: str, icon_name: str) -> str:
    """Engineering 스타일 텍스트 포맷팅"""
    return EngineeringIcons.format_text_with_icon(text, category, icon_name)

def get_qc_severity_icon(severity: str) -> str:
    """QC 심각도 아이콘 반환"""
    return EngineeringIcons.get_severity_icon(severity)

def get_status_icon(status: str) -> str:
    """상태 아이콘 반환"""
    return EngineeringIcons.get_status_icon(status)


# 상수들 (빠른 접근용)
class Icons:
    """빠른 접근을 위한 아이콘 상수"""
    
    # 자주 사용되는 아이콘들
    APP = '🔧'
    SUCCESS = '✅'
    ERROR = '❌'
    WARNING = '⚠️'
    INFO = 'ℹ️'
    LOADING = '⏳'
    EXECUTE = '🚀'
    SEARCH = '🔍'
    SETTINGS = '⚙️'
    FOLDER = '📁'
    FILE = '📄'
    REFRESH = '🔄'
    EXPORT = '📤'
    IMPORT = '📥'
    
    # QC 관련
    QC_INSPECTION = '🔍'
    QC_HIGH = '🔴'
    QC_MEDIUM = '🟠'
    QC_LOW = '🟡'
    QC_PASS = '✅'
    QC_FAIL = '❌'
    
    # 데이터 관련
    DATA_TABLE = '📊'
    DATA_CHART = '📈'
    DATA_REPORT = '📋'
    DATA_LOG = '📝'
    DATA_COMPARE = '⚖️'
    
    # 장비 관련
    EQUIPMENT = '🏭'
    TOOL = '🔧'
    MACHINE = '⚙️'
    INSTRUMENT = '🔬'