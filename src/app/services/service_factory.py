"""
서비스 팩토리

서비스 인스턴스 생성과 의존성 주입을 관리합니다.
기존 코드와의 호환성을 위한 어댑터 패턴도 제공합니다.
"""

from typing import Optional, Dict, Any
import logging

from .common.service_registry import ServiceRegistry
from .common.cache_service import CacheService
from .common.logging_service import LoggingService

# 인터페이스들
from .interfaces.equipment_service_interface import IEquipmentService, IParameterService
from .interfaces.data_service_interface import IDataProcessingService, IFileService
from .interfaces.validation_service_interface import IValidationService, IQCService

# 구현체들
from .equipment.equipment_service import EquipmentService

class ServiceFactory:
    """서비스 팩토리 - 서비스 인스턴스 생성 및 관리"""
    
    def __init__(self, db_schema=None, config: Optional[Dict[str, Any]] = None):
        """
        팩토리 초기화
        
        Args:
            db_schema: 데이터베이스 스키마 인스턴스
            config: 서비스 설정 딕셔너리
        """
        self._db_schema = db_schema
        self._config = config or {}
        self._registry = ServiceRegistry()
        self._logging = LoggingService()
        self._logger = self._logging.get_logger(self.__class__.__name__)
        
        # 공통 서비스들 초기화
        self._setup_common_services()
        
        # 핵심 서비스들 등록
        self._register_services()
    
    def _setup_common_services(self):
        """공통 서비스들 설정"""
        # 캐시 서비스 설정
        cache_config = self._config.get('cache', {})
        cache_service = CacheService(
            max_size=cache_config.get('max_size', 1000),
            default_ttl=cache_config.get('default_ttl', 300)
        )
        
        # 공통 서비스들 등록
        self._registry.register_singleton(CacheService, cache_service)
        self._registry.register_singleton(LoggingService, self._logging)
        
        self._logger.info("공통 서비스 설정 완료")
    
    def _register_services(self):
        """핵심 서비스들 등록"""
        try:
            # 장비 관리 서비스 등록
            if self._db_schema:
                cache_service = self._registry.get_service(CacheService)
                equipment_service = EquipmentService(self._db_schema, cache_service)
                self._registry.register_singleton(IEquipmentService, equipment_service)
                
                self._logger.info("장비 관리 서비스 등록 완료")
            else:
                self._logger.warning("DB 스키마가 없어 장비 관리 서비스를 등록할 수 없습니다")
            
            # TODO: 다른 서비스들도 점진적으로 추가
            # self._registry.register_singleton(IParameterService, parameter_service)
            # self._registry.register_singleton(IDataProcessingService, data_service)
            
        except Exception as e:
            self._logger.error(f"서비스 등록 중 오류 발생: {str(e)}")
            raise
    
    def get_equipment_service(self) -> IEquipmentService:
        """장비 관리 서비스 조회"""
        return self._registry.get_service(IEquipmentService)
    
    def get_parameter_service(self) -> Optional[IParameterService]:
        """파라미터 서비스 조회"""
        try:
            return self._registry.get_service(IParameterService)
        except ValueError:
            self._logger.warning("파라미터 서비스가 등록되지 않았습니다")
            return None
    
    def get_data_processing_service(self) -> Optional[IDataProcessingService]:
        """데이터 처리 서비스 조회"""
        try:
            return self._registry.get_service(IDataProcessingService)
        except ValueError:
            self._logger.warning("데이터 처리 서비스가 등록되지 않았습니다")
            return None
    
    def get_validation_service(self) -> Optional[IValidationService]:
        """검증 서비스 조회"""
        try:
            return self._registry.get_service(IValidationService)
        except ValueError:
            self._logger.warning("검증 서비스가 등록되지 않았습니다")
            return None
    
    def get_qc_service(self) -> Optional[IQCService]:
        """QC 서비스 조회"""
        try:
            return self._registry.get_service(IQCService)
        except ValueError:
            self._logger.warning("QC 서비스가 등록되지 않았습니다")
            return None
    
    def get_cache_service(self) -> CacheService:
        """캐시 서비스 조회"""
        return self._registry.get_service(CacheService)
    
    def get_logging_service(self) -> LoggingService:
        """로깅 서비스 조회"""
        return self._registry.get_service(LoggingService)
    
    def is_service_available(self, service_type) -> bool:
        """서비스 사용 가능 여부 확인"""
        return self._registry.is_registered(service_type)
    
    def get_service_status(self) -> Dict[str, str]:
        """모든 서비스의 상태 조회"""
        return self._registry.get_registered_services()
    
    def cleanup(self):
        """팩토리 정리"""
        self._registry.clear_all()
        self._logger.info("서비스 팩토리 정리 완료")

class LegacyAdapter:
    """
    기존 코드와의 호환성을 위한 어댑터
    
    기존 DBManager 클래스의 메서드들을 새로운 서비스로 연결합니다.
    """
    
    def __init__(self, service_factory: ServiceFactory):
        """
        어댑터 초기화
        
        Args:
            service_factory: 서비스 팩토리 인스턴스
        """
        self._factory = service_factory
        self._logger = service_factory.get_logging_service().get_logger(self.__class__.__name__)
    
    def get_equipment_types(self):
        """
        기존 get_equipment_types 메서드 호환
        
        Returns:
            기존 형식의 장비 유형 리스트 [(id, name, description), ...]
        """
        try:
            equipment_service = self._factory.get_equipment_service()
            equipment_types = equipment_service.get_all_equipment_types()
            
            # 기존 형식으로 변환
            return [(eq.id, eq.name, eq.description) for eq in equipment_types]
            
        except Exception as e:
            self._logger.error(f"어댑터: 장비 유형 조회 실패 - {str(e)}")
            # 실패 시 빈 리스트 반환 (기존 동작 유지)
            return []
    
    def add_equipment_type(self, type_name: str, description: str = ""):
        """
        기존 add_equipment_type 메서드 호환
        
        Args:
            type_name: 장비 유형 이름
            description: 설명
            
        Returns:
            생성된 장비 유형 ID
        """
        try:
            equipment_service = self._factory.get_equipment_service()
            return equipment_service.create_equipment_type(type_name, description)
            
        except Exception as e:
            self._logger.error(f"어댑터: 장비 유형 생성 실패 - {str(e)}")
            raise
    
    def delete_equipment_type(self, type_id: int):
        """
        기존 delete_equipment_type 메서드 호환
        
        Args:
            type_id: 삭제할 장비 유형 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            equipment_service = self._factory.get_equipment_service()
            return equipment_service.delete_equipment_type(type_id)
            
        except Exception as e:
            self._logger.error(f"어댑터: 장비 유형 삭제 실패 - {str(e)}")
            return False 