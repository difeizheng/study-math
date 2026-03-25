"""
家校沟通模块
- 学情报告自动生成：PDF 格式的学习报告，包含成绩分析、薄弱点、建议
- 进步幅度展示：可视化展示学生的进步轨迹
- 对比基准说明：与班级/年级平均水平的对比
"""
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class StudentReport:
    """学生学情报告"""
    student_id: int
    student_name: str
    report_date: str
    total_exams: int
    avg_score: float
    best_score: float
    trend: str  # 上升/稳定/下降
    strongest_knowledge: str  # 最强知识点
    weakest_knowledge: str  # 最弱知识点
    suggestions: List[str]  # 学习建议
    teacher_comment: str  # 教师评语


@dataclass
class ProgressMetric:
    """进步幅度指标"""
    metric_name: str
    current_value: float
    previous_value: float
    change: float
    change_percent: float
    trend: str  # improved/declined/stable


class ReportGenerator:
    """学情报告生成器"""

    def __init__(self, knowledge_points: Dict = None):
        """初始化报告生成器"""
        self.knowledge_points = knowledge_points or {}

    def generate_report(self, student_id: int, student_name: str,
                       scores: List[float], exam_names: List[str] = None,
                       mastery_data: Dict = None) -> StudentReport:
        """
        生成学情报告

        Args:
            student_id: 学生 ID
            student_name: 学生姓名
            scores: 成绩列表（按时间顺序）
            exam_names: 考试名称列表
            mastery_data: 知识点掌握度数据

        Returns:
            StudentReport 学情报告
        """
        if not scores:
            return StudentReport(
                student_id=student_id,
                student_name=student_name,
                report_date=datetime.now().strftime("%Y-%m-%d"),
                total_exams=0,
                avg_score=0,
                best_score=0,
                trend='稳定',
                strongest_knowledge='N/A',
                weakest_knowledge='N/A',
                suggestions=['请继续努力学习'],
                teacher_comment='继续加油！'
            )

        # 计算基本统计
        avg_score = sum(scores) / len(scores)
        best_score = max(scores)

        # 判断趋势
        if len(scores) >= 3:
            recent_avg = sum(scores[-3:]) / 3
            earlier_avg = sum(scores[:3]) / 3 if len(scores) >= 6 else scores[0]
            if recent_avg > earlier_avg + 5:
                trend = '上升'
            elif recent_avg < earlier_avg - 5:
                trend = '下降'
            else:
                trend = '稳定'
        else:
            trend = '稳定'

        # 分析知识点
        strongest_kp = 'N/A'
        weakest_kp = 'N/A'
        if mastery_data:
            sorted_kp = sorted(mastery_data.items(), key=lambda x: x[1], reverse=True)
            strongest_kp = self._get_kp_name(sorted_kp[0][0])
            weakest_kp = self._get_kp_name(sorted_kp[-1][0])

        # 生成建议
        suggestions = self._generate_suggestions(avg_score, trend, mastery_data)

        # 教师评语
        teacher_comment = self._generate_comment(avg_score, trend, best_score)

        return StudentReport(
            student_id=student_id,
            student_name=student_name,
            report_date=datetime.now().strftime("%Y-%m-%d"),
            total_exams=len(scores),
            avg_score=round(avg_score, 1),
            best_score=best_score,
            trend=trend,
            strongest_knowledge=strongest_kp,
            weakest_knowledge=weakest_kp,
            suggestions=suggestions,
            teacher_comment=teacher_comment
        )

    def _get_kp_name(self, code: str) -> str:
        """获取知识点名称"""
        kp = self.knowledge_points.get(code)
        return kp.name if hasattr(kp, 'name') else code

    def _generate_suggestions(self, avg_score: float, trend: str,
                              mastery_data: Dict = None) -> List[str]:
        """生成学习建议"""
        suggestions = []

        if avg_score >= 90:
            suggestions.append("✓ 成绩优秀，保持当前学习状态")
            suggestions.append("可以尝试挑战性题目，拓展思维")
        elif avg_score >= 80:
            suggestions.append("成绩良好，基础扎实")
            suggestions.append("重点关注薄弱知识点，争取突破 90 分")
        elif avg_score >= 70:
            suggestions.append("成绩中等，有提升空间")
            suggestions.append("加强基础练习，巩固基本概念")
        elif avg_score >= 60:
            suggestions.append("成绩及格，需要加强学习")
            suggestions.append("建议回归课本，掌握核心知识点")
        else:
            suggestions.append("成绩需要关注，建议制定提升计划")
            suggestions.append("从基础题开始，逐步建立信心")

        if trend == '下降':
            suggestions.append("⚠️ 近期成绩有所下滑，请分析原因")
            suggestions.append("建议与老师沟通，针对性辅导")
        elif trend == '上升':
            suggestions.append("📈 近期进步明显，继续保持！")

        return suggestions

    def _generate_comment(self, avg_score: float, trend: str, best_score: float) -> str:
        """生成教师评语"""
        if avg_score >= 90:
            base = "该生学习成绩优秀，"
        elif avg_score >= 80:
            base = "该生学习成绩良好，"
        elif avg_score >= 70:
            base = "该生学习成绩中等，"
        else:
            base = "该生学习需要加强，"

        if trend == '上升':
            comment = base + "近期进步明显，希望继续保持！"
        elif trend == '下降':
            comment = base + "近期有所松懈，望加倍努力！"
        else:
            comment = base + "学习状态稳定，望再接再厉！"

        return comment

    def create_report_preview_chart(self, report: StudentReport) -> go.Figure:
        """
        创建报告预览图

        Args:
            report: 学情报告

        Returns:
            Plotly 仪表图
        """
        # 确定颜色
        if report.avg_score >= 90:
            color = '#27ae60'
        elif report.avg_score >= 80:
            color = '#2ecc71'
        elif report.avg_score >= 70:
            color = '#f1c40f'
        elif report.avg_score >= 60:
            color = '#e67e22'
        else:
            color = '#e74c3c'

        # 趋势图标
        trend_icons = {'上升': '📈', '稳定': '➡️', '下降': '📉'}
        trend_icon = trend_icons.get(report.trend, '')

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=report.avg_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"平均分 (满分 100)", 'font': {'size': 24}},
            delta={'reference': 75, 'increasing': {'color': "#27ae60"}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'steps': [
                    {'range': [0, 60], 'color': "#ffebee"},
                    {'range': [60, 75], 'color': "#fff3e0"},
                    {'range': [75, 85], 'color': "#e8f5e9"},
                    {'range': [85, 100], 'color': "#c8e6c9"}
                ],
            }
        ))

        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=50, b=50)
        )

        return fig

    def create_report_pdf_data(self, report: StudentReport) -> Dict:
        """
        生成 PDF 报告数据

        Args:
            report: 学情报告

        Returns:
            PDF 内容字典
        """
        return {
            'title': f'{report.student_name} 学情分析报告',
            'date': report.report_date,
            'sections': [
                {
                    'title': '基本情况',
                    'content': [
                        f'考试次数：{report.total_exams}次',
                        f'平均分：{report.avg_score}分',
                        f'最高分：{report.best_score}分',
                        f'趋势：{report.trend} {self._get_trend_icon(report.trend)}'
                    ]
                },
                {
                    'title': '知识点分析',
                    'content': [
                        f'最强知识点：{report.strongest_knowledge}',
                        f'最弱知识点：{report.weakest_knowledge}'
                    ]
                },
                {
                    'title': '学习建议',
                    'content': report.suggestions
                },
                {
                    'title': '教师评语',
                    'content': [report.teacher_comment]
                }
            ]
        }

    def _get_trend_icon(self, trend: str) -> str:
        """获取趋势图标"""
        icons = {'上升': '↑', '稳定': '→', '下降': '↓'}
        return icons.get(trend, '')


