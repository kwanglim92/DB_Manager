"""
데이터 처리 관련 헬퍼 함수들
"""

import pandas as pd
import numpy as np
from typing import Any, Union, List, Dict, Optional, Tuple
import re
import hashlib


class DataHelpers:
    """데이터 처리를 위한 헬퍼 클래스"""
    
    @staticmethod
    def format_num_value(value: Any, decimal_places: int = 3) -> str:
        """
        숫자 값을 포맷팅합니다.
        
        Args:
            value: 포맷팅할 값
            decimal_places: 소수점 자릿수
            
        Returns:
            str: 포맷팅된 문자열
        """
        if value is None or pd.isna(value):
            return ""
        
        try:
            # 숫자로 변환 시도
            num_value = float(value)
            
            # 정수인지 확인
            if num_value.is_integer():
                return str(int(num_value))
            
            # 소수점 포맷팅
            formatted = f"{num_value:.{decimal_places}f}"
            
            # 불필요한 0 제거
            formatted = formatted.rstrip('0').rstrip('.')
            
            return formatted
            
        except (ValueError, TypeError):
            # 숫자가 아닌 경우 문자열로 반환
            return str(value)
    
    @staticmethod
    def parse_numeric_value(value: Any) -> Optional[float]:
        """
        문자열에서 숫자 값을 추출합니다.
        
        Args:
            value: 파싱할 값
            
        Returns:
            Optional[float]: 추출된 숫자 값 (실패시 None)
        """
        if value is None or pd.isna(value):
            return None
        
        try:
            # 이미 숫자인 경우
            if isinstance(value, (int, float)):
                return float(value)
            
            # 문자열에서 숫자 추출
            value_str = str(value).strip()
            
            # 빈 문자열인 경우
            if not value_str:
                return None
            
            # 정규식으로 숫자 패턴 찾기 (음수, 소수점 포함)
            pattern = r'[-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][-+]?\\d+)?'
            matches = re.findall(pattern, value_str)
            
            if matches:
                return float(matches[0])
            
            return None
            
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def clean_string_value(value: Any) -> str:
        """
        문자열 값을 정리합니다.
        
        Args:
            value: 정리할 값
            
        Returns:
            str: 정리된 문자열
        """
        if value is None or pd.isna(value):
            return ""
        
        # 문자열로 변환
        str_value = str(value).strip()
        
        # 여러 공백을 단일 공백으로 변환
        str_value = re.sub(r'\\s+', ' ', str_value)
        
        # 특수 문자 정리 (필요에 따라)
        # str_value = re.sub(r'[^\\w\\s.-]', '', str_value)
        
        return str_value
    
    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """
        두 문자열의 유사도를 계산합니다 (Levenshtein 거리 기반).
        
        Args:
            str1: 첫 번째 문자열
            str2: 두 번째 문자열
            
        Returns:
            float: 유사도 (0-1, 1이 완전히 동일)
        """
        if not str1 and not str2:
            return 1.0
        
        if not str1 or not str2:
            return 0.0
        
        # 대소문자 구분 안함
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()
        
        if str1 == str2:
            return 1.0
        
        # Levenshtein 거리 계산
        len1, len2 = len(str1), len(str2)
        matrix = np.zeros((len1 + 1, len2 + 1))
        
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if str1[i-1] == str2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # 삭제
                    matrix[i][j-1] + 1,      # 삽입
                    matrix[i-1][j-1] + cost  # 치환
                )
        
        # 유사도 계산 (0-1)
        max_len = max(len1, len2)
        distance = matrix[len1][len2]
        similarity = 1 - (distance / max_len)
        
        return max(0.0, similarity)
    
    @staticmethod
    def detect_data_type(series: pd.Series) -> str:
        """
        Series의 데이터 타입을 감지합니다.
        
        Args:
            series: 분석할 pandas Series
            
        Returns:
            str: 감지된 데이터 타입 ('numeric', 'text', 'boolean', 'mixed')
        """
        if series.empty:
            return 'empty'
        
        # NaN이 아닌 값들만 분석
        non_null_series = series.dropna()
        
        if non_null_series.empty:
            return 'null'
        
        numeric_count = 0
        text_count = 0
        boolean_count = 0
        
        for value in non_null_series:
            if isinstance(value, (bool, np.bool_)):
                boolean_count += 1
            elif DataHelpers.parse_numeric_value(value) is not None:
                numeric_count += 1
            else:
                text_count += 1
        
        total_count = len(non_null_series)
        
        # 80% 이상이 같은 타입이면 해당 타입으로 분류
        if numeric_count / total_count >= 0.8:
            return 'numeric'
        elif boolean_count / total_count >= 0.8:
            return 'boolean'
        elif text_count / total_count >= 0.8:
            return 'text'
        else:
            return 'mixed'
    
    @staticmethod
    def find_outliers(series: pd.Series, method: str = 'iqr') -> List[int]:
        """
        Series에서 이상값의 인덱스를 찾습니다.
        
        Args:
            series: 분석할 pandas Series
            method: 이상값 검출 방법 ('iqr', 'zscore')
            
        Returns:
            List[int]: 이상값의 인덱스 리스트
        """
        outlier_indices = []
        
        # 숫자 데이터만 추출
        numeric_values = []
        numeric_indices = []
        
        for idx, value in series.items():
            num_val = DataHelpers.parse_numeric_value(value)
            if num_val is not None:
                numeric_values.append(num_val)
                numeric_indices.append(idx)
        
        if len(numeric_values) < 4:  # 데이터가 너무 적으면 분석 안함
            return outlier_indices
        
        numeric_array = np.array(numeric_values)
        
        if method == 'iqr':
            # IQR 방법
            q1 = np.percentile(numeric_array, 25)
            q3 = np.percentile(numeric_array, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for i, value in enumerate(numeric_array):
                if value < lower_bound or value > upper_bound:
                    outlier_indices.append(numeric_indices[i])
        
        elif method == 'zscore':
            # Z-score 방법
            mean = np.mean(numeric_array)
            std = np.std(numeric_array)
            
            if std > 0:  # 표준편차가 0이 아닌 경우
                z_scores = np.abs((numeric_array - mean) / std)
                
                for i, z_score in enumerate(z_scores):
                    if z_score > 3:  # |z-score| > 3인 경우 이상값
                        outlier_indices.append(numeric_indices[i])
        
        return outlier_indices
    
    @staticmethod
    def calculate_statistics(series: pd.Series) -> Dict[str, Any]:
        """
        Series의 기본 통계를 계산합니다.
        
        Args:
            series: 분석할 pandas Series
            
        Returns:
            Dict[str, Any]: 통계 정보
        """
        stats = {
            'count': len(series),
            'non_null_count': series.count(),
            'null_count': series.isnull().sum(),
            'null_percentage': (series.isnull().sum() / len(series)) * 100,
            'unique_count': series.nunique(),
            'data_type': DataHelpers.detect_data_type(series)
        }
        
        # 숫자 데이터의 경우 추가 통계
        if stats['data_type'] == 'numeric':
            numeric_values = [DataHelpers.parse_numeric_value(v) for v in series.dropna()]
            numeric_values = [v for v in numeric_values if v is not None]
            
            if numeric_values:
                numeric_array = np.array(numeric_values)
                stats.update({
                    'mean': np.mean(numeric_array),
                    'median': np.median(numeric_array),
                    'std': np.std(numeric_array),
                    'min': np.min(numeric_array),
                    'max': np.max(numeric_array),
                    'range': np.max(numeric_array) - np.min(numeric_array)
                })
        
        # 텍스트 데이터의 경우 추가 정보
        elif stats['data_type'] == 'text':
            text_values = series.dropna().astype(str)
            if not text_values.empty:
                stats.update({
                    'avg_length': text_values.str.len().mean(),
                    'min_length': text_values.str.len().min(),
                    'max_length': text_values.str.len().max(),
                    'most_common': text_values.value_counts().index[0] if len(text_values.value_counts()) > 0 else None
                })
        
        return stats
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        텍스트를 정규화합니다.
        
        Args:
            text: 정규화할 텍스트
            
        Returns:
            str: 정규화된 텍스트
        """
        if not text:
            return ""
        
        # 소문자 변환
        normalized = text.lower().strip()
        
        # 여러 공백을 단일 공백으로
        normalized = re.sub(r'\\s+', ' ', normalized)
        
        # 특수 문자 정리 (선택적)
        # normalized = re.sub(r'[^\\w\\s.-]', '', normalized)
        
        return normalized
    
    @staticmethod
    def generate_hash(data: str) -> str:
        """
        데이터의 해시값을 생성합니다.
        
        Args:
            data: 해시할 데이터
            
        Returns:
            str: SHA-256 해시값
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """
        안전한 나눗셈을 수행합니다.
        
        Args:
            numerator: 분자
            denominator: 분모
            default: 분모가 0일 때 반환할 기본값
            
        Returns:
            float: 나눗셈 결과
        """
        try:
            if denominator == 0:
                return default
            return numerator / denominator
        except (TypeError, ValueError):
            return default
    
    @staticmethod
    def merge_dataframes(dfs: List[pd.DataFrame], on_columns: List[str], 
                        how: str = 'outer') -> pd.DataFrame:
        """
        여러 DataFrame을 병합합니다.
        
        Args:
            dfs: 병합할 DataFrame 리스트
            on_columns: 병합 기준 컬럼들
            how: 병합 방식 ('inner', 'outer', 'left', 'right')
            
        Returns:
            pd.DataFrame: 병합된 DataFrame
        """
        if not dfs:
            return pd.DataFrame()
        
        if len(dfs) == 1:
            return dfs[0].copy()
        
        result = dfs[0].copy()
        
        for df in dfs[1:]:
            try:
                result = pd.merge(result, df, on=on_columns, how=how, suffixes=('', '_duplicate'))
            except Exception as e:
                print(f"DataFrame 병합 오류: {str(e)}")
                continue
        
        return result
    
    @staticmethod
    def pivot_data(df: pd.DataFrame, index_col: str, columns_col: str, 
                  values_col: str) -> pd.DataFrame:
        """
        DataFrame을 피벗합니다.
        
        Args:
            df: 피벗할 DataFrame
            index_col: 인덱스로 사용할 컬럼
            columns_col: 컬럼으로 사용할 컬럼
            values_col: 값으로 사용할 컬럼
            
        Returns:
            pd.DataFrame: 피벗된 DataFrame
        """
        try:
            pivoted = df.pivot(index=index_col, columns=columns_col, values=values_col)
            return pivoted.fillna('')
        except Exception as e:
            print(f"데이터 피벗 오류: {str(e)}")
            return pd.DataFrame()
    
    @staticmethod
    def export_to_excel(df: pd.DataFrame, filename: str, sheet_name: str = 'Sheet1') -> bool:
        """
        DataFrame을 Excel 파일로 내보냅니다.
        
        Args:
            df: 내보낼 DataFrame
            filename: 파일명
            sheet_name: 시트명
            
        Returns:
            bool: 성공 여부
        """
        try:
            df.to_excel(filename, sheet_name=sheet_name, index=False)
            return True
        except Exception as e:
            print(f"Excel 내보내기 오류: {str(e)}")
            return False