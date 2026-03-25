"""
试卷分析模块
- 试卷质量分析：难度、区分度、信度分析
- 题目得分率分析：识别全班共性薄弱题目
- 自动组卷优化：根据学生水平智能推荐试卷难度
"""
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from scipy import stats


@dataclass
class ExamQualityAnalysis:
    """试卷质量分析结果"""
    exam_name: str
    total_students: int
    avg_score: float
    difficulty: float  # 难度系数 (0-1, 越小越难)
    discrimination: float  # 区分度 (0-1, 越大区分度越好)
    reliability: float  # 信度 (0-1, 越大越可靠)
    std_deviation: float  # 标准差
    score_range: Tuple[float, float]  # 分数范围


@dataclass
class QuestionAnalysis:
    """题目分析结果"""
    question_id: str
    question_type: str  # 题型
    knowledge_point: str  # 知识点
    full_score: float  # 满分
    avg_score: float  # 平均分
    difficulty: float  # 难度系数
    discrimination: float  # 区分度
    error_rate: float  # 错误率


class ExamQualityAnalyzer:
    """试卷质量分析器"""

    def __init__(self):
        """初始化分析器"""
        pass

    def analyze_exam_quality(self, scores: List[float],
                              exam_name: str = "") -> ExamQualityAnalysis:
        """
        分析试卷质量

        Args:
            scores: 学生成绩列表
            exam_name: 考试名称

        Returns:
            试卷质量分析结果
        """
        if not scores or len(scores) < 2:
            return ExamQualityAnalysis(
                exam_name=exam_name,
                total_students=len(scores) if scores else 0,
                avg_score=0,
                difficulty=0,
                discrimination=0,
                reliability=0,
                std_deviation=0,
                score_range=(0, 0)
            )

        n = len(scores)
        avg = sum(scores) / n
        std = np.std(scores, ddof=1)

        # 难度系数：1 - (平均分/满分)，假设满分 100
        max_score = 100
        difficulty = 1 - (avg / max_score)

        # 区分度：高分组 (前 27%) 平均分 - 低分组 (后 27%) 平均分
        sorted_scores = sorted(scores)
        group_size = max(1, int(n * 0.27))
        low_group = sorted_scores[:group_size]
        high_group = sorted_scores[-group_size:]
        discrimination = (sum(high_group) / len(high_group) - sum(low_group) / len(low_group)) / max_score

        # 信度：使用简化的 Cronbach's alpha 近似
        # 简化计算：用折半信度近似
        if n >= 10:
            mid = n // 2
            first_half = scores[:mid]
            second_half = scores[mid:]
            if np.std(first_half) > 0 and np.std(second_half) > 0:
                corr = np.corrcoef(first_half, second_half)[0, 1]
                reliability = max(0, min(1, corr)) if not np.isnan(corr) else 0
            else:
                reliability = 0
        else:
            reliability = 0

        return ExamQualityAnalysis(
            exam_name=exam_name,
            total_students=n,
            avg_score=round(avg, 2),
            difficulty=round(difficulty, 3),
            discrimination=round(discrimination, 3),
            reliability=round(reliability, 3),
            std_deviation=round(std, 2),
            score_range=(min(scores), max(scores))
        )

    def create_exam_quality_chart(self, analyses: List[ExamQualityAnalysis]) -> go.Figure:
        """
        创建试卷质量对比图

        Args:
            analyses: 试卷质量分析结果列表

        Returns:
            Plotly 雷达图
        """
        if not analyses:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=450, title="试卷质量分析")
            return fig

        # 归一化指标
        max_difficulty = max(a.difficulty for a in analyses) or 1
        max_discrimination = max(a.discrimination for a in analyses) or 1
        max_reliability = max(a.reliability for a in analyses) or 1
        max_std = max(a.std_deviation for a in analyses) or 1

        categories = ['难度', '区分度', '信度', '离散度']

        fig = go.Figure()

        for analysis in analyses:
            values = [
                analysis.difficulty / max_difficulty * 100,
                analysis.discrimination / max_discrimination * 100,
                analysis.reliability / max_reliability * 100,
                analysis.std_deviation / max_std * 100
            ]
            values += values[:1]
            cats = categories + [categories[0]]

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=cats,
                name=analysis.exam_name,
                fill='toself',
                fillopacity=0.3
            ))

        fig.update_layout(
            title="试卷质量对比",
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

    def create_difficulty_distribution_chart(self, analyses: List[ExamQualityAnalysis]) -> go.Figure:
        """
        创建难度分布直方图

        Args:
            analyses: 试卷质量分析结果列表

        Returns:
            Plotly 直方图
        """
        if not analyses:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="试卷难度分布")
            return fig

        difficulties = [a.difficulty for a in analyses]
        exam_names = [a.exam_name for a in analyses]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=exam_names,
            y=difficulties,
            marker_color=['#27ae60' if d < 0.3 else '#f39c12' if d < 0.5 else '#e74c3c'
                         for d in difficulties],
            text=[f"{d:.3f}" for d in difficulties],
            textposition='auto'
        ))

        fig.add_hline(y=0.3, line_dash="dash", line_color="green",
                     annotation_text="容易", annotation_position="right")
        fig.add_hline(y=0.5, line_dash="dash", line_color="orange",
                     annotation_text="中等", annotation_position="right")
        fig.add_hline(y=0.7, line_dash="dash", line_color="red",
                     annotation_text="困难", annotation_position="right")

        fig.update_layout(
            title="试卷难度系数分布（难度系数 = 1 - 平均分/满分）",
            xaxis_title="考试",
            yaxis_title="难度系数",
            yaxis_range=[0, 1],
            height=400,
            showlegend=False
        )

        return fig


