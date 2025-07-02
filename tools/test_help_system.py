#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모듈화된 도움말 시스템 테스트 (새로운 HelpDataService 구조)

새로 구현된 도움말 시스템이 올바르게 작동하는지 테스트합니다.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import logging

# 프로젝트 루트를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def test_help_system_import():
    """도움말 시스템 import 테스트"""
    print("🔍 도움말 시스템 import 테스트...")
    
    try:
        from app.help_system import AppInfo, RevisionInfo, HelpDataService, HelpUIManager
        from app.help_system.utils.help_utils import create_db_manager_help_system
        print("✅ 모든 모듈 import 성공")
        return True
    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        return False

def test_basic_functionality():
    """기본 기능 테스트"""
    print("\n🔍 기본 기능 테스트...")
    
    try:
        from app.help_system.core.app_info import AppInfo, RevisionInfo, AppInfoManager
        from app.help_system.core.help_service import HelpDataService
        
        # 애플리케이션 정보 생성
        app_info = AppInfo(
            name="테스트 앱",
            version="1.0.0",
            release_date="2025-07-02",
            developer="테스트 개발자",
            organization="테스트 조직",
            contact="test@example.com",
            description="테스트용 애플리케이션입니다."
        )
        
        revision = RevisionInfo(
            version="1.0.0",
            date="2025-07-02",
            summary="초기 릴리스",
            details={"New Features": ["기본 기능 구현"]}
        )
        
        app_info_manager = AppInfoManager(app_info, [revision])
        
        # 도움말 데이터 서비스 생성
        help_data_service = HelpDataService()
        
        print("✅ 기본 객체 생성 성공")
        
        # 가이드 텍스트 생성 테스트
        guide_text = help_data_service.generate_user_guide_text()
        assert len(guide_text) > 0
        print("✅ 가이드 텍스트 생성 성공")
        
        # 앱 정보 포맷팅 테스트
        formatted_info = app_info_manager.get_formatted_app_info()
        assert "테스트 앱" in formatted_info
        print("✅ 앱 정보 포맷팅 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ 기본 기능 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_db_manager_integration():
    """DB Manager 통합 테스트"""
    print("\n🔍 DB Manager 통합 테스트...")
    
    try:
        from app.help_system.core.app_info import create_db_manager_app_info
        from app.help_system.core.help_service import create_db_manager_help_service
        
        # DB Manager 전용 컴포넌트 생성
        app_info_manager = create_db_manager_app_info()
        help_data_service = create_db_manager_help_service()
        
        # 검증
        assert app_info_manager.app_info.name == "DB Manager"
        assert len(app_info_manager.revisions) > 0
        
        # HelpDataService 검증
        guide_data = help_data_service.get_user_guide_data()
        assert len(guide_data.shortcuts) > 0
        assert len(guide_data.features) > 0
        assert len(guide_data.faqs) > 0
        
        print("✅ DB Manager 전용 컴포넌트 생성 성공")
        print(f"  📋 리비전 수: {len(app_info_manager.revisions)}")
        print(f"  ⌨️ 단축키 수: {len(guide_data.shortcuts)}")
        print(f"  🎯 기능 수: {len(guide_data.features)}")
        print(f"  ❓ FAQ 수: {len(guide_data.faqs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ DB Manager 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_manager_integration():
    """ConfigManager 통합 테스트"""
    print("\n🔍 ConfigManager 통합 테스트...")
    
    try:
        from app.config_manager import show_about, show_user_guide
        from app.config_manager import HELP_SYSTEM_AVAILABLE
        
        print(f"📊 도움말 시스템 사용 가능: {HELP_SYSTEM_AVAILABLE}")
        
        # 함수 호출 가능성 확인 (실제 GUI 생성하지 않음)
        assert callable(show_about)
        assert callable(show_user_guide)
        
        print("✅ ConfigManager 통합 함수 확인 성공")
        
        # show_troubleshooting_guide가 제거되었는지 확인
        try:
            from app.config_manager import show_troubleshooting_guide
            print("❌ show_troubleshooting_guide가 아직 존재합니다")
            return False
        except ImportError:
            print("✅ show_troubleshooting_guide 제거 확인")
            
        return True
        
    except Exception as e:
        print(f"❌ ConfigManager 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_components():
    """UI 컴포넌트 테스트 (실제 창 생성 없이)"""
    print("\n🔍 UI 컴포넌트 테스트...")
    
    try:
        from app.help_system.ui.dialogs import AboutDialog, UserGuideDialog
        from app.help_system.ui.help_manager import HelpUIManager
        
        print("✅ UI 컴포넌트 import 성공")
        
        # 클래스 존재 확인
        assert AboutDialog is not None
        assert UserGuideDialog is not None
        assert HelpUIManager is not None
        
        print("✅ 필요한 UI 컴포넌트 클래스 확인 성공")
        
        # TroubleshootingDialog가 제거되었는지 확인
        try:
            from app.help_system.ui.dialogs import TroubleshootingDialog
            print("❌ TroubleshootingDialog가 아직 존재합니다")
            return False
        except ImportError:
            print("✅ TroubleshootingDialog 제거 확인")
            
        return True
        
    except Exception as e:
        print(f"❌ UI 컴포넌트 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_help_system_creation():
    """도움말 시스템 생성 테스트"""
    print("\n🔍 도움말 시스템 생성 테스트...")
    
    # 더미 윈도우 생성 (표시하지 않음)
    root = tk.Tk()
    root.withdraw()  # 창 숨기기
    
    try:
        from app.help_system.utils.help_utils import create_db_manager_help_system
        
        help_manager = create_db_manager_help_system(parent_window=root)
        
        assert help_manager is not None
        assert help_manager.help_data_service is not None
        assert help_manager.app_info_manager is not None
        
        # 기본 메서드 존재 확인
        assert hasattr(help_manager, 'show_about_dialog')
        assert hasattr(help_manager, 'show_user_guide')
        
        print("✅ 도움말 시스템 생성 테스트 성공")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ 도움말 시스템 생성 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        
        root.destroy()
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 모듈화된 도움말 시스템 테스트 시작 (새로운 HelpDataService 구조)")
    print("=" * 70)
    
    # 로깅 설정
    logging.basicConfig(level=logging.WARNING)  # 테스트 중 로그 노이즈 줄이기
    
    tests = [
        ("Import 테스트", test_help_system_import),
        ("기본 기능 테스트", test_basic_functionality),
        ("DB Manager 통합 테스트", test_db_manager_integration),
        ("ConfigManager 통합 테스트", test_config_manager_integration),
        ("UI 컴포넌트 테스트", test_ui_components),
        ("도움말 시스템 생성 테스트", test_help_system_creation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 중 예외 발생: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("📊 테스트 결과 요약")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{status} {test_name}")
    
    print("=" * 70)
    print(f"전체 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("\n🎉 모든 테스트가 성공적으로 통과했습니다!")
        print("\n📋 구현 완료된 기능:")
        print("  ✅ HelpDataService 패턴 구현")
        print("  ✅ 사용자 제공 코드와 동일한 구조")
        print("  ✅ 서비스 기반 아키텍처")
        print("  ✅ 기존 시스템과의 호환성")
        print("  ✅ DB Manager 전용 콘텐츠")
        return True
    else:
        print(f"\n⚠️ {total - passed}개의 테스트가 실패했습니다.")
        print("🔧 추가 확인이 필요합니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)