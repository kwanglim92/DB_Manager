"""
통합 QC 검수 시스템 (간소화)
기존 중복된 QC 함수들을 통합하여 단일 진입점 제공
"""

import os
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

class UnifiedQCSystem:
    """통합 QC 검수 시스템 - 단일 진입점 (간소화)"""
    
    def __init__(self, db_schema, update_log_callback=None):
        self.db_schema = db_schema
        self.update_log = update_log_callback or self._default_log
    
    def _default_log(self, message: str):
        """기본 로그 출력"""
        print(f"[QC] {message}")
    
    def perform_unified_qc_check(self, equipment_type_id: int, mode: str = "comprehensive") -> Dict[str, Any]:
        """
        통합 QC 검수 실행
        
        Args:
            equipment_type_id: 장비 유형 ID
            mode: 검수 모드 ("comprehensive", "checklist_only", "critical_only")
            
        Returns:
            검수 결과 딕셔너리
        """
        try:
            self.update_log(f"🔍 통합 QC 검수 시작 - 장비 ID: {equipment_type_id}, 모드: {mode}")
            
            # 1. 데이터 로드
            checklist_only = (mode == "checklist_only")
            data = self.db_schema.get_default_values(equipment_type_id, checklist_only=checklist_only)
            
            if not data:
                return {
                    'success': False,
                    'message': f'검수할 데이터가 없습니다 (모드: {mode})',
                    'results': []
                }
            
            # 2. 데이터프레임 변환
            df = pd.DataFrame(data, columns=[
                "id", "parameter_name", "default_value", "min_spec", "max_spec", "type_name",
                "occurrence_count", "total_files", "confidence_score", "source_files", "description",
                "module_name", "part_name", "item_type", "is_checklist"
            ])
            
            # 3. QC 검수 실행
            qc_results = self._run_comprehensive_qc_checks(df, mode)
            
            # 4. 결과 종합
            result_summary = self._summarize_qc_results(qc_results, mode)
            
            self.update_log(f"✅ 통합 QC 검수 완료 - 총 {len(qc_results)}개 항목 검사")
            
            return {
                'success': True,
                'equipment_type_id': equipment_type_id,
                'mode': mode,
                'summary': result_summary,
                'detailed_results': qc_results,
                'recommendations': self._generate_recommendations(qc_results, mode)
            }
            
        except Exception as e:
            error_msg = f"통합 QC 검수 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            return {
                'success': False,
                'message': error_msg,
                'results': []
            }
    
    def _run_comprehensive_qc_checks(self, df: pd.DataFrame, mode: str) -> List[Dict]:
        """종합적인 QC 검사 실행"""
        results = []
        
        for idx, row in df.iterrows():
            param_results = []
            
            # 1. 기본 데이터 검증
            param_results.extend(self._check_basic_data_integrity(row))
            
            # 2. 스펙 범위 검증
            param_results.extend(self._check_spec_compliance(row))
            
            # 3. 체크리스트 전용 검증 (해당되는 경우)
            if row['is_checklist'] or mode == "checklist_only":
                param_results.extend(self._check_critical_parameters(row))
            
            results.extend(param_results)
        
        return results
    
    def _check_basic_data_integrity(self, row: pd.Series) -> List[Dict]:
        """기본 데이터 무결성 검사"""
        issues = []
        
        # 필수 필드 누락 검사
        if pd.isna(row['parameter_name']) or str(row['parameter_name']).strip() == '':
            issues.append({
                'parameter': row.get('parameter_name', 'Unknown'),
                'issue_type': 'Missing Data',
                'description': '파라미터명이 누락되었습니다.',
                'severity': '높음'
            })
        
        if pd.isna(row['default_value']) or str(row['default_value']).strip() == '':
            issues.append({
                'parameter': row.get('parameter_name', 'Unknown'),
                'issue_type': 'Missing Data',
                'description': '기본값이 누락되었습니다.',
                'severity': '높음'
            })
        
        return issues
    
    def _check_spec_compliance(self, row: pd.Series) -> List[Dict]:
        """스펙 준수 검사"""
        issues = []
        
        try:
            default_val = float(str(row['default_value']).replace(',', ''))
            
            # Min 스펙 검사
            if not pd.isna(row['min_spec']) and str(row['min_spec']).strip():
                min_val = float(str(row['min_spec']).replace(',', ''))
                if default_val < min_val:
                    issues.append({
                        'parameter': row['parameter_name'],
                        'issue_type': 'Spec Out',
                        'description': f'기본값 {default_val}이 최소 스펙 {min_val}보다 작습니다.',
                        'severity': '높음'
                    })
            
            # Max 스펙 검사
            if not pd.isna(row['max_spec']) and str(row['max_spec']).strip():
                max_val = float(str(row['max_spec']).replace(',', ''))
                if default_val > max_val:
                    issues.append({
                        'parameter': row['parameter_name'],
                        'issue_type': 'Spec Out',
                        'description': f'기본값 {default_val}이 최대 스펙 {max_val}보다 큽니다.',
                        'severity': '높음'
                    })
        
        except ValueError:
            # 숫자가 아닌 값은 스킵
            pass
        except Exception as e:
            issues.append({
                'parameter': row.get('parameter_name', 'Unknown'),
                'issue_type': 'Data Error',
                'description': f'스펙 검사 중 오류 발생: {str(e)}',
                'severity': '중간'
            })
        
        return issues
    
    
    def _check_critical_parameters(self, row: pd.Series) -> List[Dict]:
        """중요 파라미터 전용 검사"""
        issues = []
        
        # 체크리스트 항목에 대한 특별 검사
        if row['is_checklist']:
            occurrence_ratio = int(row['occurrence_count']) / max(1, int(row['total_files']))
            
            if occurrence_ratio < 0.8:  # 80% 미만 발생 시 경고
                issues.append({
                    'parameter': row['parameter_name'],
                    'issue_type': 'Critical Parameter',
                    'description': f'중요 파라미터의 발생 빈도가 낮습니다 ({occurrence_ratio:.1%})',
                    'severity': '높음'
                })
        
        return issues
    
    def _summarize_qc_results(self, results: List[Dict], mode: str) -> Dict:
        """QC 결과 요약"""
        total_issues = len(results)
        severity_counts = {'높음': 0, '중간': 0, '낮음': 0}
        
        for result in results:
            severity = result.get('severity', '낮음')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # 전체 상태 판정
        if severity_counts['높음'] > 0:
            overall_status = 'FAIL'
        elif severity_counts['중간'] > 3:  # 중간 이슈가 3개 이상이면 주의
            overall_status = 'WARNING'
        else:
            overall_status = 'PASS'
        
        return {
            'overall_status': overall_status,
            'total_issues': total_issues,
            'high_severity': severity_counts['높음'],
            'medium_severity': severity_counts['중간'],
            'low_severity': severity_counts['낮음'],
            'mode': mode
        }
    
    def _generate_recommendations(self, results: List[Dict], mode: str) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        high_severity_count = sum(1 for r in results if r.get('severity') == '높음')
        
        if high_severity_count > 0:
            recommendations.append(f"⚠️ {high_severity_count}개의 높은 심각도 이슈가 발견되었습니다. 즉시 검토가 필요합니다.")
        
        
        spec_issues = [r for r in results if r.get('issue_type') == 'Spec Out']
        if spec_issues:
            recommendations.append("🎯 스펙 범위를 벗어난 파라미터들의 기본값을 조정하세요.")
        
        if mode == "checklist_only" and not results:
            recommendations.append("✅ 모든 중요 파라미터가 정상 상태입니다.")
        
        return recommendations

