#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
도움말 UI 관리 모듈
사용 설명서 및 프로그램 정보 창 생성과 관리를 담당합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
import logging

from ..services.help_service import HelpDataService, get_help_service
from ..core.app_info import AppInfoManager, get_app_info_manager


class HelpUIManager:
    """도움말 UI 관리자 클래스"""
    
    def __init__(self, parent_window: tk.Tk, help_service: Optional[HelpDataService] = None,
                 app_info_manager: Optional[AppInfoManager] = None, logger: Optional[logging.Logger] = None):
        """
        Args:
            parent_window: 부모 윈도우
            help_service: 도움말 서비스
            app_info_manager: 애플리케이션 정보 관리자
            logger: 로거 인스턴스
        """
        self.parent_window = parent_window
        self.help_service = help_service or get_help_service()
        self.app_info_manager = app_info_manager or get_app_info_manager()
        self.logger = logger or logging.getLogger(__name__)
        
        # 창 참조 저장 (중복 생성 방지)
        self._user_guide_window = None
        self._about_window = None
    
    def show_user_guide(self, event=None):
        """사용 설명서 창 표시"""
        try:
            # 이미 열린 창이 있으면 포커스만 이동
            if self._user_guide_window and self._user_guide_window.winfo_exists():
                self._user_guide_window.lift()
                self._user_guide_window.focus()
                return
            
            self.logger.info("사용 설명서가 호출되었습니다.")
            
            guide_window = tk.Toplevel(self.parent_window)
            self._user_guide_window = guide_window
            
            guide_data = self.help_service.user_guide_data
            guide_window.title(guide_data.title)
            guide_window.geometry("800x600")
            guide_window.resizable(True, True)
            
            # 중앙 정렬
            self._center_window(guide_window, 800, 600)
            
            # 스타일 설정
            self._setup_guide_styles()
            
            # 메인 프레임
            main_frame = ttk.Frame(guide_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # 스크롤 가능한 컨텐츠 영역
            canvas = tk.Canvas(main_frame)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # 제목
            ttk.Label(scrollable_frame, text=guide_data.title, style="Title.TLabel").pack(pady=(0, 20))
            
            # 섹션들 표시
            for section in guide_data.sections:
                ttk.Label(scrollable_frame, text=section.title, style="Heading.TLabel").pack(anchor="w", pady=(15, 5))
                for line in section.content:
                    ttk.Label(scrollable_frame, text=line, style="Content.TLabel", 
                             wraplength=700, justify="left").pack(anchor="w", padx=(20, 0))
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # 창 닫힘 이벤트 처리
            guide_window.protocol("WM_DELETE_WINDOW", lambda: self._on_guide_window_close())
            
        except tk.TclError as e:
            self.logger.error(f"사용 설명서 창 생성 중 Tkinter 오류: {e}", exc_info=True)
            messagebox.showerror("오류", "사용 설명서 창을 여는 중 오류가 발생했습니다.", parent=self.parent_window)
        except Exception as e:
            self.logger.error(f"사용 설명서 창 생성 중 예상치 못한 오류: {e}", exc_info=True)
            messagebox.showwarning("경고", "사용 설명서 창을 여는 데 문제가 발생했습니다.", parent=self.parent_window)
    
    def show_about_dialog(self):
        """프로그램 정보 창 표시"""
        try:
            # 이미 열린 창이 있으면 포커스만 이동
            if self._about_window and self._about_window.winfo_exists():
                self._about_window.lift()
                self._about_window.focus()
                return
            
            self.logger.info("프로그램 정보 창 호출됨.")
            
            about_window = tk.Toplevel(self.parent_window)
            self._about_window = about_window
            
            app_info = self.app_info_manager.app_info
            about_window.title(f"About {app_info.name}")
            about_window.geometry("600x800")
            about_window.resizable(False, False)
            about_window.transient(self.parent_window)
            about_window.grab_set()
            
            # 아이콘 설정
            if app_info.icon_path:
                try:
                    about_window.iconbitmap(app_info.icon_path)
                except Exception as icon_e:
                    self.logger.warning(f"아이콘 로드 실패: {icon_e}")
            
            # 스타일 설정
            self._setup_about_styles()
            
            container = ttk.Frame(about_window, padding="20")
            container.pack(fill=tk.BOTH, expand=True)
            
            # 제목
            title_frame = ttk.Frame(container)
            title_frame.pack(fill=tk.X, pady=(0, 20))
            ttk.Label(title_frame, text=app_info.name, style="AboutTitle.TLabel").pack()
            
            # 기본 정보 섹션들
            self._create_info_sections(container, app_info)
            
            # 설명 섹션
            self._create_description_section(container, app_info)
            
            # 리비전 히스토리 섹션
            self._create_revision_section(container, about_window)
            
            # 닫기 버튼
            ttk.Button(container, text="닫기", command=about_window.destroy).pack(pady=(20, 0))
            
            # 창 닫힘 이벤트 처리
            about_window.protocol("WM_DELETE_WINDOW", lambda: self._on_about_window_close())
            
        except tk.TclError as e:
            self.logger.error(f"프로그램 정보 창 생성 중 Tkinter 오류: {e}", exc_info=True)
            messagebox.showerror("오류", "프로그램 정보 창을 여는 중 오류가 발생했습니다.", parent=self.parent_window)
        except Exception as e:
            self.logger.error(f"프로그램 정보 창 생성 중 예상치 못한 오류: {e}", exc_info=True)
            messagebox.showerror("오류", "프로그램 정보 창을 여는 중 예상치 못한 오류가 발생했습니다.", parent=self.parent_window)
    
    def _center_window(self, window: tk.Toplevel, width: int, height: int):
        """창을 화면 중앙에 배치"""
        x = self.parent_window.winfo_x() + (self.parent_window.winfo_width() // 2) - (width // 2)
        y = self.parent_window.winfo_y() + (self.parent_window.winfo_height() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _setup_guide_styles(self):
        """사용 설명서 스타일 설정"""
        style = ttk.Style()
        style.configure("Title.TLabel", font=('Helvetica', 16, 'bold'))
        style.configure("Heading.TLabel", font=('Helvetica', 12, 'bold'))
        style.configure("Content.TLabel", font=('Helvetica', 10))
    
    def _setup_about_styles(self):
        """프로그램 정보 스타일 설정"""
        style = ttk.Style()
        style.configure("AboutTitle.TLabel", font=('Helvetica', 16, 'bold'))
        style.configure("AboutHeader.TLabel", font=('Helvetica', 12, 'bold'))
        style.configure("AboutContent.TLabel", font=('Helvetica', 10))
        style.configure("RevCategory.TLabel", font=('Helvetica', 11, 'bold'))
        style.configure("RevItem.TLabel", font=('Helvetica', 10))
    
    def _create_info_sections(self, container: ttk.Frame, app_info):
        """기본 정보 섹션들 생성"""
        sections_data = [
            ("Product Information", [
                ("Version", app_info.version),
                ("Release Date", app_info.release_date),
            ]),
            ("Development", [
                ("Developer", app_info.developer),
                ("Organization", app_info.organization),
                ("Contact", app_info.contact),
            ]),
        ]
        
        for section_title, items in sections_data:
            section_frame = ttk.LabelFrame(container, text=section_title, padding="10")
            section_frame.pack(fill=tk.X, pady=(0, 10))
            for i, (key, value) in enumerate(items):
                ttk.Label(section_frame, text=key + ":", style="AboutHeader.TLabel").grid(
                    row=i, column=0, sticky="w", padx=(0, 10), pady=2)
                ttk.Label(section_frame, text=value, style="AboutContent.TLabel").grid(
                    row=i, column=1, sticky="w", pady=2)
    
    def _create_description_section(self, container: ttk.Frame, app_info):
        """설명 섹션 생성"""
        desc_frame = ttk.LabelFrame(container, text="Description", padding="10")
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(desc_frame, text=app_info.description, style="AboutContent.TLabel",
                  wraplength=500, justify="left").pack(anchor="w")
    
    def _create_revision_section(self, container: ttk.Frame, about_window: tk.Toplevel):
        """리비전 히스토리 섹션 생성"""
        revisions = self.app_info_manager.revisions
        
        revision_frame = ttk.LabelFrame(container, text="Revision History", padding="10")
        revision_frame.pack(fill=tk.X, pady=(0, 10))
        
        rev_tree_frame = ttk.Frame(revision_frame)
        rev_tree_frame.pack(fill=tk.X, expand=True)
        
        revision_tree = ttk.Treeview(rev_tree_frame, height=6)
        revision_tree["columns"] = ("Version", "Date", "Summary")
        revision_tree.heading("#0", text="")
        revision_tree.column("#0", width=0, stretch=False)
        
        for col, width in [("Version", 70), ("Date", 100), ("Summary", 380)]:
            revision_tree.heading(col, text=col)
            revision_tree.column(col, width=width, anchor="w")
        
        for rev in revisions:
            revision_tree.insert("", tk.END, values=(
                rev.version, rev.date, rev.summary
            ), tags=("revision",))
        
        def show_revision_details(event):
            try:
                selection = revision_tree.selection()
                if not selection:
                    return
                
                item_id = selection[0]
                version_str = revision_tree.item(item_id)["values"][0]
                rev_info = next((r for r in revisions if r.version == version_str), None)
                
                if not rev_info:
                    self.logger.warning(f"리비전 상세 정보를 찾을 수 없습니다: {version_str}")
                    return
                
                self._show_revision_detail_window(rev_info, about_window)
                
            except IndexError:
                self.logger.info("리비전 히스토리에서 선택된 항목이 없습니다.")
            except Exception as e_detail:
                self.logger.error(f"리비전 상세 정보 표시 중 오류: {e_detail}", exc_info=True)
        
        revision_tree.bind("<Double-1>", show_revision_details)
        
        scrollbar = ttk.Scrollbar(rev_tree_frame, orient="vertical", command=revision_tree.yview)
        revision_tree.configure(yscrollcommand=scrollbar.set)
        revision_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _show_revision_detail_window(self, rev_info, parent_window):
        """리비전 상세 정보 창 표시"""
        detail_window = tk.Toplevel(parent_window)
        detail_window.title(f"Version {rev_info.version} Details")
        detail_window.geometry("500x450")
        detail_window.resizable(False, False)
        detail_window.transient(parent_window)
        detail_window.grab_set()
        
        # 위치 조정 (부모 창 옆에 배치)
        about_x = parent_window.winfo_x()
        about_y = parent_window.winfo_y()
        about_width = parent_window.winfo_width()
        screen_width = detail_window.winfo_screenwidth()
        new_x = about_x + about_width + 10
        if new_x + 500 > screen_width:
            new_x = about_x - 510
        if new_x < 0:
            new_x = 0
        detail_window.geometry(f"+{new_x}+{about_y}")
        
        detail_container = ttk.Frame(detail_window, padding="20")
        detail_container.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(detail_container, text=f"Version {rev_info.version} ({rev_info.date})",
                  style="AboutTitle.TLabel").pack(anchor="w", pady=(0, 10))
        
        for category, cat_items in rev_info.details.items():
            ttk.Label(detail_container, text=category, style="RevCategory.TLabel").pack(anchor="w", pady=(10, 5))
            for item_detail in cat_items:
                ttk.Label(detail_container, text=f"• {item_detail}", style="RevItem.TLabel",
                          wraplength=450).pack(anchor="w", padx=(20, 0))
        
        ttk.Button(detail_container, text="닫기", command=detail_window.destroy).pack(pady=(20, 0))
    
    def _on_guide_window_close(self):
        """사용 설명서 창 닫힘 처리"""
        self._user_guide_window = None
    
    def _on_about_window_close(self):
        """프로그램 정보 창 닫힘 처리"""
        self._about_window = None
    
    def setup_help_menu(self, menubar: tk.Menu) -> tk.Menu:
        """도움말 메뉴 설정"""
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도움말", menu=help_menu)
        help_menu.add_command(label="사용 설명서 (F1)", command=self.show_user_guide)
        help_menu.add_separator()
        help_menu.add_command(label="프로그램 정보", command=self.show_about_dialog)
        return help_menu
    
    def setup_help_bindings(self):
        """도움말 관련 키 바인딩 설정"""
        self.parent_window.bind('<F1>', lambda event: self.show_user_guide())


# 유틸리티 함수들
def create_help_ui_manager(parent_window: tk.Tk, help_service: Optional[HelpDataService] = None,
                          app_info_manager: Optional[AppInfoManager] = None, 
                          logger: Optional[logging.Logger] = None) -> HelpUIManager:
    """도움말 UI 관리자 생성"""
    return HelpUIManager(parent_window, help_service, app_info_manager, logger) 