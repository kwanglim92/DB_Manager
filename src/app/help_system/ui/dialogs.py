# -*- coding: utf-8 -*-
"""
도움말 시스템 다이얼로그

프로그램 정보, 사용자 가이드, 리비전 히스토리 등의 다이얼로그를 제공합니다.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional, Dict, Any, List
import logging


class BaseHelpDialog:
    """도움말 다이얼로그 기본 클래스"""
    
    def __init__(self, parent: tk.Tk, title: str, size: tuple = (600, 500)):
        """
        Args:
            parent: 부모 윈도우
            title: 다이얼로그 제목
            size: 다이얼로그 크기 (width, height)
        """
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{size[0]}x{size[1]}")
        self.dialog.resizable(True, True)
        
        # 모달 설정
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 중앙 정렬
        self._center_dialog()
        
        # 닫기 이벤트 처리
        self.dialog.protocol("WM_DELETE_WINDOW", self.close)
        
    def _center_dialog(self):
        """다이얼로그를 화면 중앙에 배치"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def close(self):
        """다이얼로그 닫기"""
        self.dialog.grab_release()
        self.dialog.destroy()
        
    def show(self):
        """다이얼로그 표시"""
        self.dialog.focus_set()
        self.dialog.wait_window()


class AboutDialog(BaseHelpDialog):
    """프로그램 정보 다이얼로그"""
    
    def __init__(self, parent: tk.Tk, app_info_manager, logger: Optional[logging.Logger] = None):
        """
        Args:
            parent: 부모 윈도우
            app_info_manager: 애플리케이션 정보 관리자
            logger: 로거
        """
        super().__init__(parent, "프로그램 정보", (650, 550))
        self.app_info_manager = app_info_manager
        self.logger = logger or logging.getLogger(__name__)
        
        self._create_ui()
        
    def _create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 상단: 애플리케이션 정보
        info_frame = ttk.LabelFrame(main_frame, text="기본 정보", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 애플리케이션 정보 텍스트
        info_text = scrolledtext.ScrolledText(
            info_frame, 
            height=8, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            bg=self.dialog.cget('bg')
        )
        info_text.pack(fill=tk.BOTH, expand=True)
        
        # 애플리케이션 정보 채우기
        info_content = self.app_info_manager.get_formatted_app_info()
        info_text.config(state=tk.NORMAL)
        info_text.insert(tk.END, info_content)
        info_text.config(state=tk.DISABLED)
        
        # 하단: 리비전 히스토리
        revision_frame = ttk.LabelFrame(main_frame, text="리비전 히스토리", padding="10")
        revision_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 리비전 리스트
        self._create_revision_list(revision_frame)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="닫기", command=self.close).pack(side=tk.RIGHT)
        
    def _create_revision_list(self, parent):
        """리비전 목록 생성"""
        # 리스트박스와 스크롤바
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.revision_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.revision_listbox.yview)
        
        self.revision_listbox.configure(yscrollcommand=scrollbar.set)
        self.revision_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 리비전 데이터 채우기
        for revision in self.app_info_manager.revisions:
            display_text = f"v{revision.version} ({revision.date}) - {revision.summary}"
            self.revision_listbox.insert(tk.END, display_text)
            
        # 더블클릭 이벤트
        self.revision_listbox.bind("<Double-Button-1>", self._on_revision_double_click)
        
        # 안내 라벨
        ttk.Label(parent, text="더블클릭하여 상세 내용을 확인하세요.", 
                 font=("", 9), foreground="gray").pack(pady=(5, 0))
                 
    def _on_revision_double_click(self, event):
        """리비전 더블클릭 이벤트"""
        selection = self.revision_listbox.curselection()
        if selection:
            index = selection[0]
            revision = self.app_info_manager.revisions[index]
            RevisionDetailDialog(self.dialog, revision).show()