# 기존 중복 함수들을 대체하는 통합 함수
def perform_unified_qc_check(manager_instance, mode: str = "comprehensive"):
    """
    기존 perform_qc_check 함수들을 대체하는 통합 함수
    
    Args:
        manager_instance: DBManager 인스턴스
        mode: 검수 모드
    """
    if not hasattr(manager_instance, 'maint_mode') or not manager_instance.maint_mode:
        messagebox.showwarning("접근 제한", "QC 검수는 Maintenance Mode에서만 사용 가능합니다.")
        return
    
    # 장비 유형 선택 확인
    if not hasattr(manager_instance, 'qc_type_var') or not manager_instance.qc_type_var.get():
        messagebox.showinfo("알림", "장비 유형을 선택해주세요.")
        return
    
    try:
        # 장비 유형 ID 추출
        selected_type = manager_instance.qc_type_var.get()
        equipment_types = getattr(manager_instance, 'equipment_types_for_qc', {})
        equipment_type_id = equipment_types.get(selected_type)
        
        if not equipment_type_id:
            messagebox.showerror("오류", "유효하지 않은 장비 유형입니다.")
            return
        
        # 통합 QC 시스템 실행
        qc_system = UnifiedQCSystem(
            db_schema=manager_instance.db_schema,
            update_log_callback=getattr(manager_instance, 'update_log', None)
        )
        
        result = qc_system.perform_unified_qc_check(equipment_type_id, mode)
        
        if result['success']:
            # 결과를 UI에 표시
            _display_qc_results(manager_instance, result)
            
            # 상태에 따른 메시지
            status = result['summary']['overall_status']
            if status == 'PASS':
                messagebox.showinfo("QC 검수 완료", "모든 검사를 통과했습니다!")
            elif status == 'WARNING':
                messagebox.showwarning("QC 검수 완료", "일부 주의사항이 있습니다. 상세 결과를 확인하세요.")
            else:
                messagebox.showerror("QC 검수 완료", "검수 실패! 즉시 조치가 필요합니다.")
        else:
            messagebox.showerror("QC 검수 오류", result['message'])
    
    except Exception as e:
        messagebox.showerror("QC 검수 오류", f"예상치 못한 오류가 발생했습니다: {str(e)}")

