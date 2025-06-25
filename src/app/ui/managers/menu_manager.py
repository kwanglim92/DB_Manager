"""
메뉴 생성 및 관리를 담당하는 모듈
"""

import tkinter as tk
from tkinter import messagebox, simpledialog


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
        tools_menu.add_separator()
        tools_menu.add_command(label="🔐 비밀번호 변경", command=self.show_change_password_dialog)
        tools_menu.add_command(label="⚙️ 설정", command=self.show_settings_dialog)
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
        messagebox.showinfo(
            "프로그램 정보",
            "DB Manager\\n버전: 1.0.1\\n제작자: kwanglim92\\n\\n이 프로그램은 DB 파일 비교, 관리, 보고서 생성 등 다양한 기능을 제공합니다."
        )
    
    def show_user_guide(self, event=None):
        """사용자 가이드 다이얼로그 표시"""
        guide_text = (
            "[DB Manager 사용자 가이드]\\n\\n"
            "• 폴더 열기: 파일 > 폴더 열기 (Ctrl+O)\\n"
            "• DB 비교: 여러 DB 파일을 불러와 값 차이, 격자 뷰, 보고서 등 다양한 탭에서 확인\\n"
            "• 유지보수 모드: 도구 > Maintenance Mode (비밀번호 필요)\\n"
            "• Default DB 관리, QC 검수, 변경 이력 등은 유지보수 모드에서만 사용 가능\\n"
            "• 각 탭에서 우클릭 및 버튼으로 항목 추가/삭제/내보내기 등 다양한 작업 지원\\n"
            "• 문의: github.com/kwanglim92/DB_Manager\\n\\n"
            "= 사용자 역할 =\\n"
            "• 장비 생산 엔지니어: DB 비교 기능 사용\\n"
            "• QC 엔지니어: Maintenance Mode로 모든 기능 사용"
        )
        messagebox.showinfo("사용 설명서", guide_text)
    
    def show_change_password_dialog(self):
        """유지보수 모드 비밀번호 변경 다이얼로그를 표시합니다."""
        current_password = simpledialog.askstring("비밀번호 변경", "현재 비밀번호를 입력하세요:", show="*")
        if current_password is None:
            return
        
        from app.utils import verify_password, change_maintenance_password
        if not verify_password(current_password):
            messagebox.showerror("오류", "현재 비밀번호가 일치하지 않습니다.")
            return
        
        new_password = simpledialog.askstring("비밀번호 변경", "새 비밀번호를 입력하세요:", show="*")
        if new_password is None:
            return
        
        confirm_password = simpledialog.askstring("비밀번호 변경", "새 비밀번호를 다시 입력하세요:", show="*")
        if confirm_password is None:
            return
        
        if new_password != confirm_password:
            messagebox.showerror("오류", "새 비밀번호가 일치하지 않습니다.")
            return
        
        if change_maintenance_password(current_password, new_password):
            messagebox.showinfo("성공", "비밀번호가 성공적으로 변경되었습니다.")
            self.manager.update_log("유지보수 모드 비밀번호가 변경되었습니다.")
        else:
            messagebox.showerror("오류", "비밀번호 변경에 실패했습니다.")
    
    def show_settings_dialog(self):
        """설정 다이얼로그를 표시합니다."""
        # 기존 manager.py에서 show_settings_dialog 메서드 구현을 여기로 이동 예정
        # 현재는 placeholder
        messagebox.showinfo("설정", "설정 기능은 추후 구현 예정입니다.")