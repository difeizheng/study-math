"""
能力成长档案模块
生成学生专属的数学能力雷达图，追踪 5 大核心素养发展
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class AbilityScore:
    """能力得分"""
    ability_name: str
    score: float  # 0-100
    level: str  # 优秀/良好/中等/需努力
    description: str
    trends: List[float]  # 历史趋势


# 五大核心素养定义
CORE_ABILITIES = {
    "数感": {
        "description": "对数的概念、大小、关系的直观理解和灵活运用能力",
        "sub_abilities": ["数的认识", "数的大小比较", "数的估算", "数与运算的联系"],
        "knowledge_mapping": [
            "G1U01", "G1U03", "G1U05", "G1U06", "G1D02", "G1D03", "G1D05",
            "G2U02", "G2D07", "G3U02", "G3U04", "G3U05", "G3U08", "G3D07"
        ]
    },
    "符号意识": {
        "description": "理解并运用数学符号进行表达、运算和推理的能力",
        "sub_abilities": ["运算符号理解", "等式意识", "代数思维萌芽", "符号转换"],
        "knowledge_mapping": [
            "G1U03", "G1U05", "G1U08", "G1D02", "G1D05",
            "G2U04", "G2U06", "G2D02", "G2D04", "G2D05", "G2D06",
            "G3U05", "G3U06", "G3D02", "G3D04"
        ]
    },
    "空间观念": {
        "description": "对空间图形、位置关系、几何变换的想象和理解能力",
        "sub_abilities": ["图形认识", "空间位置", "几何变换", "测量能力"],
        "knowledge_mapping": [
            "G1U02", "G1U04", "G1D01",
            "G2U01", "G2U03", "G2U05", "G2D03",
            "G3U03", "G3U07", "G3D01", "G3D05"
        ]
    },
    "数据分析观念": {
        "description": "收集、整理、分析数据，从数据中提取信息的能力",
        "sub_abilities": ["数据收集", "数据整理", "统计图表", "数据推断"],
        "knowledge_mapping": [
            "G2D01", "G3D03"
        ]
    },
    "推理能力": {
        "description": "运用逻辑推理解决数学问题的思维能力",
        "sub_abilities": ["归纳推理", "演绎推理", "类比推理", "解决问题策略"],
        "knowledge_mapping": [
            "G1U08", "G1D02", "G1D04",
            "G2U07", "G2D05", "G2D06",
            "G3U01", "G3D06"
        ]
    }
}

# 能力等级评定标准
ABILITY_LEVELS = {
    "优秀": {"min": 85, "description": "能力发展突出，远超同龄人平均水平"},
    "良好": {"min": 70, "description": "能力发展较好，达到同龄人平均水平"},
    "中等": {"min": 55, "description": "能力发展一般，基本达到要求"},
    "需努力": {"min": 0, "description": "能力发展不足，需要加强培养"}
}


class AbilityPortfolio:
    """能力成长档案"""

    def __init__(self):
        self.abilities = CORE_ABILITIES
        self.levels = ABILITY_LEVELS

    def calculate_ability_score(self, ability_name: str,
                                knowledge_mastery: Dict[str, Dict]) -> Tuple[float, str]:
        """
        计算某项核心能力的得分

        Args:
            ability_name: 能力名称
            knowledge_mastery: 知识点掌握情况 {code: {avg_score: ...}}

        Returns:
            (得分，等级)
        """
        if ability_name not in self.abilities:
            return 0.0, "未知"

        ability = self.abilities[ability_name]
        scores = []

        for kp_code in ability["knowledge_mapping"]:
            if kp_code in knowledge_mastery:
                scores.append(knowledge_mastery[kp_code]["avg_score"])

        if not scores:
            return 0.0, "数据不足"

        # 计算平均分
        avg_score = np.mean(scores)

        # 确定等级
        level = "需努力"
        for level_name, criteria in self.levels.items():
            if avg_score >= criteria["min"]:
                level = level_name
                break

        return round(avg_score, 2), level

    def analyze_all_abilities(self, knowledge_mastery: Dict[str, Dict]) -> Dict:
        """
        分析所有核心能力

        Args:
            knowledge_mastery: 知识点掌握情况

        Returns:
            能力分析报告
        """
        report = {
            "abilities": {},
            "radar_data": [],
            "strongest": None,
            "weakest": None,
            "overall_level": "中等"
        }

        scores = []

        for ability_name in self.abilities.keys():
            score, level = self.calculate_ability_score(ability_name, knowledge_mastery)
            ability_info = self.abilities[ability_name]

            report["abilities"][ability_name] = {
                "score": score,
                "level": level,
                "description": ability_info["description"],
                "sub_abilities": ability_info["sub_abilities"],
                "knowledge_count": len(ability_info["knowledge_mapping"])
            }

            report["radar_data"].append({
                "ability": ability_name,
                "score": score
            })

            scores.append((ability_name, score))

        # 找出最强和最弱能力
        if scores:
            scores.sort(key=lambda x: x[1], reverse=True)
            report["strongest"] = {
                "name": scores[0][0],
                "score": scores[0][1]
            }
            report["weakest"] = {
                "name": scores[-1][0],
                "score": scores[-1][1]
            }

            # 整体水平
            avg_all = np.mean([s[1] for s in scores])
            for level_name, criteria in self.levels.items():
                if avg_all >= criteria["min"]:
                    report["overall_level"] = level_name
                    break

        return report

    def get_ability_trends(self, ability_name: str,
                           semester_scores: Dict[str, Dict[str, Dict]]) -> List[float]:
        """
        获取某项能力的历史趋势

        Args:
            ability_name: 能力名称
            semester_scores: 各学期知识点掌握情况 {semester: {code: {avg_score: ...}}}

        Returns:
            能力得分趋势列表
        """
        trends = []

        for semester in sorted(semester_scores.keys()):
            score, _ = self.calculate_ability_score(ability_name, semester_scores[semester])
            trends.append(score)

        return trends

    def generate_growth_report(self, student_name: str, student_id: int,
                               knowledge_mastery: Dict[str, Dict]) -> str:
        """
        生成能力成长报告（Markdown 格式）

        Args:
            student_name: 学生姓名
            student_id: 学号
            knowledge_mastery: 知识点掌握情况

        Returns:
            Markdown 格式报告
        """
        report = self.analyze_all_abilities(knowledge_mastery)

        md = f"""# 🌟 {student_name} 的数学能力成长档案

