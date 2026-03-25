"""
成绩预测与预警模块
- 成绩趋势预测：基于历史数据用线性回归预测下次考试
- 智能预警系统：当学生成绩连续下滑或低于阈值时自动提醒
- 目标达成分析：设定目标分数，追踪达成进度
"""
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from scipy import stats


@dataclass
class PredictionResult:
    """预测结果"""
    predicted_score: float  # 预测分数
    confidence_interval: Tuple[float, float]  # 置信区间
    trend: str  # upward/stable/downward
    trend_slope: float  # 趋势斜率
    r_squared: float  # 拟合度
    prediction_reliable: bool  # 预测是否可靠


@dataclass
class WarningInfo:
    """预警信息"""
    warning_type: str  # declining/low_score/volatile/at_risk
    warning_name: str  # 成绩下滑/低分/波动大/危险
    severity: str  # low/medium/high
    message: str
    details: Dict[str, Any]


@dataclass
class GoalProgress:
    """目标进度"""
    goal_score: float  # 目标分数
    current_avg: float  # 当前平均分
    best_score: float  # 最高分
    progress_rate: float  # 进度百分比
    remaining_gap: float  # 剩余差距
    projected_reach: bool  # 预计能否达成
    exams_needed: int  # 还需要几次考试


class ScorePredictor:
    """成绩预测器"""

    def __init__(self):
        """初始化预测器"""
        pass

    def linear_regression_predict(self, scores: List[float],
                                   weeks: List[int] = None) -> PredictionResult:
        """
        使用线性回归预测下次考试成绩

        Args:
            scores: 历史成绩列表（按时间顺序）
            weeks: 周次列表（可选，默认为 1,2,3...）

        Returns:
            PredictionResult 预测结果
        """
        if len(scores) < 2:
            return PredictionResult(
                predicted_score=scores[0] if scores else 0,
                confidence_interval=(0, 100),
                trend='stable',
                trend_slope=0,
                r_squared=0,
                prediction_reliable=False
            )

        n = len(scores)
        if weeks is None:
            weeks = list(range(1, n + 1))

        # 线性回归
        slope, intercept, r_value, p_value, std_err = stats.linregress(weeks, scores)
        r_squared = r_value ** 2

        # 预测下次考试
        next_week = weeks[-1] + 1
        predicted_score = slope * next_week + intercept

        # 限制在 0-100 范围内
        predicted_score = max(0, min(100, predicted_score))

        # 计算置信区间（95%）
        t_value = 1.96  # 大样本近似
        se_pred = std_err * np.sqrt(1 + 1/n + (next_week - np.mean(weeks))**2 / np.sum((np.array(weeks) - np.mean(weeks))**2))
        margin = t_value * se_pred

        confidence_interval = (
            max(0, predicted_score - margin),
            min(100, predicted_score + margin)
        )

        # 判断趋势
        if slope > 2:
            trend = 'upward'
        elif slope < -2:
            trend = 'downward'
        else:
            trend = 'stable'

        # 评估预测可靠性
        prediction_reliable = (n >= 5 and r_squared >= 0.5) or (n >= 8 and r_squared >= 0.3)

        return PredictionResult(
            predicted_score=round(predicted_score, 1),
            confidence_interval=(round(confidence_interval[0], 1), round(confidence_interval[1], 1)),
            trend=trend,
            trend_slope=round(slope, 3),
            r_squared=round(r_squared, 3),
            prediction_reliable=prediction_reliable
        )

    def exponential_smoothing_predict(self, scores: List[float],
                                       alpha: float = 0.3) -> PredictionResult:
        """
        使用指数平滑法预测

        Args:
            scores: 历史成绩列表
            alpha: 平滑系数 (0-1)，越大越重视近期数据

        Returns:
            PredictionResult 预测结果
        """
        if len(scores) < 2:
            return PredictionResult(
                predicted_score=scores[0] if scores else 0,
                confidence_interval=(0, 100),
                trend='stable',
                trend_slope=0,
                r_squared=0,
                prediction_reliable=False
            )

        # 指数平滑
        smoothed = [scores[0]]
        for i in range(1, len(scores)):
            smoothed.append(alpha * scores[i] + (1 - alpha) * smoothed[-1])

        # 预测下次
        predicted_score = smoothed[-1]

        # 计算趋势（基于最后几个平滑值的斜率）
        if len(smoothed) >= 3:
            recent_slope = smoothed[-1] - smoothed[-3]
            if recent_slope > 2:
                trend = 'upward'
            elif recent_slope < -2:
                trend = 'downward'
            else:
                trend = 'stable'
        else:
            trend = 'stable'

        # 计算标准差作为置信区间
        std = np.std(scores)
        confidence_interval = (
            max(0, predicted_score - 1.96 * std),
            min(100, predicted_score + 1.96 * std)
        )

        return PredictionResult(
            predicted_score=round(predicted_score, 1),
            confidence_interval=(round(confidence_interval[0], 1), round(confidence_interval[1], 1)),
            trend=trend,
            trend_slope=0,
            r_squared=0,
            prediction_reliable=len(scores) >= 5
        )


