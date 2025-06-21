# 텍스트 파일 Import/Export 기능

import os
import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

class TextFileHandler:
    """
    장비 설정 텍스트 파일의 Import/Export 기능을 처리하는 클래스
    """
    
    # 텍스트 파일의 표준 헤더
    TEXT_FILE_HEADER = ["Module", "Part", "ItemName", "ItemType", "ItemValue", "ItemDescription"]
    
    def __init__(self, db_schema):
        """
        Args:
            db_schema: DBSchema 인스턴스
        """
        self.db_schema = db_schema
    
    def validate_text_file_format(self, file_path: str) -> Tuple[bool, str]:
        """
        텍스트 파일의 형식을 검증합니다.
        
        Args:
            file_path (str): 검증할 파일 경로
            
        Returns:
            Tuple[bool, str]: (검증 성공 여부, 오류 메시지)
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                first_line = file.readline().strip()
                
            # 탭으로 분리된 헤더 확인
            headers = [h.strip() for h in first_line.split('\t')]
            
            if len(headers) != len(self.TEXT_FILE_HEADER):
                return False, f"헤더 개수가 맞지 않습니다. 예상: {len(self.TEXT_FILE_HEADER)}, 실제: {len(headers)}"
            
            # 헤더 이름 검증
            for i, (expected, actual) in enumerate(zip(self.TEXT_FILE_HEADER, headers)):
                if expected != actual:
                    return False, f"헤더 '{actual}'가 예상되는 '{expected}'와 다릅니다."
            
            return True, "파일 형식이 올바릅니다."
            
        except Exception as e:
            return False, f"파일 읽기 오류: {str(e)}"
    
    def parse_text_file(self, file_path: str) -> Tuple[bool, List[Dict], str]:
        """
        텍스트 파일을 파싱하여 데이터를 추출합니다.
        
        Args:
            file_path (str): 파싱할 파일 경로
            
        Returns:
            Tuple[bool, List[Dict], str]: (성공 여부, 파싱된 데이터 리스트, 오류 메시지)
        """
        try:
            # 파일 형식 검증
            is_valid, error_msg = self.validate_text_file_format(file_path)
            if not is_valid:
                return False, [], error_msg
            
            parsed_data = []
            line_number = 0
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                # 헤더 라인 건너뛰기
                file.readline()
                line_number = 1
                
                for line in file:
                    line_number += 1
                    line = line.strip()
                    
                    # 빈 라인 건너뛰기
                    if not line:
                        continue
                    
                    # 탭으로 분리
                    parts = line.split('\t')
                    
                    if len(parts) != 6:
                        print(f"라인 {line_number}: 컬럼 개수가 맞지 않습니다. (실제: {len(parts)})")
                        continue
                    
                    # 데이터 정리
                    data_row = {
                        'module': parts[0].strip(),
                        'part': parts[1].strip(),
                        'item_name': parts[2].strip(),
                        'item_type': parts[3].strip(),
                        'item_value': parts[4].strip(),
                        'item_description': parts[5].strip(),
                        'line_number': line_number
                    }
                    
                    # 필수 필드 검증
                    if not data_row['item_name'] or not data_row['item_value']:
                        print(f"라인 {line_number}: 필수 필드(ItemName 또는 ItemValue)가 비어있습니다.")
                        continue
                    
                    parsed_data.append(data_row)
            
            return True, parsed_data, f"성공적으로 {len(parsed_data)}개의 항목을 파싱했습니다."
            
        except Exception as e:
            return False, [], f"파일 파싱 오류: {str(e)}"
    
    def import_from_text_file(self, file_path: str, equipment_type_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        텍스트 파일에서 데이터를 Import합니다.
        
        Args:
            file_path (str): Import할 파일 경로
            equipment_type_name (str, optional): 장비 유형명. None이면 파일명에서 추출
            
        Returns:
            Tuple[bool, str]: (성공 여부, 결과 메시지)
        """
        try:
            # 파일 파싱
            success, parsed_data, message = self.parse_text_file(file_path)
            if not success:
                return False, message
            
            if not parsed_data:
                return False, "Import할 데이터가 없습니다."
            
            # 장비 유형명 결정
            if not equipment_type_name:
                # 파일명에서 장비 유형명 추출 (확장자 제거)
                filename = os.path.basename(file_path)
                equipment_type_name = os.path.splitext(filename)[0]
            
            # 장비 유형 추가 또는 기존 유형 확인
            equipment_type_id = self.db_schema.add_equipment_type(
                equipment_type_name, 
                f"텍스트 파일에서 Import됨: {os.path.basename(file_path)}"
            )
            
            # 데이터 Import 통계
            imported_count = 0
            updated_count = 0
            error_count = 0
            
            source_file = os.path.basename(file_path)
            
            # 기존 데이터 조회 (한 번만 조회하여 성능 향상)
            existing_values = self.db_schema.get_default_values(equipment_type_id)
            existing_params = {row[1]: row[0] for row in existing_values} if existing_values else {}
            
            for data_row in parsed_data:
                try:
                    # 기존 데이터 확인
                    if data_row['item_name'] in existing_params:
                        updated_count += 1
                    else:
                        imported_count += 1
                    
                    # DB에 데이터 추가/업데이트
                    self.db_schema.add_default_value(
                        equipment_type_id=equipment_type_id,
                        parameter_name=data_row['item_name'],
                        default_value=data_row['item_value'],
                        min_spec=None,  # 텍스트 파일에는 min_spec이 없음
                        max_spec=None,  # 텍스트 파일에는 max_spec이 없음
                        occurrence_count=1,
                        total_files=1,
                        source_files=source_file,
                        description=data_row['item_description'],
                        module_name=data_row['module'],
                        part_name=data_row['part'],
                        item_type=data_row['item_type']
                    )
                    
                except Exception as e:
                    error_count += 1
                    print(f"라인 {data_row['line_number']} 처리 중 오류: {str(e)}")
            
            # 결과 메시지 생성
            result_message = f"""텍스트 파일 Import 완료:
• 파일: {os.path.basename(file_path)}
• 장비 유형: {equipment_type_name}
• 새로 추가된 파라미터: {imported_count}개
• 업데이트된 파라미터: {updated_count}개
• 오류: {error_count}개"""
            
            return True, result_message
            
        except Exception as e:
            return False, f"Import 중 오류 발생: {str(e)}"
    
    def export_to_text_file(self, equipment_type_id: int, file_path: str) -> Tuple[bool, str]:
        """
        DB 데이터를 텍스트 파일로 Export합니다.
        
        Args:
            equipment_type_id (int): Export할 장비 유형 ID
            file_path (str): Export할 파일 경로
            
        Returns:
            Tuple[bool, str]: (성공 여부, 결과 메시지)
        """
        try:
            # DB에서 데이터 조회
            db_values = self.db_schema.get_default_values(equipment_type_id)
            
            if not db_values:
                return False, "Export할 데이터가 없습니다."
            
            # 텍스트 파일 생성
            with open(file_path, 'w', encoding='utf-8', newline='') as file:
                # 헤더 작성
                file.write('\t'.join(self.TEXT_FILE_HEADER) + '\n')
                
                # 데이터 작성
                for row in db_values:
                    # 15개 값 unpacking (is_performance 포함)
                    (id, parameter_name, default_value, min_spec, max_spec, type_name,
                     occurrence_count, total_files, confidence_score, source_files, description,
                     module_name, part_name, item_type, is_performance) = row
                    
                    # 텍스트 파일 형식으로 변환
                    text_row = [
                        module_name or "DSP",  # 기본값 설정
                        part_name or "General",  # 기본값 설정
                        parameter_name,
                        item_type or "string",  # 기본값 설정
                        str(default_value),
                        description or f"This is a {parameter_name} Description"
                    ]
                    
                    file.write('\t'.join(text_row) + '\n')
            
            result_message = f"""텍스트 파일 Export 완료:
• 파일: {os.path.basename(file_path)}
• Export된 파라미터: {len(db_values)}개
• 장비 유형: {db_values[0][5] if db_values else 'Unknown'}"""
            
            return True, result_message
            
        except Exception as e:
            return False, f"Export 중 오류 발생: {str(e)}"
    
    def get_equipment_type_from_text_data(self, parsed_data: List[Dict]) -> str:
        """
        파싱된 텍스트 데이터에서 장비 유형을 추출합니다.
        
        Args:
            parsed_data (List[Dict]): 파싱된 데이터
            
        Returns:
            str: 추천되는 장비 유형명
        """
        if not parsed_data:
            return "Unknown_Equipment"
        
        # Module과 Part의 조합을 분석하여 장비 유형 추천
        modules = set()
        parts = set()
        
        for data in parsed_data:
            modules.add(data['module'])
            parts.add(data['part'])
        
        # 가장 일반적인 조합 사용
        primary_module = max(modules, key=lambda m: sum(1 for d in parsed_data if d['module'] == m))
        primary_part = max(parts, key=lambda p: sum(1 for d in parsed_data if d['part'] == p))
        
        return f"{primary_module}_{primary_part}_Equipment"
    
    def validate_export_data(self, equipment_type_id: int) -> Tuple[bool, str, int]:
        """
        Export할 데이터의 유효성을 검증합니다.
        
        Args:
            equipment_type_id (int): 장비 유형 ID
            
        Returns:
            Tuple[bool, str, int]: (유효성 여부, 메시지, 데이터 개수)
        """
        try:
            db_values = self.db_schema.get_default_values(equipment_type_id)
            
            if not db_values:
                return False, "Export할 데이터가 없습니다.", 0
            
            # 필수 필드 검증
            missing_fields = []
            for row in db_values:
                parameter_name = row[1]
                default_value = row[2]
                
                if not parameter_name:
                    missing_fields.append("파라미터명이 비어있는 항목이 있습니다.")
                    break
                if not str(default_value).strip():
                    missing_fields.append(f"파라미터 '{parameter_name}'의 설정값이 비어있습니다.")
                    break
            
            if missing_fields:
                return False, "데이터 검증 실패: " + ", ".join(missing_fields), len(db_values)
            
            return True, f"Export 가능한 데이터: {len(db_values)}개", len(db_values)
            
        except Exception as e:
            return False, f"데이터 검증 중 오류: {str(e)}", 0 