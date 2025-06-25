"""
QC 보고서 생성 기능
"""

import pandas as pd
from typing import Dict, List, Any, Optional
import os
from datetime import datetime
from .base_qc import QCResult, QCSeverity, QCCategory
from .qc_scoring import QCScoringSystem


class QCReportGenerator:
    """QC 보고서 생성을 담당하는 클래스"""
    
    def __init__(self):
        self.scoring_system = QCScoringSystem()
    
    def generate_report(self, qc_result: QCResult, filename: str) -> bool:
        """QC 보고서를 생성합니다."""
        try:
            if filename.endswith('.xlsx'):
                return self._generate_excel_report(qc_result, filename)
            elif filename.endswith('.pdf'):
                return self._generate_pdf_report(qc_result, filename)
            else:
                # 기본적으로 Excel 형식으로 생성
                return self._generate_excel_report(qc_result, filename + '.xlsx')
        
        except Exception as e:
            print(f"보고서 생성 오류: {str(e)}")
            return False
    
    def _generate_excel_report(self, qc_result: QCResult, filename: str) -> bool:
        """Excel 형식의 보고서 생성"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 1. 요약 시트
                self._create_summary_sheet(qc_result, writer)
                
                # 2. 상세 이슈 시트
                self._create_issues_sheet(qc_result, writer)
                
                # 3. 통계 시트
                self._create_statistics_sheet(qc_result, writer)
                
                # 4. 점수 분석 시트
                self._create_scoring_sheet(qc_result, writer)
                
                # 5. 권장사항 시트
                self._create_recommendations_sheet(qc_result, writer)
            
            return True
        
        except Exception as e:
            print(f"Excel 보고서 생성 오류: {str(e)}")
            return False
    
    def _create_summary_sheet(self, qc_result: QCResult, writer: pd.ExcelWriter):
        """요약 시트 생성"""
        summary_data = []
        
        # 기본 정보
        overall_score = self.scoring_system.calculate_overall_score(qc_result)
        interpretation = self.scoring_system.get_score_interpretation(overall_score)
        summary_stats = qc_result.get_summary_stats()
        
        summary_data.extend([
            ['QC 검수 보고서', ''],
            ['생성 시간', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['검수 시간', summary_stats['timestamp'].strftime('%Y-%m-%d %H:%M:%S')],
            ['실행 시간', f"{summary_stats['execution_time']:.2f}초"],
            ['', ''],
            ['전체 점수', f"{overall_score:.1f}점"],
            ['등급', f"{interpretation['grade']} ({interpretation['interpretation']})"],
            ['해석', interpretation['description']],
            ['', ''],
            ['검수 대상', f"{summary_stats['total_items']}개 항목"],
            ['발견 이슈', f"{summary_stats['total_issues']}개"],
            ['', '']
        ])
        
        # 심각도별 통계
        summary_data.append(['심각도별 이슈 분포', ''])
        for severity, count in summary_stats['severity_distribution'].items():
            percentage = (count / summary_stats['total_issues'] * 100) if summary_stats['total_issues'] > 0 else 0
            summary_data.append([f"• {severity}", f"{count}개 ({percentage:.1f}%)"])
        
        summary_data.append(['', ''])
        
        # 카테고리별 통계
        summary_data.append(['카테고리별 이슈 분포', ''])
        for category, count in summary_stats['category_distribution'].items():
            percentage = (count / summary_stats['total_issues'] * 100) if summary_stats['total_issues'] > 0 else 0
            summary_data.append([f"• {category}", f"{count}개 ({percentage:.1f}%)"])
        
        # 카테고리별 점수
        category_scores = self.scoring_system.calculate_category_scores(qc_result)
        if category_scores:
            summary_data.append(['', ''])
            summary_data.append(['카테고리별 점수', ''])
            for category, score in category_scores.items():
                cat_interpretation = self.scoring_system.get_score_interpretation(score)
                summary_data.append([f"• {category.value}", f"{score:.1f}점 ({cat_interpretation['grade']})"])
        
        summary_df = pd.DataFrame(summary_data, columns=['항목', '값'])
        summary_df.to_excel(writer, sheet_name='요약', index=False)
    
    def _create_issues_sheet(self, qc_result: QCResult, writer: pd.ExcelWriter):
        """상세 이슈 시트 생성"""
        if not qc_result.issues:
            empty_df = pd.DataFrame({'메시지': ['발견된 이슈가 없습니다.']})
            empty_df.to_excel(writer, sheet_name='상세 이슈', index=False)
            return
        
        issues_data = []
        for i, issue in enumerate(qc_result.issues, 1):
            issues_data.append({
                '번호': i,
                '심각도': issue.severity.value,
                '카테고리': issue.category.value,
                '메시지': issue.message,
                '모듈': issue.item_info.get('Module', ''),
                '부품': issue.item_info.get('Part', ''),
                '항목명': issue.item_info.get('Item_Name', ''),
                '값': issue.item_info.get('Value', ''),
                '권장조치': issue.recommended_action,
                '점수영향': issue.score_impact,
                '발견시간': issue.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        issues_df = pd.DataFrame(issues_data)
        issues_df.to_excel(writer, sheet_name='상세 이슈', index=False)
    
    def _create_statistics_sheet(self, qc_result: QCResult, writer: pd.ExcelWriter):
        """통계 시트 생성"""
        stats_data = []
        summary_stats = qc_result.get_summary_stats()
        
        # 기본 통계
        stats_data.extend([
            ['기본 통계', ''],
            ['총 검수 항목', summary_stats['total_items']],
            ['발견된 이슈', summary_stats['total_issues']],
            ['이슈 발생률', f"{(summary_stats['total_issues']/summary_stats['total_items']*100):.2f}%" if summary_stats['total_items'] > 0 else "0%"],
            ['실행 시간', f"{summary_stats['execution_time']:.2f}초"],
            ['', '']
        ])
        
        # 심각도별 상세 통계
        severity_impact = self.scoring_system.calculate_severity_impact(qc_result)
        stats_data.append(['심각도별 상세 분석', ''])
        
        for severity, impact_data in severity_impact.items():
            stats_data.extend([
                [f"{severity.value} 심각도", ''],
                ['  이슈 수', impact_data['count']],
                ['  전체 비율', f"{impact_data['percentage']:.1f}%"],
                ['  총 감점', f"{impact_data['total_deduction']:.1f}점"],
                ['', '']
            ])
        
        # 개선 가능성 분석
        improvement = self.scoring_system.calculate_improvement_potential(qc_result)
        stats_data.extend([
            ['개선 가능성 분석', ''],
            ['현재 점수', f"{improvement['current_score']:.1f}점"],
            ['최대 가능 점수', f"{improvement['max_possible_score']:.1f}점"],
            ['개선 여지', f"{improvement['improvement_potential']:.1f}점"],
            ['', '']
        ])
        
        stats_df = pd.DataFrame(stats_data, columns=['항목', '값'])
        stats_df.to_excel(writer, sheet_name='통계 분석', index=False)
    
    def _create_scoring_sheet(self, qc_result: QCResult, writer: pd.ExcelWriter):
        """점수 분석 시트 생성"""
        # 상세 점수 분석 데이터
        scoring_df = self.scoring_system.export_detailed_scoring(qc_result)
        if not scoring_df.empty:
            scoring_df.to_excel(writer, sheet_name='점수 분석', index=False)
        else:
            empty_df = pd.DataFrame({'메시지': ['점수 분석 데이터가 없습니다.']})
            empty_df.to_excel(writer, sheet_name='점수 분석', index=False)
    
    def _create_recommendations_sheet(self, qc_result: QCResult, writer: pd.ExcelWriter):
        """권장사항 시트 생성"""
        recommendations_data = []
        
        # 전체적인 권장사항
        overall_score = self.scoring_system.calculate_overall_score(qc_result)
        interpretation = self.scoring_system.get_score_interpretation(overall_score)
        
        recommendations_data.extend([
            ['전체 권장사항', ''],
            ['현재 상태', interpretation['description']],
            ['', '']
        ])
        
        # 개선 우선순위
        improvement = self.scoring_system.calculate_improvement_potential(qc_result)
        if improvement['recommendations']:
            recommendations_data.append(['개선 우선순위', ''])
            for i, rec in enumerate(improvement['recommendations'], 1):
                recommendations_data.append([f"{i}.", rec])
            recommendations_data.append(['', ''])
        
        # 심각도별 권장사항
        summary_stats = qc_result.get_summary_stats()
        critical_count = summary_stats['severity_distribution'].get('Critical', 0)
        high_count = summary_stats['severity_distribution'].get('High', 0)
        medium_count = summary_stats['severity_distribution'].get('Medium', 0)
        low_count = summary_stats['severity_distribution'].get('Low', 0)
        
        recommendations_data.append(['심각도별 대응 방안', ''])
        
        if critical_count > 0:
            recommendations_data.extend([
                ['Critical 이슈', f"{critical_count}개"],
                ['대응 방안', '즉시 해결 필요. 시스템에 심각한 영향을 줄 수 있습니다.'],
                ['목표 기간', '24시간 이내'],
                ['', '']
            ])
        
        if high_count > 0:
            recommendations_data.extend([
                ['High 이슈', f"{high_count}개"],
                ['대응 방안', '우선적으로 해결 필요. 품질에 큰 영향을 줍니다.'],
                ['목표 기간', '1주일 이내'],
                ['', '']
            ])
        
        if medium_count > 0:
            recommendations_data.extend([
                ['Medium 이슈', f"{medium_count}개"],
                ['대응 방안', '계획적으로 해결. 점진적 개선이 필요합니다.'],
                ['목표 기간', '1개월 이내'],
                ['', '']
            ])
        
        if low_count > 0:
            recommendations_data.extend([
                ['Low 이슈', f"{low_count}개"],
                ['대응 방안', '여유가 있을 때 해결. 전체적인 품질 향상을 위해 개선.'],
                ['목표 기간', '3개월 이내'],
                ['', '']
            ])
        
        # 카테고리별 권장사항
        category_scores = self.scoring_system.calculate_category_scores(qc_result)
        recommendations_data.append(['카테고리별 개선 방안', ''])
        
        for category, score in category_scores.items():
            if score < 90:
                recommendations_data.extend([
                    [f"{category.value}", f"{score:.1f}점"],
                    ['개선 방안', self._get_category_recommendation(category, score)],
                    ['', '']
                ])
        
        recommendations_df = pd.DataFrame(recommendations_data, columns=['항목', '내용'])
        recommendations_df.to_excel(writer, sheet_name='권장사항', index=False)
    
    def _get_category_recommendation(self, category: QCCategory, score: float) -> str:
        """카테고리별 개선 권장사항 생성"""
        recommendations = {
            QCCategory.PERFORMANCE: {
                90: "성능 파라미터의 정확성을 높이기 위해 측정 방법과 기준값을 재검토하세요.",
                80: "중요 성능 지표들의 일관성을 확보하고 누락된 파라미터를 추가하세요.",
                70: "성능 파라미터 관리 프로세스를 전면 재검토하고 표준화하세요.",
                0: "성능 파라미터의 완전한 재설계가 필요합니다."
            },
            QCCategory.ACCURACY: {
                90: "일부 데이터의 정확도 검증을 강화하고 검증 절차를 개선하세요.",
                80: "데이터 입력 및 검증 프로세스를 점검하고 오류 방지 체계를 구축하세요.",
                70: "데이터 정확도 관리 시스템을 전면 개선하고 자동 검증 도구를 도입하세요.",
                0: "데이터 정확도 관리 체계의 근본적인 재구축이 필요합니다."
            },
            QCCategory.COMPLETENESS: {
                90: "누락된 데이터 항목들을 확인하고 보완하세요.",
                80: "데이터 완성도 체크리스트를 만들고 입력 프로세스를 개선하세요.",
                70: "데이터 수집 및 관리 프로세스를 재설계하고 완성도 모니터링을 강화하세요.",
                0: "데이터 수집 체계의 전면적인 재구축이 필요합니다."
            },
            QCCategory.CONSISTENCY: {
                90: "일부 불일치 항목들을 표준화하고 가이드라인을 명확히 하세요.",
                80: "데이터 표준화 규칙을 수립하고 일관성 검사 도구를 활용하세요.",
                70: "데이터 일관성 관리 프로세스를 재정비하고 자동화 도구를 도입하세요.",
                0: "데이터 일관성 관리 체계의 완전한 재설계가 필요합니다."
            },
            QCCategory.NAMING: {
                90: "명명 규칙의 일부 예외 사항들을 정리하고 가이드를 업데이트하세요.",
                80: "명명 규칙을 명확히 정의하고 팀 전체에 교육을 실시하세요.",
                70: "명명 규칙의 전면 재정비와 자동 검증 시스템 구축이 필요합니다.",
                0: "명명 체계의 완전한 재설계와 표준화가 필요합니다."
            }
        }
        
        category_recs = recommendations.get(category, {})
        
        # 점수 구간에 따른 권장사항 선택
        if score >= 90:
            return category_recs.get(90, "품질이 우수합니다. 현재 수준을 유지하세요.")
        elif score >= 80:
            return category_recs.get(80, "일부 개선이 필요합니다.")
        elif score >= 70:
            return category_recs.get(70, "상당한 개선이 필요합니다.")
        else:
            return category_recs.get(0, "전면적인 재검토가 필요합니다.")
    
    def _generate_pdf_report(self, qc_result: QCResult, filename: str) -> bool:
        """PDF 형식의 보고서 생성 (기본 구현)"""
        try:
            # PDF 생성을 위해서는 추가 라이브러리 (reportlab 등)가 필요
            # 현재는 텍스트 형식으로 저장
            text_filename = filename.replace('.pdf', '.txt')
            
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write(self._generate_text_report(qc_result))
            
            return True
        
        except Exception as e:
            print(f"PDF 보고서 생성 오류: {str(e)}")
            return False
    
    def _generate_text_report(self, qc_result: QCResult) -> str:
        """텍스트 형식의 보고서 생성"""
        overall_score = self.scoring_system.calculate_overall_score(qc_result)
        interpretation = self.scoring_system.get_score_interpretation(overall_score)
        summary_stats = qc_result.get_summary_stats()
        
        report = f"""