class WarningSystem:
    """成绩预警系统"""

    # 预警阈值配置
    DECLINE_THRESHOLD = -5  # 连续下滑幅度
    LOW_SCORE_THRESHOLD = 60  # 低分阈值
    VOLATILITY_THRESHOLD = 15  # 波动阈值（标准差）
    AT_RISK_THRESHOLD = 50  # 危险阈值

    def __init__(self):
        """初始化预警系统"""
        pass

    def analyze_warnings(self, scores: List[float],
                         exam_dates: List[str] = None) -> List[WarningInfo]:
        """
        分析预警信息

        Args:
            scores: 历史成绩列表（按时间顺序）
            exam_dates: 考试日期列表

        Returns:
            预警信息列表
        """
        warnings = []

        if len(scores) < 2:
            return warnings

        # 1. 检查成绩下滑趋势
        decline_warning = self._check_declining(scores)
        if decline_warning:
            warnings.append(decline_warning)

        # 2. 检查低分
        low_score_warning = self._check_low_score(scores)
        if low_score_warning:
            warnings.append(low_score_warning)

        # 3. 检查成绩波动
        volatile_warning = self._check_volatile(scores)
        if volatile_warning:
            warnings.append(volatile_warning)

        # 4. 检查危险状态
        at_risk_warning = self._check_at_risk(scores)
        if at_risk_warning:
            warnings.append(at_risk_warning)

        # 按严重程度排序
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        warnings.sort(key=lambda w: severity_order.get(w.severity, 3))

        return warnings

    def _check_declining(self, scores: List[float]) -> Optional[WarningInfo]:
        """检查成绩是否连续下滑"""
        if len(scores) < 3:
            return None

        # 检查最近 3 次考试是否连续下滑
        recent = scores[-3:]
        if all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
            total_decline = recent[0] - recent[-1]
            if total_decline >= abs(self.DECLINE_THRESHOLD):
                return WarningInfo(
                    warning_type='declining',
                    warning_name='成绩下滑',
                    severity='high' if total_decline >= 15 else 'medium',
                    message=f'最近 3 次考试连续下滑，累计下降 {total_decline:.1f} 分',
                    details={
                        'recent_scores': recent,
                        'total_decline': total_decline
                    }
                )

        # 检查斜率
        if len(scores) >= 5:
            slope, _, r_value, _, _ = stats.linregress(range(len(scores)), scores)
            if slope < self.DECLINE_THRESHOLD and r_value < -0.5:
                return WarningInfo(
                    warning_type='declining',
                    warning_name='成绩下滑趋势',
                    severity='medium',
                    message=f'整体呈下滑趋势，平均每次考试下降 {abs(slope):.1f} 分',
                    details={'slope': slope}
                )

        return None

    def _check_low_score(self, scores: List[float]) -> Optional[WarningInfo]:
        """检查是否有低分"""
        recent = scores[-3:] if len(scores) >= 3 else scores
        avg_recent = sum(recent) / len(recent)

        if avg_recent < self.LOW_SCORE_THRESHOLD:
            return WarningInfo(
                warning_type='low_score',
                warning_name='低分预警',
                severity='high' if avg_recent < 50 else 'medium',
                message=f'最近平均分仅 {avg_recent:.1f} 分，低于及格线',
                details={'recent_avg': avg_recent}
            )

        # 检查最低分
        min_score = min(scores[-5:]) if len(scores) >= 5 else min(scores)
        if min_score < self.AT_RISK_THRESHOLD:
            return WarningInfo(
                warning_type='low_score',
                warning_name='出现危险分数',
                severity='high',
                message=f'最近出现 {min_score:.1f} 分的危险分数',
                details={'min_score': min_score}
            )

        return None

    def _check_volatile(self, scores: List[float]) -> Optional[WarningInfo]:
        """检查成绩波动是否过大"""
        if len(scores) < 4:
            return None

        recent = scores[-5:] if len(scores) >= 5 else scores
        std = np.std(recent)

        if std > self.VOLATILITY_THRESHOLD:
            return WarningInfo(
                warning_type='volatile',
                warning_name='成绩波动大',
                severity='medium' if std < 20 else 'high',
                message=f'最近成绩波动较大，标准差为 {std:.1f} 分',
                details={
                    'std': std,
                    'max': max(recent),
                    'min': min(recent),
                    'range': max(recent) - min(recent)
                }
            )

        return None

    def _check_at_risk(self, scores: List[float]) -> Optional[WarningInfo]:
        """检查是否处于危险状态"""
        if not scores:
            return None

        latest = scores[-1]
        if latest < self.AT_RISK_THRESHOLD:
            return WarningInfo(
                warning_type='at_risk',
                warning_name='危险状态',
                severity='high',
                message=f'最新考试仅 {latest:.1f} 分，处于危险水平',
                details={'latest_score': latest}
            )

        return None


