"""
Mother DB 관리자 클래스
Mother DB 설정, 관리, 분석을 위한 최적화된 워크플로우 제공
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import Counter
import sqlite3

@dataclass
class MotherDBCandidate:
    """Mother DB 후보 항목"""
    parameter_name: str
    default_value: str
    occurrence_count: int
    total_files: int
    confidence_score: float
    source_files: List[str]
    min_spec: Optional[str] = None
    max_spec: Optional[str] = None
    
    @property
    def occurrence_rate(self) -> float:
        """발생률 계산"""
        return self.occurrence_count / self.total_files if self.total_files > 0 else 0

class CandidateAnalyzer:
    """Mother DB 후보 분석기"""
    
    def __init__(self, min_occurrence_rate: float = 0.8, confidence_threshold: float = 0.7):
        """
        초기화
        
        Args:
            min_occurrence_rate: 최소 발생률 (기본 80%)
            confidence_threshold: 최소 신뢰도 (기본 70%)
        """
        self.min_occurrence_rate = min_occurrence_rate
        self.confidence_threshold = confidence_threshold
    
    def analyze_comparison_results(self, comparison_data: pd.DataFrame, file_names: List[str]) -> List[MotherDBCandidate]:
        """
        비교 결과에서 Mother DB 후보 자동 분석
        
        Args:
            comparison_data: 비교 데이터프레임
            file_names: 비교한 파일 이름 리스트
            
        Returns:
            Mother DB 후보 리스트
        """
        candidates = []
        total_files = len(file_names)
        
        # 파라미터별로 그룹화
        grouped = comparison_data.groupby('parameter_name')
        
        for param_name, group in grouped:
            # 값들의 분포 분석
            value_counts = group['default_value'].value_counts()
            
            # 가장 많이 나타난 값
            most_common_value = value_counts.index[0]
            occurrence_count = value_counts.iloc[0]
            
            # 발생률 계산
            occurrence_rate = occurrence_count / total_files
            
            # 신뢰도 계산 (값의 일관성 기반)
            confidence_score = self._calculate_confidence(value_counts, total_files)
            
            # 후보 조건 확인
            if occurrence_rate >= self.min_occurrence_rate and confidence_score >= self.confidence_threshold:
                # 소스 파일 찾기
                source_files = group[group['default_value'] == most_common_value]['file_name'].tolist()
                
                # min/max 스펙 추출
                min_spec = group['min_spec'].mode().iloc[0] if 'min_spec' in group.columns and not group['min_spec'].empty else None
                max_spec = group['max_spec'].mode().iloc[0] if 'max_spec' in group.columns and not group['max_spec'].empty else None
                
                candidate = MotherDBCandidate(
                    parameter_name=param_name,
                    default_value=most_common_value,
                    occurrence_count=occurrence_count,
                    total_files=total_files,
                    confidence_score=confidence_score,
                    source_files=source_files,
                    min_spec=min_spec,
                    max_spec=max_spec
                )
                candidates.append(candidate)
        
        # 신뢰도 순으로 정렬
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return candidates
    
    def _calculate_confidence(self, value_counts: pd.Series, total_files: int) -> float:
        """
        신뢰도 계산
        
        Args:
            value_counts: 값별 카운트
            total_files: 전체 파일 수
            
        Returns:
            신뢰도 점수 (0~1)
        """
        if len(value_counts) == 0:
            return 0.0
        
        # 가장 많이 나타난 값의 비율
        max_count = value_counts.iloc[0]
        dominance_ratio = max_count / value_counts.sum()
        
        # 값의 다양성 (엔트로피 기반)
        probabilities = value_counts / value_counts.sum()
        entropy = -sum(p * np.log2(p) if p > 0 else 0 for p in probabilities)
        max_entropy = np.log2(len(value_counts)) if len(value_counts) > 1 else 1
        normalized_entropy = 1 - (entropy / max_entropy if max_entropy > 0 else 0)
        
        # 종합 신뢰도 (지배율 70%, 일관성 30%)
        confidence = 0.7 * dominance_ratio + 0.3 * normalized_entropy
        
        return min(max(confidence, 0.0), 1.0)

class ConflictResolver:
    """Mother DB 충돌 해결기"""
    
    def __init__(self, db_schema):
        """
        초기화
        
        Args:
            db_schema: 데이터베이스 스키마 객체
        """
        self.db_schema = db_schema
    
    def detect_conflicts(self, candidates: List[MotherDBCandidate], equipment_type_id: int) -> List[Dict]:
        """
        기존 DB와의 충돌 감지
        
        Args:
            candidates: Mother DB 후보 리스트
            equipment_type_id: 장비 유형 ID
            
        Returns:
            충돌 정보 리스트
        """
        conflicts = []
        
        # 기존 DB 데이터 조회
        existing_params = self._get_existing_parameters(equipment_type_id)
        
        for candidate in candidates:
            if candidate.parameter_name in existing_params:
                existing = existing_params[candidate.parameter_name]
                
                # 값이 다른 경우 충돌
                if existing['default_value'] != candidate.default_value:
                    conflicts.append({
                        'parameter_name': candidate.parameter_name,
                        'new_value': candidate.default_value,
                        'existing_value': existing['default_value'],
                        'new_confidence': candidate.confidence_score,
                        'existing_confidence': existing.get('confidence_score', 0),
                        'resolution': self._suggest_resolution(candidate, existing)
                    })
        
        return conflicts
    
    def _get_existing_parameters(self, equipment_type_id: int) -> Dict:
        """기존 파라미터 조회"""
        params = {}
        
        try:
            conn = sqlite3.connect(self.db_schema.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT parameter_name, default_value, confidence_score
                FROM Default_DB_Values
                WHERE equipment_type_id = ?
            ''', (equipment_type_id,))
            
            for row in cursor.fetchall():
                params[row[0]] = {
                    'default_value': row[1],
                    'confidence_score': row[2] if row[2] else 0
                }
            
            conn.close()
        except Exception as e:
            print(f"기존 파라미터 조회 중 오류: {e}")
        
        return params
    
    def _suggest_resolution(self, new_item: MotherDBCandidate, existing_item: Dict) -> str:
        """충돌 해결 방법 제안"""
        if new_item.confidence_score > existing_item.get('confidence_score', 0) * 1.2:
            return "UPDATE"  # 새 값으로 업데이트
        elif new_item.confidence_score < existing_item.get('confidence_score', 0) * 0.8:
            return "KEEP"    # 기존 값 유지
        else:
            return "REVIEW"  # 수동 검토 필요
    
    def auto_resolve(self, conflicts: List[Dict]) -> List[Dict]:
        """
        충돌 자동 해결
        
        Args:
            conflicts: 충돌 정보 리스트
            
        Returns:
            해결된 충돌 리스트
        """
        resolved = []
        
        for conflict in conflicts:
            if conflict['resolution'] == "UPDATE":
                conflict['action'] = "update"
                conflict['final_value'] = conflict['new_value']
            elif conflict['resolution'] == "KEEP":
                conflict['action'] = "skip"
                conflict['final_value'] = conflict['existing_value']
            else:
                # REVIEW인 경우 신뢰도가 높은 것 선택
                if conflict['new_confidence'] >= conflict['existing_confidence']:
                    conflict['action'] = "update"
                    conflict['final_value'] = conflict['new_value']
                else:
                    conflict['action'] = "skip"
                    conflict['final_value'] = conflict['existing_value']
            
            resolved.append(conflict)
        
        return resolved

class MotherDBManager:
    """Mother DB 통합 관리자"""
    
    def __init__(self, db_schema):
        """
        초기화
        
        Args:
            db_schema: 데이터베이스 스키마 객체
        """
        self.db_schema = db_schema
        self.candidate_analyzer = CandidateAnalyzer()
        self.conflict_resolver = ConflictResolver(db_schema)
    
    def quick_setup_mother_db(self, comparison_data: pd.DataFrame, file_names: List[str], equipment_type_id: int) -> Dict:
        """
        Mother DB 빠른 설정 (3단계 프로세스)
        
        Args:
            comparison_data: 비교 데이터
            file_names: 파일 이름 리스트
            equipment_type_id: 장비 유형 ID
            
        Returns:
            설정 결과 정보
        """
        result = {
            'total_candidates': 0,
            'selected_count': 0,
            'conflict_count': 0,
            'saved_count': 0,
            'errors': []
        }
        
        try:
            # 1단계: 자동 후보 분석
            candidates = self.candidate_analyzer.analyze_comparison_results(comparison_data, file_names)
            result['total_candidates'] = len(candidates)
            
            # 2단계: 충돌 감지 및 해결
            conflicts = self.conflict_resolver.detect_conflicts(candidates, equipment_type_id)
            result['conflict_count'] = len(conflicts)
            
            if conflicts:
                resolved_conflicts = self.conflict_resolver.auto_resolve(conflicts)
                # 해결된 충돌 적용
                for conflict in resolved_conflicts:
                    if conflict['action'] == 'update':
                        # 해당 candidate 업데이트
                        for candidate in candidates:
                            if candidate.parameter_name == conflict['parameter_name']:
                                candidate.default_value = conflict['final_value']
                                break
            
            # 3단계: 일괄 저장
            saved_count = self._batch_save_to_mother_db(candidates, equipment_type_id)
            result['saved_count'] = saved_count
            result['selected_count'] = len(candidates)
            
        except Exception as e:
            result['errors'].append(str(e))
        
        return result
    
    def _batch_save_to_mother_db(self, candidates: List[MotherDBCandidate], equipment_type_id: int) -> int:
        """
        Mother DB에 일괄 저장
        
        Args:
            candidates: 저장할 후보 리스트
            equipment_type_id: 장비 유형 ID
            
        Returns:
            저장된 항목 수
        """
        saved_count = 0
        
        try:
            conn = sqlite3.connect(self.db_schema.db_path)
            cursor = conn.cursor()
            
            for candidate in candidates:
                try:
                    # UPSERT 작업 (있으면 업데이트, 없으면 삽입)
                    cursor.execute('''
                        INSERT OR REPLACE INTO Default_DB_Values 
                        (equipment_type_id, parameter_name, default_value, min_spec, max_spec,
                         occurrence_count, total_files, confidence_score, source_files)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        equipment_type_id,
                        candidate.parameter_name,
                        candidate.default_value,
                        candidate.min_spec,
                        candidate.max_spec,
                        candidate.occurrence_count,
                        candidate.total_files,
                        candidate.confidence_score,
                        ','.join(candidate.source_files)
                    ))
                    saved_count += 1
                except Exception as e:
                    print(f"파라미터 {candidate.parameter_name} 저장 실패: {e}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Mother DB 저장 중 오류: {e}")
        
        return saved_count
    
    def analyze_mother_db_status(self, equipment_type_id: int) -> Dict:
        """
        Mother DB 상태 분석
        
        Args:
            equipment_type_id: 장비 유형 ID
            
        Returns:
            상태 분석 결과
        """
        status = {
            'total_parameters': 0,
            'high_confidence_count': 0,
            'low_confidence_count': 0,
            'average_confidence': 0,
            'coverage_rate': 0,
            'parameter_groups': {}
        }
        
        try:
            conn = sqlite3.connect(self.db_schema.db_path)
            cursor = conn.cursor()
            
            # 전체 파라미터 수
            cursor.execute('''
                SELECT COUNT(*), AVG(confidence_score)
                FROM Default_DB_Values
                WHERE equipment_type_id = ?
            ''', (equipment_type_id,))
            
            row = cursor.fetchone()
            status['total_parameters'] = row[0] if row[0] else 0
            status['average_confidence'] = row[1] if row[1] else 0
            
            # 신뢰도별 카운트
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN confidence_score >= 0.8 THEN 1 ELSE 0 END) as high,
                    SUM(CASE WHEN confidence_score < 0.5 THEN 1 ELSE 0 END) as low
                FROM Default_DB_Values
                WHERE equipment_type_id = ?
            ''', (equipment_type_id,))
            
            row = cursor.fetchone()
            status['high_confidence_count'] = row[0] if row[0] else 0
            status['low_confidence_count'] = row[1] if row[1] else 0
            
            conn.close()
            
        except Exception as e:
            print(f"Mother DB 상태 분석 중 오류: {e}")
        
        return status