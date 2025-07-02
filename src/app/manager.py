# DBManager 클래스 및 메인 GUI 관리

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sys, os
from datetime import datetime
from app.schema import DBSchema
from app.loading import LoadingDialog
from app.qc import add_qc_check_functions_to_class
from app.enhanced_qc import add_enhanced_qc_functions_to_class
# Default DB 기능 제거됨 - 리팩토링으로 중복 코드 정리
from app.utils import create_treeview_with_scrollbar, create_label_entry_pair, format_num_value
from app.data_utils import numeric_sort_key, calculate_string_similarity
from app.config_manager import ConfigManager
from app.file_service import FileService, export_dataframe_to_file, export_tree_data_to_file
from app.dialog_helpers import create_parameter_dialog, center_dialog, validate_numeric_range, handle_error

# 🆕 새로운 설정 시스템 (선택적 사용)
try:
    from app.core.config import AppConfig
    from app.utils.path_utils import PathManager
    from app.utils.validation import ValidationUtils
    USE_NEW_CONFIG = True
except ImportError:
    USE_NEW_CONFIG = False

# 🆕 새로운 서비스 시스템 (점진적 전환)
try:
    from app.services import ServiceFactory, LegacyAdapter, SERVICES_AVAILABLE
    import json
    USE_NEW_SERVICES = True
except ImportError:
    USE_NEW_SERVICES = False
    SERVICES_AVAILABLE = False


# 첫 번째 DBManager 클래스 제거됨 - 중복 코드 정리

