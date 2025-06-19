"""
TreeView 컴포넌트
기존 utils.py의 create_treeview_with_scrollbar 함수를 객체지향 방식으로 개선
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Any, Callable, Tuple

from .base_component import BaseComponent

class TreeViewComponent(BaseComponent):
    """
    스크롤바가 있는 TreeView 컴포넌트
    기존 create_treeview_with_scrollbar 함수와 호환되는 객체지향 버전
    """
    
    def __init__(self, parent: tk.Widget, columns: Tuple[str, ...], 
                 headings: Dict[str, str], column_widths: Dict[str, int],
                 height: Optional[int] = None, **kwargs):
        """
        TreeView 컴포넌트 초기화
        
        Args:
            parent: 부모 위젯
            columns: 컬럼 ID 튜플
            headings: 컬럼 제목 매핑 {컬럼ID: 표시명}
            column_widths: 컬럼 너비 매핑 {컬럼ID: 너비}
            height: TreeView 높이 (행 수)
            **kwargs: 추가 TreeView 옵션
        """
        self.columns = columns
        self.headings = headings
        self.column_widths = column_widths
        self.tree_height = height
        self.tree_options = kwargs
        
        # TreeView 관련 속성
        self.treeview = None
        self.y_scrollbar = None
        self.x_scrollbar = None
        self.data_items = []  # 데이터 아이템 추적
        
        super().__init__(parent)
    
    def _setup_widget(self):
        """TreeView와 스크롤바가 포함된 프레임 생성"""
        # 메인 프레임 생성
        self.widget = ttk.Frame(self.parent)
        
        # 세로 스크롤바 생성
        self.y_scrollbar = ttk.Scrollbar(self.widget)
        self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 가로 스크롤바 생성
        self.x_scrollbar = ttk.Scrollbar(self.widget, orient="horizontal")
        self.x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # TreeView 옵션 설정
        tree_kwargs = {
            'columns': self.columns,
            'show': "headings",
            'yscrollcommand': self.y_scrollbar.set,
            'xscrollcommand': self.x_scrollbar.set
        }
        
        if self.tree_height:
            tree_kwargs['height'] = self.tree_height
        
        # 추가 옵션 병합
        tree_kwargs.update(self.tree_options)
        
        # TreeView 생성
        self.treeview = ttk.Treeview(self.widget, **tree_kwargs)
        self.treeview.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤바 연결
        self.y_scrollbar.config(command=self.treeview.yview)
        self.x_scrollbar.config(command=self.treeview.xview)
    
    def _configure_widget(self):
        """컬럼 설정"""
        for col in self.columns:
            # 컬럼 제목 설정
            heading_text = self.headings.get(col, col)
            self.treeview.heading(col, text=heading_text)
            
            # 컬럼 너비 설정
            width = self.column_widths.get(col, 100)
            self.treeview.column(col, width=width, stretch=True)
    
    def get_treeview(self) -> ttk.Treeview:
        """TreeView 위젯 반환 (기존 코드 호환성)"""
        return self.treeview
    
    def insert_item(self, parent: str = "", index: str = tk.END, 
                   values: Tuple = (), tags: Tuple = (), **kwargs) -> str:
        """
        TreeView에 아이템 삽입
        
        Args:
            parent: 부모 아이템 ID
            index: 삽입 위치
            values: 컬럼 값들
            tags: 태그들
            **kwargs: 추가 옵션
            
        Returns:
            str: 생성된 아이템 ID
        """
        item_id = self.treeview.insert(parent, index, values=values, tags=tags, **kwargs)
        self.data_items.append(item_id)
        return item_id
    
    def update_item(self, item_id: str, values: Tuple = None, **kwargs):
        """아이템 업데이트"""
        if values is not None:
            self.treeview.item(item_id, values=values, **kwargs)
        else:
            self.treeview.item(item_id, **kwargs)
    
    def delete_item(self, item_id: str):
        """아이템 삭제"""
        self.treeview.delete(item_id)
        if item_id in self.data_items:
            self.data_items.remove(item_id)
    
    def clear_all_items(self):
        """모든 아이템 삭제"""
        for item_id in self.treeview.get_children():
            self.treeview.delete(item_id)
        self.data_items.clear()
    
    def get_selected_items(self) -> Tuple[str, ...]:
        """선택된 아이템 ID들 반환"""
        return self.treeview.selection()
    
    def get_item_values(self, item_id: str) -> Tuple:
        """아이템의 값들 반환"""
        return self.treeview.item(item_id, 'values')
    
    def set_item_values(self, item_id: str, values: Tuple):
        """아이템의 값들 설정"""
        self.treeview.item(item_id, values=values)
    
    def get_all_items(self) -> List[str]:
        """모든 아이템 ID 목록 반환"""
        return list(self.treeview.get_children())
    
    def get_item_count(self) -> int:
        """아이템 개수 반환"""
        return len(self.get_all_items())
    
    def bind_treeview_event(self, event: str, callback: Callable):
        """TreeView 이벤트 바인딩"""
        if self.treeview:
            self.treeview.bind(event, callback)
        return self
    
    def bind_double_click(self, callback: Callable):
        """더블클릭 이벤트 바인딩"""
        return self.bind_treeview_event("<Double-1>", callback)
    
    def bind_selection_change(self, callback: Callable):
        """선택 변경 이벤트 바인딩"""
        return self.bind_treeview_event("<<TreeviewSelect>>", callback)
    
    def bind_right_click(self, callback: Callable):
        """우클릭 이벤트 바인딩"""
        return self.bind_treeview_event("<Button-3>", callback)
    
    def configure_column(self, column: str, **options):
        """컬럼 설정 변경"""
        if self.treeview and column in self.columns:
            self.treeview.column(column, **options)
        return self
    
    def configure_heading(self, column: str, **options):
        """컬럼 제목 설정 변경"""
        if self.treeview and column in self.columns:
            self.treeview.heading(column, **options)
        return self
    
    def add_tag_config(self, tag_name: str, **options):
        """태그 스타일 설정"""
        if self.treeview:
            self.treeview.tag_configure(tag_name, **options)
        return self
    
    def sort_by_column(self, column: str, reverse: bool = False):
        """컬럼별 정렬"""
        if not self.treeview or column not in self.columns:
            return
        
        # 현재 아이템들과 값들을 가져오기
        items = [(self.treeview.set(item_id, column), item_id) 
                for item_id in self.treeview.get_children('')]
        
        # 정렬
        items.sort(reverse=reverse)
        
        # 정렬된 순서대로 재배치
        for index, (_, item_id) in enumerate(items):
            self.treeview.move(item_id, '', index)
        
        return self
    
    def filter_items(self, filter_func: Callable[[str], bool]):
        """
        아이템 필터링 (조건에 맞지 않는 아이템 숨기기)
        
        Args:
            filter_func: 아이템 ID를 받아 True/False를 반환하는 함수
        """
        for item_id in self.get_all_items():
            if not filter_func(item_id):
                self.treeview.detach(item_id)
    
    def show_all_items(self):
        """모든 아이템 다시 표시 (필터링 해제)"""
        for item_id in self.data_items:
            try:
                self.treeview.reattach(item_id, '', 'end')
            except tk.TclError:
                # 이미 attached된 경우 무시
                pass
    
    def export_to_list(self) -> List[Dict[str, Any]]:
        """
        TreeView 데이터를 리스트로 익스포트
        
        Returns:
            List[Dict]: 각 행이 딕셔너리인 리스트
        """
        data = []
        for item_id in self.get_all_items():
            values = self.get_item_values(item_id)
            row_data = {}
            for i, col in enumerate(self.columns):
                row_data[col] = values[i] if i < len(values) else ""
            data.append(row_data)
        return data
    
    def load_from_list(self, data: List[Dict[str, Any]], clear_existing: bool = True):
        """
        리스트에서 TreeView로 데이터 로드
        
        Args:
            data: 로드할 데이터 (딕셔너리 리스트)
            clear_existing: 기존 데이터 삭제 여부
        """
        if clear_existing:
            self.clear_all_items()
        
        for row_data in data:
            values = []
            for col in self.columns:
                values.append(str(row_data.get(col, "")))
            self.insert_item(values=tuple(values))
    
    def search_items(self, search_term: str, search_columns: Optional[List[str]] = None) -> List[str]:
        """
        아이템 검색
        
        Args:
            search_term: 검색어
            search_columns: 검색할 컬럼들 (None이면 모든 컬럼)
            
        Returns:
            List[str]: 검색 결과 아이템 ID 목록
        """
        if not search_term:
            return self.get_all_items()
        
        if search_columns is None:
            search_columns = list(self.columns)
        
        matching_items = []
        search_term_lower = search_term.lower()
        
        for item_id in self.get_all_items():
            values = self.get_item_values(item_id)
            
            for i, col in enumerate(self.columns):
                if col in search_columns and i < len(values):
                    cell_value = str(values[i]).lower()
                    if search_term_lower in cell_value:
                        matching_items.append(item_id)
                        break
        
        return matching_items
    
    def highlight_search_results(self, search_term: str, 
                                search_columns: Optional[List[str]] = None,
                                highlight_tag: str = "search_highlight"):
        """
        검색 결과 하이라이트
        
        Args:
            search_term: 검색어
            search_columns: 검색할 컬럼들
            highlight_tag: 하이라이트용 태그명
        """
        # 기존 하이라이트 제거
        for item_id in self.get_all_items():
            tags = list(self.treeview.item(item_id, 'tags'))
            if highlight_tag in tags:
                tags.remove(highlight_tag)
                self.treeview.item(item_id, tags=tags)
        
        if not search_term:
            return
        
        # 검색 결과 하이라이트
        matching_items = self.search_items(search_term, search_columns)
        for item_id in matching_items:
            tags = list(self.treeview.item(item_id, 'tags'))
            if highlight_tag not in tags:
                tags.append(highlight_tag)
                self.treeview.item(item_id, tags=tags)
        
        # 하이라이트 스타일 설정 (노란색 배경)
        self.add_tag_config(highlight_tag, background="yellow")

# TreeView 컴포넌트의 팩토리 함수 (기존 코드와의 호환성을 위해)
def create_enhanced_treeview(parent: tk.Widget, columns: Tuple[str, ...], 
                           headings: Dict[str, str], column_widths: Dict[str, int],
                           height: Optional[int] = None, **kwargs) -> Tuple[ttk.Frame, TreeViewComponent]:
    """
    향상된 TreeView 생성 (기존 create_treeview_with_scrollbar 함수와 호환)
    
    Args:
        parent: 부모 위젯
        columns: 컬럼 ID 튜플
        headings: 컬럼 제목 매핑
        column_widths: 컬럼 너비 매핑
        height: TreeView 높이
        **kwargs: 추가 옵션
    
    Returns:
        Tuple[ttk.Frame, TreeViewComponent]: (프레임, TreeView 컴포넌트)
    """
    tree_component = TreeViewComponent(parent, columns, headings, column_widths, height, **kwargs)
    return tree_component.get_widget(), tree_component 