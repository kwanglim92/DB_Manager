# 간단한 DB 비교 기능

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime


class SimpleComparison:
    """간단한 DB 비교 클래스"""
    
    def __init__(self, manager):
        self.manager = manager
        
    def create_simple_comparison_tab(self):
        """간단한 비교 탭 생성"""
        simple_tab = ttk.Frame(self.manager.comparison_notebook)
        self.manager.comparison_notebook.add(simple_tab, text="간단 비교")
        
        # 상단 컨트롤
        control_frame = ttk.Frame(simple_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            control_frame, 
            text="비교 실행", 
            command=self.perform_simple_comparison
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="차이점만 보기", 
            command=self.show_differences_only
        ).pack(side=tk.LEFT, padx=5)
        
        # 결과 표시
        result_frame = ttk.Frame(simple_tab)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 트리뷰 생성
        columns = ("parameter", "file1", "file2", "status")
        self.comparison_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=20)
        
        # 헤딩 설정
        self.comparison_tree.heading("parameter", text="파라미터")
        self.comparison_tree.heading("file1", text="파일1 값")
        self.comparison_tree.heading("file2", text="파일2 값")
        self.comparison_tree.heading("status", text="상태")
        
        # 컬럼 너비 설정
        self.comparison_tree.column("parameter", width=300)
        self.comparison_tree.column("file1", width=150)
        self.comparison_tree.column("file2", width=150)
        self.comparison_tree.column("status", width=100)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.comparison_tree.yview)
        self.comparison_tree.configure(yscrollcommand=scrollbar.set)
        
        self.comparison_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 색상 태그
        self.comparison_tree.tag_configure("different", background="#FFCDD2")
        self.comparison_tree.tag_configure("same", background="#C8E6C9")
        
    def perform_simple_comparison(self):
        """간단한 비교 수행"""
        if self.manager.merged_df is None or self.manager.merged_df.empty:
            messagebox.showwarning("경고", "비교할 데이터가 없습니다.")
            return
            
        if len(self.manager.file_names) < 2:
            messagebox.showwarning("경고", "비교를 위해서는 최소 2개의 파일이 필요합니다.")
            return
        
        # 트리뷰 초기화
        for item in self.comparison_tree.get_children():
            self.comparison_tree.delete(item)
        
        # 비교 수행
        grouped = self.manager.merged_df.groupby(["Module", "Part", "ItemName"])
        
        same_count = 0
        diff_count = 0
        
        for (module, part, item_name), group in grouped:
            param_name = f"{module}.{part}.{item_name}"
            
            # 첫 번째와 두 번째 파일의 값 비교
            file_names = list(self.manager.file_names)
            if len(file_names) >= 2:
                file1_data = group[group["Model"] == file_names[0]]
                file2_data = group[group["Model"] == file_names[1]]
                
                file1_value = file1_data["ItemValue"].iloc[0] if not file1_data.empty else "N/A"
                file2_value = file2_data["ItemValue"].iloc[0] if not file2_data.empty else "N/A"
                
                # 값 비교
                if str(file1_value) == str(file2_value):
                    status = "동일"
                    tag = "same"
                    same_count += 1
                else:
                    status = "차이"
                    tag = "different"
                    diff_count += 1
                
                # 트리뷰에 추가
                self.comparison_tree.insert("", "end", values=(
                    param_name,
                    str(file1_value),
                    str(file2_value),
                    status
                ), tags=(tag,))
        
        # 결과 로그
        total_count = same_count + diff_count
        self.manager.update_log(
            f"[간단 비교] 총 {total_count}개 파라미터 중 {diff_count}개 차이점 발견"
        )
        
    def show_differences_only(self):
        """차이점만 표시"""
        # 현재 트리뷰에서 동일한 항목들 숨기기
        for item in self.comparison_tree.get_children():
            tags = self.comparison_tree.item(item, 'tags')
            if 'same' in tags:
                self.comparison_tree.detach(item)
        
        self.manager.update_log("[간단 비교] 차이점만 표시")


