"""
변경 이력 관리 기능을 위한 헬퍼 모듈

이 모듈은 DBManager 클래스에 변경 이력 관리 기능을 추가하는 함수들을 제공합니다.
런타임에 DBManager 클래스에 기능을 추가하는 방식으로 동작합니다.
"""

import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import pandas as pd
from common_utils import create_treeview_with_scrollbar, create_label_entry_pair

def add_change_history_functions_to_class(cls):
    """
    DBManager 클래스에 변경 이력 관리 기능을 추가합니다.
    
    Args:
        cls: 기능을 추가할 클래스 (DBManager)
    """
    
    def create_change_history_tab(self):
        """
        변경 이력 관리 탭을 생성합니다.
        변경 이력 조회 및 시각화 기능을 제공합니다.
        """
        history_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(history_tab, text="변경 이력 관리")
        
        # 좌측 프레임 (필터 및 조회)
        left_frame = ttk.LabelFrame(history_tab, text="변경 이력 조회", width=300, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 날짜 범위 선택
        date_frame = ttk.Frame(left_frame)
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="시작 날짜:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.start_date_var = tk.StringVar()
        ttk.Entry(date_frame, textvariable=self.start_date_var, width=12).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(date_frame, text="(YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        
        ttk.Label(date_frame, text="종료 날짜:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.end_date_var = tk.StringVar()
        ttk.Entry(date_frame, textvariable=self.end_date_var, width=12).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(date_frame, text="(YYYY-MM-DD)").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        # 항목 유형 선택
        type_frame = ttk.Frame(left_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="항목 유형:").pack(side=tk.LEFT, padx=5)
        self.item_type_var = tk.StringVar(value="all")
        ttk.Radiobutton(type_frame, text="전체", variable=self.item_type_var, value="all").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="장비 유형", variable=self.item_type_var, value="equipment_type").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="파라미터", variable=self.item_type_var, value="parameter").pack(side=tk.LEFT, padx=5)
        
        # 변경 유형 선택
        change_frame = ttk.Frame(left_frame)
        change_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(change_frame, text="변경 유형:").pack(side=tk.LEFT, padx=5)
        self.change_type_var = tk.StringVar(value="all")
        ttk.Radiobutton(change_frame, text="전체", variable=self.change_type_var, value="all").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(change_frame, text="추가", variable=self.change_type_var, value="add").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(change_frame, text="수정", variable=self.change_type_var, value="update").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(change_frame, text="삭제", variable=self.change_type_var, value="delete").pack(side=tk.LEFT, padx=5)
        
        # 조회 버튼
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="조회", command=self.load_change_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="내보내기", command=self.export_change_history).pack(side=tk.LEFT, padx=5)
        
        # 변경 이력 트리뷰
        columns = ("timestamp", "change_type", "item_type", "item_name", "old_value", "new_value", "changed_by")
        headings = {
            "timestamp": "변경 시간", 
            "change_type": "변경 유형", 
            "item_type": "항목 유형",
            "item_name": "항목 이름",
            "old_value": "변경 전 값",
            "new_value": "변경 후 값",
            "changed_by": "변경자"
        }
        column_widths = {
            "timestamp": 150, 
            "change_type": 80, 
            "item_type": 100,
            "item_name": 150,
            "old_value": 120,
            "new_value": 120,
            "changed_by": 80
        }
        
        history_frame, self.history_tree = create_treeview_with_scrollbar(
            left_frame, columns, headings, column_widths, height=15)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 우측 프레임 (시각화)
        right_frame = ttk.LabelFrame(history_tab, text="변경 이력 시각화", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 그래프 영역 생성
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # 캔버스 생성 및 배치
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 초기 데이터 로드
        self.load_change_history()
    
    def load_change_history(self):
        """변경 이력을 로드하고 표시합니다."""
        try:
            # 필터 조건 가져오기
            start_date = self.start_date_var.get() if self.start_date_var.get() else None
            end_date = self.end_date_var.get() if self.end_date_var.get() else None
            item_type = None if self.item_type_var.get() == "all" else self.item_type_var.get()
            change_type = None if self.change_type_var.get() == "all" else self.change_type_var.get()
            
            # 변경 이력 조회
            history_data = self.db_schema.get_change_history(start_date, end_date, item_type, change_type)
            
            # 트리뷰 초기화
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # 트리뷰에 데이터 추가
            for row in history_data:
                id, change_type, item_type, item_name, old_value, new_value, changed_by, timestamp = row
                
                # 변경 유형에 따라 아이콘 설정
                icon = ""
                if change_type == "add":
                    icon = "➕"
                elif change_type == "update":
                    icon = "🔄"
                elif change_type == "delete":
                    icon = "❌"
                
                # 항목 유형 변환
                if item_type == "equipment_type":
                    item_type_display = "장비 유형"
                elif item_type == "parameter":
                    item_type_display = "파라미터"
                else:
                    item_type_display = item_type
                
                # 변경 유형 변환
                if change_type == "add":
                    change_type_display = "추가"
                elif change_type == "update":
                    change_type_display = "수정"
                elif change_type == "delete":
                    change_type_display = "삭제"
                else:
                    change_type_display = change_type
                
                self.history_tree.insert(
                    "", tk.END, 
                    values=(timestamp, f"{icon} {change_type_display}", item_type_display, item_name, 
                            old_value, new_value, changed_by),
                    tags=(str(id),)
                )
            
            # 시각화
            self.visualize_change_history(history_data)
            
        except Exception as e:
            messagebox.showerror("오류", f"변경 이력 로드 중 오류 발생: {str(e)}")
            self.update_log(f"변경 이력 로드 오류: {str(e)}")
    
    def visualize_change_history(self, history_data):
        """변경 이력을 시각화합니다."""
        try:
            self.ax.clear()
            
            if not history_data:
                self.ax.text(0.5, 0.5, "데이터가 없습니다", ha='center', va='center')
                self.canvas.draw()
                return
            
            # 데이터프레임 변환
            df = pd.DataFrame(history_data, columns=[
                'id', 'change_type', 'item_type', 'item_name', 
                'old_value', 'new_value', 'changed_by', 'timestamp'
            ])
            
            # 날짜 변환
            df['date'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('date')
            
            # 변경 유형별 카운트
            add_counts = df[df['change_type'] == 'add'].groupby(df['date'].dt.date).size()
            update_counts = df[df['change_type'] == 'update'].groupby(df['date'].dt.date).size()
            delete_counts = df[df['change_type'] == 'delete'].groupby(df['date'].dt.date).size()
            
            # 날짜 범위 설정
            date_range = pd.date_range(start=min(df['date']), end=max(df['date']))
            
            # 플롯 생성
            if not add_counts.empty:
                self.ax.plot(add_counts.index, add_counts.values, 'g-', marker='o', label='추가')
            if not update_counts.empty:
                self.ax.plot(update_counts.index, update_counts.values, 'b-', marker='s', label='수정')
            if not delete_counts.empty:
                self.ax.plot(delete_counts.index, delete_counts.values, 'r-', marker='x', label='삭제')
            
            # 그래프 설정
            self.ax.set_xlabel('날짜')
            self.ax.set_ylabel('변경 횟수')
            self.ax.set_title('시간에 따른 변경 이력')
            self.ax.legend()
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            # x축 날짜 포맷 설정
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            self.fig.autofmt_xdate()
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"시각화 오류: {str(e)}")
            self.ax.clear()
            self.ax.text(0.5, 0.5, f"시각화 오류: {str(e)}", ha='center', va='center')
            self.canvas.draw()
    
    def export_change_history(self):
        """변경 이력을 CSV 파일로 내보냅니다."""
        try:
            # 필터 조건 가져오기
            start_date = self.start_date_var.get() if self.start_date_var.get() else None
            end_date = self.end_date_var.get() if self.end_date_var.get() else None
            item_type = None if self.item_type_var.get() == "all" else self.item_type_var.get()
            change_type = None if self.change_type_var.get() == "all" else self.change_type_var.get()
            
            # 변경 이력 조회
            history_data = self.db_schema.get_change_history(start_date, end_date, item_type, change_type)
            
            if not history_data:
                messagebox.showinfo("알림", "내보낼 데이터가 없습니다.")
                return
            
            # 저장 경로 선택
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
                title="변경 이력 내보내기"
            )
            
            if not file_path:
                return
            
            # 데이터프레임 변환
            df = pd.DataFrame(history_data, columns=[
                'id', 'change_type', 'item_type', 'item_name', 
                'old_value', 'new_value', 'changed_by', 'timestamp'
            ])
            
            # 변경 유형 변환
            df['change_type'] = df['change_type'].replace({
                'add': '추가',
                'update': '수정',
                'delete': '삭제'
            })
            
            # 항목 유형 변환
            df['item_type'] = df['item_type'].replace({
                'equipment_type': '장비 유형',
                'parameter': '파라미터'
            })
            
            # 열 이름 변환
            df.columns = [
                'ID', '변경 유형', '항목 유형', '항목 이름',
                '변경 전 값', '변경 후 값', '변경자', '변경 시간'
            ]
            
            # CSV로 저장
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("알림", f"변경 이력이 {file_path}에 저장되었습니다.")
            
        except Exception as e:
            messagebox.showerror("오류", f"변경 이력 내보내기 중 오류 발생: {str(e)}")
            self.update_log(f"변경 이력 내보내기 오류: {str(e)}")
    
    # 클래스에 메서드 추가
    cls.create_change_history_tab = create_change_history_tab
    cls.load_change_history = load_change_history
    cls.visualize_change_history = visualize_change_history
    cls.export_change_history = export_change_history
    
    return cls
