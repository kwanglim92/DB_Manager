"""
QC 기능의 기본 클래스
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Any, Tuple
from enum import Enum


class QCSeverity(Enum):
    """QC 검사 심각도"""
    LOW = "Low"
    MEDIUM = "Medium" 
    HIGH = "High"
    CRITICAL = "Critical"


class QCCategory(Enum):
    """QC 검사 카테고리"""
    PERFORMANCE = "Performance"
    CONSISTENCY = "Consistency"
    COMPLETENESS = "Completeness"
    ACCURACY = "Accuracy"
    NAMING = "Naming"


class QCIssue:
    """QC 이슈를 나타내는 클래스"""
    
    def __init__(self, 
                 category: QCCategory,
                 severity: QCSeverity, 
                 message: str,
                 item_info: Dict[str, Any] = None,
                 recommended_action: str = "",
                 score_impact: float = 0.0):
        self.category = category
        self.severity = severity
        self.message = message
        self.item_info = item_info or {}
        self.recommended_action = recommended_action
        self.score_impact = score_impact
        self.timestamp = pd.Timestamp.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """이슈를 딕셔너리로 변환"""
        return {
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'module': self.item_info.get('Module', ''),
            'part': self.item_info.get('Part', ''),
            'item_name': self.item_info.get('Item_Name', ''),
            'value': self.item_info.get('Value', ''),
            'recommended_action': self.recommended_action,
            'score_impact': self.score_impact,
            'timestamp': self.timestamp
        }


class QCResult:
    """QC 검사 결과를 나타내는 클래스"""
    
    def __init__(self, total_items: int = 0):
        self.total_items = total_items
        self.issues: List[QCIssue] = []
        self.overall_score: float = 100.0
        self.category_scores: Dict[str, float] = {}
        self.execution_time: float = 0.0
        self.timestamp = pd.Timestamp.now()
    
    def add_issue(self, issue: QCIssue):
        """이슈 추가"""
        self.issues.append(issue)
        self.overall_score = max(0, self.overall_score - issue.score_impact)
    
    def get_issues_by_severity(self, severity: QCSeverity) -> List[QCIssue]:
        """심각도별 이슈 반환"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_category(self, category: QCCategory) -> List[QCIssue]:
        """카테고리별 이슈 반환"""
        return [issue for issue in self.issues if issue.category == category]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """요약 통계 반환"""
        severity_counts = {}
        for severity in QCSeverity:
            severity_counts[severity.value] = len(self.get_issues_by_severity(severity))
        
        category_counts = {}
        for category in QCCategory:
            category_counts[category.value] = len(self.get_issues_by_category(category))
        
        return {
            'total_items': self.total_items,
            'total_issues': len(self.issues),
            'overall_score': round(self.overall_score, 1),
            'severity_distribution': severity_counts,
            'category_distribution': category_counts,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """이슈들을 DataFrame으로 변환"""
        if not self.issues:
            return pd.DataFrame()
        
        return pd.DataFrame([issue.to_dict() for issue in self.issues])


class BaseQCValidator(ABC):
    """QC 검증의 기본 추상 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.severity_weights = {
            QCSeverity.LOW: 1.0,
            QCSeverity.MEDIUM: 3.0,
            QCSeverity.HIGH: 7.0,
            QCSeverity.CRITICAL: 15.0
        }
    
    @abstractmethod
    def validate(self, data: pd.DataFrame, **kwargs) -> QCResult:
        """데이터 검증을 수행합니다."""
        pass
    
    def create_issue(self, 
                    category: QCCategory,
                    severity: QCSeverity,
                    message: str,
                    item_row: pd.Series = None,
                    recommended_action: str = "") -> QCIssue:
        """QC 이슈를 생성합니다."""
        item_info = {}
        if item_row is not None:
            item_info = {
                'Module': item_row.get('Module', ''),
                'Part': item_row.get('Part', ''),
                'Item_Name': item_row.get('Item_Name', ''),
                'Value': item_row.get('Value', '')
            }
        
        score_impact = self.severity_weights.get(severity, 1.0)
        
        return QCIssue(
            category=category,
            severity=severity,
            message=message,
            item_info=item_info,
            recommended_action=recommended_action,
            score_impact=score_impact
        )
    
    def check_missing_values(self, data: pd.DataFrame, required_columns: List[str]) -> List[QCIssue]:
        """필수 컬럼의 누락값을 검사합니다."""
        issues = []
        
        for column in required_columns:
            if column in data.columns:
                missing_mask = data[column].isna() | (data[column].astype(str).str.strip() == '')
                missing_rows = data[missing_mask]
                
                for _, row in missing_rows.iterrows():
                    issue = self.create_issue(
                        category=QCCategory.COMPLETENESS,
                        severity=QCSeverity.HIGH if column in ['Module', 'Part', 'Item_Name'] else QCSeverity.MEDIUM,
                        message=f"필수 컬럼 '{column}'의 값이 누락되었습니다.",
                        item_row=row,
                        recommended_action=f"{column} 값을 입력하세요."
                    )
                    issues.append(issue)
        
        return issues
    
    def check_duplicates(self, data: pd.DataFrame, key_columns: List[str]) -> List[QCIssue]:
        """중복 항목을 검사합니다."""
        issues = []
        
        if all(col in data.columns for col in key_columns):
            # 중복 검사
            duplicated_mask = data.duplicated(subset=key_columns, keep=False)
            duplicated_rows = data[duplicated_mask]
            
            # 중복 그룹별로 처리
            for key_values, group in duplicated_rows.groupby(key_columns):
                if len(group) > 1:
                    key_str = ', '.join(f"{col}={val}" for col, val in zip(key_columns, key_values))
                    
                    for _, row in group.iterrows():
                        issue = self.create_issue(
                            category=QCCategory.CONSISTENCY,
                            severity=QCSeverity.HIGH,
                            message=f"중복된 항목이 발견되었습니다: {key_str}",
                            item_row=row,
                            recommended_action="중복 항목을 제거하거나 병합하세요."
                        )
                        issues.append(issue)
        
        return issues
    
    def check_naming_conventions(self, data: pd.DataFrame, column: str, patterns: List[str]) -> List[QCIssue]:
        """명명 규칙을 검사합니다."""
        issues = []
        
        if column in data.columns:
            import re
            
            for _, row in data.iterrows():
                value = str(row[column]).strip()
                if value:
                    # 패턴 중 하나라도 일치하는지 확인
                    matches_pattern = any(re.match(pattern, value) for pattern in patterns)
                    
                    if not matches_pattern:
                        issue = self.create_issue(
                            category=QCCategory.NAMING,
                            severity=QCSeverity.LOW,
                            message=f"명명 규칙에 맞지 않습니다: {value}",
                            item_row=row,
                            recommended_action=f"명명 규칙에 맞게 수정하세요. 패턴: {', '.join(patterns)}"
                        )
                        issues.append(issue)
        
        return issues
    
    def check_value_ranges(self, data: pd.DataFrame, column: str, min_val: float = None, max_val: float = None) -> List[QCIssue]:
        """값 범위를 검사합니다."""
        issues = []
        
        if column in data.columns:
            for _, row in data.iterrows():
                try:
                    value = float(row[column])
                    
                    if min_val is not None and value < min_val:
                        issue = self.create_issue(
                            category=QCCategory.ACCURACY,
                            severity=QCSeverity.MEDIUM,
                            message=f"값이 최소 범위보다 작습니다: {value} < {min_val}",
                            item_row=row,
                            recommended_action=f"값을 {min_val} 이상으로 수정하세요."
                        )
                        issues.append(issue)
                    
                    if max_val is not None and value > max_val:
                        issue = self.create_issue(
                            category=QCCategory.ACCURACY,
                            severity=QCSeverity.MEDIUM,
                            message=f"값이 최대 범위보다 큽니다: {value} > {max_val}",
                            item_row=row,
                            recommended_action=f"값을 {max_val} 이하로 수정하세요."
                        )
                        issues.append(issue)
                        
                except (ValueError, TypeError):
                    # 숫자로 변환할 수 없는 경우
                    issue = self.create_issue(
                        category=QCCategory.ACCURACY,
                        severity=QCSeverity.MEDIUM,
                        message=f"숫자 형식이 아닙니다: {row[column]}",
                        item_row=row,
                        recommended_action="올바른 숫자 형식으로 수정하세요."
                    )
                    issues.append(issue)
        
        return issues
    
    def set_enabled(self, enabled: bool):
        """검증기 활성화/비활성화"""
        self.enabled = enabled
    
    def is_enabled(self) -> bool:
        """검증기 활성화 상태 반환"""
        return self.enabled