QC 검수 보고서
==============

생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
검수 시간: {summary_stats['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
실행 시간: {summary_stats['execution_time']:.2f}초

전체 결과
---------
전체 점수: {overall_score:.1f}점 ({interpretation['grade']}) - {interpretation['interpretation']}
{interpretation['description']}

검수 대상: {summary_stats['total_items']}개 항목
발견 이슈: {summary_stats['total_issues']}개

심각도별 이슈 분포
-----------------
"""
        
        for severity, count in summary_stats['severity_distribution'].items():
            percentage = (count / summary_stats['total_issues'] * 100) if summary_stats['total_issues'] > 0 else 0
            report += f"• {severity}: {count}개 ({percentage:.1f}%)\\n"
        
        report += "\\n카테고리별 이슈 분포\\n"
        report += "-" * 20 + "\\n"
        
        for category, count in summary_stats['category_distribution'].items():
            percentage = (count / summary_stats['total_issues'] * 100) if summary_stats['total_issues'] > 0 else 0
            report += f"• {category}: {count}개 ({percentage:.1f}%)\\n"
        
        # 카테고리별 점수
        category_scores = self.scoring_system.calculate_category_scores(qc_result)
        if category_scores:
            report += "\\n카테고리별 점수\\n"
            report += "-" * 15 + "\\n"
            for category, score in category_scores.items():
                cat_interpretation = self.scoring_system.get_score_interpretation(score)
                report += f"• {category.value}: {score:.1f}점 ({cat_interpretation['grade']})\\n"
        
        # 상세 이슈 목록 (상위 20개만)
        if qc_result.issues:
            report += "\\n주요 이슈 목록 (상위 20개)\\n"
            report += "-" * 25 + "\\n"
            
            # 심각도순으로 정렬
            sorted_issues = sorted(qc_result.issues, 
                                 key=lambda x: ['Critical', 'High', 'Medium', 'Low'].index(x.severity.value))
            
            for i, issue in enumerate(sorted_issues[:20], 1):
                report += f"{i:2d}. [{issue.severity.value}] {issue.category.value}: {issue.message}\\n"
                if issue.item_info.get('Module') or issue.item_info.get('Part') or issue.item_info.get('Item_Name'):
                    location = f"    위치: {issue.item_info.get('Module', '')}.{issue.item_info.get('Part', '')}.{issue.item_info.get('Item_Name', '')}"
                    report += location + "\\n"
                if issue.recommended_action:
                    report += f"    권장조치: {issue.recommended_action}\\n"
                report += "\\n"
        
        # 개선 권장사항
        improvement = self.scoring_system.calculate_improvement_potential(qc_result)
        if improvement['recommendations']:
            report += "개선 권장사항\\n"
            report += "-" * 12 + "\\n"
            for rec in improvement['recommendations']:
                report += f"• {rec}\\n"
        
        return report
    
    def generate_summary_report(self, qc_result: QCResult) -> str:
        """간단한 요약 보고서 생성"""
        overall_score = self.scoring_system.calculate_overall_score(qc_result)
        interpretation = self.scoring_system.get_score_interpretation(overall_score)
        summary_stats = qc_result.get_summary_stats()
        
        summary = f"""QC 검수 요약

점수: {overall_score:.1f}점 ({interpretation['grade']})
상태: {interpretation['interpretation']}
검수 항목: {summary_stats['total_items']}개
발견 이슈: {summary_stats['total_issues']}개

{interpretation['description']}"""
        
        return summary