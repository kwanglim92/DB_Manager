# Enhanced QC 기능 - Performance 모드 및 파일 선택 지원

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from app.loading import LoadingDialog
from app.utils import create_treeview_with_scrollbar
from app.schema import DBSchema

class EnhancedQCValidator:
    """향상된 QC 검증 클래스 - Performance 모드 지원"""

    SEVERITY_LEVELS = {
        "높음": 3,
        "중간": 2,
        "낮음": 1
    }

    @staticmethod
    def check_performance_parameters(df, equipment_type):
        """Performance 파라미터 특별 검사"""
        results = []
        
        if 'is_performance' in df.columns:
            performance_params = df[df['is_performance'] == 1]
            
            # Performance 파라미터의 신뢰도 검사 (더 엄격한 기준)
            if 'confidence_score' in df.columns:
                low_perf_confidence = performance_params[performance_params['confidence_score'] < 0.8]
                for _, row in low_perf_confidence.iterrows():
                    results.append({
                        "parameter": row['parameter_name'],
                        "issue_type": "Performance 신뢰도 부족",
                        "description": f"Performance 중요 파라미터의 신뢰도가 {row['confidence_score']*100:.1f}%로 낮습니다 (권장: 80% 이상)",
                        "severity": "높음"
                    })
            
            # Performance 파라미터의 사양 범위 누락 검사
            missing_specs = performance_params[
                (performance_params['min_spec'].isna() | (performance_params['min_spec'] == '')) |
                (performance_params['max_spec'].isna() | (performance_params['max_spec'] == ''))
            ]
            for _, row in missing_specs.iterrows():
                results.append({
                    "parameter": row['parameter_name'],
                    "issue_type": "Performance 사양 누락",
                    "description": f"Performance 중요 파라미터에 사양 범위(min/max)가 누락되었습니다",
                    "severity": "높음"
                })
        
        return results

    @staticmethod
    def run_enhanced_checks(df, equipment_type, is_performance_mode=False):
        """향상된 QC 검사 실행"""
        from app.qc import QCValidator
        
        # 기본 검사 실행
        all_results = QCValidator.run_all_checks(df, equipment_type)
        
        # Performance 모드일 때 추가 검사
        if is_performance_mode or 'is_performance' in df.columns:
            perf_results = EnhancedQCValidator.check_performance_parameters(df, equipment_type)
            all_results.extend(perf_results)

        # 심각도 순으로 정렬
        all_results.sort(key=lambda x: EnhancedQCValidator.SEVERITY_LEVELS.get(x["severity"], 0), reverse=True)

        return all_results


