# 고급 DB 비교 및 분석 기능

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.simpledialog as simpledialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import json
import os
from app.utils import create_treeview_with_scrollbar, format_num_value
from app.loading import LoadingDialog

class AdvancedComparison:
    """고급 DB 비교 및 분석 클래스"""
    
    def __init__(self, manager):
        self.manager = manager
        self.comparison_profiles = {}
        self.tolerance_settings = {}
        
    def create_advanced_analysis_tab(self):
        """고급 분석 탭 생성"""
        analysis_tab = ttk.Frame(self.manager.comparison_notebook)
        self.manager.comparison_notebook.add(analysis_tab, text="고급 분석")
        
        # 상단 제어 패널
        control_frame = ttk.LabelFrame(analysis_tab, text="분석 옵션", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 분석 유형 선택
        ttk.Label(control_frame, text="분석 유형:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.analysis_type_var = tk.StringVar(value="통계적 비교")
        analysis_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.analysis_type_var,
            values=["통계적 비교", "수치 범위 분석", "패턴 분석", "상관관계 분석"],
            state="readonly", 
            width=20
        )
        analysis_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 허용 오차 설정
        ttk.Label(control_frame, text="허용 오차 (%):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.tolerance_var = tk.StringVar(value="5.0")
        tolerance_entry = ttk.Entry(control_frame, textvariable=self.tolerance_var, width=10)
        tolerance_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # 분석 실행 버튼
        analyze_btn = ttk.Button(
            control_frame, 
            text="분석 실행", 
            command=self.perform_advanced_analysis
        )
        analyze_btn.grid(row=0, column=4, padx=10, pady=5)
        
        # 프로파일 저장/불러오기
        profile_frame = ttk.Frame(control_frame)
        profile_frame.grid(row=1, column=0, columnspan=5, pady=5, sticky="ew")
        
        ttk.Button(profile_frame, text="프로파일 저장", command=self.save_comparison_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(profile_frame, text="프로파일 불러오기", command=self.load_comparison_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(profile_frame, text="보고서 생성", command=self.generate_detailed_report).pack(side=tk.LEFT, padx=5)
        
        # 결과 표시 영역
        result_frame = ttk.LabelFrame(analysis_tab, text="분석 결과", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 결과 노트북 (탭)
        self.result_notebook = ttk.Notebook(result_frame)
        self.result_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 분석 결과 탭들 생성
        self.create_analysis_result_tabs()
        
    def create_analysis_result_tabs(self):
        """분석 결과 탭들 생성"""
        # 1. 상세 비교 결과 탭
        detail_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(detail_tab, text="상세 비교")
        
        columns = ("parameter", "file1_value", "file2_value", "difference", "percentage", "status")
        headings = {
            "parameter": "파라미터",
            "file1_value": "파일1 값",
            "file2_value": "파일2 값", 
            "difference": "차이값",
            "percentage": "차이율(%)",
            "status": "상태"
        }
        column_widths = {
            "parameter": 200,
            "file1_value": 100,
            "file2_value": 100,
            "difference": 100,
            "percentage": 80,
            "status": 80
        }
        
        detail_tree_frame, self.detail_tree = create_treeview_with_scrollbar(
            detail_tab, columns, headings, column_widths, height=15
        )
        detail_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 2. 통계 요약 탭
        stats_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(stats_tab, text="통계 요약")
        
        # 통계 정보 표시 영역
        self.stats_text = tk.Text(stats_tab, height=20, wrap=tk.WORD)
        stats_scroll = ttk.Scrollbar(stats_tab, orient="vertical", command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scroll.set)
        
        stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 3. 시각화 탭
        chart_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(chart_tab, text="시각화")
        
        self.chart_frame = ttk.Frame(chart_tab)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def perform_advanced_analysis(self):
        """고급 분석 수행"""
        if self.manager.merged_df is None or self.manager.merged_df.empty:
            messagebox.showwarning("경고", "분석할 데이터가 없습니다. 먼저 파일을 로드해주세요.")
            return
            
        if len(self.manager.file_names) < 2:
            messagebox.showwarning("경고", "비교를 위해서는 최소 2개의 파일이 필요합니다.")
            return
        
        try:
            loading_dialog = LoadingDialog(self.manager.window)
            loading_dialog.update_progress(10, "분석 데이터 준비 중...")
            
            analysis_type = self.analysis_type_var.get()
            tolerance = float(self.tolerance_var.get())
            
            # 분석 수행
            if analysis_type == "통계적 비교":
                results = self.perform_statistical_comparison(tolerance)
            elif analysis_type == "수치 범위 분석":
                results = self.perform_range_analysis(tolerance)
            elif analysis_type == "패턴 분석":
                results = self.perform_pattern_analysis()
            elif analysis_type == "상관관계 분석":
                results = self.perform_correlation_analysis()
            
            loading_dialog.update_progress(70, "결과 표시 중...")
            
            # 결과 표시
            self.display_analysis_results(results, analysis_type)
            
            loading_dialog.update_progress(100, "완료")
            loading_dialog.close()
            
            self.manager.update_log(f"[고급 분석] {analysis_type} 완료")
            
        except ValueError:
            messagebox.showerror("오류", "허용 오차는 숫자여야 합니다.")
        except Exception as e:
            if 'loading_dialog' in locals():
                loading_dialog.close()
            messagebox.showerror("오류", f"분석 중 오류 발생: {str(e)}")
    
    def perform_statistical_comparison(self, tolerance):
        """통계적 비교 수행"""
        results = {
            'details': [],
            'summary': {},
            'charts': []
        }
        
        grouped = self.manager.merged_df.groupby(["Module", "Part", "ItemName"])
        
        total_params = 0
        different_params = 0
        within_tolerance = 0
        
        for (module, part, item_name), group in grouped:
            param_name = f"{module}.{part}.{item_name}"
            
            # 수치 데이터만 분석
            numeric_values = []
            file_values = {}
            
            for model in self.manager.file_names:
                model_data = group[group["Model"] == model]
                if not model_data.empty:
                    value_str = str(model_data["ItemValue"].iloc[0])
                    file_values[model] = value_str
                    
                    # 숫자로 변환 시도
                    try:
                        numeric_val = float(value_str)
                        numeric_values.append(numeric_val)
                    except (ValueError, TypeError):
                        pass
            
            total_params += 1
            
            if len(numeric_values) >= 2:
                # 통계 계산
                mean_val = np.mean(numeric_values)
                std_val = np.std(numeric_values)
                min_val = np.min(numeric_values)
                max_val = np.max(numeric_values)
                
                # 차이율 계산
                if mean_val != 0:
                    diff_percentage = (std_val / abs(mean_val)) * 100
                else:
                    diff_percentage = 0
                
                # 상태 판정
                if std_val == 0:
                    status = "동일"
                elif diff_percentage <= tolerance:
                    status = "허용범위"
                    within_tolerance += 1
                else:
                    status = "주의필요"
                    different_params += 1
                
                # 상세 결과 추가
                results['details'].append({
                    'parameter': param_name,
                    'values': file_values,
                    'mean': mean_val,
                    'std': std_val,
                    'min': min_val,
                    'max': max_val,
                    'diff_percentage': diff_percentage,
                    'status': status
                })
        
        # 요약 통계
        results['summary'] = {
            'total_parameters': total_params,
            'different_parameters': different_params,
            'within_tolerance': within_tolerance,
            'tolerance_rate': (within_tolerance / total_params * 100) if total_params > 0 else 0
        }
        
        return results
    
    def perform_range_analysis(self, tolerance):
        """수치 범위 분석 수행"""
        results = {
            'details': [],
            'summary': {},
            'charts': []
        }
        
        # Default DB에서 허용 범위 정보 가져오기
        if hasattr(self.manager, 'db_schema') and self.manager.db_schema:
            try:
                equipment_types = self.manager.db_schema.get_equipment_types()
                default_ranges = {}
                
                for type_id, type_name, _ in equipment_types:
                    default_values = self.manager.db_schema.get_default_values(type_id)
                    for _, param_name, default_val, min_spec, max_spec, _ in default_values:
                        default_ranges[param_name] = {
                            'default': default_val,
                            'min': min_spec,
                            'max': max_spec
                        }
            except:
                default_ranges = {}
        else:
            default_ranges = {}
        
        grouped = self.manager.merged_df.groupby(["Module", "Part", "ItemName"])
        
        for (module, part, item_name), group in grouped:
            param_name = f"{module}.{part}.{item_name}"
            param_key = f"{part}_{item_name}"
            
            # 수치 값들 수집
            numeric_values = []
            for model in self.manager.file_names:
                model_data = group[group["Model"] == model]
                if not model_data.empty:
                    try:
                        value = float(model_data["ItemValue"].iloc[0])
                        numeric_values.append(value)
                    except (ValueError, TypeError):
                        pass
            
            if numeric_values:
                current_min = min(numeric_values)
                current_max = max(numeric_values)
                current_range = current_max - current_min
                
                # Default DB 범위와 비교
                range_status = "정상"
                if param_key in default_ranges:
                    default_info = default_ranges[param_key]
                    try:
                        spec_min = float(default_info['min']) if default_info['min'] else None
                        spec_max = float(default_info['max']) if default_info['max'] else None
                        
                        if spec_min is not None and current_min < spec_min:
                            range_status = "최소값 미만"
                        elif spec_max is not None and current_max > spec_max:
                            range_status = "최대값 초과"
                    except (ValueError, TypeError):
                        pass
                
                results['details'].append({
                    'parameter': param_name,
                    'current_min': current_min,
                    'current_max': current_max,
                    'current_range': current_range,
                    'spec_min': default_ranges.get(param_key, {}).get('min', 'N/A'),
                    'spec_max': default_ranges.get(param_key, {}).get('max', 'N/A'),
                    'status': range_status
                })
        
        return results
    
    def perform_pattern_analysis(self):
        """패턴 분석 수행"""
        results = {
            'details': [],
            'summary': {},
            'charts': []
        }
        
        # 파라미터별 패턴 분석
        grouped = self.manager.merged_df.groupby(["Module", "Part", "ItemName"])
        
        for (module, part, item_name), group in grouped:
            param_name = f"{module}.{part}.{item_name}"
            
            # 각 파일의 값 수집
            values = []
            for model in self.manager.file_names:
                model_data = group[group["Model"] == model]
                if not model_data.empty:
                    try:
                        value = float(model_data["ItemValue"].iloc[0])
                        values.append(value)
                    except (ValueError, TypeError):
                        values.append(None)
                else:
                    values.append(None)
            
            # 패턴 분석
            non_null_values = [v for v in values if v is not None]
            if len(non_null_values) >= 2:
                # 추세 분석 (증가/감소/변동)
                if len(non_null_values) == len(values):
                    differences = [non_null_values[i+1] - non_null_values[i] for i in range(len(non_null_values)-1)]
                    
                    # 수치만 비교하도록 타입 체크 추가
                    if all(isinstance(d, (int, float)) and d > 0 for d in differences):
                        pattern = "증가 추세"
                    elif all(isinstance(d, (int, float)) and d < 0 for d in differences):
                        pattern = "감소 추세"
                    elif all(isinstance(d, (int, float)) and abs(d) < 0.001 for d in differences):
                        pattern = "일정"
                    else:
                        pattern = "변동"
                else:
                    pattern = "불완전 데이터"
                
                results['details'].append({
                    'parameter': param_name,
                    'pattern': pattern,
                    'values': values,
                    'non_null_count': len(non_null_values)
                })
        
        return results
    
    def perform_correlation_analysis(self):
        """상관관계 분석 수행"""
        results = {
            'details': [],
            'summary': {},
            'charts': []
        }
        
        # 수치 데이터만 추출하여 상관관계 분석
        numeric_data = {}
        
        grouped = self.manager.merged_df.groupby(["Module", "Part", "ItemName"])
        
        for (module, part, item_name), group in grouped:
            param_name = f"{module}.{part}.{item_name}"
            
            values = []
            for model in self.manager.file_names:
                model_data = group[group["Model"] == model]
                if not model_data.empty:
                    try:
                        value = float(model_data["ItemValue"].iloc[0])
                        values.append(value)
                    except (ValueError, TypeError):
                        values.append(np.nan)
                else:
                    values.append(np.nan)
            
            # 모든 값이 유효한 경우만 포함
            if not all(np.isnan(values)):
                numeric_data[param_name] = values
        
        # 상관관계 매트릭스 계산
        if len(numeric_data) >= 2:
            df_corr = pd.DataFrame(numeric_data)
            correlation_matrix = df_corr.corr()
            
            # 높은 상관관계 찾기 (절댓값 0.7 이상)
            high_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if not np.isnan(corr_value) and abs(corr_value) >= 0.7:
                        high_correlations.append({
                            'param1': correlation_matrix.columns[i],
                            'param2': correlation_matrix.columns[j],
                            'correlation': corr_value,
                            'strength': '강한 양의 상관관계' if corr_value > 0.7 else '강한 음의 상관관계'
                        })
            
            results['details'] = high_correlations
            results['correlation_matrix'] = correlation_matrix
        
        return results
    
    def display_analysis_results(self, results, analysis_type):
        """분석 결과 표시"""
        # 상세 결과 트리뷰 업데이트
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
        
        if analysis_type == "통계적 비교":
            for detail in results['details']:
                # 첫 번째와 두 번째 파일 값 비교
                file_names = list(detail['values'].keys())
                if len(file_names) >= 2:
                    val1 = detail['values'][file_names[0]]
                    val2 = detail['values'][file_names[1]]
                    
                    try:
                        num_val1 = float(val1)
                        num_val2 = float(val2)
                        difference = num_val2 - num_val1
                        
                        self.detail_tree.insert("", "end", values=(
                            detail['parameter'],
                            val1,
                            val2,
                            f"{difference:.4f}",
                            f"{detail['diff_percentage']:.2f}",
                            detail['status']
                        ), tags=(detail['status'].lower(),))
                    except (ValueError, TypeError):
                        self.detail_tree.insert("", "end", values=(
                            detail['parameter'],
                            val1,
                            val2,
                            "N/A",
                            "N/A",
                            "비수치"
                        ))
        elif analysis_type == "상관관계 분석":
            for detail in results['details']:
                self.detail_tree.insert("", "end", values=(
                    detail['param1'],
                    detail['param2'],
                    f"{detail['correlation']:.3f}",
                    detail['strength'],
                    "",
                    ""
                ))
        
        # 상태별 색상 설정
        self.detail_tree.tag_configure("동일", background="#C8E6C9")
        self.detail_tree.tag_configure("허용범위", background="#FFF9C4")
        self.detail_tree.tag_configure("주의필요", background="#FFCDD2")
        
        # 통계 요약 업데이트
        self.stats_text.delete(1.0, tk.END)
        
        if 'summary' in results:
            summary = results['summary']
            stats_report = f"""
=== 분석 요약 ===
분석 유형: {analysis_type}
분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 전체 통계 ===
총 파라미터 수: {summary.get('total_parameters', 0)}
차이가 있는 파라미터: {summary.get('different_parameters', 0)}
허용 범위 내 파라미터: {summary.get('within_tolerance', 0)}
허용 범위 준수율: {summary.get('tolerance_rate', 0):.2f}%

=== 상세 분석 ===
"""
            for detail in results['details'][:10]:  # 상위 10개만 표시
                stats_report += f"""
파라미터: {detail['parameter']}
상태: {detail['status']}
"""
                if 'diff_percentage' in detail:
                    stats_report += f"차이율: {detail['diff_percentage']:.2f}%\n"
            
            self.stats_text.insert(tk.END, stats_report)
        
        # 차트 생성
        self.create_analysis_charts(results, analysis_type)
    
    def create_analysis_charts(self, results, analysis_type):
        """분석 차트 생성"""
        # 기존 차트 제거
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        if analysis_type == "통계적 비교" and 'summary' in results:
            # 파이 차트 생성
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # 상태별 분포 차트
            summary = results['summary']
            status_counts = {'동일': 0, '허용범위': 0, '주의필요': 0}
            
            for detail in results['details']:
                status = detail['status']
                if status in status_counts:
                    status_counts[status] += 1
            
            labels = list(status_counts.keys())
            sizes = list(status_counts.values())
            colors = ['#4CAF50', '#FFC107', '#F44336']
            
            ax1.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            ax1.set_title('파라미터 상태 분포')
            
            # 차이율 히스토그램
            diff_percentages = [d['diff_percentage'] for d in results['details'] if 'diff_percentage' in d]
            if diff_percentages:
                ax2.hist(diff_percentages, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
                ax2.set_xlabel('차이율 (%)')
                ax2.set_ylabel('빈도')
                ax2.set_title('차이율 분포')
                ax2.axvline(float(self.tolerance_var.get()), color='red', linestyle='--', label='허용 오차')
                ax2.legend()
            
            plt.tight_layout()
            
            # tkinter에 차트 표시
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def save_comparison_profile(self):
        """비교 프로파일 저장"""
        profile_name = simpledialog.askstring("프로파일 저장", "프로파일 이름을 입력하세요:")
        if not profile_name:
            return
        
        profile = {
            'name': profile_name,
            'analysis_type': self.analysis_type_var.get(),
            'tolerance': self.tolerance_var.get(),
            'created_at': datetime.now().isoformat(),
            'file_names': self.manager.file_names
        }
        
        # 프로파일 파일에 저장
        profiles_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'comparison_profiles.json')
        
        try:
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
            else:
                profiles = {}
            
            profiles[profile_name] = profile
            
            os.makedirs(os.path.dirname(profiles_file), exist_ok=True)
            with open(profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("성공", f"프로파일 '{profile_name}'이 저장되었습니다.")
            self.manager.update_log(f"[프로파일] '{profile_name}' 저장됨")
            
        except Exception as e:
            messagebox.showerror("오류", f"프로파일 저장 중 오류 발생: {str(e)}")
    
    def load_comparison_profile(self):
        """비교 프로파일 불러오기"""
        profiles_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'comparison_profiles.json')
        
        if not os.path.exists(profiles_file):
            messagebox.showinfo("알림", "저장된 프로파일이 없습니다.")
            return
        
        try:
            with open(profiles_file, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
            
            if not profiles:
                messagebox.showinfo("알림", "저장된 프로파일이 없습니다.")
                return
            
            # 프로파일 선택 대화상자
            profile_names = list(profiles.keys())
            selected_profile = simpledialog.askstring(
                "프로파일 불러오기", 
                f"불러올 프로파일을 선택하세요:\n{', '.join(profile_names)}"
            )
            
            if selected_profile and selected_profile in profiles:
                profile = profiles[selected_profile]
                
                # 프로파일 설정 적용
                self.analysis_type_var.set(profile.get('analysis_type', '통계적 비교'))
                self.tolerance_var.set(profile.get('tolerance', '5.0'))
                
                messagebox.showinfo("성공", f"프로파일 '{selected_profile}'이 불러와졌습니다.")
                self.manager.update_log(f"[프로파일] '{selected_profile}' 불러옴")
            
        except Exception as e:
            messagebox.showerror("오류", f"프로파일 불러오기 중 오류 발생: {str(e)}")
    
    def generate_detailed_report(self):
        """상세 보고서 생성"""
        if not hasattr(self, 'detail_tree') or not self.detail_tree.get_children():
            messagebox.showwarning("경고", "생성할 보고서 데이터가 없습니다. 먼저 분석을 실행해주세요.")
            return
        
        # 파일 저장 대화상자
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")],
            title="상세 보고서 저장"
        )
        
        if not file_path:
            return
        
        try:
            # 보고서 데이터 수집
            report_data = []
            for item_id in self.detail_tree.get_children():
                values = self.detail_tree.item(item_id, 'values')
                report_data.append(list(values))
            
            # 데이터프레임 생성
            columns = ["파라미터", "파일1 값", "파일2 값", "차이값", "차이율(%)", "상태"]
            df = pd.DataFrame(report_data, columns=columns)
            
            # 메타데이터 추가
            metadata = {
                "분석 유형": [self.analysis_type_var.get()],
                "허용 오차": [f"{self.tolerance_var.get()}%"],
                "분석 일시": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "분석 파일": [", ".join(self.manager.file_names)]
            }
            meta_df = pd.DataFrame(metadata)
            
            # Excel 파일로 저장
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                meta_df.to_excel(writer, sheet_name="분석 정보", index=False)
                df.to_excel(writer, sheet_name="상세 비교 결과", index=False)
            
            messagebox.showinfo("성공", f"상세 보고서가 저장되었습니다.\n{file_path}")
            self.manager.update_log(f"[보고서] 상세 분석 보고서 생성: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("오류", f"보고서 생성 중 오류 발생: {str(e)}")

def add_advanced_comparison_to_class(cls):
    """DBManager 클래스에 고급 비교 기능 추가"""
    
    def create_advanced_comparison_features(self):
        """고급 비교 기능 초기화 (DB 비교 탭용)"""
        self.advanced_comparison = AdvancedComparison(self)
        self.advanced_comparison.create_advanced_analysis_tab()
    
    def create_advanced_comparison_features_in_qc(self):
        """QC 탭에서 고급 분석 기능 초기화"""
        if not hasattr(self, 'qc_notebook'):
            return
            
        # QC 노트북을 사용하는 고급 분석 인스턴스 생성
        self.qc_advanced_comparison = AdvancedComparisonForQC(self)
        self.qc_advanced_comparison.create_advanced_analysis_tab_in_qc()
    
    # 클래스에 메서드 추가
    cls.create_advanced_comparison_features = create_advanced_comparison_features
    cls.create_advanced_comparison_features_in_qc = create_advanced_comparison_features_in_qc


class AdvancedComparisonForQC(AdvancedComparison):
    """QC 탭용 고급 비교 및 분석 클래스"""
    
    def create_advanced_analysis_tab_in_qc(self):
        """QC 노트북에 고급 분석 탭 생성"""
        if not hasattr(self.manager, 'qc_notebook'):
            return
            
        analysis_tab = ttk.Frame(self.manager.qc_notebook)
        self.manager.qc_notebook.add(analysis_tab, text="고급 분석")
        
        # 상단 제어 패널
        control_frame = ttk.LabelFrame(analysis_tab, text="분석 옵션", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 분석 유형 선택
        ttk.Label(control_frame, text="분석 유형:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.analysis_type_var = tk.StringVar(value="통계적 비교")
        analysis_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.analysis_type_var,
            values=["통계적 비교", "수치 범위 분석", "패턴 분석", "상관관계 분석"],
            state="readonly", 
            width=20
        )
        analysis_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 허용 오차 설정
        ttk.Label(control_frame, text="허용 오차 (%):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.tolerance_var = tk.StringVar(value="5.0")
        tolerance_entry = ttk.Entry(control_frame, textvariable=self.tolerance_var, width=10)
        tolerance_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # 분석 실행 버튼
        analyze_btn = ttk.Button(
            control_frame, 
            text="분석 실행", 
            command=self.perform_advanced_analysis
        )
        analyze_btn.grid(row=0, column=4, padx=10, pady=5)
        
        # 결과 표시 영역
        result_frame = ttk.LabelFrame(analysis_tab, text="분석 결과", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 결과 노트북 (탭)
        self.result_notebook = ttk.Notebook(result_frame)
        self.result_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 분석 결과 탭들 생성
        self.create_analysis_result_tabs()
        
        # 간소화된 프로파일 버튼들
        profile_frame = ttk.Frame(control_frame)
        profile_frame.grid(row=1, column=0, columnspan=5, pady=5, sticky="ew")
        
        ttk.Button(profile_frame, text="결과 내보내기", command=self.export_qc_analysis_results).pack(side=tk.LEFT, padx=5)
    
    def export_qc_analysis_results(self):
        """QC 분석 결과를 CSV로 내보내기"""
        if not hasattr(self, 'detail_tree') or not self.detail_tree.get_children():
            messagebox.showwarning("경고", "내보낼 분석 결과가 없습니다. 먼저 분석을 실행해주세요.")
            return
        
        # 파일 저장 대화상자
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
            title="QC 분석 결과 저장"
        )
        
        if not file_path:
            return
        
        try:
            import csv
            
            # 분석 결과 데이터 수집
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # 헤더 작성
                writer.writerow(["파라미터", "파일1 값", "파일2 값", "차이값", "차이율(%)", "상태"])
                
                # 데이터 작성
                for item_id in self.detail_tree.get_children():
                    values = self.detail_tree.item(item_id, 'values')
                    writer.writerow(values)
            
            messagebox.showinfo("성공", f"QC 분석 결과가 저장되었습니다.\n{file_path}")
            self.manager.update_log(f"[QC 고급 분석] 결과 내보내기: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("오류", f"결과 내보내기 중 오류 발생: {str(e)}") 