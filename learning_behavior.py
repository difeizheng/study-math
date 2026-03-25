"""
学习行为分析模块
- 答题时间分析：答题速度和用时模式
- 复习效果追踪：基于艾宾浩斯遗忘曲线
- 学习习惯画像：学习时间、频率、偏好分析
"""
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from collections import Counter


@dataclass
class TimeAnalysis:
    """时间分析结果"""
    avg_time_per_question: float  # 平均每题用时（秒）
    total_study_time: int  # 总学习时长（分钟）
    time_distribution: Dict[str, int]  # 时间分布 {时段：题目数}
    efficiency_score: float  # 效率评分
    pace: str  # 节奏 (fast/medium/slow)


@dataclass
class ReviewEffect:
    """复习效果"""
    knowledge_code: str
    knowledge_name: str
    initial_mastery: float  # 初始掌握度
    current_mastery: float  # 当前掌握度
    retention_rate: float  # 保持率
    review_count: int  # 复习次数
    next_review_date: str  # 下次复习日期
    effect: str  # 效果等级


@dataclass
class HabitProfile:
    """学习习惯画像"""
    student_id: int
    study_time_preference: str  # 偏好时段 (morning/afternoon/evening)
    study_frequency: float  # 学习频率 (次/周)
    consistency_score: float  # 坚持度评分
    focus_score: float  # 专注度评分
    persistence_score: float  # 毅力评分
    learning_style: str  # 学习风格
    habit_tags: List[str]  # 习惯标签
    suggestions: List[str]  # 改进建议


class TimeAnalyzer:
    """答题时间分析器"""

    # 时段定义
    TIME_PERIODS = {
        'morning': (6, 12, '早晨'),
        'afternoon': (12, 18, '下午'),
        'evening': (18, 22, '晚上'),
        'night': (22, 24, '深夜')
    }

    def __init__(self):
        """初始化时间分析器"""
        pass

    def analyze_time(self, time_records: List[Dict]) -> TimeAnalysis:
        """
        分析答题时间

        Args:
            time_records: 时间记录 [{question_id, time_spent, timestamp}]

        Returns:
            TimeAnalysis 分析结果
        """
        if not time_records:
            return TimeAnalysis(
                avg_time_per_question=0,
                total_study_time=0,
                time_distribution={},
                efficiency_score=0,
                pace='unknown'
            )

        # 计算平均用时
        times = [r.get('time_spent', 60) for r in time_records]
        avg_time = sum(times) / len(times)

        # 总学习时长（分钟）
        total_minutes = sum(times) / 60

        # 时间分布
        distribution = {'早晨': 0, '下午': 0, '晚上': 0, '深夜': 0}
        for record in time_records:
            timestamp = record.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    hour = dt.hour
                    for period, (start, end, name) in self.TIME_PERIODS.items():
                        if start <= hour < end:
                            distribution[name] = distribution.get(name, 0) + 1
                            break
                except:
                    pass

        # 效率评分（基于用时合理性）
        # 理想用时：30-90 秒/题
        efficiency = 0
        for t in times:
            if 30 <= t <= 90:
                efficiency += 1
            elif 20 <= t < 30 or 90 < t <= 120:
                efficiency += 0.7
            else:
                efficiency += 0.3
        efficiency_score = efficiency / len(times) * 100

        # 节奏判断
        if avg_time < 30:
            pace = 'fast'
        elif avg_time < 60:
            pace = 'medium'
        else:
            pace = 'slow'

        return TimeAnalysis(
            avg_time_per_question=round(avg_time, 1),
            total_study_time=round(total_minutes),
            time_distribution=distribution,
            efficiency_score=round(efficiency_score, 1),
            pace=pace
        )

    def create_time_distribution_chart(self, time_records: List[Dict]) -> go.Figure:
        """
        创建时间分布图

        Args:
            time_records: 时间记录

        Returns:
            Plotly 图表
        """
        analysis = self.analyze_time(time_records)

        if not analysis.time_distribution:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="学习时间分布")
            return fig

        # 饼图
        labels = list(analysis.time_distribution.keys())
        values = list(analysis.time_distribution.values())

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo='label+percent+value',
            hovertemplate='<b>%{label}</b><br>%{value}题<extra></extra>'
        )])

        fig.update_layout(
            title=f"学习时间分布（效率评分：{analysis.efficiency_score}）",
            height=400
        )

        return fig

    def create_pace_analysis_chart(self, time_records: List[Dict]) -> go.Figure:
        """
        创建答题节奏分析图

        Args:
            time_records: 时间记录

        Returns:
            Plotly 图表
        """
        if not time_records:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="答题节奏分析")
            return fig

        times = [r.get('time_spent', 60) for r in time_records]

        fig = go.Figure()

        # 用时折线图
        fig.add_trace(go.Scatter(
            y=times,
            mode='lines+markers',
            line=dict(color='#3498db', width=2),
            marker=dict(size=6),
            name='用时',
            hovertemplate='第%{x}题：%{y}秒<extra></extra>'
        ))

        # 参考线
        fig.add_hline(y=30, line_dash="dash", line_color="green",
                     annotation_text="快速", annotation_position="right", opacity=0.5)
        fig.add_hline(y=60, line_dash="dash", line_color="orange",
                     annotation_text="中等", annotation_position="right", opacity=0.5)
        fig.add_hline(y=90, line_dash="dash", line_color="red",
                     annotation_text="较慢", annotation_position="right", opacity=0.5)

        fig.update_layout(
            title="答题节奏分析",
            xaxis_title="题目序号",
            yaxis_title="用时（秒）",
            height=400,
            showlegend=False
        )

        return fig


