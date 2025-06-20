# Enhanced 비교 기능 - Default DB 비교 모드 지원

import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from app.widgets import CheckboxTreeview
from app.utils import create_treeview_with_scrollbar, format_num_value
from app.schema import DBSchema

class EnhancedComparisonMode:
    """향상된 비교 모드 클래스"""
    
    FILE_TO_FILE = "file_to_file"
    FILE_TO_DEFAULT_DB = "file_to_default_db"
    
    @staticmethod
    def get_mode_description(mode):
        """모드 설명 반환"""
        descriptions = {
            EnhancedComparisonMode.FILE_TO_FILE: "파일 간 비교 (기존 방식)",
            EnhancedComparisonMode.FILE_TO_DEFAULT_DB: "파일 vs Default DB 비교"
        }
        return descriptions.get(mode, "알 수 없는 모드")

def add_enhanced_comparison_functions_to_class(cls):
    """
    DBManager 클래스에 향상된 비교 기능을 추가합니다.
    """
    
    def create_enhanced_comparison_tab(self):
        """향상된 비교 탭 생성 - Default DB 비교 모드 포함"""
        enhanced_comparison_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(enhanced_comparison_tab, text="🆕 DB 비교")

        # 상단 컨트롤 프레임
        control_frame = ttk.Frame(enhanced_comparison_tab, padding=(10, 5))
        control_frame.pack(fill=tk.X)

        # 비교 모드 선택 프레임
        mode_frame = ttk.LabelFrame(control_frame, text="비교 모드 선택", padding=10)
        mode_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # 비교 모드 라디오 버튼
        self.comparison_mode_var = tk.StringVar(value=EnhancedComparisonMode.FILE_TO_FILE)
        
        file_to_file_radio = ttk.Radiobutton(
            mode_frame, 
            text="파일 간 비교", 
            variable=self.comparison_mode_var, 
            value=EnhancedComparisonMode.FILE_TO_FILE,
            command=self.on_comparison_mode_changed
        )
        file_to_file_radio.pack(anchor="w", pady=2)
        
        file_to_db_radio = ttk.Radiobutton(
            mode_frame, 
            text="파일 vs Default DB 비교", 
            variable=self.comparison_mode_var, 
            value=EnhancedComparisonMode.FILE_TO_DEFAULT_DB,
            command=self.on_comparison_mode_changed
        )
        file_to_db_radio.pack(anchor="w", pady=2)

        # Default DB 설정 프레임
        db_settings_frame = ttk.LabelFrame(control_frame, text="Default DB 설정", padding=10)
        db_settings_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # 장비 유형 선택
        ttk.Label(db_settings_frame, text="장비 유형:").pack(anchor="w")
        self.enhanced_equipment_type_var = tk.StringVar()
        self.enhanced_equipment_type_combobox = ttk.Combobox(
            db_settings_frame, 
            textvariable=self.enhanced_equipment_type_var, 
            state="readonly", 
            width=20
        )
        self.enhanced_equipment_type_combobox.pack(anchor="w", pady=(0, 5))
        self.enhanced_equipment_type_combobox.bind("<<ComboboxSelected>>", self.on_enhanced_equipment_type_selected)

        # Performance 모드 체크박스
        self.enhanced_performance_mode_var = tk.BooleanVar(value=False)
        self.enhanced_performance_checkbox = ttk.Checkbutton(
            db_settings_frame,
            text="Performance 항목만",
            variable=self.enhanced_performance_mode_var,
            command=self.on_enhanced_performance_mode_changed
        )
        self.enhanced_performance_checkbox.pack(anchor="w", pady=2)

        # 새로고침 버튼
        refresh_btn = ttk.Button(
            db_settings_frame, 
            text="🔄 새로고침", 
            command=self.refresh_enhanced_comparison_data
        )
        refresh_btn.pack(anchor="w", pady=(5, 0))

        # 중간 프레임 - 비교 정보
        info_frame = ttk.Frame(enhanced_comparison_tab, padding=(10, 5))
        info_frame.pack(fill=tk.X)

        # 비교 정보 레이블
        self.enhanced_comparison_info_label = ttk.Label(
            info_frame, 
            text="비교 모드: 파일 간 비교", 
            font=("Arial", 10, "bold")
        )
        self.enhanced_comparison_info_label.pack(side=tk.LEFT)

        # 결과 통계
        self.enhanced_comparison_stats_label = ttk.Label(
            info_frame, 
            text="비교 결과: 준비 중..."
        )
        self.enhanced_comparison_stats_label.pack(side=tk.RIGHT)

        # 메인 비교 결과 프레임
        main_frame = ttk.Frame(enhanced_comparison_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 비교 결과 트리뷰
        columns = ("parameter", "file_value", "default_value", "difference", "status")
        headings = {
            "parameter": "파라미터",
            "file_value": "파일 값",
            "default_value": "Default DB 값",
            "difference": "차이점",
            "status": "상태"
        }
        column_widths = {
            "parameter": 250,
            "file_value": 150,
            "default_value": 150,
            "difference": 200,
            "status": 100
        }

        comparison_result_frame, self.enhanced_comparison_tree = create_treeview_with_scrollbar(
            main_frame, columns, headings, column_widths, height=20
        )
        comparison_result_frame.pack(fill=tk.BOTH, expand=True)

        # 컨텍스트 메뉴 생성
        self.create_enhanced_comparison_context_menu()
        self.enhanced_comparison_tree.bind("<Button-3>", self.show_enhanced_comparison_context_menu)

        # 초기 설정
        self.load_enhanced_equipment_types()
        self.on_comparison_mode_changed()

    def create_enhanced_comparison_context_menu(self):
        """향상된 비교 탭 컨텍스트 메뉴 생성"""
        self.enhanced_comparison_context_menu = tk.Menu(self.enhanced_comparison_tree, tearoff=0)
        self.enhanced_comparison_context_menu.add_command(
            label="Default DB 값으로 업데이트", 
            command=self.update_to_default_value
        )
        self.enhanced_comparison_context_menu.add_command(
            label="파일 값으로 Default DB 업데이트", 
            command=self.update_default_db_value
        )
        self.enhanced_comparison_context_menu.add_separator()
        self.enhanced_comparison_context_menu.add_command(
            label="차이점 상세 정보", 
            command=self.show_difference_details
        )

    def show_enhanced_comparison_context_menu(self, event):
        """향상된 비교 컨텍스트 메뉴 표시"""
        item = self.enhanced_comparison_tree.identify_row(event.y)
        if item:
            self.enhanced_comparison_tree.selection_set(item)
            self.enhanced_comparison_context_menu.post(event.x_root, event.y_root)

    def load_enhanced_equipment_types(self):
        """향상된 비교용 장비 유형 목록 로드"""
        try:
            if not hasattr(self, 'db_schema') or not self.db_schema:
                self.update_log("❌ DB 스키마가 초기화되지 않았습니다.")
                return

            equipment_types = self.db_schema.get_equipment_types()
            
            if equipment_types:
                self.enhanced_equipment_types = {name: id for id, name, desc in equipment_types}
                self.enhanced_equipment_type_combobox['values'] = list(self.enhanced_equipment_types.keys())
                
                # 첫 번째 항목 선택
                if self.enhanced_equipment_types:
                    first_type = list(self.enhanced_equipment_types.keys())[0]
                    self.enhanced_equipment_type_combobox.set(first_type)
                    
                self.update_log(f"✅ 향상된 비교용 장비 유형 로드 완료: {len(equipment_types)}개")
            else:
                self.enhanced_equipment_types = {}
                self.enhanced_equipment_type_combobox['values'] = []
                self.update_log("⚠️ 등록된 장비 유형이 없습니다.")

        except Exception as e:
            error_msg = f"향상된 비교용 장비 유형 로드 실패: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)

    def on_comparison_mode_changed(self):
        """비교 모드 변경 시 호출"""
        mode = self.comparison_mode_var.get()
        mode_desc = EnhancedComparisonMode.get_mode_description(mode)
        
        # UI 상태 업데이트
        if mode == EnhancedComparisonMode.FILE_TO_DEFAULT_DB:
            # Default DB 비교 모드
            self.enhanced_equipment_type_combobox.config(state="readonly")
            self.enhanced_performance_checkbox.config(state="normal")
        else:
            # 파일 간 비교 모드
            self.enhanced_equipment_type_combobox.config(state="disabled")
            self.enhanced_performance_checkbox.config(state="disabled")

        self.enhanced_comparison_info_label.config(text=f"비교 모드: {mode_desc}")
        self.update_log(f"🔄 비교 모드 변경: {mode_desc}")

        # 비교 결과 업데이트
        self.update_enhanced_comparison_view()

    def on_enhanced_equipment_type_selected(self, event=None):
        """장비 유형 선택 변경 시 호출"""
        selected_type = self.enhanced_equipment_type_var.get()
        if selected_type:
            self.update_log(f"🎯 선택된 장비 유형: {selected_type}")
            self.update_enhanced_comparison_view()

    def on_enhanced_performance_mode_changed(self):
        """Performance 모드 변경 시 호출"""
        performance_mode = self.enhanced_performance_mode_var.get()
        mode_text = "Performance 항목만" if performance_mode else "전체 항목"
        self.update_log(f"🔄 Performance 모드: {mode_text}")
        self.update_enhanced_comparison_view()

    def refresh_enhanced_comparison_data(self):
        """향상된 비교 데이터 새로고침"""
        self.load_enhanced_equipment_types()
        self.update_enhanced_comparison_view()
        messagebox.showinfo("새로고침 완료", "비교 데이터가 최신 상태로 업데이트되었습니다.")

    def update_enhanced_comparison_view(self):
        """향상된 비교 뷰 업데이트"""
        # 기존 결과 클리어
        for item in self.enhanced_comparison_tree.get_children():
            self.enhanced_comparison_tree.delete(item)

        mode = self.comparison_mode_var.get()
        
        if mode == EnhancedComparisonMode.FILE_TO_DEFAULT_DB:
            self._update_file_to_default_db_comparison()
        else:
            self._update_file_to_file_comparison()

    def _update_file_to_default_db_comparison(self):
        """파일 vs Default DB 비교 업데이트"""
        try:
            # 선택된 장비 유형 확인
            selected_type = self.enhanced_equipment_type_var.get()
            if not selected_type or selected_type not in self.enhanced_equipment_types:
                self.enhanced_comparison_stats_label.config(text="장비 유형을 선택해주세요.")
                return

            # 업로드된 파일 확인
            if not hasattr(self, 'merged_df') or self.merged_df is None:
                self.enhanced_comparison_stats_label.config(text="먼저 파일을 업로드해주세요.")
                return

            # Default DB 데이터 로드
            equipment_type_id = self.enhanced_equipment_types[selected_type]
            performance_only = self.enhanced_performance_mode_var.get()
            
            default_values = self.db_schema.get_default_values(equipment_type_id, performance_only=performance_only)
            
            if not default_values:
                mode_text = "Performance 항목" if performance_only else "전체 항목"
                self.enhanced_comparison_stats_label.config(
                    text=f"선택된 장비 유형에 {mode_text}이 없습니다."
                )
                return

            # 비교 수행
            comparison_results = self._perform_file_to_default_comparison(default_values)
            
            # 결과 표시
            self._display_comparison_results(comparison_results)
            
        except Exception as e:
            error_msg = f"파일 vs Default DB 비교 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            self.enhanced_comparison_stats_label.config(text="비교 중 오류 발생")

    def _perform_file_to_default_comparison(self, default_values):
        """파일과 Default DB 간 실제 비교 수행"""
        comparison_results = []
        
        # Default DB 값들을 딕셔너리로 변환 (parameter_name을 키로)
        default_dict = {}
        for row in default_values:
            param_name = row[1]  # parameter_name
            default_value = row[2]  # default_value
            min_spec = row[3]  # min_spec
            max_spec = row[4]  # max_spec
            default_dict[param_name] = {
                'value': default_value,
                'min_spec': min_spec,
                'max_spec': max_spec
            }

        # 파일 데이터와 비교
        for _, file_row in self.merged_df.iterrows():
            # 파라미터 이름 생성 (Part_ItemName 형식)
            part = file_row.get('Part', '')
            item_name = file_row.get('ItemName', '')
            param_name = f"{part}_{item_name}"
            
            # 파일 값 (첫 번째 파일 값 사용)
            file_value = None
            for col in self.merged_df.columns:
                if col not in ['Module', 'Part', 'ItemName'] and pd.notna(file_row[col]):
                    file_value = str(file_row[col])
                    break
            
            if file_value is None:
                continue

            # Default DB에서 해당 파라미터 찾기
            if param_name in default_dict:
                default_info = default_dict[param_name]
                default_value = default_info['value']
                
                # 차이점 분석
                difference = self._analyze_difference(file_value, default_value, default_info)
                status = self._get_comparison_status(difference)
                
                comparison_results.append({
                    'parameter': param_name,
                    'file_value': file_value,
                    'default_value': default_value,
                    'difference': difference['description'],
                    'status': status,
                    'full_info': difference
                })
            else:
                # Default DB에 없는 파라미터
                comparison_results.append({
                    'parameter': param_name,
                    'file_value': file_value,
                    'default_value': "-",
                    'difference': "Default DB에 없음",
                    'status': "신규",
                    'full_info': {'type': 'missing_in_default'}
                })

        return comparison_results

    def _analyze_difference(self, file_value, default_value, default_info):
        """차이점 분석"""
        try:
            # 문자열 비교
            if str(file_value) == str(default_value):
                return {'type': 'match', 'description': '일치'}
            
            # 수치 비교 시도
            try:
                file_num = float(file_value)
                default_num = float(default_value)
                
                # 사양 범위 확인
                min_spec = default_info.get('min_spec')
                max_spec = default_info.get('max_spec')
                
                if min_spec and max_spec:
                    min_val = float(min_spec)
                    max_val = float(max_spec)
                    
                    if file_num < min_val:
                        return {
                            'type': 'below_spec',
                            'description': f'사양 미달 (최소: {min_spec})'
                        }
                    elif file_num > max_val:
                        return {
                            'type': 'above_spec',
                            'description': f'사양 초과 (최대: {max_spec})'
                        }
                
                # 수치 차이 계산
                diff = abs(file_num - default_num)
                diff_percent = (diff / abs(default_num) * 100) if default_num != 0 else 0
                
                return {
                    'type': 'numeric_diff',
                    'description': f'차이: {diff:.3f} ({diff_percent:.1f}%)'
                }
                
            except ValueError:
                # 문자열 차이
                return {
                    'type': 'text_diff',
                    'description': f'값 다름: "{file_value}" ≠ "{default_value}"'
                }
                
        except Exception:
            return {'type': 'error', 'description': '비교 오류'}

    def _get_comparison_status(self, difference):
        """비교 상태 결정"""
        diff_type = difference.get('type', 'unknown')
        
        status_map = {
            'match': '✅ 일치',
            'below_spec': '❌ 사양미달',
            'above_spec': '❌ 사양초과',
            'numeric_diff': '⚠️ 차이',
            'text_diff': '⚠️ 다름',
            'error': '❓ 오류'
        }
        
        return status_map.get(diff_type, '❓ 알수없음')

    def _display_comparison_results(self, comparison_results):
        """비교 결과 표시"""
        total_count = len(comparison_results)
        match_count = sum(1 for r in comparison_results if r['status'] == '✅ 일치')
        diff_count = total_count - match_count
        
        # 통계 업데이트
        self.enhanced_comparison_stats_label.config(
            text=f"총 {total_count}개 | 일치: {match_count}개 | 차이: {diff_count}개"
        )
        
        # 트리뷰에 결과 추가
        for result in comparison_results:
            item_id = self.enhanced_comparison_tree.insert("", "end", values=(
                result['parameter'],
                result['file_value'],
                result['default_value'],
                result['difference'],
                result['status']
            ))
            
            # 상태에 따른 색상 설정
            if result['status'] == '✅ 일치':
                self.enhanced_comparison_tree.set(item_id, "status", result['status'])
            elif '❌' in result['status']:
                self.enhanced_comparison_tree.item(item_id, tags=('error',))
            elif '⚠️' in result['status']:
                self.enhanced_comparison_tree.item(item_id, tags=('warning',))
        
        # 태그 색상 설정
        self.enhanced_comparison_tree.tag_configure('error', background='#ffcccc')
        self.enhanced_comparison_tree.tag_configure('warning', background='#ffffcc')

    def _update_file_to_file_comparison(self):
        """파일 간 비교 업데이트 (기존 방식)"""
        self.enhanced_comparison_stats_label.config(text="파일 간 비교 모드 - 기존 '비교' 탭을 사용하세요.")

    def update_to_default_value(self):
        """선택된 항목을 Default DB 값으로 업데이트"""
        # 구현 예정 - 파일의 값을 Default DB 값으로 변경
        messagebox.showinfo("알림", "이 기능은 향후 구현 예정입니다.")

    def update_default_db_value(self):
        """파일 값으로 Default DB 업데이트"""
        # 구현 예정 - Default DB의 값을 파일 값으로 변경
        messagebox.showinfo("알림", "이 기능은 향후 구현 예정입니다.")

    def show_difference_details(self):
        """차이점 상세 정보 표시"""
        selected_items = self.enhanced_comparison_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        values = self.enhanced_comparison_tree.item(item, "values")
        
        detail_text = f"""
파라미터: {values[0]}
파일 값: {values[1]}
Default DB 값: {values[2]}
차이점: {values[3]}
상태: {values[4]}
        """
        
        messagebox.showinfo("차이점 상세 정보", detail_text.strip())

    # 클래스에 메서드 추가
    cls.create_enhanced_comparison_tab = create_enhanced_comparison_tab
    cls.create_enhanced_comparison_context_menu = create_enhanced_comparison_context_menu
    cls.show_enhanced_comparison_context_menu = show_enhanced_comparison_context_menu
    cls.load_enhanced_equipment_types = load_enhanced_equipment_types
    cls.on_comparison_mode_changed = on_comparison_mode_changed
    cls.on_enhanced_equipment_type_selected = on_enhanced_equipment_type_selected
    cls.on_enhanced_performance_mode_changed = on_enhanced_performance_mode_changed
    cls.refresh_enhanced_comparison_data = refresh_enhanced_comparison_data
    cls.update_enhanced_comparison_view = update_enhanced_comparison_view
    cls._update_file_to_default_db_comparison = _update_file_to_default_db_comparison
    cls._perform_file_to_default_comparison = _perform_file_to_default_comparison
    cls._analyze_difference = _analyze_difference
    cls._get_comparison_status = _get_comparison_status
    cls._display_comparison_results = _display_comparison_results
    cls._update_file_to_file_comparison = _update_file_to_file_comparison
    cls.update_to_default_value = update_to_default_value
    cls.update_default_db_value = update_default_db_value
    cls.show_difference_details = show_difference_details 