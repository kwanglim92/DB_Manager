"""
QC 검수 탭 컨트롤러
QC 기능을 위한 전용 탭 컨트롤러
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

from ..base_controller import TabController
from ...components.treeview_component import TreeViewComponent
from ...components.toolbar_component import ToolbarComponent
from ...components.filter_component import FilterComponent
from app.utils import create_treeview_with_scrollbar


class QCTabController(TabController):
    """QC 검수 탭 컨트롤러 - 향상된 기능 지원"""
    
    def __init__(self, tab_frame: tk.Frame, viewmodel, tab_name: str = "QC 검수", main_window=None):
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
        self.qc_results = []
        self.qc_mode = "performance"  # performance, full
        self.selected_qc_options = {
            'check_performance': True,
            'check_naming': True,
            'check_ranges': True,
            'check_trends': False
        }
        
        # Enhanced QC 기능 사용 가능 여부 확인
        self.enhanced_qc_available = self._check_enhanced_qc_availability()
        
        # UI 생성
        self._create_tab_ui()
    
    def _check_enhanced_qc_availability(self) -> bool:
        """Enhanced QC 기능 사용 가능 여부 확인"""
        try:
            from app.enhanced_qc import EnhancedQCValidator
            return True
        except ImportError:
            return False
    
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
        if self.enhanced_qc_available:
            self._create_enhanced_qc_ui()
        else:
            self._create_basic_qc_ui()
    
    def _create_enhanced_qc_ui(self):
        """향상된 QC UI 생성"""
        # 🎨 상단 컨트롤 패널
        control_panel = ttk.LabelFrame(self.tab_frame, text="🎛️ QC 검수 설정", padding=15)
        control_panel.pack(fill=tk.X, padx=10, pady=10)

        # 첫 번째 행: 장비 유형 및 모드 선택
        row1 = ttk.Frame(control_panel)
        row1.pack(fill=tk.X, pady=(0, 10))

        # 장비 유형 선택
        ttk.Label(row1, text="🏭 장비 유형:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.equipment_type_var = tk.StringVar()
        self.equipment_type_combo = ttk.Combobox(row1, textvariable=self.equipment_type_var, 
                                               state="readonly", width=25)
        self.equipment_type_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.equipment_type_combo.bind('<<ComboboxSelected>>', self._on_equipment_type_changed)
        
        # 새로고침 버튼
        refresh_btn = ttk.Button(row1, text="🔄 새로고침", command=self._refresh_equipment_types)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 15))

        # 검수 모드 선택
        ttk.Label(row1, text="🔍 검수 모드:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.qc_mode_var = tk.StringVar(value="performance")
        
        performance_radio = ttk.Radiobutton(row1, text="⚡ Performance 중점", 
                                          variable=self.qc_mode_var, value="performance",
                                          command=self._on_mode_changed)
        performance_radio.pack(side=tk.LEFT, padx=(0, 10))
        
        full_radio = ttk.Radiobutton(row1, text="📋 전체 검수", 
                                   variable=self.qc_mode_var, value="full",
                                   command=self._on_mode_changed)
        full_radio.pack(side=tk.LEFT, padx=(0, 10))

        # 두 번째 행: 검수 옵션 및 실행 버튼
        row2 = ttk.Frame(control_panel)
        row2.pack(fill=tk.X, pady=(5, 0))

        # 검수 옵션
        options_frame = ttk.LabelFrame(row2, text="🔧 검수 옵션", padding=10)
        options_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        self.qc_option_vars = {
            'check_performance': tk.BooleanVar(value=True),
            'check_naming': tk.BooleanVar(value=True),
            'check_ranges': tk.BooleanVar(value=True),
            'check_trends': tk.BooleanVar(value=False)
        }

        ttk.Checkbutton(options_frame, text="Performance 중점 검사", 
                       variable=self.qc_option_vars['check_performance']).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="명명 규칙 검사", 
                       variable=self.qc_option_vars['check_naming']).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="값 범위 분석", 
                       variable=self.qc_option_vars['check_ranges']).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="데이터 트렌드 분석", 
                       variable=self.qc_option_vars['check_trends']).pack(anchor='w')

        # 실행 버튼 영역
        action_frame = ttk.Frame(row2)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # 메인 QC 실행 버튼
        self.qc_run_btn = ttk.Button(action_frame, text="🚀 QC 검수 실행", 
                                   command=self._handle_run_qc_check)
        self.qc_run_btn.pack(pady=(0, 5))

        # 파일 선택 버튼
        self.file_select_btn = ttk.Button(action_frame, text="📁 검수 파일 선택", 
                                        command=self._handle_select_files)
        self.file_select_btn.pack(pady=(0, 5))

        # 결과 내보내기 버튼
        self.export_btn = ttk.Button(action_frame, text="📤 결과 내보내기", 
                                   command=self._handle_export_results,
                                   state="disabled")
        self.export_btn.pack()

        # 🎨 메인 결과 영역 - 탭 구조
        main_frame = ttk.Frame(self.tab_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 결과 탭 노트북
        self.results_notebook = ttk.Notebook(main_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)

        # 탭 1: 검수 결과 목록
        self._create_results_tab()
        
        # 탭 2: 통계 및 요약
        self._create_statistics_tab()
        
        # 탭 3: 시각화
        self._create_visualization_tab()

        # 🎨 하단 상태 표시줄
        self._create_status_bar()
        
        # 초기 데이터 로드
        self._load_initial_data()

    def _create_basic_qc_ui(self):
        """기본 QC UI 생성 (Enhanced QC가 없는 경우)"""
        # 기본 QC UI 구현
        control_frame = ttk.LabelFrame(self.tab_frame, text="QC 검수 설정", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 장비 유형 선택
        ttk.Label(control_frame, text="장비 유형:").pack(side=tk.LEFT, padx=(0, 5))
        self.equipment_type_var = tk.StringVar()
        self.equipment_type_combo = ttk.Combobox(control_frame, textvariable=self.equipment_type_var, 
                                               state="readonly", width=25)
        self.equipment_type_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        # QC 실행 버튼
        self.qc_run_btn = ttk.Button(control_frame, text="QC 검수 실행", 
                                   command=self._handle_run_basic_qc)
        self.qc_run_btn.pack(side=tk.LEFT)
        
        # 결과 영역
        results_frame = ttk.LabelFrame(self.tab_frame, text="검수 결과", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 기본 결과 트리뷰
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

        result_frame, self.result_tree = create_treeview_with_scrollbar(
            results_frame, columns, headings, column_widths, height=15)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self._load_initial_data()

    def _create_results_tab(self):
        """검수 결과 탭 생성"""
        results_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(results_tab, text="📋 검수 결과")

        # 검수 결과 트리뷰 (향상된 컬럼 구조)
        columns = ("parameter", "issue_type", "description", "severity", "category", "recommendation")
        headings = {
            "parameter": "파라미터", 
            "issue_type": "문제 유형", 
            "description": "상세 설명", 
            "severity": "심각도",
            "category": "카테고리",
            "recommendation": "권장사항"
        }
        column_widths = {
            "parameter": 150, 
            "issue_type": 120, 
            "description": 250, 
            "severity": 80,
            "category": 100,
            "recommendation": 200
        }

        results_frame, self.result_tree = create_treeview_with_scrollbar(
            results_tab, columns, headings, column_widths, height=12)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 트리뷰 이벤트 바인딩
        self.result_tree.bind('<<TreeviewSelect>>', self._on_result_selected)
        self.result_tree.bind('<Double-1>', self._on_result_double_click)

    def _create_statistics_tab(self):
        """통계 및 요약 탭 생성"""
        stats_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(stats_tab, text="📊 통계 요약")

        # 통계 요약 영역
        self.stats_frame = ttk.Frame(stats_tab)
        self.stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_visualization_tab(self):
        """시각화 탭 생성"""
        chart_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(chart_tab, text="📈 시각화")

        self.chart_frame = ttk.Frame(chart_tab)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_status_bar(self):
        """상태 표시줄 생성"""
        status_frame = ttk.Frame(self.tab_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_label = ttk.Label(status_frame, text="📋 QC 검수 대기 중...", 
                                    font=('Arial', 9), foreground='blue')
        self.status_label.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))

    def _load_initial_data(self):
        """초기 데이터 로드"""
        try:
            # 장비 유형 목록 로드
            self._refresh_equipment_types()
        except Exception as e:
            self.show_error("초기화 오류", f"QC 탭 초기화 중 오류가 발생했습니다: {str(e)}")

    def _refresh_equipment_types(self):
        """장비 유형 목록 새로고침"""
        try:
            equipment_types = self.viewmodel.get_equipment_types()
            equipment_names = [eq_type[1] for eq_type in equipment_types]
            
            self.equipment_type_combo['values'] = equipment_names
            if equipment_names:
                self.equipment_type_combo.set(equipment_names[0])
                self.current_equipment_type = equipment_types[0][0]  # ID 저장
            
            self._update_status(f"✅ {len(equipment_names)}개 장비 유형 로드됨")
            
        except Exception as e:
            self.show_error("오류", f"장비 유형 로드 중 오류: {str(e)}")
            self._update_status("❌ 장비 유형 로드 실패")

    def _on_equipment_type_changed(self, event=None):
        """장비 유형 변경 이벤트"""
        selected_name = self.equipment_type_var.get()
        if selected_name:
            # 선택된 장비 유형의 ID 찾기
            equipment_types = self.viewmodel.get_equipment_types()
            for eq_type in equipment_types:
                if eq_type[1] == selected_name:
                    self.current_equipment_type = eq_type[0]
                    break
            
            self._update_status(f"📋 장비 유형 선택: {selected_name}")

    def _on_mode_changed(self):
        """검수 모드 변경 이벤트"""
        self.qc_mode = self.qc_mode_var.get()
        mode_text = "Performance 중점" if self.qc_mode == "performance" else "전체 검수"
        self._update_status(f"🔍 검수 모드: {mode_text}")

    def _on_result_selected(self, event=None):
        """검수 결과 선택 이벤트"""
        selection = self.result_tree.selection()
        if selection:
            item = self.result_tree.item(selection[0])
            values = item['values']
            if values:
                # 선택된 항목의 상세 정보 표시 (향후 구현)
                pass

    def _on_result_double_click(self, event=None):
        """검수 결과 더블클릭 이벤트"""
        selection = self.result_tree.selection()
        if selection:
            item = self.result_tree.item(selection[0])
            values = item['values']
            if values:
                # 상세 분석 다이얼로그 표시 (향후 구현)
                self.show_info("상세 정보", f"파라미터: {values[0]}\n문제: {values[1]}\n설명: {values[2]}")

    def _handle_run_qc_check(self, event=None):
        """QC 검수 실행 처리"""
        if not self.current_equipment_type:
            self.show_warning("알림", "장비 유형을 먼저 선택해주세요.")
            return

        try:
            self.qc_status = "running"
            self._update_status("🔄 QC 검수 실행 중...")
            self.qc_run_btn.config(state="disabled")
            self.progress_bar.config(value=10)

            # Enhanced QC 또는 기본 QC 실행
            if self.enhanced_qc_available:
                self._run_enhanced_qc()
            else:
                self._run_basic_qc()

        except Exception as e:
            self.qc_status = "error"
            self._update_status("❌ QC 검수 실패")
            self.show_error("오류", f"QC 검수 중 오류가 발생했습니다: {str(e)}")
        finally:
            self.qc_run_btn.config(state="normal")

    def _run_enhanced_qc(self):
        """향상된 QC 검수 실행"""
        # Enhanced QC 기능 실행
        # 실제 구현은 viewmodel을 통해 수행
        self.viewmodel.execute_command('run_enhanced_qc_check', {
            'equipment_type_id': self.current_equipment_type,
            'mode': self.qc_mode,
            'options': {key: var.get() for key, var in self.qc_option_vars.items()},
            'callback': self._qc_check_complete
        })

    def _run_basic_qc(self):
        """기본 QC 검수 실행"""
        # 기본 QC 기능 실행
        self.viewmodel.execute_command('run_basic_qc_check', {
            'equipment_type_id': self.current_equipment_type,
            'callback': self._qc_check_complete
        })

    def _handle_run_basic_qc(self):
        """기본 QC 검수 실행 (기본 UI용)"""
        if not self.current_equipment_type:
            self.show_warning("알림", "장비 유형을 먼저 선택해주세요.")
            return
        
        self._run_basic_qc()

    def _qc_check_complete(self, success: bool, results: Dict):
        """QC 검수 완료 콜백"""
        if success:
            self.qc_status = "complete"
            self.qc_results = results.get('issues', [])
            self._display_qc_results()
            self._update_status(f"✅ QC 검수 완료 - {len(self.qc_results)}개 이슈 발견")
            self.export_btn.config(state="normal")
        else:
            self.qc_status = "error"
            self._update_status("❌ QC 검수 실패")
            self.show_error("오류", f"QC 검수 중 오류가 발생했습니다: {results.get('error', '알 수 없는 오류')}")
        
        self.progress_bar.config(value=100 if success else 0)

    def _display_qc_results(self):
        """QC 검수 결과 표시"""
        # 기존 결과 삭제
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # 새 결과 추가
        for result in self.qc_results:
            severity = result.get("severity", "낮음")
            tag = f"severity_{severity}"
            
            if self.enhanced_qc_available:
                values = (
                    result.get("parameter", ""),
                    result.get("issue_type", ""),
                    result.get("description", ""),
                    severity,
                    result.get("category", ""),
                    result.get("recommendation", "")
                )
            else:
                values = (
                    result.get("parameter", ""),
                    result.get("issue_type", ""),
                    result.get("description", ""),
                    severity
                )
            
            self.result_tree.insert("", "end", values=values, tags=(tag,))

        # 트리뷰 태그 색상 설정
        self.result_tree.tag_configure("severity_높음", background="#ffebee", foreground="#c62828")
        self.result_tree.tag_configure("severity_중간", background="#fff3e0", foreground="#ef6c00")
        self.result_tree.tag_configure("severity_낮음", background="#f3e5f5", foreground="#7b1fa2")

        # 통계 업데이트
        if hasattr(self, 'stats_frame'):
            self._update_statistics()

    def _update_statistics(self):
        """통계 정보 업데이트"""
        # 기존 통계 위젯 삭제
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        if not self.qc_results:
            ttk.Label(self.stats_frame, text="검수 결과가 없습니다.", 
                     font=('Arial', 12)).pack(pady=20)
            return

        # 통계 정보 생성 및 표시
        severity_counts = {"높음": 0, "중간": 0, "낮음": 0}
        for result in self.qc_results:
            severity = result.get("severity", "낮음")
            severity_counts[severity] += 1

        # 통계 표시
        stats_label = ttk.Label(self.stats_frame, text="QC 검수 결과 통계", 
                               font=('Arial', 14, 'bold'))
        stats_label.pack(pady=(10, 20))

        for severity, count in severity_counts.items():
            if count > 0:
                color = "#c62828" if severity == "높음" else "#ef6c00" if severity == "중간" else "#7b1fa2"
                label = ttk.Label(self.stats_frame, text=f"• {severity}: {count}개", 
                                 font=('Arial', 11), foreground=color)
                label.pack(anchor='w', padx=20, pady=2)

    def _handle_select_files(self):
        """검수 파일 선택 처리"""
        # 파일 선택 다이얼로그 (향후 구현)
        self.show_info("파일 선택", "검수 파일 선택 기능은 향후 구현 예정입니다.")

    def _handle_export_results(self):
        """결과 내보내기 처리"""
        if not self.qc_results:
            self.show_warning("알림", "내보낼 QC 검수 결과가 없습니다.")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                title="QC 검수 결과 저장",
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel 파일", "*.xlsx"),
                    ("CSV 파일", "*.csv"),
                    ("모든 파일", "*.*")
                ]
            )
            
            if file_path:
                # 결과 내보내기 실행
                df = pd.DataFrame(self.qc_results)
                
                if file_path.endswith('.xlsx'):
                    df.to_excel(file_path, index=False)
                else:
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                
                self.show_info("성공", f"QC 검수 결과가 저장되었습니다.\n{file_path}")
                
        except Exception as e:
            self.show_error("오류", f"결과 내보내기 중 오류: {str(e)}")

    def _update_status(self, message: str):
        """상태 메시지 업데이트"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
        
        # 로그에도 기록
        if hasattr(self.viewmodel, 'add_log_message'):
            self.viewmodel.add_log_message(f"[QC] {message}")

    def refresh_data(self):
        """데이터 새로고침"""
        self._refresh_equipment_types()

    def get_tab_info(self) -> Dict:
        """탭 정보 반환"""
        return {
            "name": "QC 검수",
            "icon": "🔍",
            "description": "품질 검수 및 분석",
            "enhanced": self.enhanced_qc_available
        }