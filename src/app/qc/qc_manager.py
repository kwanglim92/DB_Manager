"""
QC 기능들을 통합 관리하는 매니저
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from typing import Dict, List, Any, Optional
import threading
import time

from .qc_validators import StandardQCValidator, EnhancedQCValidator
from .base_qc import QCResult, QCSeverity, QCCategory
from .qc_scoring import QCScoringSystem
from .qc_reports import QCReportGenerator


class QCManager:
    """QC 기능들을 통합 관리하는 클래스"""
    
    def __init__(self, manager):
        """
        Args:
            manager: DBManager 인스턴스 참조
        """
        self.manager = manager
        self.validators = {}
        self.scoring_system = QCScoringSystem()
        self.report_generator = QCReportGenerator()
        
        # QC UI 요소들
        self.qc_frame = None
        self.results_tree = None
        self.progress_var = None
        self.progress_bar = None
        self.status_label = None
        
        # QC 결과 저장
        self.current_result: Optional[QCResult] = None
        self.qc_history: List[QCResult] = []
        
        self._initialize_validators()
    
    def _initialize_validators(self):
        """검증기들을 초기화합니다."""
        self.validators = {
            'standard': StandardQCValidator(),
            'enhanced': EnhancedQCValidator(self.manager.db_schema)
        }
    
    def create_qc_ui(self, parent_frame):
        """QC UI를 생성합니다."""
        self.qc_frame = ttk.LabelFrame(parent_frame, text="QC 검수 시스템", padding=10)
        self.qc_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 상단 컨트롤 프레임
        control_frame = ttk.Frame(self.qc_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # QC 모드 선택
        ttk.Label(control_frame, text="검수 모드:").grid(row=0, column=0, sticky="w", padx=5)
        self.qc_mode = tk.StringVar(value="enhanced")
        ttk.Radiobutton(control_frame, text="표준 검수", variable=self.qc_mode, 
                       value="standard").grid(row=0, column=1, padx=5)
        ttk.Radiobutton(control_frame, text="향상된 검수", variable=self.qc_mode, 
                       value="enhanced").grid(row=0, column=2, padx=5)
        
        # 장비 타입 선택 (향상된 검수용)
        ttk.Label(control_frame, text="장비 타입:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.equipment_var = tk.StringVar()
        self.equipment_combo = ttk.Combobox(control_frame, textvariable=self.equipment_var, width=20)
        self.equipment_combo.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        
        # 검수 실행 버튼
        ttk.Button(control_frame, text="QC 검수 실행", 
                  command=self.run_qc_check).grid(row=0, column=3, rowspan=2, padx=20, pady=5)
        
        # 진행률 표시
        progress_frame = ttk.Frame(self.qc_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=300)
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(progress_frame, text="준비")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # 결과 노트북
        self.results_notebook = ttk.Notebook(self.qc_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 요약 탭
        self._create_summary_tab()
        
        # 상세 결과 탭
        self._create_details_tab()
        
        # 통계 탭
        self._create_statistics_tab()
        
        # 장비 타입 목록 로드
        self.load_equipment_types()
    
    def _create_summary_tab(self):
        """요약 탭 생성"""
        summary_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(summary_frame, text="요약")
        
        # 점수 표시 프레임
        score_frame = ttk.LabelFrame(summary_frame, text="QC 점수", padding=10)
        score_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 전체 점수
        self.overall_score_label = ttk.Label(score_frame, text="전체 점수: -", 
                                           font=("Arial", 14, "bold"))
        self.overall_score_label.pack(pady=5)
        
        # 카테고리별 점수
        self.category_scores_frame = ttk.Frame(score_frame)
        self.category_scores_frame.pack(fill=tk.X, pady=5)
        
        # 심각도별 통계
        severity_frame = ttk.LabelFrame(summary_frame, text="심각도별 이슈", padding=10)
        severity_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.severity_labels = {}
        for i, severity in enumerate(QCSeverity):
            label = ttk.Label(severity_frame, text=f"{severity.value}: 0개")
            label.grid(row=0, column=i, padx=10, pady=5)
            self.severity_labels[severity] = label
        
        # 권장사항
        recommendation_frame = ttk.LabelFrame(summary_frame, text="권장사항", padding=10)
        recommendation_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.recommendation_text = tk.Text(recommendation_frame, wrap=tk.WORD, height=8)
        rec_scrollbar = ttk.Scrollbar(recommendation_frame, orient="vertical", 
                                    command=self.recommendation_text.yview)
        self.recommendation_text.configure(yscrollcommand=rec_scrollbar.set)
        
        self.recommendation_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rec_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_details_tab(self):
        """상세 결과 탭 생성"""
        details_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(details_frame, text="상세 결과")
        
        # 필터 프레임
        filter_frame = ttk.Frame(details_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 심각도 필터
        ttk.Label(filter_frame, text="심각도:").pack(side=tk.LEFT, padx=5)
        self.severity_filter = tk.StringVar(value="All")
        severity_combo = ttk.Combobox(filter_frame, textvariable=self.severity_filter, 
                                    values=["All"] + [s.value for s in QCSeverity], width=10)
        severity_combo.pack(side=tk.LEFT, padx=5)
        severity_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        # 카테고리 필터  
        ttk.Label(filter_frame, text="카테고리:").pack(side=tk.LEFT, padx=5)
        self.category_filter = tk.StringVar(value="All")
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_filter,
                                    values=["All"] + [c.value for c in QCCategory], width=12)
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        # 검색
        ttk.Label(filter_frame, text="검색:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # 결과 트리뷰
        columns = ['severity', 'category', 'message', 'module', 'part', 'item_name', 'value', 'action']
        headings = {
            'severity': '심각도',
            'category': '카테고리',
            'message': '메시지',
            'module': '모듈',
            'part': '부품',
            'item_name': '항목명',
            'value': '값',
            'action': '권장조치'
        }
        
        tree_frame = ttk.Frame(details_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.results_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # 컬럼 설정
        for col in columns:
            self.results_tree.heading(col, text=headings[col])
            if col in ['module', 'part', 'item_name']:
                self.results_tree.column(col, width=100)
            elif col == 'message':
                self.results_tree.column(col, width=200)
            elif col == 'action':
                self.results_tree.column(col, width=150)
            else:
                self.results_tree.column(col, width=80)
        
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 심각도별 색상 태그
        self.results_tree.tag_configure('critical', background='#FFB3B3')
        self.results_tree.tag_configure('high', background='#FFD9B3')
        self.results_tree.tag_configure('medium', background='#FFFFB3')
        self.results_tree.tag_configure('low', background='#E6FFE6')
        
        # 컨텍스트 메뉴
        self._create_context_menu()
    
    def _create_statistics_tab(self):
        """통계 탭 생성"""
        stats_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(stats_frame, text="통계")
        
        self.statistics_text = tk.Text(stats_frame, wrap=tk.WORD, state=tk.DISABLED)
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", 
                                      command=self.statistics_text.yview)
        self.statistics_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.statistics_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_context_menu(self):
        """결과 트리뷰의 컨텍스트 메뉴 생성"""
        self.context_menu = tk.Menu(self.results_tree, tearoff=0)
        self.context_menu.add_command(label="상세 정보", command=self.show_issue_details)
        self.context_menu.add_command(label="해당 항목으로 이동", command=self.goto_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="이슈 무시", command=self.ignore_issue)
        self.context_menu.add_command(label="보고서 생성", command=self.generate_report)
        
        def show_context_menu(event):
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
        
        self.results_tree.bind("<Button-3>", show_context_menu)
    
    def load_equipment_types(self):
        """장비 타입 목록을 로드합니다."""
        try:
            if self.manager.db_schema:
                equipment_types = self.manager.db_schema.get_equipment_types()
                type_names = [eq_type['type_name'] for eq_type in equipment_types]
                self.equipment_combo['values'] = type_names
        except Exception as e:
            self.manager.update_log(f"장비 타입 로드 실패: {str(e)}")
    
    def run_qc_check(self):
        """QC 검수를 실행합니다."""
        if not hasattr(self.manager, 'merged_df') or self.manager.merged_df is None:
            messagebox.showwarning("경고", "검수할 데이터가 없습니다. 먼저 파일을 로드하세요.")
            return
        
        # 별도 스레드에서 QC 실행 (UI 블로킹 방지)
        qc_thread = threading.Thread(target=self._execute_qc_check)
        qc_thread.daemon = True
        qc_thread.start()
    
    def _execute_qc_check(self):
        """실제 QC 검수를 실행합니다."""
        try:
            self.manager.window.after(0, lambda: self.progress_var.set(0))
            self.manager.window.after(0, lambda: self.status_label.config(text="QC 검수 시작..."))
            
            # 검수 모드와 파라미터 설정
            mode = self.qc_mode.get()
            equipment_type = self.equipment_var.get() if mode == "enhanced" else None
            
            validator = self.validators[mode]
            
            self.manager.window.after(0, lambda: self.progress_var.set(25))
            self.manager.window.after(0, lambda: self.status_label.config(text="데이터 검증 중..."))
            
            # QC 검수 실행
            result = validator.validate(
                self.manager.merged_df,
                equipment_type=equipment_type
            )
            
            self.manager.window.after(0, lambda: self.progress_var.set(75))
            self.manager.window.after(0, lambda: self.status_label.config(text="결과 처리 중..."))
            
            # 결과 저장 및 UI 업데이트
            self.current_result = result
            self.qc_history.append(result)
            
            self.manager.window.after(0, lambda: self.progress_var.set(100))
            self.manager.window.after(0, lambda: self.status_label.config(text="완료"))
            self.manager.window.after(0, self.update_qc_results)
            
            # 로그 메시지
            summary = result.get_summary_stats()
            log_message = (f"QC 검수 완료 - 전체: {summary['total_items']}개, "
                         f"이슈: {summary['total_issues']}개, "
                         f"점수: {summary['overall_score']:.1f}점")
            self.manager.window.after(0, lambda: self.manager.update_log(log_message))
            
        except Exception as e:
            error_msg = f"QC 검수 실행 오류: {str(e)}"
            self.manager.window.after(0, lambda: self.status_label.config(text="오류"))
            self.manager.window.after(0, lambda: self.manager.update_log(error_msg))
            self.manager.window.after(0, lambda: messagebox.showerror("오류", error_msg))
    
    def update_qc_results(self):
        """QC 결과를 UI에 업데이트합니다."""
        if not self.current_result:
            return
        
        # 요약 탭 업데이트
        self._update_summary_tab()
        
        # 상세 결과 탭 업데이트
        self._update_details_tab()
        
        # 통계 탭 업데이트
        self._update_statistics_tab()
    
    def _update_summary_tab(self):
        """요약 탭 업데이트"""
        result = self.current_result
        summary = result.get_summary_stats()
        
        # 전체 점수 업데이트
        score = summary['overall_score']
        score_color = self._get_score_color(score)
        self.overall_score_label.config(text=f"전체 점수: {score:.1f}점", foreground=score_color)
        
        # 카테고리별 점수 업데이트
        for widget in self.category_scores_frame.winfo_children():
            widget.destroy()
        
        if result.category_scores:
            for i, (category, score) in enumerate(result.category_scores.items()):
                color = self._get_score_color(score)
                label = ttk.Label(self.category_scores_frame, 
                                text=f"{category}: {score:.1f}점",
                                foreground=color)
                label.grid(row=0, column=i, padx=10, pady=2)
        
        # 심각도별 통계 업데이트
        severity_dist = summary['severity_distribution']
        for severity, label in self.severity_labels.items():
            count = severity_dist.get(severity.value, 0)
            label.config(text=f"{severity.value}: {count}개")
        
        # 권장사항 업데이트
        self.recommendation_text.config(state=tk.NORMAL)
        self.recommendation_text.delete(1.0, tk.END)
        
        recommendations = self._generate_recommendations()
        self.recommendation_text.insert(tk.END, recommendations)
        self.recommendation_text.config(state=tk.DISABLED)
    
    def _update_details_tab(self):
        """상세 결과 탭 업데이트"""
        # 기존 데이터 삭제
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        if not self.current_result or not self.current_result.issues:
            return
        
        # 필터 적용
        filtered_issues = self._apply_filters(self.current_result.issues)
        
        # 이슈 표시
        for issue in filtered_issues:
            values = [
                issue.severity.value,
                issue.category.value,
                issue.message[:100] + "..." if len(issue.message) > 100 else issue.message,
                issue.item_info.get('Module', ''),
                issue.item_info.get('Part', ''),
                issue.item_info.get('Item_Name', ''),
                str(issue.item_info.get('Value', '')),
                issue.recommended_action[:50] + "..." if len(issue.recommended_action) > 50 else issue.recommended_action
            ]
            
            tag = issue.severity.value.lower()
            self.results_tree.insert('', tk.END, values=values, tags=(tag,))
    
    def _update_statistics_tab(self):
        """통계 탭 업데이트"""
        self.statistics_text.config(state=tk.NORMAL)
        self.statistics_text.delete(1.0, tk.END)
        
        if not self.current_result:
            self.statistics_text.insert(tk.END, "QC 결과가 없습니다.")
            self.statistics_text.config(state=tk.DISABLED)
            return
        
        summary = self.current_result.get_summary_stats()
        
        stats_text = f"""
