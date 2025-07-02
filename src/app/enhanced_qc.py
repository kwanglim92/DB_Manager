# Enhanced QC 기능 - Check list 모드 및 파일 선택 지원

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from .loading import LoadingDialog
from .utils import create_treeview_with_scrollbar
from .schema import DBSchema

class EnhancedQCValidator:
    """향상된 QC 검증 클래스 - Check list 모드 지원"""

    SEVERITY_LEVELS = {
        "높음": 3,
        "중간": 2,
        "낮음": 1
    }

    ISSUE_TYPES = {
        "data_quality": "데이터 품질",
        "checklist": "Check list 관련",
        "consistency": "일관성",
        "completeness": "완전성",
        "accuracy": "정확성"
    }

    @staticmethod
    def check_checklist_parameters(df, equipment_type):
        """Check list 파라미터 특별 검사 - 개선된 버전"""
        results = []
        
        if 'is_checklist' in df.columns:
            try:
                # is_checklist를 안전하게 숫자로 변환
                df_copy = df.copy()
                df_copy['is_checklist_numeric'] = pd.to_numeric(df_copy['is_checklist'], errors='coerce')
                checklist_params = df_copy[df_copy['is_checklist_numeric'] == 1]
                
                # Check list 파라미터의 신뢰도 검사 (더 엄격한 기준)
                if 'confidence_score' in df.columns and len(checklist_params) > 0:
                    try:
                        # confidence_score를 안전하게 숫자로 변환
                        checklist_params['confidence_score_numeric'] = pd.to_numeric(checklist_params['confidence_score'], errors='coerce')
                        low_checklist_confidence = checklist_params[checklist_params['confidence_score_numeric'] < 0.8]
                        
                        for _, row in low_checklist_confidence.iterrows():
                            confidence_val = row.get('confidence_score_numeric', 0)
                            if pd.notna(confidence_val):
                                results.append({
                                    "parameter": row['parameter_name'],
                                    "issue_type": "Check list 신뢰도 부족",
                                    "description": f"Check list 중요 파라미터의 신뢰도가 {confidence_val*100:.1f}%로 낮습니다 (권장: 80% 이상)",
                                    "severity": "높음",
                                    "category": "checklist",
                                    "recommendation": "더 많은 소스 파일에서 확인하거나 수동 검증이 필요합니다.",
                                    "default_value": row.get('default_value', 'N/A'),
                                    "file_value": "N/A",
                                    "pass_fail": "FAIL"
                                })
                    except Exception as confidence_error:
                        print(f"신뢰도 검사 중 오류: {confidence_error}")
                
                # Check list 파라미터의 사양 범위 누락 검사
                missing_specs = checklist_params[
                    (checklist_params['min_spec'].isna() | (checklist_params['min_spec'] == '')) |
                    (checklist_params['max_spec'].isna() | (checklist_params['max_spec'] == ''))
                ]
                for _, row in missing_specs.iterrows():
                    results.append({
                        "parameter": row['parameter_name'],
                        "issue_type": "Check list 사양 누락",
                        "description": f"Check list 중요 파라미터에 사양 범위(min/max)가 누락되었습니다",
                        "severity": "높음",
                        "category": "completeness",
                        "recommendation": "장비 매뉴얼을 참조하여 사양 범위를 추가하세요.",
                        "default_value": row.get('default_value', 'N/A'),
                        "file_value": "N/A",
                        "pass_fail": "FAIL"
                    })
            except Exception as e:
                print(f"Check list 파라미터 검사 중 오류: {e}")
        
        return results

    @staticmethod
    def check_checklist_with_file_comparison(checklist_df, file_df, equipment_type):
        """Check list 파라미터와 파일 데이터 비교 검사 - 단순화된 버전"""
        results = []
        
        if checklist_df.empty or file_df.empty:
            return results
        
        # Check list 파라미터만 필터링
        if 'is_checklist' in checklist_df.columns:
            try:
                checklist_df_copy = checklist_df.copy()
                checklist_df_copy['is_checklist_numeric'] = pd.to_numeric(checklist_df_copy['is_checklist'], errors='coerce')
                checklist_params = checklist_df_copy[checklist_df_copy['is_checklist_numeric'] == 1]
            except:
                checklist_params = checklist_df
        else:
            checklist_params = checklist_df
        
        for _, checklist_row in checklist_params.iterrows():
            param_name = checklist_row['parameter_name']
            default_value = str(checklist_row['default_value']).strip()
            min_spec = checklist_row.get('min_spec', '')
            max_spec = checklist_row.get('max_spec', '')
            
            # 파일에서 동일한 파라미터 찾기
            matching_params = pd.DataFrame()
            param_columns = ['Parameter', 'parameter', 'Item', 'item', 'Name', 'name', 'ItemName', 'Item Name']
            param_column = None
            
            for col in param_columns:
                if col in file_df.columns:
                    param_column = col
                    break
            
            if not param_column:
                # 파라미터 컬럼을 찾을 수 없음 - 누락
                results.append({
                    "parameter": param_name,
                    "issue_type": "누락",
                    "description": f"파일에서 파라미터 컬럼을 찾을 수 없습니다",
                    "severity": "높음",
                    "category": "completeness",
                    "recommendation": "파일 형식을 확인하세요",
                    "default_value": default_value,
                    "file_value": "N/A",
                    "pass_fail": "FAIL"
                })
                continue
            
            # 파라미터명으로 매칭 시도
            try:
                matching_params = file_df[file_df[param_column].str.contains(param_name, case=False, na=False)]
            except:
                matching_params = file_df[file_df[param_column] == param_name]
            
            if matching_params.empty:
                # 파라미터가 파일에 없음 - 누락
                results.append({
                    "parameter": param_name,
                    "issue_type": "누락",
                    "description": f"파일에서 '{param_name}' 파라미터를 찾을 수 없습니다",
                    "severity": "높음",
                    "category": "completeness",
                    "recommendation": "파라미터가 파일에 포함되어 있는지 확인하세요",
                    "default_value": default_value,
                    "file_value": "N/A",
                    "pass_fail": "FAIL"
                })
                continue
            
            # 파라미터가 발견된 경우 값 비교
            for _, file_row in matching_params.iterrows():
                # 파일 값 추출
                value_columns = ['Value', 'value', 'Data', 'data', 'Setting', 'setting', 'Val', 'ItemValue']
                file_value = 'N/A'
                
                for val_col in value_columns:
                    if val_col in file_row.index and pd.notna(file_row[val_col]):
                        file_value = str(file_row[val_col]).strip()
                        break
                
                if file_value == 'N/A':
                    # 값을 찾을 수 없음 - 누락
                    results.append({
                        "parameter": param_name,
                        "issue_type": "누락",
                        "description": f"파라미터는 있지만 값이 없습니다",
                        "severity": "높음",
                        "category": "completeness",
                        "recommendation": "파라미터 값을 확인하세요",
                        "default_value": default_value,
                        "file_value": "N/A",
                        "pass_fail": "FAIL"
                    })
                    continue
                
                # 값 비교 및 Pass/Fail 판정
                issue_type = ""
                pass_fail = "PASS"
                description = ""
                severity = "낮음"
                
                # 1. Min/Max 범위 검사 (있는 경우)
                has_spec_range = (min_spec and str(min_spec).strip() and min_spec != 'N/A' and 
                                max_spec and str(max_spec).strip() and max_spec != 'N/A')
                
                if has_spec_range:
                    try:
                        file_num = float(str(file_value).replace(',', ''))
                        min_num = float(str(min_spec).replace(',', ''))
                        max_num = float(str(max_spec).replace(',', ''))
                        
                        if not (min_num <= file_num <= max_num):
                            # 범위를 벗어남 - Spec Out
                            issue_type = "Spec Out"
                            pass_fail = "FAIL"
                            description = f"파일 값이 허용 범위를 벗어났습니다 (허용: {min_spec}~{max_spec})"
                            severity = "높음"
                        else:
                            # 범위 내에 있음 - Default Value와 비교
                            if default_value == file_value:
                                # 완전히 일치 - PASS
                                issue_type = ""
                                pass_fail = "PASS"
                                description = f"✅ 기준값과 일치하며 범위 내에 있습니다"
                                severity = "낮음"
                            else:
                                # 범위 내이지만 기준값과 다름 - 기준값 Out
                                issue_type = "기준값 Out"
                                pass_fail = "FAIL"
                                description = f"범위 내이지만 기준값과 다릅니다"
                                severity = "중간"
                        
                    except (ValueError, TypeError):
                        # 숫자 변환 실패 - 문자열로 비교
                        if default_value == file_value:
                            issue_type = ""
                            pass_fail = "PASS"
                            description = f"✅ 기준값과 일치합니다"
                            severity = "낮음"
                        else:
                            issue_type = "기준값 Out"
                            pass_fail = "FAIL"
                            description = f"기준값과 다릅니다"
                            severity = "중간"
                else:
                    # Min/Max 범위가 없는 경우 - Default Value와만 비교
                    if default_value == file_value:
                        issue_type = ""
                        pass_fail = "PASS"
                        description = f"✅ 기준값과 일치합니다"
                        severity = "낮음"
                    else:
                        issue_type = "기준값 Out"
                        pass_fail = "FAIL"
                        description = f"기준값과 다릅니다"
                        severity = "중간"
                
                # 결과 추가
                results.append({
                    "parameter": param_name,
                    "issue_type": issue_type,
                    "description": description,
                    "severity": severity,
                    "category": "consistency" if issue_type == "기준값 Out" else "accuracy" if issue_type == "Spec Out" else "pass",
                    "recommendation": "수정이 필요합니다" if pass_fail == "FAIL" else "문제없음",
                    "default_value": default_value,
                    "file_value": file_value,
                    "pass_fail": pass_fail
                })
        
        return results

    @staticmethod
    def check_data_trends(df, equipment_type):
        """데이터 트렌드 분석 - 새로운 고급 검사"""
        results = []
        
        # 모듈별 파라미터 분포 분석
        if 'module_name' in df.columns and 'parameter_name' in df.columns:
            module_counts = df['module_name'].value_counts()
            
            # 파라미터가 너무 적은 모듈 찾기
            low_param_modules = module_counts[module_counts < 3]
            for module, count in low_param_modules.items():
                results.append({
                    "parameter": f"모듈: {module}",
                    "issue_type": "모듈 파라미터 부족",
                    "description": f"'{module}' 모듈에 파라미터가 {count}개만 있습니다 (권장: 3개 이상)",
                    "severity": "낮음",
                    "category": "completeness",
                    "recommendation": "해당 모듈의 추가 파라미터를 확인하세요.",
                    "default_value": "N/A",
                    "file_value": "N/A",
                    "pass_fail": "CHECK"
                })
        
        # 파트별 분석
        if 'part_name' in df.columns:
            part_counts = df['part_name'].value_counts()
            
            # 파라미터가 너무 많은 파트 찾기 (잠재적 중복)
            high_param_parts = part_counts[part_counts > 20]
            for part, count in high_param_parts.items():
                results.append({
                    "parameter": f"파트: {part}",
                    "issue_type": "파트 파라미터 과다",
                    "description": f"'{part}' 파트에 파라미터가 {count}개로 많습니다 (검토 권장: 20개 초과)",
                    "severity": "낮음",
                    "category": "consistency",
                    "recommendation": "중복되거나 불필요한 파라미터가 있는지 검토하세요.",
                    "default_value": "N/A",
                    "file_value": "N/A",
                    "pass_fail": "CHECK"
                })
        
        return results


    @staticmethod
    def check_value_ranges(df, equipment_type):
        """값 범위 고급 분석 - 새로운 검사"""
        results = []
        
        if all(col in df.columns for col in ['min_spec', 'max_spec', 'default_value']):
            for _, row in df.iterrows():
                try:
                    if pd.notna(row['min_spec']) and pd.notna(row['max_spec']) and pd.notna(row['default_value']):
                        min_val = float(row['min_spec'])
                        max_val = float(row['max_spec'])
                        default_val = float(row['default_value'])
                        
                        # 범위가 너무 넓은 경우
                        range_ratio = (max_val - min_val) / abs(default_val) if default_val != 0 else float('inf')
                        if range_ratio > 10:  # 기본값 대비 범위가 10배 이상
                            results.append({
                                "parameter": row['parameter_name'],
                                "issue_type": "범위 과도",
                                "description": f"사양 범위가 기본값 대비 너무 넓습니다 (범위: {min_val}~{max_val}, 기본값: {default_val})",
                                "severity": "낮음",
                                "category": "accuracy",
                                "recommendation": "사양 범위가 적절한지 검토하세요."
                            })
                        
                        # 기본값이 범위의 중앙에서 너무 치우친 경우
                        if max_val != min_val:
                            center_position = (default_val - min_val) / (max_val - min_val)
                            if center_position < 0.1 or center_position > 0.9:
                                results.append({
                                    "parameter": row['parameter_name'],
                                    "issue_type": "기본값 위치 부적절",
                                    "description": f"기본값이 사양 범위의 {'하한' if center_position < 0.1 else '상한'}에 치우쳐 있습니다",
                                    "severity": "낮음",
                                    "category": "accuracy",
                                    "recommendation": "기본값을 범위의 중앙 근처로 조정하는 것을 고려하세요."
                                })
                        
                except (ValueError, TypeError, ZeroDivisionError):
                    continue
        
        return results

    @staticmethod
    def run_enhanced_checks(df, equipment_type, is_checklist_mode=False, file_df=None):
        """개선된 QC 검사 실행 - 파일 비교 기능 포함"""
        from .qc import QCValidator
        
        enhanced_results = []
        
        # Check list 모드에서는 파일이 반드시 필요
        if is_checklist_mode:
            if file_df is None:
                # Check list 모드에서 파일이 없으면 오류 결과 반환
                return [{
                    "parameter": "파일 비교 오류",
                    "default_value": "N/A",
                    "file_value": "파일 없음",
                    "pass_fail": "FAIL",
                    "issue_type": "파일 누락",
                    "description": "Check list 검수 모드에서는 비교할 파일이 필요합니다.",
                    "severity": "높음",
                    "category": "system_error",
                    "recommendation": "📁 파일 선택 버튼을 사용하여 검수할 파일을 선택해주세요."
                }]
            
            # Check list 모드: 파일과 Default DB 비교 검사
            enhanced_results.extend(
                EnhancedQCValidator.check_checklist_with_file_comparison(df, file_df, equipment_type)
            )
        else:
            # 전체 검수 모드: 기본 검사 실행 (파일 없이도 가능)
            all_results = QCValidator.run_all_checks(df, equipment_type)
            
            # 기존 결과에 category와 recommendation 추가
            for result in all_results:
                if 'category' not in result:
                    result['category'] = 'data_quality'
                if 'recommendation' not in result:
                    result['recommendation'] = '상세 검토가 필요합니다.'
                # 새로운 필드 추가
                if 'default_value' not in result:
                    result['default_value'] = 'N/A'
                if 'file_value' not in result:
                    result['file_value'] = 'N/A'
                if 'pass_fail' not in result:
                    result['pass_fail'] = 'CHECK'
            
            enhanced_results.extend(all_results)
            
            # 전체 검수 모드: 모든 향상된 검사 수행
            enhanced_results.extend(EnhancedQCValidator.check_checklist_parameters(df, equipment_type))
            enhanced_results.extend(EnhancedQCValidator.check_data_trends(df, equipment_type))

        # 심각도 순으로 정렬
        enhanced_results.sort(key=lambda x: EnhancedQCValidator.SEVERITY_LEVELS.get(x["severity"], 0), reverse=True)

        return enhanced_results

    @staticmethod
    def generate_qc_summary(results):
        """QC 검수 요약 정보 생성"""
        if not results:
            return {
                "total_issues": 0,
                "severity_breakdown": {"높음": 0, "중간": 0, "낮음": 0},
                "category_breakdown": {},
                "recommendations": [],
                "overall_score": 100
            }
        
        # 심각도별 분류
        severity_breakdown = {"높음": 0, "중간": 0, "낮음": 0}
        for result in results:
            severity = result.get("severity", "낮음")
            severity_breakdown[severity] += 1
        
        # 카테고리별 분류
        category_breakdown = {}
        for result in results:
            category = result.get("category", "data_quality")
            category_name = EnhancedQCValidator.ISSUE_TYPES.get(category, category)
            category_breakdown[category_name] = category_breakdown.get(category_name, 0) + 1
        
        # 주요 권장사항 수집
        recommendations = []
        for result in results:
            if result.get("severity") == "높음" and result.get("recommendation"):
                recommendations.append(result["recommendation"])
        recommendations = list(set(recommendations))[:5]  # 중복 제거 후 최대 5개
        
        # 전체 점수 계산 (100점 만점)
        total_issues = len(results)
        high_weight = severity_breakdown["높음"] * 10
        medium_weight = severity_breakdown["중간"] * 5
        low_weight = severity_breakdown["낮음"] * 2
        
        penalty = min(high_weight + medium_weight + low_weight, 100)
        overall_score = max(0, 100 - penalty)
        
        return {
            "total_issues": total_issues,
            "severity_breakdown": severity_breakdown,
            "category_breakdown": category_breakdown,
            "recommendations": recommendations,
            "overall_score": overall_score
        }


