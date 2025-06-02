# 이 파일은 리팩토링되어 실제 코드는 app/qc.py에서 확인하세요.
# 프로그램 실행은 main.py를 사용하세요.

"""
이 모듈은 DBManager 클래스에 QC 검수 기능을 추가하는 함수들을 제공합니다.
런타임에 DBManager 클래스에 기능을 추가하는 방식으로 동작합니다.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from LoadingDialog import LoadingDialog
from common_utils import create_treeview_with_scrollbar

def add_qc_check_functions_to_class(cls):
    """
    DBManager 클래스에 QC 검수 기능을 추가합니다.

    Args:
        cls: 기능을 추가할 클래스 (DBManager)
    """

    def create_qc_check_tab(self):
        """QC 검수 탭을 생성합니다."""
        qc_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(qc_tab, text="QC 검수")
        
        # 상단 프레임 - 검수 대상 선택 및 검수 버튼
        top_frame = ttk.LabelFrame(qc_tab, text="검수 대상 선택", padding=10)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 장비 유형 선택
        type_frame = ttk.Frame(top_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="장비 유형:").pack(side=tk.LEFT, padx=5)
        self.qc_type_var = tk.StringVar()
        self.qc_type_combobox = ttk.Combobox(type_frame, textvariable=self.qc_type_var, state="readonly", width=30)
        self.qc_type_combobox.pack(side=tk.LEFT, padx=5)
        
        # 검수 버튼
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="검수 실행", command=self.perform_qc_check).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="검수 결과 내보내기", command=self.export_qc_results).pack(side=tk.LEFT, padx=5)
        
        # 중간 프레임 - 검수 결과 표시
        middle_frame = ttk.LabelFrame(qc_tab, text="검수 결과", padding=10)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 검수 결과 트리뷰
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
        
        # 하단 프레임 - 통계 및 차트
        bottom_frame = ttk.LabelFrame(qc_tab, text="검수 통계", padding=10)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 통계 정보 표시 영역
        self.stats_frame = ttk.Frame(bottom_frame)
        self.stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 차트 표시 영역
        self.chart_frame = ttk.Frame(bottom_frame)
        self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 장비 유형 목록 로드
        self.load_equipment_types_for_qc()
    
    def load_equipment_types_for_qc(self):
        """QC 검수를 위한 장비 유형 목록을 로드합니다."""
        try:
            equipment_types = self.db_schema.get_equipment_types()
            type_names = [name for _, name, _ in equipment_types]
            
            self.qc_type_combobox['values'] = type_names
            if type_names:
                self.qc_type_combobox.current(0)
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 로드 중 오류 발생: {str(e)}")
            self.update_log(f"장비 유형 로드 오류: {str(e)}")
    
    def perform_qc_check(self):
        """선택한 장비 유형에 대한 QC 검수를 수행합니다."""
        selected_type = self.qc_type_var.get()
        if not selected_type:
            messagebox.showinfo("알림", "검수할 장비 유형을 선택하세요.")
            return
        
        # 로딩 다이얼로그 표시
        loading_dialog = LoadingDialog(self.window)
        loading_dialog.update_progress(0, "QC 검수 준비 중...")
        
        try:
            # 장비 유형 ID 조회
            equipment_types = self.db_schema.get_equipment_types()
            type_id = None
            for id, name, _ in equipment_types:
                if name == selected_type:
                    type_id = id
                    break
            
            if not type_id:
                messagebox.showerror("오류", "선택한 장비 유형을 찾을 수 없습니다.")
                return
            
            loading_dialog.update_progress(10, f"{selected_type} 파라미터 로드 중...")
            
            # 파라미터 정보 조회
            parameters = self.db_schema.get_default_values(type_id)
            
            # QC 검수 수행
            loading_dialog.update_progress(20, "QC 검수 수행 중...")
            qc_results = []
            
            # 파라미터별 검수 수행
            total_params = len(parameters)
            for i, (value_id, param_name, default_val, min_val, max_val, _) in enumerate(parameters):
                progress = 20 + (i / total_params * 60)
                loading_dialog.update_progress(progress, f"파라미터 검사 중: {param_name}")
                
                # 1. 필수값 검사
                if default_val is None or default_val == "":
                    qc_results.append({
                        'parameter': param_name,
                        'issue_type': '필수값 누락',
                        'description': '기본값이 설정되지 않았습니다.',
                        'severity': '높음',
                        'value_id': value_id
                    })
                
                # 2. 값 범위 검사
                if min_val is not None and max_val is not None:
                    try:
                        min_val_float = float(min_val)
                        max_val_float = float(max_val)
                        
                        if min_val_float >= max_val_float:
                            qc_results.append({
                                'parameter': param_name,
                                'issue_type': '범위 오류',
                                'description': f'최소값({min_val})이 최대값({max_val})보다 크거나 같습니다.',
                                'severity': '높음',
                                'value_id': value_id
                            })
                    except ValueError:
                        qc_results.append({
                            'parameter': param_name,
                            'issue_type': '형식 오류',
                            'description': '최소값 또는 최대값이 숫자 형식이 아닙니다.',
                            'severity': '중간',
                            'value_id': value_id
                        })
                
                # 3. 기본값 범위 검사
                if default_val:
                    try:
                        default_val_float = float(default_val)
                        
                        if min_val is not None:
                            min_val_float = float(min_val)
                            if default_val_float < min_val_float:
                                qc_results.append({
                                    'parameter': param_name,
                                    'issue_type': '기본값 범위 오류',
                                    'description': f'기본값({default_val})이 최소값({min_val})보다 작습니다.',
                                    'severity': '중간',
                                    'value_id': value_id
                                })
                        
                        if max_val is not None:
                            max_val_float = float(max_val)
                            if default_val_float > max_val_float:
                                qc_results.append({
                                    'parameter': param_name,
                                    'issue_type': '기본값 범위 오류',
                                    'description': f'기본값({default_val})이 최대값({max_val})보다 큽니다.',
                                    'severity': '중간',
                                    'value_id': value_id
                                })
                    except ValueError:
                        qc_results.append({
                            'parameter': param_name,
                            'issue_type': '형식 오류',
                            'description': '기본값이 숫자 형식이 아닙니다.',
                            'severity': '낮음',
                            'value_id': value_id
                        })
            
            # 검수 결과 표시
            loading_dialog.update_progress(80, "검수 결과 표시 중...")
            self.display_qc_results(qc_results, selected_type, total_params)
            
            loading_dialog.update_progress(100, "QC 검수 완료")
            
        except Exception as e:
            messagebox.showerror("오류", f"QC 검수 중 오류 발생: {str(e)}")
            self.update_log(f"QC 검수 오류: {str(e)}")
        finally:
            loading_dialog.close()
    
    def display_qc_results(self, qc_results, type_name, total_params):
        """QC 검수 결과를 화면에 표시합니다."""
        # 트리뷰 초기화
        self.qc_result_tree.delete(*self.qc_result_tree.get_children())
        
        # 결과 추가
        for result in qc_results:
            self.qc_result_tree.insert(
                "", tk.END, 
                values=(result['parameter'], result['issue_type'], 
                        result['description'], result['severity']),
                tags=(str(result['value_id']),)
            )
        
        # 통계 정보 표시
        self.display_qc_statistics(qc_results, type_name, total_params)
        
        # 로그 업데이트
        self.update_log(f"QC 검수 완료: {type_name}, 발견된 문제: {len(qc_results)}개")
    
    def display_qc_statistics(self, qc_results, type_name, total_params):
        """QC 검수 통계 정보를 표시합니다."""
        # 기존 위젯 제거
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # 통계 계산
        total_issues = len(qc_results)
        issue_types = {}
        severity_counts = {'높음': 0, '중간': 0, '낮음': 0}
        
        for result in qc_results:
            issue_type = result['issue_type']
            severity = result['severity']
            
            if issue_type in issue_types:
                issue_types[issue_type] += 1
            else:
                issue_types[issue_type] = 1
            
            severity_counts[severity] += 1
        
        # 통계 정보 표시
        ttk.Label(self.stats_frame, text=f"장비 유형: {type_name}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=2)
        ttk.Label(self.stats_frame, text=f"전체 파라미터: {total_params}개").pack(anchor=tk.W, pady=2)
        ttk.Label(self.stats_frame, text=f"발견된 문제: {total_issues}개").pack(anchor=tk.W, pady=2)
        ttk.Label(self.stats_frame, text=f"문제 비율: {total_issues/total_params*100:.1f}%").pack(anchor=tk.W, pady=2)
        
        ttk.Separator(self.stats_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        ttk.Label(self.stats_frame, text="심각도별 문제:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=2)
        for severity, count in severity_counts.items():
            if count > 0:
                ttk.Label(self.stats_frame, text=f"{severity}: {count}개").pack(anchor=tk.W, pady=2)
        
        ttk.Separator(self.stats_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        ttk.Label(self.stats_frame, text="문제 유형별 개수:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, pady=2)
        for issue_type, count in issue_types.items():
            ttk.Label(self.stats_frame, text=f"{issue_type}: {count}개").pack(anchor=tk.W, pady=2)
        
        # 차트 표시
        if total_issues > 0:
            self.create_qc_charts(issue_types, severity_counts)
    
    def create_qc_charts(self, issue_types, severity_counts):
        """QC 검수 결과를 차트로 표시합니다."""
        fig = plt.Figure(figsize=(8, 6), dpi=100)
        
        # 문제 유형별 차트
        ax1 = fig.add_subplot(211)
        issue_labels = list(issue_types.keys())
        issue_values = list(issue_types.values())
        ax1.bar(issue_labels, issue_values, color='skyblue')
        ax1.set_title('문제 유형별 개수')
        ax1.set_ylabel('개수')
        plt.setp(ax1.get_xticklabels(), rotation=30, ha='right')
        
        # 심각도별 차트
        ax2 = fig.add_subplot(212)
        severity_labels = list(severity_counts.keys())
        severity_values = list(severity_counts.values())
        colors = ['red', 'orange', 'green']
        ax2.pie(severity_values, labels=severity_labels, autopct='%1.1f%%', 
                startangle=90, colors=colors)
        ax2.set_title('심각도별 비율')
        ax2.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        # 차트 표시
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def export_qc_results(self):
        """QC 검수 결과를 Excel 파일로 내보냅니다."""
        selected_type = self.qc_type_var.get()
        if not selected_type:
            messagebox.showinfo("알림", "내보낼 검수 결과가 없습니다.")
            return
        
        # 결과 데이터 수집
        results = []
        for item in self.qc_result_tree.get_children():
            values = self.qc_result_tree.item(item, 'values')
            results.append({
                '파라미터': values[0],
                '문제 유형': values[1],
                '설명': values[2],
                '심각도': values[3]
            })
        
        if not results:
            messagebox.showinfo("알림", "내보낼 검수 결과가 없습니다.")
            return
        
        # 저장 경로 선택
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx")],
            initialfile=f"QC_검수결과_{selected_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
        if not file_path:
            return
        
        try:
            # DataFrame 생성 및 Excel 저장
            df = pd.DataFrame(results)
            df.to_excel(file_path, index=False, sheet_name="QC 검수 결과")
            
            messagebox.showinfo("알림", f"검수 결과가 저장되었습니다.\n{file_path}")
            self.update_log(f"QC 검수 결과 내보내기 완료: {file_path}")
        except Exception as e:
            messagebox.showerror("오류", f"결과 내보내기 중 오류 발생: {str(e)}")
            self.update_log(f"QC 검수 결과 내보내기 오류: {str(e)}")
    
    # 클래스에 메서드 추가
    cls.create_qc_check_tab = create_qc_check_tab
    cls.load_equipment_types_for_qc = load_equipment_types_for_qc
    cls.perform_qc_check = perform_qc_check
    cls.display_qc_results = display_qc_results
    cls.display_qc_statistics = display_qc_statistics
    cls.create_qc_charts = create_qc_charts
    cls.export_qc_results = export_qc_results
    
    return cls
