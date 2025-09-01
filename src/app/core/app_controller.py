"""
애플리케이션 메인 컨트롤러
모든 컴포넌트를 통합하고 조정하는 중앙 컨트롤러
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from typing import List, Dict, Optional, Any
from pathlib import Path
import os
import sys

# Core 모듈들
from .main_window import MainWindow
from .mode_manager import ModeManager, UserMode
from .controllers.mother_db_manager import MotherDBManager
from .controllers.comparison_engine import OptimizedComparisonEngine
from .controllers.qc_manager import UnifiedQCSystem, QCMode

# 기존 모듈들
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema import DBSchema
from loading import LoadingDialog

class AppController:
    """애플리케이션 메인 컨트롤러"""
    
    def __init__(self):
        """초기화"""
        # 핵심 컴포넌트
        self.main_window = MainWindow()
        self.mode_manager = ModeManager()
        self.db_schema = None
        
        # 비즈니스 로직 매니저
        self.mother_db_manager = None
        self.comparison_engine = OptimizedComparisonEngine()
        self.qc_system = None
        
        # 상태 변수
        self.current_files = []
        self.comparison_result = None
        self.selected_equipment_type_id = None
        
        # 초기화
        self._initialize_components()
        self._setup_event_handlers()
    
    def _initialize_components(self):
        """컴포넌트 초기화"""
        # 데이터베이스 초기화
        try:
            self.db_schema = DBSchema()
            self.mother_db_manager = MotherDBManager(self.db_schema)
            self.qc_system = UnifiedQCSystem(self.db_schema)
            self.main_window.update_log("✅ 데이터베이스 초기화 완료")
        except Exception as e:
            self.main_window.update_log(f"❌ 데이터베이스 초기화 실패: {e}")
            self.db_schema = None
        
        # 윈도우 초기화
        self.window = self.main_window.initialize()
        
        # 모드 변경 콜백 등록
        self.mode_manager.register_mode_change_callback(self._on_mode_changed)
        
        # 초기 UI 설정
        self._setup_initial_ui()
    
    def _setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        # 메뉴 이벤트
        self._setup_menu_handlers()
        
        # 키 바인딩
        self.window.bind('<Control-o>', lambda e: self.load_folder())
        self.window.bind('<Control-O>', lambda e: self.load_folder())
        self.window.bind('<F1>', lambda e: self.show_help())
    
    def _setup_menu_handlers(self):
        """메뉴 핸들러 설정"""
        menubar = self.main_window.menubar
        
        # 파일 메뉴
        file_menu = menubar.nametowidget(menubar.entryconfig(0, 'menu')['menu'])
        file_menu.entryconfig("폴더 열기 (Ctrl+O)", command=self.load_folder)
        file_menu.entryconfig("보고서 내보내기", command=self.export_report)
        
        # 도구 메뉴
        tools_menu = menubar.nametowidget(menubar.entryconfig(1, 'menu')['menu'])
        tools_menu.entryconfig("👤 사용자 모드 전환", command=self.toggle_mode)
        tools_menu.entryconfig("⚙️ 설정", command=self.show_settings)
        
        # Mother DB 메뉴 (QC 모드에서만)
        if self.mode_manager.is_qc_mode():
            mother_menu = menubar.nametowidget(menubar.entryconfig(2, 'menu')['menu'])
            mother_menu.entryconfig("🎯 Mother DB 빠른 설정", command=self.quick_setup_mother_db)
            mother_menu.entryconfig("📊 Mother DB 분석", command=self.analyze_mother_db)
            mother_menu.entryconfig("🔄 Mother DB 동기화", command=self.sync_mother_db)
        
        # 도움말 메뉴
        help_menu = menubar.nametowidget(menubar.entryconfig("도움말", 'menu')['menu'])
        help_menu.entryconfig("사용 설명서 (F1)", command=self.show_help)
        help_menu.entryconfig("프로그램 정보", command=self.show_about)
    
    def _setup_initial_ui(self):
        """초기 UI 설정"""
        # 비교 탭 생성
        self._create_comparison_tabs()
        
        # 초기 로그 메시지
        self.main_window.update_log("DB Manager 시작 - 장비 생산 엔지니어 모드")
        self.main_window.update_log("Ctrl+O를 눌러 폴더를 선택하세요")
    
    def _create_comparison_tabs(self):
        """비교 관련 탭 생성"""
        notebook = self.main_window.get_comparison_notebook()
        
        # 전체 목록 탭
        self.grid_view_frame = ttk.Frame(notebook)
        notebook.add(self.grid_view_frame, text="📋 전체 목록")
        self._setup_grid_view_tab()
        
        # 메인 비교 탭
        self.comparison_frame = ttk.Frame(notebook)
        notebook.add(self.comparison_frame, text="🔍 메인 비교")
        self._setup_comparison_tab()
        
        # 차이점 분석 탭
        self.diff_frame = ttk.Frame(notebook)
        notebook.add(self.diff_frame, text="⚡ 차이점 분석")
        self._setup_diff_tab()
    
    def _setup_grid_view_tab(self):
        """전체 목록 탭 설정"""
        # 상단 도구바
        toolbar = ttk.Frame(self.grid_view_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="전체 파라미터 목록").pack(side=tk.LEFT, padx=5)
        
        # 필터 버튼
        ttk.Button(toolbar, text="🔍 필터", command=self.show_filter_dialog).pack(side=tk.RIGHT, padx=5)
        
        # 트리뷰
        tree_frame = ttk.Frame(self.grid_view_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.grid_tree = ttk.Treeview(tree_frame)
        self.grid_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.grid_tree.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.grid_tree.configure(yscrollcommand=v_scroll.set)
        
        h_scroll = ttk.Scrollbar(self.grid_view_frame, orient="horizontal", command=self.grid_tree.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.grid_tree.configure(xscrollcommand=h_scroll.set)
    
    def _setup_comparison_tab(self):
        """메인 비교 탭 설정"""
        # 상단 도구바
        toolbar = ttk.Frame(self.comparison_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # 전체 선택 체크박스
        self.select_all_var = tk.BooleanVar()
        ttk.Checkbutton(
            toolbar, 
            text="전체 선택", 
            variable=self.select_all_var,
            command=self.toggle_select_all
        ).pack(side=tk.LEFT, padx=5)
        
        # 선택 카운트
        self.selected_count_label = ttk.Label(toolbar, text="선택: 0 항목")
        self.selected_count_label.pack(side=tk.LEFT, padx=20)
        
        # Mother DB 전송 버튼 (QC 모드에서만)
        self.send_to_mother_btn = ttk.Button(
            toolbar,
            text="🚀 Mother DB로 전송",
            command=self.send_to_mother_db,
            state="disabled"
        )
        self.send_to_mother_btn.pack(side=tk.RIGHT, padx=5)
        
        # 트리뷰
        tree_frame = ttk.Frame(self.comparison_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.comparison_tree = ttk.Treeview(tree_frame)
        self.comparison_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.comparison_tree.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.comparison_tree.configure(yscrollcommand=v_scroll.set)
    
    def _setup_diff_tab(self):
        """차이점 분석 탭 설정"""
        # 상단 정보
        info_frame = ttk.Frame(self.diff_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.diff_info_label = ttk.Label(info_frame, text="차이점 분석 결과")
        self.diff_info_label.pack(side=tk.LEFT, padx=5)
        
        # 트리뷰
        tree_frame = ttk.Frame(self.diff_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.diff_tree = ttk.Treeview(tree_frame)
        self.diff_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.diff_tree.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.diff_tree.configure(yscrollcommand=v_scroll.set)
    
    def _on_mode_changed(self, new_mode: UserMode):
        """모드 변경 이벤트 처리"""
        mode_name = self.mode_manager.get_mode_display_name()
        self.main_window.update_status(mode_name)
        self.main_window.update_log(f"모드 변경: {mode_name}")
        
        if new_mode == UserMode.QC_ENGINEER:
            self._enable_qc_features()
        else:
            self._disable_qc_features()
    
    def _enable_qc_features(self):
        """QC 엔지니어 기능 활성화"""
        # Mother DB 메뉴 활성화
        self.main_window.enable_mother_db_menu(True)
        
        # Mother DB 전송 버튼 활성화
        if hasattr(self, 'send_to_mother_btn'):
            self.send_to_mother_btn.config(state="normal")
        
        # QC 탭 추가
        self._add_qc_tabs()
        
        self.main_window.update_log("✅ QC 엔지니어 기능 활성화")
    
    def _disable_qc_features(self):
        """QC 엔지니어 기능 비활성화"""
        # Mother DB 메뉴 비활성화
        self.main_window.enable_mother_db_menu(False)
        
        # Mother DB 전송 버튼 비활성화
        if hasattr(self, 'send_to_mother_btn'):
            self.send_to_mother_btn.config(state="disabled")
        
        # QC 탭 제거
        self._remove_qc_tabs()
        
        self.main_window.update_log("📌 장비 생산 엔지니어 모드로 전환")
    
    def _add_qc_tabs(self):
        """QC 관련 탭 추가"""
        main_notebook = self.main_window.get_main_notebook()
        
        # QC 검수 탭
        self.qc_frame = ttk.Frame(main_notebook)
        main_notebook.add(self.qc_frame, text="✅ QC 검수")
        self._setup_qc_tab()
        
        # Mother DB 관리 탭
        self.mother_db_frame = ttk.Frame(main_notebook)
        main_notebook.add(self.mother_db_frame, text="🎯 Mother DB 관리")
        self._setup_mother_db_tab()
    
    def _remove_qc_tabs(self):
        """QC 관련 탭 제거"""
        main_notebook = self.main_window.get_main_notebook()
        
        # 탭 제거
        for tab_name in ["✅ QC 검수", "🎯 Mother DB 관리"]:
            self.main_window.remove_tab(main_notebook, tab_name)
    
    def _setup_qc_tab(self):
        """QC 검수 탭 설정"""
        # 상단 컨트롤
        control_frame = ttk.Frame(self.qc_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="QC 모드:").pack(side=tk.LEFT, padx=5)
        
        self.qc_mode_var = tk.StringVar(value="자동")
        qc_mode_combo = ttk.Combobox(
            control_frame,
            textvariable=self.qc_mode_var,
            values=["자동", "기본", "고급"],
            state="readonly",
            width=10
        )
        qc_mode_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="🔍 QC 검수 실행",
            command=self.run_qc_check
        ).pack(side=tk.LEFT, padx=20)
        
        ttk.Button(
            control_frame,
            text="📄 리포트 생성",
            command=self.generate_qc_report
        ).pack(side=tk.LEFT, padx=5)
        
        # 결과 표시 영역
        result_frame = ttk.LabelFrame(self.qc_frame, text="검수 결과")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.qc_result_tree = ttk.Treeview(result_frame)
        self.qc_result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        qc_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.qc_result_tree.yview)
        qc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.qc_result_tree.configure(yscrollcommand=qc_scroll.set)
    
    def _setup_mother_db_tab(self):
        """Mother DB 관리 탭 설정"""
        # 상단 정보
        info_frame = ttk.Frame(self.mother_db_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 장비 유형 선택
        ttk.Label(info_frame, text="장비 유형:").pack(side=tk.LEFT, padx=5)
        
        self.equipment_type_var = tk.StringVar()
        self.equipment_combo = ttk.Combobox(
            info_frame,
            textvariable=self.equipment_type_var,
            state="readonly",
            width=20
        )
        self.equipment_combo.pack(side=tk.LEFT, padx=5)
        self.equipment_combo.bind("<<ComboboxSelected>>", self.on_equipment_selected)
        
        # Mother DB 상태
        self.mother_db_status = ttk.Label(info_frame, text="상태: -")
        self.mother_db_status.pack(side=tk.LEFT, padx=20)
        
        # 버튼들
        button_frame = ttk.Frame(self.mother_db_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="🎯 빠른 설정",
            command=self.quick_setup_mother_db
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="📊 분석",
            command=self.analyze_mother_db
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🔄 동기화",
            command=self.sync_mother_db
        ).pack(side=tk.LEFT, padx=5)
        
        # Mother DB 내용 표시
        content_frame = ttk.LabelFrame(self.mother_db_frame, text="Mother DB 내용")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.mother_db_tree = ttk.Treeview(content_frame)
        self.mother_db_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        mother_scroll = ttk.Scrollbar(content_frame, orient="vertical", command=self.mother_db_tree.yview)
        mother_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.mother_db_tree.configure(yscrollcommand=mother_scroll.set)
        
        # 장비 유형 목록 로드
        self._load_equipment_types()
    
    def _load_equipment_types(self):
        """장비 유형 목록 로드"""
        if self.db_schema:
            try:
                types = self.db_schema.get_equipment_types()
                type_names = [t[1] for t in types]  # type_name만 추출
                
                if hasattr(self, 'equipment_combo'):
                    self.equipment_combo['values'] = type_names
                    if type_names:
                        self.equipment_combo.current(0)
                        self.on_equipment_selected(None)
            except Exception as e:
                self.main_window.update_log(f"장비 유형 로드 실패: {e}")
    
    # === 이벤트 핸들러 ===
    
    def load_folder(self):
        """폴더 선택 및 파일 로드"""
        folder_path = filedialog.askdirectory(title="DB 파일이 있는 폴더를 선택하세요")
        
        if not folder_path:
            return
        
        # 지원하는 파일 확장자
        supported_extensions = ['.txt', '.csv', '.xlsx', '.xls']
        
        # 폴더에서 파일 찾기
        files = []
        for ext in supported_extensions:
            files.extend(Path(folder_path).glob(f"*{ext}"))
        
        if not files:
            messagebox.showwarning("파일 없음", "선택한 폴더에 DB 파일이 없습니다.")
            return
        
        # 파일 선택 다이얼로그
        file_paths = filedialog.askopenfilenames(
            initialdir=folder_path,
            title="비교할 파일들을 선택하세요 (최대 6개)",
            filetypes=[
                ("모든 DB 파일", "*.txt;*.csv;*.xlsx;*.xls"),
                ("텍스트 파일", "*.txt"),
                ("CSV 파일", "*.csv"),
                ("Excel 파일", "*.xlsx;*.xls")
            ]
        )
        
        if not file_paths:
            return
        
        if len(file_paths) > 6:
            messagebox.showwarning("파일 수 제한", "최대 6개까지만 선택 가능합니다.")
            file_paths = file_paths[:6]
        
        # 로딩 다이얼로그 표시
        loading = LoadingDialog(self.window, "파일 로딩 중...")
        loading.show()
        
        try:
            # 파일 비교
            self.current_files = list(file_paths)
            self.comparison_result = self.comparison_engine.compare_files(self.current_files)
            
            # UI 업데이트
            self._update_comparison_display()
            
            self.main_window.update_log(f"✅ {len(file_paths)}개 파일 로드 완료")
            
            # 차이점 요약
            summary = self.comparison_engine.get_difference_summary(self.comparison_result)
            self.main_window.update_log(
                f"📊 비교 결과: 전체 {summary['total_parameters']}개, "
                f"차이 {summary['different_parameters']}개 ({summary['difference_rate']:.1f}%)"
            )
            
        except Exception as e:
            messagebox.showerror("오류", f"파일 로드 실패: {e}")
            self.main_window.update_log(f"❌ 파일 로드 실패: {e}")
        finally:
            loading.close()
    
    def _update_comparison_display(self):
        """비교 결과 표시 업데이트"""
        if self.comparison_result is None or self.comparison_result.empty:
            return
        
        # 전체 목록 탭 업데이트
        self._update_grid_view()
        
        # 메인 비교 탭 업데이트
        self._update_comparison_view()
        
        # 차이점 분석 탭 업데이트
        self._update_diff_view()
    
    def _update_grid_view(self):
        """전체 목록 뷰 업데이트"""
        # 기존 항목 제거
        for item in self.grid_tree.get_children():
            self.grid_tree.delete(item)
        
        # 컬럼 설정
        columns = list(self.comparison_result.columns)
        self.grid_tree['columns'] = columns
        self.grid_tree.heading('#0', text='')
        self.grid_tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.grid_tree.heading(col, text=col)
            self.grid_tree.column(col, width=100)
        
        # 데이터 추가
        for idx, row in self.comparison_result.iterrows():
            values = [row[col] for col in columns]
            self.grid_tree.insert('', 'end', values=values)
    
    def _update_comparison_view(self):
        """메인 비교 뷰 업데이트"""
        # 기존 항목 제거
        for item in self.comparison_tree.get_children():
            self.comparison_tree.delete(item)
        
        # 파라미터별로 그룹화
        grouped = self.comparison_result.groupby('parameter_name')
        
        # 컬럼 설정
        file_names = [Path(f).stem for f in self.current_files]
        columns = ['parameter_name'] + file_names + ['차이여부']
        self.comparison_tree['columns'] = columns
        self.comparison_tree.heading('#0', text='')
        self.comparison_tree.column('#0', width=50)  # 체크박스용
        
        for col in columns:
            self.comparison_tree.heading(col, text=col)
            self.comparison_tree.column(col, width=120)
        
        # 데이터 추가
        for param_name, group in grouped:
            values = [param_name]
            
            # 각 파일의 값
            for file_name in file_names:
                file_data = group[group['file_name'] == file_name]
                if not file_data.empty:
                    values.append(file_data.iloc[0].get('default_value', ''))
                else:
                    values.append('')
            
            # 차이 여부
            is_different = group['is_different'].iloc[0] if 'is_different' in group.columns else False
            values.append('O' if is_different else 'X')
            
            # 트리에 추가
            item = self.comparison_tree.insert('', 'end', values=values)
            
            # 차이가 있으면 색상 변경
            if is_different:
                self.comparison_tree.item(item, tags=('different',))
        
        # 태그 색상 설정
        self.comparison_tree.tag_configure('different', background='#ffe0e0')
    
    def _update_diff_view(self):
        """차이점 분석 뷰 업데이트"""
        # 기존 항목 제거
        for item in self.diff_tree.get_children():
            self.diff_tree.delete(item)
        
        # 차이점만 필터링
        diff_only = self.comparison_result[self.comparison_result['is_different'] == True]
        
        if diff_only.empty:
            self.diff_info_label.config(text="차이점 없음")
            return
        
        # 정보 업데이트
        self.diff_info_label.config(text=f"차이점: {len(diff_only['parameter_name'].unique())}개 항목")
        
        # 컬럼 설정
        columns = ['parameter_name', 'file_name', 'default_value', 'common_value']
        self.diff_tree['columns'] = columns
        self.diff_tree.heading('#0', text='')
        self.diff_tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.diff_tree.heading(col, text=col)
            self.diff_tree.column(col, width=150)
        
        # 데이터 추가
        for idx, row in diff_only.iterrows():
            values = [row.get(col, '') for col in columns]
            self.diff_tree.insert('', 'end', values=values)
    
    def toggle_mode(self):
        """사용자 모드 전환"""
        success = self.mode_manager.toggle_mode(self.window)
        if success:
            mode_name = self.mode_manager.get_mode_display_name()
            messagebox.showinfo("모드 전환", f"{mode_name}로 전환되었습니다.")
    
    def quick_setup_mother_db(self):
        """Mother DB 빠른 설정"""
        if not self.comparison_result or self.comparison_result.empty:
            messagebox.showwarning("데이터 없음", "먼저 파일을 로드하고 비교를 수행하세요.")
            return
        
        if not self.selected_equipment_type_id:
            messagebox.showwarning("장비 미선택", "장비 유형을 선택하세요.")
            return
        
        # 확인 다이얼로그
        response = messagebox.askyesno(
            "Mother DB 빠른 설정",
            "비교 결과에서 80% 이상 일치하는 항목들을 자동으로 Mother DB로 설정합니다.\n계속하시겠습니까?"
        )
        
        if not response:
            return
        
        # 로딩 다이얼로그
        loading = LoadingDialog(self.window, "Mother DB 설정 중...")
        loading.show()
        
        try:
            # Mother DB 설정
            file_names = [Path(f).stem for f in self.current_files]
            result = self.mother_db_manager.quick_setup_mother_db(
                self.comparison_result,
                file_names,
                self.selected_equipment_type_id
            )
            
            # 결과 메시지
            message = f"""
