"""
QC 검수 탭 컨트롤러
QC 기능을 위한 전용 탭 컨트롤러
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List, Optional

from ..base_controller import TabController
from ...components.treeview_component import TreeViewComponent
from ...components.toolbar_component import ToolbarComponent
from ...components.filter_component import FilterComponent


class QCTabController(TabController):
    """QC 검수 탭 컨트롤러"""
    
    def __init__(self, tab_frame: tk.Frame, viewmodel, tab_name: str = "QC 검수"):
        """QCTabController 초기화"""
        super().__init__(tab_frame, viewmodel, tab_name)
        
        # UI 컴포넌트들
        self.toolbar = None
        self.equipment_selector = None
        self.qc_results_tree = None
        self.details_panel = None
        
        # 상태 변수들
        self.current_equipment_type = None
        self.qc_status = "ready"  # ready, running, complete, error
        
        # UI 생성
        self._create_tab_ui()
    
    def _setup_bindings(self):
        """ViewModel 바인딩 설정"""
        super()._setup_bindings()
        
        # QC 결과 바인딩
        qc_results = self.viewmodel.qc_results
        qc_results.bind_changed(self._update_qc_results_display)
        
        # 장비 유형 바인딩
        equipment_types = self.viewmodel.equipment_types
        equipment_types.bind_changed(self._update_equipment_types)
        
        # 선택된 장비 유형 바인딩
        self.bind_property_to_view('selected_equipment_type_id', self._update_selected_equipment)
    
    def _setup_view_events(self):
        """View 이벤트 설정"""
        super()._setup_view_events()
        
        # 키보드 단축키
        self.tab_frame.bind('<F5>', self._handle_run_qc_check)
        self.tab_frame.bind('<Control-s>', self._handle_save_results)
        self.tab_frame.bind('<Control-e>', self._handle_export_results)
    
    def _create_tab_ui(self):
        """탭 UI 생성"""
        # 상단 툴바
        self._create_toolbar()
        
        # 장비 선택 영역
        self._create_equipment_selector()
        
        # 메인 QC 결과 영역
        self._create_qc_results_area()
        
        # 하단 세부 정보 영역
        self._create_details_area()
    
    def _create_toolbar(self):
        """툴바 생성"""
        toolbar_frame = ttk.Frame(self.tab_frame)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        self.toolbar = ToolbarComponent(toolbar_frame)
        
        # QC 관련 버튼들
        self.toolbar.add_button("🔍 QC 검수 실행", self._handle_run_qc_check, 
                               "현재 선택된 장비 유형에 대해 QC 검수를 실행합니다", "primary")
        self.toolbar.add_separator()
        self.toolbar.add_button("📋 결과 저장", self._handle_save_results, 
                               "QC 검수 결과를 저장합니다")
        self.toolbar.add_button("📤 결과 내보내기", self._handle_export_results, 
                               "QC 검수 결과를 파일로 내보냅니다")
        self.toolbar.add_separator()
        self.toolbar.add_button("🔄 새로고침", self._handle_refresh_data, 
                               "데이터를 새로고침합니다")
        self.toolbar.add_spacer()
        
        # 진행률 표시줄
        self.progress_bar = self.toolbar.add_progress_bar(200)
        self.toolbar.add_label("준비", "default")
    
    def _create_equipment_selector(self):
        """장비 선택 영역 생성"""
        selector_frame = ttk.LabelFrame(self.tab_frame, text="🏭 장비 유형 선택")
        selector_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 장비 유형 콤보박스
        selection_frame = ttk.Frame(selector_frame)
        selection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(selection_frame, text="장비 유형:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.equipment_var = tk.StringVar()
        self.equipment_selector = ttk.Combobox(selection_frame, textvariable=self.equipment_var,
                                              state="readonly", width=30)
        self.equipment_selector.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.equipment_selector.bind('<<ComboboxSelected>>', self._handle_equipment_selection)
        
        # 장비 관리 버튼들
        ttk.Button(selection_frame, text="➕ 추가", 
                  command=self._handle_add_equipment_type).pack(side=tk.LEFT, padx=2)
        ttk.Button(selection_frame, text="✏️ 편집", 
                  command=self._handle_edit_equipment_type).pack(side=tk.LEFT, padx=2)
        ttk.Button(selection_frame, text="🗑️ 삭제", 
                  command=self._handle_delete_equipment_type).pack(side=tk.LEFT, padx=2)
    
    def _create_qc_results_area(self):
        """QC 결과 영역 생성"""
        # 좌우 분할 팬
        main_paned = ttk.PanedWindow(self.tab_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 좌측: QC 결과 트리뷰
        left_frame = ttk.LabelFrame(main_paned, text="📊 QC 검수 결과")
        main_paned.add(left_frame, weight=3)
        
        self.qc_results_tree = TreeViewComponent(left_frame)
        self.qc_results_tree.setup_columns([
            ("parameter", "파라미터", 200),
            ("expected", "예상 값", 120),
            ("actual", "실제 값", 120),
            ("status", "상태", 80),
            ("deviation", "편차", 80),
            ("tolerance", "허용 오차", 80),
            ("severity", "심각도", 80)
        ])
        
        # 트리뷰 이벤트 바인딩
        self.qc_results_tree.bind_selection_change(self._handle_result_selection)
        self.qc_results_tree.bind_double_click(self._handle_result_double_click)
        
        # 우측: 통계 및 요약
        right_frame = ttk.LabelFrame(main_paned, text="📈 QC 요약")
        main_paned.add(right_frame, weight=1)
        
        self._create_qc_summary_panel(right_frame)
    
    def _create_qc_summary_panel(self, parent):
        """QC 요약 패널 생성"""
        # 전체 통계
        stats_frame = ttk.LabelFrame(parent, text="📊 전체 통계")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.qc_stats_labels = {}
        for stat_name, display_name in [
            ("total_checks", "총 검수 항목"),
            ("passed", "통과"),
            ("warnings", "경고"),
            ("failures", "실패"),
            ("pass_rate", "통과율")
        ]:
            label = ttk.Label(stats_frame, text=f"{display_name}: -")
            label.pack(anchor=tk.W, padx=5, pady=2)
            self.qc_stats_labels[stat_name] = label
        
        # 심각도별 통계
        severity_frame = ttk.LabelFrame(parent, text="⚠️ 심각도별 통계")
        severity_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.severity_labels = {}
        for severity in ["Critical", "High", "Medium", "Low"]:
            label = ttk.Label(severity_frame, text=f"{severity}: -")
            label.pack(anchor=tk.W, padx=5, pady=2)
            self.severity_labels[severity] = label
        
        # 최근 검수 이력
        history_frame = ttk.LabelFrame(parent, text="📅 최근 검수 이력")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.history_text = tk.Text(history_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        history_scrollbar = ttk.Scrollbar(history_frame, orient="vertical", 
                                         command=self.history_text.yview)
        
        self.history_text.configure(yscrollcommand=history_scrollbar.set)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_details_area(self):
        """세부 정보 영역 생성"""
        self.details_panel = ttk.LabelFrame(self.tab_frame, text="📋 선택된 항목 세부 정보")
        self.details_panel.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # 상세 정보는 항목 선택 시 동적으로 생성
        placeholder_label = ttk.Label(self.details_panel, 
                                     text="QC 검수 항목을 선택하면 세부 정보가 표시됩니다.")
        placeholder_label.pack(pady=10)
    
    # 이벤트 핸들러들
    def _handle_run_qc_check(self, event=None):
        """QC 검수 실행 처리"""
        if not self.current_equipment_type:
            self.show_warning("알림", "장비 유형을 먼저 선택해주세요.")
            return
        
        self.qc_status = "running"
        self._update_status_display("QC 검수 실행 중...")
        
        # ViewModel 명령 실행
        self.viewmodel.execute_command('run_qc_check', {
            'equipment_type_id': self.current_equipment_type,
            'callback': self._qc_check_complete
        })
    
    def _handle_save_results(self):
        """결과 저장 처리"""
        if not self.viewmodel.qc_results:
            self.show_warning("알림", "저장할 QC 검수 결과가 없습니다.")
            return
        
        self.viewmodel.execute_command('save_qc_results')
        self.show_info("성공", "QC 검수 결과가 저장되었습니다.")
    
    def _handle_export_results(self):
        """결과 내보내기 처리"""
        if not self.viewmodel.qc_results:
            self.show_warning("알림", "내보낼 QC 검수 결과가 없습니다.")
            return
        
        self.viewmodel.execute_command('export_qc_results')
    
    def _handle_refresh_data(self):
        """데이터 새로고침 처리"""
        self.viewmodel.execute_command('load_equipment_types')
        if self.current_equipment_type:
            self._handle_run_qc_check()
    
    def _handle_equipment_selection(self, event=None):
        """장비 선택 처리"""
        selected = self.equipment_var.get()
        if selected:
            # 장비 유형 ID 찾기
            for equipment in self.viewmodel.equipment_types:
                if equipment.get('name') == selected:
                    self.current_equipment_type = equipment.get('id')
                    self.viewmodel.selected_equipment_type_id = self.current_equipment_type
                    break
            
            # 자동으로 QC 검수 실행
            self._handle_run_qc_check()
    
    def _handle_add_equipment_type(self):
        """장비 유형 추가 처리"""
        self.viewmodel.execute_command('add_equipment_type')
    
    def _handle_edit_equipment_type(self):
        """장비 유형 편집 처리"""
        if not self.current_equipment_type:
            self.show_warning("알림", "편집할 장비 유형을 선택해주세요.")
            return
        
        self.viewmodel.execute_command('edit_equipment_type', self.current_equipment_type)
    
    def _handle_delete_equipment_type(self):
        """장비 유형 삭제 처리"""
        if not self.current_equipment_type:
            self.show_warning("알림", "삭제할 장비 유형을 선택해주세요.")
            return
        
        result = self.show_confirm("확인", "선택된 장비 유형을 삭제하시겠습니까?")
        if result:
            self.viewmodel.execute_command('delete_equipment_type', self.current_equipment_type)
    
    def _handle_result_selection(self, selected_items: List[Dict]):
        """QC 결과 선택 처리"""
        if selected_items:
            self._show_result_details(selected_items[0])
    
    def _handle_result_double_click(self, item: Dict):
        """QC 결과 더블 클릭 처리"""
        # 상세 분석 창 표시
        self._show_detailed_analysis_dialog(item)
    
    def _qc_check_complete(self, success: bool, results: Dict):
        """QC 검수 완료 콜백"""
        if success:
            self.qc_status = "complete"
            self._update_status_display("QC 검수 완료")
        else:
            self.qc_status = "error"
            self._update_status_display("QC 검수 실패")
            self.show_error("오류", f"QC 검수 중 오류가 발생했습니다: {results.get('error', '알 수 없는 오류')}")
    
    # UI 업데이트 메서드들
    def _update_qc_results_display(self):
        """QC 결과 표시 업데이트"""
        if not self.qc_results_tree:
            return
        
        qc_results = self.viewmodel.qc_results
        
        # 트리뷰 클리어
        self.qc_results_tree.clear()
        
        # 결과 데이터 추가
        for result in qc_results:
            # 상태에 따른 색상 지정
            tags = []
            status = result.get('status', 'unknown')
            if status == 'PASS':
                tags.append('pass')
            elif status == 'FAIL':
                tags.append('fail')
            elif status == 'WARNING':
                tags.append('warning')
            
            self.qc_results_tree.add_item(result, tags=tags)
        
        # 색상 태그 설정
        tree_widget = self.qc_results_tree.tree
        tree_widget.tag_configure('pass', background='#d4edda', foreground='#155724')
        tree_widget.tag_configure('fail', background='#f8d7da', foreground='#721c24')
        tree_widget.tag_configure('warning', background='#fff3cd', foreground='#856404')
        
        # 통계 업데이트
        self._update_qc_statistics_display()
    
    def _update_equipment_types(self):
        """장비 유형 목록 업데이트"""
        if not self.equipment_selector:
            return
        
        equipment_types = self.viewmodel.equipment_types
        type_names = [equipment.get('name', '') for equipment in equipment_types]
        
        self.equipment_selector['values'] = type_names
        
        # 현재 선택된 항목 유지
        if self.current_equipment_type:
            for equipment in equipment_types:
                if equipment.get('id') == self.current_equipment_type:
                    self.equipment_var.set(equipment.get('name', ''))
                    break
    
    def _update_selected_equipment(self, equipment_type_id: int):
        """선택된 장비 유형 업데이트"""
        self.current_equipment_type = equipment_type_id
        
        # 콤보박스 선택 동기화
        for equipment in self.viewmodel.equipment_types:
            if equipment.get('id') == equipment_type_id:
                self.equipment_var.set(equipment.get('name', ''))
                break
    
    def _update_qc_statistics_display(self):
        """QC 통계 표시 업데이트"""
        if not hasattr(self, 'qc_stats_labels'):
            return
        
        qc_results = self.viewmodel.qc_results
        
        # 전체 통계 계산
        total = len(qc_results)
        passed = sum(1 for result in qc_results if result.get('status') == 'PASS')
        warnings = sum(1 for result in qc_results if result.get('status') == 'WARNING')
        failures = sum(1 for result in qc_results if result.get('status') == 'FAIL')
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # 통계 라벨 업데이트
        self.qc_stats_labels['total_checks'].config(text=f"총 검수 항목: {total:,}")
        self.qc_stats_labels['passed'].config(text=f"통과: {passed:,}")
        self.qc_stats_labels['warnings'].config(text=f"경고: {warnings:,}")
        self.qc_stats_labels['failures'].config(text=f"실패: {failures:,}")
        self.qc_stats_labels['pass_rate'].config(text=f"통과율: {pass_rate:.1f}%")
        
        # 심각도별 통계 계산
        severity_counts = {}
        for result in qc_results:
            severity = result.get('severity', 'Low')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # 심각도 라벨 업데이트
        for severity, label in self.severity_labels.items():
            count = severity_counts.get(severity, 0)
            label.config(text=f"{severity}: {count:,}")
    
    def _update_status_display(self, status_text: str):
        """상태 표시 업데이트"""
        # 툴바의 상태 라벨 업데이트 (향후 구현)
        print(f"QC 상태: {status_text}")
    
    def _show_result_details(self, result: Dict):
        """결과 세부 정보 표시"""
        # 세부 정보 패널 업데이트
        for widget in self.details_panel.winfo_children():
            widget.destroy()
        
        # 상세 정보 표시
        details_frame = ttk.Frame(self.details_panel)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 기본 정보
        info_text = f"""파라미터: {result.get('parameter', 'N/A')}
