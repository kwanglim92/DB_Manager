"""
데이터 검증 관련 헬퍼 함수들
"""

import re
import pandas as pd
from typing import Any, List, Dict, Optional, Tuple, Union
import hashlib
import os


class ValidationHelpers:
    """데이터 검증을 위한 헬퍼 클래스"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        이메일 주소의 유효성을 검사합니다.
        
        Args:
            email: 검사할 이메일 주소
            
        Returns:
            bool: 유효성 여부
        """
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_number(value: Any, allow_negative: bool = True, 
                       allow_decimal: bool = True) -> bool:
        """
        숫자의 유효성을 검사합니다.
        
        Args:
            value: 검사할 값
            allow_negative: 음수 허용 여부
            allow_decimal: 소수점 허용 여부
            
        Returns:
            bool: 유효성 여부
        """
        if value is None or pd.isna(value):
            return False
        
        try:
            num_value = float(value)
            
            # 음수 검사
            if not allow_negative and num_value < 0:
                return False
            
            # 소수점 검사
            if not allow_decimal and num_value != int(num_value):
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_range(value: Any, min_val: Optional[float] = None, 
                      max_val: Optional[float] = None) -> bool:
        """
        값이 지정된 범위 내에 있는지 검사합니다.
        
        Args:
            value: 검사할 값
            min_val: 최소값 (None이면 제한 없음)
            max_val: 최대값 (None이면 제한 없음)
            
        Returns:
            bool: 범위 내 여부
        """
        if not ValidationHelpers.is_valid_number(value):
            return False
        
        try:
            num_value = float(value)
            
            if min_val is not None and num_value < min_val:
                return False
            
            if max_val is not None and num_value > max_val:
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_pattern(value: str, pattern: str) -> bool:
        """
        값이 정규표현식 패턴과 일치하는지 검사합니다.
        
        Args:
            value: 검사할 값
            pattern: 정규표현식 패턴
            
        Returns:
            bool: 패턴 일치 여부
        """
        if not value:
            return False
        
        try:
            return bool(re.match(pattern, str(value)))
        except re.error:
            return False
    
    @staticmethod
    def is_not_empty(value: Any) -> bool:
        """
        값이 비어있지 않은지 검사합니다.
        
        Args:
            value: 검사할 값
            
        Returns:
            bool: 비어있지 않음 여부
        """
        if value is None or pd.isna(value):
            return False
        
        if isinstance(value, str):
            return bool(value.strip())
        
        return True
    
    @staticmethod
    def is_unique_in_series(series: pd.Series, value: Any) -> bool:
        """
        Series 내에서 값이 유일한지 검사합니다.
        
        Args:
            series: 검사할 Series
            value: 검사할 값
            
        Returns:
            bool: 유일성 여부
        """
        if value is None or pd.isna(value):
            return False
        
        return (series == value).sum() <= 1
    
    @staticmethod
    def validate_dataframe_columns(df: pd.DataFrame, 
                                 required_columns: List[str]) -> Dict[str, bool]:
        """
        DataFrame의 필수 컬럼 존재 여부를 검사합니다.
        
        Args:
            df: 검사할 DataFrame
            required_columns: 필수 컬럼 리스트
            
        Returns:
            Dict[str, bool]: 컬럼별 존재 여부
        """
        result = {}
        for column in required_columns:
            result[column] = column in df.columns
        return result
    
    @staticmethod
    def validate_dataframe_data(df: pd.DataFrame, 
                               validation_rules: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """
        DataFrame의 데이터를 검증 규칙에 따라 검사합니다.
        
        Args:
            df: 검사할 DataFrame
            validation_rules: 검증 규칙
                {
                    "column_name": {
                        "required": True,
                        "type": "number",
                        "min": 0,
                        "max": 100,
                        "pattern": r"^[A-Z]+$"
                    }
                }
                
        Returns:
            pd.DataFrame: 검증 결과 (각 셀별 True/False)
        """
        result = pd.DataFrame(index=df.index, columns=df.columns, dtype=bool)
        result.fillna(True, inplace=True)  # 기본값은 True (유효)
        
        for column, rules in validation_rules.items():
            if column not in df.columns:
                continue
            
            series = df[column]
            column_result = pd.Series(True, index=series.index)
            
            # 필수 여부 검사
            if rules.get("required", False):
                column_result &= series.apply(ValidationHelpers.is_not_empty)
            
            # 타입 검사
            if "type" in rules:
                type_rule = rules["type"]
                if type_rule == "number":
                    column_result &= series.apply(ValidationHelpers.is_valid_number)
                elif type_rule == "email":
                    column_result &= series.apply(ValidationHelpers.is_valid_email)
            
            # 범위 검사
            if "min" in rules or "max" in rules:
                min_val = rules.get("min")
                max_val = rules.get("max")
                column_result &= series.apply(
                    lambda x: ValidationHelpers.is_valid_range(x, min_val, max_val)
                )
            
            # 패턴 검사
            if "pattern" in rules:
                pattern = rules["pattern"]
                column_result &= series.apply(
                    lambda x: ValidationHelpers.is_valid_pattern(str(x), pattern)
                )
            
            # 유일성 검사
            if rules.get("unique", False):
                column_result &= series.apply(
                    lambda x: ValidationHelpers.is_unique_in_series(series, x)
                )
            
            result[column] = column_result
        
        return result
    
    @staticmethod
    def check_naming_convention(value: str, convention: str) -> bool:
        """
        명명 규칙을 검사합니다.
        
        Args:
            value: 검사할 값
            convention: 명명 규칙 ('camelCase', 'snake_case', 'PascalCase', 'UPPER_CASE')
            
        Returns:
            bool: 명명 규칙 준수 여부
        """
        if not value:
            return False
        
        patterns = {
            'camelCase': r'^[a-z][a-zA-Z0-9]*$',
            'snake_case': r'^[a-z][a-z0-9_]*$',
            'PascalCase': r'^[A-Z][a-zA-Z0-9]*$',
            'UPPER_CASE': r'^[A-Z][A-Z0-9_]*$',
            'kebab-case': r'^[a-z][a-z0-9-]*$'
        }
        
        pattern = patterns.get(convention)
        if not pattern:
            return False
        
        return bool(re.match(pattern, value))
    
    @staticmethod
    def verify_password(password: str, password_hash: str = None) -> bool:
        """
        비밀번호를 검증합니다.
        
        Args:
            password: 입력된 비밀번호
            password_hash: 저장된 해시 (None이면 설정 파일에서 읽음)
            
        Returns:
            bool: 비밀번호 일치 여부
        """
        if not password:
            return False
        
        # 설정 파일에서 해시 읽기 (password_hash가 제공되지 않은 경우)
        if password_hash is None:
            try:
                import json
                config_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                    "config", "settings.json"
                )
                
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    password_hash = settings.get('maint_password_hash', '')
                else:
                    return False
            except Exception:
                return False
        
        # 입력된 비밀번호의 해시 계산
        input_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        return input_hash == password_hash
    
    @staticmethod
    def change_maintenance_password(current_password: str, new_password: str) -> bool:
        """
        유지보수 모드 비밀번호를 변경합니다.
        
        Args:
            current_password: 현재 비밀번호
            new_password: 새 비밀번호
            
        Returns:
            bool: 변경 성공 여부
        """
        # 현재 비밀번호 확인
        if not ValidationHelpers.verify_password(current_password):
            return False
        
        try:
            import json
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "config", "settings.json"
            )
            
            # 설정 파일 읽기
            settings = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # 새 비밀번호 해시 생성
            new_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            settings['maint_password_hash'] = new_hash
            
            # 설정 파일 저장
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"비밀번호 변경 오류: {str(e)}")
            return False
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, str]:
        """
        파일 경로의 유효성을 검사합니다.
        
        Args:
            file_path: 검사할 파일 경로
            
        Returns:
            Tuple[bool, str]: (유효성 여부, 오류 메시지)
        """
        if not file_path:
            return False, "파일 경로가 비어있습니다."
        
        # 위험한 문자 검사
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in file_path for char in dangerous_chars):
            return False, "파일 경로에 허용되지 않는 문자가 포함되어 있습니다."
        
        # 상대 경로 공격 검사
        if '..' in file_path:
            return False, "상위 디렉토리 접근은 허용되지 않습니다."
        
        # 길이 검사
        if len(file_path) > 260:  # Windows 경로 길이 제한
            return False, "파일 경로가 너무 깁니다."
        
        return True, ""
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """
        사용자 입력을 안전하게 정리합니다.
        
        Args:
            input_str: 정리할 입력 문자열
            
        Returns:
            str: 정리된 문자열
        """
        if not input_str:
            return ""
        
        # HTML 태그 제거
        cleaned = re.sub(r'<[^>]+>', '', input_str)
        
        # 스크립트 관련 키워드 제거
        dangerous_patterns = [
            r'javascript:', r'vbscript:', r'onload=', r'onerror=',
            r'<script', r'</script>', r'eval\\(', r'document\\.'
        ]
        
        for pattern in dangerous_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # 여러 공백을 단일 공백으로
        cleaned = re.sub(r'\\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    @staticmethod
    def validate_column_data_types(df: pd.DataFrame, 
                                  expected_types: Dict[str, str]) -> Dict[str, bool]:
        """
        DataFrame 컬럼의 데이터 타입을 검증합니다.
        
        Args:
            df: 검사할 DataFrame
            expected_types: 예상 타입 딕셔너리 {"column": "type"}
            
        Returns:
            Dict[str, bool]: 컬럼별 타입 일치 여부
        """
        result = {}
        
        for column, expected_type in expected_types.items():
            if column not in df.columns:
                result[column] = False
                continue
            
            series = df[column].dropna()
            if series.empty:
                result[column] = True  # 비어있으면 통과
                continue
            
            type_match = False
            
            if expected_type == "numeric":
                type_match = series.apply(ValidationHelpers.is_valid_number).all()
            elif expected_type == "string":
                type_match = series.apply(lambda x: isinstance(x, str)).all()
            elif expected_type == "boolean":
                type_match = series.apply(lambda x: isinstance(x, bool)).all()
            elif expected_type == "datetime":
                try:
                    pd.to_datetime(series)
                    type_match = True
                except:
                    type_match = False
            
            result[column] = type_match
        
        return result
    
    @staticmethod
    def check_data_consistency(df: pd.DataFrame, 
                              key_columns: List[str]) -> Dict[str, List[Any]]:
        """
        데이터의 일관성을 검사합니다.
        
        Args:
            df: 검사할 DataFrame
            key_columns: 키로 사용할 컬럼들
            
        Returns:
            Dict[str, List[Any]]: 일관성 이슈 딕셔너리
        """
        issues = {
            'duplicates': [],
            'missing_keys': [],
            'inconsistent_values': []
        }
        
        # 중복 검사
        if all(col in df.columns for col in key_columns):
            duplicates = df[df.duplicated(subset=key_columns, keep=False)]
            if not duplicates.empty:
                issues['duplicates'] = duplicates.to_dict('records')
        
        # 키 값 누락 검사
        for col in key_columns:
            if col in df.columns:
                missing = df[df[col].isna() | (df[col].astype(str).str.strip() == '')]
                if not missing.empty:
                    issues['missing_keys'].extend(missing.index.tolist())
        
        return issues