# 간소화된 QC 검수 보고서 생성 모듈

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd


def export_qc_results_to_excel(qc_results: List[Dict], equipment_name: str, 
                              equipment_type: str, file_path: str) -> bool:
    """QC 검수 결과를 Excel 파일로 내보내기"""
    try:
        # 검수 결과 데이터프레임 생성
        results_data = []
        for result in qc_results:
            results_data.append({
                '파라미터': result.get('parameter', ''),
                '문제 유형': result.get('issue_type', ''),
                '상세 설명': result.get('description', ''),
                '심각도': result.get('severity', ''),
                '카테고리': result.get('category', ''),
                '권장사항': result.get('recommendation', '')
            })
        
        results_df = pd.DataFrame(results_data)
        
        # 검수 요약 정보
        summary_data = {
            '항목': [
                '검수 일시',
                '장비명', 
                '장비 유형',
                '총 이슈 수',
                '높은 심각도',
                '중간 심각도', 
                '낮은 심각도'
            ],
            '값': [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                equipment_name,
                equipment_type,
                len(qc_results),
                len([r for r in qc_results if r.get('severity') == '높음']),
                len([r for r in qc_results if r.get('severity') == '중간']),
                len([r for r in qc_results if r.get('severity') == '낮음'])
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Excel 파일 생성
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # 검수 요약 시트
            summary_df.to_excel(writer, sheet_name='검수 요약', index=False)
            
            # 검수 결과 시트
            if results_df.empty:
                # 이슈가 없는 경우
                no_issues_df = pd.DataFrame({
                    '결과': ['✅ 검수 완료 - 발견된 이슈가 없습니다.']
                })
                no_issues_df.to_excel(writer, sheet_name='검수 결과', index=False)
            else:
                results_df.to_excel(writer, sheet_name='검수 결과', index=False)
        
        return True
        
    except Exception as e:
        print(f"Excel 보고서 생성 오류: {e}")
        return False


def export_qc_results_to_csv(qc_results: List[Dict], equipment_name: str,
                            equipment_type: str, file_path: str) -> bool:
    """QC 검수 결과를 CSV 파일로 내보내기"""
    try:
        # 검수 결과 데이터프레임 생성
        results_data = []
        for result in qc_results:
            results_data.append({
                '파라미터': result.get('parameter', ''),
                '문제 유형': result.get('issue_type', ''),
                '상세 설명': result.get('description', ''),
                '심각도': result.get('severity', ''),
                '카테고리': result.get('category', ''),
                '권장사항': result.get('recommendation', '')
            })
        
        results_df = pd.DataFrame(results_data)
        
        # CSV 파일 생성
        results_df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return True
        
    except Exception as e:
        print(f"CSV 보고서 생성 오류: {e}")
        return False