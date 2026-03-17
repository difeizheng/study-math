"""
学习习惯分析模块
分析学生的答题习惯，识别粗心错误 vs 知识性错误
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class HabitAnalysis:
    """学习习惯分析结果"""
    student_id: int
    analysis_date: str
    # 错误类型分布
    error_distribution: Dict[str, int]
    # 习惯评分 (0-100)
    habit_scores: Dict[str, float]
    # 主要问题
    main_issues: List[str]
    # 改进建议
    suggestions: List[str]
    # 趋势分析
    trends: Dict[str, List[float]]


# 错误模式定义
ERROR_PATTERNS = {
    "计算粗心": {
        "keywords": ["计算错误", "进位错误", "退位错误", "口诀记错", "算错"],
        "description": "计算过程中出现的失误，通常是由于注意力不集中或熟练度不够"
    },
    "审题不清": {
        "keywords": ["看错题", "漏看条件", "理解错题意", "单位没注意", "问题看错"],
        "description": "没有准确理解题目要求或遗漏关键信息"
    },
    "抄写错误": {
        "keywords": ["抄错数", "写错符号", "答案抄错", "誊写错误"],
        "description": "在誊写过程中出现的错误"
    },
    "步骤缺失": {
        "keywords": ["步骤不全", "跳步", "漏写单位", "格式错误", "没写答"],
        "description": "解题过程不完整，缺少必要步骤"
    },
    "时间管理": {
        "keywords": ["时间不够", "没做完", "匆忙作答", "后面没做"],
        "description": "考试时间分配不合理导致的问题"
    },
    "概念混淆": {
        "keywords": ["概念不清", "公式记错", "方法用错", "知识混淆"],
        "description": "对知识点理解不透彻或概念混淆"
    }
}

# 习惯评分维度
HABIT_DIMENSIONS = {
    "仔细读题": {
        "description": "做题前仔细阅读题目的习惯",
        "weight": 0.2,
        "related_errors": ["审题不清"]
    },
    "规范书写": {
        "description": "书写工整、格式规范的习惯",
        "weight": 0.15,
        "related_errors": ["抄写错误", "步骤缺失"]
    },
    "认真计算": {
        "description": "计算时专注、细致的习惯",
        "weight": 0.2,
        "related_errors": ["计算粗心"]
    },
    "检查习惯": {
        "description": "完成后检查的习惯",
        "weight": 0.2,
        "related_errors": ["计算粗心", "抄写错误", "步骤缺失"]
    },
    "时间管理": {
        "description": "合理分配答题时间的能力",
        "weight": 0.15,
        "related_errors": ["时间管理"]
    },
    "知识扎实": {
        "description": "基础知识掌握程度",
        "weight": 0.1,
        "related_errors": ["概念混淆"]
    }
}


class StudyHabitAnalyzer:
    """学习习惯分析器"""

    def __init__(self):
        self.error_patterns = ERROR_PATTERNS
        self.habit_dimensions = HABIT_DIMENSIONS
        self.error_records: List[Dict] = []

    def add_error_record(self, student_id: int, exam_name: str, exam_date: str,
                         error_type: str, score: float, description: str = "",
                         detailed_analysis: Optional[Dict] = None):
        """
        添加错题记录（含错误分析）

        detailed_analysis: {
            "question_text": "...",
            "student_answer": "...",
            "correct_answer": "...",
            "error_analysis": "..."
        }
        """
        record = {
            "student_id": student_id,
            "exam_name": exam_name,
            "exam_date": exam_date,
            "error_type": error_type,
            "score": score,
            "description": description,
            "detailed_analysis": detailed_analysis or {},
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.error_records.append(record)

    def import_from_error_tracker(self, error_tracker) -> int:
        """从错题追踪器导入数据"""
        imported = 0

        # 这里简化处理，实际应该遍历所有学生的错题
        for error in error_tracker.errors:
            self.add_error_record(
                student_id=error.student_id,
                exam_name=error.exam_name,
                exam_date=error.exam_date,
                error_type=error.error_type,
                score=error.score,
                description=error.error_description
            )
            imported += 1

        return imported

    def _create_default_analysis(self, student_id: int) -> HabitAnalysis:
        """创建默认分析结果（无数据时）"""
        return HabitAnalysis(
            student_id=student_id,
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            error_distribution={},
            habit_scores={habit: 100.0 for habit in self.habit_dimensions.keys()},
            main_issues=[],
            suggestions=[
                "暂无错题记录，建议先添加学生的考试错题数据",
                "保持良好的学习习惯，继续努力",
                "建立错题本，及时记录和分析错题"
            ],
            trends={habit: [] for habit in self.habit_dimensions.keys()}
        )

    def analyze_student_habits(self, student_id: int) -> HabitAnalysis:
        """
        分析学生的学习习惯

        Args:
            student_id: 学生 ID

        Returns:
            习惯分析结果
        """
        # 筛选该学生的记录
        student_records = [r for r in self.error_records if r["student_id"] == student_id]

        if not student_records:
            # 返回默认结果
            return self._create_default_analysis(student_id)

        # 错误类型统计
        error_dist = {}
        for record in student_records:
            error_type = self._classify_error(record)
            error_dist[error_type] = error_dist.get(error_type, 0) + 1

        # 习惯评分计算
        habit_scores = self._calculate_habit_scores(error_dist, len(student_records))

        # 主要问题识别
        main_issues = self._identify_main_issues(error_dist, habit_scores)

        # 改进建议生成
        suggestions = self._generate_suggestions(main_issues, habit_scores)

        # 趋势分析
        trends = self._analyze_trends(student_records)

        return HabitAnalysis(
            student_id=student_id,
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            error_distribution=error_dist,
            habit_scores=habit_scores,
            main_issues=main_issues,
            suggestions=suggestions,
            trends=trends
        )

    def _classify_error(self, record: Dict) -> str:
        """根据记录分类错误类型"""
        description = (record.get("description", "") + " " +
                      record.get("detailed_analysis", {}).get("error_analysis", "")).lower()

        # 匹配错误模式
        for pattern, info in self.error_patterns.items():
            for keyword in info["keywords"]:
                if keyword in description:
                    return pattern

        # 默认返回原错误类型
        return record.get("error_type", "其他")

    def _calculate_habit_scores(self, error_dist: Dict, total_errors: int) -> Dict[str, float]:
        """计算各习惯维度得分"""
        scores = {}

        for habit, info in self.habit_dimensions.items():
            # 计算该习惯相关的错误总数
            related_error_count = sum(
                error_dist.get(err_type, 0)
                for err_type in info["related_errors"]
            )

            # 得分计算：假设平均每错一次扣 5 分，起始分 100
            base_score = 100
            penalty = related_error_count * (100 / max(total_errors, 1)) * 0.5
            score = max(0, base_score - penalty)

            scores[habit] = round(score, 1)

        return scores

    def _identify_main_issues(self, error_dist: Dict, habit_scores: Dict) -> List[str]:
        """识别主要问题"""
        issues = []

        # 找出错误最多的类型
        if error_dist:
            max_error_type = max(error_dist, key=error_dist.get)
            count = error_dist[max_error_type]
            if count >= 3:
                pattern = self.error_patterns.get(max_error_type, {})
                issues.append(f"**{max_error_type}** 较多（{count}次）：{pattern.get('description', '')}")

        # 找出得分最低的习惯
        if habit_scores:
            min_habit = min(habit_scores, key=habit_scores.get)
            score = habit_scores[min_habit]
            if score < 60:
                habit = self.habit_dimensions.get(min_habit, {})
                issues.append(f"**{min_habit}** 需加强（得分{score}）：{habit.get('description', '')}")

        return issues

    def _generate_suggestions(self, main_issues: List[str], habit_scores: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 根据最低分习惯生成建议
        if habit_scores:
            sorted_habits = sorted(habit_scores.items(), key=lambda x: x[1])

            for habit, score in sorted_habits[:3]:
                if score < 80:
                    suggestion = self._get_habit_suggestion(habit)
                    suggestions.append(f"{habit}: {suggestion}")

        # 通用建议
        if not suggestions:
            suggestions = [
                "保持现有良好习惯，继续努力",
                "建议建立错题本，定期回顾",
                "可以适当增加练习难度"
            ]

        return suggestions

    def _get_habit_suggestion(self, habit: str) -> str:
        """获取特定习惯的改进建议"""
        suggestion_map = {
            "仔细读题": "做题前用笔圈出关键词，读题至少两遍再动笔",
            "规范书写": "使用草稿纸分区计算，保持卷面整洁，步骤写完整",
            "认真计算": "加强口算和笔算练习，每天 5 分钟计算训练",
            "检查习惯": "做完后从后往前检查，重点检查计算和单位",
            "时间管理": "平时练习限时完成，模拟考场节奏，先易后难",
            "知识扎实": "建立知识框架图，定期复习，做错题整理"
        }
        return suggestion_map.get(habit, "针对性练习，查漏补缺")

    def _analyze_trends(self, student_records: List[Dict]) -> Dict[str, List[float]]:
        """分析习惯变化趋势"""
        trends = {habit: [] for habit in self.habit_dimensions.keys()}

        # 按月份分组
        monthly_errors: Dict[str, Dict] = {}

        for record in student_records:
            month = record["exam_date"][:7]  # YYYY-MM
            if month not in monthly_errors:
                monthly_errors[month] = {}
            error_type = self._classify_error(record)
            monthly_errors[month][error_type] = monthly_errors[month].get(error_type, 0) + 1

        # 计算每月习惯得分
        for month in sorted(monthly_errors.keys()):
            month_errors = monthly_errors[month]
            total = sum(month_errors.values())
            scores = self._calculate_habit_scores(month_errors, total)

            for habit in trends.keys():
                trends[habit].append(scores.get(habit, 0))

        return trends

    def generate_habit_report(self, student_id: int, student_name: str) -> str:
        """生成学习习惯分析报告"""
        analysis = self.analyze_student_habits(student_id)

        md = f"""# 📝 {student_name} 的学习习惯分析报告