def _display_qc_results(manager_instance, result: Dict):
    """QC 결과를 UI에 표시"""
    if not hasattr(manager_instance, 'qc_result_tree'):
        return
    
    # 기존 결과 지우기
    for item in manager_instance.qc_result_tree.get_children():
        manager_instance.qc_result_tree.delete(item)
    
    # 새 결과 표시
    for qc_result in result['detailed_results']:
        manager_instance.qc_result_tree.insert(
            "", "end",
            values=(
                qc_result.get('parameter', ''),
                qc_result.get('issue_type', ''),
                qc_result.get('description', ''),
                qc_result.get('severity', '')
            )
        )
    
    # 요약 정보 표시 (stats_frame이 있는 경우)
    if hasattr(manager_instance, 'stats_frame'):
        summary = result['summary']
        
        # 기존 위젯 정리
        for widget in manager_instance.stats_frame.winfo_children():
            widget.destroy()
        
        # 요약 정보 표시
        tk.Label(manager_instance.stats_frame, 
                text=f"전체 상태: {summary['overall_status']}", 
                font=('Arial', 12, 'bold')).pack(anchor='w')
        
        tk.Label(manager_instance.stats_frame, 
                text=f"총 이슈: {summary['total_issues']}개").pack(anchor='w')
        
        tk.Label(manager_instance.stats_frame, 
                text=f"높음: {summary['high_severity']}, 중간: {summary['medium_severity']}, 낮음: {summary['low_severity']}").pack(anchor='w')
        
        # 권장사항 표시
        if result.get('recommendations'):
            tk.Label(manager_instance.stats_frame, text="권장사항:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 0))
            for recommendation in result['recommendations']:
                tk.Label(manager_instance.stats_frame, text=f"• {recommendation}", wraplength=400).pack(anchor='w')