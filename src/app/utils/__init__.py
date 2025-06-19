# app.utils 패키지 초기화
# 유틸리티 함수들

# 기존 utils.py의 함수들을 import하여 호환성 유지
import sys
import os

# 부모 디렉토리의 utils.py 모듈에 접근
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
utils_file = os.path.join(parent_dir, 'utils.py')

if os.path.exists(utils_file):
    # utils.py 파일을 직접 import
    import importlib.util
    spec = importlib.util.spec_from_file_location("legacy_utils", utils_file)
    legacy_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_utils)
    
    # 기존 함수들을 현재 네임스페이스로 가져오기
    create_treeview_with_scrollbar = legacy_utils.create_treeview_with_scrollbar
    create_label_entry_pair = legacy_utils.create_label_entry_pair
    format_num_value = legacy_utils.format_num_value
    generate_unique_filename = legacy_utils.generate_unique_filename
    open_folder_dialog = legacy_utils.open_folder_dialog
    open_file_dialog = legacy_utils.open_file_dialog
    save_file_dialog = legacy_utils.save_file_dialog
    create_sqlite_connection = legacy_utils.create_sqlite_connection
    execute_query = legacy_utils.execute_query
    excel_to_dataframe = legacy_utils.excel_to_dataframe
    dataframe_to_excel = legacy_utils.dataframe_to_excel
    create_backup = legacy_utils.create_backup
    compare_values = legacy_utils.compare_values
    verify_password = legacy_utils.verify_password
    change_maintenance_password = legacy_utils.change_maintenance_password
    
    # __all__ 정의하여 명시적으로 export
    __all__ = [
        'create_treeview_with_scrollbar',
        'create_label_entry_pair', 
        'format_num_value',
        'generate_unique_filename',
        'open_folder_dialog',
        'open_file_dialog', 
        'save_file_dialog',
        'create_sqlite_connection',
        'execute_query',
        'excel_to_dataframe',
        'dataframe_to_excel',
        'create_backup',
        'compare_values',
        'verify_password',
        'change_maintenance_password'
    ] 