예상 값: {result.get('expected', 'N/A')}
실제 값: {result.get('actual', 'N/A')}
상태: {result.get('status', 'N/A')}
편차: {result.get('deviation', 'N/A')}
허용 오차: {result.get('tolerance', 'N/A')}
심각도: {result.get('severity', 'N/A')}
"""
        
        info_label = ttk.Label(details_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W)
        
        # 추가 정보나 액션 버튼들 (필요시)
        if result.get('status') == 'FAIL':
            action_frame = ttk.Frame(details_frame)
            action_frame.pack(fill=tk.X, pady=(10, 0))
            
            ttk.Button(action_frame, text="📋 상세 분석", 
                      command=lambda: self._show_detailed_analysis_dialog(result)).pack(side=tk.LEFT, padx=5)
            ttk.Button(action_frame, text="📝 리포트 생성", 
                      command=lambda: self._generate_failure_report(result)).pack(side=tk.LEFT, padx=5)
    
    def _show_detailed_analysis_dialog(self, result: Dict):
        """상세 분석 다이얼로그 표시"""
        # 향후 구현
        self.show_info("상세 분석", f"'{result.get('parameter', 'Unknown')}' 항목의 상세 분석 기능은 향후 구현됩니다.")
    
    def _generate_failure_report(self, result: Dict):
        """실패 리포트 생성"""
        # 향후 구현
        self.show_info("리포트 생성", f"'{result.get('parameter', 'Unknown')}' 항목의 실패 리포트 생성 기능은 향후 구현됩니다.")
    
    def on_tab_activated(self):
        """탭 활성화 시 호출"""
        super().on_tab_activated()
        
        # 장비 유형 목록 로드
        self.viewmodel.execute_command('load_equipment_types')
    
    def get_tab_title(self) -> str:
        """탭 제목 반환"""
        if self.current_equipment_type:
            # 현재 선택된 장비 유형 이름 찾기
            for equipment in self.viewmodel.equipment_types:
                if equipment.get('id') == self.current_equipment_type:
                    return f"🔍 QC 검수 ({equipment.get('name', 'Unknown')})"
        
        return "🔍 QC 검수"