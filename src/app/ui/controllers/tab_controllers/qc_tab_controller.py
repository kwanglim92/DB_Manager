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
        try:
            super()._setup_bindings()
            
            # QC 결과 바인딩 (안전하게 처리)
            if hasattr(self.viewmodel, 'qc_results'):
                qc_results = self.viewmodel.qc_results
                if hasattr(qc_results, 'bind_changed'):
                    qc_results.bind_changed(self._update_qc_results_display)
            
            # 장비 유형 바인딩 (안전하게 처리)
            if hasattr(self.viewmodel, 'equipment_types'):
                equipment_types = self.viewmodel.equipment_types
                if hasattr(equipment_types, 'bind_changed'):
                    equipment_types.bind_changed(self._update_equipment_types)
            
            # 선택된 장비 유형 바인딩 (안전하게 처리)
            try:
                self.bind_property_to_view('selected_equipment_type_id', self._update_selected_equipment)
            except:
                pass  # 바인딩 실패 시 무시
                
        except Exception as e:
            # 바인딩 실패 시에도 계속 진행
            print(f"바인딩 설정 중 오류 (무시): {e}")
    
    def _setup_view_events(self):
        """View 이벤트 설정"""
        try:
            super()._setup_view_events()
        except:
            pass  # 상위 클래스 이벤트 설정 실패 시 무시
        
        # 키보드 단축키 (안전하게 처리)
        try:
            self.tab_frame.bind('<F5>', self._handle_run_qc_check)
            self.tab_frame.bind('<Control-s>', self._handle_save_results)
            self.tab_frame.bind('<Control-e>', self._handle_export_results)
        except Exception as e:
            print(f"키보드 단축키 설정 실패 (무시): {e}")
    
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

        # 검수 모드 선택 (숨김 처리 - 리팩토링 중)
        self.qc_mode_label = ttk.Label(row1, text="🔍 검수 모드:", font=('Arial', 9, 'bold'))
        self.qc_mode_label.pack(side=tk.LEFT, padx=(0, 5))
        self.qc_mode_label.pack_forget()  # 숨김 처리
        
        self.qc_mode_var = tk.StringVar(value="performance")
        
        self.performance_radio = ttk.Radiobutton(row1, text="⚡ Performance 중점", 
                                          variable=self.qc_mode_var, value="performance",
                                          command=self._on_mode_changed)
        self.performance_radio.pack(side=tk.LEFT, padx=(0, 10))
        self.performance_radio.pack_forget()  # 숨김 처리
        
        self.full_radio = ttk.Radiobutton(row1, text="📋 전체 검수", 
                                   variable=self.qc_mode_var, value="full",
                                   command=self._on_mode_changed)
        self.full_radio.pack(side=tk.LEFT, padx=(0, 10))
        self.full_radio.pack_forget()  # 숨김 처리

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

        # 신규 전체 항목 포함 체크박스 추가
        self.chk_include_all_var = tk.BooleanVar(value=False)
        self.chk_include_all = ttk.Checkbutton(options_frame, text="전체 항목 포함", 
                                              variable=self.chk_include_all_var)
        self.chk_include_all.pack(anchor='w')

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
        
        # 탭 2: 통계 및 요약 (숨김 처리 - 리팩토링 중)
        self.statistics_tab = self._create_statistics_tab()
        
        # 탭 3: 시각화 (숨김 처리 - 리팩토링 중)
        self.visualization_tab = self._create_visualization_tab()
        
        # 탭 4: 최종 보고서 (신규 추가)
        self._create_final_report_tab()

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
        """통계 및 요약 탭 생성 (숨김 처리 - 리팩토링 중)"""
        stats_tab = ttk.Frame(self.results_notebook)
        # self.results_notebook.add(stats_tab, text="📊 통계 요약")  # 숨김 처리

        # 통계 요약 영역
        self.stats_frame = ttk.Frame(stats_tab)
        self.stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        return stats_tab  # 탭 참조 반환 (나중에 삭제 용도)

    def _create_visualization_tab(self):
        """시각화 탭 생성 (숨김 처리 - 리팩토링 중)"""
        chart_tab = ttk.Frame(self.results_notebook)
        # self.results_notebook.add(chart_tab, text="📈 시각화")  # 숨김 처리

        self.chart_frame = ttk.Frame(chart_tab)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        return chart_tab  # 탭 참조 반환 (나중에 삭제 용도)

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
        # [신규 추가] 전체 항목 포함 체크박스 상태 확인
        include_all = getattr(self, 'chk_include_all_var', tk.BooleanVar()).get()
        
        # Enhanced QC 기능 실행
        # 실제 구현은 viewmodel을 통해 수행
        self.viewmodel.execute_command('run_enhanced_qc_check', {
            'equipment_type_id': self.current_equipment_type,
            'mode': self.qc_mode,
            'options': {key: var.get() for key, var in self.qc_option_vars.items()},
            'include_all_items': include_all,  # 전체 항목 포함 여부 추가
            'callback': self._qc_check_complete
        })

    def _run_basic_qc(self):
        """기본 QC 검수 실행"""
        # [신규 추가] 전체 항목 포함 체크박스 상태 확인
        include_all = getattr(self, 'chk_include_all_var', tk.BooleanVar()).get()
        
        # 기본 QC 기능 실행
        self.viewmodel.execute_command('run_basic_qc_check', {
            'equipment_type_id': self.current_equipment_type,
            'include_all_items': include_all,  # 전체 항목 포함 여부 추가
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
            
            # [신규 추가] 최종 보고서 탭 업데이트 및 탭 전환
            self._update_final_report_tab(self.qc_results)
            if hasattr(self, 'tab_report'):
                self.results_notebook.select(self.tab_report)  # 최종 보고서 탭으로 전환
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

    def _create_final_report_tab(self):
        """최종 보고서 탭 생성 (신규)"""
        # 최종 보고서 탭 프레임
        self.tab_report = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.tab_report, text="📊 최종 보고서")
        
        # 메인 그리드 레이아웃 설정
        main_layout = tk.Frame(self.tab_report)
        main_layout.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 그리드 레이아웃 사용
        main_layout.grid_rowconfigure(3, weight=1)  # 실패 항목 테이블이 확장되도록
        main_layout.grid_columnconfigure(0, weight=1)
        
        # (1행) 최종 판정 레이블
        self.lbl_overall_result = tk.Label(main_layout, text="검수 대기 중", 
                                          font=('Arial', 20, 'bold'),
                                          fg='blue', bg='white',
                                          relief='solid', borderwidth=2,
                                          pady=15)
        self.lbl_overall_result.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        # (2행) 검수 정보 그룹박스
        info_group = ttk.LabelFrame(main_layout, text="🔍 검수 정보", padding=10)
        info_group.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        
        # 검수 정보 레이블들
        info_frame = ttk.Frame(info_group)
        info_frame.pack(fill=tk.X)
        
        self.lbl_equipment_type = ttk.Label(info_frame, text="장비 유형: -")
        self.lbl_equipment_type.grid(row=0, column=0, sticky='w', padx=(0, 20))
        
        self.lbl_check_date = ttk.Label(info_frame, text="검수 일시: -")
        self.lbl_check_date.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        self.lbl_total_items = ttk.Label(info_frame, text="총 항목 수: -")
        self.lbl_total_items.grid(row=1, column=0, sticky='w', padx=(0, 20))
        
        self.lbl_check_mode = ttk.Label(info_frame, text="검수 모드: -")
        self.lbl_check_mode.grid(row=1, column=1, sticky='w', padx=(0, 20))
        
        # (3행) 핵심 요약 그룹박스
        summary_group = ttk.LabelFrame(main_layout, text="📈 핵심 요약", padding=10)
        summary_group.grid(row=2, column=0, sticky='ew', pady=(0, 10))
        
        # 요약 통계 프레임
        summary_frame = ttk.Frame(summary_group)
        summary_frame.pack(fill=tk.X)
        
        self.lbl_pass_count = ttk.Label(summary_frame, text="통과: 0개", 
                                       font=('Arial', 10, 'bold'), foreground='green')
        self.lbl_pass_count.grid(row=0, column=0, sticky='w', padx=(0, 30))
        
        self.lbl_fail_count = ttk.Label(summary_frame, text="실패: 0개", 
                                       font=('Arial', 10, 'bold'), foreground='red')
        self.lbl_fail_count.grid(row=0, column=1, sticky='w', padx=(0, 30))
        
        self.lbl_critical_count = ttk.Label(summary_frame, text="심각: 0개", 
                                          font=('Arial', 10, 'bold'), foreground='darkred')
        self.lbl_critical_count.grid(row=0, column=2, sticky='w')
        
        self.lbl_pass_rate = ttk.Label(summary_frame, text="통과율: 0%", 
                                      font=('Arial', 12, 'bold'))
        self.lbl_pass_rate.grid(row=1, column=0, columnspan=3, sticky='w', pady=(5, 0))
        
        # (4행) 실패 항목 상세 테이블
        failures_group = ttk.LabelFrame(main_layout, text="❌ 실패 항목 상세", padding=10)
        failures_group.grid(row=3, column=0, sticky='nsew', pady=(0, 10))
        
        # 실패 항목 테이블 생성
        table_frame = ttk.Frame(failures_group)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 테이블 컬럼 정의
        columns = ("parameter", "default_value", "file_value", "pass_fail", "issue_type", "description")
        
        self.tbl_failures = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)
        
        # 컬럼 헤더 설정
        self.tbl_failures.heading("parameter", text="파라미터명")
        self.tbl_failures.heading("default_value", text="Default Value")
        self.tbl_failures.heading("file_value", text="File Value")
        self.tbl_failures.heading("pass_fail", text="Pass/Fail")
        self.tbl_failures.heading("issue_type", text="Issue Type")
        self.tbl_failures.heading("description", text="설명")
        
        # 컬럼 너비 설정
        self.tbl_failures.column("parameter", width=150)
        self.tbl_failures.column("default_value", width=120)
        self.tbl_failures.column("file_value", width=120)
        self.tbl_failures.column("pass_fail", width=80)
        self.tbl_failures.column("issue_type", width=120)
        self.tbl_failures.column("description", width=200)
        
        # 편집 불가 설정 (이미 기본값)
        
        # 스크롤바 추가
        scrollbar_v = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tbl_failures.yview)
        scrollbar_h = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tbl_failures.xview)
        self.tbl_failures.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # 테이블과 스크롤바 배치
        self.tbl_failures.grid(row=0, column=0, sticky='nsew')
        scrollbar_v.grid(row=0, column=1, sticky='ns')
        scrollbar_h.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # (5행) 액션 버튼들
        button_frame = ttk.Frame(main_layout)
        button_frame.grid(row=4, column=0, sticky='ew', pady=(10, 0))
        
        # 버튼 우측 정렬
        ttk.Button(button_frame, text="🖨️ 인쇄", 
                  command=self._on_print_report).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(button_frame, text="📄 PDF 저장", 
                  command=self._on_save_pdf).pack(side=tk.RIGHT, padx=(5, 0))

    def _update_final_report_tab(self, results: list):
        """최종 보고서 탭 업데이트"""
        if not hasattr(self, 'tab_report') or not results:
            return
            
        from datetime import datetime
        
        # 1. 통계 계산
        total_items = len(results)
        fail_items = [r for r in results if r.get('pass_fail', '').upper() == 'FAIL']
        pass_items = [r for r in results if r.get('pass_fail', '').upper() == 'PASS']
        critical_items = [r for r in results if r.get('severity', '') == '높음']
        
        pass_count = len(pass_items)
        fail_count = len(fail_items)
        critical_count = len(critical_items)
        pass_rate = (pass_count / total_items * 100) if total_items > 0 else 0
        
        # 2. 최종 판정 설정
        overall_result = "PASS" if fail_count == 0 else "FAIL"
        result_color = 'green' if overall_result == "PASS" else 'red'
        result_bg = '#e8f5e8' if overall_result == "PASS" else '#ffe8e8'
        
        self.lbl_overall_result.config(
            text=f"최종 판정: {overall_result}",
            fg=result_color,
            bg=result_bg
        )
        
        # 3. 검수 정보 업데이트
        equipment_type = self.equipment_type_var.get() or "미선택"
        check_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        include_all = "전체 포함" if getattr(self, 'chk_include_all_var', tk.BooleanVar()).get() else "일반"
        
        self.lbl_equipment_type.config(text=f"장비 유형: {equipment_type}")
        self.lbl_check_date.config(text=f"검수 일시: {check_date}")
        self.lbl_total_items.config(text=f"총 항목 수: {total_items}개")
        self.lbl_check_mode.config(text=f"검수 모드: {include_all}")
        
        # 4. 핵심 요약 업데이트
        self.lbl_pass_count.config(text=f"통과: {pass_count}개")
        self.lbl_fail_count.config(text=f"실패: {fail_count}개")
        self.lbl_critical_count.config(text=f"심각: {critical_count}개")
        self.lbl_pass_rate.config(text=f"통과율: {pass_rate:.1f}%")
        
        # 5. 실패 항목 테이블 업데이트
        # 기존 항목 삭제
        for item in self.tbl_failures.get_children():
            self.tbl_failures.delete(item)
            
        # 실패 항목만 추가
        for result in fail_items:
            values = (
                result.get('parameter', ''),
                result.get('default_value', ''),
                result.get('file_value', ''),
                result.get('pass_fail', ''),
                result.get('issue_type', ''),
                result.get('description', '')
            )
            
            # 심각도에 따른 태그 설정
            severity = result.get('severity', '낮음')
            tag = f"severity_{severity}"
            
            self.tbl_failures.insert("", "end", values=values, tags=(tag,))
        
        # 테이블 태그 색상 설정
        self.tbl_failures.tag_configure("severity_높음", background="#ffebee", foreground="#c62828")
        self.tbl_failures.tag_configure("severity_중간", background="#fff3e0", foreground="#ef6c00")
        self.tbl_failures.tag_configure("severity_낮음", background="#f3e5f5", foreground="#7b1fa2")

    def _on_print_report(self):
        """보고서 인쇄"""
        try:
            # 간단한 텍스트 형태로 보고서 생성
            report_content = self._generate_text_report()
            
            # 임시 파일로 저장하고 기본 인쇄 프로그램으로 열기
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(report_content)
                temp_file_path = temp_file.name
            
            # 기본 텍스트 에디터로 열기 (사용자가 인쇄 가능)
            if os.name == 'nt':  # Windows
                os.startfile(temp_file_path)
            elif os.name == 'posix':  # macOS, Linux
                os.system(f'open "{temp_file_path}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{temp_file_path}"')
                
        except Exception as e:
            messagebox.showerror("오류", f"인쇄 준비 중 오류가 발생했습니다: {str(e)}")

    def _on_save_pdf(self):
        """PDF로 보고서 저장"""
        try:
            from tkinter import filedialog
            
            # 저장할 파일 경로 선택
            file_path = filedialog.asksaveasfilename(
                title="QC 검수 보고서 저장",
                defaultextension=".txt",
                filetypes=[
                    ("텍스트 파일", "*.txt"),
                    ("CSV 파일", "*.csv"),
                    ("모든 파일", "*.*")
                ]
            )
            
            if file_path:
                if file_path.endswith('.csv'):
                    self._save_as_csv(file_path)
                else:
                    self._save_as_text(file_path)
                    
                messagebox.showinfo("저장 완료", f"보고서가 저장되었습니다:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("오류", f"보고서 저장 중 오류가 발생했습니다: {str(e)}")

    def _generate_text_report(self):
        """텍스트 형태 보고서 생성"""
        from datetime import datetime
        
        # 보고서 헤더
        report = []
        report.append("=" * 60)
        report.append("QC 검수 최종 보고서")
        report.append("=" * 60)
        report.append("")
        
        # 검수 정보
        equipment_type = self.equipment_type_var.get() or "미선택"
        check_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        include_all = "전체 포함" if getattr(self, 'chk_include_all_var', tk.BooleanVar()).get() else "일반"
        
        report.append("📋 검수 정보")
        report.append("-" * 30)
        report.append(f"장비 유형: {equipment_type}")
        report.append(f"검수 일시: {check_date}")
        report.append(f"총 항목 수: {len(self.qc_results)}개")
        report.append(f"검수 모드: {include_all}")
        report.append("")
        
        # 요약 통계
        fail_items = [r for r in self.qc_results if r.get('pass_fail', '').upper() == 'FAIL']
        pass_items = [r for r in self.qc_results if r.get('pass_fail', '').upper() == 'PASS']
        critical_items = [r for r in self.qc_results if r.get('severity', '') == '높음']
        
        pass_count = len(pass_items)
        fail_count = len(fail_items)
        critical_count = len(critical_items)
        pass_rate = (pass_count / len(self.qc_results) * 100) if self.qc_results else 0
        overall_result = "PASS" if fail_count == 0 else "FAIL"
        
        report.append("📈 핵심 요약")
        report.append("-" * 30)
        report.append(f"최종 판정: {overall_result}")
        report.append(f"통과: {pass_count}개")
        report.append(f"실패: {fail_count}개")
        report.append(f"심각: {critical_count}개")
        report.append(f"통과율: {pass_rate:.1f}%")
        report.append("")
        
        # 실패 항목 상세
        if fail_items:
            report.append("❌ 실패 항목 상세")
            report.append("-" * 50)
            for i, item in enumerate(fail_items, 1):
                report.append(f"{i}. {item.get('parameter', 'N/A')}")
                report.append(f"   Default Value: {item.get('default_value', 'N/A')}")
                report.append(f"   File Value: {item.get('file_value', 'N/A')}")
                report.append(f"   Pass/Fail: {item.get('pass_fail', 'N/A')}")
                report.append(f"   Issue Type: {item.get('issue_type', 'N/A')}")
                report.append(f"   설명: {item.get('description', 'N/A')}")
                report.append("")
        else:
            report.append("✅ 모든 항목이 통과했습니다.")
            report.append("")
        
        report.append("=" * 60)
        report.append("보고서 생성 완료")
        report.append("=" * 60)
        
        return "\n".join(report)

    def _save_as_text(self, file_path):
        """텍스트 파일로 저장"""
        report_content = self._generate_text_report()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

    def _save_as_csv(self, file_path):
        """CSV 파일로 저장"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            # 헤더
            writer.writerow(['파라미터명', 'Default Value', 'File Value', 'Pass/Fail', 'Issue Type', '설명', '심각도'])
            
            # 데이터
            for result in self.qc_results:
                writer.writerow([
                    result.get('parameter', ''),
                    result.get('default_value', ''),
                    result.get('file_value', ''),
                    result.get('pass_fail', ''),
                    result.get('issue_type', ''),
                    result.get('description', ''),
                    result.get('severity', '')
                ])

    def _handle_save_results(self, event=None):
        """QC 결과 저장 (단축키용)"""
        self._on_save_pdf()

    def _handle_export_results(self, event=None):
        """QC 결과 내보내기 (단축키용)"""
        if hasattr(self, 'export_btn') and self.export_btn['state'] != 'disabled':
            self._on_save_pdf()
        else:
            messagebox.showinfo("알림", "먼저 QC 검수를 실행해주세요.")

    def _handle_select_files(self):
        """파일 선택 핸들러"""
        try:
            from app.qc_utils import QCFileSelector
            
            # 업로드된 파일 목록 확인
            uploaded_files = getattr(self.viewmodel, 'uploaded_files', {})
            
            if not uploaded_files:
                messagebox.showinfo("파일 없음", "먼저 파일을 업로드해주세요.")
                return
            
            # 파일 선택 다이얼로그
            selected = QCFileSelector.create_file_selection_dialog(
                self.tab_frame, uploaded_files, max_files=6
            )
            
            if selected:
                self.selected_qc_files = selected
                self._update_status(f"📁 {len(selected)}개 파일이 선택되었습니다.")
                
        except Exception as e:
            messagebox.showerror("오류", f"파일 선택 중 오류: {str(e)}")

    def _refresh_equipment_types(self):
        """장비 유형 목록 새로고침"""
        try:
            if hasattr(self.viewmodel, 'db_schema') and self.viewmodel.db_schema:
                equipment_types = self.viewmodel.db_schema.get_equipment_types()
                
                # 콤보박스 업데이트
                if hasattr(self, 'equipment_type_combo'):
                    type_names = [f"{et[1]} (ID: {et[0]})" for et in equipment_types]
                    self.equipment_type_combo['values'] = type_names
                    
                    if type_names:
                        self.equipment_type_combo.set(type_names[0])
                        
                self._update_status(f"📋 장비 유형 {len(equipment_types)}개 로드됨")
            else:
                self._update_status("❌ 데이터베이스 연결 실패")
                
        except Exception as e:
            self._update_status(f"❌ 장비 유형 로드 실패: {str(e)}")

    def _on_equipment_type_changed(self, event=None):
        """장비 유형 변경 이벤트"""
        try:
            selected_text = self.equipment_type_var.get()
            if selected_text and "ID: " in selected_text:
                # "Type Name (ID: 123)" 형식에서 ID 추출
                type_id = selected_text.split("ID: ")[1].split(")")[0]
                self.current_equipment_type = int(type_id)
                self._update_status(f"🔧 장비 유형 선택: {selected_text}")
        except Exception as e:
            print(f"장비 유형 변경 처리 중 오류: {e}")

    def _on_mode_changed(self):
        """검수 모드 변경 핸들러"""
        mode = self.qc_mode_var.get()
        self.qc_mode = mode
        self._update_status(f"🔍 검수 모드: {mode}")

    def _load_initial_data(self):
        """초기 데이터 로드"""
        self._refresh_equipment_types()

    def _update_equipment_types(self, equipment_types):
        """장비 유형 업데이트 (바인딩용)"""
        try:
            if hasattr(self, 'equipment_type_combo'):
                type_names = [f"{et[1]} (ID: {et[0]})" for et in equipment_types]
                self.equipment_type_combo['values'] = type_names
        except Exception as e:
            print(f"장비 유형 업데이트 실패: {e}")

    def _update_selected_equipment(self, equipment_id):
        """선택된 장비 업데이트 (바인딩용)"""
        self.current_equipment_type = equipment_id

    def _update_qc_results_display(self, results):
        """QC 결과 표시 업데이트 (바인딩용)"""
        self.qc_results = results
        self._display_qc_results()