**学号**: {student_id}
**生成日期**: {datetime.now().strftime("%Y-%m-%d")}
**综合评级**: {self._get_level_badge(report["overall_level"])}

---

## 📊 五大核心素养雷达图数据

| 核心素养 | 得分 | 等级 | 能力描述 |
|----------|------|------|----------|
"""
        for ability_name, data in report["abilities"].items():
            icon = self._get_ability_icon(ability_name)
            md += f"| {icon} {ability_name} | {data['score']} | {self._get_level_badge(data['level'])} | {data['description'][:20]}... |\n"

        md += f"""
---

## 🏆 能力亮点

### 最强能力
{self._get_ability_icon(report['strongest']['name'])} **{report['strongest']['name']}**: {report['strongest']['score']}分

> {self.abilities[report['strongest']['name']]['description']}

### 需加强能力
📚 **{report['weakest']['name']}**: {report['weakest']['score']}分

> {self.abilities[report['weakest']['name']]['description']}

---

## 📈 各能力详细分析

"""
        for ability_name, data in report["abilities"].items():
            icon = self._get_ability_icon(ability_name)
            md += f"""### {icon} {ability_name}

**得分**: {data['score']} | **等级**: {self._get_level_badge(data['level'])}

**子能力构成**:
"""
            for sub in data["sub_abilities"]:
                md += f"- {sub}\n"

            md += f"\n**涉及知识点**: {data['knowledge_count']}个\n\n"

        md += """---

## 💡 个性化发展建议

根据能力分析结果，提出以下建议：

"""
        # 生成建议
        suggestions = self._generate_suggestions(report)
        for i, sug in enumerate(suggestions, 1):
            md += f"{i}. {sug}\n"

        md += """
---

## 📅 能力发展记录

| 时间 | 最强能力 | 最弱能力 | 综合评级 |
|------|----------|----------|----------|
| 本次评估 | {strong} | {weak} | {overall} |

> 注：持续记录可生成能力发展趋势图

---