class ProgressAnalyzer:
    """进步幅度分析器"""

    def __init__(self):
        """初始化分析器"""
        pass

    def analyze_progress(self, scores: List[float],
                        exam_dates: List[str] = None) -> List[ProgressMetric]:
        """
        分析进步幅度

        Args:
            scores: 成绩列表（按时间顺序）
            exam_dates: 考试日期列表

        Returns:
            进步指标列表
        """
        if len(scores) < 2:
            return []

        metrics = []

        # 1. 总体进步
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        overall_change = second_avg - first_avg
        overall_percent = (overall_change / first_avg * 100) if first_avg > 0 else 0

        metrics.append(ProgressMetric(
            metric_name='总体成绩',
            current_value=second_avg,
            previous_value=first_avg,
            change=overall_change,
            change_percent=overall_percent,
            trend='improved' if overall_change > 2 else 'declined' if overall_change < -2 else 'stable'
        ))

        # 2. 最近三次 vs 之前
        if len(scores) >= 4:
            recent_3 = scores[-3:]
            before_3 = scores[:-3] if len(scores) > 3 else scores[:1]

            recent_avg = sum(recent_3) / 3
            before_avg = sum(before_3) / len(before_3)

            recent_change = recent_avg - before_avg
            recent_percent = (recent_change / before_avg * 100) if before_avg > 0 else 0

            metrics.append(ProgressMetric(
                metric_name='近期表现',
                current_value=recent_avg,
                previous_value=before_avg,
                change=recent_change,
                change_percent=recent_percent,
                trend='improved' if recent_change > 2 else 'declined' if recent_change < -2 else 'stable'
            ))

        # 3. 最高分进步
        if len(scores) >= 4:
            first_half_max = max(scores[:len(scores)//2])
            second_half_max = max(scores[len(scores)//2:])

            max_change = second_half_max - first_half_max
            max_percent = (max_change / first_half_max * 100) if first_half_max > 0 else 0

            metrics.append(ProgressMetric(
                metric_name='最高分',
                current_value=second_half_max,
                previous_value=first_half_max,
                change=max_change,
                change_percent=max_percent,
                trend='improved' if max_change > 0 else 'stable' if max_change == 0 else 'declined'
            ))

        return metrics

    def create_progress_chart(self, scores: List[float],
                             exam_names: List[str] = None) -> go.Figure:
        """
        创建进步幅度图表

        Args:
            scores: 成绩列表
            exam_names: 考试名称列表

        Returns:
            Plotly 图表
        """
        if not scores:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="进步幅度分析")
            return fig

        n = len(scores)
        x_labels = exam_names if exam_names else [f"考试{i+1}" for i in range(n)]

        # 创建图表
        fig = go.Figure()

        # 成绩线
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=scores,
            mode='lines+markers',
            name='成绩',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8)
        ))

        # 趋势线
        if n >= 2:
            from scipy import stats
            slope, intercept, r_value, _, _ = stats.linregress(range(n), scores)
            trend_y = [slope * x + intercept for x in range(n)]

            fig.add_trace(go.Scatter(
                x=x_labels,
                y=trend_y,
                mode='lines',
                name='趋势线',
                line=dict(color='#e74c3c', width=2, dash='dash')
            ))

        # 添加参考线
        fig.add_hline(y=60, line_dash="dash", line_color="gray",
                     annotation_text="及格线", annotation_position="right", opacity=0.5)
        fig.add_hline(y=85, line_dash="dash", line_color="orange",
                     annotation_text="优秀线", annotation_position="right", opacity=0.5)
        fig.add_hline(y=90, line_dash="dash", line_color="green",
                     annotation_text="卓越线", annotation_position="right", opacity=0.5)

        # 计算进步幅度
        if n >= 2:
            first_half = scores[:n//2]
            second_half = scores[n//2:]
            change = sum(second_half) / len(second_half) - sum(first_half) / len(first_half)

            # 添加进步标注
            if change > 0:
                annotation_text = f"📈 进步 {change:+.1f}分"
                color = "#27ae60"
            elif change < 0:
                annotation_text = f"📉 退步 {change:+.1f}分"
                color = "#e74c3c"
            else:
                annotation_text = "➡️ 保持稳定"
                color = "#95a5a6"

            fig.add_annotation(
                text=annotation_text,
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                showarrow=False,
                font=dict(size=14, color=color),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor=color,
                borderwidth=1,
                borderpad=4
            )

        fig.update_layout(
            title="进步幅度分析",
            xaxis_title="考试",
            yaxis_title="分数",
            yaxis_range=[max(0, min(scores) - 10), min(100, max(scores) + 15)],
            height=450,
            hovermode='x unified'
        )

        return fig


class BenchmarkComparator:
    """对比基准分析器"""

    def __init__(self, class_scores: Dict[str, List[float]] = None):
        """
        初始化对比分析器

        Args:
            class_scores: 班级成绩数据 {班级名：[成绩列表]}
        """
        self.class_scores = class_scores or {}

    def compare_with_benchmark(self, student_score: float,
                               benchmark_type: str = 'class') -> Dict:
        """
        与基准对比

        Args:
            student_score: 学生分数
            benchmark_type: 对比类型 (class/grade/school)

        Returns:
            对比结果
        """
        if not self.class_scores:
            return {
                'student_score': student_score,
                'benchmark_avg': 0,
                'benchmark_name': '暂无基准数据',
                'difference': 0,
                'percentile': 50,
                'ranking': '中等'
            }

        # 合并所有班级成绩作为基准
        all_scores = []
        for scores in self.class_scores.values():
            all_scores.extend(scores)

        if not all_scores:
            return {
                'student_score': student_score,
                'benchmark_avg': 0,
                'benchmark_name': '暂无基准数据',
                'difference': 0,
                'percentile': 50,
                'ranking': '中等'
            }

        benchmark_avg = sum(all_scores) / len(all_scores)
        difference = student_score - benchmark_avg

        # 计算百分位
        percentile = sum(1 for s in all_scores if s <= student_score) / len(all_scores) * 100

        # 确定排名
        if percentile >= 90:
            ranking = '前 10%'
        elif percentile >= 75:
            ranking = '前 25%'
        elif percentile >= 50:
            ranking = '中上'
        elif percentile >= 25:
            ranking = '中下'
        else:
            ranking = '后 25%'

        return {
            'student_score': student_score,
            'benchmark_avg': round(benchmark_avg, 1),
            'benchmark_name': '班级平均',
            'difference': round(difference, 1),
            'percentile': round(percentile, 1),
            'ranking': ranking
        }

    def create_benchmark_chart(self, comparison: Dict) -> go.Figure:
        """
        创建基准对比图

        Args:
            comparison: 对比结果

        Returns:
            Plotly 图表
        """
        fig = go.Figure()

        # 学生分数条
        student_color = '#3498db' if comparison['difference'] >= 0 else '#e74c3c'
        fig.add_trace(go.Bar(
            name='学生分数',
            x=[comparison['student_score']],
            y=[''],
            orientation='h',
            marker_color=student_color,
            text=[f"{comparison['student_score']}分"],
            textposition='outside'
        ))

        # 基准分数条
        fig.add_trace(go.Bar(
            name=comparison['benchmark_name'],
            x=[comparison['benchmark_avg']],
            y=[''],
            orientation='h',
            marker_color='#95a5a6',
            text=[f"{comparison['benchmark_avg']}分"],
            textposition='outside'
        ))

        # 添加百分位标注
        fig.add_annotation(
            text=f"百分位：{comparison['percentile']}% ({comparison['ranking']})",
            xref="paper", yref="paper",
            x=0.5, y=-0.3,
            showarrow=False,
            font_size=14
        )

        fig.update_layout(
            title=f"与{comparison['benchmark_name']}对比",
            xaxis_title="分数",
            xaxis_range=[0, 100],
            height=200,
            showlegend=True,
            barmode='overlay'
        )

        return fig
