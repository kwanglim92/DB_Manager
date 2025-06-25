"""
다양한 비교 전략 구현
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
from .base_comparison import BaseComparison


class SimpleComparison(BaseComparison):
    """간단한 비교 기능"""
    
    def create_ui(self, parent_frame):
        """간단한 비교 UI 생성"""
        self.frame = ttk.LabelFrame(parent_frame, text="간단 비교", padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 검색 프레임
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="검색:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # 트리뷰 생성
        columns = ['Module', 'Part', 'Item_Name', 'File1', 'File2', 'Difference']
        headings = {
            'Module': '모듈',
            'Part': '부품', 
            'Item_Name': '항목명',
            'File1': '파일1',
            'File2': '파일2',
            'Difference': '차이'
        }
        
        tree_frame, self.tree = self.create_treeview_with_scrollbar(
            self.frame, columns, headings, height=15
        )
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 컨텍스트 메뉴 설정
        self.setup_context_menu(self.tree)
    
    def update_view(self, data=None):
        """간단 비교 뷰 업데이트"""
        if self.tree is None:
            return
        
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if data is None or data.empty:
            return
        
        # 검색 필터 적용
        search_filter = getattr(self, 'search_var', tk.StringVar()).get()
        filtered_data = self.filter_data(data, search_filter)
        
        # 데이터 표시
        for _, row in filtered_data.iterrows():
            values = [
                row.get('Module', ''),
                row.get('Part', ''),
                row.get('Item_Name', ''),
                row.get('File1', ''),
                row.get('File2', ''),
                row.get('Difference', '')
            ]
            
            # 차이가 있는 경우 태그 설정
            tags = ('different',) if row.get('Difference', '') == 'Different' else ()
            
            self.tree.insert('', tk.END, values=values, tags=tags)
        
        # 태그 색상 설정
        self.tree.tag_configure('different', background='#FFEEAA')
    
    def process_data(self, file_data):
        """간단한 데이터 처리"""
        if not file_data or len(file_data) < 2:
            return pd.DataFrame()
        
        file1_data = file_data[0]
        file2_data = file_data[1]
        
        # 간단한 차이 분석
        comparison_result = []
        
        # 공통 키 생성 (Module, Part, Item_Name)
        file1_keys = set()
        file2_keys = set()
        
        for _, row in file1_data.iterrows():
            key = (row.get('Module', ''), row.get('Part', ''), row.get('Item_Name', ''))
            file1_keys.add(key)
        
        for _, row in file2_data.iterrows():
            key = (row.get('Module', ''), row.get('Part', ''), row.get('Item_Name', ''))
            file2_keys.add(key)
        
        all_keys = file1_keys.union(file2_keys)
        
        for key in all_keys:
            module, part, item_name = key
            
            # 각 파일에서 해당 키의 값 찾기
            file1_value = self._get_value_by_key(file1_data, key)
            file2_value = self._get_value_by_key(file2_data, key)
            
            difference = 'Different' if file1_value != file2_value else 'Same'
            
            comparison_result.append({
                'Module': module,
                'Part': part,
                'Item_Name': item_name,
                'File1': file1_value,
                'File2': file2_value,
                'Difference': difference
            })
        
        return pd.DataFrame(comparison_result)
    
    def _get_value_by_key(self, data, key):
        """키로 데이터에서 값 찾기"""
        module, part, item_name = key
        
        mask = (
            (data.get('Module', '') == module) & 
            (data.get('Part', '') == part) & 
            (data.get('Item_Name', '') == item_name)
        )
        
        matched_rows = data[mask]
        if not matched_rows.empty:
            # Value 컬럼이 있다면 반환, 없으면 첫 번째 값 반환
            if 'Value' in matched_rows.columns:
                return matched_rows.iloc[0]['Value']
            else:
                return str(matched_rows.iloc[0].values[0])
        
        return ''
    
    def on_search_changed(self, event=None):
        """검색어 변경 시 호출"""
        if hasattr(self, 'comparison_data') and self.comparison_data is not None:
            self.update_view(self.comparison_data)


class EnhancedComparison(BaseComparison):
    """향상된 비교 기능 (DB 비교 포함)"""
    
    def create_ui(self, parent_frame):
        """향상된 비교 UI 생성"""
        self.frame = ttk.LabelFrame(parent_frame, text="향상된 비교", padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 비교 모드 선택
        mode_frame = ttk.Frame(self.frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(mode_frame, text="비교 모드:").pack(side=tk.LEFT)
        self.comparison_mode = tk.StringVar(value="file_to_file")
        
        ttk.Radiobutton(mode_frame, text="파일 대 파일", variable=self.comparison_mode, 
                       value="file_to_file", command=self.on_mode_changed).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(mode_frame, text="파일 대 DB", variable=self.comparison_mode, 
                       value="file_to_db", command=self.on_mode_changed).pack(side=tk.LEFT, padx=(10, 0))
        
        # 장비 타입 선택 (DB 비교용)
        self.equipment_frame = ttk.Frame(self.frame)
        self.equipment_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.equipment_frame, text="장비 타입:").pack(side=tk.LEFT)
        self.equipment_var = tk.StringVar()
        self.equipment_combo = ttk.Combobox(self.equipment_frame, textvariable=self.equipment_var)
        self.equipment_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 성능 파라미터만 옵션
        self.performance_only = tk.BooleanVar()
        ttk.Checkbutton(self.equipment_frame, text="성능 파라미터만", 
                       variable=self.performance_only, command=self.on_filter_changed).pack(side=tk.LEFT, padx=(20, 0))
        
        # 초기에는 장비 프레임 숨김
        self.equipment_frame.pack_forget()
        
        # 검색 프레임
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="검색:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # 통계 프레임
        stats_frame = ttk.LabelFrame(self.frame, text="비교 통계", padding=5)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, text="통계 정보가 여기에 표시됩니다.")
        self.stats_label.pack()
        
        # 트리뷰 생성
        columns = ['Module', 'Part', 'Item_Name', 'File_Value', 'DB_Value', 'Difference', 'Confidence']
        headings = {
            'Module': '모듈',
            'Part': '부품',
            'Item_Name': '항목명', 
            'File_Value': '파일값',
            'DB_Value': 'DB값',
            'Difference': '차이',
            'Confidence': '신뢰도'
        }
        
        tree_frame, self.tree = self.create_treeview_with_scrollbar(
            self.frame, columns, headings, height=12
        )
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 컨텍스트 메뉴 설정
        self.setup_context_menu(self.tree)
        
        # 장비 타입 목록 로드
        self.load_equipment_types()
    
    def load_equipment_types(self):
        """장비 타입 목록을 로드합니다."""
        try:
            if self.manager.db_schema:
                equipment_types = self.manager.db_schema.get_equipment_types()
                type_names = [eq_type['type_name'] for eq_type in equipment_types]
                self.equipment_combo['values'] = type_names
        except Exception as e:
            self.manager.update_log(f"장비 타입 로드 실패: {str(e)}")
    
    def on_mode_changed(self):
        """비교 모드 변경 시 호출"""
        if self.comparison_mode.get() == "file_to_db":
            self.equipment_frame.pack(fill=tk.X, pady=(0, 10), before=self.frame.children[list(self.frame.children.keys())[-3]])
        else:
            self.equipment_frame.pack_forget()
    
    def on_filter_changed(self):
        """필터 변경 시 호출"""
        if hasattr(self, 'comparison_data') and self.comparison_data is not None:
            self.update_view(self.comparison_data)
    
    def update_view(self, data=None):
        """향상된 비교 뷰 업데이트"""
        if self.tree is None:
            return
        
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if data is None or data.empty:
            self.update_statistics(pd.DataFrame())
            return
        
        # 필터 적용
        search_filter = getattr(self, 'search_var', tk.StringVar()).get()
        filtered_data = self.filter_data(data, search_filter)
        
        # 성능 파라미터 필터
        if self.performance_only.get():
            filtered_data = filtered_data[filtered_data.get('Is_Performance', False)]
        
        # 데이터 표시
        for _, row in filtered_data.iterrows():
            values = [
                row.get('Module', ''),
                row.get('Part', ''),
                row.get('Item_Name', ''),
                row.get('File_Value', ''),
                row.get('DB_Value', ''),
                row.get('Difference', ''),
                f"{row.get('Confidence', 0):.1f}%" if pd.notna(row.get('Confidence', 0)) else ''
            ]
            
            # 차이와 신뢰도에 따른 태그 설정
            tags = []
            if row.get('Difference', '') == 'Different':
                confidence = row.get('Confidence', 0)
                if confidence < 50:
                    tags.append('low_confidence')
                else:
                    tags.append('different')
            
            self.tree.insert('', tk.END, values=values, tags=tuple(tags))
        
        # 태그 색상 설정
        self.tree.tag_configure('different', background='#FFEEAA')
        self.tree.tag_configure('low_confidence', background='#FFE6E6')
        
        # 통계 업데이트
        self.update_statistics(filtered_data)
    
    def update_statistics(self, data):
        """통계 정보 업데이트"""
        if data.empty:
            self.stats_label.config(text="데이터가 없습니다.")
            return
        
        total_items = len(data)
        different_items = len(data[data.get('Difference', '') == 'Different'])
        same_items = total_items - different_items
        
        avg_confidence = data.get('Confidence', pd.Series()).mean()
        
        stats_text = f"전체: {total_items}개 | 동일: {same_items}개 | 차이: {different_items}개"
        if pd.notna(avg_confidence):
            stats_text += f" | 평균 신뢰도: {avg_confidence:.1f}%"
        
        self.stats_label.config(text=stats_text)
    
    def process_data(self, file_data):
        """향상된 데이터 처리"""
        if self.comparison_mode.get() == "file_to_db":
            return self._process_file_to_db(file_data)
        else:
            return self._process_file_to_file(file_data)
    
    def _process_file_to_file(self, file_data):
        """파일 대 파일 비교"""
        # SimpleComparison과 유사하지만 더 상세한 분석
        if not file_data or len(file_data) < 2:
            return pd.DataFrame()
        
        # 기본 비교 로직 + 통계 분석
        simple_comparison = SimpleComparison(self.manager)
        result = simple_comparison.process_data(file_data)
        
        # 신뢰도 추가 (예시)
        result['Confidence'] = np.random.uniform(70, 95, len(result))  # 실제로는 더 정교한 로직 필요
        result['DB_Value'] = result['File2']  # 파일 대 파일의 경우
        result['File_Value'] = result['File1']
        
        return result
    
    def _process_file_to_db(self, file_data):
        """파일 대 DB 비교"""
        if not file_data:
            return pd.DataFrame()
        
        equipment_type = self.equipment_var.get()
        if not equipment_type:
            return pd.DataFrame()
        
        try:
            # DB에서 기본값 가져오기
            db_values = self.manager.db_schema.get_default_values_by_type_name(equipment_type)
            
            file_df = file_data[0]
            comparison_result = []
            
            for _, file_row in file_df.iterrows():
                key = (file_row.get('Module', ''), file_row.get('Part', ''), file_row.get('Item_Name', ''))
                
                # DB에서 해당 키 찾기
                db_value = self._find_db_value(db_values, key)
                file_value = file_row.get('Value', '')
                
                difference = 'Different' if str(file_value) != str(db_value.get('default_value', '')) else 'Same'
                
                comparison_result.append({
                    'Module': key[0],
                    'Part': key[1], 
                    'Item_Name': key[2],
                    'File_Value': file_value,
                    'DB_Value': db_value.get('default_value', ''),
                    'Difference': difference,
                    'Confidence': db_value.get('confidence_score', 0),
                    'Is_Performance': db_value.get('is_performance', False)
                })
            
            return pd.DataFrame(comparison_result)
            
        except Exception as e:
            self.manager.update_log(f"DB 비교 실패: {str(e)}")
            return pd.DataFrame()
    
    def _find_db_value(self, db_values, key):
        """DB에서 키에 해당하는 값 찾기"""
        module, part, item_name = key
        
        for db_row in db_values:
            if (db_row.get('module', '') == module and 
                db_row.get('part', '') == part and 
                db_row.get('item_name', '') == item_name):
                return db_row
        
        return {}
    
    def on_search_changed(self, event=None):
        """검색어 변경 시 호출"""
        if hasattr(self, 'comparison_data') and self.comparison_data is not None:
            self.update_view(self.comparison_data)


class AdvancedComparison(BaseComparison):
    """고급 비교 기능 (통계 분석 포함)"""
    
    def create_ui(self, parent_frame):
        """고급 비교 UI 생성"""
        self.frame = ttk.LabelFrame(parent_frame, text="고급 통계 비교", padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 분석 옵션 프레임
        options_frame = ttk.LabelFrame(self.frame, text="분석 옵션", padding=5)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 분석 타입 선택
        ttk.Label(options_frame, text="분석 타입:").grid(row=0, column=0, sticky="w", padx=5)
        self.analysis_type = tk.StringVar(value="statistical")
        ttk.Radiobutton(options_frame, text="통계 분석", variable=self.analysis_type, 
                       value="statistical").grid(row=0, column=1, padx=5)
        ttk.Radiobutton(options_frame, text="트렌드 분석", variable=self.analysis_type, 
                       value="trend").grid(row=0, column=2, padx=5)
        
        # 임계값 설정
        ttk.Label(options_frame, text="차이 임계값:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.threshold_var = tk.StringVar(value="5.0")
        ttk.Entry(options_frame, textvariable=self.threshold_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(options_frame, text="%").grid(row=1, column=2, sticky="w", pady=5)
        
        # 분석 실행 버튼
        ttk.Button(options_frame, text="분석 실행", 
                  command=self.run_analysis).grid(row=1, column=3, padx=20, pady=5)
        
        # 결과 노트북 (탭)
        self.result_notebook = ttk.Notebook(self.frame)
        self.result_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 상세 비교 탭
        detail_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(detail_frame, text="상세 비교")
        
        columns = ['Module', 'Part', 'Item_Name', 'Value1', 'Value2', 'Diff_Percent', 'Severity']
        headings = {
            'Module': '모듈',
            'Part': '부품',
            'Item_Name': '항목명',
            'Value1': '값1',
            'Value2': '값2', 
            'Diff_Percent': '차이율(%)',
            'Severity': '심각도'
        }
        
        tree_frame, self.detail_tree = self.create_treeview_with_scrollbar(
            detail_frame, columns, headings, height=15
        )
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 통계 요약 탭
        stats_frame = ttk.Frame(self.result_notebook)
        self.result_notebook.add(stats_frame, text="통계 요약")
        
        self.stats_text = tk.Text(stats_frame, wrap=tk.WORD, state=tk.DISABLED)
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 컨텍스트 메뉴 설정
        self.setup_context_menu(self.detail_tree)
    
    def create_ui(self, parent_frame):
        """UI 생성"""
        pass  # 위에서 이미 구현됨
    
    def update_view(self, data=None):
        """고급 비교 뷰 업데이트"""
        self.comparison_data = data
        if data is not None and not data.empty:
            self.run_analysis()
    
    def process_data(self, file_data):
        """고급 데이터 처리 및 통계 분석"""
        if not file_data or len(file_data) < 2:
            return pd.DataFrame()
        
        file1_data = file_data[0]
        file2_data = file_data[1]
        
        # 수치 데이터만 비교
        comparison_result = []
        
        for _, row1 in file1_data.iterrows():
            key = (row1.get('Module', ''), row1.get('Part', ''), row1.get('Item_Name', ''))
            
            # file2에서 같은 키 찾기
            file2_row = self._find_matching_row(file2_data, key)
            
            if file2_row is not None:
                value1 = self._parse_numeric_value(row1.get('Value', ''))
                value2 = self._parse_numeric_value(file2_row.get('Value', ''))
                
                if value1 is not None and value2 is not None:
                    # 차이율 계산
                    if value1 != 0:
                        diff_percent = abs((value2 - value1) / value1) * 100
                    else:
                        diff_percent = 0 if value2 == 0 else float('inf')
                    
                    # 심각도 계산
                    severity = self._calculate_severity(diff_percent)
                    
                    comparison_result.append({
                        'Module': key[0],
                        'Part': key[1],
                        'Item_Name': key[2],
                        'Value1': value1,
                        'Value2': value2,
                        'Diff_Percent': diff_percent,
                        'Severity': severity
                    })
        
        return pd.DataFrame(comparison_result)
    
    def _find_matching_row(self, data, key):
        """키와 일치하는 행 찾기"""
        module, part, item_name = key
        
        for _, row in data.iterrows():
            if (row.get('Module', '') == module and 
                row.get('Part', '') == part and 
                row.get('Item_Name', '') == item_name):
                return row
        return None
    
    def _parse_numeric_value(self, value):
        """문자열을 숫자로 변환"""
        try:
            # 문자열에서 숫자 추출
            import re
            numeric_str = re.sub(r'[^\d.-]', '', str(value))
            return float(numeric_str) if numeric_str else None
        except:
            return None
    
    def _calculate_severity(self, diff_percent):
        """차이율에 따른 심각도 계산"""
        threshold = float(self.threshold_var.get())
        
        if diff_percent == float('inf'):
            return "Critical"
        elif diff_percent > threshold * 2:
            return "High"
        elif diff_percent > threshold:
            return "Medium"
        else:
            return "Low"
    
    def run_analysis(self):
        """분석 실행"""
        if not hasattr(self, 'comparison_data') or self.comparison_data is None:
            return
        
        data = self.comparison_data
        
        # 상세 비교 테이블 업데이트
        self._update_detail_view(data)
        
        # 통계 요약 업데이트
        self._update_statistics_summary(data)
    
    def _update_detail_view(self, data):
        """상세 비교 뷰 업데이트"""
        # 기존 데이터 삭제
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
        
        if data.empty:
            return
        
        # 심각도 순으로 정렬
        severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        data_sorted = data.copy()
        data_sorted['severity_rank'] = data_sorted['Severity'].map(severity_order)
        data_sorted = data_sorted.sort_values('severity_rank')
        
        # 데이터 표시
        for _, row in data_sorted.iterrows():
            values = [
                row.get('Module', ''),
                row.get('Part', ''),
                row.get('Item_Name', ''),
                f"{row.get('Value1', 0):.3f}",
                f"{row.get('Value2', 0):.3f}",
                f"{row.get('Diff_Percent', 0):.2f}",
                row.get('Severity', '')
            ]
            
            # 심각도에 따른 태그 설정
            severity = row.get('Severity', '')
            tags = (severity.lower(),)
            
            self.detail_tree.insert('', tk.END, values=values, tags=tags)
        
        # 태그 색상 설정
        self.detail_tree.tag_configure('critical', background='#FF6B6B')
        self.detail_tree.tag_configure('high', background='#FFE66D')
        self.detail_tree.tag_configure('medium', background='#4ECDC4')
        self.detail_tree.tag_configure('low', background='#95E1D3')
    
    def _update_statistics_summary(self, data):
        """통계 요약 업데이트"""
        self.stats_text.configure(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        if data.empty:
            self.stats_text.insert(tk.END, "분석할 데이터가 없습니다.")
            self.stats_text.configure(state=tk.DISABLED)
            return
        
        # 기본 통계
        total_items = len(data)
        threshold = float(self.threshold_var.get())
        
        critical_items = len(data[data['Severity'] == 'Critical'])
        high_items = len(data[data['Severity'] == 'High'])
        medium_items = len(data[data['Severity'] == 'Medium'])
        low_items = len(data[data['Severity'] == 'Low'])
        
        # 차이율 통계
        diff_stats = data['Diff_Percent'].describe()
        
        summary = f"""
