"""
다양한 QC 검증기 구현
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import time
from .base_qc import BaseQCValidator, QCResult, QCIssue, QCSeverity, QCCategory


class StandardQCValidator(BaseQCValidator):
    """표준 QC 검증기"""
    
    def __init__(self):
        super().__init__("Standard QC Validator")
    
    def validate(self, data: pd.DataFrame, **kwargs) -> QCResult:
        """표준 QC 검증을 수행합니다."""
        start_time = time.time()
        result = QCResult(total_items=len(data))
        
        if data.empty:
            result.execution_time = time.time() - start_time
            return result
        
        # 기본 검증 수행
        issues = []
        
        # 1. 필수 컬럼 누락값 검사
        required_columns = ['Module', 'Part', 'Item_Name', 'Value']
        issues.extend(self.check_missing_values(data, required_columns))
        
        # 2. 중복 항목 검사
        key_columns = ['Module', 'Part', 'Item_Name']
        issues.extend(self.check_duplicates(data, key_columns))
        
        # 3. 데이터 타입 검사
        issues.extend(self._check_data_types(data))
        
        # 4. 기본 일관성 검사
        issues.extend(self._check_basic_consistency(data))
        
        # 모든 이슈를 결과에 추가
        for issue in issues:
            result.add_issue(issue)
        
        result.execution_time = time.time() - start_time
        return result
    
    def _check_data_types(self, data: pd.DataFrame) -> List[QCIssue]:
        """데이터 타입 검사"""
        issues = []
        
        # Value 컬럼이 있는 경우 숫자 형식 검사
        if 'Value' in data.columns:
            for _, row in data.iterrows():
                value_str = str(row['Value']).strip()
                if value_str and value_str.lower() not in ['nan', 'null', '']:
                    try:
                        float(value_str)
                    except ValueError:
                        # 숫자가 아닌 값 중에서 의미있는 텍스트인지 확인
                        if len(value_str) > 50:  # 너무 긴 텍스트
                            issue = self.create_issue(
                                category=QCCategory.ACCURACY,
                                severity=QCSeverity.LOW,
                                message=f"값이 너무 깁니다: {value_str[:30]}...",
                                item_row=row,
                                recommended_action="값을 간단히 요약하거나 숫자로 변경하세요."
                            )
                            issues.append(issue)
        
        return issues
    
    def _check_basic_consistency(self, data: pd.DataFrame) -> List[QCIssue]:
        """기본 일관성 검사"""
        issues = []
        
        # Module과 Part 조합의 일관성 검사
        if all(col in data.columns for col in ['Module', 'Part', 'Item_Name']):
            # 같은 Module-Part 조합에서 Item_Name 패턴 검사
            for (module, part), group in data.groupby(['Module', 'Part']):
                if len(group) > 1:
                    item_names = group['Item_Name'].unique()
                    
                    # 매우 유사한 이름들이 있는지 검사 (오타 가능성)
                    for i, name1 in enumerate(item_names):
                        for name2 in item_names[i+1:]:
                            if self._calculate_similarity(str(name1), str(name2)) > 0.8:
                                # 첫 번째 항목에 대해서만 이슈 생성 (중복 방지)
                                first_row = group[group['Item_Name'] == name1].iloc[0]
                                issue = self.create_issue(
                                    category=QCCategory.CONSISTENCY,
                                    severity=QCSeverity.LOW,
                                    message=f"유사한 항목명이 발견되었습니다: '{name1}' vs '{name2}'",
                                    item_row=first_row,
                                    recommended_action="항목명을 통일하거나 의도된 차이인지 확인하세요."
                                )
                                issues.append(issue)
        
        return issues
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """두 문자열의 유사도 계산 (간단한 Levenshtein 기반)"""
        if len(str1) == 0 or len(str2) == 0:
            return 0.0
        
        # 간단한 유사도 계산
        max_len = max(len(str1), len(str2))
        if str1 == str2:
            return 1.0
        
        # 공통 부분 문자열 길이 계산
        common_length = 0
        min_len = min(len(str1), len(str2))
        
        for i in range(min_len):
            if str1[i] == str2[i]:
                common_length += 1
            else:
                break
        
        return common_length / max_len


class EnhancedQCValidator(BaseQCValidator):
    """향상된 QC 검증기 (성능 파라미터 중심)"""
    
    def __init__(self, db_schema=None):
        super().__init__("Enhanced QC Validator")
        self.db_schema = db_schema
        
        # 향상된 심각도 가중치
        self.severity_weights = {
            QCSeverity.LOW: 0.5,
            QCSeverity.MEDIUM: 2.0,
            QCSeverity.HIGH: 5.0,
            QCSeverity.CRITICAL: 10.0
        }
    
    def validate(self, data: pd.DataFrame, **kwargs) -> QCResult:
        """향상된 QC 검증을 수행합니다."""
        start_time = time.time()
        result = QCResult(total_items=len(data))
        
        if data.empty:
            result.execution_time = time.time() - start_time
            return result
        
        # 표준 검증 먼저 수행
        standard_validator = StandardQCValidator()
        standard_result = standard_validator.validate(data, **kwargs)
        
        # 표준 검증 이슈들 추가
        for issue in standard_result.issues:
            result.add_issue(issue)
        
        # 향상된 검증 수행
        issues = []
        
        # 1. 성능 파라미터 우선 검사
        issues.extend(self._check_performance_parameters(data, kwargs.get('equipment_type')))
        
        # 2. 통계적 이상값 검사
        issues.extend(self._check_statistical_outliers(data))
        
        # 3. DB와의 일관성 검사 (DB가 있는 경우)
        if self.db_schema and kwargs.get('equipment_type'):
            issues.extend(self._check_db_consistency(data, kwargs.get('equipment_type')))
        
        # 4. 고급 명명 규칙 검사
        issues.extend(self._check_advanced_naming(data))
        
        # 5. 값 분포 분석
        issues.extend(self._check_value_distribution(data))
        
        # 모든 이슈를 결과에 추가
        for issue in issues:
            result.add_issue(issue)
        
        # 카테고리별 점수 계산
        result.category_scores = self._calculate_category_scores(result)
        
        result.execution_time = time.time() - start_time
        return result
    
    def _check_performance_parameters(self, data: pd.DataFrame, equipment_type: str = None) -> List[QCIssue]:
        """성능 파라미터 우선 검사"""
        issues = []
        
        if not self.db_schema or not equipment_type:
            return issues
        
        try:
            # DB에서 성능 파라미터 목록 가져오기
            db_values = self.db_schema.get_default_values_by_type_name(equipment_type)
            performance_params = [
                (row['module'], row['part'], row['item_name']) 
                for row in db_values 
                if row.get('is_performance', False)
            ]
            
            # 성능 파라미터가 누락되었는지 확인
            for module, part, item_name in performance_params:
                matching_rows = data[
                    (data['Module'] == module) & 
                    (data['Part'] == part) & 
                    (data['Item_Name'] == item_name)
                ]
                
                if matching_rows.empty:
                    # 가상의 행 생성 (누락된 파라미터 표시용)
                    virtual_row = pd.Series({
                        'Module': module,
                        'Part': part,
                        'Item_Name': item_name,
                        'Value': 'MISSING'
                    })
                    
                    issue = self.create_issue(
                        category=QCCategory.PERFORMANCE,
                        severity=QCSeverity.CRITICAL,
                        message=f"중요 성능 파라미터가 누락되었습니다: {module}.{part}.{item_name}",
                        item_row=virtual_row,
                        recommended_action="성능 파라미터를 추가하세요."
                    )
                    issues.append(issue)
        
        except Exception as e:
            # DB 연결 실패 등의 경우 - 심각하지 않은 이슈로 처리
            pass
        
        return issues
    
    def _check_statistical_outliers(self, data: pd.DataFrame) -> List[QCIssue]:
        """통계적 이상값 검사"""
        issues = []
        
        if 'Value' not in data.columns:
            return issues
        
        # 숫자 값만 추출
        numeric_data = []
        numeric_rows = []
        
        for _, row in data.iterrows():
            try:
                value = float(row['Value'])
                numeric_data.append(value)
                numeric_rows.append(row)
            except (ValueError, TypeError):
                continue
        
        if len(numeric_data) < 10:  # 충분한 데이터가 없으면 통계 분석 스킵
            return issues
        
        # IQR 방법으로 이상값 검출
        q1 = np.percentile(numeric_data, 25)
        q3 = np.percentile(numeric_data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        for i, (value, row) in enumerate(zip(numeric_data, numeric_rows)):
            if value < lower_bound or value > upper_bound:
                # 극단적 이상값인지 확인 (3 * IQR)
                extreme_lower = q1 - 3 * iqr
                extreme_upper = q3 + 3 * iqr
                
                if value < extreme_lower or value > extreme_upper:
                    severity = QCSeverity.HIGH
                    message = f"극단적 이상값 발견: {value} (정상 범위: {lower_bound:.2f} ~ {upper_bound:.2f})"
                else:
                    severity = QCSeverity.MEDIUM
                    message = f"이상값 발견: {value} (정상 범위: {lower_bound:.2f} ~ {upper_bound:.2f})"
                
                issue = self.create_issue(
                    category=QCCategory.ACCURACY,
                    severity=severity,
                    message=message,
                    item_row=row,
                    recommended_action="값의 정확성을 확인하고 필요시 수정하세요."
                )
                issues.append(issue)
        
        return issues
    
    def _check_db_consistency(self, data: pd.DataFrame, equipment_type: str) -> List[QCIssue]:
        """DB와의 일관성 검사"""
        issues = []
        
        try:
            db_values = self.db_schema.get_default_values_by_type_name(equipment_type)
            db_dict = {}
            
            for row in db_values:
                key = (row['module'], row['part'], row['item_name'])
                db_dict[key] = row
            
            # 데이터의 각 항목을 DB와 비교
            for _, data_row in data.iterrows():
                key = (data_row['Module'], data_row['Part'], data_row['Item_Name'])
                
                if key in db_dict:
                    db_row = db_dict[key]
                    
                    # 값 비교
                    try:
                        data_value = float(data_row['Value'])
                        db_value = float(db_row['default_value'])
                        
                        # 허용 오차 계산 (DB 값의 5% 또는 최소 0.1)
                        tolerance = max(abs(db_value * 0.05), 0.1)
                        
                        if abs(data_value - db_value) > tolerance:
                            confidence = db_row.get('confidence_score', 0)
                            
                            if confidence > 80:  # 높은 신뢰도의 DB 값과 차이가 큰 경우
                                severity = QCSeverity.MEDIUM
                                message = f"DB 기본값과 차이: {data_value} vs {db_value} (신뢰도: {confidence}%)"
                            else:
                                severity = QCSeverity.LOW
                                message = f"DB 기본값과 차이: {data_value} vs {db_value} (낮은 신뢰도: {confidence}%)"
                            
                            issue = self.create_issue(
                                category=QCCategory.CONSISTENCY,
                                severity=severity,
                                message=message,
                                item_row=data_row,
                                recommended_action="값의 정확성을 확인하고 DB 업데이트를 고려하세요."
                            )
                            issues.append(issue)
                    
                    except (ValueError, TypeError):
                        # 숫자가 아닌 값인 경우
                        if str(data_row['Value']).strip() != str(db_row['default_value']).strip():
                            issue = self.create_issue(
                                category=QCCategory.CONSISTENCY,
                                severity=QCSeverity.LOW,
                                message=f"DB 값과 다름: '{data_row['Value']}' vs '{db_row['default_value']}'",
                                item_row=data_row,
                                recommended_action="값을 확인하고 필요시 수정하세요."
                            )
                            issues.append(issue)
        
        except Exception as e:
            # DB 관련 오류는 조용히 처리
            pass
        
        return issues
    
    def _check_advanced_naming(self, data: pd.DataFrame) -> List[QCIssue]:
        """고급 명명 규칙 검사"""
        issues = []
        
        # 일반적인 명명 규칙 패턴들
        patterns = {
            'Module': [r'^[A-Z][A-Z0-9_]*$', r'^[a-zA-Z][a-zA-Z0-9_]*$'],  # 영문자로 시작, 영숫자와 언더스코어
            'Part': [r'^[A-Z][A-Z0-9_]*$', r'^[a-zA-Z][a-zA-Z0-9_]*$'],
            'Item_Name': [r'^[A-Za-z][A-Za-z0-9_.-]*$']  # 더 유연한 항목명 패턴
        }
        
        for column, column_patterns in patterns.items():
            if column in data.columns:
                issues.extend(self.check_naming_conventions(data, column, column_patterns))
        
        return issues
    
    def _check_value_distribution(self, data: pd.DataFrame) -> List[QCIssue]:
        """값 분포 분석"""
        issues = []
        
        if 'Value' not in data.columns:
            return issues
        
        # 같은 값이 너무 많이 반복되는지 확인
        value_counts = data['Value'].value_counts()
        total_count = len(data)
        
        for value, count in value_counts.items():
            if count > total_count * 0.5 and total_count > 10:  # 전체의 50% 이상이 같은 값
                # 해당 값을 가진 첫 번째 행을 대표로 사용
                representative_row = data[data['Value'] == value].iloc[0]
                
                issue = self.create_issue(
                    category=QCCategory.CONSISTENCY,
                    severity=QCSeverity.LOW,
                    message=f"값 '{value}'이 과도하게 반복됩니다 ({count}/{total_count})",
                    item_row=representative_row,
                    recommended_action="값의 다양성을 확인하고 기본값 사용이 적절한지 검토하세요."
                )
                issues.append(issue)
        
        return issues
    
    def _calculate_category_scores(self, result: QCResult) -> Dict[str, float]:
        """카테고리별 점수 계산"""
        category_scores = {}
        
        for category in QCCategory:
            category_issues = result.get_issues_by_category(category)
            
            if not category_issues:
                category_scores[category.value] = 100.0
            else:
                # 카테고리별 점수 감점 계산
                total_deduction = sum(issue.score_impact for issue in category_issues)
                category_scores[category.value] = max(0, 100 - total_deduction)
        
        return category_scores