**分析日期**: {analysis.analysis_date}
**数据基础**: 共分析 {sum(analysis.error_distribution.values())} 次错误记录

---

## 📊 错误类型分布

"""
        # 错误类型饼图数据
        for error_type, count in analysis.error_distribution.items():
            pattern = self.error_patterns.get(error_type, {})
            md += f"- **{error_type}**: {count}次\n"
            md += f"  > {pattern.get('description', '')}\n\n"

        md += """
---

## 📈 习惯维度评分

| 习惯维度 | 得分 | 评级 |
|----------|------|------|
"""
        for habit, score in analysis.habit_scores.items():
            level = "🌟" if score >= 85 else "👍" if score >= 70 else "👌" if score >= 55 else "💪"
            md += f"| {habit} | {score} | {level} |\n"

        md += f"""
---

## ⚠️ 主要问题

"""
        for i, issue in enumerate(analysis.main_issues, 1):
            md += f"{i}. {issue}\n\n"

        md += """
---

## 💡 改进建议

"""
        for i, sug in enumerate(analysis.suggestions, 1):
            md += f"{i}. {sug}\n\n"

        # 趋势分析
        if any(analysis.trends.values()):
            md += """
---

## 📉 习惯变化趋势

"""
            for habit, values in analysis.trends.items():
                if values:
                    trend_arrow = "📈" if values[-1] > values[0] else "📉" if values[-1] < values[0] else "➡️"
                    md += f"- **{habit}**: {values[0]} → {values[-1]} {trend_arrow}\n"

        md += """
