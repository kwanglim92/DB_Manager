import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Callable, Optional, Tuple, Any

class CheckboxTreeview(ttk.Treeview):
    """체크박스 기능이 있는 트리뷰 위젯"""
    def __init__(self, master=None, checkbox_column="checkbox", **kwargs):
        # 트리뷰 초기화
        columns = kwargs.pop('columns', ())
        if checkbox_column not in columns:
            columns = (checkbox_column,) + columns

        super().__init__(master, columns=columns, **kwargs)

        # 체크박스 설정
        self.checkbox_column = checkbox_column
        self.checkboxes: Dict[str, tk.BooleanVar] = {}
        self.checkbox_images = self._create_checkbox_images()

        # 체크박스 열 설정
        self.column(checkbox_column, width=40, anchor='center', stretch=False)
        self.heading(checkbox_column, text='✓')

        # 클릭 이벤트 바인딩
        self.bind('<ButtonRelease-1>', self._on_click)

    def _create_checkbox_images(self) -> Dict[str, tk.PhotoImage]:
        """체크박스 이미지 생성"""
        checked = tk.PhotoImage(data="""iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3QYQCgkjBwXb4gAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAABP0lEQVQ4y42TvU7CYBCGn69Go3+UhdDAyLi3tnwDMTvBwHdA6ObG5kZ0hcXxitjZMBCNjRtD7ELCIMQBhPr5cyDQtrS9zeVy977PPXd3CWKcNbN2uXEDWPUqkPPT8tZDjLNm1n4GLtdmgR/gEdCAN+AFuACuKhLdAvKlONpvAuECTv0WYK0VwJpTcYSYuC9KcVR1BJhY9lnO3cUogHMvFaCOyUcUYG/DABLmG/JRCNYMoOwIKLsCOHuOgNMdR8Bhcis6An6TW84R8DVnQmS17wzIb1EB5/lOgOfZEjA6f9MBLq0PmAV+Z5RFgPKkFp4A0q9pX9MwCxDivD/fDSCHwE8ZANpYXs8CNKlrB3iZB3iY1QSMzusmQA7BWvQqMDnNTj8BHsA7MB7XNfB1XB/X4wm0Ma/rRoB/+QOpG4qM0XlCSwAAAABJRU5ErkJggg==""")
        unchecked = tk.PhotoImage(data="""iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3QYQCgkuOdXk0wAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAAyklEQVQ4y7WTsW0CQRRE36zoghI8xdzRcweuMF24A+jAJdCB3QElkJkASXQARTCUcAk3xpmJAyGw9tFu8P+fmf9nVnALXxvj9wEQcYTJOl7HsZ2AQnpZZCS5Q//oXJWoeR5QA0q/3YGGrx/A3XcNyPzWGbSvQgR31w7QWgMHF9bh9g2sgbJGbQGQ5Z6uTp8H69BbDXAHqCKFg0L7W1uA2pLG91hAYe0CCgtQFeCg9AeVrOsO+UEAy2QO+gUANM/rXfbPDLhDOkk5yUk6/QES8HahwMAXxgAAAABJRU5ErkJggg==""")
        return {"checked": checked, "unchecked": unchecked}

    def insert(self, parent, index, iid=None, **kwargs) -> str:
        """아이템 삽입 시 체크박스 변수 생성"""
        item = super().insert(parent, index, iid, **kwargs)
        self.checkboxes[item] = tk.BooleanVar(value=False)
        self.set(item, self.checkbox_column, "")
        self._set_checkbox_image(item)
        return item

    def _set_checkbox_image(self, item):
        """체크박스 이미지 설정"""
        if self.checkboxes[item].get():
            self.item(item, image=self.checkbox_images["checked"], values=self.item(item, 'values'))
        else:
            self.item(item, image=self.checkbox_images["unchecked"], values=self.item(item, 'values'))

    def _on_click(self, event):
        """클릭 이벤트 처리"""
        region = self.identify('region', event.x, event.y)
        if region == "tree":
            # 체크박스 열에서 클릭된 경우만 처리
            column = self.identify_column(event.x)
            if column == f"#{self.column(self.checkbox_column, 'id')}":
                item = self.identify_row(event.y)
                if item in self.checkboxes:
                    # 체크박스 상태 전환
                    self.checkboxes[item].set(not self.checkboxes[item].get())
                    self._set_checkbox_image(item)
                    # 체크박스 변경 이벤트 호출
                    self.event_generate('<<CheckboxToggled>>', when='tail')

    def is_checked(self, item) -> bool:
        """아이템의 체크 상태 반환"""
        return self.checkboxes.get(item, tk.BooleanVar(value=False)).get()

    def check(self, item):
        """아이템 체크"""
        if item in self.checkboxes:
            self.checkboxes[item].set(True)
            self._set_checkbox_image(item)

    def uncheck(self, item):
        """아이템 체크 해제"""
        if item in self.checkboxes:
            self.checkboxes[item].set(False)
            self._set_checkbox_image(item)

    def toggle(self, item):
        """아이템 체크 상태 전환"""
        if item in self.checkboxes:
            self.checkboxes[item].set(not self.checkboxes[item].get())
            self._set_checkbox_image(item)

    def get_checked_items(self) -> List[str]:
        """체크된 모든 아이템 ID 반환"""
        return [item for item in self.checkboxes if self.checkboxes[item].get()]


