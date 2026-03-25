"""
个性化推荐模块
- 针对性练习推荐：根据薄弱知识点推荐练习题
- 学习路径规划：基于知识依赖关系生成学习顺序建议
- 相似题型推荐：针对错题推荐同类型题目巩固
"""
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class PracticeRecommendation:
    """练习题推荐"""
    knowledge_code: str
    knowledge_name: str
    mastery_level: float  # 当前掌握度
    priority: int  # 优先级 (1-5, 1 最高)
    recommendation_reason: str  # 推荐原因
    suggested_exercises: List[str]  # 推荐练习题
    difficulty: str  # 难度等级


@dataclass
class LearningPath:
    """学习路径"""
    start_knowledge: str
    target_knowledge: str
    path: List[Dict]  # 路径上的知识点
    estimated_time: int  # 预计学习时间（分钟）
    difficulty_progression: List[str]  # 难度递进


@dataclass
class SimilarQuestion:
    """相似题目"""
    question_id: str
    question_text: str
    knowledge_code: str
    difficulty: float
    similarity_score: float  # 相似度
    source: str  # 来源


class PracticeRecommender:
    """练习题推荐器"""

    # 练习题题库（示例数据）
    EXERCISE_DATABASE = {
        'G1U03': [  # 1-5 的认识和加减法
            {'id': 'G1U03-001', 'text': '小明有 3 个苹果，妈妈又给了他 2 个，现在有几个？', 'difficulty': 1, 'type': 'application'},
            {'id': 'G1U03-002', 'text': '计算：2 + 3 = ?', 'difficulty': 1, 'type': 'calculation'},
            {'id': 'G1U03-003', 'text': '计算：5 - 2 = ?', 'difficulty': 1, 'type': 'calculation'},
            {'id': 'G1U03-004', 'text': '小红有 4 支铅笔，用了 1 支，还剩几支？', 'difficulty': 2, 'type': 'application'},
        ],
        'G1U05': [  # 6-10 的认识和加减法
            {'id': 'G1U05-001', 'text': '计算：7 + 3 = ?', 'difficulty': 1, 'type': 'calculation'},
            {'id': 'G1U05-002', 'text': '计算：10 - 4 = ?', 'difficulty': 1, 'type': 'calculation'},
            {'id': 'G1U05-003', 'text': '填空：6 + __ = 9', 'difficulty': 2, 'type': 'fill_blank'},
            {'id': 'G1U05-004', 'text': '树上有 8 只鸟，飞走了 3 只，又飞来了 2 只，现在有几只？', 'difficulty': 3, 'type': 'application'},
        ],
        'G2U04': [  # 表内乘法（一）
            {'id': 'G2U04-001', 'text': '计算：3 × 4 = ?', 'difficulty': 1, 'type': 'calculation'},
            {'id': 'G2U04-002', 'text': '计算：5 × 6 = ?', 'difficulty': 1, 'type': 'calculation'},
            {'id': 'G2U04-003', 'text': '填空：__ × 7 = 42', 'difficulty': 2, 'type': 'fill_blank'},
            {'id': 'G2U04-004', 'text': '一个盒子装 6 个鸡蛋，5 个盒子装多少个鸡蛋？', 'difficulty': 2, 'type': 'application'},
        ],
    }

    # 默认练习题（用于没有专门题库的知识点）
    DEFAULT_EXERCISES = [
        {'id': 'DEFAULT-001', 'text': '基础练习题 1', 'difficulty': 1, 'type': 'calculation'},
        {'id': 'DEFAULT-002', 'text': '基础练习题 2', 'difficulty': 1, 'type': 'calculation'},
        {'id': 'DEFAULT-003', 'text': '提升练习题 1', 'difficulty': 2, 'type': 'application'},
        {'id': 'DEFAULT-004', 'text': '挑战练习题 1', 'difficulty': 3, 'type': 'challenge'},
    ]

    def __init__(self, knowledge_points: Dict):
        """
        初始化推荐器

        Args:
            knowledge_points: 知识点字典
        """
        self.knowledge_points = knowledge_points

    def get_weak_knowledge_points(self, mastery_data: Dict[str, float],
                                   threshold: float = 70) -> List[Tuple[str, float]]:
        """
        获取薄弱知识点

        Args:
            mastery_data: 知识点掌握度数据
            threshold: 掌握度阈值

        Returns:
            [(知识点编码，掌握度)] 列表，按掌握度升序
        """
        weak = [(code, score) for code, score in mastery_data.items() if score < threshold]
        weak.sort(key=lambda x: x[1])  # 按掌握度升序
        return weak

    def recommend_practices(self, mastery_data: Dict[str, float],
                            num_recommendations: int = 5) -> List[PracticeRecommendation]:
        """
        推荐练习题

        Args:
            mastery_data: 知识点掌握度数据
            num_recommendations: 推荐数量

        Returns:
            练习题推荐列表
        """
        weak_points = self.get_weak_knowledge_points(mastery_data)
        recommendations = []

        for code, score in weak_points[:num_recommendations]:
            kp = self.knowledge_points.get(code)
            kp_name = kp.name if hasattr(kp, 'name') else code

            # 获取练习题
            exercises = self.EXERCISE_DATABASE.get(code, self.DEFAULT_EXERCISES)

            # 根据掌握度确定推荐难度
            if score < 50:
                difficulty = '基础'
                priority = 1
                reason = '掌握度较低，需要从基础练习开始'
            elif score < 70:
                difficulty = '提升'
                priority = 2
                reason = '基本掌握，需要加强练习巩固'
            else:
                difficulty = '挑战'
                priority = 3
                reason = '掌握良好，可以尝试挑战题'

            # 选择适合的练习题（按难度筛选）
            if difficulty == '基础':
                suggested = [e for e in exercises if e['difficulty'] <= 2][:3]
            elif difficulty == '提升':
                suggested = [e for e in exercises if e['difficulty'] >= 2][:3]
            else:
                suggested = [e for e in exercises if e['difficulty'] >= 3][:3]

            if not suggested:
                suggested = exercises[:3]

            recommendations.append(PracticeRecommendation(
                knowledge_code=code,
                knowledge_name=kp_name,
                mastery_level=score,
                priority=priority,
                recommendation_reason=reason,
                suggested_exercises=[s['text'] for s in suggested],
                difficulty=difficulty
            ))

        return recommendations

    def create_recommendation_chart(self, recommendations: List[PracticeRecommendation]) -> go.Figure:
        """
        创建推荐优先级图表

        Args:
            recommendations: 推荐列表

        Returns:
            Plotly 柱状图
        """
        if not recommendations:
            fig = go.Figure()
            fig.add_annotation(text="暂无推荐", showarrow=False, font_size=20)
            fig.update_layout(height=400, title="练习题推荐优先级")
            return fig

        # 按优先级排序
        recs_sorted = sorted(recommendations, key=lambda r: r.priority)

        names = [f"{r.knowledge_name[:10]}..." if len(r.knowledge_name) > 10 else r.knowledge_name
                for r in recs_sorted]
        mastery = [r.mastery_level for r in recs_sorted]
        colors = ['#e74c3c' if m < 50 else '#f39c12' if m < 70 else '#27ae60' for m in mastery]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=names,
            y=mastery,
            marker_color=colors,
            text=[f"掌握度：{m:.1f}%" for m in mastery],
            textposition='auto',
            name='掌握度'
        ))

        fig.update_layout(
            title="练习题推荐优先级（按掌握度从低到高）",
            xaxis_title="知识点",
            yaxis_title="掌握度 (%)",
            yaxis_range=[0, 100],
            height=400,
            showlegend=False
        )

        # 添加阈值线
        fig.add_hline(y=70, line_dash="dash", line_color="gray",
                     annotation_text="掌握线", annotation_position="right")
        fig.add_hline(y=50, line_dash="dash", line_color="orange",
                     annotation_text="薄弱线", annotation_position="right")

        return fig


