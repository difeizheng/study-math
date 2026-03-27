"""
班级/年级维度分析扩展模块
- 班级对比分析：多个班级之间的整体水平对比
- 分数段分布演化：追踪各分数段人数变化趋势
- 标准分/等级分转换：消除不同考试难度差异，实现跨考试对比
"""
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from scipy import stats


@dataclass
class ClassComparison:
    """班级对比数据"""
    class_name: str
    total_students: int
    avg_score: float
    max_score: float
    min_score: float
    std_score: float
    pass_rate: float
    excellent_rate: float
    median_score: float


@dataclass
class ScoreDistribution:
    """分数段分布"""
    range_name: str  # 分数段名称，如 "90-100"
    min_score: float
    max_score: float
    count: int
    percentage: float
    students: List[int]  # 学生 ID 列表


@dataclass
class StandardScoreResult:
    """标准分转换结果"""
    student_id: int
    raw_score: float  # 原始分
    standard_score: float  # 标准分 (Z 分)
    t_score: float  # T 分 (平均分 500，标准差 100)
    percentile: float  # 百分位
    grade_level: str  # 等级 (A/B/C/D/E)


class ClassComparator:
    """班级对比分析器"""

    # 分数段配置
    DEFAULT_RANGES = [
        (90, 100, "优秀 (90-100)"),
        (80, 89, "良好 (80-89)"),
        (70, 79, "中等 (70-79)"),
        (60, 69, "及格 (60-69)"),
        (0, 59, "不及格 (0-59)")
    ]

    def __init__(self):
        """初始化班级对比分析器"""
        pass

    def analyze_class(self, scores: List[float], class_name: str = "") -> ClassComparison:
        """
        分析单个班级数据

        Args:
            scores: 学生成绩列表
            class_name: 班级名称

        Returns:
            ClassComparison 班级分析数据
        """
        if not scores:
            return ClassComparison(
                class_name=class_name,
                total_students=0,
                avg_score=0,
                max_score=0,
                min_score=0,
                std_score=0,
                pass_rate=0,
                excellent_rate=0,
                median_score=0
            )

        n = len(scores)
        avg = sum(scores) / n
        std = np.std(scores, ddof=1) if n > 1 else 0
        pass_count = sum(1 for s in scores if s >= 60)
        excellent_count = sum(1 for s in scores if s >= 85)

        return ClassComparison(
            class_name=class_name,
            total_students=n,
            avg_score=round(avg, 2),
            max_score=max(scores),
            min_score=min(scores),
            std_score=round(std, 2),
            pass_rate=round(pass_count / n * 100, 1),
            excellent_rate=round(excellent_count / n * 100, 1),
            median_score=round(np.median(scores), 1)
        )

    def compare_multiple_classes(self, class_data: Dict[str, List[float]]) -> List[ClassComparison]:
        """
        对比多个班级

        Args:
            class_data: {班级名：[成绩列表]}

        Returns:
            班级对比数据列表
        """
        results = []
        for class_name, scores in class_data.items():
            results.append(self.analyze_class(scores, class_name))

        # 按平均分降序排列
        results.sort(key=lambda x: x.avg_score, reverse=True)
        return results

    def create_class_comparison_chart(self, comparisons: List[ClassComparison]) -> go.Figure:
        """
        创建班级对比柱状图

        Args:
            comparisons: 班级对比数据列表

        Returns:
            Plotly 柱状图
        """
        if not comparisons:
            fig = go.Figure()
            fig.add_annotation(text="暂无班级数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="班级对比分析")
            return fig

        class_names = [c.class_name for c in comparisons]

        fig = go.Figure()

        # 平均分
        fig.add_trace(go.Bar(
            name='平均分',
            x=class_names,
            y=[c.avg_score for c in comparisons],
            marker_color='#3498db',
            text=[f"{c.avg_score:.1f}" for c in comparisons],
            textposition='auto'
        ))

        # 优秀率
        fig.add_trace(go.Bar(
            name='优秀率 (%)',
            x=class_names,
            y=[c.excellent_rate for c in comparisons],
            marker_color='#27ae60',
            text=[f"{c.excellent_rate:.1f}%" for c in comparisons],
            textposition='auto'
        ))

        # 及格率
        fig.add_trace(go.Bar(
            name='及格率 (%)',
            x=class_names,
            y=[c.pass_rate for c in comparisons],
            marker_color='#f39c12',
            text=[f"{c.pass_rate:.1f}%" for c in comparisons],
            textposition='auto'
        ))

        fig.update_layout(
            title="班级对比分析",
            xaxis_title="班级",
            yaxis_title="分数/百分比",
            barmode='group',
            height=450,
            showlegend=True
        )

        return fig

    def create_radar_comparison(self, comparisons: List[ClassComparison]) -> go.Figure:
        """
        创建班级雷达对比图

        Args:
            comparisons: 班级对比数据列表

        Returns:
            Plotly 雷达图
        """
        if not comparisons:
            fig = go.Figure()
            fig.add_annotation(text="暂无班级数据", showarrow=False, font_size=20)
            fig.update_layout(height=450, title="班级能力雷达对比")
            return fig

        # 归一化各指标到 0-100
        max_avg = max(c.avg_score for c in comparisons) or 100
        max_pass = max(c.pass_rate for c in comparisons) or 100
        max_excel = max(c.excellent_rate for c in comparisons) or 100
        max_median = max(c.median_score for c in comparisons) or 100

        categories = ['平均分', '中位数', '及格率', '优秀率', '稳定性']

        fig = go.Figure()

        for comp in comparisons:
            # 稳定性用标准差的倒数表示（标准差越小越稳定）
            max_std = max(c.std_score for c in comparisons) or 1
            stability = 100 * (1 - comp.std_score / max_std) if max_std > 0 else 100

            values = [
                comp.avg_score / max_avg * 100,
                comp.median_score / max_median * 100,
                comp.pass_rate,
                comp.excellent_rate,
                stability
            ]
            values += values[:1]  # 闭合
            cats = categories + [categories[0]]

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=cats,
                name=comp.class_name,
                fill='toself',
                opacity=0.3
            ))

        fig.update_layout(
            title="班级能力雷达对比",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            height=450
        )

        return fig

    def create_distribution_heatmap(self, class_data: Dict[str, List[float]]) -> go.Figure:
        """
        创建分数段分布热力图

        Args:
            class_data: {班级名：[成绩列表]}

        Returns:
            Plotly 热力图
        """
        if not class_data:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="分数段分布热力图")
            return fig

        # 计算每个班级各分数段的比例
        ranges = self.DEFAULT_RANGES
        range_names = [r[2] for r in ranges]
        class_names = list(class_data.keys())

        heatmap_data = []
        for class_name in class_names:
            scores = class_data[class_name]
            row = []
            for min_s, max_s, _ in ranges:
                count = sum(1 for s in scores if min_s <= s <= max_s)
                pct = count / len(scores) * 100 if scores else 0
                row.append(round(pct, 1))
            heatmap_data.append(row)

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=range_names,
            y=class_names,
            colorscale='RdYlGn',
            zmid=50,
            text=heatmap_data,
            texttemplate='%{text}%',
            textfont={"size": 10},
            hovertemplate='<b>%{y}</b><br>%{x}<br>%{z:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            title="分数段分布热力图",
            xaxis_title="分数段",
            yaxis_title="班级",
            height=400
        )

        return fig