class ScrollableTreeview(ttk.Frame):
    """스크롤바가 있는 트리뷰 프레임"""
    def __init__(self, master=None, treeview_class=ttk.Treeview, **kwargs):
        super().__init__(master)

        # 스크롤바 생성
        self.vsb = ttk.Scrollbar(self, orient="vertical")
        self.hsb = ttk.Scrollbar(self, orient="horizontal")

        # 트리뷰 생성
        self.treeview = treeview_class(self, **kwargs)

        # 스크롤바 연결
        self.vsb.config(command=self.treeview.yview)
        self.hsb.config(command=self.treeview.xview)
        self.treeview.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        # 위젯 배치
        self.treeview.grid(column=0, row=0, sticky='nsew')
        self.vsb.grid(column=1, row=0, sticky='ns')
        self.hsb.grid(column=0, row=1, sticky='ew')

        # 그리드 설정
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)


class ContextMenuMixin:
    """컨텍스트 메뉴 기능을 제공하는 Mixin 클래스"""
    def __init__(self):
        self.context_menu = None
        self.bind('<Button-3>', self.show_context_menu)

    def create_context_menu(self, items: List[Dict[str, Any]]):
        """컨텍스트 메뉴 생성

        Args:
            items: 메뉴 항목 목록. 각 항목은 {'label': '라벨', 'command': 콜백함수, 'state': 'normal/disabled'} 형식
        """
        # 기존 메뉴 제거
        if self.context_menu:
            self.context_menu.destroy()

        # 새 메뉴 생성
        self.context_menu = tk.Menu(self, tearoff=0)

        # 메뉴 항목 추가
        for item in items:
            if item.get('separator', False):
                self.context_menu.add_separator()
            else:
                self.context_menu.add_command(
                    label=item.get('label', ''),
                    command=item.get('command', lambda: None),
                    state=item.get('state', 'normal')
                )

    def show_context_menu(self, event):
        """컨텍스트 메뉴 표시"""
        if self.context_menu:
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()


class SearchableCombobox(ttk.Combobox):
    """검색 기능이 있는 콤보박스"""
    def __init__(self, master=None, **kwargs):
        self.var = kwargs.get('textvariable') or tk.StringVar()
        kwargs['textvariable'] = self.var

        super().__init__(master, **kwargs)

        self.bind('<KeyRelease>', self._on_key_release)
        self._original_values = []

    def set_values(self, values):
        """콤보박스 값 설정 및 원본 값 저장"""
        self._original_values = list(values)
        self['values'] = self._original_values

    def _on_key_release(self, event):
        """키 입력 시 검색 수행"""
        if event.keysym in ('Up', 'Down', 'Return', 'Escape'):
            return

        current_text = self.var.get().lower()
        if current_text:
            filtered = [v for v in self._original_values if current_text in str(v).lower()]
            self['values'] = filtered
            self.event_generate('<Down>')
        else:
            self['values'] = self._original_values


class StatusBar(ttk.Frame):
    """상태 바 위젯"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        # 기본 상태 텍스트
        self.status_var = tk.StringVar(value="준비")
        self.status_label = ttk.Label(self, textvariable=self.status_var, anchor="w")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)

        # 오른쪽 정보 텍스트
        self.info_var = tk.StringVar()
        self.info_label = ttk.Label(self, textvariable=self.info_var, anchor="e")
        self.info_label.pack(side=tk.RIGHT, padx=5, pady=2)

        # 진행 표시기
        self.progress_var = tk.IntVar()
        self.progress = ttk.Progressbar(
            self, 
            variable=self.progress_var, 
            mode="determinate",
            length=100
        )
        self.progress.pack(side=tk.RIGHT, padx=5, pady=2)
        self.progress.pack_forget()  # 초기에는 숨김

    def set_status(self, text):
        """상태 텍스트 설정"""
        self.status_var.set(text)
        self.update_idletasks()

    def set_info(self, text):
        """정보 텍스트 설정"""
        self.info_var.set(text)
        self.update_idletasks()

    def start_progress(self, maximum=100):
        """진행 표시기 시작"""
        self.progress["maximum"] = maximum
        self.progress_var.set(0)
        self.progress.pack(side=tk.RIGHT, padx=5, pady=2)

    def update_progress(self, value):
        """진행 표시기 업데이트"""
        self.progress_var.set(value)
        self.update_idletasks()

    def stop_progress(self):
        """진행 표시기 중지 및 숨김"""
        self.progress.pack_forget()
        self.update_idletasks()
