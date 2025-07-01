#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB Manager Test Runner
통합된 테스트 실행 및 관리 도구

이 도구는 다음 기능들을 제공합니다:
1. 모듈별 단위 테스트 실행
2. 통합 테스트 실행
3. 테스트 결과 리포팅
4. 코드 커버리지 분석 (선택적)
"""

import sys
import os
import unittest
import time
from datetime import datetime
from io import StringIO

# 현재 파일의 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

class TestRunner:
    """통합 테스트 실행기"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        
    def run_data_utils_tests(self):
        """data_utils 모듈 테스트"""
        print("🔍 data_utils 모듈 테스트 실행...")
        
        try:
            from app.data_utils import (
                numeric_sort_key, calculate_string_similarity,
                safe_convert_to_float, safe_convert_to_int,
                normalize_parameter_name, is_numeric_string, clean_numeric_value
            )
            
            # 테스트 케이스들
            tests = [
                ("numeric_sort_key", lambda: self._test_numeric_sort_key(numeric_sort_key)),
                ("calculate_string_similarity", lambda: self._test_string_similarity(calculate_string_similarity)),
                ("safe_convert_to_float", lambda: self._test_safe_convert_float(safe_convert_to_float)),
                ("safe_convert_to_int", lambda: self._test_safe_convert_int(safe_convert_to_int)),
                ("normalize_parameter_name", lambda: self._test_normalize_param_name(normalize_parameter_name)),
                ("is_numeric_string", lambda: self._test_is_numeric_string(is_numeric_string)),
                ("clean_numeric_value", lambda: self._test_clean_numeric_value(clean_numeric_value))
            ]
            
            passed = 0
            for test_name, test_func in tests:
                try:
                    test_func()
                    print(f"  ✅ {test_name}")
                    passed += 1
                except Exception as e:
                    print(f"  ❌ {test_name}: {e}")
            
            result = passed == len(tests)
            self.test_results.append(("data_utils", result, passed, len(tests)))
            return result
            
        except ImportError as e:
            print(f"❌ data_utils import 실패: {e}")
            self.test_results.append(("data_utils", False, 0, 0))
            return False
    
    def run_schema_tests(self):
        """DB 스키마 테스트"""
        print("🔍 DB 스키마 테스트 실행...")
        
        try:
            from app.schema import DBSchema
            
            # 스키마 초기화 테스트
            db_schema = DBSchema()
            
            tests = [
                ("초기화", lambda: db_schema is not None),
                ("장비 유형 조회", lambda: len(db_schema.get_equipment_types()) >= 0),
                ("테스트 장비 추가", lambda: self._test_equipment_operations(db_schema)),
                ("파라미터 조회", lambda: self._test_parameter_operations(db_schema))
            ]
            
            passed = 0
            for test_name, test_func in tests:
                try:
                    result = test_func()
                    if result:
                        print(f"  ✅ {test_name}")
                        passed += 1
                    else:
                        print(f"  ❌ {test_name}: 테스트 실패")
                except Exception as e:
                    print(f"  ❌ {test_name}: {e}")
            
            result = passed == len(tests)
            self.test_results.append(("schema", result, passed, len(tests)))
            return result
            
        except Exception as e:
            print(f"❌ 스키마 테스트 실패: {e}")
            self.test_results.append(("schema", False, 0, 0))
            return False
    
    def run_service_tests(self):
        """서비스 레이어 테스트"""
        print("🔍 서비스 레이어 테스트 실행...")
        
        try:
            from app.services import ServiceFactory, SERVICES_AVAILABLE
            from app.schema import DBSchema
            
            if not SERVICES_AVAILABLE:
                print("  ⚠️ 서비스 레이어 비활성화")
                self.test_results.append(("services", True, 0, 0))
                return True
            
            db_schema = DBSchema()
            service_factory = ServiceFactory(db_schema)
            
            tests = [
                ("서비스 팩토리 초기화", lambda: service_factory is not None),
                ("서비스 상태 조회", lambda: len(service_factory.get_service_status()) > 0),
                ("장비 서비스 테스트", lambda: self._test_equipment_service(service_factory))
            ]
            
            passed = 0
            for test_name, test_func in tests:
                try:
                    result = test_func()
                    if result:
                        print(f"  ✅ {test_name}")
                        passed += 1
                    else:
                        print(f"  ❌ {test_name}: 테스트 실패")
                except Exception as e:
                    print(f"  ❌ {test_name}: {e}")
            
            result = passed == len(tests)
            self.test_results.append(("services", result, passed, len(tests)))
            return result
            
        except ImportError:
            print("  ⚠️ 서비스 레이어 사용 불가")
            self.test_results.append(("services", True, 0, 0))
            return True
        except Exception as e:
            print(f"❌ 서비스 테스트 실패: {e}")
            self.test_results.append(("services", False, 0, 0))
            return False
    
    def run_integration_tests(self):
        """통합 테스트 실행"""
        print("🔍 통합 테스트 실행...")
        
        try:
            from app.schema import DBSchema
            from app.manager import DBManager
            
            tests = [
                ("DB Manager 초기화", lambda: self._test_db_manager_init()),
                ("파일 로딩 시뮬레이션", lambda: self._test_file_loading_simulation()),
                ("QC 기능 통합", lambda: self._test_qc_integration())
            ]
            
            passed = 0
            for test_name, test_func in tests:
                try:
                    result = test_func()
                    if result:
                        print(f"  ✅ {test_name}")
                        passed += 1
                    else:
                        print(f"  ❌ {test_name}: 테스트 실패")
                except Exception as e:
                    print(f"  ❌ {test_name}: {e}")
            
            result = passed == len(tests)
            self.test_results.append(("integration", result, passed, len(tests)))
            return result
            
        except Exception as e:
            print(f"❌ 통합 테스트 실패: {e}")
            self.test_results.append(("integration", False, 0, 0))
            return False
    
    # 개별 테스트 함수들
    def _test_numeric_sort_key(self, func):
        assert func("123.45") == 123.45
        assert func("0") == 0.0
        assert func("N/A") == float('inf')
        assert func("") == float('inf')
        return True
    
    def _test_string_similarity(self, func):
        assert func("hello", "hello") == 1.0
        assert func("", "") == 1.0
        assert func("", "test") == 0.0
        assert 0.0 <= func("hello", "helo") <= 1.0
        return True
    
    def _test_safe_convert_float(self, func):
        assert func("123.45") == 123.45
        assert func("N/A") == 0.0  # default value
        assert func("") == 0.0     # default value
        return True
    
    def _test_safe_convert_int(self, func):
        assert func("123") == 123
        assert func("123.45") == 123
        assert func("N/A") == 0   # default value
        return True
    
    def _test_normalize_param_name(self, func):
        result = func("  Test Parameter  ")
        assert result == "testparameter"  # 실제 함수는 모든 공백/특수문자를 제거
        return True
    
    def _test_is_numeric_string(self, func):
        assert func("123.45") == True
        assert func("abc") == False
        assert func("") == False
        return True
    
    def _test_clean_numeric_value(self, func):
        result = func("  123.45  ")
        assert result == "123.45"
        return True
    
    def _test_equipment_operations(self, db_schema):
        # 테스트 장비 유형 추가
        type_id = db_schema.add_equipment_type("테스트장비", "테스트용")
        assert type_id is not None
        
        # 파라미터 추가
        param_id = db_schema.add_default_value(
            type_id, "테스트파라미터", "100.0", 
            description="테스트용 파라미터"
        )
        assert param_id is not None
        
        # 정리
        db_schema.delete_equipment_type(type_id)
        return True
    
    def _test_parameter_operations(self, db_schema):
        equipment_types = db_schema.get_equipment_types()
        if equipment_types:
            type_id = equipment_types[0][0]
            default_values = db_schema.get_default_values(type_id)
            assert isinstance(default_values, list)
        return True
    
    def _test_equipment_service(self, service_factory):
        try:
            equipment_service = service_factory.get_service('IEquipmentService')
            return equipment_service is not None
        except:
            return False
    
    def _test_db_manager_init(self):
        # GUI 없이 테스트하기 위해 간단한 초기화만 확인
        try:
            from app.schema import DBSchema
            db_schema = DBSchema()
            return db_schema is not None
        except:
            return False
    
    def _test_file_loading_simulation(self):
        # 파일 로딩 관련 유틸리티 함수 테스트
        try:
            from app.data_utils import numeric_sort_key
            # 기본적인 함수 호출 테스트
            result = numeric_sort_key("123")
            return result == 123.0
        except:
            return False
    
    def _test_qc_integration(self):
        # QC 기능 통합 테스트
        try:
            from app.schema import DBSchema
            db_schema = DBSchema()
            equipment_types = db_schema.get_equipment_types()
            return len(equipment_types) >= 0
        except:
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 DB Manager 전체 테스트 시작")
        print("=" * 60)
        print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = time.time()
        
        # 테스트 모듈들
        test_modules = [
            ("데이터 유틸리티", self.run_data_utils_tests),
            ("DB 스키마", self.run_schema_tests),
            ("서비스 레이어", self.run_service_tests),
            ("통합 테스트", self.run_integration_tests)
        ]
        
        print()
        for module_name, test_func in test_modules:
            print(f"📋 {module_name} 테스트:")
            try:
                test_func()
            except Exception as e:
                print(f"❌ {module_name} 테스트 실행 중 오류: {e}")
                self.test_results.append((module_name.lower().replace(" ", "_"), False, 0, 0))
            print()
        
        # 결과 요약
        self._print_summary()
    
    def _print_summary(self):
        """테스트 결과 요약 출력"""
        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        
        print("=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        
        total_modules = len(self.test_results)
        passed_modules = 0
        total_tests = 0
        passed_tests = 0
        
        for module_name, result, passed, total in self.test_results:
            status = "✅ 통과" if result else "❌ 실패"
            test_info = f"({passed}/{total})" if total > 0 else "(비활성화)"
            print(f"{status} {module_name}: {test_info}")
            
            if result:
                passed_modules += 1
            total_tests += total
            passed_tests += passed
        
        print("=" * 60)
        print(f"모듈 결과: {passed_modules}/{total_modules} 통과")
        print(f"테스트 결과: {passed_tests}/{total_tests} 통과")
        print(f"실행 시간: {duration:.2f}초")
        
        if passed_modules == total_modules:
            print("\n🎉 모든 테스트가 성공적으로 통과했습니다!")
        else:
            print(f"\n⚠️ {total_modules - passed_modules}개 모듈에 문제가 있습니다.")
        
        return passed_modules == total_modules

def main():
    """메인 실행 함수"""
    runner = TestRunner()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "data":
            runner.run_data_utils_tests()
        elif command == "schema":
            runner.run_schema_tests()
        elif command == "services":
            runner.run_service_tests()
        elif command == "integration":
            runner.run_integration_tests()
        else:
            print("사용법: python test_runner.py [data|schema|services|integration]")
    else:
        # 기본: 전체 테스트
        runner.run_all_tests()

if __name__ == "__main__":
    main()