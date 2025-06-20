#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB Manager 전체 통합 테스트 스크립트

이 스크립트는 다음 기능들의 통합을 테스트합니다:
1. Phase 1: DB 스키마 확장 (is_performance 컬럼)
2. Phase 2: QC 검수 탭 개선 (Performance 모드)
3. Phase 3: DB 비교 탭 확장 (Default DB 비교)
4. 전체 시스템 통합 및 호환성
"""

import os
import sys
import pandas as pd
import tempfile

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def test_phase1_db_schema_integration():
    """Phase 1: DB 스키마 확장 통합 테스트"""
    print("🔍 Phase 1: DB 스키마 확장 통합 테스트...")
    
    try:
        from app.schema import DBSchema
        
        # DB 스키마 초기화
        db_schema = DBSchema()
        
        # 장비 유형 추가
        equipment_type_id = db_schema.add_equipment_type("통합테스트_장비", "전체 통합 테스트용")
        
        # Performance 파라미터 추가
        perf_param_id = db_schema.add_default_value(
            equipment_type_id, "Performance_Critical_Param", "100.0",
            min_spec="90.0", max_spec="110.0",
            description="성능 중요 파라미터", is_performance=True
        )
        
        # 일반 파라미터 추가
        normal_param_id = db_schema.add_default_value(
            equipment_type_id, "Normal_Param", "50.0",
            description="일반 파라미터", is_performance=False
        )
        
        # Performance 항목 개수 확인
        count_info = db_schema.get_equipment_performance_count(equipment_type_id)
        
        if count_info['total'] == 2 and count_info['performance'] == 1:
            print("✅ Phase 1: DB 스키마 확장이 정상 작동합니다.")
            return True, equipment_type_id
        else:
            print(f"❌ Phase 1: 파라미터 개수 오류 - {count_info}")
            return False, None
            
    except Exception as e:
        print(f"❌ Phase 1 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_phase2_qc_enhancement_integration(equipment_type_id):
    """Phase 2: QC 검수 탭 개선 통합 테스트"""
    print("\n🔍 Phase 2: QC 검수 탭 개선 통합 테스트...")
    
    try:
        from app.enhanced_qc import EnhancedQCValidator, add_enhanced_qc_functions_to_class
        from app.schema import DBSchema
        import pandas as pd
        
        db_schema = DBSchema()
        
        # 테스트 데이터 로드
        all_params = db_schema.get_default_values(equipment_type_id, performance_only=False)
        performance_params = db_schema.get_default_values(equipment_type_id, performance_only=True)
        
        print(f"  📊 전체 파라미터: {len(all_params)}개")
        print(f"  📊 Performance 파라미터: {len(performance_params)}개")
        
        # DataFrame 생성
        if all_params:
            df_all = pd.DataFrame(all_params, columns=[
                "id", "parameter_name", "default_value", "min_spec", "max_spec", "type_name",
                "occurrence_count", "total_files", "confidence_score", "source_files", "description",
                "module_name", "part_name", "item_type", "is_performance"
            ])
            
            # Enhanced QC 검사 실행 (전체 모드)
            results_all = EnhancedQCValidator.run_enhanced_checks(df_all, "통합테스트_장비", False)
            print(f"  🔍 전체 모드 QC 검사: {len(results_all)}개 이슈")
            
            # Enhanced QC 검사 실행 (Performance 모드)
            results_perf = EnhancedQCValidator.run_enhanced_checks(df_all, "통합테스트_장비", True)
            print(f"  🔍 Performance 모드 QC 검사: {len(results_perf)}개 이슈")
            
            print("✅ Phase 2: QC 검수 탭 개선이 정상 작동합니다.")
            return True
        else:
            print("❌ Phase 2: 테스트 데이터가 없습니다.")
            return False
            
    except Exception as e:
        print(f"❌ Phase 2 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase3_comparison_enhancement_integration(equipment_type_id):
    """Phase 3: DB 비교 탭 확장 통합 테스트"""
    print("\n🔍 Phase 3: DB 비교 탭 확장 통합 테스트...")
    
    try:
        from app.enhanced_comparison import EnhancedComparisonMode, add_enhanced_comparison_functions_to_class
        from app.schema import DBSchema
        import pandas as pd
        
        # Mock 파일 데이터 생성
        mock_file_data = pd.DataFrame({
            'Module': ['Module1', 'Module1'],
            'Part': ['Part1', 'Part1'],
            'ItemName': ['Performance_Critical_Param', 'Normal_Param'],
            'TestFile': ['105.0', '55.0']  # Default와 다른 값들
        })
        
        class MockDBManager:
            def __init__(self, equipment_type_id):
                self.db_schema = DBSchema()
                self.enhanced_equipment_types = {"통합테스트_장비": equipment_type_id}
                self.merged_df = mock_file_data
                
            def update_log(self, message):
                print(f"    LOG: {message}")
        
        # Enhanced Comparison 기능 추가
        add_enhanced_comparison_functions_to_class(MockDBManager)
        
        mock_manager = MockDBManager(equipment_type_id)
        
        # Default DB 값 로드
        default_values = mock_manager.db_schema.get_default_values(equipment_type_id)
        print(f"  📊 Default DB 값: {len(default_values)}개")
        
        # 파일 vs Default DB 비교 실행
        comparison_results = mock_manager._perform_file_to_default_comparison(default_values)
        print(f"  🔍 비교 결과: {len(comparison_results)}개 항목")
        
        # 비교 결과 분석
        match_count = sum(1 for r in comparison_results if '✅' in r['status'])
        diff_count = len(comparison_results) - match_count
        
        print(f"    - 일치: {match_count}개")
        print(f"    - 차이: {diff_count}개")
        
        for result in comparison_results:
            print(f"    - {result['parameter']}: {result['file_value']} vs {result['default_value']} ({result['status']})")
        
        # Performance 모드 비교 테스트
        performance_values = mock_manager.db_schema.get_performance_parameters(equipment_type_id)
        performance_comparison = mock_manager._perform_file_to_default_comparison(performance_values)
        print(f"  🎯 Performance 모드 비교: {len(performance_comparison)}개 항목")
        
        print("✅ Phase 3: DB 비교 탭 확장이 정상 작동합니다.")
        return True
        
    except Exception as e:
        print(f"❌ Phase 3 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cross_functionality_integration(equipment_type_id):
    """기능 간 통합 테스트"""
    print("\n🔍 기능 간 통합 테스트...")
    
    try:
        from app.schema import DBSchema
        
        db_schema = DBSchema()
        
        # 1. DB 스키마에서 Performance 상태 변경
        all_values = db_schema.get_default_values(equipment_type_id)
        if all_values:
            # 첫 번째 파라미터의 Performance 상태 토글
            first_param_id = all_values[0][0]
            current_performance = all_values[0][14]  # is_performance 컬럼
            
            # Performance 상태 변경
            new_performance = not bool(current_performance)
            success = db_schema.set_performance_status(first_param_id, new_performance)
            
            if success:
                print(f"  ✅ Performance 상태 변경: {current_performance} → {new_performance}")
                
                # 변경 후 개수 재확인
                updated_count = db_schema.get_equipment_performance_count(equipment_type_id)
                print(f"  📊 업데이트된 Performance 개수: {updated_count}")
                
                # 원래 상태로 복구
                db_schema.set_performance_status(first_param_id, bool(current_performance))
                print("  🔄 원래 상태로 복구 완료")
                
            else:
                print("  ❌ Performance 상태 변경 실패")
                return False
        
        # 2. QC와 Comparison 연동 테스트
        performance_values = db_schema.get_performance_parameters(equipment_type_id)
        all_values = db_schema.get_default_values(equipment_type_id)
        
        print(f"  🔗 연동 확인: Performance {len(performance_values)}개 / 전체 {len(all_values)}개")
        
        print("✅ 기능 간 통합이 정상 작동합니다.")
        return True
        
    except Exception as e:
        print(f"❌ 기능 간 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """기존 기능 호환성 테스트"""
    print("\n🔍 기존 기능 호환성 테스트...")
    
    try:
        # 기존 QC 기능 테스트
        from app.qc import add_qc_check_functions_to_class, QCValidator
        
        class MockManager:
            pass
        
        add_qc_check_functions_to_class(MockManager)
        
        # 기존 comparison 기능 테스트
        from app.comparison import add_comparison_functions_to_class
        add_comparison_functions_to_class(MockManager)
        
        print("✅ 기존 기능 호환성이 유지됩니다.")
        return True
        
    except Exception as e:
        print(f"❌ 기존 기능 호환성 테스트 실패: {e}")
        return False

def cleanup_test_data(equipment_type_id):
    """테스트 데이터 정리"""
    print("\n🧹 테스트 데이터 정리...")
    
    try:
        from app.schema import DBSchema
        
        db_schema = DBSchema()
        
        if equipment_type_id:
            success = db_schema.delete_equipment_type(equipment_type_id)
            if success:
                print("✅ 테스트 데이터 정리 완료")
            else:
                print("⚠️ 테스트 데이터 정리 중 일부 오류 발생")
        
    except Exception as e:
        print(f"⚠️ 테스트 데이터 정리 실패: {e}")

def main():
    """메인 통합 테스트 실행"""
    print("🚀 DB Manager 전체 통합 테스트 시작")
    print("=" * 60)
    
    test_results = []
    equipment_type_id = None
    
    try:
        # Phase 1: DB 스키마 확장
        phase1_result, equipment_type_id = test_phase1_db_schema_integration()
        test_results.append(phase1_result)
        
        if phase1_result and equipment_type_id:
            # Phase 2: QC 검수 탭 개선
            phase2_result = test_phase2_qc_enhancement_integration(equipment_type_id)
            test_results.append(phase2_result)
            
            # Phase 3: DB 비교 탭 확장
            phase3_result = test_phase3_comparison_enhancement_integration(equipment_type_id)
            test_results.append(phase3_result)
            
            # 기능 간 통합 테스트
            integration_result = test_cross_functionality_integration(equipment_type_id)
            test_results.append(integration_result)
        else:
            print("❌ Phase 1 실패로 후속 테스트를 건너뜁니다.")
            test_results.extend([False, False, False])
        
        # 기존 기능 호환성 테스트
        compatibility_result = test_backward_compatibility()
        test_results.append(compatibility_result)
        
    finally:
        # 테스트 데이터 정리
        if equipment_type_id:
            cleanup_test_data(equipment_type_id)
    
    # 최종 결과 요약
    print("\n" + "=" * 60)
    print("📊 전체 통합 테스트 결과 요약")
    print("=" * 60)
    
    phase_names = [
        "Phase 1: DB 스키마 확장",
        "Phase 2: QC 검수 탭 개선", 
        "Phase 3: DB 비교 탭 확장",
        "기능 간 통합",
        "기존 기능 호환성"
    ]
    
    passed = 0
    total = len(test_results)
    
    for i, (phase, result) in enumerate(zip(phase_names, test_results)):
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{status} {phase}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"전체 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("\n🎉 모든 통합 테스트가 성공했습니다!")
        print("🚀 DB Manager Performance QC 시스템이 완전히 구현되었습니다.")
        
        print("\n📋 구현된 주요 기능:")
        print("  ✅ Phase 1: DB 스키마에 is_performance 컬럼 추가")
        print("  ✅ Phase 2: QC 검수 탭 Performance 모드 지원")
        print("  ✅ Phase 3: DB 비교 탭 Default DB 비교 기능")
        print("  ✅ 기능 간 완전 통합 및 기존 기능 호환성 유지")
        
        return True
    else:
        print(f"\n⚠️ {total - passed}개의 테스트가 실패했습니다.")
        print("🔧 추가 디버깅이 필요합니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 