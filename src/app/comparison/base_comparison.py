"""
비교 기능의 기본 클래스
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
import pandas as pd


class BaseComparison(ABC):
    """비교 기능의 기본 추상 클래스"""
    
    def __init__(self, manager):
        """
        Args:
            manager: DBManager 인스턴스 참조
        """
        self.manager = manager
        self.comparison_data = None
        self.tree = None
        self.frame = None
    
    @abstractmethod
    def create_ui(self, parent_frame):
        """UI를 생성합니다."""
        pass
    
    @abstractmethod
    def update_view(self, data=None):
        """뷰를 업데이트합니다."""
        pass
    
    @abstractmethod
    def process_data(self, file_data):
        """데이터를 처리합니다."""
        pass
    
    def create_treeview_with_scrollbar(self, parent, columns, headings, column_widths=None, height=20):
        """
        트리뷰와 스크롤바를 생성하는 공통 메서드
        """
        from app.utils import create_treeview_with_scrollbar
        return create_treeview_with_scrollbar(parent, columns, headings, column_widths, height)
    
    def setup_context_menu(self, tree):
        """컨텍스트 메뉴를 설정하는 공통 메서드"""
        context_menu = tk.Menu(tree, tearoff=0)
        context_menu.add_command(label="복사", command=lambda: self.copy_selected_item(tree))
        context_menu.add_command(label="내보내기", command=lambda: self.export_selected_items(tree))
        
        def show_context_menu(event):
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
        
        tree.bind("<Button-3>", show_context_menu)  # 우클릭
        return context_menu
    
    def copy_selected_item(self, tree):
        """선택된 항목을 클립보드에 복사"""
        selection = tree.selection()
        if selection:
            item = tree.item(selection[0])
            values = item['values']
            if values:
                # 탭으로 구분된 텍스트로 클립보드에 복사
                text = '\\t'.join(str(v) for v in values)
                self.manager.window.clipboard_clear()
                self.manager.window.clipboard_append(text)
                self.manager.update_log("선택된 항목이 클립보드에 복사되었습니다.")
    
    def export_selected_items(self, tree):
        """선택된 항목들을 파일로 내보내기"""
        from tkinter import filedialog
        import csv
        
        selection = tree.selection()
        if not selection:
            self.manager.update_log("내보낼 항목을 선택해주세요.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="비교 결과 내보내기",
            defaultextension=".csv",
            filetypes=[("CSV 파일", "*.csv"), ("텍스트 파일", "*.txt")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # 헤더 작성
                    columns = [tree.heading(col)['text'] for col in tree['columns']]
                    writer.writerow(columns)
                    
                    # 선택된 데이터 작성
                    for item_id in selection:
                        item = tree.item(item_id)
                        writer.writerow(item['values'])
                
                self.manager.update_log(f"비교 결과가 {filename}으로 내보내졌습니다.")
            except Exception as e:
                self.manager.update_log(f"내보내기 실패: {str(e)}")
    
    def filter_data(self, data, search_filter=""):
        """데이터를 필터링하는 공통 메서드"""
        if not search_filter or data is None:
            return data
        
        if isinstance(data, pd.DataFrame):
            # DataFrame의 경우 텍스트 컬럼에서 검색
            mask = data.astype(str).apply(
                lambda x: x.str.contains(search_filter, case=False, na=False)
            ).any(axis=1)
            return data[mask]
        
        return data
    
    def get_difference_color(self, value1, value2):
        """값의 차이에 따른 색상을 반환"""
        if pd.isna(value1) or pd.isna(value2):
            return "#FFE6E6"  # 연한 빨강 (결측값)
        
        if str(value1) != str(value2):
            return "#FFEEAA"  # 연한 노랑 (차이)
        
        return "#FFFFFF"  # 흰색 (동일)