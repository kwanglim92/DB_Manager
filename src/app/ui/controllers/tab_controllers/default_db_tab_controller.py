"""
Default DB 관리 탭 컨트롤러
Check list 기능을 포함한 완전한 Default DB 관리 시스템
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional

from ..base_controller import TabController


class DefaultDBTabController(TabController):
    """Default DB 관리 탭 컨트롤러 - Check list 기능 포함"""
    
    def __init__(self, tab_frame: tk.Frame, viewmodel, tab_name: str = "Default DB 관리"):
        """DefaultDBTabController 초기화"""
        super().__init__(tab_frame, viewmodel, tab_name)
        
        # 상태 변수
        self.equipment_type_var = tk.StringVar()
        self.show_performance_only_var = tk.BooleanVar()
        self.confidence_filter_var = tk.StringVar(value="전체")
        
        # UI 컴포넌트 참조
        self.equipment_type_combo = None
        self.default_db_tree = None
        self.default_db_context_menu = None
        self.default_db_status_label = None
        self.performance_stats_label = None
        
        # DB 스키마 참조
        self.db_schema = getattr(viewmodel, 'db_schema', None)
        self.maint_mode = getattr(viewmodel, 'maint_mode', False)
        
        # UI 생성
        self._create_tab_ui()
        
        # 초기 데이터 로드
        self.tab_frame.after(200, self._refresh_equipment_types)
    
    def _create_tab_ui(self):
        """Default DB 관리 탭 UI 생성"""
        try:
            # 상단 제어 패널
            control_frame = ttk.Frame(self.tab_frame)
            control_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # 장비 유형 관리 섹션
            self._create_equipment_section(control_frame)
            
            # 파라미터 관리 섹션
            self._create_parameter_section(control_frame)
            
            # 파라미터 목록 트리뷰
            self._create_treeview_section()
            
            # 상태 표시줄
            self._create_status_section()
            
        except Exception as e:
            print(f"Default DB 탭 UI 생성 오류: {e}")
    
    def _create_equipment_section(self, parent):
        """장비 유형 관리 섹션 생성"""
        equipment_frame = ttk.LabelFrame(parent, text="🔧 장비 유형 관리", padding=10)
        equipment_frame.pack(fill=tk.X, pady=5)
        
        # 장비 유형 선택
        ttk.Label(equipment_frame, text="장비 유형:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.equipment_type_combo = ttk.Combobox(
            equipment_frame, 
            textvariable=self.equipment_type_var, 
            state="readonly", 
            width=30
        )
        self.equipment_type_combo.grid(row=0, column=1, padx=5, pady=5)
        self.equipment_type_combo.bind("<<ComboboxSelected>>", self._on_equipment_type_selected)
        
        # 장비 유형 관리 버튼들
        ttk.Button(
            equipment_frame, 
            text="새 장비 유형 추가", 
            command=self._add_equipment_type_dialog
        ).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(
            equipment_frame, 
            text="삭제", 
            command=self._delete_equipment_type
        ).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(
            equipment_frame, 
            text="새로고침", 
            command=self._refresh_equipment_types
        ).grid(row=0, column=4, padx=5, pady=5)
    
    def _create_parameter_section(self, parent):
        """파라미터 관리 섹션 생성"""
        param_frame = ttk.LabelFrame(parent, text="📊 파라미터 관리", padding=10)
        param_frame.pack(fill=tk.X, pady=5)
        
        # 첫 번째 줄: 기본 관리 버튼들
        basic_mgmt_frame = ttk.Frame(param_frame)
        basic_mgmt_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(basic_mgmt_frame, text="파라미터 추가", command=self._add_parameter_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(basic_mgmt_frame, text="선택 항목 삭제", command=self._delete_selected_parameters).pack(side=tk.LEFT, padx=5)
        
        # 🎯 Check list 관리 버튼들
        ttk.Button(basic_mgmt_frame, text="🎯 Check list 토글", command=self._toggle_performance_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(basic_mgmt_frame, text="📊 Check list 통계", command=self._show_performance_statistics).pack(side=tk.LEFT, padx=5)
        ttk.Button(basic_mgmt_frame, text="✅ Check list 설정", command=lambda: self._set_performance_status(True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(basic_mgmt_frame, text="❌ Check list 해제", command=lambda: self._set_performance_status(False)).pack(side=tk.LEFT, padx=5)
        
        # 두 번째 줄: 필터링 및 보기 옵션
        filter_frame = ttk.Frame(param_frame)
        filter_frame.pack(fill=tk.X, pady=2)
        
        # Check list 필터 체크박스
        performance_cb = ttk.Checkbutton(
            filter_frame, 
            text="🎯 Check list 항목만 표시", 
            variable=self.show_performance_only_var,
            command=self._apply_performance_filter
        )
        performance_cb.pack(side=tk.LEFT, padx=5)
        
        # 신뢰도 필터
        ttk.Label(filter_frame, text="신뢰도 필터:").pack(side=tk.LEFT, padx=(20, 5))
        confidence_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.confidence_filter_var,
            values=["전체", "90% 이상", "80% 이상", "70% 이상", "50% 이상"],
            state="readonly",
            width=12
        )
        confidence_combo.pack(side=tk.LEFT, padx=5)
        confidence_combo.bind("<<ComboboxSelected>>", self._apply_confidence_filter)
        
        # 필터 적용/초기화 버튼
        ttk.Button(filter_frame, text="🔍 필터 적용", command=self._apply_all_filters).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text="🔄 필터 초기화", command=self._reset_all_filters).pack(side=tk.LEFT, padx=5)
    
    def _create_treeview_section(self):
        """파라미터 목록 트리뷰 섹션 생성"""
        tree_frame = ttk.Frame(self.tab_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 트리뷰 컬럼 정의 (순차 번호 컬럼으로 변경)
        columns = (
            "no", "parameter_name", "module", "part", "item_type", "default_value", 
            "min_spec", "max_spec", "occurrence_count", "total_files", "confidence_score", 
            "is_performance", "source_files", "description"
        )
        
        self.default_db_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # 컬럼 헤더 설정
        headers = {
            "no": "No.",  # 순차 번호 컬럼
            "parameter_name": "파라미터명",
            "module": "Module",
            "part": "Part", 
            "item_type": "데이터 타입",
            "default_value": "설정값",
            "min_spec": "최소값",
            "max_spec": "최대값",
            "occurrence_count": "발생횟수",
            "total_files": "전체파일",
            "confidence_score": "신뢰도(%)",
            "is_performance": "🎯 Check list",
            "source_files": "소스파일",
            "description": "설명"
        }
        
        column_widths = {
            "no": 50,  # 순차 번호 컬럼 너비
            "parameter_name": 200,
            "module": 80,
            "part": 100,
            "item_type": 80,
            "default_value": 100,
            "min_spec": 80,
            "max_spec": 80,
            "occurrence_count": 80,
            "total_files": 80,
            "confidence_score": 80,
            "is_performance": 90,
            "source_files": 150,
            "description": 150
        }
        
        for col in columns:
            self.default_db_tree.heading(col, text=headers[col])
            self.default_db_tree.column(col, width=column_widths[col], minwidth=50)
        
        # 스크롤바 추가
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.default_db_tree.yview)
        self.default_db_tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.default_db_tree.xview)
        self.default_db_tree.configure(xscrollcommand=h_scrollbar.set)
        
        # 배치
        self.default_db_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # 이벤트 바인딩
        self.default_db_tree.bind("<Double-1>", self._edit_parameter_dialog)
        self.default_db_tree.bind("<Button-3>", self._show_context_menu)
        
        # 컨텍스트 메뉴 생성
        self._create_context_menu()
    
    def _create_status_section(self):
        """상태 표시줄 섹션 생성"""
        status_frame = ttk.Frame(self.tab_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.default_db_status_label = ttk.Label(status_frame, text="장비 유형을 선택하세요.")
        self.default_db_status_label.pack(side=tk.LEFT)
        
        self.performance_stats_label = ttk.Label(status_frame, text="", foreground="blue")
        self.performance_stats_label.pack(side=tk.RIGHT)
    
    def _create_context_menu(self):
        """컨텍스트 메뉴 생성"""
        self.default_db_context_menu = tk.Menu(self.tab_frame, tearoff=0)
        
        # Check list 관련 메뉴
        self.default_db_context_menu.add_command(label="🎯 Check list로 설정", command=lambda: self._set_performance_status(True))
        self.default_db_context_menu.add_command(label="❌ Check list 해제", command=lambda: self._set_performance_status(False))
        self.default_db_context_menu.add_command(label="🔄 Check list 토글", command=self._toggle_performance_status)
        self.default_db_context_menu.add_separator()
        
        # 기본 편집 메뉴
        self.default_db_context_menu.add_command(label="✏️ 편집", command=lambda: self._edit_parameter_dialog(None))
        self.default_db_context_menu.add_command(label="🗑️ 삭제", command=self._delete_selected_parameters)
        self.default_db_context_menu.add_separator()
        
        # 정보 메뉴
        self.default_db_context_menu.add_command(label="📊 상세 정보", command=self._show_parameter_details)
    
    def _refresh_equipment_types(self):
        """장비 유형 목록 새로고침"""
        try:
            if not self.db_schema:
                return
            
            equipment_types = self.db_schema.get_equipment_types()
            
            # 콤보박스 값 업데이트
            type_list = [f"{type_name} (ID: {type_id})" for type_id, type_name, _ in equipment_types]
            self.equipment_type_combo['values'] = type_list
            
            print(f"✅ 장비 유형 목록 새로고침: {len(equipment_types)}개")
            
        except Exception as e:
            print(f"❌ 장비 유형 새로고침 오류: {e}")
    
    def _on_equipment_type_selected(self, event=None):
        """장비 유형 선택 시 호출"""
        try:
            selected = self.equipment_type_var.get()
            if not selected or "ID: " not in selected:
                return
            
            # 장비 유형 ID 추출
            equipment_type_id = int(selected.split("ID: ")[1].split(")")[0])
            
            # 파라미터 목록 조회
            performance_only = self.show_performance_only_var.get()
            default_values = self.db_schema.get_default_values(equipment_type_id, performance_only)
            
            # 화면 업데이트
            self._update_default_db_display(default_values)
            
        except Exception as e:
            print(f"❌ 장비 유형 선택 오류: {e}")
    
    def _update_default_db_display(self, default_values):
        """파라미터 목록 화면 업데이트"""
        try:
            # 기존 항목들 제거
            for item in self.default_db_tree.get_children():
                self.default_db_tree.delete(item)
            
            if not default_values:
                return
            
            # 새 항목들 추가
            added_count = 0
            for record in default_values:
                # 필터링 적용
                if self._should_filter_record(record):
                    continue
                
                # 값 파싱
                values = self._parse_record_values(record)
                
                # 트리뷰에 추가
                self.default_db_tree.insert("", "end", values=values)
                added_count += 1
            
            # 상태 업데이트
            self._update_status_display(default_values, added_count)
            
        except Exception as e:
            print(f"❌ 파라미터 목록 업데이트 오류: {e}")
    
    def _should_filter_record(self, record):
        """레코드 필터링 여부 결정"""
        try:
            # Check list 필터
            if self.show_performance_only_var.get():
                is_performance = record[14] if len(record) > 14 else False
                if not is_performance:
                    return True
            
            # 신뢰도 필터
            filter_value = self.confidence_filter_var.get()
            if filter_value != "전체":
                required_confidence = float(filter_value.replace("% 이상", "")) / 100.0
                confidence_score = record[8] if len(record) > 8 else 1.0
                if confidence_score < required_confidence:
                    return True
            
            return False
        except:
            return False
    
    def _parse_record_values(self, record):
        """레코드 값 파싱"""
        try:
            record_id = record[0]
            parameter_name = record[1]
            default_value = record[2] if record[2] is not None else ""
            min_spec = record[3] if record[3] else ""
            max_spec = record[4] if record[4] else ""
            
            # 추가 정보 처리
            occurrence_count = record[6] if len(record) > 6 else 1
            total_files = record[7] if len(record) > 7 else 1
            confidence_score = record[8] if len(record) > 8 else 1.0
            source_files = record[9] if len(record) > 9 else ""
            description = record[10] if len(record) > 10 and record[10] else f"This is a {parameter_name} Description"
            module_name = record[11] if len(record) > 11 and record[11] else "DSP"
            part_name = record[12] if len(record) > 12 and record[12] else "Unknown"
            item_type = record[13] if len(record) > 13 and record[13] else "double"
            is_performance = record[14] if len(record) > 14 else False
            
            # 신뢰도를 퍼센트로 변환
            confidence_percent = f"{confidence_score * 100:.1f}"
            
            # Check list 상태 표시
            performance_display = "✅ Yes" if is_performance else "❌ No"
            
            return (
                record_id, parameter_name, module_name, part_name, item_type, default_value, 
                min_spec, max_spec, occurrence_count, total_files, confidence_percent, 
                performance_display, source_files, description
            )
            
        except Exception as e:
            print(f"레코드 파싱 오류: {e}")
            return ("", "", "", "", "", "", "", "", "", "", "", "", "", "")
    
    def _update_status_display(self, default_values, added_count):
        """상태 표시줄 업데이트"""
        try:
            count = len(default_values)
            selected_type = self.equipment_type_var.get().split(" (ID:")[0] if self.equipment_type_var.get() else "선택없음"
            
            # Check list 통계 계산
            performance_count = sum(1 for record in default_values if len(record) > 14 and record[14])
            performance_ratio = (performance_count / count * 100) if count > 0 else 0
            
            status_text = f"장비유형: {selected_type} | 파라미터: {count}개 | 표시: {added_count}개"
            performance_text = f"🎯 Check list: {performance_count}개 ({performance_ratio:.1f}%)"
            
            self.default_db_status_label.config(text=status_text)
            self.performance_stats_label.config(text=performance_text)
            
        except Exception as e:
            print(f"상태 표시 업데이트 오류: {e}")
    
    def _toggle_performance_status(self):
        """Check list 상태 토글"""
        try:
            if not self._check_maintenance_mode():
                return
            
            selected_items = self.default_db_tree.selection()
            if not selected_items:
                messagebox.showwarning("선택 필요", "Check list 상태를 토글할 파라미터를 선택해주세요.")
                return
            
            # 첫 번째 선택된 항목의 현재 Check list 상태 확인
            first_item = selected_items[0]
            values = self.default_db_tree.item(first_item, 'values')
            if not values:
                return
            
            current_performance = values[11]  # is_performance 컬럼
            is_currently_performance = "Yes" in str(current_performance)
            new_performance_status = not is_currently_performance
            
            # 모든 선택된 항목에 새로운 상태 적용
            self._apply_performance_status_to_selection(selected_items, new_performance_status)
            
        except Exception as e:
            print(f"Check list 토글 오류: {e}")
            messagebox.showerror("오류", f"Check list 상태 토글 오류: {str(e)}")
    
    def _set_performance_status(self, is_performance):
        """Check list 상태 설정"""
        try:
            if not self._check_maintenance_mode():
                return
            
            selected_items = self.default_db_tree.selection()
            if not selected_items:
                messagebox.showwarning("선택 필요", "Check list 상태를 변경할 파라미터를 선택해주세요.")
                return
            
            self._apply_performance_status_to_selection(selected_items, is_performance)
            
        except Exception as e:
            print(f"Check list 상태 설정 오류: {e}")
            messagebox.showerror("오류", f"Check list 상태 설정 오류: {str(e)}")
    
    def _apply_performance_status_to_selection(self, selected_items, is_performance):
        """선택된 항목들에 Check list 상태 적용"""
        try:
            success_count = 0
            for item in selected_items:
                values = self.default_db_tree.item(item, 'values')
                if values:
                    record_id = values[0]  # ID 컬럼
                    parameter_name = values[1]  # 파라미터명
                    
                    # DB에서 Check list 상태 업데이트
                    if self.db_schema.set_performance_status(record_id, is_performance):
                        success_count += 1
                        print(f"✅ {parameter_name}: Check list {'설정' if is_performance else '해제'}")
                    else:
                        print(f"❌ {parameter_name}: Check list 상태 변경 실패")
            
            if success_count > 0:
                status_text = "Check list로 설정" if is_performance else "Check list 해제"
                messagebox.showinfo("완료", f"{success_count}개 파라미터의 {status_text}가 완료되었습니다.")
                
                # 화면 새로고침
                self._on_equipment_type_selected()
            else:
                messagebox.showerror("오류", "Check list 상태 변경에 실패했습니다.")
                
        except Exception as e:
            print(f"Check list 상태 적용 오류: {e}")
    
    def _show_performance_statistics(self):
        """Check list 통계 다이얼로그 표시"""
        try:
            if not self.equipment_type_var.get():
                messagebox.showwarning("선택 필요", "먼저 장비 유형을 선택해주세요.")
                return
            
            # 현재 선택된 장비 유형 ID 추출
            selected_text = self.equipment_type_var.get()
            if "ID: " not in selected_text:
                return
            
            equipment_type_id = int(selected_text.split("ID: ")[1].split(")")[0])
            
            # Check list 통계 조회
            stats = self.db_schema.get_equipment_performance_count(equipment_type_id)
            
            # 통계 다이얼로그 생성
            self._create_statistics_dialog(stats, selected_text)
            
        except Exception as e:
            print(f"Check list 통계 표시 오류: {e}")
            messagebox.showerror("오류", f"Check list 통계 표시 오류: {str(e)}")
    
    def _create_statistics_dialog(self, stats, selected_text):
        """통계 다이얼로그 생성"""
        stats_window = tk.Toplevel(self.tab_frame)
        stats_window.title("📊 Check list 통계")
        stats_window.geometry("400x300")
        stats_window.transient(self.tab_frame.winfo_toplevel())
        stats_window.grab_set()
        
        # 통계 정보 표시
        stats_frame = ttk.Frame(stats_window, padding=20)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(
            stats_frame, 
            text=f"🎯 Check list 통계\n{selected_text.split(' (ID:')[0]}", 
            font=('Arial', 12, 'bold'),
            justify='center'
        )
        title_label.pack(pady=(0, 20))
        
        # 통계 카드들
        total_frame = ttk.LabelFrame(stats_frame, text="📊 전체 파라미터", padding=10)
        total_frame.pack(fill=tk.X, pady=5)
        ttk.Label(total_frame, text=f"{stats['total']}개", font=('Arial', 16, 'bold')).pack()
        
        perf_frame = ttk.LabelFrame(stats_frame, text="🎯 Check list 파라미터", padding=10)
        perf_frame.pack(fill=tk.X, pady=5)
        ttk.Label(perf_frame, text=f"{stats['performance']}개", font=('Arial', 16, 'bold'), foreground='blue').pack()
        
        # 비율 계산
        if stats['total'] > 0:
            percentage = (stats['performance'] / stats['total']) * 100
            ratio_text = f"{percentage:.1f}%"
        else:
            ratio_text = "0.0%"
        
        ratio_frame = ttk.LabelFrame(stats_frame, text="📈 Check list 비율", padding=10)
        ratio_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ratio_frame, text=ratio_text, font=('Arial', 16, 'bold'), foreground='green').pack()
        
        # 권장사항
        recommendation = self._get_recommendation(stats['performance'], percentage if stats['total'] > 0 else 0)
        rec_frame = ttk.LabelFrame(stats_frame, text="💡 권장사항", padding=10)
        rec_frame.pack(fill=tk.X, pady=5)
        rec_label = ttk.Label(rec_frame, text=recommendation[0], foreground=recommendation[1], justify='center')
        rec_label.pack()
        
        # 닫기 버튼
        ttk.Button(stats_frame, text="닫기", command=stats_window.destroy).pack(pady=20)
    
    def _get_recommendation(self, performance_count, percentage):
        """권장사항 텍스트와 색상 반환"""
        if performance_count == 0:
            return ("⚠️ Check list 파라미터가 설정되지 않았습니다.\nQC 검수 품질 향상을 위해 중요한 파라미터를 Check list로 설정해주세요.", 'red')
        elif percentage < 20:
            return ("💡 Check list 파라미터 비율이 낮습니다.\n추가 설정을 권장합니다.", 'orange')
        else:
            return ("✅ Check list 파라미터가 적절히 설정되었습니다.", 'green')
    
    def _apply_performance_filter(self):
        """Check list 필터 적용"""
        self._on_equipment_type_selected()
    
    def _apply_confidence_filter(self, event=None):
        """신뢰도 필터 적용"""
        self._on_equipment_type_selected()
    
    def _apply_all_filters(self):
        """모든 필터 적용"""
        self._on_equipment_type_selected()
    
    def _reset_all_filters(self):
        """모든 필터 초기화"""
        self.show_performance_only_var.set(False)
        self.confidence_filter_var.set("전체")
        self._on_equipment_type_selected()
        print("✅ 필터가 초기화되었습니다.")
    
    def _show_context_menu(self, event):
        """컨텍스트 메뉴 표시"""
        try:
            # 클릭한 위치의 아이템 선택
            item = self.default_db_tree.identify_row(event.y)
            if item:
                self.default_db_tree.selection_set(item)
                self.default_db_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"컨텍스트 메뉴 표시 오류: {e}")
    
    def _show_parameter_details(self):
        """파라미터 상세 정보 표시"""
        try:
            selected_items = self.default_db_tree.selection()
            if not selected_items:
                messagebox.showwarning("선택 필요", "상세 정보를 볼 파라미터를 선택해주세요.")
                return
            
            item = selected_items[0]
            values = self.default_db_tree.item(item, 'values')
            if not values:
                return
            
            # 상세 정보 다이얼로그 생성
            self._create_detail_dialog(values)
            
        except Exception as e:
            print(f"상세 정보 표시 오류: {e}")
            messagebox.showerror("오류", f"상세 정보 표시 오류: {str(e)}")
    
    def _create_detail_dialog(self, values):
        """상세 정보 다이얼로그 생성"""
        detail_window = tk.Toplevel(self.tab_frame)
        detail_window.title("📊 파라미터 상세 정보")
        detail_window.geometry("500x400")
        detail_window.transient(self.tab_frame.winfo_toplevel())
        detail_window.grab_set()
        
        # 정보 표시
        info_text = tk.Text(detail_window, wrap=tk.WORD, padx=10, pady=10)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 파라미터 정보 구성
        param_info = f"""📋 파라미터 상세 정보