class ScoreDistributionAnalyzer:
    """分数段分布分析器"""

    def __init__(self):
        """初始化分析器"""
        self.comparator = ClassComparator()

    def analyze_distribution_over_time(self, time_series_data: Dict[str, List[float]]) -> List[Dict]:
        """
        分析分数段分布随时间演化

        Args:
            time_series_data: {时间点：[成绩列表]}，时间点可以是考试名称或日期

        Returns:
            分布演化数据
        """
        evolution = []

        for time_point, scores in time_series_data.items():
            dist = self._calculate_distribution(scores)
            evolution.append({
                'time': time_point,
                'total': len(scores),
                'distribution': dist
            })

        return evolution

    def _calculate_distribution(self, scores: List[float]) -> Dict[str, ScoreDistribution]:
        """计算分数段分布"""
        result = {}
        for min_s, max_s, name in self.comparator.DEFAULT_RANGES:
            count = sum(1 for s in scores if min_s <= s <= max_s)
            pct = count / len(scores) * 100 if scores else 0
            result[name] = ScoreDistribution(
                range_name=name,
                min_score=min_s,
                max_score=max_s,
                count=count,
                percentage=round(pct, 1),
                students=[]
            )
        return result

    def create_distribution_evolution_chart(self, time_series_data: Dict[str, List[float]]) -> go.Figure:
        """
        创建分数段分布演化堆叠面积图

        Args:
            time_series_data: {时间点：[成绩列表]}

        Returns:
            Plotly 堆叠面积图
        """
        if not time_series_data:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="分数段分布演化")
            return fig

        time_points = list(time_series_data.keys())

        # 为每个分数段创建数据系列
        range_colors = {
            '优秀 (90-100)': '#27ae60',
            '良好 (80-89)': '#2ecc71',
            '中等 (70-79)': '#f1c40f',
            '及格 (60-69)': '#e67e22',
            '不及格 (0-59)': '#e74c3c'
        }

        fig = go.Figure()

        for range_name in range_colors.keys():
            percentages = []
            for time_point in time_points:
                scores = time_series_data[time_point]
                count = sum(1 for s in scores if self._in_range(s, range_name))
                pct = count / len(scores) * 100 if scores else 0
                percentages.append(pct)

            fig.add_trace(go.Area(
                name=range_name,
                x=time_points,
                y=percentages,
                stackgroup='one',
                line=dict(width=0.5),
                color=range_colors[range_name],
                hovertemplate='<b>%{x}</b><br>%{y:.1f}%<extra></extra>'
            ))

        fig.update_layout(
            title="分数段分布演化趋势",
            xaxis_title="考试",
            yaxis_title="百分比 (%)",
            yaxis_range=[0, 100],
            height=450,
            showlegend=True,
            area_groupnorm='percent'
        )

        return fig

    def _in_range(self, score: float, range_name: str) -> bool:
        """判断分数是否在指定范围"""
        ranges = {
            '优秀 (90-100)': (90, 100),
            '良好 (80-89)': (80, 89),
            '中等 (70-79)': (70, 79),
            '及格 (60-69)': (60, 69),
            '不及格 (0-59)': (0, 59)
        }
        min_s, max_s = ranges.get(range_name, (0, 100))
        return min_s <= score <= max_s


