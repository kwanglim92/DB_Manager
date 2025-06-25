"""
파일 처리 관련 헬퍼 함수들
"""

import os
import json
import csv
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
import shutil
from pathlib import Path
import tempfile


class FileHelpers:
    """파일 처리를 위한 헬퍼 클래스"""
    
    @staticmethod
    def read_text_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        텍스트 파일을 읽습니다.
        
        Args:
            file_path: 파일 경로
            encoding: 인코딩 방식
            
        Returns:
            Optional[str]: 파일 내용 (실패시 None)
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            print(f"파일 읽기 오류 ({file_path}): {str(e)}")
            return None
    
    @staticmethod
    def write_text_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        텍스트 파일을 작성합니다.
        
        Args:
            file_path: 파일 경로
            content: 작성할 내용
            encoding: 인코딩 방식
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 디렉토리 생성 (존재하지 않는 경우)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"파일 쓰기 오류 ({file_path}): {str(e)}")
            return False
    
    @staticmethod
    def read_json_file(file_path: str, encoding: str = 'utf-8') -> Optional[Dict[str, Any]]:
        """
        JSON 파일을 읽습니다.
        
        Args:
            file_path: 파일 경로
            encoding: 인코딩 방식
            
        Returns:
            Optional[Dict[str, Any]]: JSON 데이터 (실패시 None)
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except Exception as e:
            print(f"JSON 파일 읽기 오류 ({file_path}): {str(e)}")
            return None
    
    @staticmethod
    def write_json_file(file_path: str, data: Dict[str, Any], 
                       encoding: str = 'utf-8', indent: int = 2) -> bool:
        """
        JSON 파일을 작성합니다.
        
        Args:
            file_path: 파일 경로
            data: 저장할 데이터
            encoding: 인코딩 방식
            indent: 들여쓰기 칸 수
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 디렉토리 생성 (존재하지 않는 경우)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            return True
        except Exception as e:
            print(f"JSON 파일 쓰기 오류 ({file_path}): {str(e)}")
            return False
    
    @staticmethod
    def read_csv_file(file_path: str, encoding: str = 'utf-8', 
                     delimiter: str = ',', **kwargs) -> Optional[pd.DataFrame]:
        """
        CSV 파일을 읽습니다.
        
        Args:
            file_path: 파일 경로
            encoding: 인코딩 방식
            delimiter: 구분자
            **kwargs: pandas.read_csv에 전달할 추가 인수
            
        Returns:
            Optional[pd.DataFrame]: DataFrame (실패시 None)
        """
        try:
            return pd.read_csv(file_path, encoding=encoding, delimiter=delimiter, **kwargs)
        except Exception as e:
            print(f"CSV 파일 읽기 오류 ({file_path}): {str(e)}")
            return None
    
    @staticmethod
    def write_csv_file(df: pd.DataFrame, file_path: str, encoding: str = 'utf-8-sig',
                      index: bool = False, **kwargs) -> bool:
        """
        DataFrame을 CSV 파일로 저장합니다.
        
        Args:
            df: 저장할 DataFrame
            file_path: 파일 경로
            encoding: 인코딩 방식
            index: 인덱스 포함 여부
            **kwargs: pandas.to_csv에 전달할 추가 인수
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 디렉토리 생성 (존재하지 않는 경우)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            df.to_csv(file_path, encoding=encoding, index=index, **kwargs)
            return True
        except Exception as e:
            print(f"CSV 파일 쓰기 오류 ({file_path}): {str(e)}")
            return False
    
    @staticmethod
    def read_excel_file(file_path: str, sheet_name: Union[str, int] = 0, 
                       **kwargs) -> Optional[pd.DataFrame]:
        """
        Excel 파일을 읽습니다.
        
        Args:
            file_path: 파일 경로
            sheet_name: 시트명 또는 시트 인덱스
            **kwargs: pandas.read_excel에 전달할 추가 인수
            
        Returns:
            Optional[pd.DataFrame]: DataFrame (실패시 None)
        """
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
        except Exception as e:
            print(f"Excel 파일 읽기 오류 ({file_path}): {str(e)}")
            return None
    
    @staticmethod
    def write_excel_file(df: pd.DataFrame, file_path: str, sheet_name: str = 'Sheet1',
                        index: bool = False, **kwargs) -> bool:
        """
        DataFrame을 Excel 파일로 저장합니다.
        
        Args:
            df: 저장할 DataFrame
            file_path: 파일 경로
            sheet_name: 시트명
            index: 인덱스 포함 여부
            **kwargs: pandas.to_excel에 전달할 추가 인수
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 디렉토리 생성 (존재하지 않는 경우)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            df.to_excel(file_path, sheet_name=sheet_name, index=index, **kwargs)
            return True
        except Exception as e:
            print(f"Excel 파일 쓰기 오류 ({file_path}): {str(e)}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
        """
        파일 정보를 가져옵니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            Optional[Dict[str, Any]]: 파일 정보 딕셔너리
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            path_obj = Path(file_path)
            
            return {
                'name': path_obj.name,
                'extension': path_obj.suffix,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_file': path_obj.is_file(),
                'is_dir': path_obj.is_dir(),
                'absolute_path': str(path_obj.absolute())
            }
        except Exception as e:
            print(f"파일 정보 조회 오류 ({file_path}): {str(e)}")
            return None
    
    @staticmethod
    def list_files(directory: str, extension: str = None, 
                  recursive: bool = False) -> List[str]:
        """
        디렉토리의 파일 목록을 가져옵니다.
        
        Args:
            directory: 디렉토리 경로
            extension: 필터할 확장자 (예: '.txt')
            recursive: 하위 디렉토리 포함 여부
            
        Returns:
            List[str]: 파일 경로 리스트
        """
        try:
            files = []
            path_obj = Path(directory)
            
            if not path_obj.exists() or not path_obj.is_dir():
                return files
            
            # 파일 검색 패턴
            pattern = "*"
            if extension:
                pattern = f"*{extension}"
            
            if recursive:
                files = [str(f) for f in path_obj.rglob(pattern) if f.is_file()]
            else:
                files = [str(f) for f in path_obj.glob(pattern) if f.is_file()]
            
            return sorted(files)
            
        except Exception as e:
            print(f"파일 목록 조회 오류 ({directory}): {str(e)}")
            return []
    
    @staticmethod
    def copy_file(source: str, destination: str, overwrite: bool = False) -> bool:
        """
        파일을 복사합니다.
        
        Args:
            source: 원본 파일 경로
            destination: 대상 파일 경로
            overwrite: 덮어쓰기 허용 여부
            
        Returns:
            bool: 성공 여부
        """
        try:
            if not os.path.exists(source):
                print(f"원본 파일이 존재하지 않습니다: {source}")
                return False
            
            if os.path.exists(destination) and not overwrite:
                print(f"대상 파일이 이미 존재합니다: {destination}")
                return False
            
            # 대상 디렉토리 생성
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            shutil.copy2(source, destination)
            return True
            
        except Exception as e:
            print(f"파일 복사 오류: {str(e)}")
            return False
    
    @staticmethod
    def move_file(source: str, destination: str, overwrite: bool = False) -> bool:
        """
        파일을 이동합니다.
        
        Args:
            source: 원본 파일 경로
            destination: 대상 파일 경로
            overwrite: 덮어쓰기 허용 여부
            
        Returns:
            bool: 성공 여부
        """
        try:
            if not os.path.exists(source):
                print(f"원본 파일이 존재하지 않습니다: {source}")
                return False
            
            if os.path.exists(destination) and not overwrite:
                print(f"대상 파일이 이미 존재합니다: {destination}")
                return False
            
            # 대상 디렉토리 생성
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            shutil.move(source, destination)
            return True
            
        except Exception as e:
            print(f"파일 이동 오류: {str(e)}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        파일을 삭제합니다.
        
        Args:
            file_path: 삭제할 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            else:
                print(f"파일이 존재하지 않습니다: {file_path}")
                return False
        except Exception as e:
            print(f"파일 삭제 오류: {str(e)}")
            return False
    
    @staticmethod
    def create_backup(file_path: str, backup_suffix: str = ".backup") -> Optional[str]:
        """
        파일의 백업을 생성합니다.
        
        Args:
            file_path: 백업할 파일 경로
            backup_suffix: 백업 파일 접미사
            
        Returns:
            Optional[str]: 백업 파일 경로 (실패시 None)
        """
        try:
            if not os.path.exists(file_path):
                print(f"백업할 파일이 존재하지 않습니다: {file_path}")
                return None
            
            backup_path = file_path + backup_suffix
            
            # 기존 백업 파일이 있다면 타임스탬프 추가
            if os.path.exists(backup_path):
                import time
                timestamp = int(time.time())
                backup_path = f"{file_path}.{timestamp}{backup_suffix}"
            
            if FileHelpers.copy_file(file_path, backup_path, overwrite=True):
                return backup_path
            return None
            
        except Exception as e:
            print(f"백업 생성 오류: {str(e)}")
            return None
    
    @staticmethod
    def create_temp_file(suffix: str = ".tmp", prefix: str = "temp_") -> str:
        """
        임시 파일을 생성합니다.
        
        Args:
            suffix: 파일 확장자
            prefix: 파일 접두사
            
        Returns:
            str: 임시 파일 경로
        """
        try:
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
            os.close(fd)  # 파일 핸들 닫기
            return temp_path
        except Exception as e:
            print(f"임시 파일 생성 오류: {str(e)}")
            return ""
    
    @staticmethod
    def parse_custom_text_file(file_path: str, encoding: str = 'utf-8') -> Optional[pd.DataFrame]:
        """
        사용자 정의 텍스트 파일을 파싱합니다.
        
        Args:
            file_path: 파일 경로
            encoding: 인코딩 방식
            
        Returns:
            Optional[pd.DataFrame]: 파싱된 DataFrame
        """
        try:
            content = FileHelpers.read_text_file(file_path, encoding)
            if not content:
                return None
            
            lines = content.strip().split('\\n')
            data = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):  # 빈 줄이나 주석 무시
                    continue
                
                # 탭, 쉼표, 공백 등으로 분리 시도
                parts = None
                for delimiter in ['\\t', ',', '|', ';']:
                    parts = line.split(delimiter)
                    if len(parts) > 1:
                        break
                
                if not parts or len(parts) < 2:
                    # 공백으로 분리 시도
                    parts = line.split()
                
                if len(parts) >= 3:  # Module, Part, Item_Name, Value 등을 기대
                    row_data = {
                        'Module': parts[0].strip(),
                        'Part': parts[1].strip(),
                        'Item_Name': parts[2].strip(),
                        'Value': parts[3].strip() if len(parts) > 3 else ''
                    }
                    
                    # 추가 컬럼이 있는 경우
                    for i, part in enumerate(parts[4:], 4):
                        row_data[f'Column_{i}'] = part.strip()
                    
                    data.append(row_data)
            
            if data:
                return pd.DataFrame(data)
            return None
            
        except Exception as e:
            print(f"텍스트 파일 파싱 오류 ({file_path}): {str(e)}")
            return None
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        안전한 파일명을 생성합니다.
        
        Args:
            filename: 원본 파일명
            
        Returns:
            str: 안전한 파일명
        """
        import re
        
        # 위험한 문자들을 제거하거나 치환
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 연속된 언더스코어를 단일로 변환
        safe_filename = re.sub(r'_+', '_', safe_filename)
        
        # 앞뒤 공백 및 점 제거
        safe_filename = safe_filename.strip('. ')
        
        # 빈 문자열인 경우 기본값
        if not safe_filename:
            safe_filename = "untitled"
        
        # 길이 제한 (255자)
        if len(safe_filename) > 255:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:255-len(ext)] + ext
        
        return safe_filename
    
    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """
        디렉토리가 존재하는지 확인하고 없으면 생성합니다.
        
        Args:
            directory: 디렉토리 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            print(f"디렉토리 생성 오류 ({directory}): {str(e)}")
            return False