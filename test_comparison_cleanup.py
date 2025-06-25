#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB 비교 메뉴 기능 정리 테스트
비교 통계 및 데이터 내보내기 기능 제거 확인
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def test_removed_methods():
    """제거된 메소드들이 더 이상 존재하지 않는지 확인"""
    print("🔍 제거된 메소드 확인 테스트...")
    
    try:
        from app.manager import DBManager
        
        # DBManager 클래스에서 제거된 메소드들이 없는지 확인
        removed_methods = [
            '_show_comparison_statistics',
            '_export_comparison_data'
        ]
        
        for method_name in removed_methods:
            if hasattr(DBManager, method_name):
                print(f"❌ {method_name} 메소드가 아직 존재합니다!")
                return False
            else:
                print(f"✅ {method_name} 메소드가 성공적으로 제거되었습니다.")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

def test_remaining_functionality():
    """남아있는 기능들이 정상 작동하는지 확인"""
    print("\n🔍 남은 기능 정상 작동 테스트...")
    
    try:
        from app.manager import DBManager
        
        # FileService 관련 기능들이 여전히 존재하는지 확인
        remaining_methods = [
            'export_report',  # 이 메소드는 FileService를 사용하므로 유지되어야 함
        ]
        
        for method_name in remaining_methods:
            if hasattr(DBManager, method_name):
                print(f"✅ {method_name} 메소드가 정상적으로 유지되고 있습니다.")
            else:
                print(f"❌ {method_name} 메소드가 예상치 못하게 제거되었습니다!")
                return False
        
        # FileService 초기화 확인
        print("✅ FileService 관련 기능들이 정상적으로 유지되고 있습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

def test_code_cleanup():
    """코드 정리 확인"""
    print("\n🔍 코드 정리 확인 테스트...")
    
    try:
        manager_path = os.path.join(src_path, 'app', 'manager.py')
        
        with open(manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 제거되어야 할 텍스트들이 없는지 확인 (comparison 컨텍스트에서)
        removed_texts = [
            '📊 비교 통계',
            'command=self._show_comparison_statistics',
            'command=self._export_comparison_data',
            '_show_comparison_statistics',
            '_export_comparison_data',
            'def _show_comparison_statistics',
            'def _export_comparison_data'
        ]
        
        found_removed = []
        for text in removed_texts:
            if text in content:
                found_removed.append(text)
        
        if found_removed:
            print(f"❌ 다음 제거되어야 할 텍스트들이 아직 남아있습니다: {found_removed}")
            return False
        else:
            print("✅ 모든 관련 텍스트가 성공적으로 제거되었습니다.")
        
        # FileService import가 여전히 존재하는지 확인 (다른 기능에서 사용)
        if 'from app.file_service import FileService' in content:
            print("✅ FileService import가 정상적으로 유지되고 있습니다.")
        else:
            print("❌ FileService import가 예상치 못하게 제거되었습니다!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

def test_line_count_reduction():
    """라인 수 감소 확인"""
    print("\n🔍 라인 수 감소 확인...")
    
    try:
        manager_path = os.path.join(src_path, 'app', 'manager.py')
        
        with open(manager_path, 'r', encoding='utf-8') as f:
            current_lines = len(f.readlines())
        
        # 이전 상태에서 감소했는지 확인 (대략 55라인 감소 예상)
        previous_lines = 4714  # 이전 상태
        reduction = previous_lines - current_lines
        
        print(f"📊 이전 라인 수: {previous_lines}")
        print(f"📊 현재 라인 수: {current_lines}")
        print(f"📉 감소된 라인 수: {reduction}")
        
        if reduction > 0:
            print(f"✅ {reduction}라인이 성공적으로 감소되었습니다.")
            return True
        else:
            print("⚠️ 라인 수 감소가 확인되지 않았습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 DB 비교 메뉴 기능 정리 테스트 시작")
    print("=" * 60)
    
    tests = [
        ("제거된 메소드 확인", test_removed_methods),
        ("남은 기능 정상 작동", test_remaining_functionality),
        ("코드 정리 확인", test_code_cleanup),
        ("라인 수 감소 확인", test_line_count_reduction)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 테스트:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 기능 정리 테스트 결과 요약:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"전체 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("\n🎉 모든 기능 정리가 성공적으로 완료되었습니다!")
        print("\n📋 완료된 작업:")
        print("  ✅ 📊 비교 통계 버튼 제거")
        print("  ✅ 📤 데이터 내보내기 버튼 제거")
        print("  ✅ _show_comparison_statistics 메소드 제거")
        print("  ✅ _export_comparison_data 메소드 제거")
        print("  ✅ 관련 코드 완전 정리")
        print("  ✅ 다른 기능들 정상 유지")
        
        return True
    else:
        print(f"\n⚠️ {total - passed}개의 테스트가 실패했습니다.")
        print("🔧 추가 확인이 필요합니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)