Mother DB 설정 완료!

• 분석된 후보: {result['total_candidates']}개
• 저장된 항목: {result['saved_count']}개
• 충돌 해결: {result['conflict_count']}개
            """
            
            messagebox.showinfo("완료", message.strip())
            self.main_window.update_log(f"✅ Mother DB 설정 완료: {result['saved_count']}개 항목 저장")
            
            # Mother DB 탭 업데이트
            self._refresh_mother_db_display()
            
        except Exception as e:
            messagebox.showerror("오류", f"Mother DB 설정 실패: {e}")
            self.main_window.update_log(f"❌ Mother DB 설정 실패: {e}")
        finally:
            loading.close()
    
    def analyze_mother_db(self):
        """Mother DB 분석"""
        if not self.selected_equipment_type_id:
            messagebox.showwarning("장비 미선택", "장비 유형을 선택하세요.")
            return
        
        try:
            # Mother DB 상태 분석
            status = self.mother_db_manager.analyze_mother_db_status(self.selected_equipment_type_id)
            
            # 결과 표시
            message = f"""
Mother DB 분석 결과

• 전체 파라미터: {status['total_parameters']}개
• 높은 신뢰도: {status['high_confidence_count']}개
• 낮은 신뢰도: {status['low_confidence_count']}개
• 평균 신뢰도: {status['average_confidence']:.2f}
            """
            
            messagebox.showinfo("Mother DB 분석", message.strip())
            
        except Exception as e:
            messagebox.showerror("오류", f"분석 실패: {e}")
    
    def sync_mother_db(self):
        """Mother DB 동기화"""
        messagebox.showinfo("동기화", "Mother DB 동기화 기능은 준비 중입니다.")
    
    def run_qc_check(self):
        """QC 검수 실행"""
        if not self.comparison_result or self.comparison_result.empty:
            messagebox.showwarning("데이터 없음", "먼저 파일을 로드하세요.")
            return
        
        # QC 모드 결정
        mode_map = {
            "자동": QCMode.AUTO,
            "기본": QCMode.BASIC,
            "고급": QCMode.ADVANCED
        }
        qc_mode = mode_map.get(self.qc_mode_var.get(), QCMode.AUTO)
        
        # 로딩 다이얼로그
        loading = LoadingDialog(self.window, "QC 검수 진행 중...")
        loading.show()
        
        try:
            # QC 검수 실행
            result = self.qc_system.perform_qc(
                self.comparison_result,
                self.selected_equipment_type_id or 1,
                mode=qc_mode
            )
            
            # 결과 표시
            self._display_qc_results(result)
            
            # 요약 메시지
            message = f"""
