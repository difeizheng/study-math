"""
交互体验优化模块
- 动态趋势动画：成绩变化的动画展示
- 交互式仪表盘：可交互的数据可视化
- 移动端适配优化：响应式布局支持
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime


class AnimatedTrendChart:
    """动态趋势图表"""

    def __init__(self):
        """初始化动态趋势图表"""
        self.colors = {
            'primary': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c'
        }

    def create_animated_line_chart(self, scores: List[float],
                                    exam_names: List[str] = None,
                                    title: str = "成绩趋势动画") -> go.Figure:
        """
        创建动态折线图

        Args:
            scores: 成绩列表
            exam_names: 考试名称列表
            title: 图表标题

        Returns:
            Plotly 图表
        """
        if not scores:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title=title)
            return fig

        n = len(scores)
        x_labels = exam_names if exam_names else [f"考试{i+1}" for i in range(n)]

        # 创建帧数据
        frames = []
        for i in range(1, n + 1):
            frame_data = [
                go.Scatter(
                    x=x_labels[:i],
                    y=scores[:i],
                    mode='lines+markers',
                    line=dict(color=self.colors['primary'], width=3),
                    marker=dict(size=8),
                    name='成绩'
                )
            ]

            # 添加趋势线
            if i >= 3:
                from scipy import stats
                slope, intercept, _, _, _ = stats.linregress(range(i), scores[:i])
                trend_y = [slope * x + intercept for x in range(i)]
                frame_data.append(
                    go.Scatter(
                        x=x_labels[:i],
                        y=trend_y,
                        mode='lines',
                        line=dict(color=self.colors['danger'], width=2, dash='dash'),
                        name='趋势线',
                        opacity=0.7
                    )
                )

            frames.append(go.Frame(data=frame_data, name=str(i)))

        # 初始数据
        initial_data = [
            go.Scatter(
                x=x_labels[:1],
                y=scores[:1],
                mode='markers',
                marker=dict(size=10, color=self.colors['primary']),
                name='成绩'
            )
        ]

        # 创建图表
        fig = go.Figure(
            data=initial_data,
            layout=go.Layout(
                title=title,
                xaxis=dict(title="考试", range=[-0.5, n - 0.5]),
                yaxis=dict(title="分数", range=[0, 100]),
                height=450,
                updatemenus=[{
                    'type': 'buttons',
                    'showactive': False,
                    'direction': 'left',
                    'x': 0.1,
                    'y': 0,
                    'xanchor': 'right',
                    'yanchor': 'top',
                    'buttons': [
                        {
                            'label': '▶ 播放',
                            'method': 'animate',
                            'args': [None, {
                                'frame': {'duration': 500, 'redraw': True},
                                'fromcurrent': True,
                                'transition': {'duration': 300}
                            }]
                        },
                        {
                            'label': '⏸ 暂停',
                            'method': 'animate',
                            'args': [[None], {
                                'frame': {'duration': 0, 'redraw': True},
                                'mode': 'immediate',
                                'transition': {'duration': 0}
                            }]
                        }
                    ]
                }],
                sliders=[{
                    'active': 0,
                    'yanchor': 'top',
                    'xanchor': 'left',
                    'currentvalue': {
                        'font': {'size': 14},
                        'prefix': '进度：',
                        'visible': True,
                        'xanchor': 'right'
                    },
                    'transition': {'duration': 300},
                    'pad': {'b': 10, 't': 50},
                    'len': 0.9,
                    'x': 0.1,
                    'y': 0,
                    'steps': [
                        {
                            'args': [[str(i)], {
                                'frame': {'duration': 0, 'redraw': True},
                                'mode': 'immediate',
                                'transition': {'duration': 0}
                            }],
                            'label': str(i),
                            'method': 'animate'
                        } for i in range(1, n + 1)
                    ]
                }]
            ),
            frames=frames
        )

        return fig

    def create_race_chart(self, student_scores: Dict[str, List[float]],
                          title: str = "成绩排行榜") -> go.Figure:
        """
        创建排行榜竞赛图

        Args:
            student_scores: {学生名：[成绩列表]}
            title: 图表标题

        Returns:
            Plotly 图表
        """
        if not student_scores:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title=title)
            return fig

        students = list(student_scores.keys())
        n_exams = len(list(student_scores.values())[0])

        # 创建帧数据
        frames = []
        for i in range(n_exams):
            # 获取当前考试所有学生的成绩
            current_scores = [(name, scores[i] if i < len(scores) else 0)
                            for name, scores in student_scores.items()]
            current_scores.sort(key=lambda x: x[1], reverse=True)

            names = [x[0] for x in current_scores]
            scores = [x[1] for x in current_scores]

            frame_data = [
                go.Bar(
                    y=names,
                    x=scores,
                    orientation='h',
                    marker=dict(
                        color=scores,
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="分数")
                    ),
                    text=scores,
                    textposition='outside',
                    name=f'考试{i+1}'
                )
            ]
            frames.append(go.Frame(data=frame_data, name=str(i)))

        # 初始数据
        initial_scores = [(name, scores[0] if scores else 0)
                         for name, scores in student_scores.items()]
        initial_scores.sort(key=lambda x: x[1], reverse=True)
        initial_data = [
            go.Bar(
                y=[x[0] for x in initial_scores],
                x=[x[1] for x in initial_scores],
                orientation='h',
                marker=dict(
                    color=[x[1] for x in initial_scores],
                    colorscale='Viridis',
                    showscale=True
                ),
                text=[x[1] for x in initial_scores],
                textposition='outside'
            )
        ]

        fig = go.Figure(
            data=initial_data,
            layout=go.Layout(
                title=title,
                xaxis=dict(range=[0, 100], title="分数"),
                height=400,
                updatemenus=[{
                    'type': 'buttons',
                    'buttons': [
                        {'label': '▶ 播放', 'method': 'animate', 'args': [None, {
                            'frame': {'duration': 800, 'redraw': True},
                            'fromcurrent': True
                        }]},
                        {'label': '⏸ 暂停', 'method': 'animate', 'args': [[None], {
                            'frame': {'duration': 0, 'redraw': True},
                            'mode': 'immediate'
                        }]}
                    ]
                }]
            ),
            frames=frames
        )

        return fig


class InteractiveDashboard:
    """交互式仪表盘"""

    def __init__(self):
        """初始化仪表盘"""
        self.colors = {
            'primary': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'info': '#1abc9c'
        }

    def create_score_overview_dashboard(self, student_data: Dict) -> go.Figure:
        """
        创建成绩概览仪表盘

        Args:
            student_data: 学生数据

        Returns:
            Plotly 仪表盘
        """
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'indicator'}, {'type': 'pie'}],
                   [{'type': 'scatter'}, {'type': 'bar'}]],
            subplot_titles=['综合评分', '等级分布', '成绩趋势', '各单元表现'],
            vertical_spacing=0.15,
            horizontal_spacing=0.12
        )

        # 1. 综合评分（仪表）
        avg_score = student_data.get('avg_score', 75)
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=avg_score,
            title={'text': "平均分"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': self.colors['primary']},
                'steps': [
                    {'range': [0, 60], 'color': "#ffebee"},
                    {'range': [60, 75], 'color': "#fff3e0"},
                    {'range': [75, 85], 'color': "#e8f5e9"},
                    {'range': [85, 100], 'color': "#c8e6c9"}
                ]
            }
        ), row=1, col=1)

        # 2. 等级分布（饼图）
        grades = student_data.get('grades', {'A': 3, 'B': 5, 'C': 2, 'D': 1, 'E': 0})
        fig.add_trace(go.Pie(
            labels=list(grades.keys()),
            values=list(grades.values()),
            marker_colors=[self.colors['success'], self.colors['info'],
                          self.colors['warning'], self.colors['danger'], '#95a5a6'],
            hole=0.4
        ), row=1, col=2)

        # 3. 成绩趋势（折线图）
        scores = student_data.get('scores', [])
        exams = student_data.get('exam_names', [f"考试{i+1}" for i in range(len(scores))])
        fig.add_trace(go.Scatter(
            x=exams, y=scores,
            mode='lines+markers',
            line=dict(color=self.colors['primary'], width=3),
            marker=dict(size=8),
            name='成绩'
        ), row=2, col=1)

        # 4. 各单元表现（柱状图）
        units = student_data.get('units', ['单元 1', '单元 2', '单元 3', '单元 4'])
        unit_scores = student_data.get('unit_scores', [80, 75, 85, 78])
        fig.add_trace(go.Bar(
            x=units, y=unit_scores,
            marker_color=self.colors['info'],
            name='单元成绩'
        ), row=2, col=2)

        fig.update_layout(
            height=600,
            title_text="📊 成绩概览仪表盘",
            showlegend=False
        )

        return fig

    def create_comparison_dashboard(self, data1: Dict, data2: Dict,
                                    names: Tuple[str, str]) -> go.Figure:
        """
        创建对比仪表盘

        Args:
            data1: 学生 1 数据
            data2: 学生 2 数据
            names: (学生 1 名，学生 2 名)

        Returns:
            Plotly 仪表盘
        """
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'scatter'}, {'type': 'scatterpolar'}],
                   [{'type': 'bar'}, {'type': 'indicator'}]],
            subplot_titles=['成绩对比', '能力雷达图', '等级对比', '平均分对比'],
            vertical_spacing=0.15,
            horizontal_spacing=0.12
        )

        # 1. 成绩对比（折线图）
        scores1 = data1.get('scores', [])
        scores2 = data2.get('scores', [])
        n = max(len(scores1), len(scores2))
        exams = [f"考试{i+1}" for i in range(n)]

        fig.add_trace(go.Scatter(
            x=exams[:len(scores1)], y=scores1,
            mode='lines+markers',
            line=dict(color=self.colors['primary'], width=2),
            marker=dict(size=8),
            name=names[0]
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=exams[:len(scores2)], y=scores2,
            mode='lines+markers',
            line=dict(color=self.colors['danger'], width=2),
            marker=dict(size=8),
            name=names[1]
        ), row=1, col=1)

        # 2. 能力雷达图
        categories = ['知识', '技能', '推理', '应用', '反思']
        abilities1 = data1.get('abilities', [70, 70, 70, 70, 70])
        abilities2 = data2.get('abilities', [70, 70, 70, 70, 70])

        # 闭合雷达图
        cats_closed = categories + [categories[0]]
        abil1_closed = abilities1 + [abilities1[0]]
        abil2_closed = abilities2 + [abilities2[0]]

        fig.add_trace(go.Scatterpolar(
            r=abil1_closed, theta=cats_closed,
            fill='toself',
            name=names[0],
            line=dict(color=self.colors['primary']),
            opacity=0.7
        ), row=1, col=2, polar=True)

        fig.add_trace(go.Scatterpolar(
            r=abil2_closed, theta=cats_closed,
            fill='toself',
            name=names[1],
            line=dict(color=self.colors['danger']),
            opacity=0.7
        ), row=1, col=2, polar=True)

        # 3. 等级对比（柱状图）
        grades1 = [data1.get('grade_count', 10)]
        grades2 = [data2.get('grade_count', 10)]

        fig.add_trace(go.Bar(
            x=['考试次数'], y=grades1,
            marker_color=self.colors['primary'],
            name=names[0]
        ), row=2, col=1)

        fig.add_trace(go.Bar(
            x=['考试次数'], y=grades2,
            marker_color=self.colors['danger'],
            name=names[1]
        ), row=2, col=1)

        # 4. 平均分对比（仪表）
        avg1 = data1.get('avg_score', 75)
        avg2 = data2.get('avg_score', 75)

        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=avg1,
            title={'text': names[0]}
        ), row=2, col=2)

        fig.update_layout(
            height=700,
            title_text=f"📊 {names[0]} vs {names[1]} 对比仪表盘"
        )

        return fig


class MobileOptimizer:
    """移动端优化器"""

    @staticmethod
    def get_mobile_layout() -> Dict:
        """获取移动端布局配置"""
        return {
            'chart_height': 300,
            'chart_margin': {'l': 30, 'r': 30, 't': 30, 'b': 50},
            'font_size': 12,
            'title_font_size': 16,
            'legend_font_size': 10,
            'touch_target_size': 44  # 最小触摸目标尺寸 (pt)
        }

    @staticmethod
    def get_desktop_layout() -> Dict:
        """获取桌面端布局配置"""
        return {
            'chart_height': 450,
            'chart_margin': {'l': 60, 'r': 60, 't': 40, 'b': 60},
            'font_size': 14,
            'title_font_size': 18,
            'legend_font_size': 12,
            'touch_target_size': None
        }

    @staticmethod
    def optimize_figure(fig: go.Figure, is_mobile: bool = False) -> go.Figure:
        """
        优化图表布局

        Args:
            fig: Plotly 图表
            is_mobile: 是否为移动端

        Returns:
            优化后的图表
        """
        layout = MobileOptimizer.get_mobile_layout() if is_mobile else MobileOptimizer.get_desktop_layout()

        fig.update_layout(
            height=layout['chart_height'],
            margin=layout['chart_margin'],
            font_size=layout['font_size'],
            title_font_size=layout['title_font_size'],
            legend_font_size=layout['legend_font_size']
        )

        return fig

    @staticmethod
    def create_responsive_container() -> str:
        """
        创建响应式容器 HTML

        Returns:
            HTML 代码
        """
        return """
        <style>
            .responsive-chart {
                position: relative;
                width: 100%;
                padding-bottom: 56.25%;
                height: 0;
            }
            .responsive-chart iframe {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border: none;
            }
            @media (max-width: 768px) {
                .chart-container {
                    padding: 10px !important;
                }
                .chart-title {
                    font-size: 16px !important;
                }
            }
        </style>
        <div class="responsive-chart">
            <iframe src="{chart_url}" title="Responsive Chart"></iframe>
        </div>
        """