class GoalTracker:
    """目标追踪器"""

    def __init__(self):
        """初始化目标追踪器"""
        pass

    def analyze_goal_progress(self, scores: List[float],
                               goal_score: float,
                               predictor: ScorePredictor = None) -> GoalProgress:
        """
        分析目标达成进度

        Args:
            scores: 历史成绩列表
            goal_score: 目标分数
            predictor: 成绩预测器

        Returns:
            GoalProgress 目标进度信息
        """
        if not scores:
            return GoalProgress(
                goal_score=goal_score,
                current_avg=0,
                best_score=0,
                progress_rate=0,
                remaining_gap=goal_score,
                projected_reach=False,
                exams_needed=0
            )

        current_avg = sum(scores) / len(scores)
        best_score = max(scores)
        remaining_gap = goal_score - current_avg

        # 计算进度率（当前平均距离目标的比例）
        if goal_score > 0:
            progress_rate = min(100, (current_avg / goal_score) * 100)
        else:
            progress_rate = 0

        # 预测能否达成
        projected_reach = current_avg >= goal_score
        exams_needed = 0

        if predictor and current_avg < goal_score:
            # 使用预测器判断趋势
            prediction = predictor.linear_regression_predict(scores)
            if prediction.trend == 'upward' and prediction.trend_slope > 0:
                # 按当前趋势，计算还需要几次考试
                exams_needed = max(1, int((goal_score - current_avg) / prediction.trend_slope))
                projected_reach = prediction.predicted_score >= goal_score * 0.9

        return GoalProgress(
            goal_score=goal_score,
            current_avg=round(current_avg, 1),
            best_score=round(best_score, 1),
            progress_rate=round(progress_rate, 1),
            remaining_gap=round(remaining_gap, 1),
            projected_reach=projected_reach,
            exams_needed=exams_needed
        )