class LearningPathPlanner:
    """学习路径规划器"""

    # 知识依赖关系（简化版）
    DEPENDENCIES = {
        'G1U03': [],
        'G1U05': ['G1U03'],
        'G1U08': ['G1U05'],
        'G2U04': ['G1U05'],
        'G2U06': ['G2U04'],
        'G3U06': ['G2U04', 'G2U06'],
    }

    def __init__(self, knowledge_points: Dict):
        """
        初始化路径规划器

        Args:
            knowledge_points: 知识点字典
        """
        self.knowledge_points = knowledge_points

    def find_learning_path(self, start_code: str, target_code: str) -> Optional[LearningPath]:
        """
        查找学习路径

        Args:
            start_code: 起始知识点编码
            target_code: 目标知识点编码

        Returns:
            学习路径，如果无法找到返回 None
        """
        # BFS 查找路径
        if start_code == target_code:
            return LearningPath(
                start_knowledge=start_code,
                target_knowledge=target_code,
                path=[{'code': start_code, 'name': self._get_kp_name(start_code)}],
                estimated_time=30,
                difficulty_progression=['基础']
            )

        # 构建反向依赖图（从目标往前找）
        queue = [(target_code, [target_code])]
        visited = set()

        while queue:
            current, path = queue.pop(0)

            if current == start_code:
                # 找到路径
                path.reverse()
                kp_path = [{'code': code, 'name': self._get_kp_name(code)} for code in path]
                return LearningPath(
                    start_knowledge=start_code,
                    target_knowledge=target_code,
                    path=kp_path,
                    estimated_time=len(path) * 45,  # 每个知识点预计 45 分钟
                    difficulty_progression=self._estimate_difficulty(path)
                )

            if current in visited:
                continue
            visited.add(current)

            # 查找前置知识
            prereqs = self.DEPENDENCIES.get(current, [])
            for prereq in prereqs:
                queue.append((prereq, path + [prereq]))

        return None

    def recommend_learning_order(self, weak_points: List[Tuple[str, float]]) -> List[Dict]:
        """
        推荐学习顺序

        Args:
            weak_points: 薄弱知识点列表 [(code, mastery)]

        Returns:
            推荐学习顺序
        """
        if not weak_points:
            return []

        # 拓扑排序：先学前置知识
        result = []
        visited = set()

        def dfs(code: str):
            if code in visited:
                return
            visited.add(code)

            # 先学前置知识
            for prereq in self.DEPENDENCIES.get(code, []):
                if prereq in [wp[0] for wp in weak_points]:
                    dfs(prereq)

            kp = self.knowledge_points.get(code)
            result.append({
                'code': code,
                'name': self._get_kp_name(code),
                'category': kp.category if hasattr(kp, 'category') else '未知'
            })

        for code, _ in weak_points:
            dfs(code)

        return result

    def _get_kp_name(self, code: str) -> str:
        """获取知识点名称"""
        kp = self.knowledge_points.get(code)
        return kp.name if hasattr(kp, 'name') else code

    def _estimate_difficulty(self, path: List[str]) -> List[str]:
        """估计难度递进"""
        difficulties = []
        for i, code in enumerate(path):
            if i == 0:
                difficulties.append('基础')
            elif i < len(path) - 1:
                difficulties.append('提升')
            else:
                difficulties.append('挑战')
        return difficulties

    def create_path_visualization(self, path: LearningPath) -> go.Figure:
        """
        创建学习路径可视化

        Args:
            path: 学习路径

        Returns:
            Plotly 流程图
        """
        if not path or not path.path:
            fig = go.Figure()
            fig.add_annotation(text="暂无路径数据", showarrow=False, font_size=20)
            fig.update_layout(height=300, title="学习路径")
            return fig

        # 创建节点
        node_names = [p['name'][:15] + '...' if len(p['name']) > 15 else p['name']
                     for p in path.path]
        x_positions = list(range(len(node_names)))

        fig = go.Figure()

        # 绘制连线
        for i in range(len(path.path) - 1):
            fig.add_trace(go.Scatter(
                x=[i, i + 1],
                y=[0, 0],
                mode='lines',
                line=dict(color='#3498db', width=3),
                hoverinfo='none',
                showlegend=False
            ))

        # 绘制节点
        fig.add_trace(go.Scatter(
            x=x_positions,
            y=[0] * len(x_positions),
            mode='markers+text',
            marker=dict(size=50, color='#2ecc71', line=dict(width=3, color='white')),
            text=node_names,
            textposition='bottom center',
            textfont_size=10,
            hovertemplate='%{text}<extra></extra>',
            name='知识点'
        ))

        # 添加难度标签
        for i, diff in enumerate(path.difficulty_progression):
            fig.add_annotation(
                x=i, y=0.15,
                text=diff,
                showarrow=False,
                font_size=9,
                bgcolor='rgba(52, 152, 219, 0.8)'
            )

        fig.update_layout(
            title=f"学习路径：{path.path[0]['name']} → {path.path[-1]['name']}（预计 {path.estimated_time}分钟）",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       range=[-0.5, len(path.path) - 0.5]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       range=[-0.5, 0.5]),
            height=250,
            showlegend=False
        )

        return fig


