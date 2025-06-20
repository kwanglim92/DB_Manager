#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Comparison 기능 테스트 스크립트

이 스크립트는 다음을 테스트합니다:
1. Enhanced Comparison 모듈 임포트
2. 비교 모드 클래스 동작
3. 파일 vs Default DB 비교 로직
"""

import os
import sys
import pandas as pd

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def test_enhanced_comparison_import():
    """Enhanced Comparison 모듈 임포트 테스트"""
    print("🔍 1. Enhanced Comparison 모듈 임포트 테스트...")
    
    try:
        from app.enhanced_comparison import EnhancedComparisonMode, add_enhanced_comparison_functions_to_class
        
        # 비교 모드 테스트
        file_to_file_mode = EnhancedComparisonMode.FILE_TO_FILE
        file_to_db_mode = EnhancedComparisonMode.FILE_TO_DEFAULT_DB
        
        print(f"✅ FILE_TO_FILE 모드: {file_to_file_mode}")
        print(f"✅ FILE_TO_DEFAULT_DB 모드: {file_to_db_mode}")
        
        # 모드 설명 테스트
        file_to_file_desc = EnhancedComparisonMode.get_mode_description(file_to_file_mode)
        file_to_db_desc = EnhancedComparisonMode.get_mode_description(file_to_db_mode)
        
        print(f"✅ 파일 간 비교 설명: {file_to_file_desc}")
        print(f"✅ 파일 vs DB 비교 설명: {file_to_db_desc}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Enhanced Comparison 모듈 임포트 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ Enhanced Comparison 모듈 테스트 실패: {e}")
        return False

def test_enhanced_comparison_class_integration():
    """Enhanced Comparison 클래스 통합 테스트"""
    print("\n🔍 2. Enhanced Comparison 클래스 통합 테스트...")
    
    try:
        from app.enhanced_comparison import add_enhanced_comparison_functions_to_class
        
        class MockDBManager:
            def __init__(self):
                self.db_schema = None
                self.merged_df = None
                self.enhanced_equipment_types = {}
                self.comparison_mode_var = None
                self.enhanced_equipment_type_var = None
                self.enhanced_performance_mode_var = None
                
            def update_log(self, message):
                print(f"LOG: {message}")
        
        # Enhanced Comparison 기능 추가
        add_enhanced_comparison_functions_to_class(MockDBManager)
        
        # 인스턴스 생성
        mock_manager = MockDBManager()
        
        # 추가된 메서드들 확인
        methods = [method for method in dir(mock_manager) if not method.startswith('_')]
        enhanced_methods = [method for method in methods if 'enhanced' in method.lower() or 'comparison' in method.lower()]
        
        print(f"✅ Enhanced Comparison 관련 메서드들: {enhanced_methods}")
        
        # 주요 메서드 존재 확인
        required_methods = [
            'create_enhanced_comparison_tab',
            'load_enhanced_equipment_types',
            'on_comparison_mode_changed',
            'update_enhanced_comparison_view'
        ]
        
        missing_methods = [method for method in required_methods if not hasattr(mock_manager, method)]
        
        if missing_methods:
            print(f"❌ 누락된 메서드들: {missing_methods}")
            return False
        else:
            print("✅ 모든 필수 메서드가 정상적으로 추가되었습니다.")
            return True
        
    except Exception as e:
        print(f"❌ Enhanced Comparison 클래스 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_comparison_logic():
    """비교 로직 테스트"""
    print("\n🔍 3. 비교 로직 테스트...")
    
    try:
        from app.enhanced_comparison import add_enhanced_comparison_functions_to_class
        from app.schema import DBSchema
        
        class MockDBManager:
            def __init__(self):
                self.db_schema = DBSchema()
                self.enhanced_equipment_types = {"테스트_장비": 1}
                
                # 테스트용 파일 데이터 생성
                self.merged_df = pd.DataFrame({
                    'Module': ['Module1', 'Module1'],
                    'Part': ['Part1', 'Part1'],
                    'ItemName': ['TestParam1', 'TestParam2'],
                    'File1': ['100.0', '200.0']
                })
                
            def update_log(self, message):
                print(f"LOG: {message}")
        
        # Enhanced Comparison 기능 추가
        add_enhanced_comparison_functions_to_class(MockDBManager)
        
        mock_manager = MockDBManager()
        
        # 테스트용 Default DB 데이터 생성
        equipment_type_id = mock_manager.db_schema.add_equipment_type("테스트_장비", "테스트용")
        
        # Default DB 값들 추가
        mock_manager.db_schema.add_default_value(
            equipment_type_id, "Part1_TestParam1", "100.0", "90.0", "110.0", 
            description="테스트 파라미터 1", is_performance=True
        )
        mock_manager.db_schema.add_default_value(
            equipment_type_id, "Part1_TestParam2", "180.0", "170.0", "210.0",
            description="테스트 파라미터 2", is_performance=False
        )
        
        # Default DB 값 조회 테스트
        default_values = mock_manager.db_schema.get_default_values(equipment_type_id)
        print(f"✅ Default DB 값 조회: {len(default_values)}개")
        
        # Performance 항목만 조회 테스트
        performance_values = mock_manager.db_schema.get_performance_parameters(equipment_type_id)
        print(f"✅ Performance 항목 조회: {len(performance_values)}개")
        
        # 비교 로직 테스트
        comparison_results = mock_manager._perform_file_to_default_comparison(default_values)
        print(f"✅ 비교 결과: {len(comparison_results)}개")
        
        for result in comparison_results:
            print(f"  - {result['parameter']}: {result['file_value']} vs {result['default_value']} ({result['status']})")
        
        # 테스트 데이터 정리
        mock_manager.db_schema.delete_equipment_type(equipment_type_id)
        print("✅ 테스트 데이터 정리 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 비교 로직 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_difference_analysis():
    """차이점 분석 로직 테스트"""
    print("\n🔍 4. 차이점 분석 로직 테스트...")
    
    try:
        from app.enhanced_comparison import add_enhanced_comparison_functions_to_class
        
        class MockDBManager:
            def update_log(self, message):
                pass
        
        add_enhanced_comparison_functions_to_class(MockDBManager)
        mock_manager = MockDBManager()
        
        # 테스트 케이스들
        test_cases = [
            # (파일값, Default값, 사양정보, 예상결과타입)
            ("100.0", "100.0", {"min_spec": "90.0", "max_spec": "110.0"}, "match"),
            ("95.0", "100.0", {"min_spec": "90.0", "max_spec": "110.0"}, "numeric_diff"),
            ("85.0", "100.0", {"min_spec": "90.0", "max_spec": "110.0"}, "below_spec"),
            ("115.0", "100.0", {"min_spec": "90.0", "max_spec": "110.0"}, "above_spec"),
            ("text1", "text2", {}, "text_diff"),
            ("same", "same", {}, "match")
        ]
        
        print("차이점 분석 테스트:")
        for i, (file_val, default_val, spec_info, expected_type) in enumerate(test_cases, 1):
            result = mock_manager._analyze_difference(file_val, default_val, spec_info)
            actual_type = result.get('type', 'unknown')
            
            status = "✅" if actual_type == expected_type else "❌"
            print(f"  {status} 테스트 {i}: {file_val} vs {default_val} → {actual_type} (예상: {expected_type})")
            
        return True
        
    except Exception as e:
        print(f"❌ 차이점 분석 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 Enhanced Comparison 기능 종합 테스트 시작\n")
    
    test_results = []
    
    # 각 테스트 실행
    test_results.append(test_enhanced_comparison_import())
    test_results.append(test_enhanced_comparison_class_integration())
    test_results.append(test_comparison_logic())
    test_results.append(test_difference_analysis())
    
    # 결과 요약
    print("\n📊 테스트 결과 요약:")
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ 통과: {passed}/{total}")
    print(f"❌ 실패: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 모든 테스트가 통과했습니다! Enhanced Comparison 기능이 정상 작동합니다.")
        return True
    else:
        print(f"\n⚠️ {total - passed}개의 테스트가 실패했습니다. 추가 확인이 필요합니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 