class ScorePredictionVisualizer:
    """成绩预测可视化"""

    def __init__(self):
        """初始化可视化器"""
        self.predictor = ScorePredictor()

    def create_prediction_chart(self, scores: List[float],
                                 exam_names: List[str] = None,
                                 use_exponential: bool = False) -> go.Figure:
        """
        创建成绩预测图表

        Args:
            scores: 历史成绩列表
            exam_names: 考试名称列表
            use_exponential: 是否使用指数平滑预测

        Returns:
            Plotly 图表
        """
        if not scores:
            fig = go.Figure()
            fig.add_annotation(text="暂无成绩数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="成绩趋势预测")
            return fig

        n = len(scores)
        x_labels = exam_names if exam_names else [f"考试{i+1}" for i in range(n)]
        x_numeric = list(range(n))

        # 获取预测结果
        if use_exponential:
            prediction = self.predictor.exponential_smoothing_predict(scores)
        else:
            prediction = self.predictor.linear_regression_predict(scores)

        # 创建图表
        fig = go.Figure()

        # 历史成绩线
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=scores,
            mode='lines+markers',
            name='历史成绩',
            line=dict(color='#3498db', width=2),
            marker=dict(size=8)
        ))

        # 趋势线
        if not use_exponential and n >= 2:
            slope, intercept, _, _, _ = stats.linregress(x_numeric, scores)
            trend_y = [slope * x + intercept for x in x_numeric]
            fig.add_trace(go.Scatter(
                x=x_labels,
                y=trend_y,
                mode='lines',
                name='趋势线',
                line=dict(color='#e74c3c', width=2, dash='dash')
            ))

        # 预测点
        next_x = f"下次\n预测"
        pred_y = prediction.predicted_score

        fig.add_trace(go.Scatter(
            x=[next_x],
            y=[pred_y],
            mode='markers+text',
            name='预测成绩',
            marker=dict(color='#27ae60', size=12, symbol='star'),
            text=[f"{pred_y:.1f}"],
            textposition="top center"
        ))

        # 置信区间
        ci_low, ci_high = prediction.confidence_interval
        fig.add_trace(go.Scatter(
            x=[next_x, next_x],
            y=[ci_low, ci_high],
            mode='lines',
            name='置信区间',
            line=dict(color='#27ae60', width=2, dash='dot'),
            showlegend=True
        ))

        # 添加目标线（可选）
        fig.add_hline(
            y=60,
            line_dash="dash",
            line_color="gray",
            annotation_text="及格线",
            annotation_position="right",
            opacity=0.5
        )

        fig.add_hline(
            y=85,
            line_dash="dash",
            line_color="orange",
            annotation_text="优秀线",
            annotation_position="right",
            opacity=0.5
        )

        # 更新布局
        fig.update_layout(
            title="成绩趋势预测",
            xaxis_title="考试",
            yaxis_title="分数",
            yaxis_range=[max(0, min(scores) - 10), min(100, max(scores) + 15)],
            height=450,
            showlegend=True,
            hovermode='x unified'
        )

        # 添加预测信息文本框
        info_text = (
            f"<b>预测结果</b><br>"
            f"预测分数：{prediction.predicted_score:.1f}<br>"
            f"置信区间：[{prediction.confidence_interval[0]:.1f}, {prediction.confidence_interval[1]:.1f}]<br>"
            f"趋势：{self._get_trend_name(prediction.trend)}<br>"
            f"拟合度：{prediction.r_squared:.3f}<br>"
            f"可靠性：{'✓' if prediction.prediction_reliable else '✗'}"
        )

        fig.add_annotation(
            text=info_text,
            align="left",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=1.02,
            y=1,
            bordercolor="#ccc",
            borderwidth=1,
            borderpad=4,
            bgcolor="rgba(255,255,255,0.9)"
        )

        return fig

    def _get_trend_name(self, trend: str) -> str:
        """获取趋势名称"""
        trend_names = {
            'upward': '上升 ↑',
            'stable': '平稳 →',
            'downward': '下降 ↓'
        }
        return trend_names.get(trend, trend)

    def create_warning_chart(self, warnings: List[WarningInfo]) -> go.Figure:
        """
        创建预警信息图表

        Args:
            warnings: 预警信息列表

        Returns:
            Plotly 图表
        """
        if not warnings:
            fig = go.Figure()
            fig.add_annotation(
                text="✓ 暂无预警",
                showarrow=False,
                font_size=24,
                font_color="#27ae60"
            )
            fig.update_layout(
                height=200,
                title="成绩预警"
            )
            return fig

        # 创建预警列表
        severity_colors = {
            'high': '#e74c3c',
            'medium': '#f39c12',
            'low': '#3498db'
        }

        fig = go.Figure()

        for i, warning in enumerate(warnings):
            color = severity_colors.get(warning.severity, '#95a5a6')
            fig.add_trace(go.Bar(
                name=f"{warning.warning_name}",
                x=[warning.warning_name],
                y=[1],
                marker_color=color,
                hovertemplate=f"<b>{warning.warning_name}</b><br>{warning.message}<extra></extra>",
                legendgroup=warning.severity
            ))

        fig.update_layout(
            title="成绩预警",
            yaxis=dict(showticklabels=False, title="预警级别"),
            height=300,
            showlegend=True,
            barmode='group'
        )

        # 添加预警级别图例
        for severity, color in severity_colors.items():
            fig.add_trace(go.Bar(
                x=[None], y=[None],
                name=f"{severity}级预警",
                marker_color=color,
                showlegend=True
            ))

        return fig

    def create_goal_progress_chart(self, progress: GoalProgress) -> go.Figure:
        """
        创建目标进度图表

        Args:
            progress: 目标进度信息

        Returns:
            Plotly 仪表图
        """
        # 创建仪表图
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=progress.progress_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "目标达成进度", 'font': {'size': 24}},
            delta={'reference': 100, 'increasing': {'color': "#27ae60"}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#333"},
                'bar': {'color': "#3498db" if progress.progress_rate < 100 else "#27ae60"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#333",
                'steps': [
                    {'range': [0, 60], 'color': "#ffebee"},
                    {'range': [60, 85], 'color': "#fff3e0"},
                    {'range': [85, 100], 'color': "#e8f5e9"}
                ],
            }
        ))

        # 添加详细信息
        fig.add_annotation(
            text=(
                f"<b>当前平均</b>: {progress.current_avg}<br>"
                f"<b>目标分数</b>: {progress.goal_score}<br>"
                f"<b>剩余差距</b>: {progress.remaining_gap}<br>"
                f"<b>预计达成</b>: {'✓ 是' if progress.projected_reach else '✗ 否'}"
            ),
            align="left",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0,
            y=-0.3,
            bordercolor="#ccc",
            borderwidth=1,
            borderpad=4,
            bgcolor="rgba(255,255,255,0.9)"
        )

        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=50, b=100)
        )

        return fig