class SimilarQuestionRecommender:
    """相似题目推荐器"""

    # 示例题库（实际应用中应该更大）
    QUESTION_BANK = [
        {'id': 'Q001', 'text': '计算：25 + 37 = ?', 'knowledge': 'G2U02', 'difficulty': 2, 'type': 'calculation'},
        {'id': 'Q002', 'text': '计算：84 - 56 = ?', 'knowledge': 'G2U02', 'difficulty': 2, 'type': 'calculation'},
        {'id': 'Q003', 'text': '小明有 45 元，买书花了 28 元，还剩多少元？', 'knowledge': 'G2U02', 'difficulty': 3, 'type': 'application'},
        {'id': 'Q004', 'text': '计算：6 × 7 = ?', 'knowledge': 'G2U04', 'difficulty': 1, 'type': 'calculation'},
        {'id': 'Q005', 'text': '计算：8 × 9 = ?', 'knowledge': 'G2U04', 'difficulty': 1, 'type': 'calculation'},
        {'id': 'Q006', 'text': '每盒装 8 个苹果，6 盒装多少个？', 'knowledge': 'G2U04', 'difficulty': 2, 'type': 'application'},
    ]

    def __init__(self):
        """初始化推荐器"""
        pass

    def find_similar_questions(self, error_question: str,
                                knowledge_code: str,
                                num_results: int = 3) -> List[SimilarQuestion]:
        """
        查找相似题目

        Args:
            error_question: 错题题目
            knowledge_code: 知识点编码
            num_results: 返回数量

        Returns:
            相似题目列表
        """
        # 过滤相同知识点的题目
        same_knowledge = [q for q in self.QUESTION_BANK if q['knowledge'] == knowledge_code]

        if not same_knowledge:
            # 返回默认推荐
            return self._get_default_recommendations(num_results)

        # 简单相似度计算（基于题目类型）
        error_type = self._estimate_question_type(error_question)

        scored = []
        for q in same_knowledge:
            score = 0.5  # 基础分（相同知识点）
            if q['type'] == error_type:
                score += 0.3  # 类型相同加分
            if abs(q['difficulty'] - self._estimate_difficulty(error_question)) <= 1:
                score += 0.2  # 难度相近加分

            scored.append((q, score))

        # 按相似度排序
        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for q, score in scored[:num_results]:
            results.append(SimilarQuestion(
                question_id=q['id'],
                question_text=q['text'],
                knowledge_code=q['knowledge'],
                difficulty=q['difficulty'],
                similarity_score=round(score * 100, 1),
                source='题库'
            ))

        return results

    def _estimate_question_type(self, question: str) -> str:
        """估计题目类型"""
        if '计算' in question or '=' in question:
            return 'calculation'
        elif '填空' in question or '__' in question:
            return 'fill_blank'
        elif any(kw in question for kw in ['多少', '几个', '多远', '多大']):
            return 'application'
        else:
            return 'unknown'

    def _estimate_difficulty(self, question: str) -> int:
        """估计题目难度"""
        # 简单启发式：题目越长可能越难
        if len(question) < 20:
            return 1
        elif len(question) < 50:
            return 2
        else:
            return 3

    def _get_default_recommendations(self, num: int) -> List[SimilarQuestion]:
        """获取默认推荐"""
        defaults = self.QUESTION_BANK[:num] if self.QUESTION_BANK else []
        return [SimilarQuestion(
            question_id=d['id'],
            question_text=d['text'],
            knowledge_code=d['knowledge'],
            difficulty=d['difficulty'],
            similarity_score=50.0,
            source='默认推荐'
        ) for d in defaults]