class ReviewTracker:
    """复习效果追踪器"""

    # 艾宾浩斯遗忘曲线间隔（天）
    EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]

    def __init__(self, knowledge_points: Dict = None):
        """
        初始化复习追踪器

        Args:
            knowledge_points: 知识点字典
        """
        self.knowledge_points = knowledge_points or {}

    def track_review_effect(self, review_records: List[Dict]) -> List[ReviewEffect]:
        """
        追踪复习效果

        Args:
            review_records: 复习记录 [{knowledge_code, review_dates, mastery_scores}]

        Returns:
            复习效果列表
        """
        if not review_records:
            return []

        effects = []
        for record in review_records:
            kp_code = record.get('knowledge_code', '')
            kp_name = self._get_kp_name(kp_code)

            mastery_scores = record.get('mastery_scores', [])
            review_dates = record.get('review_dates', [])

            if len(mastery_scores) >= 2:
                initial = mastery_scores[0]
                current = mastery_scores[-1]
                retention = current / initial * 100 if initial > 0 else 0
            else:
                initial = mastery_scores[0] if mastery_scores else 0
                current = initial
                retention = 100

            # 计算下次复习日期
            review_count = len(review_dates)
            if review_count > 0 and review_count <= len(self.EBBINGHAUS_INTERVALS):
                interval = self.EBBINGHAUS_INTERVALS[review_count - 1]
                last_review = datetime.fromisoformat(review_dates[-1]) if review_dates else datetime.now()
                next_review = last_review + timedelta(days=interval)
                next_review_str = next_review.strftime("%Y-%m-%d")
            else:
                next_review_str = "已完成周期"

            # 效果等级
            if retention >= 90:
                effect = '优秀'
            elif retention >= 70:
                effect = '良好'
            elif retention >= 50:
                effect = '一般'
            else:
                effect = '需加强'

            effects.append(ReviewEffect(
                knowledge_code=kp_code,
                knowledge_name=kp_name,
                initial_mastery=initial,
                current_mastery=current,
                retention_rate=round(retention, 1),
                review_count=review_count,
                next_review_date=next_review_str,
                effect=effect
            ))

        return effects

    def _get_kp_name(self, code: str) -> str:
        """获取知识点名称"""
        kp = self.knowledge_points.get(code)
        return kp.name if hasattr(kp, 'name') else code

    def create_review_curve_chart(self, review_records: List[Dict]) -> go.Figure:
        """
        创建遗忘曲线图

        Args:
            review_records: 复习记录

        Returns:
            Plotly 图表
        """
        if not review_records:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="艾宾浩斯遗忘曲线")
            return fig

        fig = go.Figure()

        # 理论遗忘曲线
        days = list(range(0, 31))
        theoretical_retention = [100 * (0.5 ** (d / 7)) for d in days]  # 简化模型

        fig.add_trace(go.Scatter(
            x=days, y=theoretical_retention,
            mode='lines',
            line=dict(color='#95a5a6', width=2, dash='dash'),
            name='理论遗忘曲线'
        ))

        # 实际复习数据
        colors = ['#3498db', '#27ae60', '#e74c3c', '#f39c12', '#1abc9c']
        for i, record in enumerate(review_records[:5]):  # 最多显示 5 个知识点
            mastery_scores = record.get('mastery_scores', [])
            review_dates = record.get('review_dates', [])

            if review_dates and mastery_scores:
                # 计算天数
                base_date = datetime.fromisoformat(review_dates[0])
                review_days = [(datetime.fromisoformat(d) - base_date).days for d in review_dates]

                kp_name = self._get_kp_name(record.get('knowledge_code', ''))

                fig.add_trace(go.Scatter(
                    x=review_days, y=mastery_scores,
                    mode='lines+markers',
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=8),
                    name=kp_name[:10]
                ))

        fig.update_layout(
            title="艾宾浩斯遗忘曲线与复习追踪",
            xaxis_title="天数",
            yaxis_title="保持率 (%)",
            xaxis_range=[0, 30],
            yaxis_range=[0, 100],
            height=450
        )

        return fig


