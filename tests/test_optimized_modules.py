"""
최적화된 모듈 테스트 코드
각 핵심 모듈의 기능을 검증
"""

import unittest
import sys
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# 경로 설정
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from app.core.mode_manager import ModeManager, UserMode
from app.core.controllers.mother_db_manager import (
    MotherDBManager, CandidateAnalyzer, MotherDBCandidate
)
from app.core.controllers.comparison_engine import (
    OptimizedComparisonEngine, ComparisonCache
)
from app.core.controllers.qc_manager import (
    UnifiedQCSystem, QCMode, QCValidator, SeverityLevel
)

class TestModeManager(unittest.TestCase):
    """모드 관리자 테스트"""
    
    def setUp(self):
        self.mode_manager = ModeManager()
    
    def test_initial_mode(self):
        """초기 모드 확인"""
        self.assertEqual(self.mode_manager.get_current_mode(), UserMode.PRODUCTION_ENGINEER)
        self.assertTrue(self.mode_manager.is_production_mode())
        self.assertFalse(self.mode_manager.is_qc_mode())
    
    def test_password_verification(self):
        """비밀번호 검증"""
        # 기본 비밀번호 '1' 테스트
        self.assertTrue(self.mode_manager._verify_password('1'))
        self.assertFalse(self.mode_manager._verify_password('wrong'))
    
    def test_mode_features(self):
        """모드별 기능 확인"""
        # 생산 모드 기능
        features = self.mode_manager.get_available_features()
        self.assertTrue(features['db_comparison'])
        self.assertFalse(features['mother_db_management'])
        
        # QC 모드로 전환 (직접 설정)
        self.mode_manager.current_mode = UserMode.QC_ENGINEER
        features = self.mode_manager.get_available_features()
        self.assertTrue(features['mother_db_management'])
        self.assertTrue(features['qc_inspection'])

class TestCandidateAnalyzer(unittest.TestCase):
    """Mother DB 후보 분석기 테스트"""
    
    def setUp(self):
        self.analyzer = CandidateAnalyzer(min_occurrence_rate=0.8)
    
    def test_confidence_calculation(self):
        """신뢰도 계산 테스트"""
        # 모든 값이 같은 경우 (높은 신뢰도)
        value_counts = pd.Series([10])
        confidence = self.analyzer._calculate_confidence(value_counts, 10)
        self.assertGreater(confidence, 0.9)
        
        # 값이 분산된 경우 (낮은 신뢰도)
        value_counts = pd.Series([3, 3, 2, 2])
        confidence = self.analyzer._calculate_confidence(value_counts, 10)
        self.assertLess(confidence, 0.5)
    
    def test_analyze_comparison_results(self):
        """비교 결과 분석 테스트"""
        # 테스트 데이터 생성
        data = {
            'parameter_name': ['PARAM_001'] * 5 + ['PARAM_002'] * 5,
            'default_value': ['100'] * 4 + ['200'] + ['300'] * 5,
            'file_name': ['file1', 'file2', 'file3', 'file4', 'file5'] * 2
        }
        df = pd.DataFrame(data)
        file_names = ['file1', 'file2', 'file3', 'file4', 'file5']
        
        # 분석 실행
        candidates = self.analyzer.analyze_comparison_results(df, file_names)
        
        # 검증
        self.assertEqual(len(candidates), 1)  # PARAM_001만 80% 이상
        self.assertEqual(candidates[0].parameter_name, 'PARAM_001')
        self.assertEqual(candidates[0].default_value, '100')
        self.assertEqual(candidates[0].occurrence_count, 4)

class TestComparisonEngine(unittest.TestCase):
    """비교 엔진 테스트"""
    
    def setUp(self):
        self.engine = OptimizedComparisonEngine(chunk_size=1000)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # 임시 파일 정리
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_functionality(self):
        """캐시 기능 테스트"""
        cache = ComparisonCache(max_size=2)
        
        # 캐시 저장
        df1 = pd.DataFrame({'a': [1, 2]})
        cache.set(['file1.csv', 'file2.csv'], df1)
        
        # 캐시 조회
        result = cache.get(['file1.csv', 'file2.csv'])
        self.assertIsNotNone(result)
        pd.testing.assert_frame_equal(result, df1)
        
        # 다른 순서로도 조회 가능 (정렬됨)
        result = cache.get(['file2.csv', 'file1.csv'])
        self.assertIsNotNone(result)
    
    def test_file_comparison(self):
        """파일 비교 테스트"""
        # 테스트 파일 생성
        file1_path = os.path.join(self.temp_dir, 'test1.csv')
        file2_path = os.path.join(self.temp_dir, 'test2.csv')
        
        df1 = pd.DataFrame({
            'parameter_name': ['PARAM_001', 'PARAM_002', 'PARAM_003'],
            'default_value': ['100', '200', '300']
        })
        df2 = pd.DataFrame({
            'parameter_name': ['PARAM_001', 'PARAM_002', 'PARAM_003'],
            'default_value': ['100', '250', '300']  # PARAM_002가 다름
        })
        
        df1.to_csv(file1_path, index=False)
        df2.to_csv(file2_path, index=False)
        
        # 비교 실행
        result = self.engine.compare_files([file1_path, file2_path])
        
        # 검증
        self.assertFalse(result.empty)
        self.assertIn('is_different', result.columns)
        
        # 차이점 요약
        summary = self.engine.get_difference_summary(result)
        self.assertEqual(summary['total_parameters'], 3)
        self.assertEqual(summary['different_parameters'], 1)  # PARAM_002

class TestQCSystem(unittest.TestCase):
    """QC 시스템 테스트"""
    
    def setUp(self):
        self.qc_system = UnifiedQCSystem()
        self.validator = QCValidator()
    
    def test_missing_value_detection(self):
        """누락 값 검출 테스트"""
        # 테스트 데이터
        df = pd.DataFrame({
            'parameter_name': ['PARAM_001', 'PARAM_002', None],
            'default_value': ['100', '', '300']
        })
        
        # 검증 실행
        issues = self.validator._check_missing_values(df)
        
        # 검증
        self.assertGreater(len(issues), 0)
        missing_issues = [i for i in issues if i.issue_type == "누락값"]
        self.assertGreater(len(missing_issues), 0)
    
    def test_unified_qc_execution(self):
        """통합 QC 실행 테스트"""
        # 테스트 데이터
        df = pd.DataFrame({
            'parameter_name': ['PARAM_001', 'PARAM_002', 'PARAM_003'],
            'default_value': ['100', '200', '300'],
            'min_spec': ['50', '150', '250'],
            'max_spec': ['150', '250', '350']
        })
        
        # QC 실행
        result = self.qc_system.perform_qc(df, 1, mode=QCMode.BASIC)
        
        # 검증
        self.assertEqual(result.total_parameters, 3)
        self.assertGreaterEqual(result.passed_count, 0)
        self.assertIsInstance(result.pass_rate, float)

def run_tests():
    """테스트 실행"""
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestModeManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCandidateAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestComparisonEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestQCSystem))
    
    # 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    print(f"실행: {result.testsRun}개")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}개")
    print(f"실패: {len(result.failures)}개")
    print(f"오류: {len(result.errors)}개")
    
    if result.wasSuccessful():
        print("\n✅ 모든 테스트가 성공했습니다!")
    else:
        print("\n❌ 일부 테스트가 실패했습니다.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)