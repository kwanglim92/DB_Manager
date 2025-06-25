# 대화상자 도우미 모듈
# manager.py에서 추출된 공통 대화상자 패턴들

import tkinter as tk
from tkinter import ttk, messagebox
from app.utils import create_label_entry_pair


def center_dialog(dialog, width=450, height=420):
    """
    대화상자를 화면 중앙에 배치
    
    Args:
        dialog: tkinter 대화상자 객체
        width: 대화상자 너비
        height: 대화상자 높이
    """
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")


def validate_numeric_range(min_val_str, max_val_str):
    """
    숫자 범위 유효성 검사
    
    Args:
        min_val_str: 최소값 문자열
        max_val_str: 최대값 문자열
        
    Returns:
        tuple: (is_valid, min_val, max_val, error_message)
    """
    try:
        # 빈 값 허용
        min_val = None if not min_val_str.strip() else float(min_val_str)
        max_val = None if not max_val_str.strip() else float(max_val_str)
        
        # 범위 검증
        if min_val is not None and max_val is not None and min_val > max_val:
            return False, None, None, "최소값이 최대값보다 클 수 없습니다."
        
        return True, min_val, max_val, None
        
    except ValueError:
        return False, None, None, "유효한 숫자를 입력해주세요."


def create_parameter_dialog(parent, title, mode="add", param_data=None):
    """
    파라미터 추가/편집 대화상자 생성
    
    Args:
        parent: 부모 창
        title: 대화상자 제목
        mode: "add" 또는 "edit"
        param_data: 편집 모드일 때 기존 데이터
        
    Returns:
        tuple: (dialog, field_vars) - 대화상자와 입력 필드 변수들
    """
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.grab_set()
    
    # 기존 데이터에서 초기값 추출
    if param_data and mode == "edit":
        initial_values = {
            'name': param_data.get('parameter_name', ''),
            'default': param_data.get('default_value', ''),
            'min_spec': param_data.get('min_spec', ''),
            'max_spec': param_data.get('max_spec', ''),
            'description': param_data.get('description', ''),
            'module': param_data.get('module_name', ''),
            'part': param_data.get('part_name', ''),
            'item_type': param_data.get('item_type', 'double')
        }
    else:
        initial_values = {
            'name': '', 'default': '', 'min_spec': '', 'max_spec': '',
            'description': '', 'module': '', 'part': '', 'item_type': 'double'
        }
    
    # 메인 프레임
    main_frame = ttk.Frame(dialog, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 입력 필드들
    field_vars = {}
    
    # Parameter Name
    name_var, name_entry = create_label_entry_pair(main_frame, "Parameter Name:", 0, initial_values['name'])
    field_vars['name'] = name_var
    name_entry.grid(sticky="ew")
    
    # Module Name
    module_var, module_entry = create_label_entry_pair(main_frame, "Module:", 1, initial_values['module'])
    field_vars['module'] = module_var
    module_entry.grid(sticky="ew")
    
    # Part Name
    part_var, part_entry = create_label_entry_pair(main_frame, "Part:", 2, initial_values['part'])
    field_vars['part'] = part_var
    part_entry.grid(sticky="ew")
    
    # Default Value
    default_var, default_entry = create_label_entry_pair(main_frame, "Default Value:", 3, initial_values['default'])
    field_vars['default'] = default_var
    default_entry.grid(sticky="ew")
    
    # Min Spec
    min_var, min_entry = create_label_entry_pair(main_frame, "Min Spec:", 4, initial_values['min_spec'])
    field_vars['min_spec'] = min_var
    min_entry.grid(sticky="ew")
    
    # Max Spec
    max_var, max_entry = create_label_entry_pair(main_frame, "Max Spec:", 5, initial_values['max_spec'])
    field_vars['max_spec'] = max_var
    max_entry.grid(sticky="ew")
    
    # Item Type
    ttk.Label(main_frame, text="Item Type:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
    item_type_var = tk.StringVar(value=initial_values['item_type'])
    field_vars['item_type'] = item_type_var
    item_type_combo = ttk.Combobox(main_frame, textvariable=item_type_var,
                                   values=["double", "int", "string", "bool"], state="readonly")
    item_type_combo.grid(row=6, column=1, padx=5, pady=5, sticky="ew")
    
    # Description
    ttk.Label(main_frame, text="Description:").grid(row=7, column=0, padx=5, pady=5, sticky="nw")
    desc_var = tk.StringVar(value=initial_values['description'])
    field_vars['description'] = desc_var
    desc_text = tk.Text(main_frame, height=3, width=30)
    desc_text.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
    desc_text.insert('1.0', initial_values['description'])
    
    # Description Text 위젯을 위한 특별 처리
    field_vars['description_text'] = desc_text
    
    # 그리드 컬럼 가중치 설정
    main_frame.columnconfigure(1, weight=1)
    
    # 버튼 프레임
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=8, column=0, columnspan=2, pady=10)
    
    # 대화상자 크기 조정 및 중앙 배치
    center_dialog(dialog, 500, 380)
    
    return dialog, field_vars, button_frame


def create_filter_panel(parent, filter_config):
    """
    공통 필터 패널 생성
    
    Args:
        parent: 부모 프레임
        filter_config: 필터 설정 딕셔너리
            {
                'has_search': bool,
                'has_module': bool,
                'has_part': bool,
                'has_data_type': bool,
                'search_var': tk.StringVar,
                'module_var': tk.StringVar,
                'part_var': tk.StringVar,
                'data_type_var': tk.StringVar,
                'callbacks': {
                    'search': callable,
                    'module': callable,
                    'part': callable,
                    'data_type': callable
                }
            }
            
    Returns:
        dict: 생성된 위젯들의 참조
    """
    widgets = {}
    
    # 메인 필터 프레임
    main_filter_frame = ttk.Frame(parent)
    main_filter_frame.pack(fill=tk.X, pady=(0, 5), padx=10)
    widgets['main_frame'] = main_filter_frame
    
    current_row = 0
    
    # 검색 기능
    if filter_config.get('has_search', False):
        search_frame = ttk.Frame(main_filter_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_frame, text="🔎 Search:").pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(search_frame, textvariable=filter_config['search_var'])
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        widgets['search_entry'] = search_entry
        
        # 검색 이벤트 바인딩
        if filter_config.get('callbacks', {}).get('search'):
            search_entry.bind('<KeyRelease>', filter_config['callbacks']['search'])
        
        clear_btn = ttk.Button(search_frame, text="Clear", 
                              command=lambda: filter_config['search_var'].set(""))
        clear_btn.pack(side=tk.LEFT)
        widgets['clear_button'] = clear_btn
        
        current_row += 1
    
    # 고급 필터 섹션
    if any(filter_config.get(k, False) for k in ['has_module', 'has_part', 'has_data_type']):
        # 구분선
        separator = ttk.Separator(main_filter_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)
        
        # 고급 필터 프레임
        advanced_frame = ttk.Frame(main_filter_frame)
        advanced_frame.pack(fill=tk.X, pady=(5, 0))
        widgets['advanced_frame'] = advanced_frame
        
        col = 0
        
        # Module 필터
        if filter_config.get('has_module', False):
            module_frame = ttk.Frame(advanced_frame)
            module_frame.grid(row=0, column=col, padx=(0, 10), sticky="ew")
            
            ttk.Label(module_frame, text="Module:").pack(side=tk.TOP, anchor="w")
            module_combo = ttk.Combobox(module_frame, textvariable=filter_config['module_var'],
                                       values=["All"], state="readonly", width=15)
            module_combo.pack(side=tk.TOP, fill=tk.X)
            widgets['module_combo'] = module_combo
            
            if filter_config.get('callbacks', {}).get('module'):
                module_combo.bind('<<ComboboxSelected>>', filter_config['callbacks']['module'])
            
            col += 1
        
        # Part 필터
        if filter_config.get('has_part', False):
            part_frame = ttk.Frame(advanced_frame)
            part_frame.grid(row=0, column=col, padx=(0, 10), sticky="ew")
            
            ttk.Label(part_frame, text="Part:").pack(side=tk.TOP, anchor="w")
            part_combo = ttk.Combobox(part_frame, textvariable=filter_config['part_var'],
                                     values=["All"], state="readonly", width=15)
            part_combo.pack(side=tk.TOP, fill=tk.X)
            widgets['part_combo'] = part_combo
            
            if filter_config.get('callbacks', {}).get('part'):
                part_combo.bind('<<ComboboxSelected>>', filter_config['callbacks']['part'])
            
            col += 1
        
        # Data Type 필터
        if filter_config.get('has_data_type', False):
            data_type_frame = ttk.Frame(advanced_frame)
            data_type_frame.grid(row=0, column=col, padx=(0, 10), sticky="ew")
            
            ttk.Label(data_type_frame, text="Data Type:").pack(side=tk.TOP, anchor="w")
            data_type_combo = ttk.Combobox(data_type_frame, textvariable=filter_config['data_type_var'],
                                          values=["All", "double", "int", "string", "bool"], 
                                          state="readonly", width=15)
            data_type_combo.pack(side=tk.TOP, fill=tk.X)
            widgets['data_type_combo'] = data_type_combo
            
            if filter_config.get('callbacks', {}).get('data_type'):
                data_type_combo.bind('<<ComboboxSelected>>', filter_config['callbacks']['data_type'])
        
        # 그리드 컬럼 가중치 설정
        for i in range(col + 1):
            advanced_frame.columnconfigure(i, weight=1)
    
    return widgets


def setup_tree_columns(tree, columns, column_configs=None):
    """
    TreeView 컬럼 설정
    
    Args:
        tree: TreeView 위젯
        columns: 컬럼 이름 리스트
        column_configs: 컬럼 설정 딕셔너리 (옵션)
            {
                'column_name': {'width': int, 'anchor': str, 'text': str}
            }
    """
    if column_configs is None:
        column_configs = {}
    
    for col in columns:
        config = column_configs.get(col, {})
        
        # 헤딩 설정
        text = config.get('text', col)
        tree.heading(col, text=text)
        
        # 컬럼 설정
        width = config.get('width', 100)
        anchor = config.get('anchor', 'center')
        tree.column(col, width=width, anchor=anchor)


def handle_error(operation_name, exception, update_log_callback=None, show_messagebox=True):
    """
    표준화된 오류 처리
    
    Args:
        operation_name: 작업 이름
        exception: 예외 객체
        update_log_callback: 로그 업데이트 콜백
        show_messagebox: 메시지박스 표시 여부
        
    Returns:
        str: 오류 메시지
    """
    error_msg = f"{operation_name} 중 오류 발생: {str(exception)}"
    
    if show_messagebox:
        messagebox.showerror("오류", error_msg)
    
    if update_log_callback:
        update_log_callback(f"❌ {error_msg}")
    
    return error_msg