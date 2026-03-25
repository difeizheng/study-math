"""
教育测量学指标模块
- IRT 项目反应理论：题目难度、区分度、猜测参数估计
- 增值评价：学生进步幅度标准化评估
- 多维度能力模型：五维能力评估体系
"""
import numpy as np
from scipy import stats, optimize
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class IRTParameters:
    """IRT 参数"""
    item_id: str
    difficulty: float  # 难度参数 b (-3 to 3)
    discrimination: float  # 区分度参数 a (0 to 2)
    guessing: float  # 猜测参数 c (0 to 0.25)
    fit: float  # 拟合度


@dataclass
class AbilityEstimate:
    """能力估计"""
    person_id: int
    ability_theta: float  # 能力值 (-3 to 3)
    standard_error: float  # 标准误
    reliability: float  # 信度
    percentile: float  # 百分位


@dataclass
class ValueAddedResult:
    """增值评价结果"""
    student_id: int
    expected_growth: float  # 预期增长
    actual_growth: float  # 实际增长
    value_added: float  # 增值
    effectiveness: str  # 效能等级


class IRTAnalyzer:
    """IRT 项目反应理论分析器"""

    def __init__(self):
        """初始化 IRT 分析器"""
        # 常用 IRT 模型
        self.models = ['1PL', '2PL', '3PL']

    def estimate_parameters_3pl(self, responses: List[int],
                                 thetas: List[float] = None) -> IRTParameters:
        """
        估计 3PL 模型参数

        Args:
            responses: 作答反应 (0/1 向量)
            thetas: 考生能力估计（可选）

        Returns:
            IRTParameters IRT 参数
        """
        if not responses or len(responses) < 10:
            return IRTParameters(
                item_id='unknown',
                difficulty=0,
                discrimination=1,
                guessing=0.2,
                fit=0
            )

        n = len(responses)
        p_correct = sum(responses) / n  # 正确率

        # 简化参数估计（实际应用中需要使用 MLE 或 Bayesian 方法）
        # 难度参数：与正确率负相关
        difficulty = -stats.norm.ppf(p_correct) if 0 < p_correct < 1 else 0
        difficulty = max(-3, min(3, difficulty))

        # 区分度参数：使用点二列相关
        scores = list(range(n))
        if np.std(responses) > 0 and np.std(scores) > 0:
            discrimination = np.corrcoef(scores, responses)[0, 1]
            discrimination = max(0, min(2, abs(discrimination) * 2))
        else:
            discrimination = 1.0

        # 猜测参数：低分段正确率
        guessing = min(0.25, p_correct * 0.5)

        # 计算拟合度（简化）
        fit = 1 - abs(p_correct - 0.5)

        return IRTParameters(
            item_id='item_001',
            difficulty=round(difficulty, 3),
            discrimination=round(discrimination, 3),
            guessing=round(guessing, 3),
            fit=round(fit, 3)
        )

    def estimate_ability(self, responses: List[int],
                         item_params: List[IRTParameters] = None) -> AbilityEstimate:
        """
        估计考生能力

        Args:
            responses: 作答反应 (0/1 向量)
            item_params: 题目参数列表

        Returns:
            AbilityEstimate 能力估计
        """
        if not responses:
            return AbilityEstimate(
                person_id=0,
                ability_theta=0,
                standard_error=1,
                reliability=0,
                percentile=50
            )

        # 简单能力估计：使用正确率转换
        n = len(responses)
        p_correct = sum(responses) / n

        # 能力值转换
        if p_correct == 0:
            theta = -3
        elif p_correct == 1:
            theta = 3
        else:
            theta = stats.norm.ppf(p_correct)
            theta = max(-3, min(3, theta))

        # 标准误（简化估计）
        se = 1 / np.sqrt(n) if n > 0 else 1

        # 信度
        reliability = 1 - se ** 2
        reliability = max(0, min(1, reliability))

        # 百分位
        percentile = stats.norm.cdf(theta) * 100

        return AbilityEstimate(
            person_id=0,
            ability_theta=round(theta, 3),
            standard_error=round(se, 3),
            reliability=round(reliability, 3),
            percentile=round(percentile, 1)
        )

    def create_item_characteristic_curve(self, params: IRTParameters,
                                         theta_range: Tuple = (-3, 3)) -> Dict:
        """
        创建项目特征曲线数据

        Args:
            params: IRT 参数
            theta_range: 能力范围

        Returns:
            曲线数据 {theta: [...], p: [...]}
        """
        a, b, c = params.discrimination, params.difficulty, params.guessing

        theta_vals = np.linspace(theta_range[0], theta_range[1], 100)

        # 3PL 模型概率函数
        def p_theta(theta):
            exp_val = np.exp(1.7 * a * (theta - b))
            return c + (1 - c) * exp_val / (1 + exp_val)

        p_vals = [p_theta(t) for t in theta_vals]

        return {
            'theta': theta_vals.tolist(),
            'p': p_vals,
            'params': {
                'difficulty': params.difficulty,
                'discrimination': params.discrimination,
                'guessing': params.guessing
            }
        }


