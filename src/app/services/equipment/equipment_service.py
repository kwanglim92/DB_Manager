"""
장비 관리 서비스 구현체

장비 유형 CRUD 작업을 담당하는 서비스 클래스입니다.
기존 DBSchema를 활용하되 서비스 레이어에서 비즈니스 로직을 처리합니다.
"""

from typing import List, Optional
import logging
from contextlib import contextmanager

from ..interfaces.equipment_service_interface import IEquipmentService, EquipmentType
from ..common.cache_service import CacheService
from ..common.logging_service import LoggingService

class EquipmentService(IEquipmentService):
    """장비 관리 서비스 구현체"""
    
    def __init__(self, db_schema, cache_service: Optional[CacheService] = None):
        """
        서비스 초기화
        
        Args:
            db_schema: 데이터베이스 스키마 인스턴스
            cache_service: 캐시 서비스 (선택사항)
        """
        self._db_schema = db_schema
        self._cache = cache_service or CacheService(max_size=500, default_ttl=300)  # 5분 TTL
        self._logging = LoggingService()
        self._logger = self._logging.get_logger(self.__class__.__name__)
        
        # 캐시 키 상수
        self._CACHE_KEY_ALL_TYPES = "equipment_types_all"
        self._CACHE_KEY_TYPE_PREFIX = "equipment_type_"
    
    @contextmanager
    def _transaction(self):
        """트랜잭션 컨텍스트 매니저"""
        try:
            yield
            self._invalidate_cache()  # 트랜잭션 완료 후 캐시 무효화
            self._logging.log_service_action("EquipmentService", "Transaction completed")
        except Exception as e:
            self._logging.log_error("EquipmentService", e, "Transaction failed")
            raise
    
    def _invalidate_cache(self, type_id: Optional[int] = None):
        """캐시 무효화"""
        if type_id:
            # 특정 장비 유형 캐시만 무효화
            self._cache.delete(f"{self._CACHE_KEY_TYPE_PREFIX}{type_id}")
        else:
            # 전체 캐시 무효화
            self._cache.delete(self._CACHE_KEY_ALL_TYPES)
            # 개별 장비 유형 캐시들도 정리 (간단한 방법)
            self._cache.cleanup_expired()
    
    def get_all_equipment_types(self) -> List[EquipmentType]:
        """
        모든 장비 유형 조회
        
        Returns:
            장비 유형 리스트
        """
        # 캐시 확인
        cached_result = self._cache.get(self._CACHE_KEY_ALL_TYPES)
        if cached_result is not None:
            self._logger.debug("캐시에서 장비 유형 목록 조회")
            return cached_result
        
        try:
            raw_data = self._db_schema.get_equipment_types()
            equipment_types = [
                EquipmentType(
                    id=type_id,
                    name=name,
                    description=description or ""
                )
                for type_id, name, description in raw_data
            ]
            
            # 결과 캐싱
            self._cache.set(self._CACHE_KEY_ALL_TYPES, equipment_types)
            
            self._logging.log_service_action(
                "EquipmentService", 
                "Retrieved equipment types",
                {"count": len(equipment_types)}
            )
            
            return equipment_types
            
        except Exception as e:
            self._logging.log_error("EquipmentService", e, "Failed to retrieve equipment types")
            raise
    
    def get_equipment_type(self, type_id: int) -> Optional[EquipmentType]:
        """
        특정 장비 유형 조회
        
        Args:
            type_id: 장비 유형 ID
            
        Returns:
            장비 유형 객체 또는 None
        """
        if type_id <= 0:
            raise ValueError("장비 유형 ID는 양수여야 합니다")
        
        # 캐시 확인
        cache_key = f"{self._CACHE_KEY_TYPE_PREFIX}{type_id}"
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            self._logger.debug(f"캐시에서 장비 유형 조회: ID {type_id}")
            return cached_result
        
        # 전체 목록에서 찾기
        all_types = self.get_all_equipment_types()
        for equipment_type in all_types:
            if equipment_type.id == type_id:
                # 개별 캐시에도 저장
                self._cache.set(cache_key, equipment_type)
                return equipment_type
        
        self._logger.debug(f"장비 유형을 찾을 수 없음: ID {type_id}")
        return None
    
    def create_equipment_type(self, name: str, description: str = "") -> int:
        """
        새 장비 유형 생성
        
        Args:
            name: 장비 유형 이름
            description: 설명 (선택사항)
            
        Returns:
            생성된 장비 유형 ID
            
        Raises:
            ValueError: 이름이 비어있거나 중복된 경우
        """
        # 입력 검증
        if not name or not name.strip():
            raise ValueError("장비 유형 이름은 필수입니다")
        
        name = name.strip()
        description = description.strip()
        
        # 중복 검사
        existing_types = self.get_all_equipment_types()
        for existing in existing_types:
            if existing.name.lower() == name.lower():
                raise ValueError(f"장비 유형 '{name}'이 이미 존재합니다")
        
        with self._transaction():
            try:
                type_id = self._db_schema.add_equipment_type(name, description)
                
                self._logging.log_service_action(
                    "EquipmentService",
                    "Created equipment type",
                    {"name": name, "id": type_id, "description": description}
                )
                
                return type_id
                
            except Exception as e:
                self._logging.log_error("EquipmentService", e, f"Failed to create equipment type: {name}")
                raise
    
    def update_equipment_type(self, type_id: int, name: str, description: str) -> bool:
        """
        장비 유형 정보 수정
        
        Args:
            type_id: 장비 유형 ID
            name: 새 이름
            description: 새 설명
            
        Returns:
            수정 성공 여부
        """
        if type_id <= 0:
            raise ValueError("장비 유형 ID는 양수여야 합니다")
        
        if not name or not name.strip():
            raise ValueError("장비 유형 이름은 필수입니다")
        
        name = name.strip()
        description = description.strip()
        
        # 존재하는 장비 유형인지 확인
        existing = self.get_equipment_type(type_id)
        if not existing:
            raise ValueError(f"장비 유형 ID {type_id}를 찾을 수 없습니다")
        
        # 다른 장비 유형과 이름 중복 검사
        all_types = self.get_all_equipment_types()
        for other in all_types:
            if other.id != type_id and other.name.lower() == name.lower():
                raise ValueError(f"장비 유형 '{name}'이 이미 존재합니다")
        
        with self._transaction():
            try:
                # DBSchema에 update 메서드가 없으므로 현재는 미구현
                # 실제 구현에서는 DBSchema에 update_equipment_type 메서드 추가 필요
                self._logging.log_service_action(
                    "EquipmentService",
                    "Update equipment type requested",
                    {"id": type_id, "name": name, "description": description}
                )
                
                self._logger.warning("장비 유형 업데이트 기능은 DBSchema에서 지원되지 않습니다")
                return False
                
            except Exception as e:
                self._logging.log_error("EquipmentService", e, f"Failed to update equipment type: {type_id}")
                raise
    
    def delete_equipment_type(self, type_id: int) -> bool:
        """
        장비 유형 삭제 (관련 데이터 포함)
        
        Args:
            type_id: 삭제할 장비 유형 ID
            
        Returns:
            삭제 성공 여부
        """
        if type_id <= 0:
            raise ValueError("장비 유형 ID는 양수여야 합니다")
        
        # 존재하는 장비 유형인지 확인
        existing = self.get_equipment_type(type_id)
        if not existing:
            raise ValueError(f"장비 유형 ID {type_id}를 찾을 수 없습니다")
        
        with self._transaction():
            try:
                success = self._db_schema.delete_equipment_type(type_id)
                
                if success:
                    # 해당 장비 유형의 캐시 무효화
                    self._invalidate_cache(type_id)
                    
                    self._logging.log_service_action(
                        "EquipmentService",
                        "Deleted equipment type",
                        {"id": type_id, "name": existing.name}
                    )
                else:
                    self._logger.warning(f"장비 유형 삭제 실패: ID {type_id}")
                
                return success
                
            except Exception as e:
                self._logging.log_error("EquipmentService", e, f"Failed to delete equipment type: {type_id}")
                raise
    
    def search_equipment_types(self, query: str) -> List[EquipmentType]:
        """
        장비 유형 검색
        
        Args:
            query: 검색어
            
        Returns:
            검색 결과 리스트
        """
        if not query or not query.strip():
            return self.get_all_equipment_types()
        
        all_types = self.get_all_equipment_types()
        query_lower = query.lower().strip()
        
        results = []
        for equipment_type in all_types:
            if (query_lower in equipment_type.name.lower() or 
                query_lower in equipment_type.description.lower()):
                results.append(equipment_type)
        
        self._logging.log_service_action(
            "EquipmentService",
            "Searched equipment types",
            {"query": query, "result_count": len(results)}
        )
        
        return results
    
    def get_cache_statistics(self) -> dict:
        """캐시 통계 정보 조회"""
        return self._cache.get_statistics() 