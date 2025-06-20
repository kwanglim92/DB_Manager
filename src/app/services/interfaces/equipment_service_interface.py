"""
장비 관리 서비스 인터페이스

장비 유형, 파라미터, Default DB 관리를 위한 추상 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class EquipmentType:
    """장비 유형 데이터 클래스"""
    id: int
    name: str
    description: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class Parameter:
    """파라미터 데이터 클래스"""
    id: Optional[int]
    equipment_type_id: int
    name: str
    default_value: str
    min_spec: Optional[str] = None
    max_spec: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class IEquipmentService(ABC):
    """장비 관리 핵심 서비스 인터페이스"""
    
    @abstractmethod
    def get_all_equipment_types(self) -> List[EquipmentType]:
        """모든 장비 유형 조회"""
        pass
    
    @abstractmethod 
    def get_equipment_type(self, type_id: int) -> Optional[EquipmentType]:
        """특정 장비 유형 조회"""
        pass
    
    @abstractmethod
    def create_equipment_type(self, name: str, description: str = "") -> int:
        """새 장비 유형 생성"""
        pass
    
    @abstractmethod
    def update_equipment_type(self, type_id: int, name: str, description: str) -> bool:
        """장비 유형 정보 수정"""
        pass
    
    @abstractmethod
    def delete_equipment_type(self, type_id: int) -> bool:
        """장비 유형 삭제 (관련 데이터 포함)"""
        pass
    
    @abstractmethod
    def search_equipment_types(self, query: str) -> List[EquipmentType]:
        """장비 유형 검색"""
        pass

class IParameterService(ABC):
    """파라미터 관리 서비스 인터페이스"""
    
    @abstractmethod
    def get_parameters_by_equipment_type(self, equipment_type_id: int) -> List[Parameter]:
        """특정 장비 유형의 파라미터 조회"""
        pass
    
    @abstractmethod
    def get_parameter(self, parameter_id: int) -> Optional[Parameter]:
        """특정 파라미터 조회"""
        pass
    
    @abstractmethod
    def create_parameter(self, parameter: Parameter) -> int:
        """새 파라미터 생성"""
        pass
    
    @abstractmethod
    def update_parameter(self, parameter_id: int, parameter: Parameter) -> bool:
        """파라미터 정보 수정"""
        pass
    
    @abstractmethod
    def delete_parameter(self, parameter_id: int) -> bool:
        """파라미터 삭제"""
        pass
    
    @abstractmethod
    def search_parameters(self, query: str, equipment_type_id: Optional[int] = None) -> List[Parameter]:
        """파라미터 검색"""
        pass
    
    @abstractmethod
    def validate_parameter_value(self, parameter_id: int, value: str) -> bool:
        """파라미터 값 유효성 검사"""
        pass

class EquipmentServiceInterface(ABC):
    """장비 서비스 인터페이스"""
    
    @abstractmethod
    def get_equipment_types(self) -> List[Dict[str, Any]]:
        """모든 장비 유형 반환"""
        pass
    
    @abstractmethod
    def get_equipment_type_by_id(self, type_id: int) -> Optional[Dict[str, Any]]:
        """ID로 장비 유형 조회"""
        pass
    
    @abstractmethod
    def add_equipment_type(self, name: str, description: str = "") -> bool:
        """장비 유형 추가"""
        pass
    
    @abstractmethod
    def update_equipment_type(self, type_id: int, name: str, description: str = "") -> bool:
        """장비 유형 수정"""
        pass
    
    @abstractmethod
    def delete_equipment_type(self, type_id: int) -> bool:
        """장비 유형 삭제"""
        pass
    
    @abstractmethod
    def get_equipment_parameters(self, type_id: int) -> List[Dict[str, Any]]:
        """장비 유형별 파라미터 목록 반환"""
        pass
    
    @abstractmethod
    def validate_equipment_data(self, data: Dict[str, Any]) -> bool:
        """장비 데이터 유효성 검사"""
        pass 