*本报告基于人教版小学数学知识点体系和学生考试表现生成*
*五大核心素养依据《义务教育数学课程标准》定义*
""".format(
            strong=report["strongest"]["name"],
            weak=report["weakest"]["name"],
            overall=report["overall_level"]
        )

        return md

    def _get_ability_icon(self, ability_name: str) -> str:
        """获取能力图标"""
        icons = {
            "数感": "🔢",
            "符号意识": "🔣",
            "空间观念": "📐",
            "数据分析观念": "📊",
            "推理能力": "🧠"
        }
        return icons.get(ability_name, "📌")

    def _get_level_badge(self, level: str) -> str:
        """获取等级徽章"""
        badges = {
            "优秀": "🌟 优秀",
            "良好": "👍 良好",
            "中等": "👌 中等",
            "需努力": "💪 需努力"
        }
        return badges.get(level, level)

    def _generate_suggestions(self, report: Dict) -> List[str]:
        """生成发展建议"""
        suggestions = []

        # 针对最强能力的建议
        strongest = report["strongest"]["name"]
        suggestions.append(f"继续保持**{strongest}**的优势，可适当挑战更高难度的题目")

        # 针对最弱能力的建议
        weakest = report["weakest"]["name"]
        weakest_info = self.abilities[weakest]
        suggestions.append(f"重点培养**{weakest}**：{weakest_info['description']}")

        # 针对具体子能力的建议
        weakest_data = report["abilities"][weakest]
        suggestions.append(f"从以下子能力入手：{', '.join(weakest_data['sub_abilities'][:2])}")

        # 综合建议
        if report["overall_level"] == "优秀":
            suggestions.append("综合能力优秀，建议参加数学拓展活动或竞赛")
        elif report["overall_level"] == "良好":
            suggestions.append("整体发展良好，稳步提升即可")
        else:
            suggestions.append("建议制定专项提升计划，查漏补缺")

        return suggestions

    def export_radar_chart_data(self, knowledge_mastery: Dict[str, Dict]) -> Dict:
        """
        导出雷达图数据（用于前端可视化）

        Returns:
            雷达图数据格式
        """
        report = self.analyze_all_abilities(knowledge_mastery)

        return {
            "categories": list(self.abilities.keys()),
            "values": [report["abilities"][cat]["score"] for cat in self.abilities.keys()],
            "levels": [report["abilities"][cat]["level"] for cat in self.abilities.keys()],
            "fill": "toself",
            "max_value": 100
        }

    def compare_two_students(self, mastery_1: Dict, mastery_2: Dict,
                             name_1: str, name_2: str) -> Dict:
        """
        对比两个学生的能力发展

        Args:
            mastery_1: 学生 1 的知识点掌握
            mastery_2: 学生 2 的知识点掌握
            name_1: 学生 1 姓名
            name_2: 学生 2 姓名

        Returns:
            对比报告
        """
        report_1 = self.analyze_all_abilities(mastery_1)
        report_2 = self.analyze_all_abilities(mastery_2)

        comparison = {
            "students": [
                {"name": name_1, "report": report_1},
                {"name": name_2, "report": report_2}
            ],
            "radar_comparison": {
                "categories": list(self.abilities.keys()),
                "traces": [
                    {
                        "name": name_1,
                        "values": [report_1["abilities"][cat]["score"] for cat in self.abilities.keys()]
                    },
                    {
                        "name": name_2,
                        "values": [report_2["abilities"][cat]["score"] for cat in self.abilities.keys()]
                    }
                ]
            },
            "analysis": []
        }

        # 对比分析
        for ability in self.abilities.keys():
            score_1 = report_1["abilities"][ability]["score"]
            score_2 = report_2["abilities"][ability]["score"]
            diff = score_1 - score_2

            if abs(diff) < 3:
                analysis = f"在{ability}方面，两人水平相当"
            elif diff > 0:
                analysis = f"在{ability}方面，{name_1}领先{abs(diff):.1f}分"
            else:
                analysis = f"在{ability}方面，{name_2}领先{abs(diff):.1f}分"

            comparison["analysis"].append(analysis)

        return comparison


def main():
    """测试"""
    portfolio = AbilityPortfolio()

    # 模拟知识点掌握数据
    test_mastery = {
        "G1U03": {"avg_score": 85},
        "G1U05": {"avg_score": 90},
        "G1U08": {"avg_score": 88},
        "G1D02": {"avg_score": 82},
        "G1D03": {"avg_score": 78},
        "G2U04": {"avg_score": 75},
        "G2U01": {"avg_score": 92},
        "G2D01": {"avg_score": 88},
    }

    # 分析所有能力
    report = portfolio.analyze_all_abilities(test_mastery)
    print("能力分析结果:")
    for ability, data in report["abilities"].items():
        print(f"  {ability}: {data['score']}分 ({data['level']})")

    print(f"\n最强能力：{report['strongest']['name']} ({report['strongest']['score']}分)")
    print(f"需加强能力：{report['weakest']['name']} ({report['weakest']['score']}分)")

    # 生成报告
    md_report = portfolio.generate_growth_report("张三", 1001, test_mastery)
    print(f"\n成长报告预览:\n{md_report[:800]}...")


if __name__ == "__main__":
    main()