class DBManager:
    def __init__(self):
        # 🆕 새로운 설정 시스템 사용 (기존 코드 유지)
        if USE_NEW_CONFIG:
            self.config = AppConfig()
            self.path_manager = PathManager()
            self.validator = ValidationUtils()
        
        self.maint_mode = False
        self.selected_equipment_type_id = None
        self.file_names = []
        self.folder_path = ""
        self.merged_df = None
        self.context_menu = None
        
        # QC 엔지니어용 탭 프레임들을 저장할 변수들
        self.qc_check_frame = None
        self.default_db_frame = None
        
        try:
            self.db_schema = DBSchema()
        except Exception as e:
            print(f"DB 스키마 초기화 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            self.db_schema = None
        
        add_qc_check_functions_to_class(DBManager)
        add_enhanced_qc_functions_to_class(DBManager)
        # Default DB 기능 제거됨 - 리팩토링 완료
        
        # 서비스 레이어 초기화 (DB 스키마 초기화 후)
        self._setup_service_layer()
        
        # 🆕 아이콘 로드 개선 (기존 코드와 호환)
        if USE_NEW_CONFIG:
            self._setup_window_with_new_config()
        else:
            self._setup_window_legacy()
        
        # 바인딩 설정
        for key in ('<Control-o>', '<Control-O>'):
            self.window.bind(key, self.load_folder)
        self.window.bind('<F1>', self.show_user_guide)
        
        self.status_bar.config(text="Ready")
        self.update_log("DB Manager 초기화 완료 - 장비 생산 엔지니어 모드")
        if self.db_schema:
            self.update_log("로컬 데이터베이스 초기화 완료")
        else:
            self.update_log("DB 스키마 초기화 실패")
        
        # 서비스 레이어 상태 로그 추가
        if hasattr(self, '_service_layer_ready') and self._service_layer_ready:
            status = self.service_factory.get_service_status()
            self.update_log(f"서비스 레이어 초기화 완료: {len(status)}개 서비스 등록")
            
            # 장비 관리 서비스 상태 확인
            if 'IEquipmentService' in status:
                self.update_log("장비 관리 서비스 사용 가능")
        
        # 🆕 ConfigManager 초기화 (설정 및 서비스 관리)
        config_to_pass = self.config if USE_NEW_CONFIG else None
        self.config_manager = ConfigManager(config_to_pass, self.db_schema, self.update_log)
        
        # 🆕 FileService 초기화 (파일 처리 관리)
        self.file_service = FileService()
        
        # 기본적으로는 장비 생산 엔지니어용 탭만 생성
        self.create_comparison_tabs()

    def _setup_window_with_new_config(self):
        """새로운 설정 시스템을 사용한 윈도우 설정"""
        self.window = tk.Tk()
        self.window.title(self.config.app_name)
        self.window.geometry(self.config.window_geometry)
        
        try:
            icon_path = self.config.icon_path
            if icon_path and icon_path.exists():
                self.window.iconbitmap(str(icon_path))
        except Exception as e:
            print(f"아이콘 로드 실패: {str(e)}")
        
        self._setup_common_ui()
    
    def _setup_window_legacy(self):
        """기존 방식의 윈도우 설정 (fallback)"""
        self.window = tk.Tk()
        self.window.title("DB Manager")
        self.window.geometry("1300x800")
        try:
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                # src/app/manager.py에서 프로젝트 루트로 2번 상위 디렉토리로 이동
                application_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(application_path, "resources", "icons", "db_compare.ico")
            self.window.iconbitmap(icon_path)
        except Exception as e:
            print(f"아이콘 로드 실패: {str(e)}")
        
        self._setup_common_ui()
    
    def _setup_common_ui(self):
        """공통 UI 요소들을 설정합니다."""
        self.create_menu()
        self.status_bar = ttk.Label(self.window, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.main_notebook = ttk.Notebook(self.window)
        self.main_notebook.pack(expand=True, fill=tk.BOTH)
        self.comparison_notebook = ttk.Notebook(self.main_notebook)
        self.main_notebook.add(self.comparison_notebook, text="DB 비교")
        self.log_text = tk.Text(self.window, height=5, state=tk.DISABLED)
        self.log_text.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        log_scrollbar = ttk.Scrollbar(self.log_text, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_service_layer(self):
        """🆕 새로운 서비스 레이어 초기화"""
        self.service_factory = None
        self.legacy_adapter = None
        self.use_new_services = {}
        
        
        if not USE_NEW_SERVICES or not SERVICES_AVAILABLE:
            # 새로운 서비스 시스템이 아직 구현되지 않았으므로 기존 방식 사용 (정상 동작)
            return
        
        try:
            # 설정 파일에서 서비스 사용 설정 로드
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "settings.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.use_new_services = settings.get('use_new_services', {})
                    service_config = settings.get('service_config', {})
            else:
                self.use_new_services = {'equipment_service': False}
                service_config = {}
            
            # 서비스 팩토리 초기화
            if self.db_schema:
                self.service_factory = ServiceFactory(self.db_schema, service_config)
                self.legacy_adapter = LegacyAdapter(self.service_factory)
                
                # 서비스 상태 확인
                status = self.service_factory.get_service_status()
                # UI 초기화 후 로그 추가를 위해 플래그 설정
                self._service_layer_ready = True
                
            else:
                self.update_log("DB 스키마가 없어 서비스 팩토리를 초기화할 수 없습니다")
                
        except Exception as e:
            self.update_log(f"서비스 레이어 초기화 실패: {str(e)}")
            print(f"Service layer initialization failed: {str(e)}")
    
    def _should_use_service(self, service_name: str) -> bool:
        """특정 서비스 사용 여부 확인"""
        return self.config_manager.should_use_service(service_name)

    def get_db_connection(self):
        """
        데이터베이스 연결을 반환합니다.
        다른 모듈들(qc.py, defaultdb.py, file_handler.py)에서 사용됩니다.
        
        Returns:
            sqlite3.Connection: 데이터베이스 연결 객체
        """
        if self.db_schema:
            import sqlite3
            return sqlite3.connect(self.db_schema.db_path)
        else:
            raise Exception("DBSchema가 초기화되지 않았습니다.")

    def show_about(self):
        """프로그램 정보 다이얼로그 표시"""
        # About 창 생성
        about_window = tk.Toplevel(self.window)
        about_window.title("About")
        about_window.geometry("600x800")
        
        # 스타일 설정
        style = ttk.Style()
        style.configure("Title.TLabel", font=('Helvetica', 16, 'bold'))
        style.configure("Header.TLabel", font=('Helvetica', 12, 'bold'))
        style.configure("Content.TLabel", font=('Helvetica', 10))
        
        # 컨테이너 프레임
        container = ttk.Frame(about_window, padding="20")
        container.pack(expand=True, fill=tk.BOTH)
        
        # 프로그램 제목
        title_frame = ttk.Frame(container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(title_frame, text="DB 관리 프로그램", style="Title.TLabel").pack()
        
        # 정보 섹션들
        sections = [
            ("Product Information", [
                ("Version", "1.0.0"),
                ("Release Date", "2025-02-04"),
            ]),
            ("Development", [
                ("Developer", "Levi Beak / 백광림"),
                ("Organization", "Quality Assurance Team"),
                ("Contact", "levi.beak@parksystems.com"),
            ]),
        ]
        
        for section_title, items in sections:
            # 섹션 프레임
            section_frame = ttk.LabelFrame(container, text=section_title, padding="10")
            section_frame.pack(fill=tk.X, pady=(0, 10))
            
            # 그리드 구성
            for i, (key, value) in enumerate(items):
                ttk.Label(section_frame, text=key + ":", style="Header.TLabel").grid(
                    row=i, column=0, sticky="w", padx=(0, 10), pady=2)
                ttk.Label(section_frame, text=value, style="Content.TLabel").grid(
                    row=i, column=1, sticky="w", pady=2)
        
        # 프로그램 설명
        desc_frame = ttk.LabelFrame(container, text="Description", padding="10")
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        
        description = """이 프로그램은 XES 데이터베이스 비교 및 관리를 위한 프로그램입니다.
        
주요 기능:
• 다중 DB 파일 비교 분석
• 차이점 자동 감지 및 하이라이트
• 상세 비교 보고서 생성
• 데이터 시각화 및 통계 분석
• QC 스펙 관리 및 검증(추가 예정)
"""
        
        ttk.Label(desc_frame, text=description, style="Content.TLabel", 
                 wraplength=500, justify="left").pack(anchor="w")
        
        # 리비전 히스토리 데이터
        revisions = [
            {
                "version": "1.0.0",
                "date": "2025-02-04",
                "summary": "초기 버전 출시",
                "details": {
                    "Features": [
                        "다중 XES DB 파일 비교 분석 기능",
                        "자동 차이점 감지 및 하이라이트",
                        "상세 비교 보고서 생성"
                    ],
                    "Improvements": [
                        "데이터 시각화 도구 추가"
                    ],
                    "Bug Fixes": [
                        "파일 로드 시 인코딩 문제 수정",
                        "메모리 사용량 최적화"
                    ]
                }
            }
            # 새로운 버전이 출시될 때마다 여기에 추가
        ]
        
        # 리비전 히스토리를 위한 트리뷰 생성
        revision_frame = ttk.LabelFrame(container, text="Revision History", padding="10")
        revision_frame.pack(fill=tk.X, pady=(0, 10))
        
        revision_tree = ttk.Treeview(revision_frame, height=6)
        revision_tree["columns"] = ("Version", "Date", "Summary")
        revision_tree.heading("#0", text="")
        revision_tree.column("#0", width=0, stretch=False)
        
        for col, width in [("Version", 70), ("Date", 100), ("Summary", 400)]:
            revision_tree.heading(col, text=col)
            revision_tree.column(col, width=width)
        
        # 리비전 데이터 추가
        for rev in revisions:
            revision_tree.insert("", 0, values=(
                rev["version"],
                rev["date"],
                rev["summary"]
            ), tags=("revision",))
        
        # 더블 클릭 이벤트 처리
        def show_revision_details(event):
            if not revision_tree.selection():
                return
            item = revision_tree.selection()[0]
            version = revision_tree.item(item)["values"][0]
            
            # 해당 버전의 상세 정보 찾기
            rev_info = next(r for r in revisions if r["version"] == version)
            
            # 상세 정보 창 생성
            detail_window = tk.Toplevel(about_window)
            detail_window.title(f"Version {version} Details")
            detail_window.geometry("500x800")  # About 창과 같은 높이로 설정
            detail_window.transient(about_window)
            detail_window.grab_set()
            
            # About 창 오른쪽에 나란히 표시 (화면 범위 체크 추가)
            about_x = about_window.winfo_x()
            about_y = about_window.winfo_y()
            about_width = about_window.winfo_width()
            
            # 화면 크기 확인
            screen_width = detail_window.winfo_screenwidth()
            
            # 새 창의 x 좌표 계산
            new_x = about_x + about_width + 10
            
            # 화면 밖으로 넘어갈 경우 About 창 왼쪽에 표시
            if new_x + 500 > screen_width:  # 500은 detail_window의 너비
                new_x = about_x - 510  # 왼쪽에 표시 (간격 10픽셀)
            
            detail_window.geometry(f"500x800+{new_x}+{about_y}")
            
            # 스타일 설정
            style = ttk.Style()
            style.configure("Category.TLabel", font=('Helvetica', 11, 'bold'))
            style.configure("Item.TLabel", font=('Helvetica', 10))
            
            # 컨테이너 생성
            detail_container = ttk.Frame(detail_window, padding="20")
            detail_container.pack(fill=tk.BOTH, expand=True)
            
            # 버전 정보 헤더
            ttk.Label(
                detail_container,
                text=f"Version {version} ({rev_info['date']})",
                style="Title.TLabel"
            ).pack(anchor="w", pady=(0, 20))
            
            # 카테고리별 상세 정보 표시
            for category, items in rev_info["details"].items():
                # 카테고리 제목
                ttk.Label(
                    detail_container,
                    text=category,
                    style="Category.TLabel"
                ).pack(anchor="w", pady=(10, 5))
                
                # 항목들
                for item in items:
                    ttk.Label(
                        detail_container,
                        text=f"• {item}",
                        style="Item.TLabel",
                        wraplength=450
                    ).pack(anchor="w", padx=(20, 0))
            
            # 닫기 버튼
            ttk.Button(
                detail_container,
                text="닫기",
                command=detail_window.destroy
            ).pack(pady=(20, 0))
        
        # 더블 클릭 이벤트 바인딩
        revision_tree.bind("<Double-1>", show_revision_details)
        
        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(revision_frame, orient="vertical", command=revision_tree.yview)
        revision_tree.configure(yscrollcommand=scrollbar.set)
        
        # 레이아웃
        revision_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 닫기 버튼
        ttk.Button(container, text="닫기", command=about_window.destroy).pack(pady=(0, 10))

    def show_user_guide(self, event=None):
        """사용자 가이드 다이얼로그 표시"""
        print("사용 설명서가 호출되었습니다. (F1 키 또는 메뉴 선택)")
        guide_window = tk.Toplevel(self.window)
        guide_window.title("DB 관리 도구 사용 설명서")
        guide_window.geometry("800x600")
        guide_window.resizable(True, True)  # 창 크기 조절 가능
        
        # 부모 창 중앙에 위치
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (800 // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (600 // 2)
        guide_window.geometry(f"800x600+{x}+{y}")
        
        # 스타일 설정
        style = ttk.Style()
        style.configure("Title.TLabel", font=('Helvetica', 16, 'bold'))
        style.configure("Heading.TLabel", font=('Helvetica', 12, 'bold'))
        style.configure("Content.TLabel", font=('Helvetica', 10))
        
        # 메인 프레임과 캔바스, 스크롤바 설정
        main_frame = ttk.Frame(guide_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 내용 구성
        sections = [
            {
                "title": "시작하기",
                "content": [
                    "1. 프로그램 실행 후 '파일' 메뉴에서 '폴더 열기' 선택",
                    "2. DB Editor에서 Export한 .txt 파일이 있는 폴더 선택",
                    "3. 최대 6개의 DB 파일들을 선택하여 비교 분석 실행"
                ]
            },
            {
                "title": "주요 기능",
                "content": [
                    "• DB 파일 비교 분석",
                    "  - 여러 DB 파일의 내용을 자동으로 비교",
                    "  - 차이점 자동 감지 및 하이라이트",
                    "  - 상세 비교 결과 제공",
                    "",
                    "• QC 검수 기능 (추가 예정)",
                    "  - 설정된 기준에 따른 자동 검증",
                    "  - 오류 항목 자동 감지",
                    "  - 검수 결과 리포트 생성"
                ]
            },
            {
                "title": "단축키",
                "content": [
                    "• Ctrl + O : 폴더 열기",
                    "• Ctrl + Q : 프로그램 종료",
                    "• F1 : 도움말 열기"
                ]
            },
            {
                "title": "자주 묻는 질문",
                "content": [
                    "Q: 지원하는 파일 형식은 무엇인가요?",
                    "A: DB Editor에서 Export한 .txt 파일을 지원합니다.",
                    "",
                    "Q: 한 번에 몇 개의 파일을 비교할 수 있나요?",
                    "A: 최대 6개의 파일을 동시에 비교할 수 있습니다.",
                    ""
                ]
            }
        ]
        
        # 제목
        ttk.Label(
            scrollable_frame,
            text="DB 관리 프로그램 사용 설명서",
            style="Title.TLabel"
        ).pack(pady=(0, 20))
        
        # 섹션별 내용 추가
        for section in sections:
            # 섹션 제목
            ttk.Label(
                scrollable_frame,
                text=section["title"],
                style="Heading.TLabel"
            ).pack(anchor="w", pady=(15, 5))
            
            # 섹션 내용
            for line in section["content"]:
                ttk.Label(
                    scrollable_frame,
                    text=line,
                    style="Content.TLabel",
                    wraplength=700,
                    justify="left"
                ).pack(anchor="w", padx=(20, 0))
        
        # 레이아웃 설정
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_menu(self):
        """메뉴바를 생성합니다."""
        menubar = tk.Menu(self.window)
        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="폴더 열기 (Ctrl+O)", command=self.load_folder)
        file_menu.add_separator()
        file_menu.add_command(label="보고서 내보내기", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.window.quit)
        menubar.add_cascade(label="파일", menu=file_menu)
        # 도구 메뉴
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="👤 사용자 모드 전환", command=self.toggle_maint_mode)

        menubar.add_cascade(label="도구", menu=tools_menu)
        # 도움말 메뉴
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="사용 설명서 (F1)", command=self.show_user_guide)
        help_menu.add_separator()
        help_menu.add_command(label="프로그램 정보", command=self.show_about)
        menubar.add_cascade(label="도움말", menu=help_menu)
        self.window.config(menu=menubar)

    def update_log(self, message):
        """로그 표시 영역에 메시지를 추가합니다."""
        self.log_text.configure(state=tk.NORMAL)
        from datetime import datetime
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def toggle_maint_mode(self):
        """유지보수 모드 토글"""
        if self.maint_mode:
            self.update_log("유지보수 모드가 비활성화되었습니다. (장비 생산 엔지니어 모드)")
            self.maint_mode = False
            self.status_bar.config(text="장비 생산 엔지니어 모드")
            self.disable_maint_features()
        else:
            password = simpledialog.askstring("유지보수 모드", "QC 엔지니어 비밀번호를 입력하세요:", show="*")
            if password is None:
                return
            from app.utils import verify_password
            if verify_password(password):
                self.enable_maint_features()
            else:
                messagebox.showerror("오류", "비밀번호가 일치하지 않습니다.")
        
        self.update_default_db_ui_state()




    


    def update_default_db_ui_state(self):
        """유지보수 모드에 따라 Default DB 관련 UI 요소들의 상태를 업데이트합니다."""
        if hasattr(self, 'show_default_candidates_cb'):
            if self.maint_mode:
                self.show_default_candidates_cb.configure(state="normal")
            else:
                if hasattr(self, 'show_default_candidates_var'):
                    self.show_default_candidates_var.set(False)
                self.show_default_candidates_cb.configure(state="disabled")
                self.update_comparison_view()
        
        self.update_comparison_context_menu_state()
        
        # 모든 탭 업데이트
        if hasattr(self, 'update_all_tabs'):
            # 탭 업데이트는 파일이 로드된 경우에만
            if self.merged_df is not None:
                self.update_all_tabs()

    def enable_maint_features(self):
        """유지보수 모드 활성화 - QC 엔지니어용 탭들을 추가합니다."""
        try:
            self.maint_mode = True
            self.update_log("🚀 유지보수 모드 활성화 시작...")
            
            # QC 검수 탭 생성 (Enhanced QC 사용)
            self.update_log("📋 Enhanced QC 검수 탭 생성 중...")
            self.create_qc_tabs_with_advanced_features()
            
            # Default DB 관리 탭 생성 (동기적 실행)
            self.update_log("🔧 Default DB 관리 탭 생성 중...")
            self.create_default_db_tab()
            
            # 상태 업데이트
            self.update_log("✅ QC 엔지니어 모드가 활성화되었습니다.")
            self.status_bar.config(text="QC 엔지니어 모드")
            
            # Performance 기능 확인 메시지
            self.update_log("🎯 Performance 기능이 활성화되었습니다!")
            self.update_log("   - Default DB 관리 탭에서 Performance 관리 버튼들을 확인하세요.")
            self.update_log("   - 트리뷰에서 가로 스크롤하여 🎯 Performance 컬럼을 확인하세요.")
            
        except Exception as e:
            error_msg = f"유지보수 모드 활성화 중 오류 발생: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)
            print(f"DEBUG - enable_maint_features error: {e}")
            import traceback
            traceback.print_exc()

    def create_comparison_tabs(self):
        """비교 관련 탭 생성 - 기본 기능만"""
        self.create_grid_view_tab()
        self.create_comparison_tab()
        self.create_diff_only_tab()
        # 보고서, 간단 비교, 고급 분석은 QC 탭으로 이동

    def create_qc_tabs_with_advanced_features(self):
        """QC 탭들을 고급 기능과 함께 생성"""
        try:
            # Enhanced QC 기능 사용 시도
            from app.enhanced_qc import add_enhanced_qc_functions_to_class
            add_enhanced_qc_functions_to_class(self.__class__)
            
            # QC 검수 탭 생성 (향상된 기능)
            if not hasattr(self, 'qc_check_frame') or self.qc_check_frame is None:
                self.create_enhanced_qc_tab()
                self.qc_check_frame = True  # 플래그 설정
                self.update_log("[QC] 향상된 QC 검수 탭이 생성되었습니다.")
            
            # QC 보고서 탭 생성
            self.create_report_tab_in_qc()
            
        except ImportError:
            # Enhanced QC를 사용할 수 없는 경우 기본 QC 기능 사용
            from app.qc import add_qc_check_functions_to_class
            add_qc_check_functions_to_class(self.__class__)
            
            if not hasattr(self, 'qc_check_frame') or self.qc_check_frame is None:
                self.create_qc_check_tab()
                self.qc_check_frame = True
                self.update_log("[QC] 기본 QC 검수 탭이 생성되었습니다.")
            
            self.create_report_tab_in_qc()
        
        except Exception as e:
            self.update_log(f"❌ QC 탭 생성 중 오류: {str(e)}")
            # 기본 QC 탭이라도 생성하려고 시도
            try:
                from app.qc import add_qc_check_functions_to_class
                add_qc_check_functions_to_class(self.__class__)
                if not hasattr(self, 'qc_check_frame') or self.qc_check_frame is None:
                    self.create_qc_check_tab()
                    self.qc_check_frame = True
            except Exception as fallback_error:
                self.update_log(f"❌ 기본 QC 탭 생성도 실패: {str(fallback_error)}")

    def goto_qc_check_tab(self):
        """QC 검수 탭으로 이동"""
        if not self.maint_mode:
            messagebox.showwarning("접근 제한", "QC 검수는 Maintenance Mode에서만 사용 가능합니다.")
            return
        
        try:
            # QC 탭이 있는지 확인하고 선택
            for i in range(self.main_notebook.index("end")):
                tab_text = self.main_notebook.tab(i, "text")
                if "QC" in tab_text or "검수" in tab_text:
                    self.main_notebook.select(i)
                    self.update_log("[Navigation] QC 검수 탭으로 이동했습니다.")
                    return
            
            # QC 탭이 없으면 생성
            self.update_log("[QC] QC 검수 탭이 없어서 새로 생성합니다.")
            self.create_qc_tabs_with_advanced_features()
            
            # 다시 탭 찾기 및 선택
            for i in range(self.main_notebook.index("end")):
                tab_text = self.main_notebook.tab(i, "text")
                if "QC" in tab_text or "검수" in tab_text:
                    self.main_notebook.select(i)
                    self.update_log("[Navigation] 새로 생성된 QC 검수 탭으로 이동했습니다.")
                    return
                    
        except Exception as e:
            error_msg = f"QC 검수 탭 이동 중 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)

    def perform_qc_check(self):
        """QC 검수 실행 - Enhanced QC 우선 사용"""
        try:
            self.update_log("🚀 QC 검수 실행 시작...")
            
            # Enhanced QC 기능 사용 시도
            if hasattr(self, 'perform_enhanced_qc_check'):
                self.update_log("🔧 Enhanced QC 기능 사용")
                return self.perform_enhanced_qc_check()
            elif hasattr(self, 'perform_qc_check_enhanced'):
                self.update_log("🔧 Enhanced QC 기능 사용 (대체)")
                return self.perform_qc_check_enhanced()
            else:
                # 기본 QC 기능 fallback
                self.update_log("📋 기본 QC 기능으로 fallback")
                messagebox.showinfo(
                    "QC 검수 실행", 
                    "Enhanced QC 기능을 사용할 수 없어 기본 QC 기능을 사용합니다.\n"
                    "더 자세한 검수를 위해서는 Enhanced QC 기능을 활성화해주세요."
                )
                # 여기에 기본 QC 로직 구현 가능
                return True
                
        except Exception as e:
            error_msg = f"QC 검수 실행 중 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)
            return False

    def create_report_tab_in_qc(self):
        """QC 노트북에 보고서 탭 생성"""
        if not hasattr(self, 'qc_notebook'):
            return
            
        report_tab = ttk.Frame(self.qc_notebook)
        self.qc_notebook.add(report_tab, text="보고서")
        
        control_frame = ttk.Frame(report_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        export_btn = ttk.Button(control_frame, text="보고서 내보내기", command=self.export_report)
        export_btn.pack(side=tk.RIGHT, padx=10)
        
        columns = ["Module", "Part", "ItemName"] + (self.file_names if self.file_names else [])
        self.qc_report_tree = ttk.Treeview(report_tab, columns=columns, show="headings", selectmode="browse")
        
        for col in columns:
            self.qc_report_tree.heading(col, text=col)
            self.qc_report_tree.column(col, width=120)
        
        v_scroll = ttk.Scrollbar(report_tab, orient="vertical", command=self.qc_report_tree.yview)
        h_scroll = ttk.Scrollbar(report_tab, orient="horizontal", command=self.qc_report_tree.xview)
        self.qc_report_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.qc_report_tree.pack(expand=True, fill=tk.BOTH)
        
        self.update_qc_report_view()

    def update_qc_report_view(self):
        """QC 보고서 뷰 업데이트"""
        if not hasattr(self, 'qc_report_tree'):
            return
            
        for item in self.qc_report_tree.get_children():
            self.qc_report_tree.delete(item)
            
        if self.merged_df is not None:
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            for (module, part, item_name), group in grouped:
                values = [module, part, item_name]
                for fname in self.file_names:
                    model_data = group[group["Model"] == fname]
                    if not model_data.empty:
                        values.append(str(model_data["ItemValue"].iloc[0]))
                    else:
                        values.append("-")
                self.qc_report_tree.insert("", "end", values=values)

    def create_diff_only_tab(self):
        """차이만 보기 탭 생성"""
        diff_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(diff_tab, text="🔍 차이점 분석")
        
        # 상단 정보 패널
        control_frame = ttk.Frame(diff_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.diff_only_count_label = ttk.Label(control_frame, text="값이 다른 항목: 0개")
        self.diff_only_count_label.pack(side=tk.RIGHT, padx=10)
        
        # 트리뷰 생성
        if self.file_names:
            columns = ["Module", "Part", "ItemName"] + self.file_names
        else:
            columns = ["Module", "Part", "ItemName"]
            
        self.diff_only_tree = ttk.Treeview(diff_tab, columns=columns, show="headings", selectmode="extended")
        
        # 헤딩 설정
        for col in columns:
            self.diff_only_tree.heading(col, text=col)
            if col in ["Module", "Part", "ItemName"]:
                self.diff_only_tree.column(col, width=120)
            else:
                self.diff_only_tree.column(col, width=150)
        
        # 스크롤바 추가
        v_scroll = ttk.Scrollbar(diff_tab, orient="vertical", command=self.diff_only_tree.yview)
        h_scroll = ttk.Scrollbar(diff_tab, orient="horizontal", command=self.diff_only_tree.xview)
        self.diff_only_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        
        # 위젯 배치
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.diff_only_tree.pack(expand=True, fill=tk.BOTH)
        
        # 차이점 데이터 업데이트
        self.update_diff_only_view()

    def update_diff_only_view(self):
        """차이점만 보기 탭 업데이트 - 하이라이트 제거"""
        if not hasattr(self, 'diff_only_tree'):
            return
            
        for item in self.diff_only_tree.get_children():
            self.diff_only_tree.delete(item)
        
        diff_count = 0
        if self.merged_df is not None:
            # 컬럼 업데이트
            columns = ["Module", "Part", "ItemName"] + self.file_names
            self.diff_only_tree["columns"] = columns
            
            for col in columns:
                self.diff_only_tree.heading(col, text=col)
                if col in ["Module", "Part", "ItemName"]:
                    self.diff_only_tree.column(col, width=120)
                else:
                    self.diff_only_tree.column(col, width=150)
            
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            
            for (module, part, item_name), group in grouped:
                # 각 파일별 값 추출
                file_values = {}
                for model in self.file_names:
                    model_data = group[group["Model"] == model]
                    if not model_data.empty:
                        file_values[model] = str(model_data["ItemValue"].iloc[0])
                    else:
                        file_values[model] = "-"
                
                # 차이점이 있는지 확인
                unique_values = set(v for v in file_values.values() if v != "-")
                if len(unique_values) > 1:
                    # 차이점이 있는 항목만 추가 (하이라이트 없이)
                    row_values = [module, part, item_name]
                    row_values.extend([file_values.get(model, "-") for model in self.file_names])
                    
                    self.diff_only_tree.insert("", "end", values=row_values)
                    diff_count += 1
        
        # 차이점 카운트 업데이트
        if hasattr(self, 'diff_only_count_label'):
            self.diff_only_count_label.config(text=f"값이 다른 항목: {diff_count}개")

    def create_report_tab(self):
        report_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(report_tab, text="보고서")
        control_frame = ttk.Frame(report_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        export_btn = ttk.Button(control_frame, text="보고서 내보내기", command=self.export_report)
        export_btn.pack(side=tk.RIGHT, padx=10)
        columns = ["Module", "Part", "ItemName"] + self.file_names
        self.report_tree = ttk.Treeview(report_tab, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=120)
        v_scroll = ttk.Scrollbar(report_tab, orient="vertical", command=self.report_tree.yview)
        h_scroll = ttk.Scrollbar(report_tab, orient="horizontal", command=self.report_tree.xview)
        self.report_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.report_tree.pack(expand=True, fill=tk.BOTH)
        self.update_report_view()

    def update_report_view(self):
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        if self.merged_df is not None:
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            for (module, part, item_name), group in grouped:
                values = [module, part, item_name]
                for fname in self.file_names:
                    values.append(group[fname].iloc[0] if fname in group else "")
                self.report_tree.insert("", "end", values=values)

    def export_report(self):
        """보고서 내보내기 기능"""
        try:
            columns = ["Module", "Part", "ItemName"]
            return self.file_service.export_tree_data(
                self.report_tree, columns, self.file_names, "보고서 내보내기"
            )
        except Exception as e:
            messagebox.showerror("오류", f"보고서 내보내기 중 오류 발생: {str(e)}")


    def load_folder(self, event=None):
        # 파일 확장자 필터 설정
        filetypes = [
            ("DB 파일", "*.txt;*.db;*.csv"),
            ("텍스트 파일", "*.txt"),
            ("CSV 파일", "*.csv"),
            ("DB 파일", "*.db"),
            ("모든 파일", "*.*")
        ]
        files = filedialog.askopenfilenames(
            title="📂 DB 파일을 선택하세요",
            filetypes=filetypes,
            initialdir=self.folder_path if self.folder_path else None
        )
        if not files:
            self.status_bar.config(text="파일 선택이 취소되었습니다.")
            return
        loading_dialog = LoadingDialog(self.window)
        try:
            import pandas as pd
            import os
            import sqlite3
            df_list = []
            self.file_names = []
            # 🆕 QC 파일 선택을 위한 uploaded_files 딕셔너리 생성
            self.uploaded_files = {}
            total_files = len(files)
            loading_dialog.update_progress(0, "파일 로딩 준비 중...")
            for idx, file in enumerate(files, 1):
                try:
                    progress = (idx / total_files) * 70
                    loading_dialog.update_progress(
                        progress,
                        f"파일 로딩 중... ({idx}/{total_files})"
                    )
                    file_name = os.path.basename(file)
                    base_name = os.path.splitext(file_name)[0]
                    ext = os.path.splitext(file_name)[1].lower()
                    if ext == '.txt':
                        df = pd.read_csv(file, delimiter="\t", dtype=str)
                        # 텍스트 파일의 필수 컬럼 확인 및 추가
                        required_columns = ['Module', 'Part', 'ItemName', 'ItemType', 'ItemValue', 'ItemDescription']
                        if all(col in df.columns for col in required_columns):
                            # 표준 텍스트 파일 형식: ItemType 정보 보존
                            df = df[required_columns].copy()
                        else:
                            # 호환성을 위한 fallback: 기본 컬럼명 추가
                            if 'ItemType' not in df.columns:
                                df['ItemType'] = 'double'  # 기본값
                            if 'ItemDescription' not in df.columns:
                                df['ItemDescription'] = ''
                    elif ext == '.csv':
                        df = pd.read_csv(file, dtype=str)
                        # CSV 파일에서도 ItemType 보존 시도
                        if 'ItemType' not in df.columns:
                            df['ItemType'] = 'double'  # 기본값
                    elif ext == '.db':
                        conn = sqlite3.connect(file)
                        df = pd.read_sql("SELECT * FROM main_table", conn)
                        conn.close()
                        # DB 파일에서도 ItemType 보존 시도
                        if 'ItemType' not in df.columns:
                            df['ItemType'] = 'double'  # 기본값
                    
                    df["Model"] = base_name
                    df_list.append(df)
                    self.file_names.append(base_name)
                    # 🆕 QC 파일 선택을 위해 파일 정보 저장
                    self.uploaded_files[file_name] = file
                except Exception as e:
                    messagebox.showwarning(
                        "경고", 
                        f"'{file_name}' 파일 로드 중 오류 발생:\n{str(e)}"
                    )
            if df_list:
                self.folder_path = os.path.dirname(files[0])
                loading_dialog.update_progress(75, "데이터 병합 중...")
                self.merged_df = pd.concat(df_list, ignore_index=True)
                loading_dialog.update_progress(85, "화면 업데이트 중...")
                self.update_all_tabs()
                loading_dialog.update_progress(100, "완료!")
                loading_dialog.close()
                
                # 🆕 QC 파일 선택 가능 상태 로그 추가
                self.update_log(f"[파일 로드] {len(self.uploaded_files)}개 파일이 QC 검수 대상으로 등록되었습니다.")
                
                messagebox.showinfo(
                    "로드 완료",
                    f"총 {len(df_list)}개의 DB 파일을 성공적으로 로드했습니다.\n"
                    f"• 폴더: {self.folder_path}\n"
                    f"• 파일: {', '.join(self.file_names)}\n"
                    f"• QC 검수 파일 선택 가능: {len(self.uploaded_files)}개"
                )
                self.status_bar.config(
                    text=f"총 {len(df_list)}개의 DB 파일이 로드되었습니다. "
                         f"(폴더: {os.path.basename(self.folder_path)})"
                )
            else:
                loading_dialog.close()
                messagebox.showerror("오류", "파일을 로드할 수 없습니다.")
                self.status_bar.config(text="파일 로드 실패")
        except Exception as e:
            loading_dialog.close()
            messagebox.showerror("오류", f"예기치 않은 오류가 발생했습니다:\n{str(e)}")

    def update_all_tabs(self):
        # 기존 탭 제거
        for tab in self.comparison_notebook.winfo_children():
            tab.destroy()
        # 탭 다시 생성
        self.create_comparison_tabs()
        
        # 격자뷰와 차이점뷰 업데이트
        if hasattr(self, 'update_grid_view'):
            self.update_grid_view()
        if hasattr(self, 'update_diff_only_view'):
            self.update_diff_only_view()
        
        # QC 보고서 뷰도 업데이트 (유지보수 모드인 경우)
        if self.maint_mode and hasattr(self, 'update_qc_report_view'):
            self.update_qc_report_view()

    def create_grid_view_tab(self):
        """격자뷰 탭 생성 - 트리뷰 구조"""
        grid_frame = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(grid_frame, text="📊 메인 비교")
        
        # 상단 정보 패널
        info_frame = ttk.Frame(grid_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 통계 정보 라벨들
        self.grid_total_label = ttk.Label(info_frame, text="총 파라미터: 0")
        self.grid_total_label.pack(side=tk.LEFT, padx=10)
        
        self.grid_modules_label = ttk.Label(info_frame, text="모듈 수: 0")
        self.grid_modules_label.pack(side=tk.LEFT, padx=10)
        
        self.grid_parts_label = ttk.Label(info_frame, text="파트 수: 0")
        self.grid_parts_label.pack(side=tk.LEFT, padx=10)
        
        # 차이점 개수 라벨 추가
        self.grid_diff_label = ttk.Label(info_frame, text="값이 다른 항목: 0", foreground="red")
        self.grid_diff_label.pack(side=tk.RIGHT, padx=10)
        

        
        # 메인 트리뷰 생성 (계층 구조)
        self.grid_tree = ttk.Treeview(grid_frame, selectmode="extended")
        
        # 동적 컬럼 설정
        if self.file_names:
            columns = tuple(self.file_names)
        else:
            columns = ("값",)
            
        self.grid_tree["columns"] = columns
        
        # 첫 번째 컬럼 (트리 구조용)
        self.grid_tree.heading("#0", text="구조", anchor="w")
        self.grid_tree.column("#0", width=250, anchor="w")
        
        # 파일별 값 컬럼들
        for col in columns:
            self.grid_tree.heading(col, text=col, anchor="center")
            self.grid_tree.column(col, width=150, anchor="center")
        
        # 스크롤바 추가
        v_scroll = ttk.Scrollbar(grid_frame, orient="vertical", command=self.grid_tree.yview)
        h_scroll = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.grid_tree.xview)
        self.grid_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        
        # 위젯 배치
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.grid_tree.pack(expand=True, fill=tk.BOTH)
        
        # 격자뷰 데이터 업데이트
        self.update_grid_view()

    def update_grid_view(self):
        """격자뷰 데이터 업데이트 - 트리뷰 구조"""
        if not hasattr(self, 'grid_tree'):
            return
            
        # 기존 데이터 삭제
        for item in self.grid_tree.get_children():
            self.grid_tree.delete(item)
        
        if self.merged_df is None or self.merged_df.empty:
            # 통계 정보 초기화
            if hasattr(self, 'grid_total_label'):
                self.grid_total_label.config(text="총 파라미터: 0개")
                self.grid_modules_label.config(text="모듈 수: 0개") 
                self.grid_parts_label.config(text="파트 수: 0개")
            return
        
        # 동적 컬럼 업데이트
        columns = tuple(self.file_names) if self.file_names else ("값",)
        self.grid_tree["columns"] = columns
        
        # 컬럼 헤딩 업데이트
        for col in columns:
            self.grid_tree.heading(col, text=col, anchor="center")
            self.grid_tree.column(col, width=150, anchor="center")
        
        # 계층별 스타일 태그 설정
        # 모듈 레벨 - 가장 크고 굵게 (기본 파란색)
        self.grid_tree.tag_configure("module", 
                                    font=("Arial", 11, "bold"), 
                                    background="#F5F5F5", 
                                    foreground="#1565C0")
        
        # 모듈 레벨 - 차이 있음 (빨간색 강조)
        self.grid_tree.tag_configure("module_diff", 
                                    font=("Arial", 11, "bold"), 
                                    background="#F5F5F5", 
                                    foreground="#D32F2F")
        
        # 파트 레벨 - 중간 크기, 볼드
        self.grid_tree.tag_configure("part", 
                                    font=("Arial", 10, "bold"), 
                                    background="#FAFAFA", 
                                    foreground="#424242")
        
        # 파트 레벨 - 모든 값 동일 (초록색)
        self.grid_tree.tag_configure("part_clean", 
                                    font=("Arial", 10, "bold"), 
                                    background="#FAFAFA", 
                                    foreground="#2E7D32")
        
        # 파트 레벨 - 차이 있음 (빨간색 강조)
        self.grid_tree.tag_configure("part_diff", 
                                    font=("Arial", 10, "bold"), 
                                    background="#FAFAFA", 
                                    foreground="#D32F2F")
        

        
        # 파라미터 레벨 - 기본 크기
        self.grid_tree.tag_configure("parameter_same", 
                                    font=("Arial", 9), 
                                    background="white", 
                                    foreground="black")
        
        # 차이점이 있는 파라미터 - 전체 목록 탭과 동일한 색상
        self.grid_tree.tag_configure("parameter_different", 
                                    font=("Arial", 9), 
                                    background="#FFECB3", 
                                    foreground="#E65100")
        
        # 계층 구조 데이터 구성
        modules_data = {}
        total_params = 0
        diff_count = 0
        
        grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
        
        for (module, part, item_name), group in grouped:
            if module not in modules_data:
                modules_data[module] = {}
            if part not in modules_data[module]:
                modules_data[module][part] = {}
            
            # 각 파일별 값 수집
            values = []
            for model in self.file_names:
                model_data = group[group["Model"] == model]
                if not model_data.empty:
                    values.append(str(model_data["ItemValue"].iloc[0]))
                else:
                    values.append("-")
            
            # 값 차이 확인 (빈 값 제외)
            non_empty_values = [v for v in values if v != "-"]
            has_difference = len(set(non_empty_values)) > 1 if len(non_empty_values) > 1 else False
            
            modules_data[module][part][item_name] = {
                "values": values,
                "has_difference": has_difference
            }
            total_params += 1
            if has_difference:
                diff_count += 1
        
        # 트리뷰에 계층 구조로 데이터 추가
        for module_name in sorted(modules_data.keys()):
            # 모듈 레벨 통계 계산
            module_total = sum(len(modules_data[module_name][part]) for part in modules_data[module_name])
            module_diff = sum(1 for part in modules_data[module_name] 
                            for item in modules_data[module_name][part] 
                            if modules_data[module_name][part][item]["has_difference"])
            
            # 모듈 표시 - 파란색 통일
            if module_diff == 0:
                module_text = f"📁 {module_name} ({module_total})"
            else:
                module_text = f"📁 {module_name} ({module_total}) Diff: {module_diff}"
            module_tag = "module"
            
            # 모듈 노드 추가
            module_node = self.grid_tree.insert("", "end", 
                                               text=module_text, 
                                               values=[""] * len(columns), 
                                               open=True,
                                               tags=(module_tag,))
            
            for part_name in sorted(modules_data[module_name].keys()):
                # 파트 레벨 통계 계산
                part_total = len(modules_data[module_name][part_name])
                part_diff = sum(1 for item in modules_data[module_name][part_name] 
                              if modules_data[module_name][part_name][item]["has_difference"])
                
                # 파트 표시 - 차이가 없으면 초록색, 있으면 회색
                if part_diff == 0:
                    part_text = f"📂 {part_name} ({part_total})"
                    part_tag = "part_clean"
                else:
                    part_text = f"📂 {part_name} ({part_total}) Diff: {part_diff}"
                    part_tag = "part_diff"
                
                # 파트 노드 추가
                part_node = self.grid_tree.insert(module_node, "end", 
                                                 text=part_text, 
                                                 values=[""] * len(columns), 
                                                 open=True,
                                                 tags=(part_tag,))
                
                for item_name in sorted(modules_data[module_name][part_name].keys()):
                    # 파라미터 노드 추가 - 기본 크기, 차이점에 따라 색상 구분
                    item_data = modules_data[module_name][part_name][item_name]
                    values = item_data["values"]
                    has_difference = item_data["has_difference"]
                    
                    # 태그 선택
                    tag = "parameter_different" if has_difference else "parameter_same"
                    
                    self.grid_tree.insert(part_node, "end", 
                                        text=item_name, 
                                        values=values, 
                                        tags=(tag,))
        
        # 통계 정보 업데이트
        if hasattr(self, 'grid_total_label'):
            self.grid_total_label.config(text=f"총 파라미터: {total_params}")
            self.grid_modules_label.config(text=f"모듈 수: {len(modules_data)}")
            
            total_parts = sum(len(parts) for parts in modules_data.values())
            self.grid_parts_label.config(text=f"파트 수: {total_parts}")
            
            # 차이점 개수도 표시
            if hasattr(self, 'grid_diff_label'):
                self.grid_diff_label.config(text=f"값이 다른 항목: {diff_count}")

    def create_comparison_tab(self):
        comparison_frame = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(comparison_frame, text="📋 전체 목록")
        style = ttk.Style()
        style.configure("Custom.Treeview", rowheight=22)
        
        # 상단 검색 및 제어 패널
        top_frame = ttk.Frame(comparison_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 검색 기능 추가 (좌측)
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(search_frame, text="🔎 Search:", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        self.search_clear_btn = ttk.Button(search_frame, text="Clear", command=self.clear_search, width=8)
        self.search_clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 검색 결과 정보
        self.search_result_label = ttk.Label(search_frame, text="", foreground="#1976D2", font=('Segoe UI', 8))
        self.search_result_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 필터 컨트롤을 같은 행에 추가
        # 필터 컨트롤 영역
        self.comparison_advanced_filter_visible = tk.BooleanVar(value=False)
        
        control_frame = ttk.Frame(search_frame)
        control_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 결과 표시 레이블
        self.comparison_filter_result_label = ttk.Label(control_frame, text="", foreground="#1976D2", font=('Segoe UI', 8))
        self.comparison_filter_result_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Advanced Filter 토글 버튼
        self.comparison_toggle_advanced_btn = ttk.Button(
            control_frame, 
            text="▼ Filters", 
            command=self._toggle_comparison_advanced_filters
        )
        self.comparison_toggle_advanced_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Reset 버튼
        filter_reset_btn = ttk.Button(control_frame, text="Reset", command=self._reset_comparison_filters)
        filter_reset_btn.pack(side=tk.LEFT)
        
        # 고급 필터 패널 생성
        self._create_comparison_filter_panel(comparison_frame)
        
        control_frame = ttk.Frame(comparison_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        if self.maint_mode:
            self.select_all_var = tk.BooleanVar(value=False)
            self.select_all_cb = ttk.Checkbutton(
                control_frame,
                text="모두 선택",
                variable=self.select_all_var,
                command=self.toggle_select_all_checkboxes
            )
            self.select_all_cb.pack(side=tk.LEFT, padx=5)
        if self.maint_mode:
            self.selected_count_label = ttk.Label(control_frame, text="선택된 항목: 0개")
            self.selected_count_label.pack(side=tk.RIGHT, padx=10)
            self.send_to_default_btn = ttk.Button(
                control_frame,
                text="Default DB로 전송",
                command=self.add_to_default_db
            )
            self.send_to_default_btn.pack(side=tk.RIGHT, padx=10)
        else:
            self.diff_count_label = ttk.Label(control_frame, text="값이 다른 항목: 0개")
            self.diff_count_label.pack(side=tk.RIGHT, padx=10)
        self.item_checkboxes = {}
        if self.maint_mode:
            columns = ["Checkbox", "Module", "Part", "ItemName"] + self.file_names
        else:
            columns = ["Module", "Part", "ItemName"] + self.file_names
        self.comparison_tree = ttk.Treeview(comparison_frame, selectmode="extended", style="Custom.Treeview")
        self.comparison_tree["columns"] = columns
        self.comparison_tree.heading("#0", text="", anchor="w")
        self.comparison_tree.column("#0", width=0, stretch=False)
        col_offset = 0
        if self.maint_mode:
            self.comparison_tree.heading("Checkbox", text="선택")
            self.comparison_tree.column("Checkbox", width=50, anchor="center")
            col_offset = 1
        for idx, col in enumerate(["Module", "Part", "ItemName"]):
            self.comparison_tree.heading(col, text=col, anchor="w")
            self.comparison_tree.column(col, width=100)
        for model in self.file_names:
            self.comparison_tree.heading(model, text=model, anchor="w")
            self.comparison_tree.column(model, width=150)
        v_scroll = ttk.Scrollbar(comparison_frame, orient="vertical", 
                                command=self.comparison_tree.yview)
        h_scroll = ttk.Scrollbar(comparison_frame, orient="horizontal", 
                                command=self.comparison_tree.xview)
        self.comparison_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.comparison_tree.pack(expand=True, fill=tk.BOTH)
        self.comparison_tree.bind("<<TreeviewSelect>>", self.update_selected_count)
        self.create_comparison_context_menu()
        if not self.maint_mode:
            self.update_comparison_context_menu_state()
        self.update_comparison_view()

    def _create_comparison_filter_panel(self, parent_frame):
        """전체 목록 탭 필터 패널 생성 - 고급 필터만 생성"""
        try:
            # 메인 필터 컨테이너 프레임 (parent_frame에 직접 배치)
            self.comparison_main_filter_container = ttk.Frame(parent_frame)
            self.comparison_main_filter_container.pack(fill=tk.X, pady=(0, 5), padx=10)
            
            # 구분선 추가
            separator = ttk.Separator(self.comparison_main_filter_container, orient='horizontal')
            separator.pack(fill=tk.X, pady=(5, 8))
            
            # 고급 필터 패널 (메인 컨테이너 내부에 배치, 처음에는 숨김)
            self.comparison_advanced_filter_frame = ttk.Frame(self.comparison_main_filter_container)
            
            # 고급 필터 내용 생성 (아직 보이지 않음)
            self._create_comparison_advanced_filters()
            
            # 초기 상태는 숨겨진 상태로 설정
            print("Filter panel created - advanced filter hidden by default")
            
        except Exception as e:
            print(f"Comparison filter panel error: {e}")
            import traceback
            traceback.print_exc()

    def _create_comparison_advanced_filters(self):
        """전체 목록 탭 고급 필터 생성 - Module, Part만 포함 (Data Type 제외)"""
        try:
            # 구분선
            filter_separator = ttk.Separator(self.comparison_advanced_filter_frame, orient='horizontal')
            filter_separator.pack(fill=tk.X, pady=(5, 8))
            
            # 필터 행 - 엔지니어 스타일 단일 행 레이아웃
            filters_row = ttk.Frame(self.comparison_advanced_filter_frame)
            filters_row.pack(fill=tk.X, pady=(0, 8))
            
            # Module Filter
            module_frame = ttk.Frame(filters_row)
            module_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            ttk.Label(module_frame, text="Module:", font=('Segoe UI', 8)).pack(anchor='w')
            self.comparison_module_filter_var = tk.StringVar()
            self.comparison_module_filter_combo = ttk.Combobox(module_frame, textvariable=self.comparison_module_filter_var, 
                                                      state="readonly", width=12, font=('Segoe UI', 8))
            self.comparison_module_filter_combo.pack()
            self.comparison_module_filter_combo.bind('<<ComboboxSelected>>', self._apply_comparison_filters)
            
            # Part Filter
            part_frame = ttk.Frame(filters_row)
            part_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            ttk.Label(part_frame, text="Part:", font=('Segoe UI', 8)).pack(anchor='w')
            self.comparison_part_filter_var = tk.StringVar()
            self.comparison_part_filter_combo = ttk.Combobox(part_frame, textvariable=self.comparison_part_filter_var, 
                                                    state="readonly", width=12, font=('Segoe UI', 8))
            self.comparison_part_filter_combo.pack()
            self.comparison_part_filter_combo.bind('<<ComboboxSelected>>', self._apply_comparison_filters)
            
            # 엔지니어 관리 버튼들 (QC 모드에서만 표시)
            # 엔지니어 기능 (비교 통계 및 데이터 내보내기) 제거됨
            
        except Exception as e:
            print(f"Comparison advanced filters error: {e}")

    def _toggle_comparison_advanced_filters(self):
        """전체 목록 탭 고급 필터 토글"""
        try:
            print(f"Toggle called - Current state: {self.comparison_advanced_filter_visible.get()}")
            
            if self.comparison_advanced_filter_visible.get():
                # 현재 보이는 상태 → 숨기기
                print("Hiding advanced filters")
                self.comparison_advanced_filter_frame.pack_forget()
                self.comparison_toggle_advanced_btn.config(text="▼ Filters")
                self.comparison_advanced_filter_visible.set(False)
            else:
                # 현재 숨겨진 상태 → 보이기
                print("Showing advanced filters")
                self.comparison_advanced_filter_frame.pack(fill=tk.X, pady=(0, 5))
                self.comparison_toggle_advanced_btn.config(text="▲ Filters")
                self.comparison_advanced_filter_visible.set(True)
                
            # UI 업데이트 강제 실행
            if hasattr(self, 'comparison_main_filter_container'):
                self.comparison_main_filter_container.update_idletasks()
            if hasattr(self, 'window'):
                self.window.update_idletasks()
            
            print(f"Toggle complete - New state: {self.comparison_advanced_filter_visible.get()}")
            
        except Exception as e:
            print(f"Filter toggle error: {e}")
            import traceback
            traceback.print_exc()

    def _apply_comparison_filters(self, *args):
        """전체 목록 탭 필터 적용"""
        try:
            # 기존 검색 필터와 함께 Module, Part 필터 적용
            self.on_search_changed()
            
        except Exception as e:
            print(f"Comparison filters apply error: {e}")

    def _reset_comparison_filters(self):
        """전체 목록 탭 모든 필터 초기화"""
        try:
            # 검색 초기화
            if hasattr(self, 'search_var'):
                self.search_var.set("")
            
            # 필터 초기화
            if hasattr(self, 'comparison_module_filter_var'):
                self.comparison_module_filter_var.set("All")
            if hasattr(self, 'comparison_part_filter_var'):
                self.comparison_part_filter_var.set("All")
            
            # 필터 적용
            self._apply_comparison_filters()
            
        except Exception as e:
            print(f"Comparison filters reset error: {e}")

    def _update_comparison_filter_options(self):
        """전체 목록 탭 필터 옵션 업데이트"""
        try:
            if not hasattr(self, 'merged_df') or self.merged_df is None:
                return
                
            # Module 옵션 업데이트
            if 'Module' in self.merged_df.columns:
                modules = sorted(self.merged_df['Module'].dropna().unique())
                module_values = ["All"] + list(modules)
                if hasattr(self, 'comparison_module_filter_combo'):
                    self.comparison_module_filter_combo['values'] = module_values
                    if not self.comparison_module_filter_var.get():
                        self.comparison_module_filter_var.set("All")
            
            # Part 옵션 업데이트
            if 'Part' in self.merged_df.columns:
                parts = sorted(self.merged_df['Part'].dropna().unique())
                part_values = ["All"] + list(parts)
                if hasattr(self, 'comparison_part_filter_combo'):
                    self.comparison_part_filter_combo['values'] = part_values
                    if not self.comparison_part_filter_var.get():
                        self.comparison_part_filter_var.set("All")
                        
        except Exception as e:
            print(f"Comparison filter options update error: {e}")


    def add_to_default_db(self):
        """체크된 항목들을 Default DB로 전송 - 중복도 기반 통계 분석"""
        if not self.maint_mode:
            messagebox.showwarning("권한 없음", "유지보수 모드에서만 Default DB에 항목을 추가할 수 있습니다.")
            return

        # 체크된 항목들 수집
        selected_items = []
        if any(self.item_checkboxes.values()):
            # 체크박스가 하나라도 선택된 경우
            for item_key, is_checked in self.item_checkboxes.items():
                if is_checked:
                    # item_key에서 module, part, item_name 분리
                    parts = item_key.split('_')
                    if len(parts) >= 3:
                        module, part, item_name = parts[0], parts[1], '_'.join(parts[2:])
                        
                        # 트리뷰에서 해당 항목 찾기
                        for child_id in self.comparison_tree.get_children():
                            values = self.comparison_tree.item(child_id, 'values')
                            if len(values) >= 4 and values[1] == module and values[2] == part and values[3] == item_name:
                                selected_items.append(child_id)
                                break
        else:
            # 체크박스가 선택되지 않은 경우, 트리뷰에서 직접 선택된 항목 사용
            selected_items = self.comparison_tree.selection()

        if not selected_items:
            messagebox.showwarning("선택 필요", "Default DB에 추가할 항목을 먼저 선택해주세요.")
            return

        # 장비 유형 선택 또는 새로 생성
        equipment_types = self.db_schema.get_equipment_types()
        type_names = [f"{name} (ID: {type_id})" for type_id, name, _ in equipment_types]
        
        # 고급 선택 다이얼로그
        dlg = tk.Toplevel(self.window)
        dlg.title("Default DB 추가 - 통계 기반 기준값 설정")
        dlg.geometry("700x600")
        dlg.transient(self.window)
        dlg.grab_set()
        
        # 부모 창 중앙에 배치
        try:
            from app.utils import center_dialog_on_parent
            center_dialog_on_parent(dlg, self.window)
        except ImportError:
            # fallback: 화면 중앙에 배치
            dlg.geometry("+%d+%d" % (self.window.winfo_rootx() + 50, self.window.winfo_rooty() + 50))
        
        # 장비 유형 선택 프레임
        type_frame = ttk.LabelFrame(dlg, text="🔧 장비 유형 선택", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(type_frame, text="기존 장비 유형:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        selected_type = tk.StringVar()
        combo = ttk.Combobox(type_frame, textvariable=selected_type, values=type_names, state="readonly", width=40)
        combo.grid(row=0, column=1, padx=5, pady=5)
        if type_names:
            combo.set(type_names[0])
        
        ttk.Label(type_frame, text="또는 새 장비 유형:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        new_type_var = tk.StringVar()
        new_type_entry = ttk.Entry(type_frame, textvariable=new_type_var, width=40)
        new_type_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 통계 분석 설정
        stats_frame = ttk.LabelFrame(dlg, text="📊 통계 분석 설정 (중복도 기반 기준값 도출)", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        analyze_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(stats_frame, text="✓ 값의 중복도 분석 수행 (권장)", variable=analyze_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Label(stats_frame, text="신뢰도 임계값:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        confidence_var = tk.DoubleVar(value=50.0)
        confidence_scale = ttk.Scale(stats_frame, from_=0, to=100, variable=confidence_var, orient="horizontal", length=200)
        confidence_scale.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        confidence_label = ttk.Label(stats_frame, text="50.0% (과반수 이상)")
        confidence_label.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        def update_confidence_label(event=None):
            val = confidence_var.get()
            if val >= 80:
                desc = "매우 높음"
            elif val >= 60:
                desc = "높음" 
            elif val >= 40:
                desc = "보통"
            else:
                desc = "낮음"
            confidence_label.config(text=f"{val:.1f}% ({desc})")
        confidence_scale.configure(command=update_confidence_label)
        
        # 미리보기 영역
        preview_frame = ttk.LabelFrame(dlg, text="📋 추가될 항목 미리보기 및 통계", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        preview_text = tk.Text(preview_frame, height=12, wrap=tk.WORD, font=("Consolas", 9))
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_text.yview)
        preview_text.configure(yscrollcommand=preview_scroll.set)
        
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        preview_text.pack(fill=tk.BOTH, expand=True)
        
        def update_preview():
            """미리보기 업데이트"""
            preview_text.delete(1.0, tk.END)
            
            if not analyze_var.get():
                preview_text.insert(tk.END, f"📋 단순 추가 모드\n")
                preview_text.insert(tk.END, f"총 {len(selected_items)}개 항목을 첫 번째 파일 값으로 추가합니다.\n\n")
                for item_id in selected_items[:10]:  # 처음 10개만 미리보기
                    item_values = self.comparison_tree.item(item_id, "values")
                    col_offset = 1 if self.maint_mode else 0
                    module, part, item_name = item_values[col_offset], item_values[col_offset+1], item_values[col_offset+2]
                    value = item_values[col_offset+3]
                    preview_text.insert(tk.END, f"  • {item_name}: {value}\n")
                if len(selected_items) > 10:
                    preview_text.insert(tk.END, f"  ... 및 {len(selected_items)-10}개 더\n")
                return
            
            # 통계 분석 수행
            try:
                stats_analysis = self.analyze_parameter_statistics(selected_items)
                
                preview_text.insert(tk.END, f"📊 === 통계 분석 결과 ===\n")
                preview_text.insert(tk.END, f"분석된 파라미터: {len(stats_analysis)}개\n")
                preview_text.insert(tk.END, f"전체 파일 수: {len(self.file_names)}개\n")
                preview_text.insert(tk.END, f"파일 목록: {', '.join(self.file_names)}\n\n")
                
                high_confidence = 0
                medium_confidence = 0
                low_confidence = 0
                threshold = confidence_var.get() / 100.0
                
                for param_name, stats in stats_analysis.items():
                    confidence = stats['confidence_score']
                    if confidence >= threshold:
                        high_confidence += 1
                        status = "✅ 추가됨"
                        color_tag = "high"
                    elif confidence >= 0.3:
                        medium_confidence += 1
                        status = "⚠️ 중간 신뢰도"
                        color_tag = "medium"
                    else:
                        low_confidence += 1
                        status = "❌ 낮은 신뢰도"
                        color_tag = "low"
                    
                    # 값 분포 정보
                    value_info = f"{stats['most_common_value']}"
                    if stats['unique_values'] > 1:
                        value_info += f" (총 {stats['unique_values']}가지 값)"
                    
                    preview_text.insert(tk.END, f"{param_name}:\n")
                    preview_text.insert(tk.END, f"  기준값: {value_info}\n")
                    preview_text.insert(tk.END, f"  신뢰도: {confidence*100:.1f}% ({stats['occurrence_count']}/{stats['total_files']})\n")
                    
                    if stats['is_numeric']:
                        preview_text.insert(tk.END, f"  수치범위: {stats['min']:.3f} ~ {stats['max']:.3f}\n")
                        preview_text.insert(tk.END, f"  평균±표준편차: {stats['mean']:.3f} ± {stats['std']:.3f}\n")
                    
                    preview_text.insert(tk.END, f"  상태: {status}\n\n")
                
                preview_text.insert(tk.END, f"📈 === 요약 ===\n")
                preview_text.insert(tk.END, f"추가될 항목 (신뢰도 ≥{confidence_var.get():.1f}%): {high_confidence}개\n")
                preview_text.insert(tk.END, f"중간 신뢰도 (30-{confidence_var.get():.1f}%): {medium_confidence}개\n") 
                preview_text.insert(tk.END, f"제외될 항목 (<30%): {low_confidence}개\n")
                
            except Exception as e:
                preview_text.insert(tk.END, f"❌ 통계 분석 오류: {str(e)}")
        
        # 버튼 프레임
        button_frame = ttk.Frame(dlg)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="🔄 미리보기 업데이트", command=update_preview).pack(side=tk.LEFT, padx=5)
        
        def show_duplicate_check():
            """중복 검사 다이얼로그 표시"""
            duplicate_analysis = self.get_duplicate_analysis(selected_items)
            self.show_duplicate_analysis_dialog(duplicate_analysis)
        
        ttk.Button(button_frame, text="🔍 중복 검사", command=show_duplicate_check).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ 취소", command=dlg.destroy).pack(side=tk.RIGHT, padx=5)
        
        def on_confirm():
            # 장비 유형 결정
            if new_type_var.get().strip():
                # 새 장비 유형 생성
                type_name = new_type_var.get().strip()
                type_id = self.db_schema.add_equipment_type(type_name, f"다중 모델 비교를 통해 자동 생성된 장비 유형")
                self.update_log(f"새 장비 유형 생성: {type_name} (ID: {type_id})")
                
                self.db_schema.log_change_history(
                    "add", "equipment_type", type_name, "", 
                    f"multi-model comparison based", "admin"
                )
                
            elif selected_type.get():
                # 기존 장비 유형 사용
                type_id_str = selected_type.get().split("ID: ")[1][:-1]
                type_id = int(type_id_str)
                type_name = selected_type.get().split(" (ID:")[0]
            else:
                messagebox.showerror("오류", "장비 유형을 선택하거나 새로 입력해주세요.")
                return
            
            # 실제 DB 추가 로직
            try:
                if analyze_var.get():
                    # 통계 기반 추가
                    stats_analysis = self.analyze_parameter_statistics(selected_items)
                    added_count, updated_count, skipped_count = self.add_parameters_with_statistics(
                        type_id, stats_analysis, confidence_var.get() / 100.0
                    )
                    
                    result_msg = (f"🎯 통계 기반 Default DB 추가 완료:\n\n"
                                 f"📊 분석된 파라미터: {len(stats_analysis)}개\n"
                                 f"✅ 새로 추가: {added_count}개\n"
                                 f"🔄 업데이트: {updated_count}개\n"
                                 f"❌ 낮은 신뢰도로 제외: {skipped_count}개\n\n"
                                 f"💡 신뢰도 기준: {confidence_var.get():.1f}%")
                else:
                    # 단순 추가
                    added_count = self.add_parameters_simple(type_id, selected_items)
                    result_msg = f"📋 단순 추가 완료:\n\n총 {added_count}개의 항목이 Default DB에 추가되었습니다."
                
                total_changes = added_count + (updated_count if analyze_var.get() else 0)
                self.db_schema.log_change_history(
                    "bulk_add", "parameter", f"{type_name}_bulk_operation", 
                    "", f"Added/Updated {total_changes} parameters via multi-model analysis", "admin"
                )
                
                messagebox.showinfo("✅ 작업 완료", result_msg)
                dlg.destroy()
                self.update_comparison_view() # UI 갱신
                
                # Default DB 관리 탭이 있으면 업데이트
                if hasattr(self, 'default_db_tree') and hasattr(self, 'equipment_type_combo'):
                    self.refresh_equipment_types()
                    # 방금 추가한 장비 유형이 선택되도록 설정
                    type_names = self.equipment_type_combo['values']
                    target_type_name = None
                    
                    # 현재 사용된 장비 유형을 기준으로 찾기
                    for type_name_option in type_names:
                        if f"ID: {type_id}" in type_name_option:
                            target_type_name = type_name_option
                            break
                    
                    # 찾은 유형으로 설정하고 데이터 업데이트
                    if target_type_name:
                        self.equipment_type_combo.set(target_type_name)
                        self.on_equipment_type_selected()
                        self.update_log(f"✅ Default DB 관리 탭 업데이트 완료: {target_type_name}")
                    else:
                        # fallback: 현재 타입명으로 찾기
                        for type_name_option in type_names:
                            if type_name in type_name_option:
                                self.equipment_type_combo.set(type_name_option)
                                self.on_equipment_type_selected()
                                self.update_log(f"✅ Default DB 관리 탭 업데이트 완료 (타입명 매칭): {type_name_option}")
                                break
                        else:
                            # 최종 fallback: 첫 번째 항목 선택
                            if type_names:
                                self.equipment_type_combo.set(type_names[0])
                                self.on_equipment_type_selected()
                                self.update_log("✅ Default DB 관리 탭 업데이트 완료 (첫 번째 항목)")
                            else:
                                self.update_log("⚠️ 장비 유형이 없어 Default DB 탭 업데이트 실패")
                
            except Exception as e:
                messagebox.showerror("❌ 오류", f"Default DB 추가 중 오류 발생:\n{str(e)}")
                self.update_log(f"Default DB 추가 오류: {str(e)}")

        ttk.Button(button_frame, text="✅ Default DB에 추가", command=on_confirm).pack(side=tk.RIGHT, padx=5)
        
        # 다이얼로그 강제 업데이트 및 포커스
        dlg.update_idletasks()
        dlg.lift()
        dlg.focus_force()
        
        # 초기 미리보기 업데이트
        dlg.after(200, update_preview)
        update_confidence_label()  # 초기 신뢰도 라벨 설정

    def analyze_parameter_statistics(self, selected_items):
        """
        선택된 파라미터들의 통계 분석을 수행합니다.
        중복도 기반으로 가장 적합한 기준값을 결정합니다.
        
        Args:
            selected_items: 선택된 트리뷰 아이템 ID 리스트
            
        Returns:
            dict: 파라미터별 통계 정보
        """
        stats_analysis = {}
        
        for item_id in selected_items:
            item_values = self.comparison_tree.item(item_id, "values")
            
            # 유지보수 모드 여부에 따라 인덱스 조정
            col_offset = 1 if self.maint_mode else 0
            module, part, item_name = item_values[col_offset], item_values[col_offset+1], item_values[col_offset+2]
            
            param_name = item_name  # ItemName만 사용하여 통일
            
            # 모든 파일에서 해당 파라미터의 값 수집
            file_values = []
            for i, model in enumerate(self.file_names):
                if col_offset + 3 + i < len(item_values):
                    value = item_values[col_offset + 3 + i]
                    if value and value != "-":
                        file_values.append(str(value))
            
            if not file_values:
                continue
            
            # 값별 빈도 계산
            from collections import Counter
            value_counts = Counter(file_values)
            total_files = len(file_values)
            
            # 가장 빈번한 값 선택
            most_common_value, occurrence_count = value_counts.most_common(1)[0]
            confidence_score = occurrence_count / total_files
            
            # 수치값인 경우 통계 정보 추가 계산
            numeric_values = []
            for val in file_values:
                try:
                    numeric_values.append(float(val))
                except (ValueError, TypeError):
                    pass
            
            # ItemType 정보 추출 (merged_df에서 해당 파라미터의 ItemType 찾기)
            item_type = 'double'  # 기본값
            item_description = ''  # 기본값
            if hasattr(self, 'merged_df') and self.merged_df is not None:
                # 현재 아이템과 동일한 Module, Part, ItemName을 가진 행에서 ItemType과 ItemDescription 찾기
                matching_rows = self.merged_df[
                    (self.merged_df['Module'] == module) & 
                    (self.merged_df['Part'] == part) & 
                    (self.merged_df['ItemName'] == item_name)
                ]
                if not matching_rows.empty:
                    if 'ItemType' in matching_rows.columns:
                        item_type_values = matching_rows['ItemType'].dropna().unique()
                        if len(item_type_values) > 0:
                            item_type = item_type_values[0]  # 첫 번째 값 사용
                    
                    if 'ItemDescription' in matching_rows.columns:
                        item_desc_values = matching_rows['ItemDescription'].dropna().unique()
                        if len(item_desc_values) > 0:
                            item_description = item_desc_values[0]  # 첫 번째 값 사용
            
            stats_info = {
                'param_name': param_name,
                'module': module,
                'part': part,
                'item_name': item_name,
                'item_type': item_type,
                'item_description': item_description,
                'all_values': file_values,
                'value_counts': dict(value_counts),
                'most_common_value': most_common_value,
                'occurrence_count': occurrence_count,
                'total_files': total_files,
                'confidence_score': confidence_score,
                'unique_values': len(value_counts),
                'source_files': ','.join(self.file_names[:len(file_values)])
            }
            
            # 수치 통계 추가
            if numeric_values:
                import numpy as np
                stats_info.update({
                    'is_numeric': True,
                    'mean': np.mean(numeric_values),
                    'std': np.std(numeric_values),
                    'min': np.min(numeric_values),
                    'max': np.max(numeric_values),
                    'cv': np.std(numeric_values) / np.mean(numeric_values) if np.mean(numeric_values) != 0 else 0
                })
            else:
                stats_info['is_numeric'] = False
            
            stats_analysis[param_name] = stats_info
        
        return stats_analysis

    def add_parameters_with_statistics(self, type_id, stats_analysis, confidence_threshold=0.5):
        """
        통계 분석 결과를 바탕으로 파라미터를 Default DB에 추가합니다.
        
        Args:
            type_id: 장비 유형 ID
            stats_analysis: analyze_parameter_statistics 결과
            confidence_threshold: 신뢰도 임계값 (0.0 ~ 1.0)
            
        Returns:
            tuple: (추가된 개수, 업데이트된 개수, 제외된 개수)
        """
        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        for param_name, stats in stats_analysis.items():
            if stats['confidence_score'] < confidence_threshold:
                skipped_count += 1
                self.update_log(f"'{param_name}' 제외 - 낮은 신뢰도: {stats['confidence_score']*100:.1f}%")
                continue
            
            try:
                # 기존 항목 확인
                existing_stats = self.db_schema.get_parameter_statistics(type_id, param_name)
                
                # 최소/최대 사양 계산 (수치인 경우)
                min_spec = None
                max_spec = None
                if stats['is_numeric']:
                    # 평균 ± 2σ 범위를 사양으로 설정
                    mean = stats['mean']
                    std = stats['std']
                    min_spec = str(round(mean - 2 * std, 3))
                    max_spec = str(round(mean + 2 * std, 3))
                
                record_id = self.db_schema.add_default_value(
                    type_id, 
                    param_name, 
                    stats['most_common_value'],
                    min_spec,
                    max_spec,
                    stats['occurrence_count'],
                    stats['total_files'],
                    stats['source_files'],
                    description=stats.get('item_description', ''),
                    module_name=stats.get('module', ''),
                    part_name=stats.get('part', ''),
                    item_type=stats.get('item_type', 'double')
                )
                
                if existing_stats:
                    updated_count += 1
                    self.update_log(f"'{param_name}' 업데이트 완료 - 신뢰도: {stats['confidence_score']*100:.1f}%")
                else:
                    added_count += 1
                    self.update_log(f"'{param_name}' 추가 완료 - 신뢰도: {stats['confidence_score']*100:.1f}%")
                
            except Exception as e:
                skipped_count += 1
                self.update_log(f"'{param_name}' 처리 실패: {e}")
        
        return added_count, updated_count, skipped_count

    def add_parameters_simple(self, type_id, selected_items):
        """
        간단한 방식으로 파라미터를 Default DB에 추가합니다.
        첫 번째 파일의 값을 기준값으로 사용합니다.
        
        Args:
            type_id: 장비 유형 ID
            selected_items: 선택된 트리뷰 아이템 ID 리스트
            
        Returns:
            int: 추가된 항목 개수
        """
        count = 0
        for item_id in selected_items:
            item_values = self.comparison_tree.item(item_id, "values")
            
            # 유지보수 모드 여부에 따라 인덱스 조정
            col_offset = 1 if self.maint_mode else 0
            module, part, item_name = item_values[col_offset], item_values[col_offset+1], item_values[col_offset+2]
            
            # 첫 번째 파일의 값을 사용
            value = item_values[col_offset+3] 
            
            param_name = item_name  # ItemName만 사용하여 통일
            
            # merged_df에서 ItemType과 ItemDescription 정보 추출
            item_type = 'double'  # 기본값
            item_description = ''  # 기본값
            if hasattr(self, 'merged_df') and self.merged_df is not None:
                matching_rows = self.merged_df[
                    (self.merged_df['Module'] == module) & 
                    (self.merged_df['Part'] == part) & 
                    (self.merged_df['ItemName'] == item_name)
                ]
                if not matching_rows.empty:
                    if 'ItemType' in matching_rows.columns:
                        item_type_values = matching_rows['ItemType'].dropna().unique()
                        if len(item_type_values) > 0:
                            item_type = item_type_values[0]
                    
                    if 'ItemDescription' in matching_rows.columns:
                        item_desc_values = matching_rows['ItemDescription'].dropna().unique()
                        if len(item_desc_values) > 0:
                            item_description = item_desc_values[0]
            
            try:
                record_id = self.db_schema.add_default_value(
                    type_id, param_name, value, None, None, 1, 1, self.file_names[0],
                    description=item_description,
                    module_name=module,
                    part_name=part,
                    item_type=item_type
                )
                
                self.db_schema.log_change_history(
                    "add", "parameter", param_name, "", 
                    f"default: {value}, source: {self.file_names[0]}", "admin"
                )
                
                count += 1
                self.update_log(f"'{param_name}' 추가 성공 (ID: {record_id})")
            except Exception as e:
                self.update_log(f"'{param_name}' 추가 실패: {e}")
        
        return count

    def on_search_changed(self, event=None):
        """검색어 변경 시 필터링"""
        search_text = self.search_var.get().lower().strip()
        self.update_comparison_view(search_filter=search_text)
    
    def clear_search(self):
        """검색 입력창 지우기"""
        self.search_var.set("")
        self.update_comparison_view(search_filter="")

    def toggle_select_all_checkboxes(self):
        if not self.maint_mode:
            return
        check = self.select_all_var.get()
        for item in self.comparison_tree.get_children():
            values = list(self.comparison_tree.item(item, "values"))
            if len(values) > 0:
                values[0] = "☑" if check else "☐"
                self.comparison_tree.item(item, values=values)
                module, part, item_name = values[1], values[2], values[3]
                item_key = f"{module}_{part}_{item_name}"
                self.item_checkboxes[item_key] = check
        self.update_checked_count()

    def update_comparison_view(self, search_filter=""):
        for item in self.comparison_tree.get_children():
            self.comparison_tree.delete(item)
        
        saved_checkboxes = self.item_checkboxes.copy()
        self.item_checkboxes.clear()
        
        if self.maint_mode:
            self.comparison_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
        else:
            self.comparison_tree.unbind("<ButtonRelease-1>")
        
        diff_count = 0
        total_items = 0
        filtered_items = 0
        
        if self.merged_df is not None:
            # 파라미터별로 그룹화하여 비교
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            
            for (module, part, item_name), group in grouped:
                total_items += 1
                
                # 검색 필터링 적용
                if search_filter and search_filter not in item_name.lower():
                    continue
                
                # Module 필터링 적용
                if hasattr(self, 'comparison_module_filter_var'):
                    module_filter = self.comparison_module_filter_var.get()
                    if module_filter and module_filter != "All" and module != module_filter:
                        continue
                
                # Part 필터링 적용
                if hasattr(self, 'comparison_part_filter_var'):
                    part_filter = self.comparison_part_filter_var.get()
                    if part_filter and part_filter != "All" and part != part_filter:
                        continue
                
                filtered_items += 1
                
                values = []
                
                if self.maint_mode:
                    checkbox_state = "☐"
                    item_key = f"{module}_{part}_{item_name}"
                    if item_key in saved_checkboxes and saved_checkboxes[item_key]:
                        checkbox_state = "☑"
                    self.item_checkboxes[item_key] = (checkbox_state == "☑")
                    values.append(checkbox_state)
                
                values.extend([module, part, item_name])
                
                # 각 파일별 값 추출 및 비교
                file_values = []
                for model in self.file_names:
                    model_data = group[group["Model"] == model]
                    if not model_data.empty:
                        value = model_data["ItemValue"].iloc[0]
                        file_values.append(str(value))
                    else:
                        file_values.append("-")
                
                values.extend(file_values)
                
                # 차이점 검사 - 모든 값이 동일한지 확인
                unique_values = set(v for v in file_values if v != "-")
                has_difference = len(unique_values) > 1
                
                tags = []
                if has_difference:
                    tags.append("different")
                    diff_count += 1
                
                # Default DB에 존재하는지 확인
                is_existing = self.check_if_parameter_exists(module, part, item_name)
                if is_existing:
                    tags.append("existing")
                
                self.comparison_tree.insert("", "end", values=values, tags=tuple(tags))
            
            # 스타일 설정
            self.comparison_tree.tag_configure("different", background="#FFECB3", foreground="#E65100")
            self.comparison_tree.tag_configure("existing", foreground="#1976D2")
            
            if self.maint_mode:
                self.comparison_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
            
            self.update_selected_count(None)
        
        # 차이점 카운트 업데이트
        if not self.maint_mode and hasattr(self, 'diff_count_label'):
            self.diff_count_label.config(text=f"값이 다른 항목: {diff_count}개")
        
        # 검색 결과 표시 업데이트
        if hasattr(self, 'search_result_label'):
            if search_filter:
                self.search_result_label.config(text=f"검색 결과: {filtered_items}개 (전체: {total_items}개)")
            else:
                self.search_result_label.config(text="")
        
        # 필터 옵션 업데이트
        if hasattr(self, '_update_comparison_filter_options'):
            self._update_comparison_filter_options()
        
        # 필터 결과 표시 업데이트
        if hasattr(self, 'comparison_filter_result_label'):
            # Module/Part 필터가 적용된 경우 결과 표시
            module_filter = getattr(self, 'comparison_module_filter_var', tk.StringVar()).get()
            part_filter = getattr(self, 'comparison_part_filter_var', tk.StringVar()).get()
            
            if (module_filter and module_filter != "All") or (part_filter and part_filter != "All"):
                self.comparison_filter_result_label.config(text=f"필터 결과: {filtered_items}/{total_items} 항목")
            else:
                self.comparison_filter_result_label.config(text="")

    def create_comparison_context_menu(self):
        self.comparison_context_menu = tk.Menu(self.window, tearoff=0)
        self.comparison_context_menu.add_command(label="선택한 항목을 Default DB에 추가", command=self.add_to_default_db)
        self.comparison_tree.bind("<Button-3>", self.show_comparison_context_menu)
        self.update_comparison_context_menu_state()

    def show_comparison_context_menu(self, event):
        if not self.maint_mode:
            return
        if not self.comparison_tree.selection():
            return
        try:
            self.comparison_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.comparison_context_menu.grab_release()

    def update_comparison_context_menu_state(self):
        if hasattr(self, 'comparison_context_menu'):
            state = "normal" if self.maint_mode else "disabled"
            try:
                self.comparison_context_menu.entryconfig("선택한 항목을 Default DB에 추가", state=state)
            except Exception as e:
                self.update_log(f"컨텍스트 메뉴 상태 업데이트 중 오류 발생: {str(e)}")

    def toggle_checkbox(self, event):
        if not self.maint_mode:
            return
        region = self.comparison_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.comparison_tree.identify_column(event.x)
        if column != "#1":
            return
        item = self.comparison_tree.identify_row(event.y)
        if not item:
            return
        values = self.comparison_tree.item(item, "values")
        if not values or len(values) < 4:
            return
        current_state = values[0]
        module, part, item_name = values[1], values[2], values[3]
        item_key = f"{module}_{part}_{item_name}"
        new_state = "☑" if current_state == "☐" else "☐"
        self.item_checkboxes[item_key] = (new_state == "☑")
        new_values = list(values)
        new_values[0] = new_state
        self.comparison_tree.item(item, values=new_values)
        self.update_checked_count()

    def update_selected_count(self, event):
        if not self.maint_mode:
            return
        checked_count = sum(1 for checked in self.item_checkboxes.values() if checked)
        if checked_count > 0:
            self.selected_count_label.config(text=f"체크된 항목: {checked_count}개")
        else:
            selected_items = self.comparison_tree.selection()
            count = len(selected_items)
            self.selected_count_label.config(text=f"선택된 항목: {count}개")

    def update_checked_count(self):
        if not self.maint_mode:
            return
        checked_count = sum(1 for checked in self.item_checkboxes.values() if checked)
        self.selected_count_label.config(text=f"체크된 항목: {checked_count}개")

    def check_if_parameter_exists(self, module, part, item_name):
        try:
            equipment_types = self.db_schema.get_equipment_types()
            for type_id, type_name, _ in equipment_types:
                if type_name.lower() == module.lower():
                    default_values = self.db_schema.get_default_values(type_id)
                    for _, param_name, _, _, _, _ in default_values:
                        # ItemName만으로 체크하도록 통일
                        if param_name == item_name:
                            return True
            return False
        except Exception as e:
            self.update_log(f"DB_ItemName 존재 여부 확인 중 오류: {str(e)}")
            return False

    def disable_maint_features(self):
        """유지보수 모드 비활성화 - QC 엔지니어용 탭들을 제거합니다."""
        try:
            self.update_log("🔄 유지보수 모드 비활성화 시작...")
            
            # QC 엔지니어용 탭들 제거
            if hasattr(self, 'main_notebook') and self.main_notebook:
                tabs_to_remove = []
                
                # 역순으로 탭 확인 (인덱스 변경 방지)
                for tab_id in range(self.main_notebook.index('end') - 1, -1, -1):
                    try:
                        tab_text = self.main_notebook.tab(tab_id, 'text')
                        # 이모지가 포함된 탭 텍스트도 고려하여 패턴 매칭
                        should_remove = False
                        if ("Default DB 관리" in tab_text or 
                            "QC 검수" in tab_text or 
                            "검수" in tab_text):
                            should_remove = True
                        
                        if should_remove:
                            tabs_to_remove.append((tab_id, tab_text))
                    except tk.TclError:
                        continue  # 탭이 이미 제거된 경우
                
                # 탭 제거 실행
                for tab_id, tab_text in tabs_to_remove:
                    try:
                        self.main_notebook.forget(tab_id)
                        self.update_log(f"✅ {tab_text} 탭 제거 완료")
                    except tk.TclError as e:
                        self.update_log(f"⚠️ {tab_text} 탭 제거 실패: {e}")
                        
                self.update_log(f"🗑️ 총 {len(tabs_to_remove)}개 유지보수 탭 제거 완료")
            
            # QC 엔지니어용 탭 프레임 참조 완전 제거
            self.qc_check_frame = None
            self.default_db_frame = None
            
            # QC 관련 추가 참조 제거
            if hasattr(self, 'qc_notebook'):
                try:
                    del self.qc_notebook
                    self.update_log("✅ QC 노트북 참조 제거 완료")
                except:
                    pass
            
            # QC 관련 위젯 참조 제거
            qc_widgets = ['qc_type_var', 'qc_type_combobox', 'qc_result_tree', 
                         'stats_frame', 'chart_frame']
            for widget_name in qc_widgets:
                if hasattr(self, widget_name):
                    try:
                        delattr(self, widget_name)
                    except:
                        pass
            
            # 유지보수 모드 비활성화
            self.maint_mode = False
            
            # 상태바 업데이트
            if hasattr(self, 'status_bar'):
                self.status_bar.config(text="장비 생산 엔지니어 모드")
            
            self.update_log("✅ 유지보수 모드가 완전히 비활성화되었습니다.")
            
        except Exception as e:
            error_msg = f"유지보수 모드 비활성화 중 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            print(f"DEBUG - disable_maint_features error: {e}")
            import traceback
            traceback.print_exc()

    def create_qc_check_tab(self):
        """QC 검수 탭 생성 - 새로운 QCTabController 사용"""
        try:
            # 기존 탭 중복 검사 강화
            if hasattr(self, 'main_notebook') and self.main_notebook:
                for tab_id in range(self.main_notebook.index('end')):
                    try:
                        tab_text = self.main_notebook.tab(tab_id, 'text')
                        if "QC 검수" in tab_text or "검수" in tab_text:
                            self.update_log(f"⚠️ QC 검수 탭이 이미 존재함 ({tab_text}) - 기존 탭으로 이동")
                            self.main_notebook.select(tab_id)
                            return
                    except tk.TclError:
                        continue
            
            # 프레임 참조 체크
            if self.qc_check_frame is not None:
                self.update_log("⚠️ QC 프레임 참조가 남아있음 - 초기화 후 재생성")
                self.qc_check_frame = None
            
            self.update_log("🚀 새로운 QC 탭 컨트롤러로 탭 생성 시작...")
            
            # 🚀 새로운 QCTabController 사용
            from app.ui.controllers.tab_controllers.qc_tab_controller import QCTabController
            
            # QC 검수 탭 프레임 생성
            self.qc_check_frame = ttk.Frame(self.main_notebook)
            self.main_notebook.add(self.qc_check_frame, text="🔍 QC 검수 (신규)")
            
            # QCTabController 인스턴스 생성
            self.qc_tab_controller = QCTabController(self.qc_check_frame, self)
            
            self.update_log("🎉 새로운 QC 탭 컨트롤러로 탭이 생성되었습니다!")
            self.update_log("   ✅ 리팩토링된 UI 적용됨")
            self.update_log("   ✅ 최종 보고서 기능 포함됨")
            return  # 여기서 메서드 종료 (기존 코드 실행 방지)
            
            # 🆕 src/app/qc.py의 완전한 QC 탭 기능 사용
            # 기존 기본 탭 대신 고급 QC 기능이 포함된 탭 생성
            
            # 상단 컨트롤 프레임
            control_frame = ttk.Frame(self.qc_check_frame)
            control_frame.pack(fill=tk.X, padx=5, pady=5)

            # 장비 유형 선택 프레임
            type_frame = ttk.LabelFrame(control_frame, text="장비 유형 선택", padding=10)
            type_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            # 장비 유형 콤보박스
            ttk.Label(type_frame, text="장비 유형:").pack(side=tk.LEFT, padx=(0, 5))
            self.qc_type_var = tk.StringVar()
            self.qc_type_combobox = ttk.Combobox(type_frame, textvariable=self.qc_type_var, state="readonly", width=20)
            self.qc_type_combobox.pack(side=tk.LEFT, padx=(0, 10))

            # 🆕 새로고침 버튼 추가
            refresh_btn = ttk.Button(type_frame, text="🔄 목록 새로고침", command=self.refresh_qc_equipment_types)
            refresh_btn.pack(side=tk.LEFT, padx=(5, 10))

            # QC 실행 버튼
            qc_btn = ttk.Button(type_frame, text="QC 검수 실행", command=self.perform_qc_check)
            qc_btn.pack(side=tk.LEFT, padx=(0, 5))

            # 검수 결과 프레임
            middle_frame = ttk.LabelFrame(self.qc_check_frame, text="검수 결과", padding=10)
            middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # 검수 결과 트리뷰
            from app.widgets import create_treeview_with_scrollbar
            
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

            qc_result_frame, self.qc_result_tree = create_treeview_with_scrollbar(
                middle_frame, columns, headings, column_widths, height=15)
            qc_result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # 검수 통계 프레임
            bottom_frame = ttk.LabelFrame(self.qc_check_frame, text="검수 통계", padding=10)
            bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            self.stats_frame = ttk.Frame(bottom_frame)
            self.stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            self.chart_frame = ttk.Frame(bottom_frame)
            self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            # 장비 유형 목록 로드
            self.load_equipment_types_for_qc()
            
            # 생성된 탭으로 자동 이동
            for tab_id in range(self.main_notebook.index('end')):
                try:
                    tab_text = self.main_notebook.tab(tab_id, 'text')
                    if tab_text == "QC 검수":
                        self.main_notebook.select(tab_id)
                        break
                except tk.TclError:
                    continue
            
            self.update_log("✅ QC 검수 탭 생성 및 활성화 완료")
            
        except Exception as e:
            error_msg = f"QC 검수 탭 생성 중 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            print(f"DEBUG - create_qc_check_tab error: {e}")
            import traceback
            traceback.print_exc()
            # 실패 시 프레임 참조 정리
            self.qc_check_frame = None

    def create_default_db_tab(self):
        """Default DB 관리 탭 생성 - 중복 생성 방지 강화"""
        try:
            self.update_log("🔧 Default DB 관리 탭 생성 시작...")
            
            # 기존 탭 중복 검사 강화
            if hasattr(self, 'main_notebook') and self.main_notebook:
                for tab_id in range(self.main_notebook.index('end')):
                    try:
                        tab_text = self.main_notebook.tab(tab_id, 'text')
                        if "Default DB 관리" in tab_text or tab_text == "Default DB 관리":
                            self.update_log("⚠️ Default DB 관리 탭이 이미 존재함 - 기존 탭으로 이동")
                            self.main_notebook.select(tab_id)
                            return
                    except tk.TclError:
                        continue
            
            # 프레임 참조 체크
            if self.default_db_frame is not None:
                self.update_log("⚠️ Default DB 프레임 참조가 남아있음 - 초기화 후 재생성")
                self.default_db_frame = None
            
            # DBSchema 확인
            if not self.db_schema:
                self.update_log("❌ DBSchema가 초기화되지 않음 - 탭 생성 취소")
                return
                
            self.default_db_frame = ttk.Frame(self.main_notebook)
            self.main_notebook.add(self.default_db_frame, text="Default DB 관리")
            self.update_log("✅ Default DB 탭 프레임 생성 완료")
            
            # 상단 제어 패널 - 배경색과 패딩 개선
            control_frame = ttk.Frame(self.default_db_frame, style="Control.TFrame")
            control_frame.pack(fill=tk.X, padx=15, pady=10)
            
            # 장비 유형 관리 섹션
            equipment_frame = ttk.LabelFrame(control_frame, text="Equipment Type Management", padding=12)
            equipment_frame.pack(fill=tk.X, pady=(0, 8))
            
            # 장비 유형 선택
            type_select_frame = ttk.Frame(equipment_frame)
            type_select_frame.pack(fill=tk.X, pady=(0, 8))
            
            ttk.Label(type_select_frame, text="Equipment Type:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))
            self.equipment_type_var = tk.StringVar()
            self.equipment_type_combo = ttk.Combobox(type_select_frame, textvariable=self.equipment_type_var, 
                                                   state="readonly", width=40, font=("Segoe UI", 9))
            self.equipment_type_combo.pack(side=tk.LEFT, padx=(0, 12))
            self.equipment_type_combo.bind("<<ComboboxSelected>>", self.on_equipment_type_selected)
            self.update_log("✅ 장비 유형 콤보박스 생성 완료")
            
            # 장비 유형 관리 버튼들
            type_buttons_frame = ttk.Frame(equipment_frame)
            type_buttons_frame.pack(fill=tk.X)
            
            add_type_btn = ttk.Button(type_buttons_frame, text="Add Equipment Type", 
                                    command=self.add_equipment_type_dialog, width=18)
            add_type_btn.pack(side=tk.LEFT, padx=(0, 6))
            
            delete_type_btn = ttk.Button(type_buttons_frame, text="Delete", 
                                       command=self.delete_equipment_type, width=10)
            delete_type_btn.pack(side=tk.LEFT, padx=(0, 6))
            
            refresh_btn = ttk.Button(type_buttons_frame, text="Refresh", 
                                   command=self.refresh_equipment_types, width=10)
            refresh_btn.pack(side=tk.LEFT, padx=(0, 6))
            
            # 파라미터 관리 섹션
            param_frame = ttk.LabelFrame(control_frame, text="Parameter Management", padding=12)
            param_frame.pack(fill=tk.X, pady=(0, 8))
            
            # 모든 관리 버튼들을 한 행에 배치
            mgmt_buttons_frame = ttk.Frame(param_frame)
            mgmt_buttons_frame.pack(fill=tk.X)
            
            # 4개 버튼을 한 행에 배치 - 버튼 크기 개선
            add_param_btn = ttk.Button(mgmt_buttons_frame, text="Add Parameter", 
                                     command=self.add_parameter_dialog, width=13)
            add_param_btn.pack(side=tk.LEFT, padx=(0, 6))
            
            delete_param_btn = ttk.Button(mgmt_buttons_frame, text="Delete Selected", 
                                        command=self.delete_selected_parameters, width=13)
            delete_param_btn.pack(side=tk.LEFT, padx=(0, 6))
            
            import_btn = ttk.Button(mgmt_buttons_frame, text="Import from Text File", 
                                  command=self.import_from_text_file, width=18)
            import_btn.pack(side=tk.LEFT, padx=(0, 6))
            
            export_btn = ttk.Button(mgmt_buttons_frame, text="Export to Text File", 
                                  command=self.export_to_text_file, width=16)
            export_btn.pack(side=tk.LEFT)
            
            # Excel 기능 제거됨
            
            # 파라미터 목록 트리뷰
            tree_container = ttk.LabelFrame(self.default_db_frame, text="Parameter List", padding=10)
            tree_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 8))
            
            # 🔍 필터 패널 추가 (새로운 기능)
            self._create_parameter_filter_panel(tree_container)
            
            tree_frame = ttk.Frame(tree_container)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            
            # 트리뷰 컬럼 정의 (순차 번호 컬럼으로 변경)
            columns = ("no", "parameter_name", "module", "part", "item_type", "default_value", "min_spec", "max_spec", 
                      "is_performance", "description")

            self.default_db_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
            self.update_log("✅ Default DB 트리뷰 생성 완료")

            # 컬럼 헤더 설정
            headers = {
                "no": "No.",  # 순차 번호 컬럼
                "parameter_name": "ItemName",
                "module": "Module",
                "part": "Part", 
                "item_type": "Data Type",
                "default_value": "Default Value",
                "min_spec": "Min Spec",
                "max_spec": "Max Spec",
                "is_performance": "Check list",
                "description": "Description"
            }

            # 컬럼 너비 최적화
            column_widths = {
                "no": 50,  # 순차 번호 컬럼 너비
                "parameter_name": 220,
                "module": 80,
                "part": 100,
                "item_type": 85,
                "default_value": 100,
                "min_spec": 80,
                "max_spec": 80,
                "is_performance": 90,
                "description": 150
            }
            
            for col in columns:
                self.default_db_tree.heading(col, text=headers[col])
                self.default_db_tree.column(col, width=column_widths[col], minwidth=50)
            
            # 스크롤바 추가 - 스타일 개선
            db_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.default_db_tree.yview)
            self.default_db_tree.configure(yscrollcommand=db_scrollbar.set)
            
            db_h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.default_db_tree.xview)
            self.default_db_tree.configure(xscrollcommand=db_h_scrollbar.set)
            
            # 배치 - 간격 조정
            self.default_db_tree.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=(0, 2))
            db_scrollbar.grid(row=0, column=1, sticky="ns", pady=(0, 2))
            db_h_scrollbar.grid(row=1, column=0, sticky="ew", padx=(0, 2))
            
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # 더블클릭으로 편집
            self.default_db_tree.bind("<Double-1>", self.edit_parameter_dialog)
            
            # 🆕 우클릭 메뉴 추가
            self.create_default_db_context_menu()
            self.default_db_tree.bind("<Button-3>", self.show_default_db_context_menu)
            
            # 🔍 필터 기능 초기화 (새로운 기능)
            self._initialize_parameter_filter_functionality()
            
            # 상태 표시줄
            status_container = ttk.LabelFrame(self.default_db_frame, text="Status Information", padding=10)
            status_container.pack(fill=tk.X, padx=15, pady=(0, 8))
            
            status_frame = ttk.Frame(status_container)
            status_frame.pack(fill=tk.X)
            
            # 상태 메시지
            self.default_db_status_label = ttk.Label(status_frame, text="Please select an equipment type.", 
                                                   font=("Segoe UI", 9))
            self.default_db_status_label.pack(side=tk.LEFT)
            
            # Performance 통계 표시
            self.performance_stats_label = ttk.Label(status_frame, text="", 
                                                   foreground="#2E5BBA", font=("Segoe UI", 9, "bold"))
            self.performance_stats_label.pack(side=tk.RIGHT)
            
            self.update_log("✅ Default DB 상태 표시줄 생성 완료")
            
            # 초기 데이터 로드 (UI 초기화 완료 후 실행)
            self.window.after(200, self.refresh_equipment_types)
            
            # 디버깅을 위한 로그 추가
            self.update_log("✅ Default DB 관리 탭이 완전히 생성되었습니다.")
            
        except Exception as e:
            error_msg = f"Default DB 관리 탭 생성 오류: {e}"
            self.update_log(f"❌ {error_msg}")
            print(f"DEBUG - create_default_db_tab error: {e}")
            import traceback
            traceback.print_exc()

    def _create_parameter_filter_panel(self, parent_frame):
        """파라미터 필터 패널 생성 (새로운 기능)"""
        try:
            # 필터 프레임 - Parameter List에 통합된 스타일
            self.filter_frame = ttk.Frame(parent_frame)
            self.filter_frame.pack(fill=tk.X, pady=(0, 5))
            
            # 구분선
            separator = ttk.Separator(self.filter_frame, orient='horizontal')
            separator.pack(fill=tk.X, pady=(5, 8))
            
            # 검색 및 필터 행
            filter_row = ttk.Frame(self.filter_frame)
            filter_row.pack(fill=tk.X, pady=(0, 8))
            
            # 실시간 검색
            search_frame = ttk.Frame(filter_row)
            search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            ttk.Label(search_frame, text="🔎 Search:", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 6))
            self.param_search_var = tk.StringVar()
            self.param_search_entry = ttk.Entry(search_frame, textvariable=self.param_search_var, width=25, font=('Segoe UI', 9))
            self.param_search_entry.pack(side=tk.LEFT, padx=(0, 6))
            
            # Clear 버튼
            clear_btn = ttk.Button(search_frame, text="Clear", command=self._clear_parameter_search)
            clear_btn.pack(side=tk.LEFT, padx=(0, 15))
            
            # Check list 필터 체크박스를 Parameter List로 이동
            self.show_performance_only_var = tk.BooleanVar()
            performance_cb = ttk.Checkbutton(
                search_frame, 
                text="Check list Only", 
                variable=self.show_performance_only_var,
                command=self.apply_performance_filter
            )
            performance_cb.pack(side=tk.LEFT, padx=(0, 10))
            
            # 필터 컨트롤 영역
            self.advanced_filter_visible = tk.BooleanVar(value=False)
            
            control_row = ttk.Frame(filter_row)
            control_row.pack(side=tk.RIGHT, padx=(10, 0))
            
            # 결과 표시 레이블
            self.filter_result_label = ttk.Label(control_row, text="", foreground="#1976D2", font=('Segoe UI', 8))
            self.filter_result_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Advanced Filter 토글 버튼
            self.toggle_advanced_btn = ttk.Button(
                control_row, 
                text="▼ Filters", 
                command=self._toggle_advanced_parameter_filters
            )
            self.toggle_advanced_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Reset 버튼
            reset_btn = ttk.Button(control_row, text="Reset", command=self._reset_parameter_filters)
            reset_btn.pack(side=tk.LEFT)
            
            # 고급 필터 패널 (처음에는 숨김)
            self.advanced_filter_frame = ttk.Frame(self.filter_frame)
            
            self._create_advanced_parameter_filters()
            
            self.update_log("✅ Parameter filters initialized")
            
        except Exception as e:
            self.update_log(f"❌ Parameter filters error: {e}")

    def _create_advanced_parameter_filters(self):
        """고급 파라미터 필터 생성 - 엔지니어 스타일 단일 행 레이아웃 (새로운 기능)"""
        try:
            # 구분선
            filter_separator = ttk.Separator(self.advanced_filter_frame, orient='horizontal')
            filter_separator.pack(fill=tk.X, pady=(5, 8))
            
            # 필터 행
            filters_row = ttk.Frame(self.advanced_filter_frame)
            filters_row.pack(fill=tk.X, pady=(0, 8))
            
            # Module Filter
            module_frame = ttk.Frame(filters_row)
            module_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            ttk.Label(module_frame, text="Module:", font=('Segoe UI', 8)).pack(anchor='w')
            self.module_filter_var = tk.StringVar()
            self.module_filter_combo = ttk.Combobox(module_frame, textvariable=self.module_filter_var, 
                                                  state="readonly", width=12, font=('Segoe UI', 8))
            self.module_filter_combo.pack()
            self.module_filter_combo.bind('<<ComboboxSelected>>', self._on_module_filter_changed)
            
            # Part Filter
            part_frame = ttk.Frame(filters_row)
            part_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            ttk.Label(part_frame, text="Part:", font=('Segoe UI', 8)).pack(anchor='w')
            self.part_filter_var = tk.StringVar()
            self.part_filter_combo = ttk.Combobox(part_frame, textvariable=self.part_filter_var, 
                                                state="readonly", width=12, font=('Segoe UI', 8))
            self.part_filter_combo.pack()
            self.part_filter_combo.bind('<<ComboboxSelected>>', self._on_part_filter_changed)
            
            # Data Type Filter
            type_frame = ttk.Frame(filters_row)
            type_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            ttk.Label(type_frame, text="Data Type:", font=('Segoe UI', 8)).pack(anchor='w')
            self.data_type_filter_var = tk.StringVar()
            self.data_type_filter_combo = ttk.Combobox(type_frame, textvariable=self.data_type_filter_var, 
                                                     state="readonly", width=10, font=('Segoe UI', 8))
            self.data_type_filter_combo.pack()
            self.data_type_filter_combo.bind('<<ComboboxSelected>>', self._on_data_type_filter_changed)
            
            self.update_log("✅ Advanced filters ready")
            
        except Exception as e:
            self.update_log(f"❌ Advanced filters error: {e}")

    def _initialize_parameter_filter_functionality(self):
        """파라미터 필터 기능 초기화 (새로운 기능)"""
        try:
            # 필터 관련 변수 초기화
            self.original_parameter_data = []  # 원본 데이터 보관
            self.filtered_parameter_data = []  # 필터링된 데이터
            self.current_sort_column = ""
            self.current_sort_reverse = False
            
            # 이벤트 바인딩
            self.param_search_var.trace('w', lambda *args: self._apply_parameter_filters())
            
            # 🔄 컬럼 헤더 클릭 정렬 설정
            self._setup_parameter_column_sorting()
            
            self.update_log("✅ Parameter 필터 기능 초기화 완료")
            
        except Exception as e:
            self.update_log(f"❌ Parameter 필터 기능 초기화 오류: {e}")

    def _setup_parameter_column_sorting(self):
        """파라미터 컬럼 헤더 클릭 정렬 설정 (새로운 기능)"""
        try:
            columns = self.default_db_tree['columns']
            
            # 각 컬럼 헤더에 클릭 이벤트 바인딩
            for col in columns:
                # 순서 번호 컬럼은 정렬에서 제외
                if col != 'no':
                    self.default_db_tree.heading(col, command=lambda c=col: self._sort_parameter_by_column(c))
            
            self.update_log("✅ Parameter 컬럼 정렬 설정 완료")
            
        except Exception as e:
            self.update_log(f"❌ Parameter 컬럼 정렬 설정 오류: {e}")

    def refresh_equipment_types(self):
        """장비 유형 목록을 새로고침합니다. (전체 탭 동기화)"""
        try:
            self.update_log("🔄 전체 장비 유형 목록 동기화 시작...")
            
            # DBSchema가 초기화되었는지 확인
            if not self.db_schema:
                self.update_log("❌ DBSchema가 초기화되지 않음")
                return
            
            # 최신 장비 유형 목록 조회
            equipment_types = self.db_schema.get_equipment_types()
            self.update_log(f"📊 조회된 장비 유형: {len(equipment_types)}개")
            
            # 1. Default DB 관리 탭 갱신
            self._refresh_default_db_equipment_types(equipment_types)
            
            # 2. QC 검수 탭 갱신  
            self._refresh_qc_equipment_types(equipment_types)
            
            # 3. defaultdb.py의 장비 유형 목록 갱신
            self._refresh_defaultdb_equipment_types(equipment_types)
            
            self.update_log("✅ 전체 장비 유형 목록 동기화 완료")
                
        except Exception as e:
            error_msg = f"장비 유형 동기화 오류: {e}"
            self.update_log(f"❌ {error_msg}")
            print(f"DEBUG - refresh_equipment_types error: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_default_db_equipment_types(self, equipment_types):
        """Default DB 관리 탭의 장비 유형 목록 갱신"""
        try:
            # manager.py의 Default DB 탭 콤보박스 갱신
            if hasattr(self, 'equipment_type_combo'):
                current_selection = self.equipment_type_var.get()
                type_names = [f"{name} (ID: {type_id})" for type_id, name, _ in equipment_types]
                
                self.equipment_type_combo['values'] = type_names
                
                # 현재 선택된 항목이 여전히 존재하는지 확인
                if current_selection and current_selection in type_names:
                    self.equipment_type_combo.set(current_selection)
                elif type_names:
                    self.equipment_type_combo.set(type_names[0])
                    self.on_equipment_type_selected()
                else:
                    self.equipment_type_var.set("")
                    self.update_default_db_display([])
                
                self.update_log(f"📋 Default DB 탭 콤보박스 갱신: {len(type_names)}개")
                
        except Exception as e:
            self.update_log(f"⚠️ Default DB 탭 갱신 실패: {e}")

    def _refresh_qc_equipment_types(self, equipment_types):
        """QC 검수 탭의 장비 유형 목록 갱신"""
        try:
            # QC 검수 탭 콤보박스 갱신
            if hasattr(self, 'qc_type_combobox') and hasattr(self, 'equipment_types_for_qc'):
                current_selection = getattr(self, 'qc_type_var', tk.StringVar()).get()
                
                # 장비 유형 딕셔너리 업데이트
                self.equipment_types_for_qc = {name: type_id for type_id, name, _ in equipment_types}
                type_names = list(self.equipment_types_for_qc.keys())
                
                self.qc_type_combobox['values'] = type_names
                
                # 현재 선택된 항목이 여전히 존재하는지 확인
                if current_selection and current_selection in type_names:
                    self.qc_type_combobox.set(current_selection)
                elif type_names:
                    self.qc_type_combobox.set(type_names[0])
                else:
                    if hasattr(self, 'qc_type_var'):
                        self.qc_type_var.set("")
                
                self.update_log(f"🔍 QC 검수 탭 콤보박스 갱신: {len(type_names)}개")
            
            # 🆕 QC 탭의 기본 장비 유형 로드 함수도 호출
            if hasattr(self, 'load_equipment_types_for_qc'):
                self.load_equipment_types_for_qc()
                self.update_log("🔍 QC 탭 load_equipment_types_for_qc 함수도 호출 완료")
                
        except Exception as e:
            self.update_log(f"⚠️ QC 검수 탭 갱신 실패: {e}")

    def _refresh_defaultdb_equipment_types(self, equipment_types):
        """defaultdb.py 모듈의 장비 유형 목록 갱신"""
        try:
            # defaultdb.py의 load_equipment_types 함수 호출
            if hasattr(self, 'load_equipment_types'):
                self.load_equipment_types()
                self.update_log("🗃️ defaultdb 모듈 장비 유형 갱신 완료")
                
            # defaultdb.py의 load_equipment_type_list도 갱신 (관리 대화상자용)
            # 이는 대화상자가 열려 있을 때만 필요하므로 별도 처리
                
        except Exception as e:
            self.update_log(f"⚠️ defaultdb 모듈 갱신 실패: {e}")

    def refresh_all_equipment_type_lists(self):
        """모든 탭의 장비 유형 목록을 강제로 새로고침 (외부 호출용)"""
        self.refresh_equipment_types()
        
        # 🆕 QC 탭도 강제 갱신
        try:
            if hasattr(self, 'load_equipment_types_for_qc'):
                self.load_equipment_types_for_qc()
                self.update_log("🔍 QC 탭 추가 갱신 완료")
        except Exception as e:
            self.update_log(f"⚠️ QC 탭 추가 갱신 실패: {e}")
        
        # 추가적으로 다른 모듈에서도 갱신이 필요한 경우
        try:
            # default_db_helpers.py의 update_equipment_type_list 호출
            if hasattr(self, 'update_equipment_type_list'):
                self.update_equipment_type_list()
                self.update_log("📋 default_db_helpers 모듈도 갱신 완료")
        except Exception as e:
            self.update_log(f"⚠️ default_db_helpers 갱신 실패: {e}")
        
        # 🆕 동기화 상태 확인
        self.update_log("🎯 전체 장비 유형 동기화 완료!")

    def on_equipment_type_selected(self, event=None):
        """장비 유형이 선택되었을 때 호출됩니다."""
        try:
            selected = self.equipment_type_var.get()
            self.update_log(f"🔄 장비 유형 선택됨: '{selected}'")
            
            if not selected:
                self.update_default_db_display([])
                self.update_log("⚠️ 선택된 장비 유형이 없음 - 빈 목록 표시")
                return
                
            # 장비 유형 ID 추출
            type_id_str = selected.split("ID: ")[1][:-1]
            type_id = int(type_id_str)
            self.update_log(f"🔍 추출된 장비 유형 ID: {type_id}")
            
            # 🆕 Performance 필터 적용하여 파라미터 조회 (현재는 checklist_only 지원)
            performance_only = hasattr(self, 'show_performance_only_var') and self.show_performance_only_var.get()
            default_values = self.db_schema.get_default_values(type_id, checklist_only=performance_only)
            
            # 🆕 Performance 통계 업데이트 (기본 구현)
            if hasattr(self, 'performance_stats_label'):
                try:
                    # 간단한 통계 계산
                    total_count = len(default_values) if default_values else 0
                    perf_count = sum(1 for item in default_values if len(item) > 14 and item[14]) if default_values else 0
                    perf_ratio = (perf_count / total_count * 100) if total_count > 0 else 0
                    stats_text = f"🎯 Performance: {perf_count}/{total_count} ({perf_ratio:.1f}%)"
                    self.performance_stats_label.config(text=stats_text)
                except:
                    self.performance_stats_label.config(text="")
            self.update_log(f"📊 조회된 파라미터 수: {len(default_values)}개")
            
            if default_values:
                # 첫 번째 파라미터 정보 로그
                first_param = default_values[0]
                self.update_log(f"🔖 첫 번째 파라미터: {first_param[1]} = {first_param[2]}")
            
            self.update_default_db_display(default_values)
            self.update_log("✅ Default DB 화면 업데이트 완료")
            
        except Exception as e:
            error_msg = f"장비 유형 선택 처리 오류: {e}"
            self.update_log(f"❌ {error_msg}")
            print(f"DEBUG - on_equipment_type_selected error: {e}")
            import traceback
            traceback.print_exc()

    def update_default_db_display(self, default_values=None):
        """Default DB 트리뷰 표시 업데이트 - 순차 번호 포함"""
        if not hasattr(self, 'default_db_tree'):
            return
            
        # 기존 항목 삭제
        for item in self.default_db_tree.get_children():
            self.default_db_tree.delete(item)
        
        if default_values is None:
            self.default_db_status_label.config(text="No parameters found for this equipment type.")
            return
        
        # Performance 필터 적용
        if hasattr(self, 'show_performance_only_var') and self.show_performance_only_var.get():
            default_values = [item for item in default_values if len(item) > 14 and item[14] == 1]
        
        # 🔍 필터 기능을 위한 원본 데이터 저장 (새로운 기능)
        if hasattr(self, 'original_parameter_data'):
            self.original_parameter_data = []
            for idx, item in enumerate(default_values, 1):
                try:
                    if len(item) >= 15:
                        # 올바른 SQL 순서에 맞게 파싱
                        record_id, param_name, default_value, min_spec, max_spec, type_name, occurrence_count, total_files, confidence_score, source_files, description, module_name, part_name, item_type, is_performance = item[:15]
                        
                        # Performance 표시
                        performance_display = "Yes" if is_performance == 1 else "No"
                        
                        # 필터용 데이터 구조 (DB 데이터 정확히 매핑)
                        row_data = [
                            record_id,  # 0: 실제 DB ID
                            param_name or "",  # 1: ItemName
                            module_name or "",  # 2: Module (실제 모듈명)
                            part_name or "",   # 3: Part
                            item_type or "double",  # 4: Data Type
                            str(default_value) if default_value is not None else "",  # 5: Default Value
                            str(min_spec) if min_spec is not None else "",  # 6: Min Spec
                            str(max_spec) if max_spec is not None else "",  # 7: Max Spec
                            performance_display,  # 8: Performance
                            description or ""  # 9: Description
                        ]
                        self.original_parameter_data.append(row_data)
                        
                    else:
                        # 이전 버전 호환성
                        record_id, param_name, default_value, min_spec, max_spec, occurrence_count = item[:6]
                        row_data = [
                            record_id,  # 실제 DB ID
                            param_name or "",
                            "", "", "double",
                            str(default_value) if default_value is not None else "",
                            str(min_spec) if min_spec is not None else "",
                            str(max_spec) if max_spec is not None else "",
                            "No", ""
                        ]
                        self.original_parameter_data.append(row_data)
                        
                except Exception as e:
                    self.update_log(f"⚠️ 필터 데이터 준비 중 오류: {e}")
                    continue
            
            # 필터링된 데이터도 초기화 (전체 데이터)
            self.filtered_parameter_data = self.original_parameter_data.copy()
            
            # 필터 옵션 업데이트
            if hasattr(self, '_update_filter_options'):
                self._update_filter_options()
            
            # 필터 적용 (초기에는 모든 데이터)
            if hasattr(self, '_apply_parameter_filters'):
                self._apply_parameter_filters()
                return  # 필터 기능이 있으면 트리뷰 업데이트는 필터에서 처리
        
        # 🔍 필터 기능이 없는 경우 기존 방식으로 처리
        # 순차 번호와 함께 데이터 표시
        for idx, item in enumerate(default_values, 1):
            try:
                if len(item) >= 15:
                    # 올바른 SQL 순서에 맞게 파싱
                    record_id, param_name, default_value, min_spec, max_spec, type_name, occurrence_count, total_files, confidence_score, source_files, description, module_name, part_name, item_type, is_performance = item[:15]
                    
                    # Performance 표시
                    performance_display = "Yes" if is_performance == 1 else "No"
                    
                    # 순차 번호를 첫 번째 컬럼에 표시
                    values = (
                        str(idx),  # 순차 번호 (1, 2, 3...)
                        param_name or "", 
                        module_name or "",  # 실제 모듈명 사용
                        part_name or "", 
                        item_type or "double",
                        str(default_value) if default_value is not None else "",
                        str(min_spec) if min_spec is not None else "",
                        str(max_spec) if max_spec is not None else "",
                        performance_display,
                        description or ""
                    )
                    
                    # 실제 DB ID는 item의 tags로 저장 (내부 관리용)
                    self.default_db_tree.insert("", "end", values=values, tags=(f"id_{record_id}",))
                    
                else:
                    # 이전 버전 호환성
                    record_id, param_name, default_value, min_spec, max_spec, occurrence_count = item[:6]
                    values = (
                        str(idx),  # 순차 번호
                        param_name or "",
                        "", "", "double",
                        str(default_value) if default_value is not None else "",
                        str(min_spec) if min_spec is not None else "",
                        str(max_spec) if max_spec is not None else "",
                        "No", ""
                    )
                    self.default_db_tree.insert("", "end", values=values, tags=(f"id_{record_id}",))
                    
            except Exception as e:
                self.update_log(f"⚠️ 항목 표시 중 오류: {e}")
                continue
        
        # 상태 업데이트
        total_count = len(default_values)
        performance_count = sum(1 for item in default_values if len(item) > 14 and item[14] == 1)
        
        self.default_db_status_label.config(text=f"총 {total_count}개 파라미터 로드됨")
        self.performance_stats_label.config(text=f"🎯 Check list: {performance_count}개")
        
        self.update_log(f"✅ Default DB 표시 업데이트 완료: {total_count}개 항목 (Check list: {performance_count}개)")

    def add_equipment_type_dialog(self):
        """새 장비 유형 추가 다이얼로그"""
        dlg = tk.Toplevel(self.window)
        dlg.title("새 장비 유형 추가")
        dlg.geometry("400x200")
        dlg.transient(self.window)
        dlg.grab_set()
        
        # 부모 창 중앙에 배치
        from app.loading import center_dialog_on_parent
        center_dialog_on_parent(dlg, self.window)
        
        ttk.Label(dlg, text="장비 유형 이름:").pack(pady=10)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dlg, textvariable=name_var, width=30)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        ttk.Label(dlg, text="설명 (선택사항):").pack(pady=10)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(dlg, textvariable=desc_var, width=50)
        desc_entry.pack(pady=5)
        
        def on_add():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("오류", "장비 유형 이름을 입력해주세요.")
                return
            
            try:
                type_id = self.db_schema.add_equipment_type(name, desc_var.get().strip())
                self.update_log(f"새 장비 유형 추가: {name} (ID: {type_id})")
                
                self.db_schema.log_change_history("add", "equipment_type", name, "", desc_var.get(), "admin")
                
                # 목록 새로고침
                self.refresh_equipment_types()
                
                # 새로 추가된 항목 선택
                type_names = self.equipment_type_combo['values']
                for type_name in type_names:
                    if f"ID: {type_id}" in type_name:
                        self.equipment_type_combo.set(type_name)
                        self.on_equipment_type_selected()
                        break
                
                dlg.destroy()
                messagebox.showinfo("성공", f"장비 유형 '{name}'이 추가되었습니다.")
                
            except Exception as e:
                messagebox.showerror("오류", f"장비 유형 추가 실패:\n{str(e)}")
        
        button_frame = ttk.Frame(dlg)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="추가", command=on_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=dlg.destroy).pack(side=tk.LEFT, padx=5)

    def delete_equipment_type(self):
        """선택된 장비 유형을 삭제합니다."""
        selected = self.equipment_type_var.get()
        if not selected:
            messagebox.showwarning("경고", "삭제할 장비 유형을 선택해주세요.")
            return
        
        type_name = selected.split(" (ID:")[0]
        type_id_str = selected.split("ID: ")[1][:-1]
        type_id = int(type_id_str)
        
        # 확인 다이얼로그
        result = messagebox.askyesno("확인", 
                                   f"장비 유형 '{type_name}'과 관련된 모든 파라미터를 삭제하시겠습니까?\n"
                                   f"이 작업은 되돌릴 수 없습니다.")
        
        if result:
            try:
                # 관련 파라미터 수 확인
                default_values = self.db_schema.get_default_values(type_id)
                param_count = len(default_values)
                
                # 삭제 실행
                success = self.db_schema.delete_equipment_type(type_id)
                
                if success:
                    self.update_log(f"장비 유형 삭제: {type_name} (파라미터 {param_count}개 포함)")
                    
                    self.db_schema.log_change_history("delete", "equipment_type", type_name, 
                                                    f"{param_count} parameters", "", "admin")
                    
                    # 🆕 전체 탭 동기화 - 모든 장비 유형 목록 새로고침
                    self.refresh_all_equipment_type_lists()
                    messagebox.showinfo("성공", f"장비 유형 '{type_name}'과 관련 파라미터 {param_count}개가 삭제되었습니다.")
                else:
                    messagebox.showerror("오류", "장비 유형 삭제에 실패했습니다.")
                    
            except Exception as e:
                messagebox.showerror("오류", f"장비 유형 삭제 중 오류:\n{str(e)}")

    def add_parameter_dialog(self):
        """새 파라미터 추가 다이얼로그"""
        if not self.maint_mode:
            messagebox.showwarning("권한 없음", "유지보수 모드에서만 파라미터를 추가할 수 있습니다.")
            return
            
        if not self.equipment_type_var.get():
            messagebox.showwarning("경고", "먼저 장비 유형을 선택해주세요.")
            return
        
        # 현재 선택된 장비 유형 ID 추출
        selected_type = self.equipment_type_var.get()
        if "ID: " not in selected_type:
            messagebox.showwarning("경고", "유효한 장비 유형을 선택해주세요.")
            return
        
        equipment_type_id = int(selected_type.split("ID: ")[1].split(")")[0])
        
        # 파라미터 추가 대화상자
        param_dialog = tk.Toplevel(self.window)
        param_dialog.title("파라미터 추가")
        param_dialog.geometry("450x420")
        param_dialog.transient(self.window)
        param_dialog.grab_set()
        
        # 부모 창 중앙에 배치
        param_dialog.geometry("450x420")
        param_dialog.update_idletasks()
        x = (param_dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (param_dialog.winfo_screenheight() // 2) - (420 // 2)
        param_dialog.geometry(f"450x420+{x}+{y}")

        param_frame = ttk.Frame(param_dialog, padding=10)
        param_frame.pack(fill=tk.BOTH, expand=True)

        # 파라미터 입력 필드
        def create_label_entry_pair(parent, label_text, row, initial_value=""):
            ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            var = tk.StringVar(value=initial_value)
            entry = ttk.Entry(parent, textvariable=var)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            return var, entry

        name_var, name_entry = create_label_entry_pair(param_frame, "파라미터명:", 0)
        module_var, module_entry = create_label_entry_pair(param_frame, "Module:", 1, "DSP")
        part_var, part_entry = create_label_entry_pair(param_frame, "Part:", 2)
        
        # ItemType 콤보박스
        ttk.Label(param_frame, text="데이터 타입:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        item_type_var = tk.StringVar()
        item_type_combo = ttk.Combobox(
            param_frame, 
            textvariable=item_type_var, 
            values=["double", "int", "string"], 
            state="readonly"
        )
        item_type_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        item_type_combo.set("double")  # 기본값
        
        default_var, default_entry = create_label_entry_pair(param_frame, "설정값:", 4)
        min_var, min_entry = create_label_entry_pair(param_frame, "최소값:", 5)
        max_var, max_entry = create_label_entry_pair(param_frame, "최대값:", 6)

        # 설명 필드 (여러 줄)
        ttk.Label(param_frame, text="설명:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        desc_text = tk.Text(param_frame, height=4, width=30)
        desc_text.grid(row=7, column=1, padx=5, pady=5, sticky="ew")

        # 열 너비 조정
        param_frame.columnconfigure(1, weight=1)

        # 버튼 프레임
        button_frame = ttk.Frame(param_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # 저장 함수
        def save_parameter():
            # 입력값 검증
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("오류", "파라미터명은 필수 입력 항목입니다.")
                return

            module_name = module_var.get().strip()
            part_name = part_var.get().strip()
            item_type = item_type_var.get()
            default_value = default_var.get().strip()

            # 숫자 입력값 변환
            try:
                min_value = float(min_var.get()) if min_var.get().strip() else None
                max_value = float(max_var.get()) if max_var.get().strip() else None
            except ValueError:
                messagebox.showerror("오류", "최소값과 최대값은 숫자여야 합니다.")
                return

            # 최소값/최대값 검증
            if min_value is not None and max_value is not None and min_value > max_value:
                messagebox.showerror("오류", "최소값이 최대값보다 클 수 없습니다.")
                return

            description = desc_text.get("1.0", tk.END).strip()

            try:
                # 중복 체크
                existing_params = self.db_schema.get_default_values(equipment_type_id)
                for param in existing_params:
                    if param[1] == name:  # parameter_name
                        messagebox.showerror("오류", "이미 존재하는 파라미터명입니다.")
                        return

                # 파라미터 추가
                record_id = self.db_schema.add_default_value(
                    equipment_type_id=equipment_type_id,
                    parameter_name=name,
                    default_value=default_value,
                    min_spec=min_value,
                    max_spec=max_value,
                    occurrence_count=1,
                    total_files=1,
                    source_files="Manual Entry",
                    description=description,
                    module_name=module_name,
                    part_name=part_name,
                    item_type=item_type
                )

                equipment_type_name = selected_type.split(" (ID:")[0]
                self.db_schema.log_change_history(
                    "add", "parameter", f"{equipment_type_name}_{name}", 
                    "", f"default: {default_value}, min: {min_value}, max: {max_value}", "admin"
                )

                # 대화상자 닫기
                param_dialog.destroy()

                # 파라미터 목록 갱신
                self.on_equipment_type_selected()

                # 로그 업데이트
                self.update_log(f"✅ 파라미터 추가 완료: {name} (장비유형: {equipment_type_name})")
                messagebox.showinfo("완료", f"파라미터 '{name}'이 성공적으로 추가되었습니다.")

            except Exception as e:
                messagebox.showerror("오류", f"파라미터 추가 중 오류 발생: {str(e)}")
                self.update_log(f"❌ 파라미터 추가 오류: {str(e)}")

        # 버튼 추가
        ttk.Button(button_frame, text="저장", command=save_parameter).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=param_dialog.destroy).pack(side=tk.RIGHT, padx=5)

        # 첫 번째 필드에 포커스
        name_entry.focus_set()

    def delete_selected_parameters(self):
        """선택된 파라미터들을 삭제합니다."""
        if not self.maint_mode:
            messagebox.showwarning("권한 없음", "유지보수 모드에서만 파라미터를 삭제할 수 있습니다.")
            return
            
        selected_items = self.default_db_tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "삭제할 파라미터를 선택해주세요.")
            return

        # 선택된 파라미터 정보 수집
        param_names = []
        param_ids = []
        
        for item in selected_items:
            # 실제 DB ID를 tags에서 가져오기
            db_id = self.get_db_id_from_item(item)
            if db_id is not None:
                param_ids.append(db_id)
                
                values = self.default_db_tree.item(item, 'values')
                if values and len(values) > 1:
                    param_names.append(values[1])  # 파라미터명
                else:
                    param_names.append(f"ID_{db_id}")

        if not param_ids:
            messagebox.showwarning("경고", "삭제할 파라미터 정보를 찾을 수 없습니다.")
            return

        # 삭제 확인
        if len(param_names) == 1:
            confirm_msg = f"파라미터 '{param_names[0]}'을(를) 삭제하시겠습니까?\n\n주의: 관련된 모든 데이터가 함께 삭제됩니다!"
        else:
            param_list = '\n'.join([f"• {name}" for name in param_names])
            confirm_msg = f"다음 {len(param_names)}개 파라미터를 삭제하시겠습니까?\n\n{param_list}\n\n주의: 관련된 모든 데이터가 함께 삭제됩니다!"

        confirm = messagebox.askyesno("삭제 확인", confirm_msg)
        if not confirm:
            return

        try:
            # 파라미터 삭제 실행
            success_count = 0
            failed_params = []
            
            for i, param_id in enumerate(param_ids):
                try:
                    # DB에서 파라미터 삭제
                    success = self.db_schema.delete_default_value(param_id)
                    if success:
                        success_count += 1
                        
                        equipment_type_name = self.equipment_type_var.get().split(" (ID:")[0]
                        self.db_schema.log_change_history(
                            "delete", "parameter", f"{equipment_type_name}_{param_names[i]}", 
                            "deleted", "", "admin"
                        )
                        
                        self.update_log(f"✅ 파라미터 삭제 완료: {param_names[i]}")
                    else:
                        failed_params.append(param_names[i])
                        self.update_log(f"❌ 파라미터 삭제 실패: {param_names[i]}")
                        
                except Exception as e:
                    failed_params.append(param_names[i])
                    self.update_log(f"❌ 파라미터 삭제 오류: {param_names[i]} - {str(e)}")

            # 결과 메시지 표시
            if success_count > 0:
                if failed_params:
                    messagebox.showwarning(
                        "부분 완료", 
                        f"{success_count}개 파라미터가 삭제되었습니다.\n"
                        f"실패한 파라미터: {', '.join(failed_params)}"
                    )
                else:
                    messagebox.showinfo("완료", f"{success_count}개 파라미터가 성공적으로 삭제되었습니다.")
                
                # 파라미터 목록 갱신
                self.on_equipment_type_selected()
            else:
                messagebox.showerror("오류", "파라미터 삭제에 실패했습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"파라미터 삭제 중 오류 발생: {str(e)}")
            self.update_log(f"❌ 파라미터 삭제 중 오류: {str(e)}")

    def edit_parameter_dialog(self, event):
        """파라미터 편집 다이얼로그"""
        if not self.maint_mode:
            messagebox.showwarning("권한 없음", "유지보수 모드에서만 파라미터를 편집할 수 있습니다.")
            return
            
        selected_items = self.default_db_tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "편집할 파라미터를 선택해주세요.")
            return

        # 첫 번째 선택된 항목만 편집
        selected_item = selected_items[0]
        
        # 실제 DB ID를 tags에서 가져오기
        param_id = self.get_db_id_from_item(selected_item)
        if param_id is None:
            messagebox.showerror("오류", "파라미터 ID를 찾을 수 없습니다.")
            return
        
        try:
            # 파라미터 정보 조회
            param_data = self.db_schema.get_parameter_by_id(param_id)
            if not param_data:
                messagebox.showerror("오류", "파라미터 정보를 찾을 수 없습니다.")
                return

            # 파라미터 수정 대화상자
            param_dialog = tk.Toplevel(self.window)
            param_dialog.title("파라미터 수정")
            param_dialog.geometry("450x420")
            param_dialog.transient(self.window)
            param_dialog.grab_set()

            # 부모 창 중앙에 배치
            param_dialog.update_idletasks()
            x = (param_dialog.winfo_screenwidth() // 2) - (450 // 2)
            y = (param_dialog.winfo_screenheight() // 2) - (420 // 2)
            param_dialog.geometry(f"450x420+{x}+{y}")

            param_frame = ttk.Frame(param_dialog, padding=10)
            param_frame.pack(fill=tk.BOTH, expand=True)

            # 파라미터 입력 필드
            def create_label_entry_pair(parent, label_text, row, initial_value=""):
                ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky="w")
                var = tk.StringVar(value=initial_value)
                entry = ttk.Entry(parent, textvariable=var)
                entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
                return var, entry

            # 기존 데이터로 필드 초기화
            name_var, name_entry = create_label_entry_pair(param_frame, "파라미터명:", 0, param_data.get('parameter_name', ''))
            module_var, module_entry = create_label_entry_pair(param_frame, "Module:", 1, param_data.get('module_name', ''))
            part_var, part_entry = create_label_entry_pair(param_frame, "Part:", 2, param_data.get('part_name', ''))
            
            # ItemType 콤보박스
            ttk.Label(param_frame, text="데이터 타입:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
            item_type_var = tk.StringVar()
            item_type_combo = ttk.Combobox(
                param_frame, 
                textvariable=item_type_var, 
                values=["double", "int", "string"], 
                state="readonly"
            )
            item_type_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
            item_type_combo.set(param_data.get('item_type', 'double'))

            default_var, default_entry = create_label_entry_pair(param_frame, "설정값:", 4, param_data.get('default_value', ''))
            min_var, min_entry = create_label_entry_pair(param_frame, "최소값:", 5, str(param_data.get('min_spec', '')) if param_data.get('min_spec') is not None else '')
            max_var, max_entry = create_label_entry_pair(param_frame, "최대값:", 6, str(param_data.get('max_spec', '')) if param_data.get('max_spec') is not None else '')

            # 설명 필드 (여러 줄)
            ttk.Label(param_frame, text="설명:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
            desc_text = tk.Text(param_frame, height=4, width=30)
            desc_text.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
            desc_text.insert("1.0", param_data.get('description', ''))

            # 열 너비 조정
            param_frame.columnconfigure(1, weight=1)

            # 버튼 프레임
            button_frame = ttk.Frame(param_dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)

            # 저장 함수
            def save_parameter():
                # 입력값 검증
                new_name = name_var.get().strip()
                if not new_name:
                    messagebox.showerror("오류", "파라미터명은 필수 입력 항목입니다.")
                    return

                new_module_name = module_var.get().strip()
                new_part_name = part_var.get().strip()
                new_item_type = item_type_var.get()
                new_default_value = default_var.get().strip()

                # 숫자 입력값 변환
                try:
                    new_min_value = float(min_var.get()) if min_var.get().strip() else None
                    new_max_value = float(max_var.get()) if max_var.get().strip() else None
                except ValueError:
                    messagebox.showerror("오류", "최소값과 최대값은 숫자여야 합니다.")
                    return

                # 최소값/최대값 검증
                if new_min_value is not None and new_max_value is not None and new_min_value > new_max_value:
                    messagebox.showerror("오류", "최소값이 최대값보다 클 수 없습니다.")
                    return

                new_description = desc_text.get("1.0", tk.END).strip()

                try:
                    # 이름이 변경된 경우 중복 체크
                    if new_name != param_data.get('parameter_name'):
                        equipment_type_id = int(self.equipment_type_var.get().split("ID: ")[1].split(")")[0])
                        existing_params = self.db_schema.get_default_values(equipment_type_id)
                        for param in existing_params:
                            if param[1] == new_name and param[0] != param_id:  # parameter_name, id
                                messagebox.showerror("오류", "이미 존재하는 파라미터명입니다.")
                                return

                    # 파라미터 수정
                    success = self.db_schema.update_default_value(
                        record_id=param_id,
                        parameter_name=new_name,
                        default_value=new_default_value,
                        min_spec=new_min_value,
                        max_spec=new_max_value,
                        description=new_description,
                        module_name=new_module_name,
                        part_name=new_part_name,
                        item_type=new_item_type
                    )

                    if success:
                        equipment_type_name = self.equipment_type_var.get().split(" (ID:")[0]
                        old_name = param_data.get('parameter_name', '')
                        self.db_schema.log_change_history(
                            "update", "parameter", f"{equipment_type_name}_{old_name}", 
                            f"old: {old_name}", f"new: {new_name}, default: {new_default_value}", "admin"
                        )

                        # 대화상자 닫기
                        param_dialog.destroy()

                        # 파라미터 목록 갱신
                        self.on_equipment_type_selected()

                        # 로그 업데이트
                        self.update_log(f"✅ 파라미터 수정 완료: {old_name} → {new_name}")
                        messagebox.showinfo("완료", f"파라미터 '{new_name}'이 성공적으로 수정되었습니다.")
                    else:
                        messagebox.showerror("오류", "파라미터 수정에 실패했습니다.")

                except Exception as e:
                    messagebox.showerror("오류", f"파라미터 수정 중 오류 발생: {str(e)}")
                    self.update_log(f"❌ 파라미터 수정 오류: {str(e)}")

            # 버튼 추가
            ttk.Button(button_frame, text="저장", command=save_parameter).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="취소", command=param_dialog.destroy).pack(side=tk.RIGHT, padx=5)

            # 첫 번째 필드에 포커스
            name_entry.focus_set()

        except Exception as e:
            messagebox.showerror("오류", f"파라미터 정보 로드 중 오류 발생: {str(e)}")
            self.update_log(f"❌ 파라미터 편집 오류: {str(e)}")

    def export_default_db_to_excel(self):
        """Default DB를 Excel로 내보내기"""
        # defaultdb.py의 export_to_excel 기능 호출
        if hasattr(self, 'export_to_excel'):
            self.export_to_excel()
        else:
            messagebox.showinfo("개발 중", "Excel 내보내기 기능은 개발 중입니다.")

    def import_default_db_from_excel(self):
        """Excel에서 Default DB 가져오기"""
        # defaultdb.py의 import_from_excel 기능 호출
        if hasattr(self, 'import_from_excel'):
            self.import_from_excel()
        else:
            messagebox.showinfo("개발 중", "Excel 가져오기 기능은 개발 중입니다.")
    
    def import_from_text_file(self):
        """텍스트 파일에서 Default DB 가져오기 (원본 형식 지원)"""
        try:
            # 파일 선택 대화상자
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="텍스트 파일에서 가져오기",
                filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
            )
            
            if not file_path:
                return
            
            # 파일 읽기 및 파싱
            imported_data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                messagebox.showwarning("경고", "파일이 비어있습니다.")
                return
            
            # 헤더 확인
            header = lines[0].strip().split('\t')
            expected_header = ['Module', 'Part', 'ItemName', 'ItemType', 'ItemValue', 'ItemDescription']
            
            if header != expected_header:
                messagebox.showwarning("경고", 
                    f"파일 형식이 올바르지 않습니다.\n"
                    f"예상 헤더: {expected_header}\n"
                    f"실제 헤더: {header}")
                return
            
            # 데이터 파싱
            for line_num, line in enumerate(lines[1:], 2):
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) != 6:
                    messagebox.showwarning("경고", f"라인 {line_num}: 컬럼 개수가 맞지 않습니다.")
                    continue
                
                imported_data.append({
                    'module': parts[0],
                    'part': parts[1],
                    'item_name': parts[2],
                    'item_type': parts[3],
                    'item_value': parts[4],
                    'item_description': parts[5]
                })
            
            if not imported_data:
                messagebox.showinfo("알림", "가져올 데이터가 없습니다.")
                return
            
            # 장비 유형 선택/생성 대화상자
            import os
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # 간단한 장비 유형 입력 대화상자
            type_dialog = tk.Toplevel(self.window)
            type_dialog.title("장비 유형 선택")
            type_dialog.geometry("400x200")
            type_dialog.transient(self.window)
            type_dialog.grab_set()
            
            ttk.Label(type_dialog, text="장비 유형명을 입력하세요:").pack(pady=10)
            
            type_var = tk.StringVar(value=file_name)
            type_entry = ttk.Entry(type_dialog, textvariable=type_var, width=40)
            type_entry.pack(pady=5)
            
            result = {'confirmed': False, 'type_name': ''}
            
            def on_ok():
                if type_var.get().strip():
                    result['confirmed'] = True
                    result['type_name'] = type_var.get().strip()
                    type_dialog.destroy()
                else:
                    messagebox.showwarning("경고", "장비 유형명을 입력해주세요.")
            
            def on_cancel():
                type_dialog.destroy()
            
            ttk.Button(type_dialog, text="확인", command=on_ok).pack(side=tk.LEFT, padx=20, pady=20)
            ttk.Button(type_dialog, text="취소", command=on_cancel).pack(side=tk.RIGHT, padx=20, pady=20)
            
            type_dialog.wait_window()
            
            if not result['confirmed']:
                return
            
            # 장비 유형 추가/확인
            type_name = result['type_name']
            type_id = self.db_schema.add_equipment_type(
                type_name, 
                f"텍스트 파일에서 가져옴: {os.path.basename(file_path)}"
            )
            
            # 데이터 추가
            added_count = 0
            updated_count = 0
            error_count = 0
            
            for data in imported_data:
                try:
                    param_name = data['item_name']  # ItemName만 사용하여 통일
                    
                    # 기존 파라미터 확인
                    existing = self.db_schema.get_parameter_statistics(type_id, param_name)
                    
                    record_id = self.db_schema.add_default_value(
                        equipment_type_id=type_id,
                        parameter_name=param_name,
                        default_value=data['item_value'],
                        min_spec=None,
                        max_spec=None,
                        occurrence_count=1,
                        total_files=1,
                        source_files=os.path.basename(file_path),
                        description=data['item_description'],
                        module_name=data['module'],
                        part_name=data['part'],
                        item_type=data['item_type']
                    )
                    
                    if existing:
                        updated_count += 1
                    else:
                        added_count += 1
                        
                except Exception as e:
                    error_count += 1
                    self.update_log(f"파라미터 '{param_name}' 추가 실패: {str(e)}")
            
            # 결과 메시지
            messagebox.showinfo(
                "✅ 가져오기 완료",
                f"텍스트 파일에서 Default DB로 성공적으로 가져왔습니다.\n\n"
                f"📄 파일: {os.path.basename(file_path)}\n"
                f"🏷️ 장비 유형: {type_name}\n"
                f"✅ 새로 추가: {added_count}개\n"
                f"🔄 업데이트: {updated_count}개\n"
                f"❌ 오류: {error_count}개"
            )
            
            # UI 업데이트
            if hasattr(self, 'refresh_equipment_types'):
                self.refresh_equipment_types()
                # 방금 추가한 장비 유형 선택
                if hasattr(self, 'equipment_type_combo'):
                    type_names = self.equipment_type_combo['values']
                    for type_option in type_names:
                        if f"ID: {type_id}" in type_option:
                            self.equipment_type_combo.set(type_option)
                            if hasattr(self, 'on_equipment_type_selected'):
                                self.on_equipment_type_selected()
                            break
            
            self.update_log(f"텍스트 파일 가져오기 완료: {file_path} (추가 {added_count}개, 업데이트 {updated_count}개)")
            
        except Exception as e:
            messagebox.showerror("❌ 오류", f"텍스트 파일 가져오기 중 오류 발생:\n{str(e)}")
            self.update_log(f"텍스트 파일 가져오기 오류: {str(e)}")
    
    def export_to_text_file(self):
        """Default DB를 텍스트 파일로 내보내기"""
        try:
            print("DEBUG: export_to_text_file 함수 시작")
            
            if not hasattr(self, 'equipment_type_combo') or not self.equipment_type_combo.get():
                messagebox.showwarning("경고", "먼저 장비 유형을 선택해주세요.")
                return
            
            # 현재 선택된 장비 유형 ID 추출
            selected_type = self.equipment_type_combo.get()
            print(f"DEBUG: Selected type: {selected_type}")
            
            if "ID: " not in selected_type:
                messagebox.showwarning("경고", "유효한 장비 유형을 선택해주세요.")
                return
            
            type_id = int(selected_type.split("ID: ")[1].split(")")[0])
            type_name = selected_type.split(" (ID:")[0]
            print(f"DEBUG: type_id: {type_id}, type_name: {type_name}")
            
            # 파일 저장 대화상자
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="텍스트 파일로 내보내기",
                defaultextension=".txt",
                filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
            )
            
            if not file_path:
                print("DEBUG: 파일 경로가 선택되지 않음")
                return
            
            print(f"DEBUG: 선택된 파일 경로: {file_path}")
            
            # text_file_handler 초기화
            if not hasattr(self, 'text_file_handler'):
                from app.text_file_handler import TextFileHandler
                self.text_file_handler = TextFileHandler(self.db_schema)
            
            # text_file_handler를 사용한 내보내기
            print("DEBUG: text_file_handler를 사용한 내보내기 시작")
            success, message = self.text_file_handler.export_to_text_file(type_id, file_path)
            
            if success:
                messagebox.showinfo("✅ 내보내기 완료", message)
                self.update_log(f"텍스트 파일 내보내기 완료: {file_path}")
            else:
                messagebox.showerror("❌ 오류", message)
                self.update_log(f"텍스트 파일 내보내기 오류: {message}")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"DEBUG: export_to_text_file 오류:\n{error_details}")
            messagebox.showerror("❌ 오류", f"텍스트 파일 내보내기 중 오류 발생:\n{str(e)}")
            self.update_log(f"텍스트 파일 내보내기 오류: {str(e)}")


    def get_duplicate_analysis(self, selected_items):
        """
        선택된 항목들의 중복 상태를 분석합니다.
        강화된 중복 검사 기능으로 잠재적 중복까지 감지합니다.
        
        Args:
            selected_items: 선택된 트리뷰 아이템 ID 리스트
            
        Returns:
            dict: 중복 분석 결과
        """
        duplicate_analysis = {
            'existing_in_db': [],      # 이미 DB에 존재하는 항목
            'potential_duplicates': [], # 비슷한 이름의 잠재적 중복
            'new_parameters': [],       # 완전히 새로운 파라미터
            'conflict_analysis': {},    # 값 충돌 분석
            'summary': {}              # 요약 정보
        }
        
        # 기존 Default DB의 모든 파라미터 목록 가져오기
        existing_params = {}
        try:
            default_values = self.db_schema.get_default_values()
            for record in default_values:
                param_name = record[1]  # parameter_name
                default_value = record[2]  # default_value
                equipment_type = record[5]  # type_name
                existing_params[param_name] = {
                    'value': default_value,
                    'equipment_type': equipment_type,
                    'record': record
                }
        except Exception as e:
            self.update_log(f"기존 파라미터 조회 오류: {e}")
            return duplicate_analysis
        
        for item_id in selected_items:
            item_values = self.comparison_tree.item(item_id, "values")
            
            # 유지보수 모드 여부에 따라 인덱스 조정
            col_offset = 1 if self.maint_mode else 0
            module, part, item_name = item_values[col_offset], item_values[col_offset+1], item_values[col_offset+2]
            
            param_name = item_name  # ItemName만 사용하여 통일
            current_value = item_values[col_offset+3] if len(item_values) > col_offset+3 else ""
            
            # 1. 정확한 이름 매칭 검사
            if param_name in existing_params:
                existing_record = existing_params[param_name]
                duplicate_analysis['existing_in_db'].append({
                    'param_name': param_name,
                    'current_value': current_value,
                    'existing_value': existing_record['value'],
                    'equipment_type': existing_record['equipment_type'],
                    'value_match': str(current_value).strip() == str(existing_record['value']).strip()
                })
                
                # 값 충돌 분석
                if str(current_value).strip() != str(existing_record['value']).strip():
                    duplicate_analysis['conflict_analysis'][param_name] = {
                        'current_value': current_value,
                        'existing_value': existing_record['value'],
                        'equipment_type': existing_record['equipment_type']
                    }
            else:
                # 2. 유사한 이름 검사 (잠재적 중복)
                similar_params = []
                for existing_param in existing_params.keys():
                    # 레벤슈타인 거리 계산
                    similarity = calculate_string_similarity(param_name, existing_param)
                    if similarity > 0.8:  # 80% 이상 유사
                        similar_params.append({
                            'existing_param': existing_param,
                            'similarity': similarity,
                            'existing_value': existing_params[existing_param]['value'],
                            'equipment_type': existing_params[existing_param]['equipment_type']
                        })
                
                if similar_params:
                    duplicate_analysis['potential_duplicates'].append({
                        'param_name': param_name,
                        'current_value': current_value,
                        'similar_params': sorted(similar_params, key=lambda x: x['similarity'], reverse=True)
                    })
                else:
                    # 3. 완전히 새로운 파라미터
                    duplicate_analysis['new_parameters'].append({
                        'param_name': param_name,
                        'current_value': current_value,
                        'module': module,
                        'part': part,
                        'item_name': item_name
                    })
        
        # 요약 정보 생성
        duplicate_analysis['summary'] = {
            'total_selected': len(selected_items),
            'exact_duplicates': len(duplicate_analysis['existing_in_db']),
            'potential_duplicates': len(duplicate_analysis['potential_duplicates']),
            'new_parameters': len(duplicate_analysis['new_parameters']),
            'value_conflicts': len(duplicate_analysis['conflict_analysis']),
            'safe_to_add': len(duplicate_analysis['new_parameters'])
        }
        
        return duplicate_analysis


    def show_duplicate_analysis_dialog(self, duplicate_analysis):
        """
        중복 분석 결과를 보여주는 다이얼로그를 표시합니다.
        
        Args:
            duplicate_analysis: get_duplicate_analysis 결과
        """
        dlg = tk.Toplevel(self.window)
        dlg.title("🔍 중복 검사 결과")
        dlg.geometry("900x700")
        dlg.transient(self.window)
        dlg.grab_set()
        
        # 요약 정보 표시
        summary_frame = ttk.LabelFrame(dlg, text="📊 요약", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        summary = duplicate_analysis['summary']
        summary_text = (f"선택된 항목: {summary['total_selected']}개 | "
                       f"정확 중복: {summary['exact_duplicates']}개 | "
                       f"잠재 중복: {summary['potential_duplicates']}개 | "
                       f"새 파라미터: {summary['new_parameters']}개 | "
                       f"값 충돌: {summary['value_conflicts']}개")
        
        ttk.Label(summary_frame, text=summary_text, font=("", 10, "bold")).pack()
        
        # 탭 구성
        notebook = ttk.Notebook(dlg)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. 기존 DB 중복 탭
        existing_frame = ttk.Frame(notebook)
        notebook.add(existing_frame, text=f"🔴 기존 DB 중복 ({len(duplicate_analysis['existing_in_db'])}개)")
        
        if duplicate_analysis['existing_in_db']:
            existing_text = tk.Text(existing_frame, wrap=tk.WORD, font=("Consolas", 9))
            existing_scroll = ttk.Scrollbar(existing_frame, orient="vertical", command=existing_text.yview)
            existing_text.configure(yscrollcommand=existing_scroll.set)
            
            existing_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            existing_text.pack(fill=tk.BOTH, expand=True)
            
            existing_text.insert(tk.END, "⚠️ 다음 파라미터들이 이미 Default DB에 존재합니다:\n\n")
            
            for item in duplicate_analysis['existing_in_db']:
                status = "✅ 값 일치" if item['value_match'] else "❌ 값 불일치"
                status_color = "✅" if item['value_match'] else "🔥"
                
                existing_text.insert(tk.END, f"{status_color} {item['param_name']}\n")
                existing_text.insert(tk.END, f"   현재 값: {item['current_value']}\n")
                existing_text.insert(tk.END, f"   DB 저장값: {item['existing_value']}\n")
                existing_text.insert(tk.END, f"   장비 유형: {item['equipment_type']}\n")
                existing_text.insert(tk.END, f"   상태: {status}\n")
                
                if not item['value_match']:
                    existing_text.insert(tk.END, f"   ⚠️ 주의: 값이 다릅니다! 기존 값을 덮어쓸지 검토 필요\n")
                existing_text.insert(tk.END, "\n")
        else:
            ttk.Label(existing_frame, text="✅ 기존 DB와 정확히 일치하는 중복 항목이 없습니다.", 
                     font=("", 12)).pack(expand=True)
        
        # 2. 잠재적 중복 탭
        potential_frame = ttk.Frame(notebook)
        notebook.add(potential_frame, text=f"🟡 잠재적 중복 ({len(duplicate_analysis['potential_duplicates'])}개)")
        
        if duplicate_analysis['potential_duplicates']:
            potential_text = tk.Text(potential_frame, wrap=tk.WORD, font=("Consolas", 9))
            potential_scroll = ttk.Scrollbar(potential_frame, orient="vertical", command=potential_text.yview)
            potential_text.configure(yscrollcommand=potential_scroll.set)
            
            potential_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            potential_text.pack(fill=tk.BOTH, expand=True)
            
            potential_text.insert(tk.END, "🔍 유사한 이름의 파라미터들이 발견되었습니다:\n")
            potential_text.insert(tk.END, "이들은 실제로는 같은 파라미터일 가능성이 있습니다.\n\n")
            
            for item in duplicate_analysis['potential_duplicates']:
                potential_text.insert(tk.END, f"🟡 새 파라미터: {item['param_name']}\n")
                potential_text.insert(tk.END, f"   값: {item['current_value']}\n")
                potential_text.insert(tk.END, f"   유사한 기존 파라미터들:\n")
                
                for similar in item['similar_params']:
                    similarity_bar = "█" * int(similar['similarity'] * 10)
                    potential_text.insert(tk.END, f"      • {similar['existing_param']}\n")
                    potential_text.insert(tk.END, f"        유사도: {similar['similarity']*100:.1f}% {similarity_bar}\n")
                    potential_text.insert(tk.END, f"        기존 값: {similar['existing_value']}\n")
                    potential_text.insert(tk.END, f"        장비 유형: {similar['equipment_type']}\n")
                potential_text.insert(tk.END, "\n")
        else:
            ttk.Label(potential_frame, text="✅ 유사한 이름의 잠재적 중복 항목이 없습니다.", 
                     font=("", 12)).pack(expand=True)
        
        # 3. 새로운 파라미터 탭
        new_frame = ttk.Frame(notebook)
        notebook.add(new_frame, text=f"🟢 새 파라미터 ({len(duplicate_analysis['new_parameters'])}개)")
        
        if duplicate_analysis['new_parameters']:
            new_text = tk.Text(new_frame, wrap=tk.WORD, font=("Consolas", 9))
            new_scroll = ttk.Scrollbar(new_frame, orient="vertical", command=new_text.yview)
            new_text.configure(yscrollcommand=new_scroll.set)
            
            new_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            new_text.pack(fill=tk.BOTH, expand=True)
            
            new_text.insert(tk.END, "✨ 완전히 새로운 파라미터들입니다:\n")
            new_text.insert(tk.END, "이들은 안전하게 Default DB에 추가할 수 있습니다.\n\n")
            
            for item in duplicate_analysis['new_parameters']:
                new_text.insert(tk.END, f"✅ {item['param_name']}\n")
                new_text.insert(tk.END, f"   값: {item['current_value']}\n")
                new_text.insert(tk.END, f"   모듈: {item['module']}\n")
                new_text.insert(tk.END, f"   파트: {item['part']}\n")
                new_text.insert(tk.END, f"   항목명: {item['item_name']}\n\n")
        else:
            ttk.Label(new_frame, text="ℹ️ 새로운 파라미터가 없습니다.", 
                     font=("", 12)).pack(expand=True)
        
        # 4. 권장사항 탭 (새로 추가)
        recommend_frame = ttk.Frame(notebook)
        notebook.add(recommend_frame, text="💡 권장사항")
        
        recommend_text = tk.Text(recommend_frame, wrap=tk.WORD, font=("", 10))
        recommend_scroll = ttk.Scrollbar(recommend_frame, orient="vertical", command=recommend_text.yview)
        recommend_text.configure(yscrollcommand=recommend_scroll.set)
        
        recommend_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        recommend_text.pack(fill=tk.BOTH, expand=True)
        
        # 권장사항 생성
        recommend_text.insert(tk.END, "📋 중복 검사 기반 권장사항\n\n")
        
        if summary['exact_duplicates'] > 0:
            recommend_text.insert(tk.END, f"🔴 정확한 중복 항목 ({summary['exact_duplicates']}개):\n")
            if summary['value_conflicts'] > 0:
                recommend_text.insert(tk.END, f"   • {summary['value_conflicts']}개 항목에서 값 충돌 발견\n")
                recommend_text.insert(tk.END, f"   • 기존 값을 덮어쓸지 신중히 검토하세요\n")
                recommend_text.insert(tk.END, f"   • 통계 기반 분석을 활용하여 신뢰도가 높은 값을 선택하세요\n")
            else:
                recommend_text.insert(tk.END, f"   • 모든 값이 일치하므로 안전하게 진행 가능합니다\n")
            recommend_text.insert(tk.END, "\n")
        
        if summary['potential_duplicates'] > 0:
            recommend_text.insert(tk.END, f"🟡 잠재적 중복 항목 ({summary['potential_duplicates']}개):\n")
            recommend_text.insert(tk.END, f"   • 파라미터 이름을 검토하여 실제 중복인지 확인하세요\n")
            recommend_text.insert(tk.END, f"   • 동일한 파라미터라면 기존 이름으로 통일을 권장합니다\n")
            recommend_text.insert(tk.END, f"   • 다른 파라미터라면 그대로 추가해도 됩니다\n\n")
        
        if summary['new_parameters'] > 0:
            recommend_text.insert(tk.END, f"🟢 새로운 파라미터 ({summary['new_parameters']}개):\n")
            recommend_text.insert(tk.END, f"   • 안전하게 Default DB에 추가할 수 있습니다\n")
            recommend_text.insert(tk.END, f"   • 통계 기반 분석으로 신뢰도 높은 기준값을 설정하세요\n\n")
        
        # 전체 권장사항
        recommend_text.insert(tk.END, "💡 전체 권장사항:\n")
        recommend_text.insert(tk.END, "1. 통계 기반 분석을 활용하여 중복도가 높은 값을 기준값으로 선택\n")
        recommend_text.insert(tk.END, "2. 신뢰도 임계값을 적절히 설정 (50% 이상 권장)\n")
        recommend_text.insert(tk.END, "3. 값 충돌이 있는 경우 수동으로 검토 후 결정\n")
        recommend_text.insert(tk.END, "4. 잠재적 중복은 파라미터 명명 규칙을 통일하여 해결\n")
        
        # 버튼 프레임
        button_frame = ttk.Frame(dlg)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="닫기", command=dlg.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 중복 해결 버튼 (추후 기능 확장용)
        if summary['potential_duplicates'] > 0 or summary['value_conflicts'] > 0:
            ttk.Button(button_frame, text="중복 해결 마법사", 
                      command=lambda: self.show_duplicate_resolution_wizard(duplicate_analysis)).pack(side=tk.LEFT, padx=5)

    def show_duplicate_resolution_wizard(self, duplicate_analysis):
        """
        중복 해결을 도와주는 마법사 다이얼로그 (추후 확장 기능)
        
        Args:
            duplicate_analysis: 중복 분석 결과
        """
        messagebox.showinfo("개발 중", "중복 해결 마법사는 추후 버전에서 제공될 예정입니다.\n\n"
                                      "현재는 수동으로 중복을 검토하고 해결해주세요.")

    # 🎯 2단계-C: 개선된 메뉴 시스템 메서드들
    def create_enhanced_menu(self):
        """개선된 사용자 역할별 메뉴 생성"""
        menubar = tk.Menu(self.window)
        
        # 🎯 파일 메뉴 - 모든 사용자 공통
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="📁 폴더 열기 (Ctrl+O)", command=self.load_folder)
        file_menu.add_separator()
        file_menu.add_command(label="📊 보고서 내보내기", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 종료", command=self.window.quit)
        menubar.add_cascade(label="파일", menu=file_menu)
        
        # 🎯 분석 메뉴 - 장비 생산 엔지니어 기본 기능
        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(label="🔍 DB 비교 분석", command=lambda: self.main_notebook.select(0))
        analysis_menu.add_separator()
        analysis_menu.add_command(label="📈 통계 분석", command=self.show_statistics_summary)
        analysis_menu.add_command(label="🔄 데이터 새로고침", command=self.refresh_all_data)
        menubar.add_cascade(label="분석", menu=analysis_menu)
        
        # 🎯 QC 관리 메뉴 - QC 엔지니어 전용 (동적 활성화)
        self.qc_menu = tk.Menu(menubar, tearoff=0)
        self.qc_menu.add_command(label="🔍 QC 검수", command=self.goto_qc_check_tab, state="disabled")
        self.qc_menu.add_command(label="🗄️ Default DB 관리", command=self.goto_default_db_tab, state="disabled")
        self.qc_menu.add_separator()
        self.qc_menu.add_command(label="📤 데이터 내보내기", command=self.export_qc_data, state="disabled")
        self.qc_menu.add_command(label="📥 데이터 가져오기", command=self.import_qc_data, state="disabled")
        
        # 🎯 도구 메뉴 - 시스템 설정
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="👤 사용자 모드 전환", command=self.toggle_maint_mode)

        menubar.add_cascade(label="도구", menu=tools_menu)
        
        # 🎯 도움말 메뉴
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="📖 사용 설명서 (F1)", command=self.show_user_guide)
        help_menu.add_command(label="🆘 문제 해결", command=self.show_troubleshooting_guide)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ 프로그램 정보", command=self.show_about)
        menubar.add_cascade(label="도움말", menu=help_menu)
        
        self.window.config(menu=menubar)
        return menubar

    def update_enhanced_menu_state(self):
        """개선된 메뉴 상태 업데이트"""
        if hasattr(self, 'qc_menu'):
            if self.maint_mode:
                self._enable_qc_menu()
            else:
                self._disable_qc_menu()

    def _enable_qc_menu(self):
        """QC 메뉴 활성화"""
        try:
            # QC 메뉴를 메뉴바에 추가 (도구 메뉴 앞에)
            current_menubar = self.window['menu']
            if current_menubar:
                # QC 관리 메뉴가 이미 있는지 확인
                menu_found = False
                try:
                    for i in range(20):  # 충분한 범위로 검색
                        try:
                            label = current_menubar.entrycget(i, 'label')
                            if label == "QC 관리":
                                menu_found = True
                                break
                        except:
                            break
                except:
                    pass
                
                if not menu_found:
                    # 도구 메뉴 앞에 QC 관리 메뉴 삽입
                    try:
                        current_menubar.insert_cascade(2, label="QC 관리", menu=self.qc_menu)
                    except:
                        current_menubar.add_cascade(label="QC 관리", menu=self.qc_menu)
            
            # QC 메뉴 항목들 활성화
            for i in range(self.qc_menu.index('end') + 1):
                try:
                    self.qc_menu.entryconfig(i, state="normal")
                except:
                    pass
                    
        except Exception as e:
            self.update_log(f"QC 메뉴 활성화 중 오류: {e}")

    def _disable_qc_menu(self):
        """QC 메뉴 비활성화"""
        try:
            # QC 메뉴 항목들 비활성화
            if hasattr(self, 'qc_menu'):
                for i in range(self.qc_menu.index('end') + 1):
                    try:
                        self.qc_menu.entryconfig(i, state="disabled")
                    except:
                        pass
            
            # QC 메뉴를 메뉴바에서 제거
            current_menubar = self.window['menu']
            if current_menubar:
                try:
                    for i in range(20):  # 충분한 범위로 검색
                        try:
                            label = current_menubar.entrycget(i, 'label')
                            if label == "QC 관리":
                                current_menubar.delete(i)
                                break
                        except:
                            break
                except:
                    pass
                    
        except Exception as e:
            self.update_log(f"QC 메뉴 비활성화 중 오류: {e}")

    def get_current_mode_display(self) -> str:
        """현재 모드 표시 문자열 반환"""
        if self.maint_mode:
            return "👤 QC 엔지니어 모드"
        else:
            return "👤 장비 생산 엔지니어 모드"

    def force_refresh_all_equipment_types(self):
        """모든 탭의 장비 유형 목록을 강제로 새로고침 (추가/삭제 후 호출용)"""
        try:
            self.update_log("🔄 강제 새로고침: 모든 탭 동기화 시작...")
            
            # 1. 기본 새로고침 실행
            self.refresh_equipment_types()
            
            # 2. QC 탭 강제 갱신
            if hasattr(self, 'load_equipment_types_for_qc'):
                try:
                    self.load_equipment_types_for_qc()
                    self.update_log("✅ QC 탭 강제 갱신 완료")
                except Exception as e:
                    self.update_log(f"⚠️ QC 탭 강제 갱신 실패: {e}")
            
            # 3. defaultdb.py 모듈 강제 갱신
            if hasattr(self, 'load_equipment_types'):
                try:
                    self.load_equipment_types()
                    self.update_log("✅ defaultdb 모듈 강제 갱신 완료")
                except Exception as e:
                    self.update_log(f"⚠️ defaultdb 모듈 강제 갱신 실패: {e}")
            
            # 4. 모든 콤보박스 상태 로그
            self._log_all_combobox_states()
            
            self.update_log("🎉 강제 새로고침 완료: 모든 탭 동기화됨")
            
        except Exception as e:
            self.update_log(f"❌ 강제 새로고침 실패: {e}")
            import traceback
            traceback.print_exc()

    def _log_all_combobox_states(self):
        """모든 콤보박스의 현재 상태를 로그에 출력"""
        try:
            # Default DB 탭 콤보박스
            if hasattr(self, 'equipment_type_combo'):
                values = self.equipment_type_combo['values']
                current = self.equipment_type_var.get() if hasattr(self, 'equipment_type_var') else "없음"
                self.update_log(f"📋 Default DB 콤보박스: {len(values)}개 항목, 현재 선택: {current}")
            
            # QC 탭 콤보박스
            if hasattr(self, 'qc_type_combobox'):
                values = self.qc_type_combobox['values']
                current = self.qc_type_var.get() if hasattr(self, 'qc_type_var') else "없음"
                self.update_log(f"🔍 QC 검수 콤보박스: {len(values)}개 항목, 현재 선택: {current}")
            
            # defaultdb.py 모듈 콤보박스
            if hasattr(self, 'equipment_type_combobox'):
                values = self.equipment_type_combobox['values']
                current = self.equipment_type_var.get() if hasattr(self, 'equipment_type_var') else "없음" 
                self.update_log(f"🗃️ defaultdb 콤보박스: {len(values)}개 항목, 현재 선택: {current}")
                
        except Exception as e:
            self.update_log(f"⚠️ 콤보박스 상태 로그 실패: {e}")

    def refresh_qc_equipment_types(self):
        """QC 탭의 장비 유형 목록 수동 새로고침"""
        try:
            self.update_log("🔄 QC 탭 장비 유형 목록 수동 새로고침 시작...")
            
            # 현재 선택된 장비 유형 저장
            current_selection = self.qc_type_var.get() if hasattr(self, 'qc_type_var') else ""
            
            # 장비 유형 목록 다시 로드
            self.load_equipment_types_for_qc()
            
            # 이전 선택이 여전히 존재하면 복원
            if (current_selection and hasattr(self, 'qc_type_combobox') and 
                current_selection in self.qc_type_combobox['values']):
                self.qc_type_combobox.set(current_selection)
                self.update_log(f"✅ QC 탭 새로고침 완료 - 이전 선택 '{current_selection}' 복원")
            else:
                self.update_log("✅ QC 탭 새로고침 완료 - 새 목록으로 업데이트")
            
            # 성공 메시지
            messagebox.showinfo("새로고침 완료", "QC 탭의 장비 유형 목록이 최신 상태로 업데이트되었습니다.")
            
        except Exception as e:
            error_msg = f"QC 탭 새로고침 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("새로고침 오류", error_msg)

    def load_equipment_types_for_qc(self):
        """QC 검수를 위한 장비 유형 목록 로드"""
        if not hasattr(self, 'qc_type_combobox'):
            self.update_log("⚠️ QC 콤보박스가 아직 생성되지 않음")
            return
            
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 장비 유형 정보 조회
            cursor.execute("SELECT id, type_name FROM Equipment_Types ORDER BY type_name")
            equipment_types = cursor.fetchall()

            # 콤보박스 업데이트
            if equipment_types:
                self.equipment_types_for_qc = {name: id for id, name in equipment_types}
                self.qc_type_combobox['values'] = list(self.equipment_types_for_qc.keys())
                if self.qc_type_combobox['values']:
                    self.qc_type_combobox.current(0)  # 첫 번째 항목 선택
                self.update_log(f"✅ QC 탭 장비 유형 로드 완료: {len(equipment_types)}개")
            else:
                self.equipment_types_for_qc = {}
                self.qc_type_combobox['values'] = []
                self.update_log("⚠️ 등록된 장비 유형이 없습니다")

        except Exception as e:
            error_msg = f"QC 장비 유형 로드 중 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)
        finally:
            if conn:
                conn.close()

    def perform_qc_check(self):
        """QC 검수 실행 - 향상된 기능 지원"""
        if not self.maint_mode:
            messagebox.showwarning("접근 제한", "QC 검수는 Maintenance Mode에서만 사용 가능합니다.")
            return
        
        try:
            # Enhanced QC 기능이 있는지 확인
            if hasattr(self, 'perform_enhanced_qc_check'):
                self.perform_enhanced_qc_check()
            elif hasattr(self, 'perform_qc_check_enhanced'):
                self.perform_qc_check_enhanced()
            else:
                # 기본 QC 기능 사용
                from app.qc import add_qc_check_functions_to_class
                add_qc_check_functions_to_class(self.__class__)
                if hasattr(self, 'perform_qc_check'):
                    # 재귀 호출 방지를 위해 직접 QC 로직 실행
                    selected_type = getattr(self, 'qc_type_var', tk.StringVar()).get()
                    if not selected_type:
                        messagebox.showinfo("알림", "장비 유형을 선택해주세요.")
                        return
                    
                    self.update_log(f"[QC] 기본 QC 검수를 실행합니다: {selected_type}")
                    # 실제 QC 로직은 qc.py의 perform_qc_check에서 처리
                else:
                    messagebox.showwarning("기능 없음", "QC 검수 기능을 사용할 수 없습니다.")
                    
        except Exception as e:
            error_msg = f"QC 검수 실행 중 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)

    def toggle_performance_status(self):
        """선택된 파라미터의 Performance 상태 토글"""
        try:
            if not self.maint_mode:
                messagebox.showwarning("권한 없음", "유지보수 모드에서만 Performance 상태를 변경할 수 있습니다.")
                return
            
            selected_items = self.default_db_tree.selection()
            if not selected_items:
                messagebox.showwarning("선택 필요", "Performance 상태를 토글할 파라미터를 선택해주세요.")
                return
            
            # 첫 번째 선택된 항목의 현재 Performance 상태 확인
            first_item = selected_items[0]
            values = self.default_db_tree.item(first_item, 'values')
            if not values:
                return
            
            current_performance = values[11]  # is_performance 컬럼
            # "✅ Yes" 또는 "❌ No" 형태로 저장되므로 파싱
            is_currently_performance = "Yes" in str(current_performance)
            new_performance_status = not is_currently_performance
            
            # 모든 선택된 항목에 새로운 상태 적용
            success_count = 0
            for item in selected_items:
                try:
                    # 트리뷰 아이템에서 tags를 통해 실제 DB ID 가져오기
                    tags = self.default_db_tree.item(item, 'tags')
                    values = self.default_db_tree.item(item, 'values')
                    
                    if not tags or not values:
                        self.update_log(f"⚠️ 선택된 항목의 정보를 찾을 수 없습니다.")
                        continue
                    
                    # tags에서 id_ 접두어를 제거하여 실제 record_id 추출
                    record_id = None
                    for tag in tags:
                        if tag.startswith('id_'):
                            record_id = tag[3:]  # 'id_' 제거
                            break
                    
                    if not record_id:
                        self.update_log(f"⚠️ 선택된 항목의 ID를 찾을 수 없습니다.")
                        continue
                    
                    parameter_name = values[1] if len(values) > 1 else "Unknown"  # 파라미터명
                    
                    # DB에서 Performance 상태 업데이트
                    if self.db_schema.set_performance_status(record_id, new_performance_status):
                        success_count += 1
                        self.update_log(f"✅ {parameter_name}: Performance {'설정' if new_performance_status else '해제'}")
                    else:
                        self.update_log(f"❌ {parameter_name}: Performance 상태 변경 실패")
                        
                except Exception as item_error:
                    self.update_log(f"⚠️ 항목 처리 중 오류: {str(item_error)}")
                    continue
            
            if success_count > 0:
                status_text = "Performance로 설정" if new_performance_status else "Performance 해제"
                messagebox.showinfo("완료", f"{success_count}개 파라미터의 {status_text}가 완료되었습니다.")
                
                # 화면 새로고침
                self.on_equipment_type_selected()
            else:
                messagebox.showerror("오류", "Performance 상태 변경에 실패했습니다.")
                
        except Exception as e:
            error_msg = f"Performance 상태 토글 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)



    def create_default_db_context_menu(self):
        """Default DB 트리뷰용 우클릭 메뉴 생성 - Check list 관리 전용"""
        self.default_db_context_menu = tk.Menu(self.window, tearoff=0)
        
        # Check list 관련 메뉴만 유지 (엔지니어링 스타일)
        self.default_db_context_menu.add_command(
            label="Set as Check list", 
            command=lambda: self.set_performance_status(True)
        )
        self.default_db_context_menu.add_command(
            label="Remove Check list", 
            command=lambda: self.set_performance_status(False)
        )

    def show_default_db_context_menu(self, event):
        """Default DB 트리뷰 우클릭 메뉴 표시"""
        try:
            # 클릭한 위치의 아이템 선택
            item = self.default_db_tree.identify_row(event.y)
            if item:
                self.default_db_tree.selection_set(item)
                self.default_db_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.update_log(f"우클릭 메뉴 표시 오류: {e}")

    def set_performance_status(self, is_performance):
        """선택된 파라미터의 Check list 상태 설정"""
        try:
            if not self.maint_mode:
                messagebox.showwarning("권한 없음", "유지보수 모드에서만 Check list 상태를 변경할 수 있습니다.")
                return
            
            selected_items = self.default_db_tree.selection()
            if not selected_items:
                messagebox.showwarning("선택 필요", "Check list 상태를 변경할 파라미터를 선택해주세요.")
                return
            
            success_count = 0
            for item in selected_items:
                try:
                    # 트리뷰 아이템에서 tags를 통해 실제 DB ID 가져오기
                    tags = self.default_db_tree.item(item, 'tags')
                    values = self.default_db_tree.item(item, 'values')
                    
                    if not tags or not values:
                        self.update_log(f"⚠️ 선택된 항목의 정보를 찾을 수 없습니다.")
                        continue
                    
                    # tags에서 id_ 접두어를 제거하여 실제 record_id 추출
                    record_id = None
                    for tag in tags:
                        if tag.startswith('id_'):
                            record_id = tag[3:]  # 'id_' 제거
                            break
                    
                    if not record_id:
                        self.update_log(f"⚠️ 선택된 항목의 ID를 찾을 수 없습니다.")
                        continue
                    
                    parameter_name = values[1] if len(values) > 1 else "Unknown"  # 파라미터명
                    
                    # DB에서 Check list 상태 업데이트
                    if self.db_schema.set_performance_status(record_id, is_performance):
                        success_count += 1
                        self.update_log(f"✅ {parameter_name}: Check list {'설정' if is_performance else '해제'}")
                    else:
                        self.update_log(f"❌ {parameter_name}: Check list 상태 변경 실패")
                        
                except Exception as item_error:
                    self.update_log(f"⚠️ 항목 처리 중 오류: {str(item_error)}")
                    continue
            
            if success_count > 0:
                status_text = "Check list로 설정" if is_performance else "Check list 해제"
                messagebox.showinfo("완료", f"{success_count}개 파라미터의 {status_text}가 완료되었습니다.")
                
                # 화면 새로고침
                self.on_equipment_type_selected()
            else:
                messagebox.showerror("오류", "Check list 상태 변경에 실패했습니다.")
                
        except Exception as e:
            error_msg = f"Check list 상태 설정 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)

    def apply_performance_filter(self):
        """Check list 필터 적용 - 필터 시스템과 연동"""
        try:
            # 현재 선택된 장비 유형으로 다시 로드
            self.on_equipment_type_selected()
        except Exception as e:
            self.update_log(f"Performance 필터 적용 오류: {e}")

    def get_selected_db_ids(self):
        """선택된 트리뷰 항목들의 실제 DB ID를 반환합니다."""
        selected_items = self.default_db_tree.selection()
        db_ids = []
        
        for item in selected_items:
            tags = self.default_db_tree.item(item, "tags")
            for tag in tags:
                if tag.startswith("id_"):
                    try:
                        db_id = int(tag.split("_")[1])
                        db_ids.append(db_id)
                        break
                    except (ValueError, IndexError):
                        continue
        
        return db_ids
    
    def get_db_id_from_item(self, tree_item):
        """특정 트리뷰 아이템의 실제 DB ID를 반환합니다."""
        tags = self.default_db_tree.item(tree_item, "tags")
        for tag in tags:
            if tag.startswith("id_"):
                try:
                    return int(tag.split("_")[1])
                except (ValueError, IndexError):
                    continue
        return None

    # ========== 🔍 새로운 Parameter 필터 기능 메서드들 ==========

    def _sort_parameter_by_column(self, column):
        """컬럼 헤더 클릭 시 정렬 (새로운 기능)"""
        try:
            # 같은 컬럼을 다시 클릭하면 정렬 순서 반전
            if self.current_sort_column == column:
                self.current_sort_reverse = not self.current_sort_reverse
            else:
                self.current_sort_column = column
                self.current_sort_reverse = False
            
            # 헤더 텍스트 업데이트 (정렬 방향 표시)
            self._update_sort_headers()
            
            # 현재 필터링된 데이터를 정렬
            self._sort_current_data()
            
            # 트리뷰 업데이트
            self._update_parameter_tree_display()
            
            self.update_log(f"📊 컬럼 '{column}' 정렬 적용 ({'내림차순' if self.current_sort_reverse else '오름차순'})")
            
        except Exception as e:
            self.update_log(f"❌ 컬럼 정렬 오류: {e}")

    def _update_sort_headers(self):
        """정렬 헤더 표시 업데이트 (새로운 기능)"""
        try:
            columns = self.default_db_tree['columns']
            headers = {
                "no": "No.",
                "parameter_name": "ItemName",
                "module": "Module",
                "part": "Part", 
                "item_type": "Data Type",
                "default_value": "Default Value",
                "min_spec": "Min Spec",
                "max_spec": "Max Spec",
                "is_performance": "Check list",
                "description": "Description"
            }
            
            for col in columns:
                if col == 'no':
                    continue
                    
                header_text = headers[col]
                if col == self.current_sort_column:
                    arrow = " ▲" if not self.current_sort_reverse else " ▼"
                    header_text += arrow
                
                self.default_db_tree.heading(col, text=header_text)
                
        except Exception as e:
            self.update_log(f"❌ 정렬 헤더 업데이트 오류: {e}")

    def _sort_current_data(self):
        """현재 데이터 정렬 (새로운 기능)"""
        try:
            if not self.filtered_parameter_data or not self.current_sort_column:
                return
            
            # 컬럼별 정렬 키 함수 정의
            sort_key_map = {
                'parameter_name': lambda x: str(x[1]).lower(),
                'module': lambda x: str(x[2]).lower(),
                'part': lambda x: str(x[3]).lower(),
                'item_type': lambda x: str(x[4]).lower(),
                'default_value': lambda x: str(x[5]).lower(),
                'min_spec': lambda x: numeric_sort_key(x[6]),
                'max_spec': lambda x: numeric_sort_key(x[7]),
                'is_performance': lambda x: x[8] == 'Yes',
                'description': lambda x: str(x[9]).lower()
            }
            
            sort_key = sort_key_map.get(self.current_sort_column, lambda x: str(x[1]).lower())
            
            self.filtered_parameter_data.sort(key=sort_key, reverse=self.current_sort_reverse)
            
        except Exception as e:
            self.update_log(f"❌ 데이터 정렬 오류: {e}")


    def _apply_parameter_filters(self):
        """모든 파라미터 필터 적용 (새로운 기능)"""
        try:
            if not hasattr(self, 'original_parameter_data') or not self.original_parameter_data:
                return
            
            # 원본 데이터로부터 필터링 시작
            filtered_data = self.original_parameter_data.copy()
            
            # 1. 빠른 검색 필터
            search_text = self.param_search_var.get().lower().strip()
            if search_text:
                filtered_data = [
                    row for row in filtered_data
                    if any(search_text in str(cell).lower() for cell in row[1:])  # No. 컬럼 제외하고 검색
                ]
            
            # 2. 모듈 필터
            if hasattr(self, 'module_filter_var'):
                module_filter = self.module_filter_var.get()
                if module_filter and module_filter != "All":
                    filtered_data = [row for row in filtered_data if row[2] == module_filter]
            
            # 3. 파트 필터  
            if hasattr(self, 'part_filter_var'):
                part_filter = self.part_filter_var.get()
                if part_filter and part_filter != "All":
                    filtered_data = [row for row in filtered_data if row[3] == part_filter]
            
            # 4. 데이터 타입 필터
            if hasattr(self, 'data_type_filter_var'):
                data_type_filter = self.data_type_filter_var.get()
                if data_type_filter and data_type_filter != "All":
                    filtered_data = [row for row in filtered_data if row[4] == data_type_filter]
            
            # 필터링된 데이터 저장
            self.filtered_parameter_data = filtered_data
            
            # 현재 정렬 적용
            if self.current_sort_column:
                self._sort_current_data()
            
            # 트리뷰 업데이트
            self._update_parameter_tree_display()
            
            # 결과 표시
            total_count = len(self.original_parameter_data)
            filtered_count = len(filtered_data)
            
            if hasattr(self, 'filter_result_label'):
                if filtered_count == total_count:
                    self.filter_result_label.config(text=f"Total: {total_count} parameters")
                else:
                    self.filter_result_label.config(text=f"Showing: {filtered_count} / {total_count}")
            
        except Exception as e:
            self.update_log(f"❌ Parameter 필터 적용 오류: {e}")

    def _update_parameter_tree_display(self):
        """파라미터 트리뷰 화면 업데이트 (새로운 기능)"""
        try:
            # 기존 데이터 클리어
            for item in self.default_db_tree.get_children():
                self.default_db_tree.delete(item)
            
            # 필터링된 데이터로 트리뷰 채우기
            for i, row in enumerate(self.filtered_parameter_data, 1):
                # row[0]은 실제 DB ID, row[1:]은 화면 표시 데이터
                record_id = row[0]  # 실제 DB ID
                display_row = [i] + list(row[1:])  # 순서 번호 + 화면 데이터
                
                # DB ID를 태그로 저장하여 편집/삭제에서 사용
                self.default_db_tree.insert("", "end", values=display_row, tags=(f"id_{record_id}",))
            
        except Exception as e:
            self.update_log(f"❌ Parameter 트리뷰 업데이트 오류: {e}")

    def _clear_parameter_search(self):
        """파라미터 검색 필터 지우기 (새로운 기능)"""
        try:
            self.param_search_var.set("")
            if hasattr(self, 'param_search_entry'):
                self.param_search_entry.focus()
        except Exception as e:
            self.update_log(f"❌ 검색 필터 지우기 오류: {e}")



    def _toggle_advanced_parameter_filters(self):
        """고급 필터 패널 토글 (새로운 기능)"""
        try:
            is_visible = self.advanced_filter_visible.get()
            
            if is_visible:
                # 숨기기
                self.advanced_filter_frame.pack_forget()
                self.toggle_advanced_btn.config(text="▼ Filters")
                self.advanced_filter_visible.set(False)
            else:
                # 보이기
                self.advanced_filter_frame.pack(fill=tk.X, pady=(5, 0))
                self.toggle_advanced_btn.config(text="▲ Hide")
                self.advanced_filter_visible.set(True)
                
                # 필터 옵션 업데이트
                self._update_filter_options()
            
        except Exception as e:
            self.update_log(f"❌ 고급 필터 토글 오류: {e}")

    def _update_filter_options(self):
        """필터 옵션 목록 업데이트 (새로운 기능)"""
        try:
            if not hasattr(self, 'original_parameter_data') or not self.original_parameter_data:
                return
            
            # 모듈 목록 업데이트
            modules = sorted(set(row[2] for row in self.original_parameter_data if row[2]))
            module_values = ["All"] + modules
            self.module_filter_combo['values'] = module_values
            if not self.module_filter_var.get():
                self.module_filter_var.set("All")
            
            # 파트 목록 업데이트
            parts = sorted(set(row[3] for row in self.original_parameter_data if row[3]))
            part_values = ["All"] + parts
            self.part_filter_combo['values'] = part_values
            if not self.part_filter_var.get():
                self.part_filter_var.set("All")
            
            # 데이터 타입 목록 업데이트
            data_types = sorted(set(row[4] for row in self.original_parameter_data if row[4]))
            type_values = ["All"] + data_types
            self.data_type_filter_combo['values'] = type_values
            if not self.data_type_filter_var.get():
                self.data_type_filter_var.set("All")
            
            self.update_log("✅ 필터 옵션 업데이트 완료")
            
        except Exception as e:
            self.update_log(f"❌ 필터 옵션 업데이트 오류: {e}")

    def _on_module_filter_changed(self, event=None):
        """모듈 필터 변경 시 처리 (새로운 기능)"""
        self._apply_parameter_filters()

    def _on_part_filter_changed(self, event=None):
        """파트 필터 변경 시 처리 (새로운 기능)"""
        self._apply_parameter_filters()

    def _on_data_type_filter_changed(self, event=None):
        """데이터 타입 필터 변경 시 처리 (새로운 기능)"""
        self._apply_parameter_filters()

    def _reset_parameter_filters(self):
        """모든 파라미터 필터 초기화 (새로운 기능)"""
        try:
            # 검색어 초기화
            self.param_search_var.set("")
            
            # 정렬 초기화
            self.current_sort_column = ""
            self.current_sort_reverse = False
            
            # 고급 필터 초기화
            if hasattr(self, 'module_filter_var'):
                self.module_filter_var.set("All")
            if hasattr(self, 'part_filter_var'):
                self.part_filter_var.set("All")
            if hasattr(self, 'data_type_filter_var'):
                self.data_type_filter_var.set("All")
            
            # 헤더 표시 초기화
            self._update_sort_headers()
            
            # 필터 적용
            self._apply_parameter_filters()
            
            self.update_log("🔄 Parameter Filters Reset")
            
        except Exception as e:
            self.update_log(f"❌ Filter Reset Error: {e}")