class QuestionScoreAnalyzer:
    """题目得分率分析器"""

    def __init__(self):
        """初始化分析器"""
        pass

    def analyze_question_scores(self, question_scores: Dict[str, List[float]],
                                 full_scores: Dict[str, float] = None) -> List[QuestionAnalysis]:
        """
        分析题目得分情况

        Args:
            question_scores: {题目 ID: [学生得分列表]}
            full_scores: {题目 ID: 满分}，默认为 10

        Returns:
            题目分析结果列表
        """
        if full_scores is None:
            full_scores = {qid: 10 for qid in question_scores.keys()}

        results = []

        for qid, scores in question_scores.items():
            if not scores:
                continue

            n = len(scores)
            full_score = full_scores.get(qid, 10)
            avg = sum(scores) / n

            # 难度系数
            difficulty = 1 - (avg / full_score)

            # 错误率
            error_rate = sum(1 for s in scores if s < full_score * 0.6) / n

            # 区分度（简化计算）
            sorted_scores = sorted(scores)
            group_size = max(1, int(n * 0.27))
            low_group_avg = sum(sorted_scores[:group_size]) / group_size
            high_group_avg = sum(sorted_scores[-group_size:]) / group_size
            discrimination = (high_group_avg - low_group_avg) / full_score

            results.append(QuestionAnalysis(
                question_id=qid,
                question_type='unknown',
                knowledge_point='unknown',
                full_score=full_score,
                avg_score=round(avg, 2),
                difficulty=round(difficulty, 3),
                discrimination=round(discrimination, 3),
                error_rate=round(error_rate, 3)
            ))

        # 按错误率降序排列
        results.sort(key=lambda r: r.error_rate, reverse=True)
        return results

    def create_question_error_rate_chart(self, analyses: List[QuestionAnalysis]) -> go.Figure:
        """
        创建题目错误率柱状图

        Args:
            analyses: 题目分析结果列表

        Returns:
            Plotly 柱状图
        """
        if not analyses:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="题目错误率分析")
            return fig

        # 取错误率最高的 10 题
        top_errors = analyses[:10]

        question_ids = [f"题{ i + 1}" for i in range(len(top_errors))]
        error_rates = [r.error_rate * 100 for r in top_errors]
        difficulties = [r.difficulty for r in top_errors]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=question_ids,
            y=error_rates,
            marker_color=['#e74c3c' if er > 50 else '#f39c12' if er > 30 else '#27ae60'
                         for er in error_rates],
            text=[f"{er:.1f}%" for er in error_rates],
            textposition='auto',
            name='错误率'
        ))

        fig.update_layout(
            title="高频错误题目 TOP10",
            xaxis_title="题目",
            yaxis_title="错误率 (%)",
            yaxis_range=[0, 100],
            height=400,
            showlegend=False
        )

        return fig

    def create_question_heatmap(self, question_scores: Dict[str, List[float]],
                                 student_ids: List[int] = None) -> go.Figure:
        """
        创建题目 - 学生得分热力图

        Args:
            question_scores: {题目 ID: [学生得分列表]}
            student_ids: 学生 ID 列表

        Returns:
            Plotly 热力图
        """
        if not question_scores:
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="题目得分热力图")
            return fig

        # 准备数据
        questions = list(question_scores.keys())
        n_students = len(list(question_scores.values())[0])

        if student_ids is None:
            student_ids = list(range(1, n_students + 1))

        # 计算得分率
        heatmap_data = []
        for qid in questions:
            scores = question_scores[qid]
            # 假设满分 10 分
            rates = [min(100, s / 10 * 100) for s in scores]
            heatmap_data.append(rates)

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=[f"学生{s}" for s in student_ids[:50]],  # 限制显示数量
            y=questions[:20],  # 限制显示数量
            colorscale='RdYlGn',
            zmid=60,
            hovertemplate='<b>%{y}</b><br>%{x}<br>得分率：%{z:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            title="题目 - 学生得分热力图（绿色=高分，红色=低分）",
            xaxis_title="学生",
            yaxis_title="题目",
            height=500
        )

        return fig


