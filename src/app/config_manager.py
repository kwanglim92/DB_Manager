# 설정 및 구성 관리 모듈
# manager.py에서 추출된 설정 관련 기능들

import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog

def show_about():
    """프로그램 정보 다이얼로그 표시"""
    messagebox.showinfo(
        "프로그램 정보",
        "DB Manager\n버전: 1.0.1\n제작자: kwanglim92\n\n이 프로그램은 DB 파일 비교, 관리, 보고서 생성 등 다양한 기능을 제공합니다."
    )

def show_user_guide(event=None):
    """사용자 가이드 다이얼로그 표시"""
    guide_text = (
        "[DB Manager 사용자 가이드]\n\n"
        "• 폴더 열기: 파일 > 폴더 열기 (Ctrl+O)\n"
        "• DB 비교: 여러 DB 파일을 불러와 값 차이, 격자 뷰, 보고서 등 다양한 탭에서 확인\n"
        "• 유지보수 모드: 도구 > Maintenance Mode (비밀번호 필요)\n"
        "• Default DB 관리, QC 검수 등은 유지보수 모드에서만 사용 가능\n"
        "• 각 탭에서 우클릭 및 버튼으로 항목 추가/삭제/내보내기 등 다양한 작업 지원\n"
        "• 문의: github.com/kwanglim92/DB_Manager\n\n"
        "= 사용자 역할 =\n"
        "• 장비 생산 엔지니어: DB 비교 기능 사용\n"
        "• QC 엔지니어: Maintenance Mode로 모든 기능 사용"
    )
    messagebox.showinfo("사용 설명서", guide_text)

def setup_service_layer(db_schema, update_log_callback=None):
    """
    새로운 서비스 레이어 초기화
    
    Args:
        db_schema: 데이터베이스 스키마 객체
        update_log_callback: 로그 업데이트를 위한 콜백 함수
        
    Returns:
        tuple: (service_factory, legacy_adapter, use_new_services)
    """
    service_factory = None
    legacy_adapter = None
    use_new_services = {}
    
    # 서비스 시스템 가용성 확인
    try:
        from app.services import ServiceFactory, LegacyAdapter, SERVICES_AVAILABLE
        USE_NEW_SERVICES = True
    except ImportError:
        USE_NEW_SERVICES = False
        SERVICES_AVAILABLE = False
    
    if not USE_NEW_SERVICES or not SERVICES_AVAILABLE:
        # 새로운 서비스 시스템이 아직 구현되지 않았으므로 기존 방식 사용 (정상 동작)
        return service_factory, legacy_adapter, use_new_services
    
    try:
        # 설정 파일에서 서비스 사용 설정 로드
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            "config", "settings.json"
        )
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                use_new_services = settings.get('use_new_services', {})
                service_config = settings.get('service_config', {})
        else:
            use_new_services = {'equipment_service': False}
            service_config = {}
        
        # 서비스 팩토리 초기화
        if db_schema:
            service_factory = ServiceFactory(db_schema, service_config)
            legacy_adapter = LegacyAdapter(service_factory)
            
            # 서비스 상태 로깅
            status = service_factory.get_service_status()
            if update_log_callback:
                update_log_callback(f"서비스 레이어 초기화 완료: {len(status)}개 서비스 등록")
            
            # 활성 서비스들 확인
            active_services = [k for k, v in use_new_services.items() if v]
            if active_services and update_log_callback:
                update_log_callback(f"활성 서비스: {', '.join(active_services)}")
        else:
            if update_log_callback:
                update_log_callback("DB 스키마가 없어 서비스 팩토리를 초기화할 수 없습니다")
                
    except Exception as e:
        if update_log_callback:
            update_log_callback(f"서비스 레이어 초기화 실패: {str(e)}")
        print(f"Service layer initialization failed: {str(e)}")
    
    return service_factory, legacy_adapter, use_new_services

def should_use_service(service_name, service_factory, use_new_services):
    """
    특정 서비스 사용 여부 확인
    
    Args:
        service_name: 확인할 서비스 이름
        service_factory: 서비스 팩토리 객체
        use_new_services: 서비스 사용 설정 딕셔너리
        
    Returns:
        bool: 서비스 사용 가능 여부
    """
    try:
        from app.services import SERVICES_AVAILABLE
        USE_NEW_SERVICES = True
    except ImportError:
        USE_NEW_SERVICES = False
        SERVICES_AVAILABLE = False
    
    return (USE_NEW_SERVICES and 
            SERVICES_AVAILABLE and 
            service_factory is not None and
            use_new_services.get(service_name, False))

class ConfigManager:
    """설정 관리 클래스 - 상태 유지가 필요한 경우 사용"""
    
    def __init__(self, config=None, db_schema=None, update_log_callback=None):
        self.config = config
        self.db_schema = db_schema
        self.update_log_callback = update_log_callback
        
        # 서비스 레이어 초기화
        self.service_factory, self.legacy_adapter, self.use_new_services = setup_service_layer(
            db_schema, update_log_callback
        )
    
    def show_about(self):
        """프로그램 정보 다이얼로그 표시"""
        return show_about()

    def show_user_guide(self, event=None):
        """사용자 가이드 다이얼로그 표시"""
        return show_user_guide(event)

    def should_use_service(self, service_name):
        """특정 서비스 사용 여부 확인"""
        return should_use_service(service_name, self.service_factory, self.use_new_services)