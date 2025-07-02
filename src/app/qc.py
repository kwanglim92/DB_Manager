# QC(품질검수) 관련 함수 및 탭 생성 로직을 src/qc_check_helpers.py에서 이관. add_qc_check_functions_to_class, create_qc_check_tab, perform_qc_check 등 포함. 한글 주석 및 기존 UI 구조 유지.

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

class QCValidator:
    """QC 검증을 수행하는 클래스"""

    SEVERITY_LEVELS = {
        "높음": 3,
        "중간": 2,
        "낮음": 1
    }

    @staticmethod
    def check_missing_values(df, equipment_type):
        """누락된 값 검사 - Default DB 구조에 맞게 수정"""
        results = []
        
        # 필수 컬럼들이 누락되었는지 확인
        essential_cols = ['parameter_name', 'default_value']
        for col in essential_cols:
            if col in df.columns:
                missing_count = df[col].isna().sum() + (df[col] == '').sum()
                if missing_count > 0:
                    results.append({
                        "parameter": col,
                        "issue_type": "누락값",
                        "description": f"필수 컬럼 '{col}'에 {missing_count}개의 누락된 값이 있습니다.",
                        "severity": "높음"
                    })
        
        # min_spec, max_spec 누락 확인 (선택적)
        optional_cols = ['min_spec', 'max_spec']
        for col in optional_cols:
            if col in df.columns:
                missing_count = df[col].isna().sum() + (df[col] == '').sum()
                if missing_count > 0:
                    results.append({
                        "parameter": col,
                        "issue_type": "누락값",
                        "description": f"선택적 컬럼 '{col}'에 {missing_count}개의 누락된 값이 있습니다.",
                        "severity": "낮음"
                    })
        
        return results

    @staticmethod
    def check_outliers(df, equipment_type):
        """이상치 검사 - 신뢰도 및 발생횟수 기준"""
        results = []
        
        # 신뢰도가 낮은 파라미터 확인
        if 'confidence_score' in df.columns:
            try:
                # confidence_score를 안전하게 숫자로 변환
                df_copy = df.copy()
                df_copy['confidence_score_numeric'] = pd.to_numeric(df_copy['confidence_score'], errors='coerce')
                low_confidence = df_copy[df_copy['confidence_score_numeric'] < 0.5]
                
                if len(low_confidence) > 0:
                    for _, row in low_confidence.iterrows():
                        confidence_val = row.get('confidence_score_numeric', 0)
                        if pd.notna(confidence_val):
                            results.append({
                                "parameter": row['parameter_name'],
                                "issue_type": "낮은 신뢰도",
                                "description": f"신뢰도가 {confidence_val*100:.1f}%로 낮습니다 (발생횟수: {row.get('occurrence_count', 'N/A')}/{row.get('total_files', 'N/A')})",
                                "severity": "중간" if confidence_val < 0.3 else "낮음"
                            })
            except Exception as e:
                print(f"신뢰도 검사 중 오류: {e}")
        
        # 발생횟수가 1인 파라미터 (단일 소스)
        if 'occurrence_count' in df.columns and 'total_files' in df.columns:
            try:
                # occurrence_count를 안전하게 숫자로 변환
                df_copy = df.copy()
                df_copy['occurrence_count_numeric'] = pd.to_numeric(df_copy['occurrence_count'], errors='coerce')
                single_source = df_copy[df_copy['occurrence_count_numeric'] == 1]
                
                if len(single_source) > 0:
                    for _, row in single_source.iterrows():
                        results.append({
                            "parameter": row['parameter_name'],
                            "issue_type": "단일 소스",
                            "description": f"단일 파일에서만 발견된 파라미터입니다 (1/{row.get('total_files', 'N/A')} 파일)",
                            "severity": "낮음"
                        })
            except Exception as e:
                print(f"발생횟수 검사 중 오류: {e}")
        
        return results

    @staticmethod
    def check_duplicate_entries(df, equipment_type):
        """중복 항목 검사 - 파라미터명 기준"""
        results = []
        
        if 'parameter_name' in df.columns:
            duplicated_params = df['parameter_name'].duplicated()
            dup_count = duplicated_params.sum()
            
            if dup_count > 0:
                dup_names = df[duplicated_params]['parameter_name'].tolist()
                results.append({
                    "parameter": "전체",
                    "issue_type": "중복 파라미터",
                    "description": f"{dup_count}개의 중복 파라미터명이 있습니다: {', '.join(dup_names[:3])}{'...' if len(dup_names) > 3 else ''}",
                    "severity": "높음"
                })
        
        return results

    @staticmethod
    def check_data_consistency(df, equipment_type):
        """데이터 일관성 검사 - 사양 범위 검사"""
        results = []
        
        # min_spec과 max_spec이 모두 있는 경우 범위 검사
        if all(col in df.columns for col in ['min_spec', 'max_spec', 'default_value']):
            for _, row in df.iterrows():
                try:
                    if pd.notna(row['min_spec']) and pd.notna(row['max_spec']) and pd.notna(row['default_value']):
                        min_val = float(row['min_spec'])
                        max_val = float(row['max_spec'])
                        default_val = float(row['default_value'])
                        
                        if min_val > max_val:
                            results.append({
                                "parameter": row['parameter_name'],
                                "issue_type": "사양 오류",
                                "description": f"최소값({min_val})이 최대값({max_val})보다 큽니다.",
                                "severity": "높음"
                            })
                        elif not (min_val <= default_val <= max_val):
                            results.append({
                                "parameter": row['parameter_name'],
                                "issue_type": "범위 초과",
                                "description": f"설정값({default_val})이 사양 범위({min_val}~{max_val})를 벗어납니다.",
                                "severity": "중간"
                            })
                except (ValueError, TypeError):
                    # 숫자가 아닌 값은 무시
                    continue
        
        return results

    @staticmethod
    def run_all_checks(df, equipment_type):
        """모든 QC 검사 실행"""
        all_results = []
        all_results.extend(QCValidator.check_missing_values(df, equipment_type))
        all_results.extend(QCValidator.check_outliers(df, equipment_type))
        all_results.extend(QCValidator.check_duplicate_entries(df, equipment_type))
        all_results.extend(QCValidator.check_data_consistency(df, equipment_type))

        # 심각도 순으로 정렬
        all_results.sort(key=lambda x: QCValidator.SEVERITY_LEVELS.get(x["severity"], 0), reverse=True)

        return all_results


