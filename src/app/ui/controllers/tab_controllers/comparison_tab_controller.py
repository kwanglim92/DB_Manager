"""
DB 비교 탭 컨트롤러
DB 비교 기능을 위한 전용 탭 컨트롤러
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List, Optional

from ..base_controller import TabController
from ...components.treeview_component import TreeViewComponent
from ...components.filter_component import FilterComponent
from ...components.toolbar_component import ToolbarComponent


class ComparisonTabController(TabController):
    """DB 비교 탭 컨트롤러"""
    
    def __init__(self, tab_frame: tk.Frame, viewmodel, tab_name: str = "DB 비교"):
        """ComparisonTabController 초기화"""
        super().__init__(tab_frame, viewmodel, tab_name)
        
        # UI 컴포넌트들
        self.toolbar = None
        self.filter_component = None
        self.comparison_tree = None
        self.details_frame = None
        
        # 상태 변수들
        self.current_filter = ""
        self.show_differences_only = False
        self.show_default_candidates = False
        
        # UI 생성
        self._create_tab_ui()
    
    def _setup_bindings(self):
        """ViewModel 바인딩 설정"""
        super()._setup_bindings()
        
        # 비교 데이터 바인딩
        comparison_data = self.viewmodel.comparison_data
        comparison_data.bind_changed(self._update_comparison_display)
        
        # 필터 관련 바인딩
        self.bind_property_to_view('search_filter', self._update_filter_display)
        self.bind_property_to_view('show_differences_only', self._update_differences_filter)
        self.bind_property_to_view('show_default_candidates', self._update_candidates_display)
        
        # 선택된 항목 바인딩
        selected_items = self.viewmodel.selected_items
        selected_items.bind_changed(self._update_selection_display)
    
    def _setup_view_events(self):
        """View 이벤트 설정"""
        super()._setup_view_events()
        
        # 키보드 단축키
        self.tab_frame.bind('<Control-f>', self._handle_quick_filter)
        self.tab_frame.bind('<F3>', self._handle_find_next)
        self.tab_frame.bind('<Control-d>', self._handle_toggle_differences)
    
    def _create_tab_ui(self):
        """탭 UI 생성"""
        # 상단 툴바
        self._create_toolbar()
        
        # 필터 영역
        self._create_filter_area()
        
        # 메인 비교 영역 (좌우 분할)
        self._create_comparison_area()
        
        # 하단 상세 정보 영역
        self._create_details_area()
    
    def _create_toolbar(self):
        """툴바 생성"""
        toolbar_frame = ttk.Frame(self.tab_frame)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        self.toolbar = ToolbarComponent(toolbar_frame)
        
        # 툴바 버튼들
        self.toolbar.add_button("📁 폴더 열기", self._handle_load_folder, "폴더에서 파일들을 로드합니다")
        self.toolbar.add_separator()
        self.toolbar.add_button("🔄 새로고침", self._handle_refresh, "비교 데이터를 새로고침합니다")
        self.toolbar.add_button("📊 통계", self._handle_show_statistics, "비교 통계를 표시합니다")
        self.toolbar.add_separator()
        self.toolbar.add_button("📤 내보내기", self._handle_export_comparison, "비교 결과를 내보냅니다")
        
        # QC 모드일 때만 표시되는 버튼들
        if self.viewmodel.maint_mode:
            self.toolbar.add_separator()
            self.toolbar.add_button("➕ 설정값 추가", self._handle_add_to_default_db, 
                                   "선택된 항목을 설정값 DB에 추가합니다")
    
    def _create_filter_area(self):
        """필터 영역 생성"""
        filter_frame = ttk.LabelFrame(self.tab_frame, text="🔍 필터 및 옵션")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.filter_component = FilterComponent(filter_frame)
        
        # 검색 필터
        self.filter_component.add_search_filter("검색:", self._handle_filter_change)
        
        # 체크박스 옵션들
        self.filter_component.add_checkbox("차이점만 표시", self._handle_differences_only_change)
        
        # QC 모드일 때만 표시
        if self.viewmodel.maint_mode:
            self.filter_component.add_checkbox("설정값 후보 표시", self._handle_candidates_change)
        
        # 빠른 필터 버튼들
        self.filter_component.add_quick_filter_buttons([
            ("모든 항목", ""),
            ("차이 있음", "different"),
            ("새 항목", "new"),
            ("누락 항목", "missing")
        ], self._handle_quick_filter_select)
    
    def _create_comparison_area(self):
        """메인 비교 영역 생성"""
        # 좌우 분할 팬
        main_paned = ttk.PanedWindow(self.tab_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 좌측: 비교 트리뷰
        left_frame = ttk.LabelFrame(main_paned, text="📊 비교 결과")
        main_paned.add(left_frame, weight=3)
        
        self.comparison_tree = TreeViewComponent(left_frame)
        self.comparison_tree.setup_columns([
            ("parameter", "파라미터", 200),
            ("file_value", "파일 값", 150),
            ("default_value", "설정값", 150),
            ("status", "상태", 100),
            ("difference", "차이", 100)
        ])
        
        # 트리뷰 이벤트 바인딩
        self.comparison_tree.bind_selection_change(self._handle_item_selection)
        self.comparison_tree.bind_double_click(self._handle_item_double_click)
        
        # 우측: 세부 정보 및 통계
        right_frame = ttk.LabelFrame(main_paned, text="ℹ️ 세부 정보")
        main_paned.add(right_frame, weight=1)
        
        self._create_info_panel(right_frame)
    
    def _create_info_panel(self, parent):
        """정보 패널 생성"""
        # 통계 영역
        stats_frame = ttk.LabelFrame(parent, text="📈 통계")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_labels = {}
        for stat_name, display_name in [
            ("total_items", "총 항목"),
            ("different_items", "차이 있음"),
            ("new_items", "새 항목"),
            ("missing_items", "누락 항목"),
            ("match_rate", "일치율")
        ]:
            label = ttk.Label(stats_frame, text=f"{display_name}: -")
            label.pack(anchor=tk.W, padx=5, pady=2)
            self.stats_labels[stat_name] = label
        
        # 선택된 항목 정보
        selection_frame = ttk.LabelFrame(parent, text="🎯 선택된 항목")
        selection_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 스크롤 가능한 텍스트 영역
        text_frame = ttk.Frame(selection_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.selection_text = tk.Text(text_frame, height=10, state=tk.DISABLED, wrap=tk.WORD)
        selection_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.selection_text.yview)
        
        self.selection_text.configure(yscrollcommand=selection_scrollbar.set)
        self.selection_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        selection_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_details_area(self):
        """하단 상세 정보 영역 생성"""
        self.details_frame = ttk.LabelFrame(self.tab_frame, text="📋 상세 비교 정보")
        self.details_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # 상세 정보는 항목 선택 시 동적으로 생성
        placeholder_label = ttk.Label(self.details_frame, 
                                     text="비교 항목을 선택하면 상세 정보가 표시됩니다.")
        placeholder_label.pack(pady=10)
    
    # 이벤트 핸들러들
    def _handle_load_folder(self):
        """폴더 로드 처리"""
        self.viewmodel.execute_command('load_folder')
    
    def _handle_refresh(self):
        """새로고침 처리"""
        self.viewmodel.execute_command('update_comparison_view')
    
    def _handle_show_statistics(self):
        """통계 표시 처리"""
        self.viewmodel.execute_command('calculate_statistics')
    
    def _handle_export_comparison(self):
        """비교 결과 내보내기 처리"""
        self.viewmodel.execute_command('export_report')
    
    def _handle_add_to_default_db(self):
        """설정값 DB 추가 처리"""
        selected_items = self.comparison_tree.get_selected_items()
        if selected_items:
            self.viewmodel.execute_command('add_to_default_db', selected_items)
    
    def _handle_filter_change(self, filter_text: str):
        """필터 변경 처리"""
        self.current_filter = filter_text
        self.viewmodel.execute_command('toggle_search_filter', filter_text)
    
    def _handle_differences_only_change(self, checked: bool):
        """차이점만 표시 변경 처리"""
        self.show_differences_only = checked
        self.viewmodel.execute_command('toggle_differences_only')
    
    def _handle_candidates_change(self, checked: bool):
        """설정값 후보 표시 변경 처리"""
        self.show_default_candidates = checked
        if self.viewmodel.maint_mode:
            self.viewmodel.execute_command('toggle_default_candidates')
    
    def _handle_quick_filter_select(self, filter_type: str):
        """빠른 필터 선택 처리"""
        self.filter_component.set_filter_text(filter_type)
        self._handle_filter_change(filter_type)
    
    def _handle_item_selection(self, selected_items: List[Dict]):
        """항목 선택 처리"""
        # 선택된 항목을 ViewModel에 업데이트
        self.viewmodel.selected_items.clear()
        for item in selected_items:
            self.viewmodel.selected_items.append(item)
    
    def _handle_item_double_click(self, item: Dict):
        """항목 더블 클릭 처리"""
        if self.viewmodel.maint_mode:
            # QC 모드에서는 편집 가능
            self._show_edit_dialog(item)
        else:
            # 일반 모드에서는 상세 정보 표시
            self._show_detail_dialog(item)
    
    def _handle_quick_filter(self, event=None):
        """빠른 필터 단축키 처리"""
        self.filter_component.focus_search()
    
    def _handle_find_next(self, event=None):
        """다음 찾기 처리"""
        # 현재 필터로 다음 항목 찾기
        pass
    
    def _handle_toggle_differences(self, event=None):
        """차이점만 표시 토글 처리"""
        current = self.filter_component.get_checkbox_state("차이점만 표시")
        self.filter_component.set_checkbox_state("차이점만 표시", not current)
        self._handle_differences_only_change(not current)
    
    # UI 업데이트 메서드들
    def _update_comparison_display(self):
        """비교 데이터 표시 업데이트"""
        if not self.comparison_tree:
            return
        
        comparison_data = self.viewmodel.comparison_data
        
        # 트리뷰 클리어
        self.comparison_tree.clear()
        
        # 데이터 추가
        for item in comparison_data:
            self.comparison_tree.add_item(item)
        
        # 통계 업데이트
        self._update_statistics_display()
    
    def _update_filter_display(self, filter_text: str):
        """필터 표시 업데이트"""
        if self.filter_component:
            self.filter_component.set_filter_text(filter_text)
    
    def _update_differences_filter(self, show_differences: bool):
        """차이점만 표시 필터 업데이트"""
        if self.filter_component:
            self.filter_component.set_checkbox_state("차이점만 표시", show_differences)
        
        # 트리뷰 필터링 적용
        if self.comparison_tree:
            self.comparison_tree.apply_filter("differences_only", show_differences)
    
    def _update_candidates_display(self, show_candidates: bool):
        """설정값 후보 표시 업데이트"""
        if self.filter_component and self.viewmodel.maint_mode:
            self.filter_component.set_checkbox_state("설정값 후보 표시", show_candidates)
    
    def _update_selection_display(self):
        """선택된 항목 표시 업데이트"""
        if not self.selection_text:
            return
        
        selected_items = self.viewmodel.selected_items
        
        # 텍스트 업데이트
        self.selection_text.configure(state=tk.NORMAL)
        self.selection_text.delete(1.0, tk.END)
        
        if len(selected_items) == 0:
            self.selection_text.insert(tk.END, "선택된 항목이 없습니다.")
        else:
            for i, item in enumerate(selected_items):
                self.selection_text.insert(tk.END, f"[{i+1}] {item.get('parameter', 'Unknown')}\n")
                self.selection_text.insert(tk.END, f"    파일 값: {item.get('file_value', '-')}\n")
                self.selection_text.insert(tk.END, f"    설정값: {item.get('default_value', '-')}\n")
                self.selection_text.insert(tk.END, f"    상태: {item.get('status', '-')}\n\n")
        
        self.selection_text.configure(state=tk.DISABLED)
    
    def _update_statistics_display(self):
        """통계 표시 업데이트"""
        if not hasattr(self, 'stats_labels'):
            return
        
        comparison_data = self.viewmodel.comparison_data
        
        # 통계 계산
        total = len(comparison_data)
        different = sum(1 for item in comparison_data if item.get('status') == 'different')
        new_items = sum(1 for item in comparison_data if item.get('status') == 'new')
        missing = sum(1 for item in comparison_data if item.get('status') == 'missing')
        match_rate = ((total - different - new_items - missing) / total * 100) if total > 0 else 0
        
        # 라벨 업데이트
        self.stats_labels['total_items'].config(text=f"총 항목: {total:,}")
        self.stats_labels['different_items'].config(text=f"차이 있음: {different:,}")
        self.stats_labels['new_items'].config(text=f"새 항목: {new_items:,}")
        self.stats_labels['missing_items'].config(text=f"누락 항목: {missing:,}")
        self.stats_labels['match_rate'].config(text=f"일치율: {match_rate:.1f}%")
    
    def _show_edit_dialog(self, item: Dict):
        """편집 다이얼로그 표시 (QC 모드)"""
        # 향후 구현
        self.show_info("편집", f"'{item.get('parameter', 'Unknown')}' 편집 기능은 향후 구현됩니다.")
    
    def _show_detail_dialog(self, item: Dict):
        """상세 정보 다이얼로그 표시"""
        detail_text = f"""파라미터: {item.get('parameter', 'Unknown')}
파일 값: {item.get('file_value', '-')}
설정값: {item.get('default_value', '-')}
상태: {item.get('status', '-')}
차이: {item.get('difference', '-')}"""
        
        self.show_info("상세 정보", detail_text)
    
    def on_tab_activated(self):
        """탭 활성화 시 호출"""
        super().on_tab_activated()
        
        # 비교 데이터 새로고침
        if self.viewmodel.has_files_loaded():
            self.viewmodel.execute_command('update_comparison_view')
    
    def get_tab_title(self) -> str:
        """탭 제목 반환"""
        file_count = self.viewmodel.get_file_count()
        if file_count > 0:
            return f"📊 DB 비교 ({file_count}개 파일)"
        return "📊 DB 비교"