---

## 📋 行动计划

根据以上分析，建议制定以下行动计划：

1. **本周重点**: 选择一个最需改进的习惯，制定具体行动计划
2. **每日练习**: 针对薄弱环节进行专项训练
3. **每周回顾**: 周末检查本周表现，调整下周计划
4. **家长配合**: 请家长协助监督习惯养成

---

*好习惯成就好未来！坚持 21 天，让优秀成为习惯！*
"""

        return md

    def get_quick_tips(self, student_id: int) -> List[str]:
        """获取快速提示"""
        analysis = self.analyze_student_habits(student_id)

        tips = ["📌 **今日提醒**:"]

        # 根据最低分习惯给出提示
        if analysis.habit_scores:
            min_habit = min(analysis.habit_scores, key=analysis.habit_scores.get)
            tips.append(f"重点关注：**{min_habit}**")
            tips.append(self._get_habit_suggestion(min_habit))

        # 随机正能量
        encouragement = [
            "✨ 细心是成功的保证！",
            "💪 坚持就是胜利！",
            "🌟 每一次进步都值得肯定！",
            "📚 好的习惯会让你受益终生！"
        ]
        tips.append(encouragement[datetime.now().day % len(encouragement)])

        return tips


def main():
    """测试"""
    analyzer = StudyHabitAnalyzer()

    # 添加测试数据
    analyzer.add_error_record(
        student_id=1001,
        exam_name="单元 3",
        exam_date="2024-09-15",
        error_type="知识性错误",
        score=75,
        description="计算进位错误，审题不清"
    )

    analyzer.add_error_record(
        student_id=1001,
        exam_name="练习 5",
        exam_date="2024-09-20",
        error_type="计算错误",
        score=82,
        description="口诀记错，计算粗心"
    )

    analyzer.add_error_record(
        student_id=1001,
        exam_name="期中",
        exam_date="2024-10-15",
        error_type="审题错误",
        score=85,
        description="漏看条件，单位没注意"
    )

    # 分析
    analysis = analyzer.analyze_student_habits(1001)
    print(f"习惯评分：{analysis.habit_scores}")
    print(f"主要问题：{analysis.main_issues}")
    print(f"建议：{analysis.suggestions}")

    # 生成报告
    report = analyzer.generate_habit_report(1001, "张三")
    print(f"\n报告预览:\n{report[:800]}...")

    # 快速提示
    tips = analyzer.get_quick_tips(1001)
    print(f"\n快速提示:")
    for tip in tips:
        print(f"  {tip}")


if __name__ == "__main__":
    main()