def add_qc_check_functions_to_class(cls):
    """
    DBManager 클래스에 QC 검수 기능을 추가합니다.
    """
    def create_qc_check_tab(self):
        """QC 검수 탭 생성 - 향상된 기능 포함"""
        # Enhanced QC 기능이 사용 가능한지 확인
        try:
            from app.enhanced_qc import add_enhanced_qc_functions_to_class
            # Enhanced QC 기능을 클래스에 추가
            add_enhanced_qc_functions_to_class(self.__class__)
            # Enhanced QC 탭 생성
            self.create_enhanced_qc_tab()
            self.update_log("[QC] 향상된 QC 검수 탭이 생성되었습니다.")
            return
        except ImportError:
            # Enhanced QC를 사용할 수 없는 경우 기본 QC 탭 생성
            self.update_log("[QC] 기본 QC 검수 탭을 생성합니다.")
        
        # 기본 QC 탭 생성
        qc_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(qc_tab, text="QC 검수")

        # 🎨 Professional Engineering Control Panel
        control_panel = ttk.Frame(qc_tab, style="Control.TFrame")
        control_panel.pack(fill=tk.X, padx=15, pady=10)

        # Equipment Type Management Section
        equipment_frame = ttk.LabelFrame(control_panel, text="Equipment Type Management", padding=12)
        equipment_frame.pack(fill=tk.X, pady=(0, 8))

        # Equipment type selection line
        equipment_line = ttk.Frame(equipment_frame)
        equipment_line.pack(fill=tk.X)

        ttk.Label(equipment_line, text="Equipment Type:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.qc_type_var = tk.StringVar()
        self.qc_type_combobox = ttk.Combobox(equipment_line, textvariable=self.qc_type_var, 
                                           state="readonly", width=25, font=("Segoe UI", 9))
        self.qc_type_combobox.pack(side=tk.LEFT, padx=(0, 12))
        
        # Professional refresh button
        refresh_btn = ttk.Button(equipment_line, text="Refresh", command=self.refresh_qc_equipment_types,
                               style="Tool.TButton")
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        # QC Mode Configuration Section
        mode_frame = ttk.LabelFrame(control_panel, text="QC Mode Configuration", padding=12)
        mode_frame.pack(fill=tk.X, pady=(0, 8))

        mode_line = ttk.Frame(mode_frame)
        mode_line.pack(fill=tk.X)

        ttk.Label(mode_line, text="Inspection Mode:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.qc_mode_var = tk.StringVar(value="performance")
        
        performance_radio = ttk.Radiobutton(mode_line, text="Check List Focused", 
                                          variable=self.qc_mode_var, value="performance")
        performance_radio.pack(side=tk.LEFT, padx=(0, 20))
        
        full_radio = ttk.Radiobutton(mode_line, text="Full Inspection", 
                                   variable=self.qc_mode_var, value="full")
        full_radio.pack(side=tk.LEFT, padx=(0, 10))

        # QC Execution Control Section
        action_frame = ttk.LabelFrame(control_panel, text="QC Execution Control", padding=12)
        action_frame.pack(fill=tk.X, pady=(0, 8))

        button_line = ttk.Frame(action_frame)
        button_line.pack(fill=tk.X)

        # Professional styled buttons
        file_select_btn = ttk.Button(button_line, text="Select QC Files", command=self.select_qc_files,
                                   style="TButton")
        file_select_btn.pack(side=tk.LEFT, padx=(0, 12))

        qc_btn = ttk.Button(button_line, text="Execute QC Inspection", command=self.perform_qc_check,
                          style="Accent.TButton")
        qc_btn.pack(side=tk.LEFT, padx=(0, 12))

        export_btn = ttk.Button(button_line, text="Export to Excel", command=self.export_qc_results,
                              style="Success.TButton")
        export_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 🎨 Professional QC Results Section
        results_frame = ttk.LabelFrame(qc_tab, text="QC Inspection Results", padding=15)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        columns = ("itemname", "issue_type", "description")
        headings = {
            "itemname": "ItemName", 
            "issue_type": "Issue Type", 
            "description": "Description"
        }
        column_widths = {
            "itemname": 250, 
            "issue_type": 200, 
            "description": 400
        }

        qc_result_frame, self.qc_result_tree = create_treeview_with_scrollbar(
            results_frame, columns, headings, column_widths, height=15)
        qc_result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 🎨 Professional QC Statistics Section
        statistics_frame = ttk.LabelFrame(qc_tab, text="QC Statistics & Analysis", padding=15)
        statistics_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.stats_frame = ttk.Frame(statistics_frame)
        self.stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=5)

        self.chart_frame = ttk.Frame(statistics_frame)
        self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=5)

        # 장비 유형 목록 로드
        self.load_equipment_types_for_qc()

    def refresh_qc_equipment_types(self):
        """QC용 장비 유형 목록 새로고침"""
        try:
            self.load_equipment_types_for_qc()
            self.update_log("[QC] 장비 유형 목록이 새로고침되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 목록 새로고침 중 오류 발생: {str(e)}")
            self.update_log(f"❌ QC 장비 유형 새로고침 오류: {str(e)}")

    def load_equipment_types_for_qc(self):
        """QC용 장비 유형 목록 로드"""
        try:
            if hasattr(self, 'db_schema') and self.db_schema:
                equipment_types = self.db_schema.get_equipment_types()
            else:
                from app.schema import DBSchema
                db_schema = DBSchema()
                equipment_types = db_schema.get_equipment_types()
            
            # 장비 유형 딕셔너리 생성 (이름 -> ID 매핑)
            self.equipment_types_for_qc = {}
            equipment_names = []
            
            for eq_type in equipment_types:
                type_id, type_name = eq_type[0], eq_type[1]
                self.equipment_types_for_qc[type_name] = type_id
                equipment_names.append(type_name)
            
            # 콤보박스 업데이트
            if hasattr(self, 'qc_type_combobox'):
                self.qc_type_combobox['values'] = equipment_names
                if equipment_names:
                    self.qc_type_combobox.set(equipment_names[0])
            
            self.update_log(f"[QC] {len(equipment_names)}개의 장비 유형이 로드되었습니다.")
            
        except Exception as e:
            error_msg = f"QC용 장비 유형 로드 중 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            if hasattr(self, 'qc_type_combobox'):
                self.qc_type_combobox['values'] = []

    def perform_qc_check(self):
        """QC 검수 실행"""
        selected_type = self.qc_type_var.get()
        qc_mode = self.qc_mode_var.get()  # 검수 모드 확인

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
            performance_only = (qc_mode == "performance")
            
            # DB 스키마 인스턴스를 통해 데이터 로드
            if hasattr(self, 'db_schema') and self.db_schema:
                data = self.db_schema.get_default_values(equipment_type_id, performance_only=performance_only)
            else:
                from app.schema import DBSchema
                db_schema = DBSchema()
                data = db_schema.get_default_values(equipment_type_id, performance_only=performance_only)

            if not data:
                loading_dialog.close()
                mode_text = "Performance 항목" if performance_only else "전체 항목"
                messagebox.showinfo("알림", f"장비 유형 '{selected_type}'에 대한 {mode_text} 검수할 데이터가 없습니다.")
                return

            # 데이터프레임 생성 (실제 데이터 구조에 맞게 수정)
            df = pd.DataFrame(data, columns=[
                "id", "parameter_name", "default_value", "min_spec", "max_spec", "type_name",
                "occurrence_count", "total_files", "confidence_score", "source_files", "description",
                "module_name", "part_name", "item_type", "is_performance"
            ])

            # QC 검사 실행 (50%)
            loading_dialog.update_progress(50, "QC 검사 실행 중...")
            results = QCValidator.run_all_checks(df, selected_type)

            # 결과 트리뷰에 표시 (75%)
            loading_dialog.update_progress(75, "결과 업데이트 중...")
            for i, result in enumerate(results):
                # 개선된 이슈 유형 매핑
                issue_type_mapping = {
                    "누락값": "Missing Data",
                    "이상치": "Spec Out", 
                    "중복": "Duplicate Entry",
                    "일관성": "Inconsistency"
                }
                mapped_issue_type = issue_type_mapping.get(result["issue_type"], result["issue_type"])
                
                self.qc_result_tree.insert(
                    "", "end", 
                    values=(result["parameter"], mapped_issue_type, result["description"])
                )

            # 통계 정보 표시 (90%)
            loading_dialog.update_progress(90, "통계 정보 생성 중...")
            self.show_qc_statistics(results)

            # 완료
            loading_dialog.update_progress(100, "완료")
            loading_dialog.close()

            # 검수 모드 정보 포함하여 로그 업데이트
            mode_text = "Performance 항목" if performance_only else "전체 항목"
            self.update_log(f"[QC 검수] 장비 유형 '{selected_type}' ({mode_text})에 대한 QC 검수가 완료되었습니다. 총 {len(results)}개의 이슈 발견.")

        except Exception as e:
            if 'loading_dialog' in locals():
                loading_dialog.close()
            messagebox.showerror("오류", f"QC 검수 중 오류 발생: {str(e)}")
            self.update_log(f"❌ QC 검수 오류: {str(e)}")

    def show_qc_statistics(self, results):
        """QC 검수 결과 통계 표시 - Professional Engineering Style"""
        if not results:
            ttk.Label(self.stats_frame, text="No Issues Detected", 
                     font=("Segoe UI", 10, "bold"), foreground="green").pack(padx=15, pady=15)
            return

        # 이슈 유형별 카운트
        issue_counts = {}
        for result in results:
            issue_type = result["issue_type"]
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        # Professional Statistics Display
        stats_title = ttk.Label(self.stats_frame, text=f"Total Issues Found: {len(results)}", 
                               font=("Segoe UI", 12, "bold"), style="Title.TLabel")
        stats_title.pack(anchor="w", padx=15, pady=(10, 5))

        # Issue Type Statistics
        type_title = ttk.Label(self.stats_frame, text="Issue Type Breakdown:", 
                              font=("Segoe UI", 10, "bold"))
        type_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        for issue_type, count in issue_counts.items():
            percentage = (count / len(results)) * 100
            stats_label = ttk.Label(self.stats_frame, 
                                  text=f"• {issue_type}: {count} ({percentage:.1f}%)",
                                  font=("Segoe UI", 9))
            stats_label.pack(anchor="w", padx=25, pady=2)

        # Create Issue Type Distribution Chart
        self.create_pie_chart(issue_counts, "Issue Type Distribution")

    def create_pie_chart(self, data, title):
        """Professional Engineering Style Pie Chart"""
        fig, ax = plt.subplots(figsize=(6, 4))

        # 데이터가 있는 항목만 포함
        labels = []
        sizes = []
        # Professional color scheme for engineering applications
        professional_colors = ['#0078d4', '#107c10', '#ff8c00', '#d13438', '#605e5c', '#8764b8']
        chart_colors = []

        for i, (label, value) in enumerate(data.items()):
            if value > 0:
                labels.append(label)
                sizes.append(value)
                chart_colors.append(professional_colors[i % len(professional_colors)])

        if not sizes:  # 데이터가 없는 경우
            ax.text(0.5, 0.5, "No Data Available", ha='center', va='center', 
                   fontsize=12, color='gray')
            ax.axis('off')
        else:
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                            colors=chart_colors, startangle=90)
            ax.axis('equal')  # 원형 파이 차트
            
            # Professional styling
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

        ax.set_title(title, fontsize=12, fontweight='bold', pad=20)

        # tkinter 캔버스에 matplotlib 차트 표시
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def export_qc_results(self):
        """QC 검수 결과 내보내기"""
        if not self.qc_result_tree.get_children():
            messagebox.showinfo("알림", "내보낼 QC 검수 결과가 없습니다.")
            return

        # 파일 저장 대화상자
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")],
            title="QC 검수 결과 저장"
        )

        if not file_path:
            return

        try:
            # 트리뷰 데이터 수집
            data = []
            columns = ["ItemName", "Issue Type", "Description"]

            for item_id in self.qc_result_tree.get_children():
                values = self.qc_result_tree.item(item_id, 'values')
                data.append(list(values))

            # 데이터프레임 생성 및 Excel 저장
            df = pd.DataFrame(data, columns=columns)

            # 추가 정보 시트 준비
            equipment_type = self.qc_type_var.get()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary_data = {
                "Information": ["Equipment Type", "Inspection Time", "Total Issues"],
                "Value": [equipment_type, timestamp, len(data)]
            }
            summary_df = pd.DataFrame(summary_data)

            # Excel 파일로 저장 (여러 시트)
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="QC 검수 결과", index=False)
                summary_df.to_excel(writer, sheet_name="검수 정보", index=False)

            messagebox.showinfo("알림", f"QC 검수 결과가 성공적으로 저장되었습니다.\n{file_path}")
            self.update_log(f"[QC 검수] 검수 결과가 '{file_path}'에 저장되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"파일 저장 중 오류 발생: {str(e)}")

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
                    f"이제 'QC 검수 실행' 버튼을 클릭하여 검수를 시작하세요."
                )
                
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
            if hasattr(self, 'update_log'):
                self.update_log(f"❌ {error_msg}")

    def perform_qc_check_enhanced(self):
        """개선된 QC 검수 실행 (Performance 모드 지원)"""
        selected_type = self.qc_type_var.get()
        qc_mode = self.qc_mode_var.get()  # Performance 또는 full

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
            performance_only = (qc_mode == "performance")
            
            # DB 스키마 인스턴스를 통해 데이터 로드
            from app.schema import DBSchema
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

            # QC 검사 실행 (50%)
            loading_dialog.update_progress(50, "QC 검사 실행 중...")
            results = QCValidator.run_all_checks(df, selected_type)

            # 결과 트리뷰에 표시 (75%)
            loading_dialog.update_progress(75, "결과 업데이트 중...")
            for i, result in enumerate(results):
                self.qc_result_tree.insert(
                    "", "end", 
                    values=(result["parameter"], result["issue_type"], result["description"], result["severity"])
                )

            # 통계 정보 표시 (90%)
            loading_dialog.update_progress(90, "통계 정보 생성 중...")
            self.show_qc_statistics(results)

            # 완료
            loading_dialog.update_progress(100, "완료")
            loading_dialog.close()

            # 검수 모드 정보 포함하여 로그 업데이트
            mode_text = "Performance 항목" if performance_only else "전체 항목"
            params_count = len(data)
            performance_count = sum(1 for row in data if row[14]) if qc_mode == "full" else params_count  # is_performance 컬럼
            
            self.update_log(f"[QC 검수] 장비 유형 '{selected_type}' ({mode_text}: {params_count}개 파라미터)에 대한 QC 검수가 완료되었습니다. 총 {len(results)}개의 이슈 발견.")
            
            # Performance 모드별 추가 정보
            if qc_mode == "full" and performance_count > 0:
                self.update_log(f"  ℹ️ 참고: 이 장비 유형에는 {performance_count}개의 Performance 중요 파라미터가 있습니다.")

        except Exception as e:
            if 'loading_dialog' in locals():
                loading_dialog.close()
            error_msg = f"QC 검수 중 오류 발생: {str(e)}"
            messagebox.showerror("오류", error_msg)
            self.update_log(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

    # 클래스에 함수 추가
    cls.create_qc_check_tab = create_qc_check_tab
    cls.load_equipment_types_for_qc = load_equipment_types_for_qc
    cls.perform_qc_check = perform_qc_check
    cls.show_qc_statistics = show_qc_statistics
    cls.create_pie_chart = create_pie_chart
    cls.export_qc_results = export_qc_results
