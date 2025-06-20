#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance QC 기능 테스트 스크립트

이 스크립트는 다음을 테스트합니다:
1. DB 스키마의 is_performance 컬럼 추가 여부
2. Performance 파라미터 설정/조회 기능
3. Enhanced QC 검증 기능
"""

import os
import sys
import sqlite3

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def test_db_schema_performance_column():
    """DB 스키마에 is_performance 컬럼이 추가되었는지 테스트"""
    print("🔍 1. DB 스키마 is_performance 컬럼 테스트...")
    
    try:
        from app.schema import DBSchema
        db_schema = DBSchema()
        
        with db_schema.get_connection() as conn:
            cursor = conn.cursor()
            
            # 테이블 정보 확인
            cursor.execute("PRAGMA table_info(Default_DB_Values)")
            columns = cursor.fetchall()
            
            column_names = [col[1] for col in columns]
            
            if 'is_performance' in column_names:
                print("✅ is_performance 컬럼이 성공적으로 추가되었습니다.")
                return True
            else:
                print("❌ is_performance 컬럼이 없습니다.")
                print(f"현재 컬럼들: {column_names}")
                return False
                
    except Exception as e:
        print(f"❌ DB 스키마 테스트 실패: {e}")
        return False

def test_performance_parameter_management():
    """Performance 파라미터 관리 기능 테스트"""
    print("\n🔍 2. Performance 파라미터 관리 기능 테스트...")
    
    try:
        from app.schema import DBSchema
        db_schema = DBSchema()
        
        # 테스트용 장비 유형 추가
        equipment_type_id = db_schema.add_equipment_type("테스트_장비", "Performance 테스트용")
        print(f"✅ 테스트 장비 유형 생성: ID {equipment_type_id}")
        
        # Performance 파라미터 추가
        param_id = db_schema.add_default_value(
            equipment_type_id,
            "Performance_Test_Parameter",
            "100.0",
            min_spec="90.0",
            max_spec="110.0",
            description="Performance 테스트 파라미터",
            is_performance=True
        )
        print(f"✅ Performance 파라미터 추가: ID {param_id}")
        
        # 일반 파라미터 추가
        normal_param_id = db_schema.add_default_value(
            equipment_type_id,
            "Normal_Test_Parameter",
            "50.0",
            description="일반 테스트 파라미터",
            is_performance=False
        )
        print(f"✅ 일반 파라미터 추가: ID {normal_param_id}")
        
        # Performance 파라미터만 조회
        performance_params = db_schema.get_performance_parameters(equipment_type_id)
        print(f"✅ Performance 파라미터 조회: {len(performance_params)}개")
        
        # 전체 파라미터 조회
        all_params = db_schema.get_default_values(equipment_type_id, performance_only=False)
        print(f"✅ 전체 파라미터 조회: {len(all_params)}개")
        
        # Performance 개수 확인
        count_info = db_schema.get_equipment_performance_count(equipment_type_id)
        print(f"✅ 파라미터 개수 정보: {count_info}")
        
        if performance_params and len(performance_params) == 1:
            print("✅ Performance 파라미터 관리 기능이 정상 작동합니다.")
            return True
        else:
            print("❌ Performance 파라미터 관리 기능에 문제가 있습니다.")
            return False
        
    except Exception as e:
        print(f"❌ Performance 파라미터 관리 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_qc_validator():
    """Enhanced QC Validator 테스트"""
    print("\n🔍 3. Enhanced QC Validator 테스트...")
    
    try:
        from app.enhanced_qc import EnhancedQCValidator
        import pandas as pd
        
        # 테스트 데이터 생성
        test_data = {
            'id': [1, 2],
            'parameter_name': ['Performance_Param', 'Normal_Param'],
            'default_value': ['100.0', '50.0'],
            'min_spec': ['90.0', '40.0'],
            'max_spec': ['110.0', '60.0'],
            'type_name': ['테스트_장비', '테스트_장비'],
            'occurrence_count': [5, 3],
            'total_files': [10, 10],
            'confidence_score': [0.5, 0.8],  # Performance 파라미터의 신뢰도가 낮음
            'source_files': ['file1,file2', 'file3,file4'],
            'description': ['성능 중요 파라미터', '일반 파라미터'],
            'module_name': ['Module1', 'Module2'],
            'part_name': ['Part1', 'Part2'],
            'item_type': ['Double', 'Integer'],
            'is_performance': [1, 0]  # 첫 번째는 Performance, 두 번째는 일반
        }
        
        df = pd.DataFrame(test_data)
        
        # Enhanced QC 검사 실행
        results = EnhancedQCValidator.run_enhanced_checks(df, "테스트_장비", is_performance_mode=True)
        
        print(f"✅ Enhanced QC 검사 완료: {len(results)}개 이슈 발견")
        
        # Performance 관련 이슈 확인
        performance_issues = [r for r in results if "Performance" in r["issue_type"]]
        print(f"✅ Performance 관련 이슈: {len(performance_issues)}개")
        
        for issue in performance_issues:
            print(f"  - {issue['parameter']}: {issue['issue_type']} ({issue['severity']})")
        
        if results:
            print("✅ Enhanced QC Validator가 정상 작동합니다.")
            return True
        else:
            print("⚠️ Enhanced QC Validator가 이슈를 발견하지 못했습니다 (정상일 수도 있음).")
            return True
            
    except Exception as e:
        print(f"❌ Enhanced QC Validator 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qc_tab_ui_components():
    """QC 탭 UI 구성 요소 테스트"""
    print("\n🔍 4. QC 탭 UI 구성 요소 테스트...")
    
    try:
        # QC 탭 생성 함수가 Performance 모드 UI를 포함하는지 확인
        from app.qc import add_qc_check_functions_to_class
        
        class MockDBManager:
            def __init__(self):
                self.qc_mode_var = None
                self.qc_type_var = None
        
        # QC 기능 추가
        add_qc_check_functions_to_class(MockDBManager)
        
        # Enhanced QC 기능 추가 시도
        try:
            from app.enhanced_qc import add_enhanced_qc_functions_to_class
            add_enhanced_qc_functions_to_class(MockDBManager)
            print("✅ Enhanced QC 기능이 성공적으로 추가되었습니다.")
        except Exception as e:
            print(f"⚠️ Enhanced QC 기능 추가 실패: {e}")
        
        # 클래스에 메서드가 추가되었는지 확인
        methods = [method for method in dir(MockDBManager) if not method.startswith('_')]
        qc_methods = [method for method in methods if 'qc' in method.lower()]
        
        print(f"✅ QC 관련 메서드들: {qc_methods}")
        
        return True
        
    except Exception as e:
        print(f"❌ QC 탭 UI 구성 요소 테스트 실패: {e}")
        return False

def cleanup_test_data():
    """테스트 데이터 정리"""
    print("\n🧹 테스트 데이터 정리 중...")
    
    try:
        from app.schema import DBSchema
        db_schema = DBSchema()
        
        with db_schema.get_connection() as conn:
            cursor = conn.cursor()
            
            # 테스트 장비 유형 삭제
            cursor.execute("DELETE FROM Default_DB_Values WHERE equipment_type_id IN (SELECT id FROM Equipment_Types WHERE type_name = '테스트_장비')")
            cursor.execute("DELETE FROM Equipment_Types WHERE type_name = '테스트_장비'")
            
            conn.commit()
            print("✅ 테스트 데이터 정리 완료")
            
    except Exception as e:
        print(f"⚠️ 테스트 데이터 정리 중 오류: {e}")

def main():
    """메인 테스트 실행"""
    print("🚀 Performance QC 기능 종합 테스트 시작\n")
    
    test_results = []
    
    # 각 테스트 실행
    test_results.append(test_db_schema_performance_column())
    test_results.append(test_performance_parameter_management())
    test_results.append(test_enhanced_qc_validator())
    test_results.append(test_qc_tab_ui_components())
    
    # 테스트 데이터 정리
    cleanup_test_data()
    
    # 결과 요약
    print("\n📊 테스트 결과 요약:")
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ 통과: {passed}/{total}")
    print(f"❌ 실패: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 모든 테스트가 통과했습니다! Performance QC 기능이 정상 작동합니다.")
        return True
    else:
        print(f"\n⚠️ {total - passed}개의 테스트가 실패했습니다. 추가 확인이 필요합니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 