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
        """Check list 파라미터 특별 검사"""
        results = []
        
        if 'is_checklist' in df.columns:
            checklist_params = df[df['is_checklist'] == 1]
            
            # Check list 파라미터의 신뢰도 검사 (더 엄격한 기준)
            if 'confidence_score' in df.columns:
                low_checklist_confidence = checklist_params[checklist_params['confidence_score'] < 0.8]
                for _, row in low_checklist_confidence.iterrows():
                    results.append({
                        "parameter": row['parameter_name'],
                        "issue_type": "Check list 신뢰도 부족",
                        "description": f"Check list 중요 파라미터의 신뢰도가 {row['confidence_score']*100:.1f}%로 낮습니다 (권장: 80% 이상)",
                        "severity": "높음",
                        "category": "checklist",
                        "recommendation": "더 많은 소스 파일에서 확인하거나 수동 검증이 필요합니다."
                    })
            
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
                    "recommendation": "장비 매뉴얼을 참조하여 사양 범위를 추가하세요."
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
                    "recommendation": "해당 모듈의 추가 파라미터를 확인하세요."
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
                    "recommendation": "중복되거나 불필요한 파라미터가 있는지 검토하세요."
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
    def run_enhanced_checks(df, equipment_type, is_checklist_mode=False):
        """간소화된 QC 검사 실행 - 검수 모드에 따라 필요한 검사만 수행"""
        from .qc import QCValidator
        
        # 기본 검사 실행 (누락 파라미터, 값 차이 등)
        all_results = QCValidator.run_all_checks(df, equipment_type)
        
        # 기존 결과에 category와 recommendation 추가
        for result in all_results:
            if 'category' not in result:
                result['category'] = 'data_quality'
            if 'recommendation' not in result:
                result['recommendation'] = '상세 검토가 필요합니다.'
        
        # 검수 모드에 따른 추가 검사
        enhanced_results = []
        
        if is_checklist_mode:
            # Check list 모드: Check list 파라미터 특별 검사만 수행
            enhanced_results.extend(EnhancedQCValidator.check_checklist_parameters(df, equipment_type))
        else:
            # 전체 검수 모드: 모든 향상된 검사 수행
            enhanced_results.extend(EnhancedQCValidator.check_checklist_parameters(df, equipment_type))
            enhanced_results.extend(EnhancedQCValidator.check_data_trends(df, equipment_type))
        
        # 결과 합치기
        all_results.extend(enhanced_results)

        # 심각도 순으로 정렬
        all_results.sort(key=lambda x: EnhancedQCValidator.SEVERITY_LEVELS.get(x["severity"], 0), reverse=True)

        return all_results

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
        """향상된 QC 검수 탭 생성"""
        qc_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(qc_tab, text="QC 검수")

        # 🎨 상단 컨트롤 패널 - 향상된 디자인
        control_panel = ttk.LabelFrame(qc_tab, text="🎛️ QC 검수 설정", padding=15)
        control_panel.pack(fill=tk.X, padx=10, pady=10)

        # 첫 번째 행: 장비 유형 및 모드 선택
        row1 = ttk.Frame(control_panel)
        row1.pack(fill=tk.X, pady=(0, 10))

        # 장비 유형 선택
        ttk.Label(row1, text="🏭 장비 유형:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.qc_type_var = tk.StringVar()
        self.qc_type_combobox = ttk.Combobox(row1, textvariable=self.qc_type_var, state="readonly", width=25)
        self.qc_type_combobox.pack(side=tk.LEFT, padx=(0, 15))
        
        # 새로고침 버튼
        refresh_btn = ttk.Button(row1, text="🔄 새로고침", command=self.refresh_qc_equipment_types)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 15))

        # 검수 모드 선택
        ttk.Label(row1, text="🔍 검수 모드:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.qc_mode_var = tk.StringVar(value="checklist")
        
        checklist_radio = ttk.Radiobutton(row1, text="⭐ Check list 중점", 
                                          variable=self.qc_mode_var, value="checklist")
        checklist_radio.pack(side=tk.LEFT, padx=(0, 10))
        
        full_radio = ttk.Radiobutton(row1, text="📋 전체 검수", 
                                   variable=self.qc_mode_var, value="full")
        full_radio.pack(side=tk.LEFT, padx=(0, 10))
        
        # 두 번째 행: 실행 버튼
        row2 = ttk.Frame(control_panel)
        row2.pack(fill=tk.X, pady=(5, 0))

        # 실행 버튼 영역
        action_frame = ttk.Frame(row2)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # 파일 선택 버튼
        file_select_btn = ttk.Button(action_frame, text="📁 검수 파일 선택", 
                                   command=self.select_qc_files)
        file_select_btn.pack(pady=(0, 5))

        # 메인 QC 실행 버튼
        self.qc_btn = ttk.Button(action_frame, text="🚀 QC 검수 실행", 
                                command=self.perform_enhanced_qc_check)
        self.qc_btn.pack(pady=(0, 5))

        # 결과 내보내기 버튼
        ttk.Button(action_frame, text="📤 Excel 내보내기", 
                  command=self.export_qc_results_simple).pack(pady=(5, 0))

        # 🎨 메인 결과 영역 - 탭 구조로 개선
        main_frame = ttk.Frame(qc_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 결과 탭 노트북
        self.qc_results_notebook = ttk.Notebook(main_frame)
        self.qc_results_notebook.pack(fill=tk.BOTH, expand=True)

        # 탭 1: 검수 결과 목록
        results_tab = ttk.Frame(self.qc_results_notebook)
        self.qc_results_notebook.add(results_tab, text="📋 검수 결과")

        # 검수 결과 트리뷰 (향상된 컬럼 구조)
        columns = ("parameter", "issue_type", "description", "severity", "category", "recommendation")
        headings = {
            "parameter": "파라미터", 
            "issue_type": "문제 유형", 
            "description": "상세 설명", 
            "severity": "심각도",
            "category": "카테고리",
            "recommendation": "권장사항"
        }
        column_widths = {
            "parameter": 150, 
            "issue_type": 120, 
            "description": 250, 
            "severity": 80,
            "category": 100,
            "recommendation": 200
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

        self.qc_status_label = ttk.Label(status_frame, text="📋 QC 검수 대기 중...", 
                                        font=('Arial', 9), foreground='blue')
        self.qc_status_label.pack(side=tk.LEFT)

        self.qc_progress = ttk.Progressbar(status_frame, mode='determinate', length=200)
        self.qc_progress.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 초기 데이터 로드
        self.load_equipment_types_for_qc()
    
    def select_qc_files(self):
        """QC 검수를 위한 파일 선택 (업로드된 파일 중에서 선택)"""
        try:
            # 업로드된 파일 목록 확인
            if not hasattr(self, 'uploaded_files') or not self.uploaded_files:
                messagebox.showinfo(
                    "파일 선택 안내", 
                    "QC 검수를 위해서는 먼저 파일을 로드해야 합니다.\n\n"
                    "📁 파일 > 폴더 열기를 통해 DB 파일들을 업로드해주세요.\n"
                    "지원 형식: .txt, .csv, .db 파일"
                )
                return
            
            # 파일 선택 대화상자 생성
            file_selection_window = tk.Toplevel(self.window)
            file_selection_window.title("🔍 QC 검수 파일 선택")
            file_selection_window.geometry("600x500")
            file_selection_window.transient(self.window)
            file_selection_window.grab_set()
            file_selection_window.resizable(True, True)
            
            # 메인 프레임
            main_frame = ttk.Frame(file_selection_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 상단 정보 프레임
            info_frame = ttk.Frame(main_frame)
            info_frame.pack(fill=tk.X, pady=(0, 10))
            
            # 제목 및 설명
            title_label = ttk.Label(
                info_frame, 
                text="QC 검수 파일 선택", 
                font=('Arial', 12, 'bold')
            )
            title_label.pack(anchor='w')
            
            desc_label = ttk.Label(
                info_frame, 
                text=f"업로드된 {len(self.uploaded_files)}개 파일 중에서 QC 검수를 수행할 파일을 선택하세요 (최대 6개)",
                font=('Arial', 9),
                foreground='gray'
            )
            desc_label.pack(anchor='w', pady=(2, 0))
            
            # 파일 목록 프레임 (스크롤 가능)
            files_frame = ttk.LabelFrame(main_frame, text="📄 파일 목록", padding=10)
            files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # 스크롤바가 있는 캔버스
            canvas = tk.Canvas(files_frame, bg='white')
            scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # 체크박스 변수들
            self.qc_file_vars = {}
            
            # 업로드된 파일들에 대한 체크박스 생성
            for i, (filename, filepath) in enumerate(self.uploaded_files.items()):
                var = tk.BooleanVar()
                self.qc_file_vars[filename] = var
                
                # 파일 정보 프레임
                file_frame = ttk.Frame(scrollable_frame)
                file_frame.pack(fill=tk.X, pady=2, padx=5)
                
                # 체크박스
                checkbox = ttk.Checkbutton(
                    file_frame, 
                    text="", 
                    variable=var
                )
                checkbox.pack(side=tk.LEFT, padx=(0, 10))
                
                # 파일 정보 레이블
                file_info_frame = ttk.Frame(file_frame)
                file_info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                # 파일명 (굵게)
                filename_label = ttk.Label(
                    file_info_frame, 
                    text=filename,
                    font=('Arial', 9, 'bold')
                )
                filename_label.pack(anchor='w')
                
                # 파일 경로 (작게)
                try:
                    import os
                    file_size = os.path.getsize(filepath)
                    file_size_str = f"{file_size:,} bytes"
                    
                    path_label = ttk.Label(
                        file_info_frame,
                        text=f"📁 {filepath} ({file_size_str})",
                        font=('Arial', 8),
                        foreground='gray'
                    )
                    path_label.pack(anchor='w')
                except:
                    path_label = ttk.Label(
                        file_info_frame,
                        text=f"📁 {filepath}",
                        font=('Arial', 8),
                        foreground='gray'
                    )
                    path_label.pack(anchor='w')
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # 하단 버튼 프레임
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(0, 0))
            
            # 선택 통계 라벨
            selection_stats_label = ttk.Label(
                button_frame, 
                text="선택된 파일: 0개",
                font=('Arial', 9),
                foreground='blue'
            )
            selection_stats_label.pack(side=tk.LEFT)
            
            def update_selection_stats():
                """선택 통계 업데이트"""
                selected_count = sum(1 for var in self.qc_file_vars.values() if var.get())
                selection_stats_label.config(
                    text=f"선택된 파일: {selected_count}개",
                    foreground='blue' if selected_count <= 6 else 'red'
                )
            
            # 체크박스 변경 시 통계 업데이트
            for var in self.qc_file_vars.values():
                var.trace('w', lambda *args: update_selection_stats())
            
            def apply_selection():
                selected_files = []
                for filename, var in self.qc_file_vars.items():
                    if var.get():
                        selected_files.append(filename)
                
                if not selected_files:
                    messagebox.showwarning("선택 필요", "최소 1개의 파일을 선택해주세요.")
                    return
                
                if len(selected_files) > 6:
                    messagebox.showwarning(
                        "선택 제한", 
                        f"최대 6개의 파일만 선택할 수 있습니다.\n현재 선택: {len(selected_files)}개"
                    )
                    return
                
                # 선택된 파일 정보 저장
                self.selected_qc_files = {name: self.uploaded_files[name] for name in selected_files}
                
                # 성공 메시지와 함께 선택된 파일 목록 표시
                file_list = '\n'.join([f"• {name}" for name in selected_files])
                messagebox.showinfo(
                    "파일 선택 완료", 
                    f"QC 검수용으로 {len(selected_files)}개 파일이 선택되었습니다.\n\n"
                    f"선택된 파일:\n{file_list}\n\n"
                    f"이제 '🚀 QC 검수 실행' 버튼을 클릭하여 검수를 시작하세요."
                )
                
                # 로그 업데이트
                self.update_log(f"[파일 선택] QC 검수 대상 파일 {len(selected_files)}개 선택 완료")
                
                file_selection_window.destroy()
            
            def select_all():
                for var in self.qc_file_vars.values():
                    var.set(True)
                update_selection_stats()
            
            def deselect_all():
                for var in self.qc_file_vars.values():
                    var.set(False)
                update_selection_stats()
            
            def select_first_n(n):
                """처음 n개 파일 선택"""
                deselect_all()
                for i, var in enumerate(self.qc_file_vars.values()):
                    if i < n:
                        var.set(True)
                    else:
                        break
                update_selection_stats()
            
            # 버튼들
            button_control_frame = ttk.Frame(button_frame)
            button_control_frame.pack(side=tk.RIGHT)
            
            ttk.Button(button_control_frame, text="처음 3개", command=lambda: select_first_n(3)).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_control_frame, text="전체 선택", command=select_all).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_control_frame, text="전체 해제", command=deselect_all).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_control_frame, text="취소", command=file_selection_window.destroy).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_control_frame, text="✅ 선택 완료", command=apply_selection).pack(side=tk.LEFT, padx=2)
            
            # 초기 통계 업데이트
            update_selection_stats()
            
        except Exception as e:
            error_msg = f"파일 선택 중 오류 발생: {str(e)}"
            messagebox.showerror("오류", error_msg)
            self.update_log(f"❌ {error_msg}")

    def perform_enhanced_qc_check(self):
        """향상된 QC 검수 실행 (Check list 모드 지원)"""
        selected_type = self.qc_type_var.get()
        qc_mode = getattr(self, 'qc_mode_var', None)
        
        if not selected_type:
            messagebox.showinfo("알림", "장비 유형을 선택해주세요.")
            return

        try:
            # 로딩 대화상자 표시
            loading_dialog = LoadingDialog(self.window)
            self.window.update_idletasks()
            
            # 상태 업데이트
            self.qc_status_label.config(text="🔄 QC 검수 진행 중...", foreground='orange')
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
            
            # Check list 모드 확인
            is_checklist_mode = qc_mode.get() == "checklist" if qc_mode else False
            
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
            
            df = pd.DataFrame(data, columns=[
                "id", "parameter_name", "default_value", "min_spec", "max_spec", "type_name",
                "occurrence_count", "total_files", "confidence_score", "source_files", "description",
                "module_name", "part_name", "item_type", "is_checklist"
            ])

            # 향상된 QC 검사 실행
            loading_dialog.update_progress(50, "향상된 QC 검사 실행 중...")
            self.qc_progress.config(value=50)
            
            results = EnhancedQCValidator.run_enhanced_checks(df, selected_type, is_checklist_mode=is_checklist_mode)

            # 결과 트리뷰에 표시
            loading_dialog.update_progress(75, "결과 업데이트 중...")
            self.qc_progress.config(value=75)
            
            for result in results:
                # 심각도에 따른 색상 태그 설정
                severity = result.get("severity", "낮음")
                tag = f"severity_{severity}"
                
                self.qc_result_tree.insert(
                    "", "end", 
                    values=(
                        result.get("parameter", ""),
                        result.get("issue_type", ""),
                        result.get("description", ""),
                        severity,
                        result.get("category", ""),
                        result.get("recommendation", "")
                    ),
                    tags=(tag,)
                )

            # 트리뷰 태그 색상 설정
            self.qc_result_tree.tag_configure("severity_높음", background="#ffebee", foreground="#c62828")
            self.qc_result_tree.tag_configure("severity_중간", background="#fff3e0", foreground="#ef6c00")
            self.qc_result_tree.tag_configure("severity_낮음", background="#f3e5f5", foreground="#7b1fa2")

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
        """간단한 QC 결과 Excel 내보내기"""
        try:
            # 검수 결과가 있는지 확인
            if not self.qc_result_tree.get_children():
                messagebox.showwarning("알림", "먼저 QC 검수를 실행해주세요.")
                return
            
            # 파일 저장 대화상자
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="QC 검수 결과 저장",
                defaultextension=".xlsx",
                filetypes=[("Excel 파일", "*.xlsx"), ("CSV 파일", "*.csv")]
            )
            
            if not file_path:
                return
            
            # 트리뷰에서 결과 데이터 수집
            results = []
            for item in self.qc_result_tree.get_children():
                values = self.qc_result_tree.item(item)['values']
                results.append({
                    'parameter': values[0],
                    'issue_type': values[1],
                    'description': values[2],
                    'severity': values[3],
                    'category': values[4],
                    'recommendation': values[5]
                })
            
            # 간단한 보고서 생성
            from .qc_reports import export_qc_results_to_excel, export_qc_results_to_csv
            
            equipment_name = getattr(self, 'qc_type_var', tk.StringVar()).get() or "Unknown"
            equipment_type = equipment_name
            
            success = False
            if file_path.endswith('.xlsx'):
                success = export_qc_results_to_excel(results, equipment_name, equipment_type, file_path)
            elif file_path.endswith('.csv'):
                success = export_qc_results_to_csv(results, equipment_name, equipment_type, file_path)
            
            if success:
                messagebox.showinfo("성공", f"QC 검수 결과가 저장되었습니다.\n{file_path}")
                self.update_log(f"[QC] 검수 결과를 '{file_path}'에 저장했습니다.")
            else:
                messagebox.showerror("오류", "결과 내보내기에 실패했습니다.")
            
        except Exception as e:
            error_msg = f"결과 내보내기 중 오류: {str(e)}"
            messagebox.showerror("오류", error_msg)
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