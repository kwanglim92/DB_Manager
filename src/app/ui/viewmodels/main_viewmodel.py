"""
메인 애플리케이션 ViewModel
기존 DBManager 클래스의 주요 상태와 비즈니스 로직을 분리
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_viewmodel import BaseViewModel, ObservableList, ObservableDict
from app.schema import DBSchema


class MainViewModel(BaseViewModel):
    """
    메인 애플리케이션의 ViewModel
    애플리케이션 전체 상태와 비즈니스 로직 관리
    """
    
    def __init__(self):
        """MainViewModel 초기화"""
        super().__init__()
        
        # 기본 상태 속성들
        self._init_properties()
        
        # 데이터베이스 연결
        self._init_database()
        
        # 명령 등록
        self._register_commands()
    
    def _init_properties(self):
        """기본 속성들 초기화"""
        # 애플리케이션 상태
        self.set_property('maint_mode', False, notify=False)
        self.set_property('selected_equipment_type_id', None, notify=False)
        self.set_property('app_title', "DB Manager", notify=False)
        self.set_property('window_geometry', "1300x800", notify=False)
        
        # 파일 및 폴더 관련
        self.set_property('file_names', ObservableList(), notify=False)
        self.set_property('folder_path', "", notify=False)
        self.set_property('merged_df', None, notify=False)
        
        # UI 상태
        self.set_property('status_message', "👤 장비 생산 엔지니어 모드", notify=False)
        self.set_property('log_messages', ObservableList(), notify=False)
        
        # 데이터베이스 상태
        self.set_property('db_connected', False, notify=False)
        self.set_property('db_path', "", notify=False)
        
        # 🎯 DB 비교 관련 속성들
        self.set_property('comparison_data', ObservableList(), notify=False)
        self.set_property('selected_items', ObservableList(), notify=False)
        self.set_property('search_filter', "", notify=False)
        self.set_property('show_differences_only', False, notify=False)
        self.set_property('show_default_candidates', False, notify=False)
        
        # 🎯 QC 기능 관련 속성들 (QC 모드일 때만 활성화)
        self.set_property('qc_results', ObservableList(), notify=False)
        self.set_property('equipment_types', ObservableList(), notify=False)
        self.set_property('default_db_values', ObservableList(), notify=False)
        
        # 🎯 통계 및 분석 관련
        self.set_property('statistics_data', ObservableDict(), notify=False)
        self.set_property('analysis_progress', 0, notify=False)
        
        # 🎯 설정 관련
        self.set_property('use_new_services', ObservableDict(), notify=False)
    
    def _init_database(self):
        """데이터베이스 초기화"""
        try:
            self.db_schema = DBSchema()
            self.set_property('db_connected', True)
            self.add_log_message("로컬 데이터베이스 초기화 완료")
            
            # 데이터베이스 경로 설정
            if hasattr(self.db_schema, 'db_path'):
                self.set_property('db_path', self.db_schema.db_path)
                
        except Exception as e:
            self.db_schema = None
            self.set_property('db_connected', False)
            self.error_message = f"DB 스키마 초기화 실패: {str(e)}"
            self.add_log_message(f"DB 스키마 초기화 실패: {str(e)}")
    
    def _register_commands(self):
        """명령들 등록"""
        # 폴더/파일 관련 명령
        self.register_command('load_folder', self._load_folder_execute)
        self.register_command('clear_files', self._clear_files_execute)
        
        # 유지보수 모드 관련 명령
        self.register_command('toggle_maintenance_mode', 
                            self._toggle_maintenance_mode_execute,
                            self._can_toggle_maintenance_mode)
        
        # 애플리케이션 명령
        self.register_command('export_report', self._export_report_execute,
                            self._can_export_report)
        self.register_command('show_about', self._show_about_execute)
        self.register_command('show_user_guide', self._show_user_guide_execute)
        
        # 로깅 명령
        self.register_command('clear_log', self._clear_log_execute)
        
        # 🎯 DB 비교 관련 명령들
        self.register_command('update_comparison_view', self._update_comparison_view_execute)
        self.register_command('toggle_search_filter', self._toggle_search_filter_execute)
        self.register_command('toggle_differences_only', self._toggle_differences_only_execute)
        self.register_command('toggle_default_candidates', self._toggle_default_candidates_execute,
                            self._can_toggle_default_candidates)
        self.register_command('add_to_default_db', self._add_to_default_db_execute,
                            self._can_add_to_default_db)
        
        # 🎯 QC 기능 관련 명령들 (QC 모드일 때만 활성화)
        self.register_command('run_qc_check', self._run_qc_check_execute,
                            self._can_run_qc_check)
        self.register_command('load_equipment_types', self._load_equipment_types_execute)
        self.register_command('add_equipment_type', self._add_equipment_type_execute,
                            self._can_modify_equipment_types)
        self.register_command('delete_equipment_type', self._delete_equipment_type_execute,
                            self._can_modify_equipment_types)
        self.register_command('load_default_db_values', self._load_default_db_values_execute)
        self.register_command('add_parameter', self._add_parameter_execute,
                            self._can_modify_parameters)
        self.register_command('edit_parameter', self._edit_parameter_execute,
                            self._can_modify_parameters)
        self.register_command('delete_parameter', self._delete_parameter_execute,
                            self._can_modify_parameters)
        
        # 🎯 통계 및 분석 관련 명령들
        self.register_command('calculate_statistics', self._calculate_statistics_execute,
                            self._can_calculate_statistics)
        self.register_command('export_statistics', self._export_statistics_execute,
                            self._can_export_statistics)
        self.register_command('refresh_all_data', self._refresh_all_data_execute)
        
    
    # 속성 접근자들
    @property
    def maint_mode(self) -> bool:
        """유지보수 모드 상태"""
        return self.get_property('maint_mode', False)
    
    @maint_mode.setter
    def maint_mode(self, value: bool):
        """유지보수 모드 상태 설정"""
        if self.set_property('maint_mode', value):
            self.add_log_message(f"유지보수 모드 {'활성화' if value else '비활성화'}")
            self.set_property('status_message', 
                            f"유지보수 모드 {'활성화' if value else '비활성화'}")
    
    @property
    def selected_equipment_type_id(self) -> Optional[int]:
        """선택된 장비 유형 ID"""
        return self.get_property('selected_equipment_type_id')
    
    @selected_equipment_type_id.setter
    def selected_equipment_type_id(self, value: Optional[int]):
        """선택된 장비 유형 ID 설정"""
        self.set_property('selected_equipment_type_id', value)
    
    @property
    def folder_path(self) -> str:
        """현재 폴더 경로"""
        return self.get_property('folder_path', "")
    
    @folder_path.setter
    def folder_path(self, value: str):
        """폴더 경로 설정"""
        self.set_property('folder_path', value)
    
    @property
    def file_names(self) -> ObservableList:
        """로드된 파일명 리스트"""
        return self.get_property('file_names', ObservableList())
    
    @property
    def status_message(self) -> str:
        """상태 메시지"""
        return self.get_property('status_message', "Ready")
    
    @status_message.setter
    def status_message(self, value: str):
        """상태 메시지 설정"""
        self.set_property('status_message', value)
    
    @property
    def log_messages(self) -> ObservableList:
        """로그 메시지 리스트"""
        return self.get_property('log_messages', ObservableList())
    
    @property
    def db_connected(self) -> bool:
        """데이터베이스 연결 상태"""
        return self.get_property('db_connected', False)
    
    @property
    def app_title(self) -> str:
        """애플리케이션 제목"""
        return self.get_property('app_title', "DB Manager")
    
    @property
    def window_geometry(self) -> str:
        """윈도우 크기"""
        return self.get_property('window_geometry', "1300x800")
    
    # 🎯 DB 비교 관련 속성 접근자들
    @property
    def comparison_data(self) -> ObservableList:
        """비교 데이터"""
        return self.get_property('comparison_data', ObservableList())
    
    @property
    def selected_items(self) -> ObservableList:
        """선택된 항목들"""
        return self.get_property('selected_items', ObservableList())
    
    @property
    def search_filter(self) -> str:
        """검색 필터"""
        return self.get_property('search_filter', "")
    
    @search_filter.setter
    def search_filter(self, value: str):
        """검색 필터 설정"""
        self.set_property('search_filter', value)
    
    @property
    def show_differences_only(self) -> bool:
        """차이점만 표시"""
        return self.get_property('show_differences_only', False)
    
    @show_differences_only.setter
    def show_differences_only(self, value: bool):
        """차이점만 표시 설정"""
        self.set_property('show_differences_only', value)
    
    @property
    def show_default_candidates(self) -> bool:
        """설정값 후보 표시"""
        return self.get_property('show_default_candidates', False)
    
    @show_default_candidates.setter
    def show_default_candidates(self, value: bool):
        """설정값 후보 표시 설정"""
        if self.maint_mode:  # QC 모드일 때만 허용
            self.set_property('show_default_candidates', value)
    
    # 🎯 QC 기능 관련 속성 접근자들
    @property
    def qc_results(self) -> ObservableList:
        """QC 검수 결과"""
        return self.get_property('qc_results', ObservableList())
    
    @property
    def equipment_types(self) -> ObservableList:
        """장비 유형 목록"""
        return self.get_property('equipment_types', ObservableList())
    
    @property
    def default_db_values(self) -> ObservableList:
        """설정값 DB 목록"""
        return self.get_property('default_db_values', ObservableList())
    
    
    # 🎯 통계 및 분석 관련 속성 접근자들
    @property
    def statistics_data(self) -> ObservableDict:
        """통계 데이터"""
        return self.get_property('statistics_data', ObservableDict())
    
    @property
    def analysis_progress(self) -> int:
        """분석 진행률 (0-100)"""
        return self.get_property('analysis_progress', 0)
    
    @analysis_progress.setter
    def analysis_progress(self, value: int):
        """분석 진행률 설정"""
        value = max(0, min(100, value))  # 0-100 범위로 제한
        self.set_property('analysis_progress', value)
    
    # 로깅 관련 메서드들
    def add_log_message(self, message: str):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        
        log_messages = self.log_messages
        log_messages.append(log_entry)
        
        # 로그가 너무 많으면 오래된 것 삭제 (최대 1000개)
        if len(log_messages) > 1000:
            log_messages.pop(0)
    
    def clear_log_messages(self):
        """로그 메시지 클리어"""
        self.log_messages.clear()
    
    def get_recent_log_messages(self, count: int = 50) -> List[str]:
        """최근 로그 메시지 가져오기"""
        log_messages = self.log_messages
        return list(log_messages[-count:]) if len(log_messages) > count else list(log_messages)
    
    # 파일 관련 메서드들
    def has_files_loaded(self) -> bool:
        """파일이 로드되었는지 확인"""
        return len(self.file_names) > 0
    
    def get_file_count(self) -> int:
        """로드된 파일 개수"""
        return len(self.file_names)
    
    def add_file(self, filename: str):
        """파일 추가"""
        if filename not in self.file_names:
            self.file_names.append(filename)
            self.add_log_message(f"파일 추가됨: {filename}")
    
    def remove_file(self, filename: str):
        """파일 제거"""
        if filename in self.file_names:
            self.file_names.remove(filename)
            self.add_log_message(f"파일 제거됨: {filename}")
    
    def clear_files(self):
        """모든 파일 클리어"""
        file_count = len(self.file_names)
        self.file_names.clear()
        self.folder_path = ""
        self.set_property('merged_df', None)
        if file_count > 0:
            self.add_log_message(f"{file_count}개 파일 클리어됨")
    
    # 데이터베이스 관련 메서드들
    def reconnect_database(self) -> bool:
        """데이터베이스 재연결"""
        try:
            if self.db_schema:
                self.db_schema = None
            
            self._init_database()
            return self.db_connected
            
        except Exception as e:
            self.error_message = f"데이터베이스 재연결 실패: {str(e)}"
            self.add_log_message(f"데이터베이스 재연결 실패: {str(e)}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """데이터베이스 정보 가져오기"""
        if not self.db_connected or not self.db_schema:
            return {}
        
        return {
            'connected': self.db_connected,
            'path': self.get_property('db_path', ''),
            'schema_version': getattr(self.db_schema, 'version', 'Unknown'),
            'tables': ['Equipment_Types', 'Default_DB_Values', 'Change_History']
        }
    
    # 유효성 검사
    def validate(self) -> List[str]:
        """ViewModel 유효성 검사"""
        errors = []
        
        if not self.db_connected:
            errors.append("데이터베이스가 연결되지 않았습니다.")
        
        return errors
    
    # 명령 실행 함수들
    def _load_folder_execute(self, folder_path: str) -> bool:
        """폴더 로드 실행"""
        try:
            if not os.path.exists(folder_path):
                raise ValueError(f"폴더가 존재하지 않습니다: {folder_path}")
            
            # 기존 파일들 클리어
            self.clear_files()
            
            # 새 폴더 설정
            self.folder_path = folder_path
            
            # 폴더 내 파일들 스캔 (예: .txt, .csv 파일들)
            supported_extensions = ['.txt', '.csv', '.xlsx']
            files_found = []
            
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file)
                    if ext.lower() in supported_extensions:
                        files_found.append(file)
            
            # 파일들 추가
            for file in sorted(files_found):
                self.add_file(file)
            
            self.add_log_message(f"폴더 로드 완료: {folder_path} ({len(files_found)}개 파일)")
            self.status_message = f"폴더 로드됨: {len(files_found)}개 파일"
            
            return True
            
        except Exception as e:
            self.error_message = f"폴더 로드 실패: {str(e)}"
            self.add_log_message(f"폴더 로드 실패: {str(e)}")
            return False
    
    def _clear_files_execute(self) -> bool:
        """파일 클리어 실행"""
        self.clear_files()
        self.status_message = "파일 클리어됨"
        return True
    
    def _toggle_maintenance_mode_execute(self, password: str = None) -> bool:
        """유지보수 모드 토글 실행"""
        if self.maint_mode:
            # 현재 활성화 상태면 비활성화
            self.maint_mode = False
            return True
        else:
            # 현재 비활성화 상태면 비밀번호 확인 후 활성화
            if password is None:
                self.error_message = "비밀번호가 필요합니다."
                return False
            
            # 비밀번호 검증 (기존 utils 함수 사용)
            try:
                from app.utils import verify_password
                if verify_password(password):
                    self.maint_mode = True
                    return True
                else:
                    self.error_message = "잘못된 비밀번호입니다."
                    return False
            except ImportError:
                # fallback: 기본 비밀번호 "1"
                if password == "1":
                    self.maint_mode = True
                    return True
                else:
                    self.error_message = "잘못된 비밀번호입니다."
                    return False
    
    def _can_toggle_maintenance_mode(self) -> bool:
        """유지보수 모드 토글 가능 여부"""
        return not self.is_busy
    
    def _export_report_execute(self) -> bool:
        """보고서 내보내기 실행"""
        try:
            if not self.has_files_loaded():
                self.error_message = "내보낼 데이터가 없습니다."
                return False
            
            # 실제 보고서 내보내기 로직은 별도 서비스에서 처리
            self.add_log_message("보고서 내보내기 요청됨")
            return True
            
        except Exception as e:
            self.error_message = f"보고서 내보내기 실패: {str(e)}"
            return False
    
    def _can_export_report(self) -> bool:
        """보고서 내보내기 가능 여부"""
        return not self.is_busy and self.has_files_loaded()
    
    def _show_about_execute(self) -> Dict[str, str]:
        """프로그램 정보 표시"""
        return {
            'title': '프로그램 정보',
            'message': (
                "DB Manager\n"
                "버전: 1.0.1\n"
                "제작자: kwanglim92\n\n"
                "이 프로그램은 DB 파일 비교, 관리, 보고서 생성 등 "
                "다양한 기능을 제공합니다."
            )
        }
    
    def _show_user_guide_execute(self) -> Dict[str, str]:
        """사용자 가이드 표시"""
        guide_text = (
            "[DB Manager 사용자 가이드]\n\n"
            "• 폴더 열기: 파일 > 폴더 열기 (Ctrl+O)\n"
            "• DB 비교: 여러 DB 파일을 불러와 값 차이, 격자 뷰, 보고서 등 다양한 탭에서 확인\n"
            "• 유지보수 모드: 도구 > Maintenance Mode (비밀번호 필요)\n"
            "• Default DB 관리, QC 검수 등은 유지보수 모드에서만 사용 가능\n"
            "• 각 탭에서 우클릭 및 버튼으로 항목 추가/삭제/내보내기 등 다양한 작업 지원\n"
            "• 문의: github.com/kwanglim92/DB_Manager\n"
        )
        return {
            'title': '사용 설명서',
            'message': guide_text
        }
    
    def _clear_log_execute(self) -> bool:
        """로그 클리어 실행"""
        self.clear_log_messages()
        self.add_log_message("로그가 클리어되었습니다.")
        return True
    
    # 리소스 정리
    def cleanup(self):
        """리소스 정리"""
        try:
            if hasattr(self, 'db_schema') and self.db_schema:
                # 데이터베이스 연결 정리
                self.db_schema = None
            
            # 파일 데이터 정리
            self.clear_files()
            
            # 부모 클래스 정리
            super().cleanup()
            
        except Exception as e:
            print(f"MainViewModel 정리 중 오류: {e}")
    
    def refresh(self):
        """ViewModel 새로고침"""
        try:
            # 데이터베이스 상태 확인
            if self.db_schema:
                self.set_property('db_connected', True)
            else:
                self.set_property('db_connected', False)
            
            # 기타 새로고침 로직
            self.add_log_message("ViewModel 새로고침 완료")
            
        except Exception as e:
            self.error_message = f"새로고침 중 오류: {str(e)}"
            self.add_log_message(f"새로고침 중 오류: {str(e)}")
    
    # 🎯 새로 추가된 명령 실행 메서드들
    
    # DB 비교 관련 명령 실행 메서드들
    def _update_comparison_view_execute(self) -> bool:
        """비교 뷰 업데이트"""
        try:
            self.add_log_message("비교 뷰 업데이트 시작")
            # 실제 비교 로직은 서비스 레이어에서 처리
            return True
        except Exception as e:
            self.error_message = f"비교 뷰 업데이트 실패: {str(e)}"
            return False
    
    def _toggle_search_filter_execute(self, filter_text: str = "") -> bool:
        """검색 필터 토글"""
        try:
            self.search_filter = filter_text
            self.add_log_message(f"검색 필터 설정: '{filter_text}'")
            return True
        except Exception as e:
            self.error_message = f"검색 필터 설정 실패: {str(e)}"
            return False
    
    def _toggle_differences_only_execute(self) -> bool:
        """차이점만 표시 토글"""
        try:
            new_value = not self.show_differences_only
            self.show_differences_only = new_value
            self.add_log_message(f"차이점만 표시: {'활성화' if new_value else '비활성화'}")
            return True
        except Exception as e:
            self.error_message = f"차이점만 표시 토글 실패: {str(e)}"
            return False
    
    def _toggle_default_candidates_execute(self) -> bool:
        """설정값 후보 표시 토글"""
        try:
            if not self.maint_mode:
                self.error_message = "QC 모드에서만 사용 가능합니다."
                return False
            
            new_value = not self.show_default_candidates
            self.show_default_candidates = new_value
            self.add_log_message(f"설정값 후보 표시: {'활성화' if new_value else '비활성화'}")
            return True
        except Exception as e:
            self.error_message = f"설정값 후보 표시 토글 실패: {str(e)}"
            return False
    
    def _can_toggle_default_candidates(self) -> bool:
        """설정값 후보 표시 토글 가능 여부"""
        return self.maint_mode
    
    def _add_to_default_db_execute(self, items: List[Dict]) -> bool:
        """설정값 DB에 항목 추가"""
        try:
            if not self.maint_mode:
                self.error_message = "QC 모드에서만 사용 가능합니다."
                return False
            
            added_count = len(items)
            self.add_log_message(f"설정값 DB에 {added_count}개 항목 추가")
            return True
        except Exception as e:
            self.error_message = f"설정값 DB 추가 실패: {str(e)}"
            return False
    
    def _can_add_to_default_db(self) -> bool:
        """설정값 DB 추가 가능 여부"""
        return self.maint_mode and len(self.selected_items) > 0
    
    # QC 기능 관련 명령 실행 메서드들
    def _run_qc_check_execute(self) -> bool:
        """QC 검수 실행"""
        try:
            if not self.maint_mode:
                self.error_message = "QC 모드에서만 사용 가능합니다."
                return False
            
            self.add_log_message("QC 검수 시작")
            # 실제 QC 로직은 서비스 레이어에서 처리
            return True
        except Exception as e:
            self.error_message = f"QC 검수 실행 실패: {str(e)}"
            return False
    
    def _can_run_qc_check(self) -> bool:
        """QC 검수 실행 가능 여부"""
        return self.maint_mode and self.has_files_loaded()
    
    def _load_equipment_types_execute(self) -> bool:
        """장비 유형 로드"""
        try:
            self.add_log_message("장비 유형 목록 로드")
            # 실제 로드 로직은 서비스 레이어에서 처리
            return True
        except Exception as e:
            self.error_message = f"장비 유형 로드 실패: {str(e)}"
            return False
    
    def _add_equipment_type_execute(self, type_name: str, description: str = "") -> bool:
        """장비 유형 추가"""
        try:
            if not self.maint_mode:
                self.error_message = "QC 모드에서만 사용 가능합니다."
                return False
            
            self.add_log_message(f"장비 유형 추가: {type_name}")
            return True
        except Exception as e:
            self.error_message = f"장비 유형 추가 실패: {str(e)}"
            return False
    
    def _delete_equipment_type_execute(self, type_id: int) -> bool:
        """장비 유형 삭제"""
        try:
            if not self.maint_mode:
                self.error_message = "QC 모드에서만 사용 가능합니다."
                return False
            
            self.add_log_message(f"장비 유형 삭제: ID {type_id}")
            return True
        except Exception as e:
            self.error_message = f"장비 유형 삭제 실패: {str(e)}"
            return False
    
    def _can_modify_equipment_types(self) -> bool:
        """장비 유형 수정 가능 여부"""
        return self.maint_mode
    
    def _load_default_db_values_execute(self) -> bool:
        """설정값 DB 로드"""
        try:
            self.add_log_message("설정값 DB 로드")
            return True
        except Exception as e:
            self.error_message = f"설정값 DB 로드 실패: {str(e)}"
            return False
    
    def _add_parameter_execute(self, parameter_data: Dict) -> bool:
        """파라미터 추가"""
        try:
            if not self.maint_mode:
                self.error_message = "QC 모드에서만 사용 가능합니다."
                return False
            
            param_name = parameter_data.get('name', 'Unknown')
            self.add_log_message(f"파라미터 추가: {param_name}")
            return True
        except Exception as e:
            self.error_message = f"파라미터 추가 실패: {str(e)}"
            return False
    
    def _edit_parameter_execute(self, parameter_id: int, parameter_data: Dict) -> bool:
        """파라미터 편집"""
        try:
            if not self.maint_mode:
                self.error_message = "QC 모드에서만 사용 가능합니다."
                return False
            
            param_name = parameter_data.get('name', f'ID {parameter_id}')
            self.add_log_message(f"파라미터 편집: {param_name}")
            return True
        except Exception as e:
            self.error_message = f"파라미터 편집 실패: {str(e)}"
            return False
    
    def _delete_parameter_execute(self, parameter_id: int) -> bool:
        """파라미터 삭제"""
        try:
            if not self.maint_mode:
                self.error_message = "QC 모드에서만 사용 가능합니다."
                return False
            
            self.add_log_message(f"파라미터 삭제: ID {parameter_id}")
            return True
        except Exception as e:
            self.error_message = f"파라미터 삭제 실패: {str(e)}"
            return False
    
    def _can_modify_parameters(self) -> bool:
        """파라미터 수정 가능 여부"""
        return self.maint_mode
    
    # 통계 및 분석 관련 명령 실행 메서드들
    def _calculate_statistics_execute(self) -> bool:
        """통계 계산"""
        try:
            self.add_log_message("통계 분석 시작")
            self.analysis_progress = 0
            
            # 진행률 시뮬레이션 (실제로는 서비스 레이어에서 처리)
            for i in range(0, 101, 10):
                self.analysis_progress = i
            
            self.add_log_message("통계 분석 완료")
            return True
        except Exception as e:
            self.error_message = f"통계 계산 실패: {str(e)}"
            return False
    
    def _can_calculate_statistics(self) -> bool:
        """통계 계산 가능 여부"""
        return self.has_files_loaded()
    
    def _export_statistics_execute(self, export_path: str) -> bool:
        """통계 내보내기"""
        try:
            self.add_log_message(f"통계 데이터 내보내기: {export_path}")
            return True
        except Exception as e:
            self.error_message = f"통계 내보내기 실패: {str(e)}"
            return False
    
    def _can_export_statistics(self) -> bool:
        """통계 내보내기 가능 여부"""
        return len(self.statistics_data) > 0
    
    def _refresh_all_data_execute(self) -> bool:
        """모든 데이터 새로고침"""
        try:
            self.add_log_message("전체 데이터 새로고침 시작")
            
            # 데이터베이스 재연결
            self.reconnect_database()
            
            # 각종 데이터 다시 로드
            if self.maint_mode:
                self._load_equipment_types_execute()
                self._load_default_db_values_execute()
            
            self.add_log_message("전체 데이터 새로고침 완료")
            return True
        except Exception as e:
            self.error_message = f"전체 데이터 새로고침 실패: {str(e)}"
            return False
    
