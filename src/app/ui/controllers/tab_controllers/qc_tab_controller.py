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
        """엔지니어 스타일 QC UI 생성 - Default DB 관리 스타일 적용"""
        # 상단 제어 패널 - 배경색과 패딩 개선
        control_frame = ttk.Frame(self.tab_frame, style="Control.TFrame")
        control_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # 장비 유형 관리 섹션
        equipment_frame = ttk.LabelFrame(control_frame, text="Equipment Type Selection", padding=12)
        equipment_frame.pack(fill=tk.X, pady=(0, 8))
        
        # 장비 유형 선택
        type_select_frame = ttk.Frame(equipment_frame)
        type_select_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(type_select_frame, text="Equipment Type:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))
        self.equipment_type_var = tk.StringVar()
        self.equipment_type_combo = ttk.Combobox(type_select_frame, textvariable=self.equipment_type_var, 
                                               state="readonly", width=40, font=("Segoe UI", 9))
        self.equipment_type_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.equipment_type_combo.bind('<<ComboboxSelected>>', self._on_equipment_type_changed)
        
        # 새로고침 버튼
        refresh_btn = ttk.Button(type_select_frame, text="Refresh", 
                               command=self._refresh_equipment_types, width=10)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 15))

        # QC 실행 관리 섹션
        qc_frame = ttk.LabelFrame(control_frame, text="QC Execution Control", padding=12)
        qc_frame.pack(fill=tk.X, pady=(0, 8))
        
        # QC 실행 버튼들
        qc_buttons_frame = ttk.Frame(qc_frame)
        qc_buttons_frame.pack(fill=tk.X)

        # 전체 항목 포함 체크박스
        self.chk_include_all_var = tk.BooleanVar(value=False)
        self.chk_include_all = ttk.Checkbutton(qc_buttons_frame, text="Include All Items", 
                                              variable=self.chk_include_all_var)
        self.chk_include_all.pack(side=tk.LEFT, padx=(0, 15))

        # QC 실행 버튼 (메인 기능)
        self.qc_run_btn = ttk.Button(qc_buttons_frame, text="Execute QC Inspection", 
                                   command=self._handle_run_qc_check, width=18)
        self.qc_run_btn.pack(side=tk.LEFT, padx=(0, 12))

        # 결과 내보내기 버튼
        self.export_btn = ttk.Button(qc_buttons_frame, text="Export Results", 
                                   command=self._handle_export_results,
                                   state="disabled", width=13)
        self.export_btn.pack(side=tk.LEFT)

        # QC 결과 영역
        results_container = ttk.LabelFrame(self.tab_frame, text="QC Inspection Results", padding=10)
        results_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 8))

        # 결과 탭 노트북
        self.results_notebook = ttk.Notebook(results_container)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)

        # 탭 1: 검수 결과 목록 (기본)
        self._create_results_tab()
        
        # 탭 2: 최종 보고서 (메인 기능)
        self._create_final_report_tab()

        # 상태 정보 섹션
        status_container = ttk.LabelFrame(self.tab_frame, text="Status Information", padding=10)
        status_container.pack(fill=tk.X, padx=15, pady=(0, 8))
        
        status_frame = ttk.Frame(status_container)
        status_frame.pack(fill=tk.X)
        
        # 상태 메시지
        self.status_label = ttk.Label(status_frame, text="Please select an equipment type and execute QC inspection.", 
                                    font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT)
        
        # 진행률 표시
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 초기 데이터 로드
        self._load_initial_data()

    def _create_basic_qc_ui(self):
        """엔지니어 스타일 기본 QC UI 생성 - Default DB 관리 스타일 적용"""
        # 상단 제어 패널 - 배경색과 패딩 개선
        control_frame = ttk.Frame(self.tab_frame, style="Control.TFrame")
        control_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # 장비 유형 관리 섹션
        equipment_frame = ttk.LabelFrame(control_frame, text="Equipment Type Selection", padding=12)
        equipment_frame.pack(fill=tk.X, pady=(0, 8))
        
        # 장비 유형 선택
        type_select_frame = ttk.Frame(equipment_frame)
        type_select_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(type_select_frame, text="Equipment Type:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))
        self.equipment_type_var = tk.StringVar()
        self.equipment_type_combo = ttk.Combobox(type_select_frame, textvariable=self.equipment_type_var, 
                                               state="readonly", width=40, font=("Segoe UI", 9))
        self.equipment_type_combo.pack(side=tk.LEFT, padx=(0, 12))
        
        # 새로고침 버튼
        refresh_btn = ttk.Button(type_select_frame, text="Refresh", 
                               command=self._refresh_equipment_types, width=10)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 15))

        # QC 실행 관리 섹션
        qc_frame = ttk.LabelFrame(control_frame, text="QC Execution Control", padding=12)
        qc_frame.pack(fill=tk.X, pady=(0, 8))
        
        # QC 실행 버튼들
        qc_buttons_frame = ttk.Frame(qc_frame)
        qc_buttons_frame.pack(fill=tk.X)
        
        # 전체 항목 포함 체크박스
        self.chk_include_all_var = tk.BooleanVar(value=False)
        self.chk_include_all = ttk.Checkbutton(qc_buttons_frame, text="Include All Items", 
                                              variable=self.chk_include_all_var)
        self.chk_include_all.pack(side=tk.LEFT, padx=(0, 15))
        
        # QC 실행 버튼
        self.qc_run_btn = ttk.Button(qc_buttons_frame, text="Execute QC Inspection", 
                                   command=self._handle_run_qc_check, width=18)
        self.qc_run_btn.pack(side=tk.LEFT, padx=(0, 12))

        # 결과 내보내기 버튼
        self.export_btn = ttk.Button(qc_buttons_frame, text="Export Results", 
                                   command=self._handle_export_results,
                                   state="disabled", width=13)
        self.export_btn.pack(side=tk.LEFT)
        
        # QC 결과 영역
        results_container = ttk.LabelFrame(self.tab_frame, text="QC Inspection Results", padding=10)
        results_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 8))

        # 결과 탭 노트북
        self.results_notebook = ttk.Notebook(results_container)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)

        # 탭 1: 검수 결과 목록
        self._create_results_tab()
        
        # 탭 2: 최종 보고서 (메인 기능)
        self._create_final_report_tab()

        # 상태 정보 섹션
        status_container = ttk.LabelFrame(self.tab_frame, text="Status Information", padding=10)
        status_container.pack(fill=tk.X, padx=15, pady=(0, 8))
        
        status_frame = ttk.Frame(status_container)
        status_frame.pack(fill=tk.X)
        
        # 상태 메시지
        self.status_label = ttk.Label(status_frame, text="Please select an equipment type and execute QC inspection.", 
                                    font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT)
        
        # 진행률 표시
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
        
        self._load_initial_data()

    def _create_results_tab(self):
        """검수 결과 탭 생성"""
        results_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(results_tab, text="QC Results List")

        # 검수 결과 트리뷰 (향상된 컬럼 구조)
        columns = ("parameter", "issue_type", "description", "severity")
        headings = {
            "parameter": "Parameter", 
            "issue_type": "Issue Type", 
            "description": "Description", 
            "severity": "Severity"
        }
        column_widths = {
            "parameter": 200, 
            "issue_type": 150, 
            "description": 300, 
            "severity": 100
        }

        results_frame, self.result_tree = create_treeview_with_scrollbar(
            results_tab, columns, headings, column_widths, height=12)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 트리뷰 이벤트 바인딩
        self.result_tree.bind('<<TreeviewSelect>>', self._on_result_selected)
        self.result_tree.bind('<Double-1>', self._on_result_double_click)

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

    def _handle_run_qc_check(self, event=None):
        """QC 검수 실행 처리 - 단순화됨"""
        if not self.current_equipment_type:
            self.show_warning("Warning", "Please select an equipment type first.")
            return

        try:
            self.qc_status = "running"
            self._update_status("QC Inspection in progress...")
            self.qc_run_btn.config(state="disabled")
            self.progress_bar.config(value=10)

            # 기본 QC 검수 실행 (검수 옵션 없이)
            self._run_basic_qc()

        except Exception as e:
            self.qc_status = "error"
            self._update_status("QC Inspection failed")
            self.show_error("Error", f"An error occurred during QC inspection: {str(e)}")
        finally:
            self.qc_run_btn.config(state="normal")

    def _run_basic_qc(self):
        """기본 QC 검수 실행 - 단순화됨"""
        # 사용자 요청: 검수 대상 필터링 로직 추가
        include_all_items = self.chk_include_all_var.get()
        
        # DBManager의 QC 검수 메서드 직접 호출 (execute_command 대신)
        try:
            # DBManager의 perform_qc_check 메서드 호출
            if hasattr(self.viewmodel, 'perform_qc_check'):
                # 기존 QC 로직 실행
                self.viewmodel.perform_qc_check()
                
                # 성공 시 콜백 호출
                self._qc_check_complete(True, {'issues': []})
            else:
                # QC 기능을 직접 구현
                self._run_direct_qc_check(include_all_items)
                
        except Exception as e:
            # 실패 시 콜백 호출
            self._qc_check_complete(False, {'error': str(e)})

    def _run_direct_qc_check(self, include_all_items=False):
        """QC 검수 직접 실행"""
        try:
            # 장비 유형 ID 확인
            if not self.current_equipment_type:
                raise Exception("장비 유형이 선택되지 않았습니다.")
            
            # DBManager의 DB 스키마를 통해 데이터 조회
            if hasattr(self.viewmodel, 'db_schema') and self.viewmodel.db_schema:
                # Performance 항목만 또는 전체 항목 조회
                performance_only = not include_all_items  # 전체 항목 포함이면 performance_only=False
                
                data = self.viewmodel.db_schema.get_default_values(
                    self.current_equipment_type, 
                    performance_only=performance_only
                )
                
                if not data:
                    raise Exception("검수할 데이터가 없습니다.")
                
                # 기본 QC 검사 수행
                import pandas as pd
                df = pd.DataFrame(data, columns=[
                    "id", "parameter_name", "default_value", "min_spec", "max_spec", "type_name",
                    "occurrence_count", "total_files", "confidence_score", "source_files", "description",
                    "module_name", "part_name", "item_type", "is_performance"
                ])
                
                # QCValidator로 기본 검사 수행
                from app.qc import QCValidator
                results = QCValidator.run_all_checks(df, "검수")
                
                # 결과를 보고서 형식으로 변환
                qc_results = []
                for result in results:
                    qc_results.append({
                        'parameter': result.get('parameter', ''),
                        'default_value': 'N/A',
                        'file_value': 'N/A', 
                        'pass_fail': 'FAIL',
                        'issue_type': result.get('issue_type', ''),
                        'description': result.get('description', ''),
                        'severity': result.get('severity', '낮음')
                    })
                
                # 성공 콜백 호출
                self._qc_check_complete(True, {'issues': qc_results})
                
            else:
                raise Exception("데이터베이스 스키마를 사용할 수 없습니다.")
                
        except Exception as e:
            # 실패 콜백 호출
            self._qc_check_complete(False, {'error': str(e)})

    def _qc_check_complete(self, success: bool, results: Dict):
        """QC 검수 완료 콜백"""
        if success:
            self.qc_status = "complete"
            self.qc_results = results.get('issues', [])
            self._display_qc_results()
            self._update_status(f"✅ QC Inspection completed - {len(self.qc_results)} items processed")
            
            # 사용자 요청: 보고서 생성 호출 및 최종 보고서 탭으로 이동
            self._update_final_report_tab(self.qc_results)
            self.results_notebook.select(1)  # 최종 보고서 탭 선택
            
            # 내보내기 버튼 활성화
            self.export_btn.config(state="normal")
            self.progress_bar.config(value=100)
        else:
            self.qc_status = "error"
            error_msg = results.get('error', 'Unknown error occurred')
            self._update_status(f"QC Inspection failed: {error_msg}")
            self.show_error("QC Inspection Error", error_msg)
            self.progress_bar.config(value=0)

    def _display_qc_results(self):
        """QC 결과 표시 - 단순화됨"""
        # 기존 결과 삭제
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 결과 표시
        for result in self.qc_results:
            self.result_tree.insert("", "end", values=(
                result.get("parameter", ""),
                result.get("issue_type", ""),
                result.get("description", ""),
                result.get("severity", "낮음")
            ))

    def _on_result_selected(self, event=None):
        """검수 결과 선택 이벤트"""
        selection = self.result_tree.selection()
        if selection:
            item = self.result_tree.item(selection[0])
            values = item['values']
            if values:
                # 선택된 항목의 상세 정보 표시
                pass

    def _on_result_double_click(self, event=None):
        """검수 결과 더블클릭 이벤트"""
        selection = self.result_tree.selection()
        if selection:
            item = self.result_tree.item(selection[0])
            values = item['values']
            if values:
                # 상세 분석 다이얼로그 표시
                self.show_info("상세 정보", f"파라미터: {values[0]}\n문제: {values[1]}\n설명: {values[2]}")

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
        """최종 보고서 탭 생성 - 영어 제목으로 통일"""
        # 최종 보고서 탭 프레임
        self.tab_report = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.tab_report, text="Final QC Report")
        
        # 메인 그리드 레이아웃 설정
        main_layout = tk.Frame(self.tab_report)
        main_layout.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 그리드 레이아웃 사용
        main_layout.grid_rowconfigure(3, weight=1)  # 실패 항목 테이블이 확장되도록
        main_layout.grid_columnconfigure(0, weight=1)
        
        # (1행) 최종 판정 레이블
        self.lbl_overall_result = tk.Label(main_layout, text="QC Inspection Pending", 
                                          font=('Segoe UI', 18, 'bold'),
                                          fg='blue', bg='white',
                                          relief='solid', borderwidth=2,
                                          pady=15)
        self.lbl_overall_result.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        # (2행) 검수 정보 그룹박스
        info_group = ttk.LabelFrame(main_layout, text="Inspection Information", padding=10)
        info_group.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        
        # 검수 정보 레이블들
        info_frame = ttk.Frame(info_group)
        info_frame.pack(fill=tk.X)
        
        self.lbl_equipment_type = ttk.Label(info_frame, text="Equipment Type: -", font=("Segoe UI", 9))
        self.lbl_equipment_type.grid(row=0, column=0, sticky='w', padx=(0, 20))
        
        self.lbl_check_date = ttk.Label(info_frame, text="Inspection Date: -", font=("Segoe UI", 9))
        self.lbl_check_date.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        self.lbl_total_items = ttk.Label(info_frame, text="Total Items: -", font=("Segoe UI", 9))
        self.lbl_total_items.grid(row=1, column=0, sticky='w', padx=(0, 20))
        
        self.lbl_check_mode = ttk.Label(info_frame, text="Inspection Mode: -", font=("Segoe UI", 9))
        self.lbl_check_mode.grid(row=1, column=1, sticky='w', padx=(0, 20))
        
        # (3행) 핵심 요약 그룹박스
        summary_group = ttk.LabelFrame(main_layout, text="Summary Statistics", padding=10)
        summary_group.grid(row=2, column=0, sticky='ew', pady=(0, 10))
        
        # 요약 통계 프레임
        summary_frame = ttk.Frame(summary_group)
        summary_frame.pack(fill=tk.X)
        
        self.lbl_pass_count = ttk.Label(summary_frame, text="Pass: 0 items", 
                                       font=('Segoe UI', 10, 'bold'), foreground='green')
        self.lbl_pass_count.grid(row=0, column=0, sticky='w', padx=(0, 30))
        
        self.lbl_fail_count = ttk.Label(summary_frame, text="Fail: 0 items", 
                                       font=('Segoe UI', 10, 'bold'), foreground='red')
        self.lbl_fail_count.grid(row=0, column=1, sticky='w', padx=(0, 30))
        
        self.lbl_critical_count = ttk.Label(summary_frame, text="Critical: 0 items", 
                                          font=('Segoe UI', 10, 'bold'), foreground='darkred')
        self.lbl_critical_count.grid(row=0, column=2, sticky='w')
        
        self.lbl_pass_rate = ttk.Label(summary_frame, text="Pass Rate: 0%", 
                                      font=('Segoe UI', 12, 'bold'))
        self.lbl_pass_rate.grid(row=1, column=0, columnspan=3, sticky='w', pady=(5, 0))
        
        # (4행) 실패 항목 상세 테이블
        failures_group = ttk.LabelFrame(main_layout, text="Failed Items Details", padding=10)
        failures_group.grid(row=3, column=0, sticky='nsew', pady=(0, 10))
        
        # 실패 항목 테이블 생성
        table_frame = ttk.Frame(failures_group)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 테이블 컬럼 정의
        columns = ("parameter", "default_value", "file_value", "pass_fail", "issue_type", "description")
        
        self.tbl_failures = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)
        
        # 컬럼 헤더 설정
        self.tbl_failures.heading("parameter", text="Parameter Name")
        self.tbl_failures.heading("default_value", text="Default Value")
        self.tbl_failures.heading("file_value", text="File Value")
        self.tbl_failures.heading("pass_fail", text="Pass/Fail")
        self.tbl_failures.heading("issue_type", text="Issue Type")
        self.tbl_failures.heading("description", text="Description")
        
        # 컬럼 너비 설정
        self.tbl_failures.column("parameter", width=150)
        self.tbl_failures.column("default_value", width=120)
        self.tbl_failures.column("file_value", width=120)
        self.tbl_failures.column("pass_fail", width=80)
        self.tbl_failures.column("issue_type", width=120)
        self.tbl_failures.column("description", width=200)
        
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
        ttk.Button(button_frame, text="Print Report", 
                  command=self._on_print_report).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(button_frame, text="Export Report", 
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
        result_color = "green" if overall_result == "PASS" else "red"
        
        # 3. UI 업데이트
        # 최종 판정 업데이트
        self.lbl_overall_result.config(text=f"QC Inspection Result: {overall_result}", fg=result_color)
        
        # 검수 정보 업데이트 (영어로 변경)
        equipment_type = self.equipment_type_var.get() or "Not Selected"
        check_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 사용자 요청: 검수 모드를 체크박스 상태에 따라 동적으로 표시
        include_all = self.chk_include_all_var.get()
        check_mode = "All Items Included" if include_all else "Check List Only"
        
        self.lbl_equipment_type.config(text=f"Equipment Type: {equipment_type}")
        self.lbl_check_date.config(text=f"Inspection Date: {check_date}")
        self.lbl_total_items.config(text=f"Total Items: {total_items}")
        self.lbl_check_mode.config(text=f"Inspection Mode: {check_mode}")
        
        # 핵심 요약 업데이트 (영어로 변경)
        self.lbl_pass_count.config(text=f"Pass: {pass_count} items")
        self.lbl_fail_count.config(text=f"Fail: {fail_count} items")
        self.lbl_critical_count.config(text=f"Critical: {critical_count} items")
        self.lbl_pass_rate.config(text=f"Pass Rate: {pass_rate:.1f}%")
        
        # 4. 실패 항목 테이블 업데이트
        # 기존 데이터 클리어
        for item in self.tbl_failures.get_children():
            self.tbl_failures.delete(item)
        
        # 실패 항목만 필터링하여 테이블에 추가
        for item in fail_items:
            values = (
                item.get('parameter', ''),
                item.get('default_value', 'N/A'),
                item.get('file_value', 'N/A'),
                item.get('pass_fail', ''),
                item.get('issue_type', ''),
                item.get('description', '')
            )
            self.tbl_failures.insert('', 'end', values=values)

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
        
        # 보고서 헤더 (영어로 변경)
        report = []
        report.append("=" * 60)
        report.append("QC INSPECTION FINAL REPORT")
        report.append("=" * 60)
        report.append("")
        
        # 검수 정보 (영어로 변경)
        equipment_type = self.equipment_type_var.get() or "Not Selected"
        check_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 사용자 요청: 검수 모드를 체크박스 상태에 따라 동적으로 표시
        include_all = self.chk_include_all_var.get()
        check_mode = "All Items Included" if include_all else "Check List Only"
        
        report.append("INSPECTION INFORMATION")
        report.append("-" * 30)
        report.append(f"Equipment Type: {equipment_type}")
        report.append(f"Inspection Date: {check_date}")
        report.append(f"Total Items: {len(self.qc_results) if hasattr(self, 'qc_results') else 0}")
        report.append(f"Inspection Mode: {check_mode}")
        report.append("")
        
        # 핵심 요약 (영어로 변경)
        if hasattr(self, 'qc_results') and self.qc_results:
            fail_items = [r for r in self.qc_results if r.get('pass_fail', '').upper() == 'FAIL']
            pass_items = [r for r in self.qc_results if r.get('pass_fail', '').upper() == 'PASS']
            
            pass_count = len(pass_items)
            fail_count = len(fail_items)
            total_count = len(self.qc_results)
            pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0
            
            report.append("SUMMARY STATISTICS")
            report.append("-" * 30)
            report.append(f"Pass: {pass_count} items")
            report.append(f"Fail: {fail_count} items")
            report.append(f"Pass Rate: {pass_rate:.1f}%")
            report.append("")
            
            # 최종 판정 (영어로 변경)
            overall_result = "PASS" if fail_count == 0 else "FAIL"
            report.append(f"FINAL RESULT: {overall_result}")
            report.append("")
            
            # 실패 항목 상세 (영어로 변경)
            if fail_items:
                report.append("FAILED ITEMS DETAILS")
                report.append("-" * 30)
                for i, item in enumerate(fail_items, 1):
                    report.append(f"{i}. Parameter: {item.get('parameter', '')}")
                    report.append(f"   Issue Type: {item.get('issue_type', '')}")
                    report.append(f"   Description: {item.get('description', '')}")
                    report.append(f"   Severity: {item.get('severity', '')}")
                    report.append("")
        
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