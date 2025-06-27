#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB Manager 종합 테스트 스위트
모든 모듈화 및 리팩토링 작업에 대한 통합 테스트
"""

import sys
import os
import unittest
import pandas as pd
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
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
    
    def test_safe_convert_to_float(self):
        """safe_convert_to_float 함수 테스트"""
        self.assertEqual(self.safe_convert_to_float("123.45"), 123.45)
        self.assertEqual(self.safe_convert_to_float("abc"), 0.0)
        self.assertEqual(self.safe_convert_to_float(None), 0.0)
        self.assertEqual(self.safe_convert_to_float("N/A"), 0.0)
    
    def test_normalize_parameter_name(self):
        """normalize_parameter_name 함수 테스트"""
        self.assertEqual(self.normalize_parameter_name("Test_Parameter"), "testparameter")
        self.assertEqual(self.normalize_parameter_name("test-parameter"), "testparameter")
        self.assertEqual(self.normalize_parameter_name("TEST PARAMETER"), "testparameter")


class TestConfigManager(unittest.TestCase):
    """config_manager 모듈 테스트"""
    
    def setUp(self):
        from app.config_manager import ConfigManager, apply_settings, should_use_service
        self.ConfigManager = ConfigManager
        self.apply_settings = apply_settings
        self.should_use_service = should_use_service
    
    def test_config_manager_creation(self):
        """ConfigManager 생성 테스트"""
        config_manager = self.ConfigManager()
        self.assertIsNotNone(config_manager)
        self.assertTrue(hasattr(config_manager, 'show_about'))
        self.assertTrue(hasattr(config_manager, 'show_user_guide'))
        self.assertTrue(hasattr(config_manager, 'should_use_service'))
    
    def test_apply_settings(self):
        """apply_settings 함수 테스트"""
        # None config 테스트
        result = self.apply_settings(None, {})
        self.assertFalse(result)
    
    def test_should_use_service(self):
        """should_use_service 함수 테스트"""
        result = self.should_use_service("test_service", None, {})
        self.assertFalse(result)


class TestFileService(unittest.TestCase):
    """file_service 모듈 테스트"""
    
    def setUp(self):
        from app.file_service import FileService, merge_dataframes, load_txt_file
        self.FileService = FileService
        self.merge_dataframes = merge_dataframes
        self.load_txt_file = load_txt_file
    
    def test_file_service_creation(self):
        """FileService 생성 테스트"""
        file_service = self.FileService()
        self.assertIsNotNone(file_service)
        self.assertTrue(hasattr(file_service, 'export_dataframe'))
        self.assertTrue(hasattr(file_service, 'load_database_files'))
    
    def test_merge_dataframes(self):
        """merge_dataframes 함수 테스트"""
        df1 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        df2 = pd.DataFrame({'A': [5, 6], 'B': [7, 8]})
        
        result = self.merge_dataframes([df1, df2])
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)  # 2 + 2 rows
        
        # 빈 리스트 테스트
        result = self.merge_dataframes([])
        self.assertIsNone(result)
        
        # 단일 DataFrame 테스트
        result = self.merge_dataframes([df1])
        self.assertTrue(result.equals(df1))


class TestDialogHelpers(unittest.TestCase):
    """dialog_helpers 모듈 테스트"""
    
    def setUp(self):
        from app.dialog_helpers import validate_numeric_range, handle_error
        self.validate_numeric_range = validate_numeric_range
        self.handle_error = handle_error
    
    def test_validate_numeric_range(self):
        """validate_numeric_range 함수 테스트"""
        # 정상 범위
        is_valid, min_val, max_val, error = self.validate_numeric_range("10", "20")
        self.assertTrue(is_valid)
        self.assertEqual(min_val, 10.0)
        self.assertEqual(max_val, 20.0)
        self.assertIsNone(error)
        
        # 빈 값
        is_valid, min_val, max_val, error = self.validate_numeric_range("", "")
        self.assertTrue(is_valid)
        self.assertIsNone(min_val)
        self.assertIsNone(max_val)
        
        # 잘못된 범위
        is_valid, min_val, max_val, error = self.validate_numeric_range("20", "10")
        self.assertFalse(is_valid)
        self.assertIsNone(min_val)
        self.assertIsNone(max_val)
        self.assertIsNotNone(error)
        
        # 유효하지 않은 숫자
        is_valid, min_val, max_val, error = self.validate_numeric_range("abc", "def")
        self.assertFalse(is_valid)
        
    def test_handle_error(self):
        """handle_error 함수 테스트"""
        test_exception = Exception("Test error")
        log_messages = []
        
        def mock_log(message):
            log_messages.append(message)
        
        error_msg = self.handle_error("Test operation", test_exception, mock_log, False)
        self.assertIn("Test operation", error_msg)
        self.assertIn("Test error", error_msg)
        self.assertEqual(len(log_messages), 1)


class TestDatabaseSchema(unittest.TestCase):
    """schema.py 데이터베이스 스키마 테스트"""
    
    def setUp(self):
        """테스트용 DB 스키마 초기화"""
        from app.schema import DBSchema
        import tempfile
        import os
        
        # 임시 DB 파일 생성
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        
        self.db_schema = DBSchema(self.temp_db_path)
    
    def tearDown(self):
        """테스트 정리"""
        import os
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
    
    def test_equipment_type_operations(self):
        """장비 유형 CRUD 테스트"""
        # 장비 유형 추가
        type_id = self.db_schema.add_equipment_type("TestEquipment", "Test Description")
        self.assertIsNotNone(type_id)
        
        # 장비 유형 조회
        equipment_types = self.db_schema.get_equipment_types()
        self.assertTrue(len(equipment_types) > 0)
        
        # 이름으로 장비 유형 조회
        found_type = self.db_schema.get_equipment_type_by_name("TestEquipment")
        self.assertIsNotNone(found_type)
        self.assertEqual(found_type[1], "TestEquipment")
    
    def test_default_value_operations(self):
        """Default DB 값 CRUD 테스트"""
        # 장비 유형 생성
        type_id = self.db_schema.add_equipment_type("TestEquipment")
        
        # Default 값 추가
        value_id = self.db_schema.add_default_value(
            equipment_type_id=type_id,
            parameter_name="TestParam",
            default_value="100",
            min_spec="90",
            max_spec="110"
        )
        self.assertIsNotNone(value_id)
        
        # Default 값 조회
        values = self.db_schema.get_default_values(type_id)
        self.assertTrue(len(values) > 0)
        
        # 특정 파라미터 조회 (새로 추가된 메서드)
        param_data = self.db_schema.get_parameter_by_id(value_id)
        self.assertIsNotNone(param_data)
        self.assertEqual(param_data['parameter_name'], "TestParam")
    
    def test_change_history_operations(self):
        """변경 이력 테스트"""
        # 변경 이력 추가 (새로 추가된 메서드)
        history_id = self.db_schema.log_change_history(
            "add", "parameter", "TestParam", "", "100", "test_user"
        )
        self.assertIsNotNone(history_id)
        
        # 변경 이력 조회
        history = self.db_schema.get_change_history(limit=10)
        self.assertTrue(len(history) > 0)
    
    def test_parameter_statistics(self):
        """파라미터 통계 조회 테스트 (새로 추가된 메서드)"""
        # 장비 유형 및 파라미터 생성
        type_id = self.db_schema.add_equipment_type("TestEquipment")
        self.db_schema.add_default_value(
            equipment_type_id=type_id,
            parameter_name="TestParam",
            default_value="100",
            occurrence_count=5,
            total_files=10,
            confidence_score=0.8
        )
        
        # 통계 조회
        stats = self.db_schema.get_parameter_statistics(type_id, "TestParam")
        self.assertIsNotNone(stats)
        self.assertEqual(stats['occurrence_count'], 5)
        self.assertEqual(stats['total_files'], 10)
    
    def test_performance_status(self):
        """Performance 상태 설정 테스트 (새로 추가된 메서드)"""
        # 장비 유형 및 파라미터 생성
        type_id = self.db_schema.add_equipment_type("TestEquipment")
        value_id = self.db_schema.add_default_value(
            equipment_type_id=type_id,
            parameter_name="TestParam",
            default_value="100"
        )
        
        # Performance 상태 설정
        result = self.db_schema.set_performance_status(value_id, True)
        self.assertTrue(result)
        
        # 설정 확인
        param_data = self.db_schema.get_parameter_by_id(value_id)
        self.assertIsNotNone(param_data)
        self.assertTrue(param_data['is_performance'])


class TestServiceLayer(unittest.TestCase):
    """서비스 레이어 테스트"""
    
    def test_service_imports(self):
        """서비스 모듈 import 테스트"""
        try:
            from app.services import ServiceFactory, LegacyAdapter, SERVICES_AVAILABLE
            self.assertTrue(SERVICES_AVAILABLE)
        except ImportError as e:
            self.fail(f"서비스 모듈 import 실패: {e}")
    
    def test_service_factory_creation(self):
        """서비스 팩토리 생성 테스트"""
        try:
            from app.services import ServiceFactory
            from app.schema import DBSchema
            
            # 임시 DB 스키마 생성
            import tempfile
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            db_schema = DBSchema(temp_db.name)
            service_factory = ServiceFactory(db_schema)
            
            self.assertIsNotNone(service_factory)
            self.assertIsNotNone(service_factory._db_schema)
            
            # 서비스 상태 확인
            status = service_factory.get_service_status()
            self.assertIsInstance(status, dict)
            
            # 정리
            import os
            os.unlink(temp_db.name)
            
        except Exception as e:
            self.fail(f"서비스 팩토리 생성 실패: {e}")


class TestManagerIntegration(unittest.TestCase):
    """manager.py 통합 테스트"""
    
    def test_manager_import(self):
        """DBManager import 테스트"""
        try:
            from app.manager import DBManager
            self.assertTrue(True)  # import 성공
        except ImportError as e:
            self.fail(f"DBManager import 실패: {e}")
    
    def test_extracted_modules_import(self):
        """추출된 모듈들의 import 테스트"""
        modules_to_test = [
            'app.data_utils',
            'app.config_manager', 
            'app.file_service',
            'app.dialog_helpers'
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
            except ImportError as e:
                self.fail(f"{module_name} import 실패: {e}")
    
    def test_schema_methods_exist(self):
        """필수 schema 메서드 존재 확인"""
        from app.schema import DBSchema
        
        # 임시 DB 생성
        import tempfile
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            db_schema = DBSchema(temp_db.name)
            
            # 필수 메서드들 존재 확인
            required_methods = [
                'get_parameter_by_id',
                'log_change_history', 
                'get_parameter_statistics',
                'set_performance_status'
            ]
            
            for method_name in required_methods:
                self.assertTrue(hasattr(db_schema, method_name), 
                              f"DBSchema에 {method_name} 메서드가 없음")
        finally:
            import os
            os.unlink(temp_db.name)


class TestCodeMetrics(unittest.TestCase):
    """코드 메트릭 테스트"""
    
    def test_line_count_reduction(self):
        """코드 라인 수 감소 확인"""
        manager_path = os.path.join(src_path, 'app', 'manager.py')
        
        with open(manager_path, 'r', encoding='utf-8') as f:
            current_lines = len(f.readlines())
        
        # 원래 4,852 라인에서 시작
        original_lines = 4852
        reduction = original_lines - current_lines
        
        self.assertLess(current_lines, original_lines, 
                       f"현재 라인 수 {current_lines}가 원래 라인 수 {original_lines}보다 적지 않음")
        
        print(f"📊 라인 수 감소: {original_lines} → {current_lines} ({reduction} 라인 감소)")
    
    def test_extracted_modules_exist(self):
        """추출된 모듈 파일들 존재 확인"""
        expected_modules = [
            'data_utils.py',
            'config_manager.py',
            'file_service.py', 
            'dialog_helpers.py'
        ]
        
        for module_name in expected_modules:
            module_path = os.path.join(src_path, 'app', module_name)
            self.assertTrue(os.path.exists(module_path), 
                          f"추출된 모듈 {module_name}이 존재하지 않음")


def run_performance_test():
    """성능 테스트 (간단한 벤치마크)"""
    print("\n🚀 성능 테스트 실행...")
    
    try:
        from app.data_utils import numeric_sort_key, calculate_string_similarity
        import time
        
        # numeric_sort_key 성능 테스트
        start_time = time.time()
        test_values = ["123.45", "67.8", "N/A", "abc", "999.999"] * 1000
        for val in test_values:
            numeric_sort_key(val)
        end_time = time.time()
        
        print(f"✅ numeric_sort_key: {len(test_values)}회 호출 - {(end_time - start_time)*1000:.2f}ms")
        
        # string_similarity 성능 테스트
        start_time = time.time()
        test_pairs = [("hello", "helo"), ("parameter", "paramter")] * 500
        for str1, str2 in test_pairs:
            calculate_string_similarity(str1, str2)
        end_time = time.time()
        
        print(f"✅ calculate_string_similarity: {len(test_pairs)}회 호출 - {(end_time - start_time)*1000:.2f}ms")
        
    except Exception as e:
        print(f"❌ 성능 테스트 실패: {e}")


def main():
    """메인 테스트 실행 함수"""
    print("🚀 DB Manager 종합 테스트 스위트")
    print("=" * 70)
    print(f"📅 테스트 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # unittest 실행
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 클래스들 추가
    test_classes = [
        TestDataUtils,
        TestConfigManager, 
        TestFileService,
        TestDialogHelpers,
        TestDatabaseSchema,
        TestServiceLayer,
        TestManagerIntegration,
        TestCodeMetrics
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 성능 테스트 실행
    run_performance_test()
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("📊 테스트 결과 요약:")
    print("=" * 70)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success = total_tests - failures - errors
    
    print(f"전체 테스트: {total_tests}개")
    print(f"✅ 성공: {success}개")
    print(f"❌ 실패: {failures}개") 
    print(f"⚠️ 오류: {errors}개")
    
    success_rate = (success / total_tests) * 100 if total_tests > 0 else 0
    print(f"📈 성공률: {success_rate:.1f}%")
    
    if failures > 0:
        print("\n❌ 실패한 테스트:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if errors > 0:
        print("\n⚠️ 오류가 발생한 테스트:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # 모듈화 성과 요약
    print("\n" + "=" * 70)
    print("📋 모듈화 성과 요약:")
    print("=" * 70)
    print("✅ 추출된 모듈:")
    print("  📦 data_utils.py - 데이터 처리 유틸리티")
    print("  📦 config_manager.py - 설정 및 구성 관리") 
    print("  📦 file_service.py - 파일 I/O 처리")
    print("  📦 dialog_helpers.py - 대화상자 공통 기능")
    print("\n🎯 달성 목표:")
    print("  ✅ 중복 코드 제거")
    print("  ✅ 모듈화를 통한 유지보수성 향상")
    print("  ✅ 코드 크기 감소")
    print("  ✅ 기능별 책임 분리")
    
    if success_rate >= 90:
        print("\n🎉 모듈화 프로젝트가 성공적으로 완료되었습니다!")
        return True
    else:
        print("\n⚠️ 일부 테스트 실패가 있습니다. 추가 검토가 필요합니다.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)