🔧 기본 정보:
• ID: {values[0]}
• 파라미터명: {values[1]}
• Module: {values[2]}
• Part: {values[3]}
• 데이터 타입: {values[4]}

⚙️ 설정값:
• 기본값: {values[5]}
• 최소값: {values[6]}
• 최대값: {values[7]}

📊 통계 정보:
• 발생 횟수: {values[8]}
• 전체 파일 수: {values[9]}
• 신뢰도: {values[10]}%

🎯 Check list 설정:
• Check list 항목: {values[11]}

📁 소스 정보:
• 소스 파일: {values[12]}

📝 설명:
{values[13]}
"""
        
        info_text.insert(tk.END, param_info)
        info_text.config(state=tk.DISABLED)
        
        # 닫기 버튼
        ttk.Button(detail_window, text="닫기", command=detail_window.destroy).pack(pady=10)
    
    def _check_maintenance_mode(self):
        """유지보수 모드 확인"""
        if not self.maint_mode:
            messagebox.showwarning("권한 없음", "유지보수 모드에서만 Check list 상태를 변경할 수 있습니다.")
            return False
        return True
    
    # 기본 인터페이스 메서드들
    def _add_equipment_type_dialog(self):
        """장비 유형 추가 다이얼로그 (향후 구현)"""
        messagebox.showinfo("구현 예정", "이 기능은 향후 구현될 예정입니다.")
    
    def _delete_equipment_type(self):
        """장비 유형 삭제"""
        if not self._check_maintenance_mode():
            return
            
        selected = self.equipment_type_var.get()
        if not selected:
            messagebox.showwarning("선택 필요", "삭제할 장비 유형을 선택해주세요.")
            return
        
        try:
            # 선택된 장비 유형의 ID 추출
            equipment_type_id = None
            for type_id, type_name in self.equipment_types.items():
                if f"{type_name} (ID: {type_id})" == selected:
                    equipment_type_id = type_id
                    break
            
            if not equipment_type_id:
                messagebox.showerror("오류", "장비 유형 ID를 찾을 수 없습니다.")
                return
            
            # 관련 파라미터 개수 확인
            param_count = self.db_schema.get_total_parameter_count(equipment_type_id)
            
            # 삭제 확인
            if param_count > 0:
                confirm_msg = (
                    f"장비 유형 '{selected.split(' (ID:')[0]}'을(를) 삭제하시겠습니까?\n\n"
                    f"⚠️  이 장비 유형에는 {param_count}개의 파라미터가 있습니다.\n"
                    f"장비 유형을 삭제하면 관련된 모든 파라미터도 함께 삭제됩니다.\n\n"
                    f"이 작업은 되돌릴 수 없습니다."
                )
            else:
                confirm_msg = (
                    f"장비 유형 '{selected.split(' (ID:')[0]}'을(를) 삭제하시겠습니까?\n\n"
                    f"이 작업은 되돌릴 수 없습니다."
                )
            
            if not messagebox.askyesno("삭제 확인", confirm_msg):
                return
            
            # 삭제 실행
            if self.db_schema.delete_equipment_type(equipment_type_id):
                messagebox.showinfo("완료", f"장비 유형이 삭제되었습니다.\n관련 파라미터 {param_count}개도 함께 삭제되었습니다.")
                self.viewmodel.add_log_message(f"[Default DB] 장비 유형 '{selected.split(' (ID:')[0]}' 및 관련 파라미터 {param_count}개 삭제 완료")
                
                # UI 새로고침
                self._refresh_equipment_types()
                self._clear_parameter_tree()
                
            else:
                messagebox.showerror("오류", "장비 유형 삭제에 실패했습니다.")
                
        except Exception as e:
            error_msg = f"장비 유형 삭제 중 오류 발생: {str(e)}"
            messagebox.showerror("오류", error_msg)
            self.viewmodel.add_log_message(f"❌ {error_msg}")
    
    def _add_parameter_dialog(self):
        """파라미터 추가 다이얼로그 (향후 구현)"""
        messagebox.showinfo("구현 예정", "이 기능은 향후 구현될 예정입니다.")
    
    def _delete_selected_parameters(self):
        """선택된 파라미터 삭제 (향후 구현)"""
        messagebox.showinfo("구현 예정", "이 기능은 향후 구현될 예정입니다.")
    
    def _edit_parameter_dialog(self, event):
        """파라미터 편집 다이얼로그 (향후 구현)"""
        messagebox.showinfo("구현 예정", "이 기능은 향후 구현될 예정입니다.")
    
    def on_tab_activated(self):
        """탭 활성화 시 호출"""
        super().on_tab_activated()
        # 필요시 추가 초기화 작업
    
    def get_tab_title(self) -> str:
        """탭 제목 반환"""
        return "📝 Default DB 관리"