"""
통합 QC 검수 관리자
기본 QC와 향상된 QC 기능을 통합하여 효율적인 검수 시스템 제공
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from datetime import datetime

class QCMode(Enum):
    """QC 검수 모드"""
    BASIC = "기본"
    ADVANCED = "고급"
    AUTO = "자동"

class SeverityLevel(Enum):
    """심각도 레벨"""
    HIGH = "높음"
    MEDIUM = "중간"
    LOW = "낮음"
    INFO = "정보"

@dataclass
class QCIssue:
    """QC 이슈 데이터 클래스"""
    parameter_name: str
    issue_type: str
    description: str
    severity: SeverityLevel
    current_value: Optional[str] = None
    expected_value: Optional[str] = None
    recommendation: Optional[str] = None

@dataclass
class QCResult:
    """QC 검수 결과"""
    total_parameters: int
    passed_count: int
    failed_count: int
    warning_count: int
    issues: List[QCIssue] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def pass_rate(self) -> float:
        """합격률 계산"""
        if self.total_parameters == 0:
            return 0.0
        return (self.passed_count / self.total_parameters) * 100

class QCValidator:
    """기본 QC 검증기"""
    
    def __init__(self, db_schema=None):
        """
        초기화
        
        Args:
            db_schema: 데이터베이스 스키마 객체
        """
        self.db_schema = db_schema
    
    def validate_basic(self, df: pd.DataFrame, equipment_type_id: int) -> List[QCIssue]:
        """
        기본 검증 수행
        
        Args:
            df: 검증할 데이터프레임
            equipment_type_id: 장비 유형 ID
            
        Returns:
            발견된 이슈 리스트
        """
        issues = []
        
        # 1. 필수 값 누락 검사
        issues.extend(self._check_missing_values(df))
        
        # 2. 데이터 타입 검증
        issues.extend(self._check_data_types(df))
        
        # 3. 범위 검증 (Min/Max)
        if self.db_schema:
            issues.extend(self._check_range_validation(df, equipment_type_id))
        
        # 4. 형식 검증
        issues.extend(self._check_format_validation(df))
        
        return issues
    
    def _check_missing_values(self, df: pd.DataFrame) -> List[QCIssue]:
        """누락 값 검사"""
        issues = []
        
        # 필수 컬럼
        required_columns = ['parameter_name', 'default_value']
        
        for col in required_columns:
            if col in df.columns:
                missing_mask = df[col].isna() | (df[col] == '')
                missing_count = missing_mask.sum()
                
                if missing_count > 0:
                    # 누락된 파라미터 이름들
                    if col == 'default_value':
                        missing_params = df[missing_mask]['parameter_name'].tolist()[:5]
                        param_list = ', '.join(missing_params)
                        if missing_count > 5:
                            param_list += f" 외 {missing_count - 5}개"
                    else:
                        param_list = f"{missing_count}개 항목"
                    
                    issues.append(QCIssue(
                        parameter_name=f"[전체] {col}",
                        issue_type="누락값",
                        description=f"{col}에 {missing_count}개의 누락값 발견: {param_list}",
                        severity=SeverityLevel.HIGH if col in required_columns else SeverityLevel.MEDIUM,
                        recommendation=f"{col} 값을 입력하거나 확인하세요"
                    ))
        
        return issues
    
    def _check_data_types(self, df: pd.DataFrame) -> List[QCIssue]:
        """데이터 타입 검증"""
        issues = []
        
        # 숫자여야 하는 컬럼들
        numeric_columns = ['min_spec', 'max_spec', 'confidence_score']
        
        for col in numeric_columns:
            if col in df.columns:
                # 숫자로 변환 시도
                non_numeric = []
                for idx, value in df[col].items():
                    if pd.notna(value) and value != '':
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            non_numeric.append(df.loc[idx, 'parameter_name'])
                
                if non_numeric:
                    issues.append(QCIssue(
                        parameter_name=f"[타입] {col}",
                        issue_type="타입오류",
                        description=f"{col}에 숫자가 아닌 값 {len(non_numeric)}개 발견",
                        severity=SeverityLevel.MEDIUM,
                        current_value=f"영향받는 파라미터: {', '.join(non_numeric[:3])}",
                        recommendation="숫자 형식으로 변환하세요"
                    ))
        
        return issues
    
    def _check_range_validation(self, df: pd.DataFrame, equipment_type_id: int) -> List[QCIssue]:
        """범위 검증 (Min/Max 스펙)"""
        issues = []
        
        if 'default_value' not in df.columns:
            return issues
        
        # Mother DB에서 스펙 정보 가져오기
        specs = self._get_specs_from_db(equipment_type_id)
        
        for idx, row in df.iterrows():
            param_name = row.get('parameter_name', '')
            default_value = row.get('default_value', '')
            
            if param_name in specs:
                spec = specs[param_name]
                
                try:
                    value = float(default_value)
                    
                    # Min 스펙 검사
                    if spec['min_spec'] is not None:
                        min_val = float(spec['min_spec'])
                        if value < min_val:
                            issues.append(QCIssue(
                                parameter_name=param_name,
                                issue_type="범위이탈",
                                description=f"값이 최소 스펙보다 작음",
                                severity=SeverityLevel.HIGH,
                                current_value=str(value),
                                expected_value=f">= {min_val}",
                                recommendation=f"값을 {min_val} 이상으로 조정하세요"
                            ))
                    
                    # Max 스펙 검사
                    if spec['max_spec'] is not None:
                        max_val = float(spec['max_spec'])
                        if value > max_val:
                            issues.append(QCIssue(
                                parameter_name=param_name,
                                issue_type="범위이탈",
                                description=f"값이 최대 스펙보다 큼",
                                severity=SeverityLevel.HIGH,
                                current_value=str(value),
                                expected_value=f"<= {max_val}",
                                recommendation=f"값을 {max_val} 이하로 조정하세요"
                            ))
                
                except (ValueError, TypeError):
                    # 숫자 변환 실패 (이미 타입 검사에서 처리됨)
                    pass
        
        return issues
    
    def _check_format_validation(self, df: pd.DataFrame) -> List[QCIssue]:
        """형식 검증"""
        issues = []
        
        # 파라미터 이름 형식 검사
        if 'parameter_name' in df.columns:
            invalid_params = []
            for param in df['parameter_name'].unique():
                if pd.notna(param):
                    # 특수문자 검사 (일부 허용)
                    if not all(c.isalnum() or c in '_-.:/ ' for c in str(param)):
                        invalid_params.append(param)
            
            if invalid_params:
                issues.append(QCIssue(
                    parameter_name="[형식] parameter_name",
                    issue_type="형식오류",
                    description=f"파라미터 이름에 허용되지 않은 문자 포함 ({len(invalid_params)}개)",
                    severity=SeverityLevel.LOW,
                    current_value=f"예: {invalid_params[0] if invalid_params else ''}",
                    recommendation="영문, 숫자, 밑줄, 하이픈만 사용하세요"
                ))
        
        return issues
    
    def _get_specs_from_db(self, equipment_type_id: int) -> Dict:
        """DB에서 스펙 정보 가져오기"""
        specs = {}
        
        if not self.db_schema:
            return specs
        
        try:
            conn = sqlite3.connect(self.db_schema.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT parameter_name, min_spec, max_spec
                FROM Default_DB_Values
                WHERE equipment_type_id = ?
            ''', (equipment_type_id,))
            
            for row in cursor.fetchall():
                specs[row[0]] = {
                    'min_spec': row[1],
                    'max_spec': row[2]
                }
            
            conn.close()
        except Exception as e:
            print(f"스펙 정보 조회 중 오류: {e}")
        
        return specs

class AdvancedQCAnalyzer:
    """향상된 QC 분석기"""
    
    def __init__(self):
        """초기화"""
        self.statistical_threshold = 2.0  # 표준편차 임계값
    
    def analyze_advanced(self, df: pd.DataFrame, reference_df: Optional[pd.DataFrame] = None) -> List[QCIssue]:
        """
        고급 분석 수행
        
        Args:
            df: 분석할 데이터프레임
            reference_df: 참조 데이터프레임 (Mother DB)
            
        Returns:
            발견된 이슈 리스트
        """
        issues = []
        
        # 1. 통계적 이상치 검출
        issues.extend(self._detect_statistical_outliers(df))
        
        # 2. 패턴 분석
        issues.extend(self._analyze_patterns(df))
        
        # 3. 일관성 검사
        if reference_df is not None:
            issues.extend(self._check_consistency(df, reference_df))
        
        # 4. 상관관계 분석
        issues.extend(self._analyze_correlations(df))
        
        return issues
    
    def _detect_statistical_outliers(self, df: pd.DataFrame) -> List[QCIssue]:
        """통계적 이상치 검출"""
        issues = []
        
        # 숫자 컬럼만 선택
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col in ['confidence_score', 'occurrence_count']:
                data = pd.to_numeric(df[col], errors='coerce')
                data = data.dropna()
                
                if len(data) > 3:  # 최소 데이터 수
                    mean = data.mean()
                    std = data.std()
                    
                    if std > 0:
                        # Z-score 계산
                        z_scores = np.abs((data - mean) / std)
                        outliers = data[z_scores > self.statistical_threshold]
                        
                        if len(outliers) > 0:
                            outlier_params = df.loc[outliers.index, 'parameter_name'].tolist()[:3]
                            
                            issues.append(QCIssue(
                                parameter_name=f"[통계] {col}",
                                issue_type="통계적이상치",
                                description=f"{col}에서 {len(outliers)}개의 이상치 검출",
                                severity=SeverityLevel.MEDIUM,
                                current_value=f"평균: {mean:.2f}, 표준편차: {std:.2f}",
                                expected_value=f"Z-score < {self.statistical_threshold}",
                                recommendation=f"이상치 파라미터 검토: {', '.join(outlier_params)}"
                            ))
        
        return issues
    
    def _analyze_patterns(self, df: pd.DataFrame) -> List[QCIssue]:
        """패턴 분석"""
        issues = []
        
        # 중복 패턴 검사
        if 'parameter_name' in df.columns and 'default_value' in df.columns:
            duplicates = df.groupby(['parameter_name', 'default_value']).size()
            high_duplicates = duplicates[duplicates > 1]
            
            if len(high_duplicates) > 0:
                issues.append(QCIssue(
                    parameter_name="[패턴] 중복",
                    issue_type="중복패턴",
                    description=f"{len(high_duplicates)}개의 중복 파라미터-값 조합 발견",
                    severity=SeverityLevel.INFO,
                    recommendation="중복 항목을 검토하고 필요시 통합하세요"
                ))
        
        # 누락 패턴 검사
        if 'parameter_name' in df.columns:
            # 연속된 번호 패턴 검사 (예: PARAM_001, PARAM_002, ...)
            params = df['parameter_name'].unique()
            numbered_params = [p for p in params if any(c.isdigit() for c in str(p))]
            
            if numbered_params:
                # 번호 추출 및 누락 검사
                import re
                numbers = []
                for param in numbered_params:
                    matches = re.findall(r'\d+', str(param))
                    if matches:
                        numbers.extend([int(m) for m in matches])
                
                if numbers:
                    numbers = sorted(set(numbers))
                    expected = set(range(min(numbers), max(numbers) + 1))
                    missing = expected - set(numbers)
                    
                    if missing:
                        issues.append(QCIssue(
                            parameter_name="[패턴] 누락",
                            issue_type="순서누락",
                            description=f"번호 시퀀스에서 {len(missing)}개 누락",
                            severity=SeverityLevel.LOW,
                            current_value=f"누락된 번호: {sorted(missing)[:5]}",
                            recommendation="누락된 파라미터를 확인하세요"
                        ))
        
        return issues
    
    def _check_consistency(self, df: pd.DataFrame, reference_df: pd.DataFrame) -> List[QCIssue]:
        """일관성 검사"""
        issues = []
        
        if 'parameter_name' not in df.columns or 'parameter_name' not in reference_df.columns:
            return issues
        
        # 참조 데이터와 비교
        df_params = set(df['parameter_name'].unique())
        ref_params = set(reference_df['parameter_name'].unique())
        
        # 누락된 필수 파라미터
        missing_params = ref_params - df_params
        if missing_params:
            issues.append(QCIssue(
                parameter_name="[일관성] 누락",
                issue_type="필수항목누락",
                description=f"Mother DB 대비 {len(missing_params)}개 파라미터 누락",
                severity=SeverityLevel.HIGH,
                current_value=f"누락: {list(missing_params)[:5]}",
                recommendation="누락된 필수 파라미터를 추가하세요"
            ))
        
        # 추가된 파라미터
        extra_params = df_params - ref_params
        if extra_params:
            issues.append(QCIssue(
                parameter_name="[일관성] 추가",
                issue_type="미등록항목",
                description=f"Mother DB에 없는 {len(extra_params)}개 파라미터 발견",
                severity=SeverityLevel.MEDIUM,
                current_value=f"추가: {list(extra_params)[:5]}",
                recommendation="새 파라미터를 Mother DB에 등록하거나 제거하세요"
            ))
        
        return issues
    
    def _analyze_correlations(self, df: pd.DataFrame) -> List[QCIssue]:
        """상관관계 분석"""
        issues = []
        
        # 숫자 데이터만 선택
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) >= 2:
            # 상관관계 계산
            corr_matrix = numeric_df.corr()
            
            # 높은 상관관계 찾기 (자기 자신 제외)
            high_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.9:  # 90% 이상 상관관계
                        high_corr.append((
                            corr_matrix.columns[i],
                            corr_matrix.columns[j],
                            corr_value
                        ))
            
            if high_corr:
                issues.append(QCIssue(
                    parameter_name="[상관관계]",
                    issue_type="높은상관관계",
                    description=f"{len(high_corr)}개의 높은 상관관계 발견",
                    severity=SeverityLevel.INFO,
                    current_value=f"예: {high_corr[0][0]} ↔ {high_corr[0][1]} ({high_corr[0][2]:.2f})",
                    recommendation="관련 파라미터들의 독립성을 검토하세요"
                ))
        
        return issues

class UnifiedQCSystem:
    """통합 QC 시스템"""
    
    def __init__(self, db_schema=None):
        """
        초기화
        
        Args:
            db_schema: 데이터베이스 스키마 객체
        """
        self.db_schema = db_schema
        self.basic_validator = QCValidator(db_schema)
        self.advanced_analyzer = AdvancedQCAnalyzer()
        self.templates = {}
    
    def perform_qc(self, 
                   df: pd.DataFrame, 
                   equipment_type_id: int,
                   mode: QCMode = QCMode.AUTO,
                   reference_df: Optional[pd.DataFrame] = None) -> QCResult:
        """
        통합 QC 검수 수행
        
        Args:
            df: 검수할 데이터프레임
            equipment_type_id: 장비 유형 ID
            mode: QC 모드
            reference_df: 참조 데이터프레임 (Mother DB)
            
        Returns:
            QC 검수 결과
        """
        # 모드 자동 선택
        if mode == QCMode.AUTO:
            mode = QCMode.ADVANCED if len(df) > 100 else QCMode.BASIC
        
        issues = []
        
        # 기본 검증 (항상 수행)
        basic_issues = self.basic_validator.validate_basic(df, equipment_type_id)
        issues.extend(basic_issues)
        
        # 고급 분석 (선택적)
        if mode == QCMode.ADVANCED:
            advanced_issues = self.advanced_analyzer.analyze_advanced(df, reference_df)
            issues.extend(advanced_issues)
        
        # 결과 집계
        result = self._aggregate_results(df, issues)
        
        return result
    
    def _aggregate_results(self, df: pd.DataFrame, issues: List[QCIssue]) -> QCResult:
        """결과 집계"""
        total_parameters = len(df) if not df.empty else 0
        
        # 심각도별 카운트
        high_count = sum(1 for issue in issues if issue.severity == SeverityLevel.HIGH)
        medium_count = sum(1 for issue in issues if issue.severity == SeverityLevel.MEDIUM)
        low_count = sum(1 for issue in issues if issue.severity == SeverityLevel.LOW)
        
        # Pass/Fail 판정
        failed_count = high_count
        warning_count = medium_count + low_count
        passed_count = max(0, total_parameters - failed_count)
        
        # 통계 정보
        statistics = {
            'severity_distribution': {
                'high': high_count,
                'medium': medium_count,
                'low': low_count
            },
            'issue_types': {}
        }
        
        # 이슈 타입별 집계
        for issue in issues:
            issue_type = issue.issue_type
            if issue_type not in statistics['issue_types']:
                statistics['issue_types'][issue_type] = 0
            statistics['issue_types'][issue_type] += 1
        
        return QCResult(
            total_parameters=total_parameters,
            passed_count=passed_count,
            failed_count=failed_count,
            warning_count=warning_count,
            issues=issues,
            statistics=statistics
        )
    
    def create_template(self, name: str, criteria: Dict) -> bool:
        """
        QC 템플릿 생성
        
        Args:
            name: 템플릿 이름
            criteria: 검수 기준
            
        Returns:
            생성 성공 여부
        """
        try:
            self.templates[name] = {
                'criteria': criteria,
                'created_at': datetime.now()
            }
            return True
        except Exception as e:
            print(f"템플릿 생성 실패: {e}")
            return False
    
    def apply_template(self, df: pd.DataFrame, template_name: str) -> QCResult:
        """템플릿 적용"""
        if template_name not in self.templates:
            raise ValueError(f"템플릿 '{template_name}'을 찾을 수 없습니다")
        
        template = self.templates[template_name]
        # 템플릿 기준에 따라 검수 수행
        # (구현 생략 - 템플릿 구조에 따라 구현)
        
        return QCResult(
            total_parameters=len(df),
            passed_count=0,
            failed_count=0,
            warning_count=0
        )
    
    def export_report(self, result: QCResult, output_path: str, format: str = 'html') -> bool:
        """
        QC 결과 리포트 내보내기
        
        Args:
            result: QC 결과
            output_path: 출력 경로
            format: 출력 형식 (html, excel, pdf)
            
        Returns:
            내보내기 성공 여부
        """
        try:
            if format == 'html':
                return self._export_html_report(result, output_path)
            elif format == 'excel':
                return self._export_excel_report(result, output_path)
            else:
                print(f"지원하지 않는 형식: {format}")
                return False
        except Exception as e:
            print(f"리포트 내보내기 실패: {e}")
            return False
    
    def _export_html_report(self, result: QCResult, output_path: str) -> bool:
        """HTML 리포트 생성"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>QC 검수 결과 리포트</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .pass {{ color: green; }}
                .fail {{ color: red; }}
                .warning {{ color: orange; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background: #4CAF50; color: white; }}
                .high {{ background: #ffebee; }}
                .medium {{ background: #fff3e0; }}
                .low {{ background: #f1f8e9; }}
            </style>
        </head>
        <body>
            <h1>QC 검수 결과 리포트</h1>
            <div class="summary">
                <h2>요약</h2>
                <p>검수 일시: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>전체 파라미터: {result.total_parameters}</p>
                <p class="pass">합격: {result.passed_count} ({result.pass_rate:.1f}%)</p>
                <p class="fail">불합격: {result.failed_count}</p>
                <p class="warning">경고: {result.warning_count}</p>
            </div>
            
            <h2>발견된 이슈</h2>
            <table>
                <tr>
                    <th>파라미터</th>
                    <th>이슈 타입</th>
                    <th>설명</th>
                    <th>심각도</th>
                    <th>권장사항</th>
                </tr>
        """
        
        for issue in result.issues:
            severity_class = issue.severity.value.lower()
            html_content += f"""
                <tr class="{severity_class}">
                    <td>{issue.parameter_name}</td>
                    <td>{issue.issue_type}</td>
                    <td>{issue.description}</td>
                    <td>{issue.severity.value}</td>
                    <td>{issue.recommendation or '-'}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return True
    
    def _export_excel_report(self, result: QCResult, output_path: str) -> bool:
        """Excel 리포트 생성"""
        # 이슈를 데이터프레임으로 변환
        issues_data = []
        for issue in result.issues:
            issues_data.append({
                '파라미터': issue.parameter_name,
                '이슈타입': issue.issue_type,
                '설명': issue.description,
                '심각도': issue.severity.value,
                '현재값': issue.current_value,
                '기대값': issue.expected_value,
                '권장사항': issue.recommendation
            })
        
        issues_df = pd.DataFrame(issues_data)
        
        # 요약 정보
        summary_data = {
            '항목': ['검수일시', '전체파라미터', '합격', '불합격', '경고', '합격률'],
            '값': [
                result.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                result.total_parameters,
                result.passed_count,
                result.failed_count,
                result.warning_count,
                f"{result.pass_rate:.1f}%"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Excel 파일로 저장
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='요약', index=False)
            issues_df.to_excel(writer, sheet_name='이슈목록', index=False)
        
        return True