class SmartPaperComposer:
    """智能组卷优化器"""

    # 知识点 - 题目数据库（简化版）
    QUESTION_POOL = {
        'G1U03': [
            {'id': 'Q1001', 'type': 'calculation', 'difficulty': 1, 'score': 5},
            {'id': 'Q1002', 'type': 'application', 'difficulty': 2, 'score': 10},
        ],
        'G1U05': [
            {'id': 'Q2001', 'type': 'calculation', 'difficulty': 1, 'score': 5},
            {'id': 'Q2002', 'type': 'fill_blank', 'difficulty': 2, 'score': 8},
            {'id': 'Q2003', 'type': 'application', 'difficulty': 3, 'score': 12},
        ],
        'G2U04': [
            {'id': 'Q3001', 'type': 'calculation', 'difficulty': 1, 'score': 5},
            {'id': 'Q3002', 'type': 'application', 'difficulty': 2, 'score': 10},
        ],
    }

    def __init__(self, knowledge_points: Dict):
        """
        初始化组卷器

        Args:
            knowledge_points: 知识点字典
        """
        self.knowledge_points = knowledge_points

    def compose_paper(self, student_level: float,
                       target_score: float = 85,
                       total_score: int = 100,
                       num_questions: int = 10) -> Dict:
        """
        智能组卷

        Args:
            student_level: 学生水平 (0-100)
            target_score: 目标分数
            total_score: 试卷总分
            num_questions: 题目数量

        Returns:
            组卷结果
        """
        # 根据学生水平确定难度分布
        if student_level >= 85:
            difficulty_dist = {'easy': 0.2, 'medium': 0.5, 'hard': 0.3}
        elif student_level >= 70:
            difficulty_dist = {'easy': 0.3, 'medium': 0.5, 'hard': 0.2}
        else:
            difficulty_dist = {'easy': 0.4, 'medium': 0.4, 'hard': 0.2}

        # 计算各难度题目数量
        num_easy = int(num_questions * difficulty_dist['easy'])
        num_medium = int(num_questions * difficulty_dist['medium'])
        num_hard = num_questions - num_easy - num_medium

        # 从题库中选择题目
        selected = []
        all_questions = []

        for kp_code, questions in self.QUESTION_POOL.items():
            for q in questions:
                q['knowledge'] = kp_code
                q['knowledge_name'] = self.knowledge_points.get(kp_code, {}).name if hasattr(self.knowledge_points.get(kp_code), 'name') else kp_code
                all_questions.append(q)

        # 按难度分类
        easy_qs = [q for q in all_questions if q['difficulty'] == 1]
        medium_qs = [q for q in all_questions if q['difficulty'] == 2]
        hard_qs = [q for q in all_questions if q['difficulty'] == 3]

        # 选择题目
        import random
        random.shuffle(easy_qs)
        random.shuffle(medium_qs)
        random.shuffle(hard_qs)

        selected = easy_qs[:num_easy] + medium_qs[:num_medium] + hard_qs[:num_hard]

        # 计算总分
        paper_total = sum(q['score'] for q in selected)

        return {
            'questions': selected,
            'total_score': paper_total,
            'difficulty_distribution': difficulty_dist,
            'num_questions': len(selected),
            'recommended_time': len(selected) * 5  # 每题 5 分钟
        }

    def create_paper_preview_chart(self, paper_result: Dict) -> go.Figure:
        """
        创建试卷预览图

        Args:
            paper_result: 组卷结果

        Returns:
            Plotly 饼图
        """
        if not paper_result or not paper_result.get('questions'):
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="试卷结构预览")
            return fig

        questions = paper_result['questions']

        # 统计难度分布
        difficulty_counts = {1: 0, 2: 0, 3: 0}
        for q in questions:
            diff = q.get('difficulty', 1)
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

        labels = ['基础题', '提升题', '挑战题']
        values = [difficulty_counts[1], difficulty_counts[2], difficulty_counts[3]]
        colors = ['#27ae60', '#f39c12', '#e74c3c']

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hole=0.4,
            textinfo='label+percent+value',
            hovertemplate='<b>%{label}</b><br>数量：%{value}<extra></extra>'
        )])

        fig.update_layout(
            title=f"试卷结构预览（共{len(questions)}题，总分{paper_result.get('total_score', 0)}分）",
            height=400,
            showlegend=True
        )

        return fig

    def create_score_prediction_chart(self, student_level: float,
                                       paper_result: Dict) -> go.Figure:
        """
        创建得分预测图

        Args:
            student_level: 学生水平
            paper_result: 组卷结果

        Returns:
            Plotly 仪表图
        """
        # 预测得分
        questions = paper_result.get('questions', [])
        total_score = paper_result.get('total_score', 100)

        # 简化预测：根据难度和学生水平计算期望得分
        difficulty_weights = {1: 0.95, 2: 0.75, 3: 0.5}
        expected_rate = 0

        for q in questions:
            diff = q.get('difficulty', 1)
            weight = difficulty_weights.get(diff, 0.5)
            # 学生水平越高，得分率越高
            expected_rate += weight * (student_level / 100)

        if questions:
            expected_rate /= len(questions)
        else:
            expected_rate = student_level / 100

        predicted_score = total_score * expected_rate

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=predicted_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"预测得分（满分{total_score}分）", 'font': {'size': 24}},
            delta={'reference': total_score * 0.85, 'increasing': {'color': "#27ae60"}},
            gauge={
                'axis': {'range': [0, total_score], 'tickwidth': 1},
                'bar': {'color': "#3498db"},
                'bgcolor': "white",
                'borderwidth': 2,
                'steps': [
                    {'range': [0, total_score * 0.6], 'color': "#ffebee"},
                    {'range': [total_score * 0.6, total_score * 0.85], 'color': "#fff3e0"},
                    {'range': [total_score * 0.85, total_score], 'color': "#e8f5e9"}
                ],
            }
        ))

        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=50, b=50)
        )

        return fig