def add_enhanced_qc_functions_to_class(cls):
    """
    DBManager 클래스에 향상된 QC 검수 기능을 추가합니다.
    """
    
    def create_enhanced_qc_tab(self):
        """향상된 QC 검수 탭 생성 - 새로운 QCTabController 사용"""
        try:
            # 새로운 QCTabController 사용
            from app.ui.controllers.tab_controllers.qc_tab_controller import QCTabController
            
            # QC 탭 프레임 생성
            qc_tab = ttk.Frame(self.main_notebook)
            self.main_notebook.add(qc_tab, text="QC 검수")
            
            # QCTabController 인스턴스 생성 및 초기화
            self.qc_tab_controller = QCTabController(qc_tab, self)
            
            # 컨트롤러 참조 저장 (나중에 사용하기 위해)
            self.qc_check_frame = qc_tab
            
            self.update_log("✅ 새로운 QC 탭 컨트롤러로 탭이 생성되었습니다.")
            return
            
        except ImportError as e:
            self.update_log(f"⚠️ QCTabController 로드 실패, 기존 방식 사용: {e}")
        except Exception as e:
            self.update_log(f"❌ QCTabController 생성 실패, 기존 방식 사용: {e}")
        
        # 기존 방식으로 폴백
        self._create_legacy_qc_tab()
    
    def _create_legacy_qc_tab(self):
        """기존 방식의 QC 탭 생성 (폴백용)"""
        qc_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(qc_tab, text="QC 검수 (기존)")

        # 🎨 상단 컨트롤 패널 - 향상된 디자인
        control_panel = ttk.Frame(qc_tab)
        control_panel.pack(fill=tk.X, padx=10, pady=10)

        # 장비 유형 선택 프레임
        type_frame = ttk.LabelFrame(control_panel, text="🔧 장비 유형 설정", padding=10)
        type_frame.pack(fill=tk.X, pady=(0, 5))

        # 장비 유형 선택 라인
        equipment_line = ttk.Frame(type_frame)
        equipment_line.pack(fill=tk.X)

        # 장비 유형 콤보박스
        ttk.Label(equipment_line, text="장비 유형:").pack(side=tk.LEFT, padx=(0, 5))
        self.qc_type_var = tk.StringVar()
        self.qc_type_combobox = ttk.Combobox(equipment_line, textvariable=self.qc_type_var, state="readonly", width=25)
        self.qc_type_combobox.pack(side=tk.LEFT, padx=(0, 10))
        
        # 새로고침 버튼
        refresh_btn = ttk.Button(equipment_line, text="🔄 새로고침", command=self.refresh_qc_equipment_types)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 검수 모드 선택 프레임
        mode_frame = ttk.LabelFrame(control_panel, text="📋 검수 모드", padding=10)
        mode_frame.pack(fill=tk.X, pady=(0, 5))

        # 검수 모드 선택
        mode_line = ttk.Frame(mode_frame)
        mode_line.pack(fill=tk.X)

        ttk.Label(mode_line, text="검수 모드:").pack(side=tk.LEFT, padx=(0, 5))
        self.qc_mode_var = tk.StringVar(value="checklist")
        
        def on_mode_change(*args):
            """검수 모드 변경 시 상태 메시지 업데이트"""
            mode = self.qc_mode_var.get()
            if mode == "checklist":
                self.qc_status_label.config(
                    text="📋 Check list 모드 - 파일 선택 후 검수 가능", 
                    foreground='blue'
                )
            else:
                self.qc_status_label.config(
                    text="📋 전체 검수 모드 - 파일 없이도 검수 가능", 
                    foreground='blue'
                )
        
        checklist_radio = ttk.Radiobutton(mode_line, text="⭐ Check list 중점", 
                                          variable=self.qc_mode_var, value="checklist",
                                          command=on_mode_change)
        checklist_radio.pack(side=tk.LEFT, padx=(0, 15))
        
        full_radio = ttk.Radiobutton(mode_line, text="📋 전체 검수", 
                                   variable=self.qc_mode_var, value="full",
                                   command=on_mode_change)
        full_radio.pack(side=tk.LEFT, padx=(0, 10))
        
        # 실행 버튼 프레임 - 행으로 나열
        action_frame = ttk.LabelFrame(control_panel, text="🚀 검수 실행", padding=10)
        action_frame.pack(fill=tk.X, pady=(0, 5))

        # 버튼들을 행으로 나열
        button_line = ttk.Frame(action_frame)
        button_line.pack(fill=tk.X)

        # 검수 파일 선택 버튼
        file_select_btn = ttk.Button(button_line, text="📁 검수 파일 선택", command=self.select_qc_files)
        file_select_btn.pack(side=tk.LEFT, padx=(0, 10))

        # QC 실행 버튼
        self.qc_btn = ttk.Button(button_line, text="🔍 QC 검수 실행", command=self.perform_enhanced_qc_check)
        self.qc_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Excel 내보내기 버튼
        export_btn = ttk.Button(button_line, text="📤 Excel 내보내기", command=self.export_qc_results_simple)
        export_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 🎨 메인 결과 영역 - 탭 구조로 개선
        main_frame = ttk.Frame(qc_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 결과 탭 노트북
        self.qc_results_notebook = ttk.Notebook(main_frame)
        self.qc_results_notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: QC Results List
        results_tab = ttk.Frame(self.qc_results_notebook)
        self.qc_results_notebook.add(results_tab, text="QC Results")

        # Professional QC Results TreeView - 개선된 컬럼 구조
        columns = ("itemname", "default_value", "file_value", "pass_fail", "issue_type", "description")
        headings = {
            "itemname": "ItemName", 
            "default_value": "Default Value",
            "file_value": "File Value",
            "pass_fail": "Pass/Fail",
            "issue_type": "Issue Type", 
            "description": "Description"
        }
        column_widths = {
            "itemname": 200, 
            "default_value": 120,
            "file_value": 120,
            "pass_fail": 80,
            "issue_type": 150, 
            "description": 300
        }

        results_frame, self.qc_result_tree = create_treeview_with_scrollbar(
            results_tab, columns, headings, column_widths, height=12)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 탭 2: 통계 및 요약
        stats_tab = ttk.Frame(self.qc_results_notebook)
        self.qc_results_notebook.add(stats_tab, text="📊 통계 요약")

        # 통계 요약 영역
        self.stats_summary_frame = ttk.Frame(stats_tab)
        self.stats_summary_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 탭 3: 시각화
        chart_tab = ttk.Frame(self.qc_results_notebook)
        self.qc_results_notebook.add(chart_tab, text="📈 시각화")

        self.chart_container = ttk.Frame(chart_tab)
        self.chart_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 🎨 하단 상태 표시줄
        status_frame = ttk.Frame(qc_tab)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.qc_status_label = ttk.Label(status_frame, text="📋 Check list 모드 - 파일 선택 후 검수 가능", 
                                        font=('Arial', 9), foreground='blue')
        self.qc_status_label.pack(side=tk.LEFT)

        self.qc_progress = ttk.Progressbar(status_frame, mode='determinate', length=200)
        self.qc_progress.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 초기 데이터 로드
        self.load_equipment_types_for_qc()
    
    def select_qc_files(self):
        """QC 검수를 위한 파일 선택 (업로드된 파일 중에서 선택)"""
        try:
            from .qc_utils import QCFileSelector
            
            # 업로드된 파일 목록 확인
            uploaded_files = getattr(self, 'uploaded_files', {})
            
            # 파일 선택 다이얼로그 표시
            selected_files = QCFileSelector.create_file_selection_dialog(
                self.window, uploaded_files, max_files=6
            )
            
            if selected_files:
                self.selected_qc_files = selected_files
                file_list = '\n'.join([f"• {name}" for name in selected_files.keys()])
                messagebox.showinfo(
                    "파일 선택 완료", 
                    f"QC 검수용으로 {len(selected_files)}개 파일이 선택되었습니다.\n\n"
                    f"선택된 파일:\n{file_list}\n\n"
                    f"이제 '🔍 QC 검수 실행' 버튼을 클릭하여 검수를 시작하세요."
                )
                self.update_log(f"[파일 선택] QC 검수 대상 파일 {len(selected_files)}개 선택 완료")
            
        except Exception as e:
            error_msg = f"파일 선택 중 오류 발생: {str(e)}"
            messagebox.showerror("오류", error_msg)
            self.update_log(f"❌ {error_msg}")

    def perform_enhanced_qc_check(self):
        """향상된 QC 검수 실행 (Check list 모드 지원) - 개선된 버전"""
        selected_type = self.qc_type_var.get()
        qc_mode = getattr(self, 'qc_mode_var', None)
        
        if not selected_type:
            messagebox.showinfo("알림", "장비 유형을 선택해주세요.")
            return

        # Check list 모드인지 확인
        is_checklist_mode = qc_mode and qc_mode.get() == "checklist"
        
        # Check list 모드 요구사항 검증
        selected_files = getattr(self, 'selected_qc_files', {})
        from .qc_utils import QCDataProcessor
        
        validation_result, error_msg = QCDataProcessor.validate_checklist_mode_requirements(
            is_checklist_mode, selected_files
        )
        
        if not validation_result:
            messagebox.showwarning("검수 요구사항 미충족", error_msg)
            self.qc_status_label.config(text="❗ 요구사항 미충족", foreground='red')
            return

        try:
            # 메모리 사용량 체크
            try:
                import psutil
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 85:
                    if not messagebox.askyesno(
                        "메모리 사용량 높음", 
                        f"현재 시스템 메모리 사용률이 {memory_percent:.1f}%입니다.\n"
                        "QC 검수 중 메모리 부족이 발생할 수 있습니다.\n"
                        "계속하시겠습니까?"
                    ):
                        return
            except ImportError:
                pass  # psutil이 없어도 계속 진행
            
            # 로딩 대화상자 표시
            loading_dialog = LoadingDialog(self.window)
            self.window.update_idletasks()
            
            # 상태 업데이트
            mode_text = "Check list 중점" if is_checklist_mode else "전체 검수"
            self.qc_status_label.config(text=f"🔄 QC 검수 진행 중... ({mode_text})", foreground='orange')
            self.qc_progress.config(value=10)

            # 트리뷰 초기화
            for item in self.qc_result_tree.get_children():
                self.qc_result_tree.delete(item)

            # 통계 및 차트 프레임 초기화
            for widget in self.stats_summary_frame.winfo_children():
                widget.destroy()
            for widget in self.chart_container.winfo_children():
                widget.destroy()

            # 선택된 장비 유형의 데이터 로드
            equipment_type_id = getattr(self, 'equipment_types_for_qc', {}).get(selected_type)
            if not equipment_type_id:
                loading_dialog.close()
                messagebox.showwarning("경고", f"장비 유형 '{selected_type}'의 ID를 찾을 수 없습니다.")
                return
            
            # Check list 모드는 앞에서 이미 설정됨 - 중복 설정 제거
            
            # DB 스키마 인스턴스를 통해 데이터 로드
            if hasattr(self, 'db_schema') and self.db_schema:
                data = self.db_schema.get_default_values(equipment_type_id, checklist_only=is_checklist_mode)
            else:
                from .schema import DBSchema
                db_schema = DBSchema()
                data = db_schema.get_default_values(equipment_type_id, checklist_only=is_checklist_mode)

            if not data:
                loading_dialog.close()
                mode_text = "Check list 항목" if is_checklist_mode else "전체 항목"
                messagebox.showinfo("알림", f"장비 유형 '{selected_type}'에 대한 {mode_text} 검수할 데이터가 없습니다.")
                self.qc_status_label.config(text="📋 QC 검수 대기 중...", foreground='blue')
                self.qc_progress.config(value=0)
                return

            # 데이터프레임 생성
            loading_dialog.update_progress(30, "데이터 분석 중...")
            self.qc_progress.config(value=30)
            
            # 안전한 데이터프레임 생성
            from .qc_utils import QCDataProcessor, QC_COLUMN_MAPPINGS
            
            df, df_error = QCDataProcessor.create_safe_dataframe(data, QC_COLUMN_MAPPINGS['DEFAULT_DB_COLUMNS'])
            
            if df is None:
                loading_dialog.close()
                messagebox.showerror("데이터 처리 오류", df_error)
                self.update_log(f"❌ DataFrame 생성 오류: {df_error}")
                return
            
            self.update_log(f"[DEBUG] 로드된 데이터: {len(df)}행, 컬럼: {list(df.columns)}")

            # 향상된 QC 검사 실행
            loading_dialog.update_progress(50, "향상된 QC 검사 실행 중...")
            self.qc_progress.config(value=50)
            
            # Check list 모드일 때 파일 데이터 준비
            file_df = None
            if is_checklist_mode:
                file_df, file_error = QCDataProcessor.extract_file_data(selected_files)
                if file_df is None:
                    self.update_log(f"[DEBUG] 파일 데이터 추출 실패: {file_error}")
                else:
                    self.update_log(f"[DEBUG] 파일 데이터 준비 완료: {len(file_df)}행, 컬럼: {list(file_df.columns)}")
            
            # QC 검사 실행
            try:
                self.update_log(f"[DEBUG] QC 검사 시작 - Check list 모드: {is_checklist_mode}, 파일 데이터: {'있음' if file_df is not None else '없음'}")
                
                results = EnhancedQCValidator.run_enhanced_checks(
                    df, selected_type, 
                    is_checklist_mode=is_checklist_mode, 
                    file_df=file_df
                )
                
                self.update_log(f"[DEBUG] QC 검사 완료 - 결과: {len(results)}개")
                
            except Exception as qc_error:
                loading_dialog.close()
                error_msg = f"QC 검사 실행 오류: {str(qc_error)}"
                messagebox.showerror("QC 검사 오류", error_msg)
                self.update_log(f"❌ QC 검사 오류: {error_msg}")
                return

            # 결과 트리뷰에 표시 (대량 데이터 처리 개선)
            loading_dialog.update_progress(75, "결과 업데이트 중...")
            self.qc_progress.config(value=75)
            
            # 대량 데이터인 경우 배치 처리
            batch_size = 50  # 한 번에 50개씩 처리
            total_results = len(results)
            
            try:
                for i in range(0, total_results, batch_size):
                    batch = results[i:i+batch_size]
                    
                    for result in batch:
                        # Pass/Fail에 따른 색상 태그 설정
                        pass_fail = result.get("pass_fail", "CHECK")
                        tag = f"status_{pass_fail.lower()}"
                        
                        self.qc_result_tree.insert(
                            "", "end", 
                            values=(
                                result.get("parameter", ""),
                                result.get("default_value", "N/A"),
                                result.get("file_value", "N/A"),
                                pass_fail,
                                result.get("issue_type", ""),
                                result.get("description", "")
                            ),
                            tags=(tag,)
                        )
                    
                    # 배치 처리 후 UI 업데이트
                    if total_results > batch_size:
                        self.window.update_idletasks()
                        progress = 75 + (i / total_results) * 15  # 75~90% 사이
                        self.qc_progress.config(value=progress)
                        
            except Exception as display_error:
                # 표시 중 오류 발생 시에도 일부 결과는 보여줌
                self.update_log(f"[WARNING] 일부 결과 표시 중 오류: {display_error}")
                messagebox.showwarning(
                    "표시 경고", 
                    f"일부 결과 표시 중 오류가 발생했습니다.\n"
                    f"표시된 결과: {len(self.qc_result_tree.get_children())}개\n"
                    f"전체 결과: {total_results}개"
                )

            # 트리뷰 태그 색상 설정 - Pass/Fail 기준
            self.qc_result_tree.tag_configure("status_pass", background="#e8f5e8", foreground="#2e7d32")  # 녹색
            self.qc_result_tree.tag_configure("status_fail", background="#ffebee", foreground="#c62828")  # 빨간색
            self.qc_result_tree.tag_configure("status_check", background="#fff3e0", foreground="#ef6c00")  # 주황색

            # 통계 정보 표시
            loading_dialog.update_progress(90, "통계 정보 생성 중...")
            self.qc_progress.config(value=90)
            
            self.show_enhanced_qc_statistics(results, is_checklist_mode)

            # 완료
            loading_dialog.update_progress(100, "완료")
            loading_dialog.close()
            
            # 상태 업데이트
            mode_text = "Check list 중점" if is_checklist_mode else "전체"
            self.qc_status_label.config(
                text=f"✅ QC 검수 완료 ({mode_text}) - {len(results)}개 이슈 발견", 
                foreground='green'
            )
            self.qc_progress.config(value=100)

            # 로그 업데이트
            self.update_log(f"[Enhanced QC] 장비 유형 '{selected_type}' ({mode_text})에 대한 향상된 QC 검수가 완료되었습니다. 총 {len(results)}개의 이슈 발견.")

        except Exception as e:
            if 'loading_dialog' in locals():
                loading_dialog.close()
            
            error_msg = f"QC 검수 중 오류 발생: {str(e)}"
            messagebox.showerror("오류", error_msg)
            self.update_log(f"❌ Enhanced QC 오류: {error_msg}")
            
            # 상태 초기화
            self.qc_status_label.config(text="❌ QC 검수 실패", foreground='red')
            self.qc_progress.config(value=0)

    def export_qc_results_simple(self):
        """간단한 QC 결과 내보내기 - 공통 유틸리티 사용"""
        try:
            from .qc_utils import QCResultExporter
            
            # 결과가 있는지 확인
            if not self.qc_result_tree.get_children():
                messagebox.showinfo("알림", "내보낼 QC 결과가 없습니다.")
                return
            
            # 트리뷰에서 결과 데이터 수집
            results = []
            for item in self.qc_result_tree.get_children():
                values = self.qc_result_tree.item(item)['values']
                results.append({
                    'parameter': values[0],        # itemname
                    'default_value': values[1],    # default_value
                    'file_value': values[2],       # file_value
                    'pass_fail': values[3],        # pass_fail
                    'issue_type': values[4],       # issue_type
                    'description': values[5],      # description
                    'severity': 'N/A',             # 트리뷰에는 없지만 내보내기용
                    'recommendation': 'N/A'        # 트리뷰에는 없지만 내보내기용
                })
            
            # 공통 내보내기 함수 사용
            if QCResultExporter.export_results_to_file(results, "qc_enhanced_results"):
                self.update_log(f"[QC] Enhanced QC 검수 결과 내보내기 완료")
            
        except Exception as e:
            from .qc_utils import QCErrorHandler
            error_msg = QCErrorHandler.handle_file_error(e, "QC 검수 결과")
            self.update_log(f"❌ {error_msg}")

    def show_enhanced_qc_statistics(self, results, is_checklist_mode=False):
        """향상된 QC 통계 정보 표시"""
        # 통계 요약 생성
        summary = EnhancedQCValidator.generate_qc_summary(results)
        
        # 기존 위젯 제거
        for widget in self.stats_summary_frame.winfo_children():
            widget.destroy()
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        # 🎨 요약 카드 스타일 프레임들
        # 전체 점수 카드
        score_frame = ttk.LabelFrame(self.stats_summary_frame, text="🏆 전체 QC 점수", padding=15)
        score_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        score_color = "green" if summary["overall_score"] >= 80 else "orange" if summary["overall_score"] >= 60 else "red"
        score_label = ttk.Label(score_frame, text=f"{summary['overall_score']:.0f}점", 
                               font=('Arial', 24, 'bold'), foreground=score_color)
        score_label.pack()
        
        score_desc = "우수" if summary["overall_score"] >= 80 else "보통" if summary["overall_score"] >= 60 else "개선 필요"
        ttk.Label(score_frame, text=f"({score_desc})", font=('Arial', 12)).pack()

        # 이슈 요약 카드
        issues_frame = ttk.LabelFrame(self.stats_summary_frame, text="📊 이슈 요약", padding=15)
        issues_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(issues_frame, text=f"총 이슈: {summary['total_issues']}개", 
                 font=('Arial', 12, 'bold')).pack(anchor='w')
        
        for severity, count in summary['severity_breakdown'].items():
            if count > 0:
                color = "#c62828" if severity == "높음" else "#ef6c00" if severity == "중간" else "#7b1fa2"
                label = ttk.Label(issues_frame, text=f"• {severity}: {count}개", 
                                 font=('Arial', 10), foreground=color)
                label.pack(anchor='w')

        # 카테고리 분석 카드
        category_frame = ttk.LabelFrame(self.stats_summary_frame, text="📋 카테고리별 분석", padding=15)
        category_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        for category, count in summary['category_breakdown'].items():
            ttk.Label(category_frame, text=f"• {category}: {count}개", 
                     font=('Arial', 10)).pack(anchor='w')

        # 🎨 시각화 차트들
        if results:
            self.create_enhanced_charts(summary, is_checklist_mode)

        # 권장사항 표시 (하단)
        if summary['recommendations']:
            recommendations_frame = ttk.LabelFrame(self.stats_summary_frame, text="💡 주요 권장사항", padding=10)
            recommendations_frame.pack(fill=tk.X, pady=(10, 0))
            
            for i, rec in enumerate(summary['recommendations'][:3], 1):
                ttk.Label(recommendations_frame, text=f"{i}. {rec}", 
                         font=('Arial', 9), wraplength=400).pack(anchor='w', pady=2)

    def create_enhanced_charts(self, summary, is_checklist_mode=False):
        """향상된 차트 생성"""
        try:
            # matplotlib 한글 폰트 설정
            plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 차트 컨테이너 프레임
            chart_frame = ttk.Frame(self.chart_container)
            chart_frame.pack(fill=tk.BOTH, expand=True)
            
            # Figure 생성 (2x2 서브플롯)
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle('QC 검수 결과 분석', fontsize=16, fontweight='bold')
            
            # 1. 심각도별 파이차트
            severity_data = summary['severity_breakdown']
            if any(severity_data.values()):
                colors1 = ['#f44336', '#ff9800', '#9c27b0']
                labels1 = list(severity_data.keys())
                sizes1 = list(severity_data.values())
                
                ax1.pie(sizes1, labels=labels1, colors=colors1, autopct='%1.1f%%', startangle=90)
                ax1.set_title('심각도별 이슈 분포')
            else:
                ax1.text(0.5, 0.5, 'No Issues Found', ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('심각도별 이슈 분포')
            
            # 2. 카테고리별 막대차트
            category_data = summary['category_breakdown']
            if category_data:
                categories = list(category_data.keys())
                counts = list(category_data.values())
                
                bars = ax2.bar(categories, counts, color=['#2196f3', '#4caf50', '#ff9800', '#9c27b0', '#f44336'])
                ax2.set_title('카테고리별 이슈 분포')
                ax2.set_ylabel('이슈 수')
                
                # 막대 위에 숫자 표시
                for bar, count in zip(bars, counts):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                            str(count), ha='center', va='bottom')
                
                # x축 라벨 회전
                plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
            else:
                ax2.text(0.5, 0.5, 'No Issues Found', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('카테고리별 이슈 분포')
            
            # 3. QC 점수 게이지 차트 (간단한 막대로 표현)
            score = summary['overall_score']
            colors = ['red' if score < 60 else 'orange' if score < 80 else 'green']
            ax3.barh(['QC 점수'], [score], color=colors)
            ax3.set_xlim(0, 100)
            ax3.set_xlabel('점수')
            ax3.set_title(f'전체 QC 점수: {score:.0f}점')
            
            # 점수 텍스트 표시
            ax3.text(score/2, 0, f'{score:.0f}점', ha='center', va='center', 
                    fontweight='bold', fontsize=12, color='white')
            
            # 4. 성능 모드 정보 (텍스트)
            mode_text = "Check list 중점 검수" if is_checklist_mode else "전체 항목 검수"
            total_issues = summary['total_issues']
            
            info_text = f"""검수 모드: {mode_text}
총 이슈 수: {total_issues}개
높은 심각도: {severity_data.get('높음', 0)}개
중간 심각도: {severity_data.get('중간', 0)}개
낮은 심각도: {severity_data.get('낮음', 0)}개

품질 등급: {'우수' if score >= 80 else '보통' if score >= 60 else '개선 필요'}"""
            
            ax4.text(0.1, 0.9, info_text, transform=ax4.transAxes, fontsize=10, 
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis('off')
            ax4.set_title('검수 정보 요약')
            
            # 레이아웃 조정
            plt.tight_layout()
            
            # Tkinter에 차트 삽입
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            # 차트 생성 실패 시 텍스트로 대체
            error_label = ttk.Label(self.chart_container, 
                                  text=f"차트 생성 중 오류 발생: {str(e)}\n\n기본 통계 정보는 '통계 요약' 탭에서 확인하세요.",
                                  font=('Arial', 10), foreground='red')
            error_label.pack(pady=20)

    def _create_new_template(self):
        """새 QC 템플릿 생성"""
        try:
            from .qc_templates import QCTemplate, QCCheckOptions
            
            # 템플릿 생성 다이얼로그
            dialog = tk.Toplevel(self.window)
            dialog.title("새 QC 템플릿 생성")
            dialog.geometry("500x600")
            dialog.transient(self.window)
            dialog.grab_set()
            
            # 기본 정보 입력
            info_frame = ttk.LabelFrame(dialog, text="기본 정보", padding=10)
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(info_frame, text="템플릿명:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            name_var = tk.StringVar()
            ttk.Entry(info_frame, textvariable=name_var, width=30).grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(info_frame, text="설명:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
            desc_var = tk.StringVar()
            ttk.Entry(info_frame, textvariable=desc_var, width=30).grid(row=1, column=1, padx=5, pady=5)
            
            ttk.Label(info_frame, text="타입:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
            type_var = tk.StringVar(value="custom")
            type_combo = ttk.Combobox(info_frame, textvariable=type_var, 
                                    values=["production", "qc", "custom"], state="readonly")
            type_combo.grid(row=2, column=1, padx=5, pady=5)
            
            ttk.Label(info_frame, text="심각도 모드:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
            severity_var = tk.StringVar(value="standard")
            severity_combo = ttk.Combobox(info_frame, textvariable=severity_var,
                                        values=["strict", "standard", "lenient"], state="readonly")
            severity_combo.grid(row=3, column=1, padx=5, pady=5)
            
            # 검수 옵션 선택
            options_frame = ttk.LabelFrame(dialog, text="검수 옵션", padding=10)
            options_frame.pack(fill=tk.X, padx=10, pady=5)
            
            option_vars = {
                'check_checklist': tk.BooleanVar(value=True),
                'check_naming': tk.BooleanVar(value=True),
                'check_ranges': tk.BooleanVar(value=True),
                'check_trends': tk.BooleanVar(value=False),
                'check_missing_values': tk.BooleanVar(value=True),
                'check_outliers': tk.BooleanVar(value=True),
                'check_duplicates': tk.BooleanVar(value=True),
                'check_consistency': tk.BooleanVar(value=True)
            }
            
            option_labels = {
                'check_checklist': 'Check list 중점 검사',
                'check_naming': '명명 규칙 검사',
                'check_ranges': '값 범위 분석',
                'check_trends': '데이터 트렌드 분석',
                'check_missing_values': '누락값 검사',
                'check_outliers': '이상치 검사',
                'check_duplicates': '중복 검사',
                'check_consistency': '일관성 검사'
            }
            
            for i, (key, var) in enumerate(option_vars.items()):
                ttk.Checkbutton(options_frame, text=option_labels[key], 
                              variable=var).grid(row=i//2, column=i%2, sticky="w", padx=5, pady=2)
            
            # 버튼 영역
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            def save_template():
                if not name_var.get():
                    messagebox.showwarning("입력 오류", "템플릿명을 입력해주세요.")
                    return
                
                # 템플릿 생성
                check_options = QCCheckOptions(**{key: var.get() for key, var in option_vars.items()})
                template = QCTemplate(
                    template_name=name_var.get(),
                    template_type=type_var.get(),
                    description=desc_var.get(),
                    severity_mode=severity_var.get(),
                    check_options=check_options,
                    created_by=getattr(self, 'current_user', 'Unknown')
                )
                
                template_id = self.template_manager.create_template(template)
                if template_id:
                    messagebox.showinfo("성공", f"템플릿 '{name_var.get()}'이 생성되었습니다.")
                    self._load_qc_templates()  # 템플릿 목록 새로고침
                    dialog.destroy()
                else:
                    messagebox.showerror("오류", "템플릿 생성에 실패했습니다.")
            
            ttk.Button(button_frame, text="취소", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="저장", command=save_template).pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("오류", f"템플릿 생성 다이얼로그 오류: {str(e)}")
    
    def _edit_template(self):
        """기존 템플릿 편집"""
        selected_template_name = self.qc_template_var.get()
        
        if selected_template_name == "기본 설정":
            messagebox.showinfo("알림", "기본 설정은 편집할 수 없습니다.")
            return
        
        template = self.template_mapping.get(selected_template_name)
        if not template:
            messagebox.showwarning("오류", "선택된 템플릿을 찾을 수 없습니다.")
            return
        
        # 편집 다이얼로그 (생성과 유사하지만 기존 값으로 초기화)
        messagebox.showinfo("구현 예정", "템플릿 편집 기능은 향후 구현 예정입니다.")
    
    def _export_template(self):
        """템플릿 내보내기"""
        selected_template_name = self.qc_template_var.get()
        
        if selected_template_name == "기본 설정":
            messagebox.showinfo("알림", "기본 설정은 내보낼 수 없습니다.")
            return
        
        template = self.template_mapping.get(selected_template_name)
        if not template:
            messagebox.showwarning("오류", "선택된 템플릿을 찾을 수 없습니다.")
            return
        
        try:
            from tkinter import filedialog
            
            file_path = filedialog.asksaveasfilename(
                title="템플릿 내보내기",
                defaultextension=".json",
                filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")]
            )
            
            if file_path:
                if self.template_manager.export_template(template.id, file_path):
                    messagebox.showinfo("성공", f"템플릿이 '{file_path}'로 내보내졌습니다.")
                else:
                    messagebox.showerror("오류", "템플릿 내보내기에 실패했습니다.")
        
        except Exception as e:
            messagebox.showerror("오류", f"템플릿 내보내기 오류: {str(e)}")
    
    def perform_batch_qc_check(self):
        """배치 QC 검수 실행"""
        try:
            from .batch_qc import BatchQCManager
            
            # 배치 검수 파일이 선택되었는지 확인
            if not hasattr(self, 'selected_qc_files') or not self.selected_qc_files:
                messagebox.showwarning("파일 선택", "배치 검수할 파일들을 먼저 선택해주세요.")
                return
            
            # 배치 검수 세션 생성 다이얼로그
            dialog = tk.Toplevel(self.window)
            dialog.title("배치 QC 검수 설정")
            dialog.geometry("400x300")
            dialog.transient(self.window)
            dialog.grab_set()
            
            # 세션 정보 입력
            ttk.Label(dialog, text="세션명:").pack(pady=5)
            session_name_var = tk.StringVar(value=f"Batch_QC_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            ttk.Entry(dialog, textvariable=session_name_var, width=40).pack(pady=5)
            
            ttk.Label(dialog, text="검수자:").pack(pady=5)
            inspector_var = tk.StringVar(value=getattr(self, 'current_user', 'Unknown'))
            ttk.Entry(dialog, textvariable=inspector_var, width=40).pack(pady=5)
            
            ttk.Label(dialog, text=f"선택된 파일: {len(self.selected_qc_files)}개").pack(pady=10)
            
            # 배치 검수 실행
            def start_batch():
                try:
                    manager = BatchQCManager(self.db_schema)
                    session = manager.create_session(
                        session_name_var.get(),
                        inspector_var.get(),
                        description="Enhanced QC에서 시작된 배치 검수"
                    )
                    
                    # 파일들을 세션에 추가
                    for filename, filepath in self.selected_qc_files.items():
                        # 장비 타입 결정 (임시로 선택된 타입 사용)
                        equipment_type_id = getattr(self, 'equipment_types_for_qc', {}).get(
                            self.qc_type_var.get(), 1
                        )
                        session.add_item(filename, equipment_type_id, filepath)
                    
                    # 진행 상황 콜백 설정
                    def progress_callback(progress, message):
                        self.qc_progress.config(value=progress)
                        self.qc_status_label.config(text=message)
                        self.window.update_idletasks()
                    
                    def completion_callback(summary):
                        self.qc_status_label.config(text=f"✅ 배치 검수 완료 - {summary['success_rate']:.1f}% 성공")
                        self.qc_progress.config(value=100)
                        messagebox.showinfo("완료", f"배치 검수가 완료되었습니다.\n성공률: {summary['success_rate']:.1f}%")
                    
                    session.set_callbacks(progress_callback, completion_callback)
                    
                    dialog.destroy()
                    
                    # 배치 검수 시작 (별도 스레드에서)
                    import threading
                    threading.Thread(target=lambda: session.start_batch_inspection(max_workers=3), 
                                   daemon=True).start()
                    
                except Exception as e:
                    messagebox.showerror("오류", f"배치 검수 시작 오류: {str(e)}")
            
            ttk.Button(dialog, text="시작", command=start_batch).pack(pady=10)
            ttk.Button(dialog, text="취소", command=dialog.destroy).pack()
            
        except Exception as e:
            messagebox.showerror("오류", f"배치 검수 오류: {str(e)}")
    
    def generate_qc_report(self):
        """QC 보고서 생성"""
        try:
            from .qc_reports import QCReportGenerator
            from tkinter import filedialog
            
            # 검수 결과가 있는지 확인
            if not hasattr(self, 'last_qc_results') or not self.last_qc_results:
                messagebox.showwarning("알림", "먼저 QC 검수를 실행해주세요.")
                return
            
            # 보고서 생성 옵션 다이얼로그
            dialog = tk.Toplevel(self.window)
            dialog.title("QC 보고서 생성")
            dialog.geometry("350x200")
            dialog.transient(self.window)
            dialog.grab_set()
            
            ttk.Label(dialog, text="보고서 유형:").pack(pady=5)
            template_var = tk.StringVar(value="standard")
            ttk.Combobox(dialog, textvariable=template_var, 
                        values=["standard", "detailed", "summary", "customer"],
                        state="readonly").pack(pady=5)
            
            ttk.Label(dialog, text="출력 형식:").pack(pady=5)
            format_var = tk.StringVar(value="pdf")
            ttk.Combobox(dialog, textvariable=format_var,
                        values=["pdf", "docx", "html", "excel"],
                        state="readonly").pack(pady=5)
            
            def generate_report():
                try:
                    file_path = filedialog.asksaveasfilename(
                        title="보고서 저장",
                        defaultextension=f".{format_var.get()}",
                        filetypes=[(f"{format_var.get().upper()} 파일", f"*.{format_var.get()}")]
                    )
                    
                    if file_path:
                        generator = QCReportGenerator()
                        result_path = generator.generate_report(
                            self.last_qc_results,
                            template_var.get(),
                            format_var.get(),
                            file_path
                        )
                        
                        if result_path:
                            messagebox.showinfo("성공", f"보고서가 생성되었습니다.\n{result_path}")
                            dialog.destroy()
                        else:
                            messagebox.showerror("오류", "보고서 생성에 실패했습니다.")
                
                except Exception as e:
                    messagebox.showerror("오류", f"보고서 생성 오류: {str(e)}")
            
            ttk.Button(dialog, text="생성", command=generate_report).pack(pady=10)
            ttk.Button(dialog, text="취소", command=dialog.destroy).pack()
            
        except Exception as e:
            messagebox.showerror("오류", f"보고서 생성 오류: {str(e)}")

    def start_batch_qc(self):
        """배치 QC 검수 시작"""
        try:
            from .batch_qc import BatchQCManager
            
            # 배치 QC 다이얼로그
            dialog = tk.Toplevel(self.window)
            dialog.title("배치 QC 검수")
            dialog.geometry("400x300")
            dialog.transient(self.window)
            dialog.grab_set()
            
            ttk.Label(dialog, text="세션 이름:").pack(pady=5)
            session_name_var = tk.StringVar(value=f"Batch_QC_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            ttk.Entry(dialog, textvariable=session_name_var).pack(pady=5)
            
            ttk.Label(dialog, text="검수자명:").pack(pady=5)
            inspector_var = tk.StringVar(value="QC Engineer")
            ttk.Entry(dialog, textvariable=inspector_var).pack(pady=5)
            
            def start_batch():
                try:
                    if not hasattr(self, 'selected_qc_files') or not self.selected_qc_files:
                        messagebox.showwarning("알림", "먼저 파일을 선택해주세요.")
                        return
                    
                    from .batch_qc import BatchQCSession
                    from .schema import DBSchema
                    
                    db_schema = getattr(self, 'db_schema', None) or DBSchema()
                    session = BatchQCSession(
                        session_name_var.get(),
                        inspector_var.get(),
                        template_id=None,
                        db_schema=db_schema
                    )
                    
                    # 선택된 파일들을 세션에 추가
                    selected_type = self.qc_type_var.get()
                    equipment_type_id = getattr(self, 'equipment_types_for_qc', {}).get(selected_type)
                    
                    for filename, filepath in self.selected_qc_files.items():
                        session.add_item(filename, equipment_type_id, filepath)
                    
                    # 진행 상황 콜백 설정
                    def progress_callback(progress, message):
                        self.qc_progress.config(value=progress)
                        self.qc_status_label.config(text=message)
                        self.window.update_idletasks()
                    
                    def completion_callback(summary):
                        self.qc_status_label.config(text=f"✅ 배치 검수 완료 - {summary['success_rate']:.1f}% 성공")
                        self.qc_progress.config(value=100)
                        messagebox.showinfo("완료", f"배치 검수가 완료되었습니다.\n성공률: {summary['success_rate']:.1f}%")
                    
                    session.set_callbacks(progress_callback, completion_callback)
                    
                    dialog.destroy()
                    
                    # 배치 검수 시작 (별도 스레드에서)
                    import threading
                    threading.Thread(target=lambda: session.start_batch_inspection(max_workers=3), 
                                   daemon=True).start()
                    
                except Exception as e:
                    messagebox.showerror("오류", f"배치 검수 시작 오류: {str(e)}")
            
            ttk.Button(dialog, text="시작", command=start_batch).pack(pady=10)
            ttk.Button(dialog, text="취소", command=dialog.destroy).pack()
            
        except Exception as e:
            messagebox.showerror("오류", f"배치 검수 오류: {str(e)}")

    # 클래스에 핵심 메서드만 추가
    cls.create_enhanced_qc_tab = create_enhanced_qc_tab
    cls.select_qc_files = select_qc_files
    cls.perform_enhanced_qc_check = perform_enhanced_qc_check
    cls.show_enhanced_qc_statistics = show_enhanced_qc_statistics
    cls.create_enhanced_charts = create_enhanced_charts
    cls.export_qc_results_simple = export_qc_results_simple 