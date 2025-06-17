# 리포트 탭 및 기능 - 통계 및 리포트 생성

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from app.utils import create_treeview_with_scrollbar
from app.loading import LoadingDialog

def add_report_functions_to_class(cls):
    """
    DBManager 클래스에 리포트 기능을 추가합니다.
    """
    def create_report_tab(self):
        """리포트 탭 생성"""
        report_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(report_tab, text="리포트")

        # 상단 프레임 - 리포트 옵션
        top_frame = ttk.Frame(report_tab, padding=(10, 5))
        top_frame.pack(fill=tk.X)

        # 리포트 유형 선택
        ttk.Label(top_frame, text="리포트 유형:").pack(side=tk.LEFT, padx=5)

        self.report_type_var = tk.StringVar(value="summary")
        report_type_frame = ttk.Frame(top_frame)
        report_type_frame.pack(side=tk.LEFT)

        ttk.Radiobutton(
            report_type_frame, text="요약", value="summary", 
            variable=self.report_type_var, command=self.update_report_view
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            report_type_frame, text="차이점", value="differences", 
            variable=self.report_type_var, command=self.update_report_view
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            report_type_frame, text="통계", value="statistics", 
            variable=self.report_type_var, command=self.update_report_view
        ).pack(side=tk.LEFT, padx=5)

        # 내보내기 버튼
        ttk.Button(
            top_frame, text="리포트 내보내기", 
            command=self.export_report
        ).pack(side=tk.RIGHT, padx=5)

        # 중간 프레임 - 트리뷰
        columns = ("item", "value")
        headings = {"item": "항목", "value": "값"}
        column_widths = {"item": 250, "value": 400}

        tree_frame, self.report_tree = create_treeview_with_scrollbar(
            report_tab, columns, headings, column_widths
        )
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 하단 프레임 - 차트
        self.chart_frame = ttk.LabelFrame(report_tab, text="통계 차트", padding=10)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def update_report_view(self):
        """리포트 뷰 업데이트"""
        # 트리뷰 초기화
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)

        # 차트 프레임 초기화
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        if self.merged_df is None or self.merged_df.empty:
            return

        report_type = self.report_type_var.get()

        if report_type == "summary":
            self.show_summary_report()
        elif report_type == "differences":
            self.show_differences_report()
        elif report_type == "statistics":
            self.show_statistics_report()

    def show_summary_report(self):
        """요약 리포트 표시"""
        # 기본 정보
        self.report_tree.insert("", "end", values=("분석 시간", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.report_tree.insert("", "end", values=("파일 수", len(self.file_names)))

        # 파일 목록
        files_item = self.report_tree.insert("", "end", values=("파일 목록", ""))
        for i, file_name in enumerate(self.file_names):
            self.report_tree.insert(files_item, "end", values=(f"파일 {i+1}", os.path.basename(file_name)))

        # 파라미터 통계
        total_params = len(self.merged_df)
        self.report_tree.insert("", "end", values=("총 파라미터 수", total_params))

        # 차이점 통계
        diff_counts = {}
        total_diffs = 0

        for file_idx in range(len(self.file_names)):
            file_col = f"file_{file_idx}"
            file_name = os.path.basename(self.file_names[file_idx])
            diff_count = 0

            for _, row in self.merged_df.iterrows():
                default_value = row['default_value'] if 'default_value' in row and pd.notna(row['default_value']) else ""
                file_value = row[file_col] if file_col in row and pd.notna(row[file_col]) else ""

                if default_value != file_value:
                    diff_count += 1

            diff_counts[file_name] = diff_count
            total_diffs += diff_count

        self.report_tree.insert("", "end", values=("총 차이점 수", total_diffs))

        diffs_item = self.report_tree.insert("", "end", values=("파일별 차이점 수", ""))
        for file_name, count in diff_counts.items():
            self.report_tree.insert(diffs_item, "end", values=(file_name, count))

        # 차트 생성
        self.create_summary_chart(diff_counts)

    def create_summary_chart(self, diff_counts):
        """요약 차트 생성"""
        fig, ax = plt.subplots(figsize=(8, 5))

        files = list(diff_counts.keys())
        counts = list(diff_counts.values())

        # 파일명이 너무 길면 축약
        short_files = [f[:15] + '...' if len(f) > 15 else f for f in files]

        # 막대 그래프 생성
        bars = ax.bar(short_files, counts, color='skyblue')

        # 막대 위에 값 표시
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    str(count), ha='center', va='bottom')

        ax.set_title('파일별 차이점 수')
        ax.set_xlabel('파일')
        ax.set_ylabel('차이점 수')

        # X축 레이블 회전
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()

        # tkinter 캔버스에 matplotlib 차트 표시
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def show_differences_report(self):
        """차이점 리포트 표시"""
        # 파일별 차이점 분석
        for file_idx, file_name in enumerate(self.file_names):
            file_basename = os.path.basename(file_name)
            file_col = f"file_{file_idx}"

            file_item = self.report_tree.insert("", "end", values=(f"파일: {file_basename}", ""))

            missing_in_default = 0
            missing_in_file = 0
            value_diffs = 0

            for _, row in self.merged_df.iterrows():
                parameter = row['parameter']
                default_value = row['default_value'] if 'default_value' in row and pd.notna(row['default_value']) else ""
                file_value = row[file_col] if file_col in row and pd.notna(row[file_col]) else ""

                # 차이 유형 확인
                if pd.isna(default_value) and pd.notna(file_value):
                    missing_in_default += 1
                    self.report_tree.insert(
                        file_item, "end", 
                        values=(f"파라미터: {parameter}", "Default DB에 없음")
                    )
                elif pd.notna(default_value) and pd.isna(file_value):
                    missing_in_file += 1
                    self.report_tree.insert(
                        file_item, "end", 
                        values=(f"파라미터: {parameter}", "파일에 없음")
                    )
                elif default_value != file_value:
                    value_diffs += 1
                    self.report_tree.insert(
                        file_item, "end", 
                        values=(f"파라미터: {parameter}", f"값 차이: {default_value} != {file_value}")
                    )

            # 요약 정보 추가
            summary_item = self.report_tree.insert(
                file_item, "end", 
                values=("요약", f"누락(Default): {missing_in_default}, 누락(파일): {missing_in_file}, 값 차이: {value_diffs}")
            )

            # 첫 번째 항목으로 이동
            self.report_tree.move(summary_item, file_item, 0)

        # 차트 생성
        self.create_differences_chart()

    def create_differences_chart(self):
        """차이점 차트 생성"""
        # 파일별 차이점 유형 데이터 수집
        diff_types = {'Default DB에 없음': [], '파일에 없음': [], '값 차이': []}
        file_labels = []

        for file_idx, file_name in enumerate(self.file_names):
            file_basename = os.path.basename(file_name)
            file_labels.append(file_basename)
            file_col = f"file_{file_idx}"

            missing_in_default = 0
            missing_in_file = 0
            value_diffs = 0

            for _, row in self.merged_df.iterrows():
                default_value = row['default_value'] if 'default_value' in row and pd.notna(row['default_value']) else ""
                file_value = row[file_col] if file_col in row and pd.notna(row[file_col]) else ""

                # 차이 유형 확인
                if pd.isna(default_value) and pd.notna(file_value):
                    missing_in_default += 1
                elif pd.notna(default_value) and pd.isna(file_value):
                    missing_in_file += 1
                elif default_value != file_value:
                    value_diffs += 1

            diff_types['Default DB에 없음'].append(missing_in_default)
            diff_types['파일에 없음'].append(missing_in_file)
            diff_types['값 차이'].append(value_diffs)

        # 파일명이 너무 길면 축약
        short_labels = [f[:15] + '...' if len(f) > 15 else f for f in file_labels]

        # 차트 생성
        fig, ax = plt.subplots(figsize=(8, 6))

        width = 0.25  # 막대 너비
        x = np.arange(len(short_labels))

        # 각 차이 유형별 막대 그래프
        bars1 = ax.bar(x - width, diff_types['Default DB에 없음'], width, label='Default DB에 없음', color='#FF9800')
        bars2 = ax.bar(x, diff_types['파일에 없음'], width, label='파일에 없음', color='#2196F3')
        bars3 = ax.bar(x + width, diff_types['값 차이'], width, label='값 차이', color='#4CAF50')

        # 축 및 레이블 설정
        ax.set_title('파일별 차이점 유형')
        ax.set_xlabel('파일')
        ax.set_ylabel('차이점 수')
        ax.set_xticks(x)
        ax.set_xticklabels(short_labels, rotation=45, ha='right')
        ax.legend()

        # 막대 위에 값 표시
        def add_labels(bars):
            for bar in bars:
                height = bar.get_height()
                if height > 0:  # 값이 0인 경우 레이블 표시 안함
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            str(int(height)), ha='center', va='bottom', fontsize=8)

        add_labels(bars1)
        add_labels(bars2)
        add_labels(bars3)

        plt.tight_layout()

        # tkinter 캔버스에 matplotlib 차트 표시
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def show_statistics_report(self):
        """통계 리포트 표시"""
        if 'default_value' not in self.merged_df.columns:
            self.report_tree.insert("", "end", values=("오류", "Default DB 값이 없습니다."))
            return

        # 수치형 파라미터만 선택
        numeric_params = []
        for _, row in self.merged_df.iterrows():
            try:
                # default_value가 숫자인지 확인
                if pd.notna(row['default_value']) and float(row['default_value']):
                    numeric_params.append(row['parameter'])
            except (ValueError, TypeError):
                continue

        if not numeric_params:
            self.report_tree.insert("", "end", values=("알림", "분석 가능한 수치형 파라미터가 없습니다."))
            return

        # 통계 데이터 생성
        stats_data = []

        for param in numeric_params[:10]:  # 상위 10개 파라미터만 분석
            param_row = self.merged_df[self.merged_df['parameter'] == param]

            # Default 값
            default_value = param_row['default_value'].iloc[0]
            if pd.isna(default_value):
                continue

            try:
                default_value = float(default_value)
            except (ValueError, TypeError):
                continue

            # 파일 값 수집
            file_values = []
            for file_idx in range(len(self.file_names)):
                file_col = f"file_{file_idx}"
                if file_col in param_row.columns and pd.notna(param_row[file_col].iloc[0]):
                    try:
                        file_values.append(float(param_row[file_col].iloc[0]))
                    except (ValueError, TypeError):
                        continue

            if not file_values:
                continue

            # 통계 계산
            mean_value = np.mean(file_values)
            min_value = np.min(file_values)
            max_value = np.max(file_values)
            std_value = np.std(file_values) if len(file_values) > 1 else 0

            # 데이터 저장
            stats_data.append({
                'parameter': param,
                'default': default_value,
                'mean': mean_value,
                'min': min_value,
                'max': max_value,
                'std': std_value,
                'values': file_values
            })

            # 트리뷰에 표시
            param_item = self.report_tree.insert("", "end", values=(f"파라미터: {param}", ""))
            self.report_tree.insert(param_item, "end", values=("Default 값", f"{default_value:.4f}"))
            self.report_tree.insert(param_item, "end", values=("평균", f"{mean_value:.4f}"))
            self.report_tree.insert(param_item, "end", values=("최소값", f"{min_value:.4f}"))
            self.report_tree.insert(param_item, "end", values=("최대값", f"{max_value:.4f}"))
            self.report_tree.insert(param_item, "end", values=("표준편차", f"{std_value:.4f}"))

            # 편차 비율
            if default_value != 0:
                deviation_pct = ((mean_value - default_value) / default_value) * 100
                self.report_tree.insert(param_item, "end", values=("Default 대비 편차", f"{deviation_pct:.2f}%"))

        # 차트 생성
        if stats_data:
            self.create_statistics_chart(stats_data)

    def create_statistics_chart(self, stats_data):
        """통계 차트 생성"""
        if not stats_data:
            return

        # 1행 2열 서브플롯 생성
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

        # 첫 번째 차트: 파라미터별 Default 값 vs 평균 값
        params = [item['parameter'] for item in stats_data]
        defaults = [item['default'] for item in stats_data]
        means = [item['mean'] for item in stats_data]

        # 파라미터명이 너무 길면 축약
        short_params = [p[:10] + '...' if len(p) > 10 else p for p in params]

        x = np.arange(len(short_params))
        width = 0.35

        ax1.bar(x - width/2, defaults, width, label='Default 값', color='#3F51B5')
        ax1.bar(x + width/2, means, width, label='평균 값', color='#FF5722')

        ax1.set_title('Default 값 vs 평균 값')
        ax1.set_xlabel('파라미터')
        ax1.set_ylabel('값')
        ax1.set_xticks(x)
        ax1.set_xticklabels(short_params, rotation=45, ha='right')
        ax1.legend()

        # 두 번째 차트: 파라미터별 편차 비율
        deviation_pcts = []
        for item in stats_data:
            if item['default'] != 0:
                deviation_pct = ((item['mean'] - item['default']) / item['default']) * 100
                deviation_pcts.append(deviation_pct)
            else:
                deviation_pcts.append(0)

        # 절대값이 너무 큰 경우 제한
        capped_deviations = []
        for dev in deviation_pcts:
            if dev > 100:
                capped_deviations.append(100)
            elif dev < -100:
                capped_deviations.append(-100)
            else:
                capped_deviations.append(dev)

        colors = ['#4CAF50' if dev >= 0 else '#F44336' for dev in capped_deviations]
        ax2.bar(short_params, capped_deviations, color=colors)

        # 원래 값 표시
        for i, (x_pos, dev, capped) in enumerate(zip(range(len(short_params)), deviation_pcts, capped_deviations)):
            if capped == 100 or capped == -100:
                ax2.text(x_pos, capped + (5 if capped > 0 else -5), f"{dev:.1f}%", 
                         ha='center', va='bottom' if capped > 0 else 'top', fontsize=8)
            else:
                ax2.text(x_pos, capped + (5 if capped > 0 else -5), f"{dev:.1f}%", 
                         ha='center', va='bottom' if capped > 0 else 'top', fontsize=8)

        ax2.set_title('Default 대비 편차 비율')
        ax2.set_xlabel('파라미터')
        ax2.set_ylabel('편차 (%)')
        ax2.set_ylim(-120, 120)  # y축 범위 설정
        ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
        ax2.set_xticklabels(short_params, rotation=45, ha='right')

        plt.tight_layout()

        # tkinter 캔버스에 matplotlib 차트 표시
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def export_report(self):
        """리포트 내보내기"""
        if self.merged_df is None or self.merged_df.empty:
            messagebox.showinfo("알림", "내보낼 데이터가 없습니다.")
            return

        # 파일 저장 대화상자
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")],
            title="리포트 저장"
        )

        if not file_path:
            return

        try:
            # 로딩 대화상자 표시
            loading_dialog = LoadingDialog(self.window)
            self.window.update_idletasks()
            loading_dialog.update_progress(10, "리포트 생성 중...")

            # 리포트 유형 확인
            report_type = self.report_type_var.get()

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 기본 정보 시트
                loading_dialog.update_progress(20, "기본 정보 작성 중...")
                info_data = {
                    "항목": [
                        "리포트 생성 일시",
                        "파일 수",
                        "총 파라미터 수",
                        "리포트 유형"
                    ],
                    "값": [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        len(self.file_names),
                        len(self.merged_df),
                        {"summary": "요약", "differences": "차이점", "statistics": "통계"}[report_type]
                    ]
                }

                # 파일 목록 추가
                for i, file_name in enumerate(self.file_names):
                    info_data["항목"].append(f"파일 {i+1}")
                    info_data["값"].append(os.path.basename(file_name))

                info_df = pd.DataFrame(info_data)
                info_df.to_excel(writer, sheet_name="기본 정보", index=False)

                # 유형별 리포트 시트
                loading_dialog.update_progress(40, "상세 리포트 작성 중...")

                if report_type == "summary":
                    # 요약 리포트 시트
                    summary_data = self.create_summary_report_data()
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name="요약 리포트", index=False)

                elif report_type == "differences":
                    # 차이점 리포트 시트
                    diffs_data = self.create_differences_report_data()
                    diffs_df = pd.DataFrame(diffs_data)
                    diffs_df.to_excel(writer, sheet_name="차이점 리포트", index=False)

                elif report_type == "statistics":
                    # 통계 리포트 시트
                    stats_data = self.create_statistics_report_data()
                    stats_df = pd.DataFrame(stats_data)
                    stats_df.to_excel(writer, sheet_name="통계 리포트", index=False)

                # 원본 데이터 시트
                loading_dialog.update_progress(70, "원본 데이터 작성 중...")
                self.merged_df.to_excel(writer, sheet_name="원본 데이터", index=False)

            # 완료
            loading_dialog.update_progress(100, "완료")
            loading_dialog.close()

            # 로그 업데이트
            self.update_log(f"[리포트] '{file_path}'에 리포트가 저장되었습니다.")

            messagebox.showinfo("내보내기 완료", f"리포트가 성공적으로 저장되었습니다.\n\n{file_path}")

        except Exception as e:
            if 'loading_dialog' in locals():
                loading_dialog.close()
            messagebox.showerror("오류", f"리포트 내보내기 중 오류 발생: {str(e)}")

    def create_summary_report_data(self):
        """요약 리포트 데이터 생성"""
        summary_data = {"항목": [], "값": []}

        # 파일별 차이점 통계
        diff_counts = {}
        total_diffs = 0

        for file_idx, file_name in enumerate(self.file_names):
            file_basename = os.path.basename(file_name)
            file_col = f"file_{file_idx}"
            diff_count = 0

            for _, row in self.merged_df.iterrows():
                default_value = row['default_value'] if 'default_value' in row and pd.notna(row['default_value']) else ""
                file_value = row[file_col] if file_col in row and pd.notna(row[file_col]) else ""

                if default_value != file_value:
                    diff_count += 1

            diff_counts[file_basename] = diff_count
            total_diffs += diff_count

        # 데이터 추가
        summary_data["항목"].append("총 파라미터 수")
        summary_data["값"].append(len(self.merged_df))

        summary_data["항목"].append("총 차이점 수")
        summary_data["값"].append(total_diffs)

        for file_name, count in diff_counts.items():
            summary_data["항목"].append(f"파일 '{file_name}'의 차이점 수")
            summary_data["값"].append(count)

        return summary_data

    def create_differences_report_data(self):
        """차이점 리포트 데이터 생성"""
        diffs_data = {"파일": [], "파라미터": [], "차이 유형": [], "Default 값": [], "파일 값": []}

        for file_idx, file_name in enumerate(self.file_names):
            file_basename = os.path.basename(file_name)
            file_col = f"file_{file_idx}"

            for _, row in self.merged_df.iterrows():
                parameter = row['parameter']
                default_value = row['default_value'] if 'default_value' in row and pd.notna(row['default_value']) else ""
                file_value = row[file_col] if file_col in row and pd.notna(row[file_col]) else ""

                # 차이 유형 확인
                if pd.isna(default_value) and pd.notna(file_value):
                    diff_type = "Default DB에 없음"
                    diffs_data["파일"].append(file_basename)
                    diffs_data["파라미터"].append(parameter)
                    diffs_data["차이 유형"].append(diff_type)
                    diffs_data["Default 값"].append("")
                    diffs_data["파일 값"].append(file_value)
                elif pd.notna(default_value) and pd.isna(file_value):
                    diff_type = "파일에 없음"
                    diffs_data["파일"].append(file_basename)
                    diffs_data["파라미터"].append(parameter)
                    diffs_data["차이 유형"].append(diff_type)
                    diffs_data["Default 값"].append(default_value)
                    diffs_data["파일 값"].append("")
                elif default_value != file_value:
                    diff_type = "값 차이"
                    diffs_data["파일"].append(file_basename)
                    diffs_data["파라미터"].append(parameter)
                    diffs_data["차이 유형"].append(diff_type)
                    diffs_data["Default 값"].append(default_value)
                    diffs_data["파일 값"].append(file_value)

        return diffs_data

    def create_statistics_report_data(self):
        """통계 리포트 데이터 생성"""
        stats_data = {
            "파라미터": [], 
            "Default 값": [], 
            "평균": [], 
            "최소값": [], 
            "최대값": [], 
            "표준편차": [], 
            "Default 대비 편차(%)": []
        }

        # 수치형 파라미터만 선택
        for _, row in self.merged_df.iterrows():
            parameter = row['parameter']

            try:
                # default_value가 숫자인지 확인
                default_value = row['default_value'] if 'default_value' in row and pd.notna(row['default_value']) else None
                if default_value is None:
                    continue

                default_value = float(default_value)

                # 파일 값 수집
                file_values = []
                for file_idx in range(len(self.file_names)):
                    file_col = f"file_{file_idx}"
                    if file_col in row and pd.notna(row[file_col]):
                        try:
                            file_values.append(float(row[file_col]))
                        except (ValueError, TypeError):
                            continue

                if not file_values:
                    continue

                # 통계 계산
                mean_value = np.mean(file_values)
                min_value = np.min(file_values)
                max_value = np.max(file_values)
                std_value = np.std(file_values) if len(file_values) > 1 else 0

                # 편차 비율
                deviation_pct = ((mean_value - default_value) / default_value) * 100 if default_value != 0 else 0

                # 데이터 추가
                stats_data["파라미터"].append(parameter)
                stats_data["Default 값"].append(default_value)
                stats_data["평균"].append(mean_value)
                stats_data["최소값"].append(min_value)
                stats_data["최대값"].append(max_value)
                stats_data["표준편차"].append(std_value)
                stats_data["Default 대비 편차(%)"].append(deviation_pct)

            except (ValueError, TypeError):
                continue

        return stats_data

    # 클래스에 함수 추가
    cls.create_report_tab = create_report_tab
    cls.update_report_view = update_report_view
    cls.show_summary_report = show_summary_report
    cls.create_summary_chart = create_summary_chart
    cls.show_differences_report = show_differences_report
    cls.create_differences_chart = create_differences_chart
    cls.show_statistics_report = show_statistics_report
    cls.create_statistics_chart = create_statistics_chart
    cls.export_report = export_report
    cls.create_summary_report_data = create_summary_report_data
    cls.create_differences_report_data = create_differences_report_data
    cls.create_statistics_report_data = create_statistics_report_data
