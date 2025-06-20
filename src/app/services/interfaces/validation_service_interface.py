"""
검증 서비스 인터페이스

데이터 검증, QC 체크, 이상치 탐지를 위한 추상 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import pandas as pd

class ValidationSeverity(Enum):
    """검증 결과 심각도"""
    LOW = "낮음"
    MEDIUM = "중간" 
    HIGH = "높음"
    CRITICAL = "심각"

class ValidationStatus(Enum):
    """검증 상태"""
    PASSED = "통과"
    FAILED = "실패"
    WARNING = "경고"
    PENDING = "대기"

@dataclass
class ValidationIssue:
    """검증 이슈 데이터 클래스"""
    parameter: str
    issue_type: str
    description: str
    severity: ValidationSeverity
    status: ValidationStatus
    value: Optional[str] = None
    expected: Optional[str] = None
    recommendation: Optional[str] = None

@dataclass
class ValidationResult:
    """검증 결과 데이터 클래스"""
    total_parameters: int
    passed_count: int
    failed_count: int
    warning_count: int
    issues: List[ValidationIssue]
    summary: Dict[str, Any]
    execution_time: float
    timestamp: str

@dataclass
class OutlierResult:
    """이상치 탐지 결과"""
    parameter: str
    value: float
    expected_range: tuple
    deviation: float
    method: str
    confidence: float
    is_outlier: bool

@dataclass
class QCCheckConfig:
    """QC 검사 설정"""
    check_outliers: bool = True
    check_missing_values: bool = True
    check_duplicates: bool = True
    check_data_types: bool = True
    outlier_method: str = "zscore"
    outlier_threshold: float = 3.0
    custom_rules: List[str] = None

class IValidationService(ABC):
    """데이터 검증 서비스 인터페이스"""
    
    @abstractmethod
    def validate_against_defaults(self, data: pd.DataFrame, equipment_type_id: int) -> ValidationResult:
        """Default DB 기준으로 데이터 검증"""
        pass
    
    @abstractmethod
    def validate_data_types(self, data: pd.DataFrame) -> ValidationResult:
        """데이터 타입 검증"""
        pass
    
    @abstractmethod
    def validate_ranges(self, data: pd.DataFrame, range_specs: Dict[str, tuple]) -> ValidationResult:
        """데이터 범위 검증"""
        pass
    
    @abstractmethod
    def validate_required_fields(self, data: pd.DataFrame, required_fields: List[str]) -> ValidationResult:
        """필수 필드 검증"""
        pass
    
    @abstractmethod
    def validate_custom_rules(self, data: pd.DataFrame, rules: List[str]) -> ValidationResult:
        """커스텀 검증 규칙 적용"""
        pass

class IQCService(ABC):
    """QC 검증 서비스 인터페이스"""
    
    @abstractmethod
    def detect_outliers(self, data: pd.DataFrame, method: str = "zscore", threshold: float = 3.0) -> List[OutlierResult]:
        """이상치 탐지"""
        pass
    
    @abstractmethod
    def check_data_consistency(self, data: pd.DataFrame) -> ValidationResult:
        """데이터 일관성 검사"""
        pass
    
    @abstractmethod
    def check_missing_values(self, data: pd.DataFrame) -> ValidationResult:
        """결측값 검사"""
        pass
    
    @abstractmethod
    def check_duplicate_entries(self, data: pd.DataFrame) -> ValidationResult:
        """중복 항목 검사"""
        pass
    
    @abstractmethod
    def run_full_qc_check(self, data: pd.DataFrame, equipment_type_id: int, config: QCCheckConfig) -> ValidationResult:
        """전체 QC 검사 수행"""
        pass
    
    @abstractmethod
    def generate_qc_report(self, validation_result: ValidationResult, format: str = "html") -> str:
        """QC 리포트 생성"""
        pass
    
    @abstractmethod
    def get_qc_statistics(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """QC 통계 정보 조회"""
        pass

class ValidationServiceInterface(ABC):
    """검증 서비스 인터페이스"""
    
    @abstractmethod
    def validate_input(self, value: Any, validation_rules: Dict[str, Any]) -> bool:
        """입력 값 검증"""
        pass
    
    @abstractmethod
    def validate_file_format(self, file_path: str, expected_format: str) -> bool:
        """파일 형식 검증"""
        pass
    
    @abstractmethod
    def validate_data_structure(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """데이터 구조 검증"""
        pass
    
    @abstractmethod
    def get_validation_errors(self) -> List[str]:
        """검증 오류 목록 반환"""
        pass
    
    @abstractmethod
    def clear_validation_errors(self) -> None:
        """검증 오류 목록 클리어"""
        pass
    
    @abstractmethod
    def validate_parameter_value(self, param_name: str, value: Any, param_type: str) -> bool:
        """파라미터 값 검증"""
        pass
    
    @abstractmethod
    def validate_range(self, value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> bool:
        """범위 검증"""
        pass 