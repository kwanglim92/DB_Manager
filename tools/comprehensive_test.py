#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB Manager Comprehensive Test Suite
종합적인 테스트 및 검증 도구

이 도구는 기존 test_suite.py를 대체하며 다음 기능을 제공합니다:
1. unittest 기반의 체계적인 테스트
2. 모듈별 세분화된 테스트
3. 성능 및 메모리 사용량 체크
4. 회귀 테스트 지원
"""

import sys
import os
import unittest
import pandas as pd
import tempfile
import time
import psutil
from datetime import datetime

# 현재 파일의 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

class TestDataUtils(unittest.TestCase):
    """data_utils 모듈 테스트"""
    
    def setUp(self):
        from app.data_utils import (
            numeric_sort_key, calculate_string_similarity,
            safe_convert_to_float, safe_convert_to_int,
            normalize_parameter_name, is_numeric_string, clean_numeric_value
        )
        self.numeric_sort_key = numeric_sort_key
        self.calculate_string_similarity = calculate_string_similarity
        self.safe_convert_to_float = safe_convert_to_float
        self.safe_convert_to_int = safe_convert_to_int
        self.normalize_parameter_name = normalize_parameter_name
        self.is_numeric_string = is_numeric_string
        self.clean_numeric_value = clean_numeric_value
    
    def test_numeric_sort_key(self):
        """numeric_sort_key 함수 테스트"""
        self.assertEqual(self.numeric_sort_key("123.45"), 123.45)
        self.assertEqual(self.numeric_sort_key("0"), 0.0)
        self.assertEqual(self.numeric_sort_key("N/A"), float('inf'))
        self.assertEqual(self.numeric_sort_key(""), float('inf'))
        self.assertEqual(self.numeric_sort_key("abc"), float('inf'))
    
    def test_calculate_string_similarity(self):
        """calculate_string_similarity 함수 테스트"""
        self.assertEqual(self.calculate_string_similarity("hello", "hello"), 1.0)
        self.assertAlmostEqual(self.calculate_string_similarity("hello", "helo"), 0.8, places=1)
        self.assertEqual(self.calculate_string_similarity("", ""), 1.0)
        self.assertEqual(self.calculate_string_similarity("", "test"), 0.0)
    
    def test_safe_convert_functions(self):
        """안전한 변환 함수들 테스트"""
        # safe_convert_to_float
        self.assertEqual(self.safe_convert_to_float("123.45"), 123.45)
        self.assertEqual(self.safe_convert_to_float("N/A"), 0.0)  # default value
        self.assertEqual(self.safe_convert_to_float(""), 0.0)     # default value
        
        # safe_convert_to_int
        self.assertEqual(self.safe_convert_to_int("123"), 123)
        self.assertEqual(self.safe_convert_to_int("123.45"), 123)
        self.assertEqual(self.safe_convert_to_int("N/A"), 0)     # default value
    
    def test_string_utilities(self):
        """문자열 유틸리티 함수들 테스트"""
        # normalize_parameter_name
        result = self.normalize_parameter_name("  Test Parameter  ")
        self.assertEqual(result, "testparameter")  # 실제 함수는 모든 공백/특수문자를 제거
        
        # is_numeric_string
        self.assertTrue(self.is_numeric_string("123.45"))
        self.assertFalse(self.is_numeric_string("abc"))
        self.assertFalse(self.is_numeric_string(""))
        
        # clean_numeric_value
        result = self.clean_numeric_value("  123.45  ")
        self.assertEqual(result, "123.45")

class TestDatabaseSchema(unittest.TestCase):
    """DB 스키마 테스트"""
    
    def setUp(self):
        from app.schema import DBSchema
        self.db_schema = DBSchema()
        self.test_equipment_ids = []
    
    def tearDown(self):
        # 테스트에서 생성한 장비 유형 정리
        for equipment_id in self.test_equipment_ids:
            try:
                self.db_schema.delete_equipment_type(equipment_id)
            except:
                pass
    
    def test_schema_initialization(self):
        """스키마 초기화 테스트"""
        self.assertIsNotNone(self.db_schema)
        self.assertTrue(os.path.exists(self.db_schema.db_path))
    
    def test_equipment_type_operations(self):
        """장비 유형 CRUD 테스트"""
        # 추가
        equipment_id = self.db_schema.add_equipment_type("테스트장비", "unittest용 테스트 장비")
        self.assertIsNotNone(equipment_id)
        self.test_equipment_ids.append(equipment_id)
        
        # 조회
        equipment_type = self.db_schema.get_equipment_type_by_name("테스트장비")
        self.assertIsNotNone(equipment_type)
        self.assertEqual(equipment_type[1], "테스트장비")
        
        # 목록 조회
        equipment_types = self.db_schema.get_equipment_types()
        self.assertIsInstance(equipment_types, list)
        self.assertTrue(len(equipment_types) > 0)
    
    def test_parameter_operations(self):
        """파라미터 CRUD 테스트"""
        # 테스트용 장비 유형 생성
        equipment_id = self.db_schema.add_equipment_type("파라미터테스트장비", "파라미터 테스트용")
        self.test_equipment_ids.append(equipment_id)
        
        # 파라미터 추가
        param_id = self.db_schema.add_default_value(
            equipment_id, "테스트파라미터", "100.0",
            min_spec="90.0", max_spec="110.0",
            description="unittest용 테스트 파라미터",
            is_performance=True
        )
        self.assertIsNotNone(param_id)
        
        # 파라미터 조회
        default_values = self.db_schema.get_default_values(equipment_id)
        self.assertIsInstance(default_values, list)
        self.assertTrue(len(default_values) > 0)
        
        # Check list 필터링 테스트
        checklist_values = self.db_schema.get_default_values(equipment_id, checklist_only=True)
        self.assertIsInstance(checklist_values, list)
        
        # Performance 상태 변경 테스트
        result = self.db_schema.set_performance_status(param_id, False)
        self.assertTrue(result)

class TestServiceLayer(unittest.TestCase):
    """서비스 레이어 테스트"""
    
    def setUp(self):
        try:
            from app.services import ServiceFactory, SERVICES_AVAILABLE
            from app.schema import DBSchema
            
            if SERVICES_AVAILABLE:
                self.db_schema = DBSchema()
                self.service_factory = ServiceFactory(self.db_schema)
                self.services_available = True
            else:
                self.services_available = False
        except ImportError:
            self.services_available = False
    
    def test_service_factory_initialization(self):
        """서비스 팩토리 초기화 테스트"""
        if not self.services_available:
            self.skipTest("서비스 레이어 비활성화")
        
        self.assertIsNotNone(self.service_factory)
        
        # 서비스 상태 확인
        status = self.service_factory.get_service_status()
        self.assertIsInstance(status, dict)
    
    def test_equipment_service(self):
        """장비 서비스 테스트"""
        if not self.services_available:
            self.skipTest("서비스 레이어 비활성화")
        
        try:
            equipment_service = self.service_factory.get_service('IEquipmentService')
            self.assertIsNotNone(equipment_service)
        except Exception as e:
            self.fail(f"장비 서비스 조회 실패: {e}")

class TestIntegration(unittest.TestCase):
    """통합 테스트"""
    
    def setUp(self):
        from app.schema import DBSchema
        self.db_schema = DBSchema()
    
    def test_file_operations_simulation(self):
        """파일 작업 시뮬레이션 테스트"""
        # 임시 데이터 생성
        test_data = {
            'Module': ['TestModule1', 'TestModule2'],
            'Part': ['TestPart1', 'TestPart2'],
            'ItemName': ['TestParam1', 'TestParam2'],
            'Value1': [100.0, 200.0],
            'Value2': [150.0, 250.0]
        }
        
        # DataFrame 생성 및 기본 작업 테스트
        df = pd.DataFrame(test_data)
        self.assertEqual(len(df), 2)
        self.assertIn('Module', df.columns)
        
        # 임시 파일 저장/로드 테스트
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_file_path = f.name
        
        try:
            loaded_df = pd.read_csv(temp_file_path)
            self.assertEqual(len(loaded_df), 2)
        finally:
            os.unlink(temp_file_path)
    
    def test_data_processing_pipeline(self):
        """데이터 처리 파이프라인 테스트"""
        from app.data_utils import numeric_sort_key, calculate_string_similarity
        
        # 데이터 처리 시뮬레이션
        test_values = ["123.45", "67.8", "N/A", "999.0"]
        sorted_values = sorted(test_values, key=numeric_sort_key)
        
        # 정렬 결과 검증
        self.assertEqual(sorted_values[0], "67.8")  # 가장 작은 숫자
        self.assertEqual(sorted_values[-1], "N/A")  # inf 값
        
        # 문자열 유사도 테스트
        similarity = calculate_string_similarity("parameter", "paramter")
        self.assertGreater(similarity, 0.5)  # 높은 유사도 기대

class PerformanceTestCase(unittest.TestCase):
    """성능 테스트"""
    
    def setUp(self):
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.start_time = time.time()
    
    def tearDown(self):
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        duration = end_time - self.start_time
        memory_increase = end_memory - self.start_memory
        
        print(f"\n성능 측정 - 실행시간: {duration:.3f}초, 메모리 증가: {memory_increase:.1f}MB")
    
    def test_large_data_processing(self):
        """대용량 데이터 처리 성능 테스트"""
        from app.data_utils import numeric_sort_key
        
        # 대량의 테스트 데이터 생성
        test_data = [f"{i}.{i%100}" for i in range(10000)]
        
        # 정렬 성능 테스트
        start_time = time.time()
        sorted_data = sorted(test_data, key=numeric_sort_key)
        duration = time.time() - start_time
        
        self.assertEqual(len(sorted_data), 10000)
        self.assertLess(duration, 5.0)  # 5초 이내 완료 기대

def run_comprehensive_tests():
    """종합 테스트 실행"""
    print("🚀 DB Manager 종합 테스트 스위트 시작")
    print("=" * 70)
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️ 시스템: {psutil.cpu_count()}CPU, {psutil.virtual_memory().total // (1024**3)}GB RAM")
    print()
    
    # 테스트 스위트 구성
    test_classes = [
        TestDataUtils,
        TestDatabaseSchema,
        TestServiceLayer,
        TestIntegration,
        PerformanceTestCase
    ]
    
    # 전체 결과 수집
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for test_class in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        
        print(f"\n📋 {test_class.__name__} 실행:")
        print("-" * 50)
        
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
    
    # 최종 결과 요약
    print("\n" + "=" * 70)
    print("📊 종합 테스트 결과 요약")
    print("=" * 70)
    
    passed = total_tests - total_failures - total_errors
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"총 테스트: {total_tests}")
    print(f"✅ 성공: {passed}")
    print(f"❌ 실패: {total_failures}")
    print(f"🚫 오류: {total_errors}")
    print(f"📈 성공률: {success_rate:.1f}%")
    
    if total_failures == 0 and total_errors == 0:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        return True
    else:
        print(f"\n⚠️ {total_failures + total_errors}개의 테스트에 문제가 있습니다.")
        return False

def main():
    """메인 실행 함수"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        
        # 개별 테스트 클래스 실행
        test_classes = {
            'data': TestDataUtils,
            'schema': TestDatabaseSchema,
            'services': TestServiceLayer,
            'integration': TestIntegration,
            'performance': PerformanceTestCase
        }
        
        if test_name in test_classes:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_classes[test_name])
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            return len(result.failures) == 0 and len(result.errors) == 0
        else:
            print("사용법: python comprehensive_test.py [data|schema|services|integration|performance]")
            return False
    else:
        # 전체 테스트 실행
        return run_comprehensive_tests()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)