def add_simple_comparison_to_class(cls):
    """DBManager 클래스에 간단한 비교 기능 추가"""
    
    def create_simple_comparison_features(self):
        """간단한 비교 기능 초기화 (DB 비교 탭용)"""
        self.simple_comparison = SimpleComparison(self)
        self.simple_comparison.create_simple_comparison_tab()
    
    def create_simple_comparison_features_in_qc(self):
        """QC 탭에서 간단한 비교 기능 초기화"""
        if not hasattr(self, 'qc_notebook'):
            return
            
        simple_tab = ttk.Frame(self.qc_notebook)
        self.qc_notebook.add(simple_tab, text="간단 비교")
        
        # 상단 컨트롤
        control_frame = ttk.Frame(simple_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            control_frame, 
            text="비교 실행", 
            command=self.perform_simple_comparison_in_qc
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="차이점만 보기", 
            command=self.show_differences_only_in_qc
        ).pack(side=tk.LEFT, padx=5)
        
        # 결과 표시
        result_frame = ttk.Frame(simple_tab)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 트리뷰 생성
        columns = ("parameter", "file1", "file2", "status")
        self.qc_comparison_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=20)
        
        # 헤딩 설정
        self.qc_comparison_tree.heading("parameter", text="파라미터")
        self.qc_comparison_tree.heading("file1", text="파일1 값")
        self.qc_comparison_tree.heading("file2", text="파일2 값")
        self.qc_comparison_tree.heading("status", text="상태")
        
        # 컬럼 너비 설정
        self.qc_comparison_tree.column("parameter", width=300)
        self.qc_comparison_tree.column("file1", width=150)
        self.qc_comparison_tree.column("file2", width=150)
        self.qc_comparison_tree.column("status", width=100)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.qc_comparison_tree.yview)
        self.qc_comparison_tree.configure(yscrollcommand=scrollbar.set)
        
        self.qc_comparison_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 색상 태그
        self.qc_comparison_tree.tag_configure("different", background="#FFCDD2")
        self.qc_comparison_tree.tag_configure("same", background="#C8E6C9")

    def perform_simple_comparison_in_qc(self):
        """QC 탭에서 간단한 비교 수행"""
        if self.merged_df is None or self.merged_df.empty:
            messagebox.showwarning("경고", "비교할 데이터가 없습니다.")
            return
            
        if len(self.file_names) < 2:
            messagebox.showwarning("경고", "비교를 위해서는 최소 2개의 파일이 필요합니다.")
            return
        
        # 트리뷰 초기화
        for item in self.qc_comparison_tree.get_children():
            self.qc_comparison_tree.delete(item)
        
        # 비교 수행
        grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
        
        same_count = 0
        diff_count = 0
        
        for (module, part, item_name), group in grouped:
            param_name = f"{module}.{part}.{item_name}"
            
            # 첫 번째와 두 번째 파일의 값 비교
            file_names = list(self.file_names)
            if len(file_names) >= 2:
                file1_data = group[group["Model"] == file_names[0]]
                file2_data = group[group["Model"] == file_names[1]]
                
                file1_value = file1_data["ItemValue"].iloc[0] if not file1_data.empty else "N/A"
                file2_value = file2_data["ItemValue"].iloc[0] if not file2_data.empty else "N/A"
                
                # 값 비교
                if str(file1_value) == str(file2_value):
                    status = "동일"
                    tag = "same"
                    same_count += 1
                else:
                    status = "차이"
                    tag = "different"
                    diff_count += 1
                
                # 트리뷰에 추가
                self.qc_comparison_tree.insert("", "end", values=(
                    param_name,
                    str(file1_value),
                    str(file2_value),
                    status
                ), tags=(tag,))
        
        # 결과 로그
        total_count = same_count + diff_count
        self.update_log(
            f"[QC 간단 비교] 총 {total_count}개 파라미터 중 {diff_count}개 차이점 발견"
        )
        
    def show_differences_only_in_qc(self):
        """QC 탭에서 차이점만 표시"""
        # 현재 트리뷰에서 동일한 항목들 숨기기
        for item in self.qc_comparison_tree.get_children():
            tags = self.qc_comparison_tree.item(item, 'tags')
            if 'same' in tags:
                self.qc_comparison_tree.detach(item)
        
        self.update_log("[QC 간단 비교] 차이점만 표시")
    
    # 클래스에 메서드 추가
    cls.create_simple_comparison_features = create_simple_comparison_features
    cls.create_simple_comparison_features_in_qc = create_simple_comparison_features_in_qc
    cls.perform_simple_comparison_in_qc = perform_simple_comparison_in_qc
    cls.show_differences_only_in_qc = show_differences_only_in_qc 