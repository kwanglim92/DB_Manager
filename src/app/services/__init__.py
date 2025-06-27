"""
서비스 레이어 패키지

비즈니스 로직을 담당하는 서비스들을 제공합니다.
UI와 데이터 레이어를 분리하여 테스트 가능하고 재사용 가능한 구조를 만듭니다.

아키텍처:
- interfaces/: 서비스 인터페이스 정의
- equipment/: 장비 관리 서비스
- data/: 데이터 처리 서비스  
- validation/: 검증 및 QC 서비스
- common/: 공통 서비스 및 유틸리티
"""

# 공통 서비스들
from .common.service_registry import ServiceRegistry
from .common.cache_service import CacheService

# 핵심 서비스 인터페이스들
from .interfaces import (
    IEquipmentService,
    IParameterService,
    IDataProcessingService,
    IFileService,
    IValidationService,
    IQCService
)

# 구현체들 (점진적 전환을 위해 조건부 import)
try:
    from .equipment import EquipmentService
    # 아직 구현되지 않은 서비스들은 주석 처리
    # from .data import DataProcessingService, FileService
    # from .validation import ValidationService, QCService
    
    # 서비스 팩토리
    from .service_factory import ServiceFactory
    
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"서비스 import 실패: {e}")
    SERVICES_AVAILABLE = False
    # import 실패 시 기본 팩토리만 사용
    from .service_factory import ServiceFactory

# 서비스 인터페이스들
from .interfaces.data_service_interface import DataServiceInterface
from .interfaces.equipment_service_interface import EquipmentServiceInterface
from .interfaces.validation_service_interface import ValidationServiceInterface

# 🎯 2단계-A 완료: 서비스 레이어 도입
SERVICE_LAYER_VERSION = "2.0.0"
SERVICE_LAYER_STATUS = "ACTIVE"

def get_service_info():
    """서비스 레이어 정보 반환"""
    return {
        'version': SERVICE_LAYER_VERSION,
        'status': SERVICE_LAYER_STATUS,
        'description': '2단계-A 완료: 서비스 레이어 도입',
        'services': [
            'ServiceFactory (중앙 서비스 관리)',
            'EquipmentService (장비 관리)',
            'LoggingService (로깅)',
            'CacheService (캐싱)',
            'ServiceRegistry (서비스 레지스트리)'
        ]
    }

# 레거시 어댑터 (기존 코드 호환성을 위해)
class LegacyAdapter:
    """
    기존 코드와의 호환성을 위한 레거시 어댑터
    USE_NEW_SERVICES 플래그를 통해 점진적 전환 지원
    """
    
    def __init__(self, service_factory=None):
        self.service_factory = service_factory or ServiceFactory()
        self._use_new_services = self._load_use_new_services_flag()
    
    def _load_use_new_services_flag(self) -> bool:
        """USE_NEW_SERVICES 플래그 로드"""
        try:
            from ..core.config import AppConfig
            config = AppConfig()
            return config.get_setting('USE_NEW_SERVICES', False)
        except:
            return False
    
    def get_equipment_service(self):
        """장비 서비스 반환 (새 서비스 또는 None)"""
        if self._use_new_services:
            try:
                return self.service_factory.get_equipment_service()
            except:
                return None
        return None
    
    def get_logging_service(self):
        """로깅 서비스 반환"""
        if self._use_new_services:
            try:
                return self.service_factory.get_logging_service()
            except:
                return None
        return None

# 전역 레거시 어댑터 인스턴스 (지연 초기화)
_legacy_adapter = None

def _get_legacy_adapter():
    """레거시 어댑터 지연 초기화"""
    global _legacy_adapter
    if _legacy_adapter is None:
        _legacy_adapter = LegacyAdapter()
    return _legacy_adapter

def get_equipment_service():
    """전역 장비 서비스 접근"""
    return _get_legacy_adapter().get_equipment_service()

def get_logging_service():
    """전역 로깅 서비스 접근"""
    return _get_legacy_adapter().get_logging_service()

__all__ = [
    # 인터페이스
    'IEquipmentService',
    'IParameterService', 
    'IDataProcessingService',
    'IFileService',
    'IValidationService',
    'IQCService',
    
    # 공통 서비스
    'ServiceRegistry',
    'CacheService',
    
    # 팩토리 (서비스가 사용 가능한 경우)
    'ServiceFactory' if SERVICES_AVAILABLE else None,
    
    # 상태 플래그
    'SERVICES_AVAILABLE',
    
    # 핵심 팩토리
    'ServiceFactory',
    
    # 인터페이스들
    'DataServiceInterface',
    'EquipmentServiceInterface', 
    'ValidationServiceInterface',
    
    # 레거시 지원
    'LegacyAdapter',
    'get_equipment_service',
    'get_logging_service',
    
    # 메타 정보
    'get_service_info',
] 