"""
최적화된 DB 비교 엔진
메모리 효율적이고 빠른 파일 비교 기능 제공
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Generator, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import hashlib
from dataclasses import dataclass
import os

@dataclass
class ComparisonResult:
    """비교 결과 데이터 클래스"""
    parameter_name: str
    values: Dict[str, str]  # {file_name: value}
    is_different: bool
    difference_count: int
    common_value: Optional[str] = None

class ComparisonCache:
    """비교 결과 캐시"""
    
    def __init__(self, max_size: int = 1000):
        """
        초기화
        
        Args:
            max_size: 최대 캐시 크기
        """
        self.cache = {}
        self.max_size = max_size
    
    def get_key(self, file_paths: List[str]) -> str:
        """캐시 키 생성"""
        # 파일 경로들을 정렬하고 해시
        sorted_paths = sorted(file_paths)
        key_string = '|'.join(sorted_paths)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, file_paths: List[str]) -> Optional[pd.DataFrame]:
        """캐시에서 결과 가져오기"""
        key = self.get_key(file_paths)
        return self.cache.get(key)
    
    def set(self, file_paths: List[str], result: pd.DataFrame):
        """캐시에 결과 저장"""
        if len(self.cache) >= self.max_size:
            # FIFO 방식으로 가장 오래된 항목 제거
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        key = self.get_key(file_paths)
        self.cache[key] = result.copy()
    
    def clear(self):
        """캐시 초기화"""
        self.cache.clear()

class OptimizedComparisonEngine:
    """최적화된 비교 엔진"""
    
    def __init__(self, chunk_size: int = 10000, max_workers: int = 4):
        """
        초기화
        
        Args:
            chunk_size: 청크 크기
            max_workers: 최대 워커 스레드 수
        """
        self.chunk_size = chunk_size
        self.max_workers = max_workers
        self.cache = ComparisonCache()
    
    def compare_files(self, file_paths: List[str], use_cache: bool = True) -> pd.DataFrame:
        """
        파일들을 비교하여 통합 데이터프레임 반환
        
        Args:
            file_paths: 비교할 파일 경로 리스트
            use_cache: 캐시 사용 여부
            
        Returns:
            비교 결과 데이터프레임
        """
        # 캐시 확인
        if use_cache:
            cached_result = self.cache.get(file_paths)
            if cached_result is not None:
                return cached_result
        
        # 파일 크기 확인
        total_size = sum(os.path.getsize(path) for path in file_paths if os.path.exists(path))
        
        # 크기에 따라 처리 방식 결정
        if total_size < 50 * 1024 * 1024:  # 50MB 미만
            result = self._compare_small_files(file_paths)
        else:
            result = self._compare_large_files_chunked(file_paths)
        
        # 캐시 저장
        if use_cache:
            self.cache.set(file_paths, result)
        
        return result
    
    def _compare_small_files(self, file_paths: List[str]) -> pd.DataFrame:
        """작은 파일들 비교 (메모리에 전체 로드)"""
        dataframes = []
        file_names = []
        
        for path in file_paths:
            try:
                df = self._load_file(path)
                if df is not None:
                    file_name = Path(path).stem
                    df['file_name'] = file_name
                    df['file_path'] = path
                    dataframes.append(df)
                    file_names.append(file_name)
            except Exception as e:
                print(f"파일 로드 실패 {path}: {e}")
        
        if not dataframes:
            return pd.DataFrame()
        
        # 모든 데이터프레임 병합
        merged_df = self._merge_dataframes(dataframes)
        
        # 차이점 분석
        merged_df = self._analyze_differences(merged_df, file_names)
        
        return merged_df
    
    def _compare_large_files_chunked(self, file_paths: List[str]) -> pd.DataFrame:
        """대용량 파일 청크 단위 비교"""
        results = []
        
        # 청크 단위로 처리
        for chunk_data in self._read_files_in_chunks(file_paths):
            chunk_result = self._process_chunk(chunk_data)
            results.append(chunk_result)
        
        # 모든 청크 결과 병합
        if results:
            final_result = pd.concat(results, ignore_index=True)
            return final_result
        
        return pd.DataFrame()
    
    def _read_files_in_chunks(self, file_paths: List[str]) -> Generator:
        """파일들을 청크 단위로 읽기"""
        # 각 파일에서 청크 읽기
        chunk_readers = []
        for path in file_paths:
            if path.endswith('.csv'):
                reader = pd.read_csv(path, chunksize=self.chunk_size, iterator=True)
            elif path.endswith(('.xlsx', '.xls')):
                # Excel 파일은 전체 로드 후 청크로 분할
                df = pd.read_excel(path)
                reader = [df[i:i+self.chunk_size] for i in range(0, len(df), self.chunk_size)]
            else:
                reader = [self._load_file(path)]
            
            chunk_readers.append({
                'path': path,
                'file_name': Path(path).stem,
                'reader': reader
            })
        
        # 청크별로 yield
        chunk_index = 0
        while True:
            chunk_data = []
            all_exhausted = True
            
            for reader_info in chunk_readers:
                try:
                    if hasattr(reader_info['reader'], '__next__'):
                        chunk = next(reader_info['reader'])
                    else:
                        if chunk_index < len(reader_info['reader']):
                            chunk = reader_info['reader'][chunk_index]
                        else:
                            continue
                    
                    chunk['file_name'] = reader_info['file_name']
                    chunk['file_path'] = reader_info['path']
                    chunk_data.append(chunk)
                    all_exhausted = False
                except StopIteration:
                    continue
            
            if all_exhausted:
                break
            
            if chunk_data:
                yield chunk_data
            
            chunk_index += 1
    
    def _process_chunk(self, chunk_data: List[pd.DataFrame]) -> pd.DataFrame:
        """청크 데이터 처리"""
        if not chunk_data:
            return pd.DataFrame()
        
        # 청크 병합
        merged = self._merge_dataframes(chunk_data)
        
        # 파일 이름 추출
        file_names = list(set(df['file_name'].iloc[0] for df in chunk_data if 'file_name' in df.columns))
        
        # 차이점 분석
        merged = self._analyze_differences(merged, file_names)
        
        return merged
    
    def parallel_compare(self, file_paths: List[str]) -> pd.DataFrame:
        """병렬 처리를 사용한 파일 비교"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 각 파일을 병렬로 로드
            future_to_path = {
                executor.submit(self._load_file_with_metadata, path): path 
                for path in file_paths
            }
            
            dataframes = []
            file_names = []
            
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    df, metadata = future.result()
                    if df is not None:
                        dataframes.append(df)
                        file_names.append(metadata['file_name'])
                except Exception as e:
                    print(f"파일 로드 실패 {path}: {e}")
            
            if dataframes:
                # 병합 및 분석
                merged = self._merge_dataframes(dataframes)
                merged = self._analyze_differences(merged, file_names)
                return merged
        
        return pd.DataFrame()
    
    def _load_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """파일 로드"""
        try:
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path, encoding='utf-8-sig')
            elif file_path.endswith(('.xlsx', '.xls')):
                return pd.read_excel(file_path)
            elif file_path.endswith('.txt'):
                # 탭 구분 텍스트 파일
                return pd.read_csv(file_path, sep='\t', encoding='utf-8-sig')
            else:
                print(f"지원하지 않는 파일 형식: {file_path}")
                return None
        except Exception as e:
            print(f"파일 로드 오류 {file_path}: {e}")
            return None
    
    def _load_file_with_metadata(self, file_path: str) -> Tuple[Optional[pd.DataFrame], Dict]:
        """파일 로드 및 메타데이터 반환"""
        df = self._load_file(file_path)
        metadata = {
            'file_name': Path(file_path).stem,
            'file_path': file_path,
            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }
        
        if df is not None:
            df['file_name'] = metadata['file_name']
            df['file_path'] = metadata['file_path']
        
        return df, metadata
    
    def _merge_dataframes(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """데이터프레임들 병합"""
        if not dataframes:
            return pd.DataFrame()
        
        # 모든 데이터프레임 연결
        merged = pd.concat(dataframes, ignore_index=True, sort=False)
        
        # 중복 제거 옵션 (필요시)
        # merged = merged.drop_duplicates(subset=['parameter_name', 'file_name'])
        
        return merged
    
    def _analyze_differences(self, df: pd.DataFrame, file_names: List[str]) -> pd.DataFrame:
        """차이점 분석"""
        if df.empty or 'parameter_name' not in df.columns:
            return df
        
        # 차이점 컬럼 추가
        df['is_different'] = False
        df['difference_count'] = 0
        df['common_value'] = None
        
        # 파라미터별로 그룹화
        for param_name, group in df.groupby('parameter_name'):
            # 해당 파라미터의 값들
            values = group['default_value'].unique() if 'default_value' in group.columns else []
            
            # 차이점 여부
            is_different = len(values) > 1
            
            # 가장 많이 나타난 값
            if 'default_value' in group.columns:
                value_counts = group['default_value'].value_counts()
                common_value = value_counts.index[0] if not value_counts.empty else None
            else:
                common_value = None
            
            # 업데이트
            df.loc[group.index, 'is_different'] = is_different
            df.loc[group.index, 'difference_count'] = len(values) - 1 if len(values) > 0 else 0
            df.loc[group.index, 'common_value'] = common_value
        
        return df
    
    def get_difference_summary(self, comparison_result: pd.DataFrame) -> Dict:
        """차이점 요약 정보 반환"""
        if comparison_result.empty:
            return {
                'total_parameters': 0,
                'different_parameters': 0,
                'identical_parameters': 0,
                'difference_rate': 0
            }
        
        total_params = comparison_result['parameter_name'].nunique()
        different_params = comparison_result[comparison_result['is_different'] == True]['parameter_name'].nunique()
        identical_params = total_params - different_params
        
        return {
            'total_parameters': total_params,
            'different_parameters': different_params,
            'identical_parameters': identical_params,
            'difference_rate': (different_params / total_params * 100) if total_params > 0 else 0
        }
    
    def export_comparison_report(self, comparison_result: pd.DataFrame, output_path: str, format: str = 'excel'):
        """비교 결과 리포트 내보내기"""
        try:
            if format == 'excel':
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    # 전체 결과
                    comparison_result.to_excel(writer, sheet_name='전체 비교', index=False)
                    
                    # 차이점만
                    diff_only = comparison_result[comparison_result['is_different'] == True]
                    diff_only.to_excel(writer, sheet_name='차이점', index=False)
                    
                    # 요약 정보
                    summary = self.get_difference_summary(comparison_result)
                    summary_df = pd.DataFrame([summary])
                    summary_df.to_excel(writer, sheet_name='요약', index=False)
            
            elif format == 'csv':
                comparison_result.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            return True
        
        except Exception as e:
            print(f"리포트 내보내기 실패: {e}")
            return False