"""
QC 점수 계산 시스템
"""

from typing import Dict, List, Any
import pandas as pd
from .base_qc import QCResult, QCSeverity, QCCategory


class QCScoringSystem:
    """QC 점수 계산을 담당하는 클래스"""
    
    def __init__(self):
        # 기본 심각도별 가중치
        self.severity_weights = {
            QCSeverity.LOW: 0.5,
            QCSeverity.MEDIUM: 2.0,
            QCSeverity.HIGH: 5.0,
            QCSeverity.CRITICAL: 10.0
        }
        
        # 카테고리별 가중치 (중요도에 따라)
        self.category_weights = {
            QCCategory.PERFORMANCE: 1.5,      # 성능 파라미터는 더 중요
            QCCategory.ACCURACY: 1.2,         # 정확도도 중요
            QCCategory.COMPLETENESS: 1.0,     # 완성도는 기본
            QCCategory.CONSISTENCY: 0.8,      # 일관성은 상대적으로 덜 중요
            QCCategory.NAMING: 0.5            # 명명 규칙은 가장 덜 중요
        }
        
        # 최대 감점 한도 (카테고리별)
        self.max_deductions = {
            QCCategory.PERFORMANCE: 30.0,
            QCCategory.ACCURACY: 25.0,
            QCCategory.COMPLETENESS: 20.0,
            QCCategory.CONSISTENCY: 15.0,
            QCCategory.NAMING: 10.0
        }
    
    def calculate_overall_score(self, qc_result: QCResult) -> float:
        """전체 QC 점수를 계산합니다."""
        if not qc_result.issues:
            return 100.0
        
        # 카테고리별 점수 계산
        category_scores = self.calculate_category_scores(qc_result)
        
        # 가중 평균으로 전체 점수 계산
        total_weight = sum(self.category_weights.values())
        weighted_sum = sum(
            score * self.category_weights[category] 
            for category, score in category_scores.items()
        )
        
        overall_score = weighted_sum / total_weight
        return max(0.0, min(100.0, overall_score))
    
    def calculate_category_scores(self, qc_result: QCResult) -> Dict[QCCategory, float]:
        """카테고리별 점수를 계산합니다."""
        category_scores = {}
        
        for category in QCCategory:
            category_issues = qc_result.get_issues_by_category(category)
            
            if not category_issues:
                category_scores[category] = 100.0
                continue
            
            # 해당 카테고리의 총 감점 계산
            total_deduction = 0.0
            for issue in category_issues:
                base_deduction = self.severity_weights[issue.severity]
                # 카테고리 가중치 적용
                weighted_deduction = base_deduction * self.category_weights[category]
                total_deduction += weighted_deduction
            
            # 최대 감점 한도 적용
            max_deduction = self.max_deductions[category]
            actual_deduction = min(total_deduction, max_deduction)
            
            # 점수 계산 (100점에서 감점)
            category_score = max(0.0, 100.0 - actual_deduction)
            category_scores[category] = category_score
        
        return category_scores
    
    def calculate_severity_impact(self, qc_result: QCResult) -> Dict[QCSeverity, Dict[str, Any]]:
        """심각도별 영향도 분석"""
        severity_impact = {}
        
        for severity in QCSeverity:
            severity_issues = qc_result.get_issues_by_severity(severity)
            
            impact_data = {
                'count': len(severity_issues),
                'percentage': len(severity_issues) / len(qc_result.issues) * 100 if qc_result.issues else 0,
                'total_deduction': sum(self.severity_weights[issue.severity] for issue in severity_issues),
                'categories': {}
            }
            
            # 해당 심각도 내 카테고리 분포
            for category in QCCategory:
                category_count = len([
                    issue for issue in severity_issues 
                    if issue.category == category
                ])
                impact_data['categories'][category] = category_count
            
            severity_impact[severity] = impact_data
        
        return severity_impact
    
    def get_score_interpretation(self, score: float) -> Dict[str, str]:
        """점수 해석 및 등급 반환"""
        if score >= 95:
            grade = "A+"
            interpretation = "최우수"
            description = "매우 높은 품질의 데이터로 즉시 사용 가능합니다."
            color = "#00AA00"
        elif score >= 90:
            grade = "A"
            interpretation = "우수"
            description = "높은 품질의 데이터로 대부분의 용도에 적합합니다."
            color = "#44AA44"
        elif score >= 85:
            grade = "B+"
            interpretation = "양호"
            description = "양호한 품질이지만 일부 개선이 권장됩니다."
            color = "#88AA00"
        elif score >= 80:
            grade = "B"
            interpretation = "보통"
            description = "보통 품질로 사용 전 검토가 필요합니다."
            color = "#AAAA00"
        elif score >= 70:
            grade = "C"
            interpretation = "미흡"
            description = "품질이 미흡하여 개선이 필요합니다."
            color = "#AA8800"
        elif score >= 60:
            grade = "D"
            interpretation = "불량"
            description = "품질이 낮아 상당한 개선이 필요합니다."
            color = "#AA4400"
        else:
            grade = "F"
            interpretation = "매우 불량"
            description = "품질이 매우 낮아 전면적인 검토가 필요합니다."
            color = "#AA0000"
        
        return {
            'grade': grade,
            'interpretation': interpretation,
            'description': description,
            'color': color
        }
    
    def calculate_improvement_potential(self, qc_result: QCResult) -> Dict[str, Any]:
        """개선 가능성 분석"""
        if not qc_result.issues:
            return {
                'max_possible_score': 100.0,
                'current_score': 100.0,
                'improvement_potential': 0.0,
                'recommendations': ["데이터가 이미 완벽합니다."]
            }
        
        current_score = self.calculate_overall_score(qc_result)
        
        # 각 심각도별로 해결했을 때의 점수 증가 계산
        improvements = {}
        
        for severity in QCSeverity:
            severity_issues = qc_result.get_issues_by_severity(severity)
            if severity_issues:
                # 해당 심각도 이슈들을 제거했을 때 점수
                temp_result = QCResult(qc_result.total_items)
                remaining_issues = [
                    issue for issue in qc_result.issues 
                    if issue.severity != severity
                ]
                for issue in remaining_issues:
                    temp_result.add_issue(issue)
                
                new_score = self.calculate_overall_score(temp_result)
                improvement = new_score - current_score
                
                improvements[severity] = {
                    'issue_count': len(severity_issues),
                    'score_improvement': improvement,
                    'effort_score': self._calculate_effort_score(severity)
                }
        
        # 효율성 분석 (노력 대비 개선 효과)
        efficiency_ranking = []
        for severity, data in improvements.items():
            if data['score_improvement'] > 0:
                efficiency = data['score_improvement'] / data['effort_score']
                efficiency_ranking.append((severity, efficiency, data))
        
        efficiency_ranking.sort(key=lambda x: x[1], reverse=True)
        
        # 권장사항 생성
        recommendations = []
        if efficiency_ranking:
            top_severity = efficiency_ranking[0][0]
            recommendations.append(f"가장 효율적인 개선: {top_severity.value} 심각도 이슈들을 우선 해결하세요.")
            
            if len(efficiency_ranking) > 1:
                second_severity = efficiency_ranking[1][0]
                recommendations.append(f"다음 개선 대상: {second_severity.value} 심각도 이슈들을 해결하세요.")
        
        max_possible_score = 100.0  # 모든 이슈를 해결했을 때
        improvement_potential = max_possible_score - current_score
        
        return {
            'max_possible_score': max_possible_score,
            'current_score': current_score,
            'improvement_potential': improvement_potential,
            'severity_improvements': improvements,
            'efficiency_ranking': [(s.value, e, d) for s, e, d in efficiency_ranking],
            'recommendations': recommendations
        }
    
    def _calculate_effort_score(self, severity: QCSeverity) -> float:
        """심각도별 해결 노력 점수 (높을수록 해결하기 어려움)"""
        effort_scores = {
            QCSeverity.LOW: 1.0,      # 쉬움
            QCSeverity.MEDIUM: 2.0,   # 보통
            QCSeverity.HIGH: 4.0,     # 어려움
            QCSeverity.CRITICAL: 8.0  # 매우 어려움
        }
        return effort_scores.get(severity, 1.0)
    
    def generate_score_summary(self, qc_result: QCResult) -> str:
        """점수 요약 텍스트 생성"""
        overall_score = self.calculate_overall_score(qc_result)
        interpretation = self.get_score_interpretation(overall_score)
        category_scores = self.calculate_category_scores(qc_result)
        
        summary = f"""
QC 점수 요약
===========

전체 점수: {overall_score:.1f}점 ({interpretation['grade']}) - {interpretation['interpretation']}
{interpretation['description']}

카테고리별 점수:
"""
        
        for category, score in category_scores.items():
            cat_interpretation = self.get_score_interpretation(score)
            summary += f"• {category.value}: {score:.1f}점 ({cat_interpretation['grade']})\\n"
        
        # 개선 가능성 정보 추가
        improvement = self.calculate_improvement_potential(qc_result)
        if improvement['improvement_potential'] > 0:
            summary += f"\\n개선 가능성: +{improvement['improvement_potential']:.1f}점\\n"
            summary += "\\n권장 개선 순서:\\n"
            for rec in improvement['recommendations']:
                summary += f"• {rec}\\n"
        
        return summary
    
    def export_detailed_scoring(self, qc_result: QCResult) -> pd.DataFrame:
        """상세 점수 정보를 DataFrame으로 내보내기"""
        if not qc_result.issues:
            return pd.DataFrame()
        
        scoring_data = []
        
        for issue in qc_result.issues:
            base_deduction = self.severity_weights[issue.severity]
            category_weight = self.category_weights[issue.category]
            weighted_deduction = base_deduction * category_weight
            
            scoring_data.append({
                'Category': issue.category.value,
                'Severity': issue.severity.value,
                'Message': issue.message,
                'Module': issue.item_info.get('Module', ''),
                'Part': issue.item_info.get('Part', ''),
                'Item_Name': issue.item_info.get('Item_Name', ''),
                'Base_Deduction': base_deduction,
                'Category_Weight': category_weight,
                'Weighted_Deduction': weighted_deduction,
                'Timestamp': issue.timestamp
            })
        
        return pd.DataFrame(scoring_data)