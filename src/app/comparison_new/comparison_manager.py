"""
비교 기능들을 통합 관리하는 매니저
"""

import tkinter as tk
from tkinter import ttk
from .comparison_strategies import SimpleComparison, EnhancedComparison, AdvancedComparison


class ComparisonManager:
    """비교 기능들을 통합 관리하는 클래스"""
    
    def __init__(self, manager):
        """
        Args:
            manager: DBManager 인스턴스 참조
        """
        self.manager = manager
        self.comparison_strategies = {}
        self.current_strategy = None
        self.comparison_notebook = None
        self.file_data = []
    
    def initialize_comparison_tabs(self, parent_notebook):
        """비교 탭들을 초기화합니다."""
        self.comparison_notebook = parent_notebook
        
        # 각 비교 전략 인스턴스 생성
        self.comparison_strategies = {
            'simple': SimpleComparison(self.manager),
            'enhanced': EnhancedComparison(self.manager), 
            'advanced': AdvancedComparison(self.manager)
        }
        
        # 탭 생성
        self._create_comparison_tabs()
        
        # 기본 전략 설정
        self.current_strategy = self.comparison_strategies['simple']
    
    def _create_comparison_tabs(self):
        """비교 탭들을 생성합니다."""
        # 간단 비교 탭
        simple_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(simple_tab, text="기본 비교")
        self.comparison_strategies['simple'].create_ui(simple_tab)
        
        # 향상된 비교 탭  
        enhanced_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(enhanced_tab, text="향상된 비교")
        self.comparison_strategies['enhanced'].create_ui(enhanced_tab)
        
        # 고급 비교 탭
        advanced_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(advanced_tab, text="고급 분석")
        self.comparison_strategies['advanced'].create_ui(advanced_tab)
        
        # 탭 변경 이벤트 바인딩
        self.comparison_notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def on_tab_changed(self, event):
        """탭 변경 시 호출"""
        try:
            selected_tab = self.comparison_notebook.index(self.comparison_notebook.select())
            
            strategy_names = list(self.comparison_strategies.keys())
            if 0 <= selected_tab < len(strategy_names):
                strategy_name = strategy_names[selected_tab]
                self.current_strategy = self.comparison_strategies[strategy_name]
                
                # 현재 데이터로 새 전략 업데이트
                if self.file_data:
                    self.update_comparison_data(self.file_data)
                    
        except Exception as e:
            self.manager.update_log(f"탭 변경 처리 오류: {str(e)}")
    
    def load_comparison_data(self, file_data):
        """비교할 파일 데이터를 로드합니다."""
        self.file_data = file_data
        self.update_comparison_data(file_data)
    
    def update_comparison_data(self, file_data):
        """모든 비교 전략의 데이터를 업데이트합니다."""
        try:
            for strategy_name, strategy in self.comparison_strategies.items():
                # 각 전략별로 데이터 처리
                processed_data = strategy.process_data(file_data)
                
                # 뷰 업데이트
                strategy.comparison_data = processed_data
                strategy.update_view(processed_data)
            
            self.manager.update_log(f"{len(file_data)}개 파일의 비교 분석이 완료되었습니다.")
            
        except Exception as e:
            self.manager.update_log(f"비교 데이터 업데이트 실패: {str(e)}")
    
    def get_current_comparison_data(self):
        """현재 선택된 전략의 비교 데이터를 반환합니다."""
        if self.current_strategy and hasattr(self.current_strategy, 'comparison_data'):
            return self.current_strategy.comparison_data
        return None
    
    def export_comparison_results(self, filename=None):
        """현재 비교 결과를 파일로 내보냅니다."""
        if not self.current_strategy:
            self.manager.update_log("활성화된 비교 전략이 없습니다.")
            return False
        
        try:
            comparison_data = self.get_current_comparison_data()
            if comparison_data is None or comparison_data.empty:
                self.manager.update_log("내보낼 비교 데이터가 없습니다.")
                return False
            
            if filename is None:
                from tkinter import filedialog
                filename = filedialog.asksaveasfilename(
                    title="비교 결과 내보내기",
                    defaultextension=".xlsx",
                    filetypes=[
                        ("Excel 파일", "*.xlsx"),
                        ("CSV 파일", "*.csv"),
                        ("텍스트 파일", "*.txt")
                    ]
                )
            
            if filename:
                if filename.endswith('.xlsx'):
                    comparison_data.to_excel(filename, index=False)
                elif filename.endswith('.csv'):
                    comparison_data.to_csv(filename, index=False, encoding='utf-8-sig')
                else:
                    comparison_data.to_csv(filename, index=False, encoding='utf-8-sig', sep='\\t')
                
                self.manager.update_log(f"비교 결과가 {filename}으로 내보내졌습니다.")
                return True
                
        except Exception as e:
            self.manager.update_log(f"비교 결과 내보내기 실패: {str(e)}")
            return False
    
    def search_comparison_data(self, search_term):
        """비교 데이터에서 검색합니다."""
        if self.current_strategy:
            # 현재 전략의 검색 기능 활용
            if hasattr(self.current_strategy, 'search_var'):
                self.current_strategy.search_var.set(search_term)
                self.current_strategy.on_search_changed()
    
    def get_comparison_statistics(self):
        """비교 결과 통계를 반환합니다."""
        comparison_data = self.get_current_comparison_data()
        if comparison_data is None or comparison_data.empty:
            return {}
        
        stats = {
            'total_items': len(comparison_data),
            'strategy_name': type(self.current_strategy).__name__
        }
        
        # 전략별 특화 통계
        if 'Difference' in comparison_data.columns:
            different_count = len(comparison_data[comparison_data['Difference'] == 'Different'])
            stats['different_items'] = different_count
            stats['same_items'] = stats['total_items'] - different_count
            stats['difference_rate'] = (different_count / stats['total_items']) * 100 if stats['total_items'] > 0 else 0
        
        if 'Severity' in comparison_data.columns:
            severity_counts = comparison_data['Severity'].value_counts().to_dict()
            stats['severity_distribution'] = severity_counts
        
        if 'Confidence' in comparison_data.columns:
            avg_confidence = comparison_data['Confidence'].mean()
            stats['average_confidence'] = avg_confidence
        
        return stats
    
    def refresh_equipment_types(self):
        """모든 비교 전략의 장비 타입을 새로고침합니다."""
        for strategy in self.comparison_strategies.values():
            if hasattr(strategy, 'load_equipment_types'):
                strategy.load_equipment_types()
    
    def set_performance_filter(self, performance_only=False):
        """성능 파라미터 필터를 설정합니다."""
        for strategy in self.comparison_strategies.values():
            if hasattr(strategy, 'performance_only'):
                strategy.performance_only.set(performance_only)
                if hasattr(strategy, 'on_filter_changed'):
                    strategy.on_filter_changed()
    
    def clear_all_data(self):
        """모든 비교 데이터를 지웁니다."""
        self.file_data = []
        for strategy in self.comparison_strategies.values():
            strategy.comparison_data = None
            strategy.update_view(None)