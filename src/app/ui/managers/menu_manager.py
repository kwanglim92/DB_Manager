"""
메뉴 생성 및 관리를 담당하는 모듈
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk


class MenuManager:
    """메뉴 생성 및 관리를 담당하는 클래스"""
    
    def __init__(self, manager):
        """
        Args:
            manager: DBManager 인스턴스 참조
        """
        self.manager = manager
    
    def create_menu(self):
        """메뉴바를 생성합니다."""
        menubar = tk.Menu(self.manager.window)
        
        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="폴더 열기 (Ctrl+O)", command=self.manager.load_folder)
        file_menu.add_separator()
        file_menu.add_command(label="보고서 내보내기", command=self.manager.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.manager.window.quit)
        menubar.add_cascade(label="파일", menu=file_menu)
        
        # 도구 메뉴
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="👤 사용자 모드 전환", command=self.manager.toggle_maint_mode)
        menubar.add_cascade(label="도구", menu=tools_menu)
        
        # 도움말 메뉴
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="사용 설명서 (F1)", command=self.show_user_guide)
        help_menu.add_separator()
        help_menu.add_command(label="프로그램 정보", command=self.show_about)
        menubar.add_cascade(label="도움말", menu=help_menu)
        
        self.manager.window.config(menu=menubar)
    
    def show_about(self):
        """프로그램 정보 다이얼로그 표시"""
        # About 창 생성
        about_window = tk.Toplevel(self.manager.window)
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
        guide_window = tk.Toplevel(self.manager.window)
        guide_window.title("DB 관리 도구 사용 설명서")
        guide_window.geometry("800x600")
        guide_window.resizable(True, True)  # 창 크기 조절 가능
        
        # 부모 창 중앙에 위치
        x = self.manager.window.winfo_x() + (self.manager.window.winfo_width() // 2) - (800 // 2)
        y = self.manager.window.winfo_y() + (self.manager.window.winfo_height() // 2) - (600 // 2)
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