class ValueAddedAnalyzer:
    """增值评价分析器"""

    def __init__(self):
        """初始化增值评价分析器"""
        # 效能等级
        self.effectiveness_levels = [
            (0.8, '高效'),
            (0.3, '有效'),
            (-0.3, '一般'),
            (-0.8, '待改进'),
            (float('-inf'), '低效')
        ]

    def calculate_value_added(self, student_scores: List[float],
                              baseline_scores: List[float] = None) -> ValueAddedResult:
        """
        计算增值

        Args:
            student_scores: 学生成绩序列
            baseline_scores: 基线成绩（用于对比）

        Returns:
            ValueAddedResult 增值结果
        """
        if len(student_scores) < 2:
            return ValueAddedResult(
                student_id=0,
                expected_growth=0,
                actual_growth=0,
                value_added=0,
                effectiveness='数据不足'
            )

        # 计算实际增长
        n = len(student_scores)
        first_half_avg = sum(student_scores[:n//2]) / (n//2)
        second_half_avg = sum(student_scores[n//2:]) / (n - n//2)
        actual_growth = second_half_avg - first_half_avg

        # 预期增长（基于初始水平）
        # 假设：初始水平越低，增长潜力越大
        initial_level = student_scores[0]
        expected_growth = (100 - initial_level) * 0.3  # 30% 增长潜力

        # 增值 = 实际增长 - 预期增长
        value_added = actual_growth - expected_growth

        # 确定效能等级
        effectiveness = self._get_effectiveness_level(value_added)

        return ValueAddedResult(
            student_id=0,
            expected_growth=round(expected_growth, 2),
            actual_growth=round(actual_growth, 2),
            value_added=round(value_added, 2),
            effectiveness=effectiveness
        )

    def _get_effectiveness_level(self, value_added: float) -> str:
        """获取效能等级"""
        for threshold, level in self.effectiveness_levels:
            if value_added >= threshold:
                return level
        return '低效'

    def batch_analyze(self, student_data: Dict[int, List[float]]) -> List[ValueAddedResult]:
        """
        批量分析增值

        Args:
            student_data: {学生 ID: 成绩序列}

        Returns:
            增值结果列表
        """
        results = []
        for student_id, scores in student_data.items():
            result = self.calculate_value_added(scores)
            result.student_id = student_id
            results.append(result)
        return results

    def create_value_added_distribution(self, results: List[ValueAddedResult]) -> Dict:
        """
        创建增值分布数据

        Args:
            results: 增值结果列表

        Returns:
            分布数据
        """
        if not results:
            return {'categories': [], 'values': [], 'effectiveness': []}

        # 按效能等级分组
        effectiveness_counts = {}
        for r in results:
            effectiveness_counts[r.effectiveness] = effectiveness_counts.get(r.effectiveness, 0) + 1

        return {
            'categories': list(effectiveness_counts.keys()),
            'values': list(effectiveness_counts.values()),
            'mean_value_added': np.mean([r.value_added for r in results]),
            'std_value_added': np.std([r.value_added for r in results])
        }


class MultiDimensionalAbilityModel:
    """多维度能力模型"""

    # 五维能力定义
    DIMENSIONS = {
        'knowledge': {
            'name': '知识掌握',
            'description': '基础知识和概念的理解与记忆',
            'indicators': ['概念理解', '公式记忆', '定理应用']
        },
        'skill': {
            'name': '技能运用',
            'description': '解题技能和运算能力',
            'indicators': ['计算准确', '步骤规范', '方法灵活']
        },
        'reasoning': {
            'name': '推理能力',
            'description': '逻辑推理和问题分析',
            'indicators': ['分析能力', '推理严谨', '思路清晰']
        },
        'application': {
            'name': '应用意识',
            'description': '数学建模和实际应用',
            'indicators': ['建模能力', '实际应用', '创新思维']
        },
        'reflection': {
            'name': '反思能力',
            'description': '错题分析和自我改进',
            'indicators': ['错因分析', '总结归纳', '迁移能力']
        }
    }

    def __init__(self):
        """初始化多维度能力模型"""
        pass

    def assess_dimensions(self, scores: List[float],
                         error_records: List = None,
                         knowledge_mastery: Dict = None) -> Dict[str, float]:
        """
        评估多维度能力

        Args:
            scores: 成绩列表
            error_records: 错题记录
            knowledge_mastery: 知识点掌握度

        Returns:
            {维度编码：能力值}
        """
        dimensions = {}

        # 1. 知识掌握维度 - 基于平均分和知识点掌握度
        avg_score = sum(scores) / len(scores) if scores else 0
        kp_factor = 1.0
        if knowledge_mastery:
            kp_factor = sum(knowledge_mastery.values()) / len(knowledge_mastery) / 100
        dimensions['knowledge'] = min(100, avg_score * 0.7 + kp_factor * 100 * 0.3)

        # 2. 技能运用维度 - 基于成绩稳定性
        if len(scores) >= 3:
            std_dev = np.std(scores)
            skill_score = max(0, 100 - std_dev * 2)
        else:
            skill_score = avg_score
        dimensions['skill'] = skill_score

        # 3. 推理能力维度 - 基于高分表现
        if scores:
            max_score = max(scores)
            reasoning_score = max_score * 0.8 + avg_score * 0.2
        else:
            reasoning_score = 50
        dimensions['reasoning'] = reasoning_score

        # 4. 应用意识维度 - 假设与知识掌握相关
        if knowledge_mastery:
            application_score = sum(knowledge_mastery.values()) / len(knowledge_mastery)
        else:
            application_score = avg_score
        dimensions['application'] = application_score

        # 5. 反思能力维度 - 基于错题分析
        if error_records and len(error_records) > 0:
            # 错题越少，反思能力越强
            error_factor = max(0, 100 - len(error_records) * 5)
            dimensions['reflection'] = error_factor
        else:
            dimensions['reflection'] = 70 if scores else 50

        return dimensions

    def create_radar_data(self, dimensions: Dict[str, float]) -> Dict:
        """
        创建雷达图数据

        Args:
            dimensions: 维度能力值

        Returns:
            雷达图数据
        """
        labels = [self.DIMENSIONS[k]['name'] for k in self.DIMENSIONS.keys()]
        values = [dimensions.get(k, 50) for k in self.DIMENSIONS.keys()]

        # 闭合雷达图
        labels_closed = labels + [labels[0]]
        values_closed = values + [values[0]]

        return {
            'labels': labels_closed,
            'values': values_closed,
            'categories': list(self.DIMENSIONS.keys())
        }

    def get_dimension_description(self, dimension: str) -> str:
        """获取维度描述"""
        dim = self.DIMENSIONS.get(dimension, {})
        return dim.get('description', '未知维度')

    def get_suggestions(self, dimensions: Dict[str, float]) -> List[str]:
        """
        生成改进建议

        Args:
            dimensions: 维度能力值

        Returns:
            建议列表
        """
        suggestions = []

        for dim_code, score in dimensions.items():
            dim_name = self.DIMENSIONS.get(dim_code, {}).get('name', dim_code)

            if score < 60:
                suggestions.append(f"{dim_name}需要加强，建议针对性练习")
            elif score < 80:
                suggestions.append(f"{dim_name}良好，可以继续提升")
            else:
                suggestions.append(f"{dim_name}优秀，保持当前状态")

        return suggestions
