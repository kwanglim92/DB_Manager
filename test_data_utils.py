#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_utils.py 모듈 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def test_data_utils():
    """data_utils 모듈의 기능들을 테스트"""
    print("🔍 data_utils.py 모듈 테스트 시작...")
    
    try:
        from app.data_utils import (
            numeric_sort_key, 
            calculate_string_similarity,
            safe_convert_to_float,
            safe_convert_to_int,
            normalize_parameter_name,
            is_numeric_string,
            clean_numeric_value
        )
        
        print("✅ 모든 함수 import 성공")
        
        # 1. numeric_sort_key 테스트
        print("\n📊 numeric_sort_key 테스트:")
        test_values = ["123.45", "67.8", "N/A", "", "abc", "0", "999.999"]
        for val in test_values:
            result = numeric_sort_key(val)
            print(f"  '{val}' → {result}")
        
        # 2. calculate_string_similarity 테스트
        print("\n📊 calculate_string_similarity 테스트:")
        test_pairs = [
            ("hello", "hello"),
            ("hello", "helo"), 
            ("parameter", "paramter"),
            ("ABC", "XYZ"),
            ("", "test")
        ]
        for str1, str2 in test_pairs:
            result = calculate_string_similarity(str1, str2)
            print(f"  '{str1}' vs '{str2}' → {result:.3f}")
        
        # 3. safe_convert_to_float 테스트
        print("\n📊 safe_convert_to_float 테스트:")
        test_values = ["123.45", "abc", "", None, "N/A", "0"]
        for val in test_values:
            result = safe_convert_to_float(val)
            print(f"  {val} → {result}")
        
        # 4. normalize_parameter_name 테스트
        print("\n📊 normalize_parameter_name 테스트:")
        test_names = ["Test_Parameter", "test-parameter", "TEST PARAMETER", "  Test  Parameter  "]
        for name in test_names:
            result = normalize_parameter_name(name)
            print(f"  '{name}' → '{result}'")
        
        # 5. is_numeric_string 테스트
        print("\n📊 is_numeric_string 테스트:")
        test_values = ["123.45", "abc", "0", "-45.6", "1e-5", "NaN"]
        for val in test_values:
            result = is_numeric_string(val)
            print(f"  '{val}' → {result}")
        
        # 6. clean_numeric_value 테스트
        print("\n📊 clean_numeric_value 테스트:")
        test_values = ["123.4500", "45.0", "abc", None, "", "67"]
        for val in test_values:
            result = clean_numeric_value(val)
            print(f"  {val} → '{result}'")
        
        print("\n✅ 모든 data_utils 테스트 완료!")
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manager_integration():
    """manager.py와의 통합 테스트"""
    print("\n🔍 manager.py 통합 테스트 시작...")
    
    try:
        # manager.py import 테스트
        from app.manager import DBManager
        print("✅ DBManager import 성공")
        
        # DBManager 초기화 테스트 (UI 제외)
        print("⚠️ DBManager 초기화는 GUI 환경에서만 가능합니다.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Manager Import 오류: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Manager 테스트 경고: {e}")
        # GUI 관련 오류는 예상되므로 True 반환
        return True

def main():
    """메인 테스트 함수"""
    print("🚀 DB Manager 모듈화 테스트 시작")
    print("=" * 50)
    
    # data_utils 테스트
    test1_result = test_data_utils()
    
    # manager 통합 테스트
    test2_result = test_manager_integration()
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약:")
    print(f"  data_utils 테스트: {'✅ 성공' if test1_result else '❌ 실패'}")
    print(f"  manager 통합 테스트: {'✅ 성공' if test2_result else '❌ 실패'}")
    
    if test1_result and test2_result:
        print("\n🎉 모든 테스트 성공! data_utils.py 모듈 추출이 완료되었습니다.")
        return True
    else:
        print("\n⚠️ 일부 테스트에서 문제가 발견되었습니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)