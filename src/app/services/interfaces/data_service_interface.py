"""
데이터 처리 서비스 인터페이스

파일 처리, 데이터 변환, 비교 분석을 위한 추상 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd

@dataclass
class FileInfo:
    """파일 정보 데이터 클래스"""
    path: str
    name: str
    size: int
    format: str
    encoding: str = "utf-8"
    is_valid: bool = True
    error_message: Optional[str] = None

@dataclass 
class DifferenceAnalysis:
    """차이점 분석 결과 데이터 클래스"""
    total_items: int
    different_items: int
    same_items: int
    missing_items: Dict[str, int]
    details: List[Dict[str, Any]]
    summary: Dict[str, Any]

@dataclass
class DataTransformOptions:
    """데이터 변환 옵션"""
    remove_duplicates: bool = False
    normalize_values: bool = False
    fill_missing: bool = False
    custom_transformations: List[str] = None

class IFileService(ABC):
    """파일 처리 서비스 인터페이스"""
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """지원하는 파일 형식 목록"""
        pass
    
    @abstractmethod
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        파일 유효성 검사
        
        Returns:
            (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def get_file_info(self, file_path: str) -> FileInfo:
        """파일 정보 조회"""
        pass
    
    @abstractmethod
    def parse_file(self, file_path: str) -> pd.DataFrame:
        """단일 파일 파싱"""
        pass
    
    @abstractmethod
    def parse_multiple_files(self, file_paths: List[str]) -> Dict[str, pd.DataFrame]:
        """여러 파일 동시 파싱"""
        pass
    
    @abstractmethod
    def export_data(self, data: pd.DataFrame, file_path: str, format: str = "excel") -> bool:
        """데이터를 파일로 내보내기"""
        pass

class IDataProcessingService(ABC):
    """데이터 처리 핵심 서비스 인터페이스"""
    
    @abstractmethod
    def merge_data(self, dataframes: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """여러 데이터프레임을 병합"""
        pass
    
    @abstractmethod
    def analyze_differences(self, merged_data: pd.DataFrame) -> DifferenceAnalysis:
        """데이터 차이점 분석"""
        pass
    
    @abstractmethod
    def filter_data(self, data: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """데이터 필터링"""
        pass
    
    @abstractmethod
    def transform_data(self, data: pd.DataFrame, options: DataTransformOptions) -> pd.DataFrame:
        """데이터 변환"""
        pass
    
    @abstractmethod
    def get_data_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """데이터 통계 정보 조회"""
        pass
    
    @abstractmethod
    def compare_with_defaults(self, data: pd.DataFrame, equipment_type_id: int) -> Dict[str, Any]:
        """Default DB와 비교 분석"""
        pass

class DataServiceInterface(ABC):
    """데이터 서비스 인터페이스"""
    
    @abstractmethod
    def load_data(self, source: str, **kwargs) -> Any:
        """데이터 로드"""
        pass
    
    @abstractmethod
    def save_data(self, data: Any, destination: str, **kwargs) -> bool:
        """데이터 저장"""
        pass
    
    @abstractmethod
    def validate_data(self, data: Any) -> bool:
        """데이터 유효성 검사"""
        pass
    
    @abstractmethod
    def transform_data(self, data: Any, transformation_rules: Dict) -> Any:
        """데이터 변환"""
        pass
    
    @abstractmethod
    def get_data_info(self, data: Any) -> Dict[str, Any]:
        """데이터 정보 반환"""
        pass 