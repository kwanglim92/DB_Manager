"""
향상된 Default DB 전송 시스템 (간소화)
중복 항목 분석 및 스마트 처리 기능
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

@dataclass
class DuplicateItem:
    """중복 항목 정보 (간소화)"""
    parameter_name: str
    existing_value: str
    new_value: str
    source_files: List[str]
    recommendation: str

class DuplicateAnalyzer:
    """중복 항목 분석기"""
    
    def __init__(self, db_schema):
        self.db_schema = db_schema
    
    def analyze_duplicates_smart(self, selected_items: List, equipment_type_id: int, 
                                manager_instance) -> Dict[str, Any]:
        """
        스마트 중복 분석
        
        Args:
            selected_items: 선택된 트리뷰 항목들
            equipment_type_id: 장비 유형 ID
            manager_instance: DBManager 인스턴스
            
        Returns:
            중복 분석 결과
        """
        duplicates = []
        new_items = []
        
        # 기존 Default DB 데이터 로드
        existing_data = self.db_schema.get_default_values(equipment_type_id)
        existing_params = {item[1]: item for item in existing_data}  # parameter_name으로 인덱싱
        
        for item_id in selected_items:
            item_values = manager_instance.comparison_tree.item(item_id, "values")
            
            # 유지보수 모드 여부에 따라 인덱스 조정
            col_offset = 1 if manager_instance.maint_mode else 0
            module = item_values[col_offset]
            part = item_values[col_offset+1] 
            item_name = item_values[col_offset+2]
            new_value = item_values[col_offset+3]
            
            parameter_name = item_name  # ItemName을 파라미터명으로 사용
            
            if parameter_name in existing_params:
                # 중복 발견
                existing_item = existing_params[parameter_name]
                existing_value = existing_item[2]  # default_value
                
                # 권장사항 결정 (간소화)
                recommendation = self._get_duplicate_recommendation(existing_value, new_value)
                
                duplicates.append(DuplicateItem(
                    parameter_name=parameter_name,
                    existing_value=existing_value,
                    new_value=new_value,
                    source_files=manager_instance.file_names,
                    recommendation=recommendation
                ))
            else:
                # 새 항목
                new_items.append({
                    'parameter_name': parameter_name,
                    'value': new_value,
                    'module': module,
                    'part': part,
                    'item_id': item_id
                })
        
        return {
            'duplicates': duplicates,
            'new_items': new_items,
            'total_duplicates': len(duplicates),
            'total_new': len(new_items),
            'analysis_summary': self._generate_duplicate_summary(duplicates)
        }
    
    def _get_duplicate_recommendation(self, existing_value: str, new_value: str) -> str:
        """중복 항목에 대한 권장사항 결정 (간소화)"""
        
        # 값이 동일한 경우
        if str(existing_value) == str(new_value):
            return "SKIP"  # 중복이므로 건너뛰기
        
        # 간단한 규칙 기반 권장
        try:
            # 숫자 값인 경우 차이 분석
            existing_num = float(str(existing_value).replace(',', ''))
            new_num = float(str(new_value).replace(',', ''))
            
            diff_ratio = abs(new_num - existing_num) / max(abs(existing_num), abs(new_num), 1)
            
            if diff_ratio < 0.05:  # 5% 미만 차이
                return "MERGE"  # 평균값 사용
            else:
                return "UPDATE"  # 새 값으로 업데이트
                
        except ValueError:
            # 문자열인 경우 기본적으로 업데이트
            return "UPDATE"
    
    def _generate_duplicate_summary(self, duplicates: List[DuplicateItem]) -> Dict[str, Any]:
        """중복 분석 요약 생성"""
        if not duplicates:
            return {'message': '중복 항목이 없습니다.', 'action_needed': False}
        
        recommendations = {}
        for duplicate in duplicates:
            rec = duplicate.recommendation
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        return {
            'total_duplicates': len(duplicates),
            'recommendations': recommendations,
            'action_needed': True,
            'conflicting_values': sum(1 for d in duplicates if d.recommendation in ['MERGE', 'UPDATE'])
        }

class DuplicateResolutionDialog:
    """중복 해결 다이얼로그"""
    
    def __init__(self, parent, analysis_result: Dict[str, Any]):
        self.parent = parent
        self.analysis = analysis_result
        self.result = None
        self.dialog = None
        
    def show_dialog(self) -> Optional[Dict[str, Any]]:
        """중복 해결 다이얼로그 표시"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("중복 항목 해결")
        self.dialog.geometry("800x600")
        self.dialog.grab_set()
        
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 요약 정보
        self._create_summary_section(main_frame)
        
        # 중복 항목 목록
        self._create_duplicate_list(main_frame)
        
        # 처리 옵션
        self._create_action_buttons(main_frame)
        
        # 대화상자 중앙 정렬
        self.dialog.transient(self.parent)
        self.dialog.wait_window()
        
        return self.result
    
    def _create_summary_section(self, parent):
        """요약 정보 섹션 생성"""
        summary_frame = ttk.LabelFrame(parent, text="중복 분석 요약", padding=10)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        summary = self.analysis['analysis_summary']
        
        ttk.Label(summary_frame, 
                 text=f"총 중복 항목: {summary['total_duplicates']}개",
                 font=('Arial', 10, 'bold')).pack(anchor='w')
        
        ttk.Label(summary_frame,
                 text=f"새 항목: {self.analysis['total_new']}개").pack(anchor='w')
        
        if summary.get('recommendations'):
            ttk.Label(summary_frame, text="권장 처리 방법:", 
                     font=('Arial', 9, 'bold')).pack(anchor='w', pady=(5, 0))
            
            for action, count in summary['recommendations'].items():
                action_text = {
                    'REPLACE': '교체 권장',
                    'UPDATE': '업데이트 권장', 
                    'KEEP_EXISTING': '기존값 유지',
                    'MERGE': '병합 검토',
                    'SKIP': '건너뛰기'
                }.get(action, action)
                
                ttk.Label(summary_frame, 
                         text=f"  • {action_text}: {count}개").pack(anchor='w')
    
    def _create_duplicate_list(self, parent):
        """중복 항목 목록 생성"""
        list_frame = ttk.LabelFrame(parent, text="중복 항목 상세", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 트리뷰 생성 (간소화)
        columns = ("parameter", "existing_value", "new_value", "recommendation")
        self.duplicate_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        # 헤더 설정
        self.duplicate_tree.heading("parameter", text="파라미터명")
        self.duplicate_tree.heading("existing_value", text="기존값")
        self.duplicate_tree.heading("new_value", text="새 값")
        self.duplicate_tree.heading("recommendation", text="권장사항")
        
        # 컬럼 너비 설정
        self.duplicate_tree.column("parameter", width=200)
        self.duplicate_tree.column("existing_value", width=150)
        self.duplicate_tree.column("new_value", width=150)
        self.duplicate_tree.column("recommendation", width=150)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.duplicate_tree.yview)
        self.duplicate_tree.configure(yscrollcommand=scrollbar.set)
        
        # 패킹
        self.duplicate_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 데이터 채우기 (간소화)
        for duplicate in self.analysis['duplicates']:
            recommendation_text = {
                'UPDATE': '📝 업데이트',
                'MERGE': '🔗 병합',
                'SKIP': '⏭️ 건너뛰기'
            }.get(duplicate.recommendation, duplicate.recommendation)
            
            self.duplicate_tree.insert("", "end", values=(
                duplicate.parameter_name,
                duplicate.existing_value,
                duplicate.new_value,
                recommendation_text
            ))
    
    def _create_action_buttons(self, parent):
        """처리 버튼 생성"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 처리 옵션 설명
        options_frame = ttk.LabelFrame(button_frame, text="처리 옵션", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(options_frame, 
                 text="• 자동 처리: 권장사항에 따라 자동으로 처리").pack(anchor='w')
        ttk.Label(options_frame,
                 text="• 선택적 처리: 각 항목을 개별적으로 검토 후 처리").pack(anchor='w')
        ttk.Label(options_frame,
                 text="• 신규만 추가: 중복 항목은 건너뛰고 새 항목만 추가").pack(anchor='w')
        
        # 버튼들
        action_button_frame = ttk.Frame(button_frame)
        action_button_frame.pack(fill=tk.X)
        
        ttk.Button(action_button_frame, text="🤖 자동 처리", 
                  command=self._auto_resolve).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(action_button_frame, text="🔍 선택적 처리",
                  command=self._selective_resolve).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_button_frame, text="➕ 신규만 추가",
                  command=self._new_only).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_button_frame, text="❌ 취소",
                  command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
    
    def _auto_resolve(self):
        """자동 해결"""
        self.result = {
            'action': 'auto',
            'analysis': self.analysis
        }
        self.dialog.destroy()
    
    def _selective_resolve(self):
        """선택적 해결"""
        self.result = {
            'action': 'selective',
            'analysis': self.analysis
        }
        self.dialog.destroy()
    
    def _new_only(self):
        """신규만 추가"""
        self.result = {
            'action': 'new_only',
            'analysis': self.analysis
        }
        self.dialog.destroy()
    
    def _cancel(self):
        """취소"""
        self.result = None
        self.dialog.destroy()

class EnhancedDefaultDBTransfer:
    """향상된 Default DB 전송 시스템"""
    
    def __init__(self, db_schema, update_log_callback=None):
        self.db_schema = db_schema
        self.update_log = update_log_callback or self._default_log
        self.duplicate_analyzer = DuplicateAnalyzer(db_schema)
    
    def _default_log(self, message: str):
        """기본 로그 출력"""
        print(f"[Transfer] {message}")
    
    def enhanced_transfer_to_default_db(self, selected_items: List, equipment_type_id: int,
                                      manager_instance) -> Dict[str, Any]:
        """
        향상된 Default DB 전송
        
        Returns:
            전송 결과 딕셔너리
        """
        try:
            self.update_log("🔍 Default DB 전송 시작 - 중복 항목 분석 중...")
            
            # 1. 중복 분석
            analysis = self.duplicate_analyzer.analyze_duplicates_smart(
                selected_items, equipment_type_id, manager_instance
            )
            
            if analysis['total_duplicates'] > 0:
                # 2. 중복 해결 다이얼로그 표시
                dialog = DuplicateResolutionDialog(manager_instance.window, analysis)
                resolution = dialog.show_dialog()
                
                if not resolution:
                    return {'success': False, 'message': '사용자가 취소했습니다.'}
                
                # 3. 선택된 방식에 따라 처리
                return self._process_transfer_with_resolution(
                    selected_items, equipment_type_id, manager_instance, 
                    analysis, resolution
                )
            else:
                # 중복 없음 - 직접 전송
                self.update_log("✅ 중복 항목 없음 - 직접 전송 진행")
                return self._direct_transfer(selected_items, equipment_type_id, manager_instance)
                
        except Exception as e:
            error_msg = f"Default DB 전송 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}
    
    def _process_transfer_with_resolution(self, selected_items: List, equipment_type_id: int,
                                        manager_instance, analysis: Dict, resolution: Dict) -> Dict[str, Any]:
        """해결 방안에 따른 전송 처리"""
        action = resolution['action']
        results = {'success': True, 'added': 0, 'updated': 0, 'skipped': 0, 'details': []}
        
        try:
            if action == 'auto':
                # 자동 처리
                results = self._auto_process_duplicates(analysis, equipment_type_id, manager_instance)
                
            elif action == 'selective':
                # 선택적 처리 (개별 확인)
                results = self._selective_process_duplicates(analysis, equipment_type_id, manager_instance)
                
            elif action == 'new_only':
                # 신규만 추가
                results = self._process_new_items_only(analysis, equipment_type_id, manager_instance)
            
            # 전송 완료 로그
            self.update_log(
                f"✅ Default DB 전송 완료 - "
                f"추가: {results['added']}, 업데이트: {results['updated']}, 건너뛰기: {results['skipped']}"
            )
            
            return results
            
        except Exception as e:
            error_msg = f"전송 처리 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}
    
    def _auto_process_duplicates(self, analysis: Dict, equipment_type_id: int, 
                               manager_instance) -> Dict[str, Any]:
        """자동 중복 처리"""
        results = {'success': True, 'added': 0, 'updated': 0, 'skipped': 0, 'details': []}
        
        # 새 항목 추가
        for new_item in analysis['new_items']:
            try:
                self._add_new_parameter(new_item, equipment_type_id, manager_instance)
                results['added'] += 1
                results['details'].append(f"추가: {new_item['parameter_name']}")
            except Exception as e:
                results['details'].append(f"추가 실패: {new_item['parameter_name']} - {str(e)}")
        
        # 중복 항목 처리
        for duplicate in analysis['duplicates']:
            try:
                action = duplicate.recommendation
                
                if action == 'REPLACE' or action == 'UPDATE':
                    self._update_existing_parameter(duplicate, equipment_type_id)
                    results['updated'] += 1
                    results['details'].append(f"업데이트: {duplicate.parameter_name}")
                    
                elif action == 'MERGE':
                    merged_value = self._merge_values(duplicate.existing_value, duplicate.new_value)
                    duplicate.new_value = merged_value
                    self._update_existing_parameter(duplicate, equipment_type_id)
                    results['updated'] += 1
                    results['details'].append(f"병합: {duplicate.parameter_name}")
                    
                else:  # KEEP_EXISTING, SKIP
                    results['skipped'] += 1
                    results['details'].append(f"건너뛰기: {duplicate.parameter_name}")
                    
            except Exception as e:
                results['details'].append(f"처리 실패: {duplicate.parameter_name} - {str(e)}")
        
        return results
    
    def _selective_process_duplicates(self, analysis: Dict, equipment_type_id: int,
                                    manager_instance) -> Dict[str, Any]:
        """선택적 중복 처리 (개별 확인)"""
        results = {'success': True, 'added': 0, 'updated': 0, 'skipped': 0, 'details': []}
        
        # 새 항목은 자동 추가
        for new_item in analysis['new_items']:
            try:
                self._add_new_parameter(new_item, equipment_type_id, manager_instance)
                results['added'] += 1
                results['details'].append(f"추가: {new_item['parameter_name']}")
            except Exception as e:
                results['details'].append(f"추가 실패: {new_item['parameter_name']} - {str(e)}")
        
        # 중복 항목은 개별 확인
        for duplicate in analysis['duplicates']:
            decision = self._ask_individual_decision(duplicate)
            
            try:
                if decision == 'update':
                    self._update_existing_parameter(duplicate, equipment_type_id)
                    results['updated'] += 1
                    results['details'].append(f"업데이트: {duplicate.parameter_name}")
                elif decision == 'merge':
                    merged_value = self._merge_values(duplicate.existing_value, duplicate.new_value)
                    duplicate.new_value = merged_value
                    self._update_existing_parameter(duplicate, equipment_type_id)
                    results['updated'] += 1
                    results['details'].append(f"병합: {duplicate.parameter_name}")
                else:  # skip
                    results['skipped'] += 1
                    results['details'].append(f"건너뛰기: {duplicate.parameter_name}")
                    
            except Exception as e:
                results['details'].append(f"처리 실패: {duplicate.parameter_name} - {str(e)}")
        
        return results
    
    def _process_new_items_only(self, analysis: Dict, equipment_type_id: int,
                              manager_instance) -> Dict[str, Any]:
        """신규 항목만 처리"""
        results = {'success': True, 'added': 0, 'updated': 0, 'skipped': len(analysis['duplicates']), 'details': []}
        
        # 새 항목만 추가
        for new_item in analysis['new_items']:
            try:
                self._add_new_parameter(new_item, equipment_type_id, manager_instance)
                results['added'] += 1
                results['details'].append(f"추가: {new_item['parameter_name']}")
            except Exception as e:
                results['details'].append(f"추가 실패: {new_item['parameter_name']} - {str(e)}")
        
        # 중복 항목은 모두 건너뛰기
        for duplicate in analysis['duplicates']:
            results['details'].append(f"건너뛰기: {duplicate.parameter_name}")
        
        return results
    
    def _add_new_parameter(self, new_item: Dict, equipment_type_id: int, manager_instance):
        """새 파라미터 추가 (간소화)"""
        # DB에 추가
        self.db_schema.add_default_value(
            equipment_type_id=equipment_type_id,
            parameter_name=new_item['parameter_name'],
            default_value=new_item['value'],
            min_spec=None,
            max_spec=None,
            occurrence_count=1,
            total_files=len(manager_instance.file_names),
            confidence_score=1.0,  # 기본값 사용
            source_files=','.join(manager_instance.file_names),
            description="",
            module_name=new_item['module'],
            part_name=new_item['part'],
            item_type='double',
            is_checklist=0
        )
    
    def _update_existing_parameter(self, duplicate: DuplicateItem, equipment_type_id: int):
        """기존 파라미터 업데이트"""
        # 기존 데이터 찾기
        existing_data = self.db_schema.get_default_values(equipment_type_id)
        
        for item in existing_data:
            if item[1] == duplicate.parameter_name:  # parameter_name 매칭
                param_id = item[0]
                
                # 업데이트 (간소화)
                self.db_schema.update_default_value(
                    param_id,
                    default_value=duplicate.new_value,
                    source_files=','.join(duplicate.source_files)
                )
                break
    
    def _merge_values(self, existing_value: str, new_value: str) -> str:
        """두 값을 통계적으로 병합"""
        try:
            # 숫자 값인 경우 평균 계산
            existing_num = float(str(existing_value).replace(',', ''))
            new_num = float(str(new_value).replace(',', ''))
            
            merged = (existing_num + new_num) / 2
            return str(merged)
            
        except ValueError:
            # 문자열인 경우 새 값 사용 (또는 다른 병합 로직)
            return new_value
    
    def _ask_individual_decision(self, duplicate: DuplicateItem) -> str:
        """개별 중복 항목에 대한 사용자 결정 요청"""
        msg = (
            f"파라미터: {duplicate.parameter_name}\n"
            f"기존값: {duplicate.existing_value}\n"
            f"새 값: {duplicate.new_value}\n\n"
            f"권장사항: {duplicate.recommendation}\n\n"
            f"어떻게 처리하시겠습니까?"
        )
        
        # 사용자 선택 다이얼로그 (간단한 버전)
        result = messagebox.askyesnocancel(
            "중복 항목 처리",
            msg + "\n\n예: 새 값으로 업데이트\n아니오: 건너뛰기\n취소: 병합"
        )
        
        if result is True:
            return 'update'
        elif result is False:
            return 'skip'
        else:
            return 'merge'
    
    def _direct_transfer(self, selected_items: List, equipment_type_id: int, 
                       manager_instance) -> Dict[str, Any]:
        """직접 전송 (중복 없는 경우)"""
        results = {'success': True, 'added': 0, 'updated': 0, 'skipped': 0, 'details': []}
        
        for item_id in selected_items:
            try:
                item_values = manager_instance.comparison_tree.item(item_id, "values")
                
                # 유지보수 모드 여부에 따라 인덱스 조정
                col_offset = 1 if manager_instance.maint_mode else 0
                module = item_values[col_offset]
                part = item_values[col_offset+1]
                item_name = item_values[col_offset+2]
                value = item_values[col_offset+3]
                
                # DB에 추가 (간소화)
                self.db_schema.add_default_value(
                    equipment_type_id=equipment_type_id,
                    parameter_name=item_name,
                    default_value=value,
                    min_spec=None,
                    max_spec=None,
                    occurrence_count=1,
                    total_files=len(manager_instance.file_names),
                    confidence_score=1.0,  # 기본값 사용
                    source_files=','.join(manager_instance.file_names),
                    description="",
                    module_name=module,
                    part_name=part,
                    item_type='double',
                    is_checklist=0
                )
                
                results['added'] += 1
                results['details'].append(f"추가: {item_name}")
                
            except Exception as e:
                results['details'].append(f"추가 실패: {item_name} - {str(e)}")
        
        return results

# manager.py에서 사용할 통합 함수
def enhanced_send_selected_to_default_db(manager_instance):
    """
    기존 send_selected_to_default_db 함수를 대체하는 향상된 버전
    """
    try:
        # 선택된 항목 확인
        selected_items = manager_instance.comparison_tree.selection()
        if not selected_items:
            messagebox.showinfo("알림", "전송할 항목을 선택해주세요.")
            return
        
        # 장비 유형 선택 다이얼로그는 기존 로직 사용
        # (기존 코드의 장비 유형 선택 부분을 그대로 활용)
        
        # 임시로 첫 번째 장비 유형 사용 (실제로는 다이얼로그에서 선택된 값 사용)
        equipment_types = manager_instance.db_schema.get_equipment_types()
        if not equipment_types:
            messagebox.showerror("오류", "등록된 장비 유형이 없습니다.")
            return
        
        equipment_type_id = equipment_types[0][0]  # 첫 번째 장비 유형 사용
        
        # 향상된 전송 시스템 실행
        transfer_system = EnhancedDefaultDBTransfer(
            db_schema=manager_instance.db_schema,
            update_log_callback=getattr(manager_instance, 'update_log', None)
        )
        
        result = transfer_system.enhanced_transfer_to_default_db(
            selected_items, equipment_type_id, manager_instance
        )
        
        if result['success']:
            messagebox.showinfo(
                "전송 완료",
                f"Default DB 전송이 완료되었습니다.\n"
                f"추가: {result['added']}개\n"
                f"업데이트: {result['updated']}개\n"
                f"건너뛰기: {result['skipped']}개"
            )
        else:
            messagebox.showerror("전송 실패", result['message'])
    
    except Exception as e:
        messagebox.showerror("오류", f"Default DB 전송 중 오류 발생: {str(e)}")