===== QC 검수 통계 =====

[기본 정보]
• 검수 시간: {summary['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
• 실행 시간: {summary['execution_time']:.2f}초
• 총 검수 항목: {summary['total_items']}개
• 발견된 이슈: {summary['total_issues']}개
• 전체 점수: {summary['overall_score']:.1f}점

[심각도별 분포]
"""
        
        for severity, count in summary['severity_distribution'].items():
            percentage = (count / summary['total_issues'] * 100) if summary['total_issues'] > 0 else 0
            stats_text += f"• {severity}: {count}개 ({percentage:.1f}%)\\n"
        
        stats_text += "\\n[카테고리별 분포]\\n"
        for category, count in summary['category_distribution'].items():
            percentage = (count / summary['total_issues'] * 100) if summary['total_issues'] > 0 else 0
            stats_text += f"• {category}: {count}개 ({percentage:.1f}%)\\n"
        
        if self.current_result.category_scores:
            stats_text += "\\n[카테고리별 점수]\\n"
            for category, score in self.current_result.category_scores.items():
                stats_text += f"• {category}: {score:.1f}점\\n"
        
        # QC 품질 평가
        stats_text += "\\n[품질 평가]\\n"
        overall_score = summary['overall_score']
        if overall_score >= 90:
            stats_text += "• 우수: 매우 높은 품질의 데이터입니다.\\n"
        elif overall_score >= 80:
            stats_text += "• 양호: 양호한 품질이지만 일부 개선이 필요합니다.\\n"
        elif overall_score >= 70:
            stats_text += "• 보통: 보통 품질로 개선이 권장됩니다.\\n"
        elif overall_score >= 60:
            stats_text += "• 미흡: 품질이 미흡하여 상당한 개선이 필요합니다.\\n"
        else:
            stats_text += "• 불량: 품질이 매우 낮아 전면적인 검토가 필요합니다.\\n"
        
        self.statistics_text.insert(tk.END, stats_text)
        self.statistics_text.config(state=tk.DISABLED)
    
    def _apply_filters(self, issues):
        """필터를 적용하여 이슈 목록을 반환합니다."""
        filtered = issues
        
        # 심각도 필터
        severity_filter = self.severity_filter.get()
        if severity_filter != "All":
            filtered = [issue for issue in filtered if issue.severity.value == severity_filter]
        
        # 카테고리 필터
        category_filter = self.category_filter.get()
        if category_filter != "All":
            filtered = [issue for issue in filtered if issue.category.value == category_filter]
        
        # 검색 필터
        search_term = self.search_var.get().lower()
        if search_term:
            filtered = [
                issue for issue in filtered 
                if (search_term in issue.message.lower() or
                    search_term in issue.item_info.get('Module', '').lower() or
                    search_term in issue.item_info.get('Part', '').lower() or
                    search_term in issue.item_info.get('Item_Name', '').lower())
            ]
        
        return filtered
    
    def _get_score_color(self, score):
        """점수에 따른 색상 반환"""
        if score >= 90:
            return "green"
        elif score >= 80:
            return "blue"
        elif score >= 70:
            return "orange"
        else:
            return "red"
    
    def _generate_recommendations(self):
        """권장사항 생성"""
        if not self.current_result:
            return "QC 결과가 없습니다."
        
        summary = self.current_result.get_summary_stats()
        recommendations = []
        
        # 전체 점수 기반 권장사항
        score = summary['overall_score']
        if score >= 90:
            recommendations.append("✅ 데이터 품질이 우수합니다. 현재 수준을 유지하세요.")
        elif score >= 80:
            recommendations.append("⚡ 데이터 품질이 양호합니다. 일부 이슈만 해결하면 완벽합니다.")
        elif score >= 70:
            recommendations.append("⚠️ 데이터 품질이 보통입니다. 주요 이슈들을 우선 해결하세요.")
        else:
            recommendations.append("🚨 데이터 품질이 낮습니다. 전면적인 검토가 필요합니다.")
        
        # 심각도별 권장사항
        critical_count = summary['severity_distribution'].get('Critical', 0)
        high_count = summary['severity_distribution'].get('High', 0)
        
        if critical_count > 0:
            recommendations.append(f"🔴 Critical 이슈 {critical_count}개를 즉시 해결하세요.")
        
        if high_count > 0:
            recommendations.append(f"🟠 High 이슈 {high_count}개를 우선적으로 해결하세요.")
        
        # 카테고리별 권장사항
        category_dist = summary['category_distribution']
        
        if category_dist.get('Performance', 0) > 0:
            recommendations.append("⚙️ 성능 파라미터 관련 이슈가 있습니다. 시스템 성능에 영향을 줄 수 있습니다.")
        
        if category_dist.get('Completeness', 0) > 0:
            recommendations.append("📝 데이터 완성도 이슈가 있습니다. 누락된 값들을 채워주세요.")
        
        if category_dist.get('Consistency', 0) > 0:
            recommendations.append("🔄 데이터 일관성 이슈가 있습니다. 중복이나 불일치를 확인하세요.")
        
        if category_dist.get('Accuracy', 0) > 0:
            recommendations.append("🎯 데이터 정확도 이슈가 있습니다. 값들이 올바른지 확인하세요.")
        
        if not recommendations:
            recommendations.append("✨ 발견된 이슈가 없습니다. 데이터가 완벽합니다!")
        
        return "\\n\\n".join(f"• {rec}" for rec in recommendations)
    
    def on_filter_changed(self, event=None):
        """필터 변경 시 호출"""
        self._update_details_tab()
    
    def on_search_changed(self, event=None):
        """검색어 변경 시 호출"""
        self._update_details_tab()
    
    def show_issue_details(self):
        """선택된 이슈의 상세 정보 표시"""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        item = self.results_tree.item(selection[0])
        values = item['values']
        
        details = f"""
이슈 상세 정보

심각도: {values[0]}
카테고리: {values[1]}
메시지: {values[2]}

대상 항목:
• 모듈: {values[3]}
• 부품: {values[4]}
• 항목명: {values[5]}
• 값: {values[6]}

권장 조치:
{values[7]}
"""
        
        messagebox.showinfo("이슈 상세 정보", details)
    
    def goto_item(self):
        """해당 항목으로 이동 (구현 예정)"""
        messagebox.showinfo("안내", "해당 항목으로 이동 기능은 구현 예정입니다.")
    
    def ignore_issue(self):
        """이슈 무시 (구현 예정)"""
        messagebox.showinfo("안내", "이슈 무시 기능은 구현 예정입니다.")
    
    def generate_report(self):
        """QC 보고서 생성"""
        if not self.current_result:
            messagebox.showwarning("경고", "생성할 QC 결과가 없습니다.")
            return
        
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="QC 보고서 저장",
                defaultextension=".xlsx",
                filetypes=[("Excel 파일", "*.xlsx"), ("PDF 파일", "*.pdf")]
            )
            
            if filename:
                success = self.report_generator.generate_report(self.current_result, filename)
                if success:
                    self.manager.update_log(f"QC 보고서가 {filename}으로 생성되었습니다.")
                    messagebox.showinfo("성공", f"QC 보고서가 생성되었습니다.\\n{filename}")
                else:
                    messagebox.showerror("오류", "보고서 생성에 실패했습니다.")
        
        except Exception as e:
            error_msg = f"보고서 생성 오류: {str(e)}"
            self.manager.update_log(error_msg)
            messagebox.showerror("오류", error_msg)
    
    def get_current_qc_result(self):
        """현재 QC 결과를 반환합니다."""
        return self.current_result
    
    def clear_qc_results(self):
        """QC 결과를 지웁니다."""
        self.current_result = None
        self.update_qc_results()