QC 검수 완료!

• 전체: {result.total_parameters}개
• 합격: {result.passed_count}개 ({result.pass_rate:.1f}%)
• 불합격: {result.failed_count}개
• 경고: {result.warning_count}개
            """
            
            messagebox.showinfo("QC 검수 완료", message.strip())
            self.main_window.update_log(f"✅ QC 검수 완료: 합격률 {result.pass_rate:.1f}%")
            
            # 결과 저장
            self.last_qc_result = result
            
        except Exception as e:
            messagebox.showerror("오류", f"QC 검수 실패: {e}")
            self.main_window.update_log(f"❌ QC 검수 실패: {e}")
        finally:
            loading.close()
    
    def _display_qc_results(self, result):
        """QC 결과 표시"""
        # 기존 항목 제거
        for item in self.qc_result_tree.get_children():
            self.qc_result_tree.delete(item)
        
        # 컬럼 설정
        columns = ['파라미터', '이슈타입', '설명', '심각도', '권장사항']
        self.qc_result_tree['columns'] = columns
        self.qc_result_tree.heading('#0', text='')
        self.qc_result_tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.qc_result_tree.heading(col, text=col)
            self.qc_result_tree.column(col, width=150)
        
        # 이슈 추가
        for issue in result.issues:
            values = [
                issue.parameter_name,
                issue.issue_type,
                issue.description,
                issue.severity.value,
                issue.recommendation or ''
            ]
            
            item = self.qc_result_tree.insert('', 'end', values=values)
            
            # 심각도에 따른 색상
            if issue.severity.value == "높음":
                self.qc_result_tree.item(item, tags=('high',))
            elif issue.severity.value == "중간":
                self.qc_result_tree.item(item, tags=('medium',))
            else:
                self.qc_result_tree.item(item, tags=('low',))
        
        # 태그 색상 설정
        self.qc_result_tree.tag_configure('high', background='#ffcccc')
        self.qc_result_tree.tag_configure('medium', background='#ffffcc')
        self.qc_result_tree.tag_configure('low', background='#ccffcc')
    
    def generate_qc_report(self):
        """QC 리포트 생성"""
        if not hasattr(self, 'last_qc_result'):
            messagebox.showwarning("결과 없음", "먼저 QC 검수를 실행하세요.")
            return
        
        # 파일 저장 다이얼로그
        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[
                ("HTML 파일", "*.html"),
                ("Excel 파일", "*.xlsx")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # 형식 결정
            format = "html" if file_path.endswith('.html') else "excel"
            
            # 리포트 생성
            success = self.qc_system.export_report(self.last_qc_result, file_path, format)
            
            if success:
                messagebox.showinfo("완료", f"리포트가 저장되었습니다:\n{file_path}")
                self.main_window.update_log(f"✅ QC 리포트 저장: {file_path}")
            else:
                messagebox.showerror("오류", "리포트 생성 실패")
                
        except Exception as e:
            messagebox.showerror("오류", f"리포트 생성 실패: {e}")
    
    def send_to_mother_db(self):
        """선택된 항목을 Mother DB로 전송"""
        messagebox.showinfo("전송", "선택된 항목을 Mother DB로 전송하는 기능은 준비 중입니다.")
    
    def on_equipment_selected(self, event):
        """장비 유형 선택 이벤트"""
        if not self.db_schema:
            return
        
        equipment_name = self.equipment_type_var.get()
        if not equipment_name:
            return
        
        try:
            # 장비 ID 찾기
            equipment = self.db_schema.get_equipment_type_by_name(equipment_name)
            if equipment:
                self.selected_equipment_type_id = equipment[0]
                self._refresh_mother_db_display()
                self.main_window.update_log(f"장비 선택: {equipment_name}")
        except Exception as e:
            self.main_window.update_log(f"장비 선택 오류: {e}")
    
    def _refresh_mother_db_display(self):
        """Mother DB 표시 갱신"""
        # 구현 생략 (실제 Mother DB 데이터 로드 및 표시)
        pass
    
    def toggle_select_all(self):
        """전체 선택/해제"""
        # 구현 생략
        pass
    
    def show_filter_dialog(self):
        """필터 다이얼로그 표시"""
        messagebox.showinfo("필터", "필터 기능은 준비 중입니다.")
    
    def export_report(self):
        """보고서 내보내기"""
        if not self.comparison_result or self.comparison_result.empty:
            messagebox.showwarning("데이터 없음", "먼저 파일을 로드하세요.")
            return
        
        # 파일 저장 다이얼로그
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Excel 파일", "*.xlsx"),
                ("CSV 파일", "*.csv")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # 형식 결정
            format = "excel" if file_path.endswith('.xlsx') else "csv"
            
            # 리포트 생성
            success = self.comparison_engine.export_comparison_report(
                self.comparison_result, 
                file_path, 
                format
            )
            
            if success:
                messagebox.showinfo("완료", f"보고서가 저장되었습니다:\n{file_path}")
                self.main_window.update_log(f"✅ 보고서 저장: {file_path}")
            else:
                messagebox.showerror("오류", "보고서 생성 실패")
                
        except Exception as e:
            messagebox.showerror("오류", f"보고서 생성 실패: {e}")
    
    def show_settings(self):
        """설정 다이얼로그"""
        messagebox.showinfo("설정", "설정 기능은 준비 중입니다.")
    
    def show_help(self):
        """도움말 표시"""
        messagebox.showinfo("도움말", "DB Manager - Mother DB 관리 시스템\n\nF1: 도움말\nCtrl+O: 폴더 열기")
    
    def show_about(self):
        """프로그램 정보"""
        messagebox.showinfo(
            "프로그램 정보",
            "DB Manager v2.0\nMother DB 관리 시스템\n\n최적화된 워크플로우로 효율적인 DB 관리"
        )
    
    def run(self):
        """애플리케이션 실행"""
        self.window.mainloop()