class HabitProfiler:
    """学习习惯画像分析器"""

    # 学习风格定义
    LEARNING_STYLES = {
        'visual': {'name': '视觉型', 'description': '偏好图表和可视化学习'},
        'auditory': {'name': '听觉型', 'description': '偏好听讲和讨论'},
        'kinesthetic': {'name': '动觉型', 'description': '偏好实践操作'},
        'reading': {'name': '读写型', 'description': '偏好阅读和笔记'}
    }

    # 习惯标签
    HABIT_TAGS = {
        'early_bird': '早起学习',
        'night_owl': '熬夜学习',
        'consistent': '规律学习',
        'crammer': '临时抱佛脚',
        'steady': '循序渐进',
        'burst': '爆发式学习'
    }

    def __init__(self):
        """初始化画像分析器"""
        pass

    def analyze_habits(self, study_records: List[Dict],
                      error_records: List[Dict] = None) -> HabitProfile:
        """
        分析学习习惯

        Args:
            study_records: 学习记录 [{timestamp, duration, activity}]
            error_records: 错题记录

        Returns:
            HabitProfile 习惯画像
        """
        if not study_records:
            return HabitProfile(
                student_id=0,
                study_time_preference='unknown',
                study_frequency=0,
                consistency_score=0,
                focus_score=0,
                persistence_score=0,
                learning_style='unknown',
                habit_tags=[],
                suggestions=['请开始记录学习数据']
            )

        # 分析时段偏好
        time_preference = self._analyze_time_preference(study_records)

        # 计算学习频率
        frequency = self._calculate_frequency(study_records)

        # 坚持度评分
        consistency = self._calculate_consistency(study_records)

        # 专注度评分
        focus = self._calculate_focus(study_records)

        # 毅力评分
        persistence = self._calculate_persistence(study_records, error_records)

        # 学习风格（简化判断）
        learning_style = self._infer_learning_style(study_records)

        # 习惯标签
        tags = self._generate_habit_tags(time_preference, consistency, frequency)

        # 建议
        suggestions = self._generate_suggestions(
            time_preference, consistency, focus, persistence, tags
        )

        return HabitProfile(
            student_id=0,
            study_time_preference=time_preference,
            study_frequency=round(frequency, 1),
            consistency_score=round(consistency, 1),
            focus_score=round(focus, 1),
            persistence_score=round(persistence, 1),
            learning_style=learning_style,
            habit_tags=tags,
            suggestions=suggestions
        )

    def _analyze_time_preference(self, records: List[Dict]) -> str:
        """分析时段偏好"""
        period_counts = {'morning': 0, 'afternoon': 0, 'evening': 0, 'night': 0}

        for record in records:
            timestamp = record.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    hour = dt.hour
                    if 6 <= hour < 12:
                        period_counts['morning'] += 1
                    elif 12 <= hour < 18:
                        period_counts['afternoon'] += 1
                    elif 18 <= hour < 22:
                        period_counts['evening'] += 1
                    else:
                        period_counts['night'] += 1
                except:
                    pass

        return max(period_counts, key=period_counts.get) if any(period_counts.values()) else 'unknown'

    def _calculate_frequency(self, records: List[Dict]) -> float:
        """计算学习频率（次/周）"""
        if not records:
            return 0

        # 获取日期范围
        dates = set()
        for record in records:
            timestamp = record.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    dates.add(dt.date())
                except:
                    pass

        if not dates:
            return 0

        # 计算周数
        min_date = min(dates)
        max_date = max(dates)
        weeks = max(1, (max_date - min_date).days / 7)

        return len(dates) / weeks

    def _calculate_consistency(self, records: List[Dict]) -> float:
        """计算坚持度评分"""
        if not records:
            return 0

        # 获取学习日期
        dates = set()
        for record in records:
            timestamp = record.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    dates.add(dt.date())
                except:
                    pass

        if not dates:
            return 0

        # 计算连续学习天数
        sorted_dates = sorted(dates)
        max_streak = 1
        current_streak = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days <= 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        # 评分（满分 100）
        return min(100, max_streak * 10)

    def _calculate_focus(self, records: List[Dict]) -> float:
        """计算专注度评分"""
        if not records:
            return 0

        durations = [r.get('duration', 30) for r in records]
        avg_duration = sum(durations) / len(durations)

        # 理想专注时长：25-45 分钟（番茄工作法）
        if 25 <= avg_duration <= 45:
            return 100
        elif avg_duration < 25:
            return avg_duration / 25 * 100
        else:
            return max(50, 100 - (avg_duration - 45) * 2)

    def _calculate_persistence(self, records: List[Dict],
                               error_records: List[Dict] = None) -> float:
        """计算毅力评分"""
        # 基于错题订正情况
        if error_records:
            corrected = sum(1 for e in error_records if e.get('corrected', False))
            total = len(error_records)
            if total > 0:
                return corrected / total * 100

        # 基于学习记录稳定性
        if records:
            durations = [r.get('duration', 0) for r in records]
            if durations:
                return min(100, sum(durations) / len(durations) * 2)

        return 50

    def _infer_learning_style(self, records: List[Dict]) -> str:
        """推断学习风格"""
        # 简化实现：基于学习时间推断
        time_pref = self._analyze_time_preference(records)

        if time_pref == 'morning':
            return 'visual'
        elif time_pref == 'afternoon':
            return 'reading'
        elif time_pref == 'evening':
            return 'auditory'
        else:
            return 'kinesthetic'

    def _generate_habit_tags(self, time_pref: str, consistency: float,
                            frequency: float) -> List[str]:
        """生成习惯标签"""
        tags = []

        if time_pref == 'morning':
            tags.append('early_bird')
        elif time_pref == 'night':
            tags.append('night_owl')

        if consistency >= 70:
            tags.append('consistent')
        elif consistency < 30:
            tags.append('crammer')

        if 4 <= frequency <= 7:
            tags.append('steady')
        elif frequency > 7:
            tags.append('burst')

        return [self.HABIT_TAGS.get(tag, tag) for tag in tags]

    def _generate_suggestions(self, time_pref: str, consistency: float,
                             focus: float, persistence: float,
                             tags: List[str]) -> List[str]:
        """生成改进建议"""
        suggestions = []

        if consistency < 50:
            suggestions.append("📅 建议制定规律的学习计划，每天固定时间学习")
        if focus < 60:
            suggestions.append("🍅 尝试番茄工作法，25 分钟专注学习 +5 分钟休息")
        if persistence < 50:
            suggestions.append("💪 建立错题本，坚持订正和复习错题")
        if 'night_owl' in tags:
            suggestions.append("😴 熬夜学习影响效率，建议调整到白天学习")
        if 'crammer' in tags:
            suggestions.append("📚 临时抱佛脚效果有限，建议平时积累")

        if not suggestions:
            suggestions.append("✓ 学习习惯良好，继续保持！")

        return suggestions

    def create_habit_radar_chart(self, profile: HabitProfile) -> go.Figure:
        """
        创建习惯雷达图

        Args:
            profile: 习惯画像

        Returns:
            Plotly 图表
        """
        categories = ['坚持度', '专注度', '毅力', '频率', '规律性']

        # 计算各维度得分
        values = [
            profile.consistency_score,
            profile.focus_score,
            profile.persistence_score,
            min(100, profile.study_frequency * 15),  # 归一化到 100
            80 if profile.study_time_preference != 'unknown' else 40
        ]

        # 闭合
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]

        fig = go.Figure(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            line=dict(color='#3498db'),
            opacity=0.7
        ))

        fig.update_layout(
            title="学习习惯画像",
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            showlegend=False,
            height=450
        )

        return fig
