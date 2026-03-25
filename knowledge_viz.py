"""
知识点掌握度可视化模块
- 知识图谱追踪：展示知识点前后置依赖关系，标识薄弱环节
- 能力雷达图：按数与代数、图形与几何、统计与概率等维度评估
- 错题归因分析：自动分类错误类型（概念不清/计算错误/审题问题）
"""
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class ErrorCause:
    """错题归因"""
    cause_type: str  # concept/calculation/reading/careless
    cause_name: str  # 概念不清/计算错误/审题问题/粗心大意
    count: int
    percentage: float
    knowledge_codes: List[str]


class KnowledgeVisualizer:
    """知识点可视化分析器"""

    # 错误类型归因映射（基于错题描述关键词）
    ERROR_CAUSE_KEYWORDS = {
        'concept': ['概念', '理解', '定义', '性质', '定理', '公式', '原理', '意义'],
        'calculation': ['计算', '算错', '运算', '口算', '笔算'],
        'reading': ['审题', '题意', '理解题意', '看错', '漏看', '条件'],
        'careless': ['粗心', '马虎', '漏写', '抄错', '符号', '单位']
    }

    ERROR_CAUSE_NAMES = {
        'concept': '概念不清',
        'calculation': '计算错误',
        'reading': '审题问题',
        'careless': '粗心大意'
    }

    # 知识领域分类
    KNOWLEDGE_CATEGORIES = {
        '数与代数': ['数', '代数', '计算', '方程', '函数', '式', '运算', '因数', '倍数', '分数', '小数', '百分数'],
        '图形与几何': ['图形', '几何', '角', '三角形', '四边形', '圆', '面积', '体积', '周长', '对称', '平移', '旋转'],
        '统计与概率': ['统计', '概率', '图表', '数据', '平均数', '条形', '折线', '扇形', '可能性'],
        '综合与实践': ['综合', '实践', '应用', '解决问题', '探索']
    }

    def __init__(self, knowledge_points: Dict):
        """
        初始化可视化分析器

        Args:
            knowledge_points: 知识点字典 {code: KnowledgeNode}
        """
        self.knowledge_points = knowledge_points

    def analyze_error_causes(self, error_records: List[Dict]) -> List[ErrorCause]:
        """
        分析错题归因

        Args:
            error_records: 错题记录列表

        Returns:
            错题归因分析结果
        """
        cause_counts = {'concept': 0, 'calculation': 0, 'reading': 0, 'careless': 0}
        cause_knowledge = {'concept': [], 'calculation': [], 'reading': [], 'careless': []}

        for record in error_records:
            # 获取错题描述
            description = (record.get('error_description') or '') + (record.get('error_type') or '')
            knowledge_code = record.get('knowledge_code', '')

            # 根据关键词匹配错误原因
            matched = False
            for cause_type, keywords in self.ERROR_CAUSE_KEYWORDS.items():
                if any(kw in description for kw in keywords):
                    cause_counts[cause_type] += 1
                    if knowledge_code and knowledge_code not in cause_knowledge[cause_type]:
                        cause_knowledge[cause_type].append(knowledge_code)
                    matched = True
                    break

            # 如果没有匹配到关键词，默认归类为概念不清
            if not matched:
                cause_counts['concept'] += 1
                if knowledge_code and knowledge_code not in cause_knowledge['concept']:
                    cause_knowledge['concept'].append(knowledge_code)

        total = sum(cause_counts.values())
        results = []

        for cause_type, count in cause_counts.items():
            if count > 0:
                results.append(ErrorCause(
                    cause_type=cause_type,
                    cause_name=self.ERROR_CAUSE_NAMES[cause_type],
                    count=count,
                    percentage=round(count / total * 100, 1) if total > 0 else 0,
                    knowledge_codes=cause_knowledge[cause_type]
                ))

        # 按数量降序排列
        results.sort(key=lambda x: x.count, reverse=True)
        return results

    def create_error_cause_chart(self, error_records: List[Dict]) -> go.Figure:
        """
        创建错题归因饼图

        Args:
            error_records: 错题记录列表

        Returns:
            Plotly 饼图
        """
        causes = self.analyze_error_causes(error_records)

        if not causes:
            # 返回空图表
            fig = go.Figure()
            fig.add_annotation(text="暂无错题数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="错题归因分析")
            return fig

        fig = go.Figure(data=[go.Pie(
            labels=[c.cause_name for c in causes],
            values=[c.count for c in causes],
            hole=0.4,
            marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'],
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>数量：%{value}<br>知识点：%{customdata}<extra></extra>',
            customdata=[', '.join(c.knowledge_codes[:3]) + ('...' if len(c.knowledge_codes) > 3 else '')
                       for c in causes]
        )])

        fig.update_layout(
            title="错题归因分析",
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )

        return fig

    def analyze_ability_radar(self, student_scores: List[Dict],
                               error_records: List[Dict] = None) -> Dict[str, float]:
        """
        分析学生能力雷达数据

        Args:
            student_scores: 学生成绩记录列表
            error_records: 错题记录列表（可选）

        Returns:
            各维度能力得分 {维度名：得分}
        """
        # 统计各知识领域的得分情况
        category_scores = {cat: [] for cat in self.KNOWLEDGE_CATEGORIES.keys()}

        # 分析错题分布
        error_by_category = {cat: 0 for cat in self.KNOWLEDGE_CATEGORIES.keys()}

        for record in error_records or []:
            kp_code = record.get('knowledge_code', '')
            kp = self.knowledge_points.get(kp_code)
            if kp:
                kp_name = kp.name if hasattr(kp, 'name') else str(kp)
                for category, keywords in self.KNOWLEDGE_CATEGORIES.items():
                    if any(kw in kp_name for kw in keywords):
                        error_by_category[category] += 1
                        break

        # 根据错题数量计算能力得分（错题越少，得分越高）
        total_errors = sum(error_by_category.values())
        ability_scores = {}

        for category, error_count in error_by_category.items():
            if total_errors == 0:
                ability_scores[category] = 100.0
            else:
                # 基础分 60，根据错误比例加分
                error_rate = error_count / total_errors
                ability_scores[category] = round(60 + (1 - error_rate) * 40, 1)

        return ability_scores

    def create_ability_radar_chart(self, student_scores: List[Dict],
                                    error_records: List[Dict] = None,
                                    student_name: str = "") -> go.Figure:
        """
        创建能力雷达图

        Args:
            student_scores: 学生成绩记录列表
            error_records: 错题记录列表
            student_name: 学生姓名

        Returns:
            Plotly 雷达图
        """
        ability_scores = self.analyze_ability_radar(student_scores, error_records)

        categories = list(ability_scores.keys())
        values = list(ability_scores.values())

        # 闭合雷达图
        values += values[:1]
        categories += categories[:1]

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=student_name or '学生',
            line_color='#3498db',
            fillcolor='rgba(52, 152, 219, 0.3)'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickformat='.0f'
                ),
                angularaxis=dict(
                    direction='clockwise',
                    rotation=90
                )
            ),
            showlegend=True,
            height=450,
            title=f"数学核心素养雷达图 - {student_name}" if student_name else "数学核心素养雷达图"
        )

        return fig

    def create_knowledge_mastery_graph(self, mastery_data: Dict[str, float],
                                        prerequisites: Dict[str, List[str]] = None,
                                        title: str = "知识图谱") -> go.Figure:
        """
        创建知识图谱可视化

        Args:
            mastery_data: 知识点掌握度数据 {知识点编码：掌握度 (0-100)}
            prerequisites: 前置知识点依赖关系 {知识点编码：[前置知识点列表]}
            title: 图表标题

        Returns:
            Plotly 散点图（模拟知识图谱）
        """
        # 为知识点分配位置（简单布局）
        positions = {}
        n = len(mastery_data)

        if n == 0:
            fig = go.Figure()
            fig.add_annotation(text="暂无知识图谱数据", showarrow=False, font_size=20)
            fig.update_layout(height=500, title=title)
            return fig

        # 简单网格布局
        cols = min(5, max(2, int(n ** 0.5)))
        rows = (n + cols - 1) // cols

        for i, kp_code in enumerate(mastery_data.keys()):
            row = i // cols
            col = i % cols
            positions[kp_code] = (col * 100 / cols + 50 / cols,
                                  row * 100 / rows + 50 / rows)

        # 获取知识点名称和掌握度
        node_names = []
        node_mastery = []
        node_x = []
        node_y = []
        node_colors = []

        for kp_code, mastery in mastery_data.items():
            kp = self.knowledge_points.get(kp_code)
            name = kp.name if hasattr(kp, 'name') else kp_code
            node_names.append(name)
            node_mastery.append(mastery)

            if kp_code in positions:
                node_x.append(positions[kp_code][0])
                node_y.append(positions[kp_code][1])

            # 根据掌握度设置颜色
            if mastery >= 90:
                node_colors.append('#27ae60')  # 绿色 - 已掌握
            elif mastery >= 70:
                node_colors.append('#f39c12')  # 黄色 - 基本掌握
            elif mastery >= 50:
                node_colors.append('#e67e22')  # 橙色 - 需要加强
            else:
                node_colors.append('#e74c3c')  # 红色 - 薄弱

        fig = go.Figure()

        # 绘制连线（前置知识关系）
        edge_x, edge_y = [], []
        if prerequisites:
            for kp_code, prereqs in prerequisites.items():
                if kp_code in positions and kp_code in mastery_data:
                    for prereq in prereqs:
                        if prereq in positions and prereq in mastery_data:
                            edge_x.extend([positions[prereq][0], positions[kp_code][0], None])
                            edge_y.extend([positions[prereq][1], positions[kp_code][1], None])

        if edge_x:
            fig.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=1, color='#bdc3c7'),
                hoverinfo='none',
                mode='lines',
                showlegend=False
            ))

        # 绘制节点
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=15,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            text=[f"{name[:8]}{'...' if len(name) > 8 else ''}" for name in node_names],
            textposition="bottom center",
            textfont_size=9,
            hovertemplate='<b>%{text}</b><br>掌握度：%{customdata:.1f}%<extra></extra>',
            customdata=node_mastery,
            name='知识点'
        ))

        fig.update_layout(
            title=title,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       range=[0, 100]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       range=[0, 100], scaleanchor="x", scaleratio=1),
            height=500,
            showlegend=False,
            plot_bgcolor='white'
        )

        # 添加图例
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(size=10, color='#27ae60'),
            name='已掌握 (≥90)',
            hoverinfo='none'
        ))
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(size=10, color='#f39c12'),
            name='基本掌握 (70-89)',
            hoverinfo='none'
        ))
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(size=10, color='#e74c3c'),
            name='薄弱 (<50)',
            hoverinfo='none'
        ))

        return fig

    def create_knowledge_bar_chart(self, mastery_data: Dict[str, float],
                                    student_name: str = "",
                                    threshold: float = 70) -> go.Figure:
        """
        创建知识点掌握度柱状图

        Args:
            mastery_data: 知识点掌握度数据 {知识点编码：掌握度}
            student_name: 学生姓名
            threshold: 掌握阈值

        Returns:
            Plotly 柱状图
        """
        if not mastery_data:
            fig = go.Figure()
            fig.add_annotation(text="暂无知识点数据", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="知识点掌握度")
            return fig

        # 准备数据
        categories = []
        mastery_values = []
        colors = []

        for kp_code, mastery in mastery_data.items():
            kp = self.knowledge_points.get(kp_code)
            name = kp.name if hasattr(kp, 'name') else kp_code
            categories.append(name)
            mastery_values.append(mastery)

            if mastery >= threshold:
                colors.append('#27ae60')
            elif mastery >= threshold * 0.7:
                colors.append('#f39c12')
            else:
                colors.append('#e74c3c')

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=categories,
            y=mastery_values,
            marker_color=colors,
            hovertemplate='<b>%{x}</b><br>掌握度：%{y:.1f}%<extra></extra>'
        ))

        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"掌握线 ({threshold}%)",
            annotation_position="right"
        )

        fig.update_layout(
            title=f"知识点掌握度分析 - {student_name}" if student_name else "知识点掌握度分析",
            xaxis_title="知识点",
            yaxis_title="掌握度 (%)",
            yaxis_range=[0, 100],
            height=400,
            showlegend=False,
            xaxis_tickangle=-45
        )

        return fig
