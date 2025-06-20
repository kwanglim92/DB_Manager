"""
서비스 레지스트리

애플리케이션의 모든 서비스들을 중앙에서 관리하는 레지스트리입니다.
의존성 주입과 서비스 라이프사이클을 관리합니다.
"""

from typing import Dict, Type, Any, Optional, TypeVar, Generic
from abc import ABC
import logging

T = TypeVar('T')

class ServiceRegistry:
    """서비스 레지스트리 - 싱글톤 패턴"""
    
    _instance: Optional['ServiceRegistry'] = None
    _services: Dict[Type, Any] = {}
    _singletons: Dict[Type, Any] = {}
    
    def __new__(cls) -> 'ServiceRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._logger = logging.getLogger(cls.__name__)
        return cls._instance
    
    def register_singleton(self, service_type: Type[T], implementation: T) -> None:
        """
        싱글톤 서비스 등록
        
        Args:
            service_type: 서비스 인터페이스 타입
            implementation: 구현 인스턴스
        """
        self._singletons[service_type] = implementation
        self._logger.info(f"싱글톤 서비스 등록: {service_type.__name__}")
    
    def register_transient(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """
        매번 새 인스턴스를 생성하는 서비스 등록
        
        Args:
            service_type: 서비스 인터페이스 타입
            implementation_type: 구현 클래스 타입
        """
        self._services[service_type] = implementation_type
        self._logger.info(f"일반 서비스 등록: {service_type.__name__}")
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        서비스 인스턴스 조회
        
        Args:
            service_type: 서비스 타입
            
        Returns:
            서비스 인스턴스
            
        Raises:
            ValueError: 서비스가 등록되지 않은 경우
        """
        # 싱글톤 서비스 먼저 확인
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        # 일반 서비스 확인
        if service_type in self._services:
            implementation_type = self._services[service_type]
            return implementation_type()
        
        raise ValueError(f"서비스가 등록되지 않았습니다: {service_type.__name__}")
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """
        서비스가 등록되었는지 확인
        
        Args:
            service_type: 서비스 타입
            
        Returns:
            등록 여부
        """
        return service_type in self._singletons or service_type in self._services
    
    def unregister(self, service_type: Type[T]) -> None:
        """
        서비스 등록 해제
        
        Args:
            service_type: 서비스 타입
        """
        if service_type in self._singletons:
            del self._singletons[service_type]
            self._logger.info(f"싱글톤 서비스 해제: {service_type.__name__}")
        
        if service_type in self._services:
            del self._services[service_type]
            self._logger.info(f"일반 서비스 해제: {service_type.__name__}")
    
    def clear_all(self) -> None:
        """모든 서비스 등록 해제"""
        self._singletons.clear()
        self._services.clear()
        self._logger.info("모든 서비스 등록이 해제되었습니다")
    
    def get_registered_services(self) -> Dict[str, str]:
        """
        등록된 서비스 목록 조회
        
        Returns:
            서비스 타입별 등록 상태 딕셔너리
        """
        result = {}
        
        for service_type in self._singletons:
            result[service_type.__name__] = "Singleton"
        
        for service_type in self._services:
            result[service_type.__name__] = "Transient"
        
        return result 