class RevisionDetailDialog(BaseHelpDialog):
    """리비전 상세 정보 다이얼로그"""
    
    def __init__(self, parent, revision):
        """
        Args:
            parent: 부모 윈도우
            revision: 리비전 정보
        """
        super().__init__(parent, f"리비전 상세 - v{revision.version}", (600, 500))
        self.revision = revision
        
        self._create_ui()
        
    def _create_ui(self):
        """UI 생성"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 헤더 정보
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text=f"버전: {self.revision.version}", 
                 font=("", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"날짜: {self.revision.date}").pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"요약: {self.revision.summary}").pack(anchor=tk.W)
        
        # 상세 내용
        if self.revision.details:
            details_frame = ttk.LabelFrame(main_frame, text="상세 내용", padding="10")
            details_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            
            details_text = scrolledtext.ScrolledText(
                details_frame, 
                wrap=tk.WORD, 
                state=tk.DISABLED
            )
            details_text.pack(fill=tk.BOTH, expand=True)
            
            # 상세 내용 채우기
            content_lines = []
            for category, items in self.revision.details.items():
                if items:
                    content_lines.append(f"[{category}]")
                    for item in items:
                        content_lines.append(f"• {item}")
                    content_lines.append("")
            
            details_text.config(state=tk.NORMAL)
            details_text.insert(tk.END, "\n".join(content_lines))
            details_text.config(state=tk.DISABLED)
        
        # 닫기 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="닫기", command=self.close).pack(side=tk.RIGHT)


class UserGuideDialog(BaseHelpDialog):
    """사용자 가이드 다이얼로그"""
    
    def __init__(self, parent: tk.Tk, guide_text_or_service, logger: Optional[logging.Logger] = None):
        """
        Args:
            parent: 부모 윈도우
            guide_text_or_service: 가이드 텍스트 문자열 또는 도움말 서비스 객체
            logger: 로거
        """
        super().__init__(parent, "사용자 가이드", (750, 600))
        
        # 입력이 문자열인지 서비스 객체인지 판단
        if isinstance(guide_text_or_service, str):
            self.guide_text = guide_text_or_service
            self.help_service = None
        else:
            self.help_service = guide_text_or_service
            self.guide_text = None
            
        self.logger = logger or logging.getLogger(__name__)
        
        self._create_ui()
        
    def _create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 가이드 텍스트가 직접 제공된 경우 간단한 텍스트 위젯 사용
        if self.guide_text:
            text_widget = scrolledtext.ScrolledText(
                main_frame, 
                wrap=tk.WORD, 
                state=tk.DISABLED,
                padding="10"
            )
            text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            text_widget.config(state=tk.NORMAL)
            text_widget.insert(tk.END, self.guide_text)
            text_widget.config(state=tk.DISABLED)
        
        # 도움말 서비스 객체가 제공된 경우 탭 구성
        elif self.help_service:
            # 노트북 위젯으로 탭 구성
            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # 개요 탭
            self._create_overview_tab(notebook)
            
            # 키보드 단축키 탭
            if hasattr(self.help_service, 'shortcuts') and self.help_service.shortcuts:
                self._create_shortcuts_tab(notebook)
                
            # 주요 기능 탭
            if hasattr(self.help_service, 'features') and self.help_service.features:
                self._create_features_tab(notebook)
                
            # FAQ 탭
            if hasattr(self.help_service, 'faqs') and self.help_service.faqs:
                self._create_faq_tab(notebook)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="닫기", command=self.close).pack(side=tk.RIGHT)
        
    def _create_overview_tab(self, notebook):
        """개요 탭 생성"""
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="📋 개요")
        
        # 스크롤 가능한 텍스트
        text_widget = scrolledtext.ScrolledText(
            overview_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            padding="10"
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 전체 가이드 텍스트 생성
        guide_text = self.help_service.generate_user_guide_text()
        
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, guide_text)
        text_widget.config(state=tk.DISABLED)
        
    def _create_shortcuts_tab(self, notebook):
        """키보드 단축키 탭 생성"""
        shortcuts_frame = ttk.Frame(notebook)
        notebook.add(shortcuts_frame, text="⌨️ 단축키")
        
        # 트리뷰로 단축키 표시
        tree_frame = ttk.Frame(shortcuts_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("shortcut", "description")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        tree.heading("shortcut", text="키 조합")
        tree.heading("description", text="설명")
        
        tree.column("shortcut", width=150, minwidth=100)
        tree.column("description", width=400, minwidth=200)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 데이터 채우기
        shortcuts_by_category = self.help_service.get_shortcuts_by_category()
        for category, shortcuts in shortcuts_by_category.items():
            if len(shortcuts_by_category) > 1:
                # 카테고리 헤더
                tree.insert("", tk.END, values=(f"[{category}]", ""), tags=("category",))
                
            for shortcut in shortcuts:
                tree.insert("", tk.END, values=(shortcut.key_combination, shortcut.description))
                
        # 카테고리 스타일
        tree.tag_configure("category", background="#f0f0f0", font=("", 9, "bold"))
        
    def _create_features_tab(self, notebook):
        """주요 기능 탭 생성"""
        features_frame = ttk.Frame(notebook)
        notebook.add(features_frame, text="🎯 기능")
        
        # 리스트박스로 기능 표시
        list_frame = ttk.Frame(features_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        listbox = tk.Listbox(list_frame, font=("", 10))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 데이터 채우기
        features_by_category = self.help_service.get_features_by_category()
        for category, features in features_by_category.items():
            if len(features_by_category) > 1:
                listbox.insert(tk.END, f"[{category}]")
                
            for feature in features:
                display_text = f"• {feature.name}"
                if feature.description:
                    display_text += f": {feature.description}"
                listbox.insert(tk.END, display_text)
                
            listbox.insert(tk.END, "")  # 빈 줄
            
    def _create_faq_tab(self, notebook):
        """FAQ 탭 생성"""
        faq_frame = ttk.Frame(notebook)
        notebook.add(faq_frame, text="❓ FAQ")
        
        # 스크롤 가능한 텍스트
        text_widget = scrolledtext.ScrolledText(
            faq_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            padding="10"
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # FAQ 내용 생성
        content_lines = []
        faqs_by_category = self.help_service.get_faqs_by_category()
        
        for category, faqs in faqs_by_category.items():
            if len(faqs_by_category) > 1:
                content_lines.append(f"[{category}]")
                content_lines.append("=" * len(category))
                content_lines.append("")
                
            for i, faq in enumerate(faqs, 1):
                content_lines.append(f"Q{i}: {faq.question}")
                content_lines.append(f"A{i}: {faq.answer}")
                content_lines.append("")
                
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, "\n".join(content_lines))
        text_widget.config(state=tk.DISABLED)