class StandardScoreConverter:
    """标准分转换器"""

    # 等级划分
    GRADE_LEVELS = [
        (90, 100, 'A'),  # 优秀
        (80, 89, 'B'),   # 良好
        (70, 79, 'C'),   # 中等
        (60, 69, 'D'),   # 及格
        (0, 59, 'E')     # 不及格
    ]

    def __init__(self, population_scores: List[float] = None):
        """
        初始化转换器

        Args:
            population_scores: 总体成绩分布（用于计算标准分）
        """
        self.population_mean = np.mean(population_scores) if population_scores else 75
        self.population_std = np.std(population_scores, ddof=1) if population_scores else 15
        if self.population_std == 0:
            self.population_std = 15  # 避免除零

    def convert(self, raw_score: float, student_id: int = 0) -> StandardScoreResult:
        """
        转换原始分为标准分

        Args:
            raw_score: 原始分
            student_id: 学生 ID

        Returns:
            StandardScoreResult 转换结果
        """
        # Z 分数（标准分）
        z_score = (raw_score - self.population_mean) / self.population_std

        # T 分数（平均分 500，标准差 100）
        t_score = 500 + 100 * z_score

        # 百分位
        percentile = stats.norm.cdf(z_score) * 100

        # 等级
        grade = 'E'
        for min_s, max_s, g in self.GRADE_LEVELS:
            if min_s <= raw_score <= max_s:
                grade = g
                break

        return StandardScoreResult(
            student_id=student_id,
            raw_score=raw_score,
            standard_score=round(z_score, 2),
            t_score=round(t_score, 1),
            percentile=round(percentile, 1),
            grade_level=grade
        )

    def convert_batch(self, scores: List[float]) -> List[StandardScoreResult]:
        """
        批量转换

        Args:
            scores: 原始分列表

        Returns:
            标准分结果列表
        """
        return [self.convert(score, i) for i, score in enumerate(scores)]

    def create_conversion_chart(self, results: List[StandardScoreResult]) -> go.Figure:
        """
        创建标准分转换散点图

        Args:
            results: 标准分结果列表

        Returns:
            Plotly 散点图
        """
        if not results:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="原始分 - 标准分对比")
            return fig

        raw_scores = [r.raw_score for r in results]
        t_scores = [r.t_score for r in results]
        percentiles = [r.percentile for r in results]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=raw_scores,
            y=t_scores,
            mode='markers',
            marker=dict(
                size=10,
                color=percentiles,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="百分位")
            ),
            text=[f"原始分：{r.raw_score}<br>T 分：{r.t_score:.1f}<br>百分位：{r.percentile}%"
                 for r in results],
            hoverinfo='text',
            name='学生'
        ))

        # 添加平均线
        fig.add_hline(
            y=500,
            line_dash="dash",
            line_color="gray",
            annotation_text="平均 T 分 (500)",
            annotation_position="right"
        )

        fig.update_layout(
            title="原始分 - 标准分 (T 分) 对比",
            xaxis_title="原始分",
            yaxis_title="T 分 (平均分 500, 标准差 100)",
            xaxis_range=[0, 100],
            yaxis_range=[300, 700],
            height=450,
            showlegend=False
        )

        return fig

    def create_grade_distribution_chart(self, results: List[StandardScoreResult]) -> go.Figure:
        """
        创建等级分布饼图

        Args:
            results: 标准分结果列表

        Returns:
            Plotly 饼图
        """
        if not results:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="等级分布")
            return fig

        # 统计各等级人数
        grade_counts = {}
        for r in results:
            grade = r.grade_level
            grade_counts[grade] = grade_counts.get(grade, 0) + 1

        grades = sorted(grade_counts.keys())
        counts = [grade_counts[g] for g in grades]
        percentages = [c / len(results) * 100 for c in counts]

        grade_names = {
            'A': '优秀 (90-100)',
            'B': '良好 (80-89)',
            'C': '中等 (70-79)',
            'D': '及格 (60-69)',
            'E': '不及格 (0-59)'
        }

        colors = ['#27ae60', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']

        fig = go.Figure(data=[go.Pie(
            labels=[f"{g} - {grade_names.get(g, g)}" for g in grades],
            values=counts,
            marker_colors=colors,
            hole=0.4,
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>人数：%{value}<br>百分比：%{percent:.1f}%<extra></extra>'
        )])

        fig.update_layout(
            title="等级分布",
            height=400,
            showlegend=True
        )

        return fig
