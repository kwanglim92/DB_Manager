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
        """누락된 값 검사"""
        results = []
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                results.append({
                    "parameter": col,
                    "issue_type": "누락값",
                    "description": f"{missing_count}개의 누락된 값이 있습니다.",
                    "severity": "높음" if missing_count > 5 else "중간"
                })
        return results

    @staticmethod
    def check_outliers(df, equipment_type):
        """이상치 검사 (3-시그마 기준)"""
        results = []
        numeric_cols = df.select_dtypes(include=['number']).columns

        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()

            if pd.isna(std) or std == 0:
                continue

            lower_bound = mean - 3 * std
            upper_bound = mean + 3 * std

            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            outlier_count = len(outliers)

            if outlier_count > 0:
                results.append({
                    "parameter": col,
                    "issue_type": "이상치",
                    "description": f"{outlier_count}개의 이상치가 있습니다. (평균: {mean:.2f}, 표준편차: {std:.2f})",
                    "severity": "높음" if outlier_count > 3 else "중간"
                })

        return results

    @staticmethod
    def check_duplicate_entries(df, equipment_type):
        """중복 항목 검사"""
        results = []
        dup_count = len(df[df.duplicated()])

        if dup_count > 0:
            results.append({
                "parameter": "전체",
                "issue_type": "중복 항목",
                "description": f"{dup_count}개의 중복 항목이 있습니다.",
                "severity": "중간"
            })

        return results

    @staticmethod
    def check_data_consistency(df, equipment_type):
        """데이터 일관성 검사"""
        results = []
        # 장비 유형에 따른 특정 검사 로직
        # 예: 특정 열 간의 관계 검사
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
        qc_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(qc_tab, text="QC 검수")

        # 검수 대상 선택 프레임
        top_frame = ttk.LabelFrame(qc_tab, text="검수 대상 선택", padding=10)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        type_frame = ttk.Frame(top_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="장비 유형:").pack(side=tk.LEFT, padx=5)
        self.qc_type_var = tk.StringVar()
        self.qc_type_combobox = ttk.Combobox(type_frame, textvariable=self.qc_type_var, state="readonly", width=30)
        self.qc_type_combobox.pack(side=tk.LEFT, padx=5)

        button_frame = ttk.Frame(top_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="검수 실행", command=self.perform_qc_check).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="검수 결과 내보내기", command=self.export_qc_results).pack(side=tk.LEFT, padx=5)

        # 검수 결과 프레임
        middle_frame = ttk.LabelFrame(qc_tab, text="검수 결과", padding=10)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("parameter", "issue_type", "description", "severity")
        headings = {
            "parameter": "파라미터", 
            "issue_type": "문제 유형", 
            "description": "설명", 
            "severity": "심각도"
        }
        column_widths = {
            "parameter": 200, 
            "issue_type": 150, 
            "description": 300, 
            "severity": 100
        }

        qc_result_frame, self.qc_result_tree = create_treeview_with_scrollbar(
            middle_frame, columns, headings, column_widths, height=15)
        qc_result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 검수 통계 프레임
        bottom_frame = ttk.LabelFrame(qc_tab, text="검수 통계", padding=10)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.stats_frame = ttk.Frame(bottom_frame)
        self.stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.chart_frame = ttk.Frame(bottom_frame)
        self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 장비 유형 목록 로드
        self.load_equipment_types_for_qc()

    def load_equipment_types_for_qc(self):
        """QC 검수를 위한 장비 유형 목록 로드"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 장비 유형 정보 조회
            cursor.execute("SELECT id, name FROM equipment_types ORDER BY name")
            equipment_types = cursor.fetchall()

            # 콤보박스 업데이트
            if equipment_types:
                self.equipment_types_for_qc = {name: id for id, name in equipment_types}
                self.qc_type_combobox['values'] = list(self.equipment_types_for_qc.keys())
                self.qc_type_combobox.current(0)  # 첫 번째 항목 선택
            else:
                self.equipment_types_for_qc = {}
                self.qc_type_combobox['values'] = []
                messagebox.showinfo("알림", "등록된 장비 유형이 없습니다.")

            conn.close()
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 로드 중 오류 발생: {str(e)}")

    def perform_qc_check(self):
        """QC 검수 실행"""
        selected_type = self.qc_type_var.get()

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
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 쿼리 실행
            query = """
            SELECT p.name as parameter_name, p.min_value, p.max_value, v.value, v.timestamp
            FROM parameters p
            LEFT JOIN parameter_values v ON p.id = v.parameter_id
            WHERE p.equipment_type_id = ?
            """
            cursor.execute(query, (equipment_type_id,))
            data = cursor.fetchall()

            if not data:
                loading_dialog.close()
                messagebox.showinfo("알림", "검수할 데이터가 없습니다.")
                return

            # 데이터프레임 생성
            df = pd.DataFrame(data, columns=["parameter_name", "min_value", "max_value", "value", "timestamp"])

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
            conn.close()
            loading_dialog.close()

            self.update_log(f"[QC 검수] 장비 유형 '{selected_type}'에 대한 QC 검수가 완료되었습니다. 총 {len(results)}개의 이슈 발견.")

        except Exception as e:
            if 'loading_dialog' in locals():
                loading_dialog.close()
            messagebox.showerror("오류", f"QC 검수 중 오류 발생: {str(e)}")

    def show_qc_statistics(self, results):
        """QC 검수 결과 통계 표시"""
        if not results:
            ttk.Label(self.stats_frame, text="이슈가 발견되지 않았습니다.").pack(padx=10, pady=10)
            return

        # 심각도별 카운트
        severity_counts = {"높음": 0, "중간": 0, "낮음": 0}
        for result in results:
            severity = result["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # 이슈 유형별 카운트
        issue_counts = {}
        for result in results:
            issue_type = result["issue_type"]
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        # 통계 표시
        ttk.Label(self.stats_frame, text=f"총 이슈 수: {len(results)}건", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)

        # 심각도별 통계
        ttk.Label(self.stats_frame, text="심각도별 통계:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=2)
        for severity, count in severity_counts.items():
            if count > 0:
                ttk.Label(self.stats_frame, text=f"• {severity}: {count}건").pack(anchor="w", padx=20, pady=1)

        # 이슈 유형별 통계
        ttk.Label(self.stats_frame, text="이슈 유형별 통계:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=2)
        for issue_type, count in issue_counts.items():
            ttk.Label(self.stats_frame, text=f"• {issue_type}: {count}건").pack(anchor="w", padx=20, pady=1)

        # 파이 차트 생성
        self.create_pie_chart(severity_counts, "심각도별 이슈 분포")

    def create_pie_chart(self, data, title):
        """파이 차트 생성"""
        fig, ax = plt.subplots(figsize=(5, 4))

        # 데이터가 있는 항목만 포함
        labels = []
        sizes = []
        colors = {'높음': 'red', '중간': 'orange', '낮음': 'green'}
        chart_colors = []

        for label, value in data.items():
            if value > 0:
                labels.append(label)
                sizes.append(value)
                chart_colors.append(colors.get(label, 'blue'))

        if not sizes:  # 데이터가 없는 경우
            ax.text(0.5, 0.5, "데이터 없음", ha='center', va='center')
            ax.axis('off')
        else:
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=chart_colors, startangle=90)
            ax.axis('equal')  # 원형 파이 차트

        ax.set_title(title)

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
            columns = ["파라미터", "문제 유형", "설명", "심각도"]

            for item_id in self.qc_result_tree.get_children():
                values = self.qc_result_tree.item(item_id, 'values')
                data.append(list(values))

            # 데이터프레임 생성 및 Excel 저장
            df = pd.DataFrame(data, columns=columns)

            # 추가 정보 시트 준비
            equipment_type = self.qc_type_var.get()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary_data = {
                "정보": ["장비 유형", "검수 일시", "총 이슈 수"],
                "값": [equipment_type, timestamp, len(data)]
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

    # 클래스에 함수 추가
    cls.create_qc_check_tab = create_qc_check_tab
    cls.load_equipment_types_for_qc = load_equipment_types_for_qc
    cls.perform_qc_check = perform_qc_check
    cls.show_qc_statistics = show_qc_statistics
    cls.create_pie_chart = create_pie_chart
    cls.export_qc_results = export_qc_results