===== 고급 비교 분석 결과 =====

[기본 통계]
• 총 비교 항목: {total_items}개
• 임계값: {threshold}%

[심각도별 분포]
• Critical: {critical_items}개 ({critical_items/total_items*100:.1f}%)
• High: {high_items}개 ({high_items/total_items*100:.1f}%)
• Medium: {medium_items}개 ({medium_items/total_items*100:.1f}%)
• Low: {low_items}개 ({low_items/total_items*100:.1f}%)

[차이율 통계]
• 평균: {diff_stats['mean']:.2f}%
• 중앙값: {diff_stats['50%']:.2f}%
• 최대: {diff_stats['max']:.2f}%
• 최소: {diff_stats['min']:.2f}%
• 표준편차: {diff_stats['std']:.2f}%

[권장사항]
"""
        
        if critical_items > 0:
            summary += f"• Critical 항목 {critical_items}개에 대한 즉시 검토가 필요합니다.\\n"
        if high_items > total_items * 0.1:
            summary += f"• High 심각도 항목이 {high_items/total_items*100:.1f}%로 높습니다. 전반적인 검토를 권장합니다.\\n"
        if diff_stats['mean'] > threshold:
            summary += f"• 평균 차이율이 임계값을 초과합니다. 임계값 조정을 고려하세요.\\n"
        
        if critical_items == 0 and high_items < total_items * 0.05:
            summary += "• 전반적으로 양호한 일치율을 보입니다.\\n"
        
        self.stats_text.insert(tk.END, summary)
        self.stats_text.configure(state=tk.DISABLED)