def add_enhanced_qc_functions_to_class(cls):
    """
    DBManager 클래스에 향상된 QC 검수 기능을 추가합니다.
    """
    
    def select_qc_files(self):
        """QC 검수를 위한 파일 선택 (업로드된 파일 중에서 선택)"""
        try:
            # 업로드된 파일 목록 확인
            if not hasattr(self, 'uploaded_files') or not self.uploaded_files:
                messagebox.showinfo("알림", "먼저 '파일 > 폴더 열기'를 통해 파일을 업로드해주세요.")
                return
            
            # 파일 선택 대화상자 생성
            file_selection_window = tk.Toplevel(self.window)
            file_selection_window.title("QC 검수 파일 선택")
            file_selection_window.geometry("500x400")
            file_selection_window.transient(self.window)
            file_selection_window.grab_set()
            
            # 설명 레이블
            ttk.Label(file_selection_window, text="QC 검수를 수행할 파일을 선택하세요 (최대 6개):").pack(pady=10)
            
            # 파일 목록 프레임
            files_frame = ttk.Frame(file_selection_window)
            files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # 스크롤바가 있는 체크박스 리스트
            canvas = tk.Canvas(files_frame)
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
                
                checkbox = ttk.Checkbutton(
                    scrollable_frame, 
                    text=f"{filename}", 
                    variable=var
                )
                checkbox.pack(anchor="w", padx=10, pady=2)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # 버튼 프레임
            button_frame = ttk.Frame(file_selection_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            def apply_selection():
                selected_files = []
                for filename, var in self.qc_file_vars.items():
                    if var.get():
                        selected_files.append(filename)
                
                if not selected_files:
                    messagebox.showwarning("경고", "최소 1개의 파일을 선택해주세요.")
                    return
                
                if len(selected_files) > 6:
                    messagebox.showwarning("경고", "최대 6개의 파일만 선택할 수 있습니다.")
                    return
                
                # 선택된 파일 정보 저장
                self.selected_qc_files = {name: self.uploaded_files[name] for name in selected_files}
                
                messagebox.showinfo("선택 완료", f"{len(selected_files)}개의 파일이 QC 검수용으로 선택되었습니다.")
                file_selection_window.destroy()
            
            def select_all():
                for var in self.qc_file_vars.values():
                    var.set(True)
            
            def deselect_all():
                for var in self.qc_file_vars.values():
                    var.set(False)
            
            # 버튼들
            ttk.Button(button_frame, text="전체 선택", command=select_all).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="전체 해제", command=deselect_all).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="취소", command=file_selection_window.destroy).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="선택 완료", command=apply_selection).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            error_msg = f"파일 선택 중 오류 발생: {str(e)}"
            messagebox.showerror("오류", error_msg)
            self.update_log(f"❌ {error_msg}")

    def perform_enhanced_qc_check(self):
        """향상된 QC 검수 실행 (Performance 모드 지원)"""
        selected_type = self.qc_type_var.get()
        qc_mode = getattr(self, 'qc_mode_var', None)
        
        if not selected_type:
            messagebox.showinfo("알림", "장비 유형을 선택해주세요.")
            return

        try:
            # 로딩 대화상자 표시
            loading_dialog = LoadingDialog(self.window)
            self.window.update_idletasks()

            # 트리뷰 초기화
            for item in self.qc_result_tree.get_children():
                self.qc_result_tree.delete(item)

            # 통계 및 차트 프레임 초기화
            for widget in self.stats_frame.winfo_children():
                widget.destroy()
            for widget in self.chart_frame.winfo_children():
                widget.destroy()

            # 선택된 장비 유형의 데이터 로드
            equipment_type_id = self.equipment_types_for_qc[selected_type]
            
            # Performance 모드에 따른 데이터 필터링
            performance_only = qc_mode and qc_mode.get() == "performance"
            
            # DB 스키마 인스턴스를 통해 데이터 로드
            db_schema = DBSchema()
            
            # Performance 모드 또는 전체 모드에 따라 데이터 로드
            data = db_schema.get_default_values(equipment_type_id, performance_only=performance_only)

            if not data:
                loading_dialog.close()
                mode_text = "Performance 항목" if performance_only else "전체 항목"
                messagebox.showinfo("알림", f"장비 유형 '{selected_type}'에 대한 {mode_text} 검수할 데이터가 없습니다.")
                return

            # 데이터프레임 생성
            # data structure: (id, parameter_name, default_value, min_spec, max_spec, type_name,
            #                  occurrence_count, total_files, confidence_score, source_files, description,
            #                  module_name, part_name, item_type, is_performance)
            df = pd.DataFrame(data, columns=[
                "id", "parameter_name", "default_value", "min_spec", "max_spec", "type_name",
                "occurrence_count", "total_files", "confidence_score", "source_files", "description",
                "module_name", "part_name", "item_type", "is_performance"
            ])

            # 향상된 QC 검사 실행 (50%)
            loading_dialog.update_progress(50, "QC 검사 실행 중...")
            results = EnhancedQCValidator.run_enhanced_checks(df, selected_type, performance_only)

            # 결과 트리뷰에 표시 (75%)
            loading_dialog.update_progress(75, "결과 업데이트 중...")
            for i, result in enumerate(results):
                self.qc_result_tree.insert(
                    "", "end", 
                    values=(result["parameter"], result["issue_type"], result["description"], result["severity"])
                )

            # 통계 정보 표시 (90%)
            loading_dialog.update_progress(90, "통계 정보 생성 중...")
            self.show_enhanced_qc_statistics(results, performance_only)

            # 완료
            loading_dialog.update_progress(100, "완료")
            loading_dialog.close()

            # 검수 모드 정보 포함하여 로그 업데이트
            mode_text = "Performance 항목" if performance_only else "전체 항목"
            params_count = len(data)
            performance_count = sum(1 for row in data if row[14]) if not performance_only else params_count  # is_performance 컬럼
            
            self.update_log(f"[QC 검수] 장비 유형 '{selected_type}' ({mode_text}: {params_count}개 파라미터)에 대한 QC 검수가 완료되었습니다. 총 {len(results)}개의 이슈 발견.")
            
            # Performance 모드별 추가 정보
            if not performance_only and performance_count > 0:
                self.update_log(f"  ℹ️ 참고: 이 장비 유형에는 {performance_count}개의 Performance 중요 파라미터가 있습니다.")

        except Exception as e:
            if 'loading_dialog' in locals():
                loading_dialog.close()
            error_msg = f"QC 검수 중 오류 발생: {str(e)}"
            messagebox.showerror("오류", error_msg)
            self.update_log(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

    def show_enhanced_qc_statistics(self, results, is_performance_mode=False):
        """향상된 QC 검수 결과 통계 표시"""
        if not results:
            mode_text = "Performance 항목" if is_performance_mode else "전체 항목"
            ttk.Label(self.stats_frame, text=f"{mode_text}에서 이슈가 발견되지 않았습니다.").pack(padx=10, pady=10)
            return

        # 심각도별 카운트
        severity_counts = {"높음": 0, "중간": 0, "낮음": 0}
        for result in results:
            severity = result["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # 이슈 유형별 카운트
        issue_counts = {}
        performance_issue_counts = {}
        for result in results:
            issue_type = result["issue_type"]
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
            
            # Performance 관련 이슈 별도 카운트
            if "Performance" in issue_type:
                performance_issue_counts[issue_type] = performance_issue_counts.get(issue_type, 0) + 1

        # 통계 표시
        mode_text = "Performance 항목" if is_performance_mode else "전체 항목"
        ttk.Label(self.stats_frame, text=f"{mode_text} QC 검수 결과", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        ttk.Label(self.stats_frame, text=f"총 이슈 수: {len(results)}건", font=("Arial", 11)).pack(anchor="w", padx=10, pady=2)

        # 심각도별 통계
        ttk.Label(self.stats_frame, text="심각도별 통계:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=2)
        for severity, count in severity_counts.items():
            if count > 0:
                color = {"높음": "red", "중간": "orange", "낮음": "green"}.get(severity, "black")
                label = ttk.Label(self.stats_frame, text=f"• {severity}: {count}건")
                label.pack(anchor="w", padx=20, pady=1)

        # Performance 관련 이슈가 있는 경우 강조 표시
        if performance_issue_counts:
            ttk.Label(self.stats_frame, text="⚠️ Performance 중요 이슈:", font=("Arial", 10, "bold"), foreground="red").pack(anchor="w", padx=10, pady=2)
            for issue_type, count in performance_issue_counts.items():
                ttk.Label(self.stats_frame, text=f"• {issue_type}: {count}건", foreground="red").pack(anchor="w", padx=20, pady=1)

        # 이슈 유형별 통계
        ttk.Label(self.stats_frame, text="이슈 유형별 통계:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=2)
        for issue_type, count in issue_counts.items():
            if "Performance" not in issue_type:  # Performance 이슈는 위에서 이미 표시
                ttk.Label(self.stats_frame, text=f"• {issue_type}: {count}건").pack(anchor="w", padx=20, pady=1)

        # 파이 차트 생성
        self.create_enhanced_pie_chart(severity_counts, f"{mode_text} 심각도별 이슈 분포")

    def create_enhanced_pie_chart(self, data, title):
        """향상된 파이 차트 생성"""
        fig, ax = plt.subplots(figsize=(5, 4))

        # 데이터가 있는 항목만 포함
        labels = []
        sizes = []
        colors = {'높음': '#FF4444', '중간': '#FF8800', '낮음': '#44AA44'}
        chart_colors = []

        for label, value in data.items():
            if value > 0:
                labels.append(f"{label}\n({value}건)")
                sizes.append(value)
                chart_colors.append(colors.get(label, 'blue'))

        if not sizes:  # 데이터가 없는 경우
            ax.text(0.5, 0.5, "✅ 이슈 없음", ha='center', va='center', fontsize=14, color='green')
            ax.axis('off')
        else:
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                            colors=chart_colors, startangle=90)
            ax.axis('equal')  # 원형 파이 차트
            
            # 텍스트 스타일 개선
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_weight('bold')

        ax.set_title(title, fontsize=12, weight='bold')

        # tkinter 캔버스에 matplotlib 차트 표시
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # 클래스에 메서드 추가
    cls.select_qc_files = select_qc_files
    cls.perform_enhanced_qc_check = perform_enhanced_qc_check
    cls.show_enhanced_qc_statistics = show_enhanced_qc_statistics
    cls.create_enhanced_pie_chart = create_enhanced_pie_chart 