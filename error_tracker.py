"""
错题追踪本模块
记录学生错题、分析错误原因、生成复习计划和举一反三练习
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import re


@dataclass
class ErrorRecord:
    """错题记录"""
    student_id: int
    student_name: str
    exam_name: str  # 考试名称
    exam_date: str  # 考试日期
    semester: str  # 学期
    knowledge_code: str  # 知识点编码
    knowledge_name: str  # 知识点名称
    error_type: str  # 错误类型：知识性/计算/审题/其他
    score: float  # 该题得分（假设满分 100 的折算分）
    error_description: str  # 错误描述
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    review_count: int = 0  # 已复习次数
    last_review: Optional[str] = None  # 最后复习日期
    mastered: bool = False  # 是否已掌握


# 艾宾浩斯遗忘曲线复习间隔（天）
EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]

# 错误类型定义
ERROR_TYPES = {
    "知识性错误": "对知识点理解不透彻或概念混淆",
    "计算错误": "计算过程中出现失误，如进位错误、口诀记错",
    "审题错误": "没有理解题意或漏看关键信息",
    "书写错误": "抄错数字、写错符号等",
    "时间不足": "考试时间不够导致未完成或匆忙作答",
}

# 举一反三题目模板（根据知识点推荐）
PRACTICE_TEMPLATES = {
    "G1U03": ["5 + 3 = ?", "8 - 2 = ?", "4 + □ = 7", "□ - 3 = 2"],
    "G1U05": ["7 + 2 = ?", "9 - 4 = ?", "3 + □ = 9", "6 + □ = 10"],
    "G1U08": ["9 + 5 = ?", "8 + 7 = ?", "7 + 6 = ?", "9 + 9 = ?"],
    "G1D02": ["15 - 7 = ?", "13 - 6 = ?", "11 - 4 = ?", "16 - 8 = ?"],
    "G1D03": ["35 + 20 = ?", "78 - 30 = ?", "42 + 7 = ?", "65 - 4 = ?"],
    "G1D05": ["23 + 5 = ?", "47 - 6 = ?", "30 + 25 = ?", "68 - 40 = ?"],
    "G2U02": ["35 + 27 = ?", "82 - 46 = ?", "19 + 58 = ?", "73 - 28 = ?"],
    "G2U04": ["3×4 = ?", "5×6 = ?", "7×8 = ?", "9×5 = ?"],
    "G2U06": ["7×7 = ?", "8×9 = ?", "6×8 = ?", "9×9 = ?"],
    "G2D02": ["12÷3 = ?", "24÷6 = ?", "35÷7 = ?", "48÷8 = ?"],
    "G2D04": ["21÷3 = ?", "36÷4 = ?", "54÷6 = ?", "72÷8 = ?"],
    "G2D05": ["3×4 + 5 = ?", "20 - 2×3 = ?", "(5+3)×2 = ?", "48÷6 + 3 = ?"],
    "G2D06": ["17÷3 = ?...?", "25÷4 = ?...?", "38÷5 = ?...?", "47÷6 = ?...?"],
    "G3U02": ["230 + 150 = ?", "480 - 290 = ?", "375 + 128 = ?", "602 - 347 = ?"],
    "G3U04": ["456 + 278 = ?", "803 - 456 = ?", "527 + 389 = ?", "700 - 234 = ?"],
    "G3U05": ["12 是 3 的几倍？", "5 的 6 倍是多少？", "36 是 9 的几倍？", "7 的 8 倍是多少？"],
    "G3U06": ["23×4 = ?", "156×3 = ?", "207×5 = ?", "340×6 = ?"],
    "G3U07": ["长方形长 8cm 宽 5cm，周长是多少？", "正方形边长 6cm，周长是多少？"],
    "G3U08": ["1/2 + 1/4 = ?", "3/5 - 1/5 = ?", "1/3 + 1/6 = ?", "7/8 - 3/8 = ?"],
    "G3D02": ["84÷2 = ?", "156÷3 = ?", "245÷5 = ?", "624÷6 = ?"],
    "G3D04": ["23×12 = ?", "45×23 = ?", "67×34 = ?", "89×56 = ?"],
    "G3D05": ["长方形长 10m 宽 6m，面积是多少？", "正方形边长 8dm，面积是多少？"],
    "G3D07": ["0.5 + 0.3 = ?", "1.2 - 0.7 = ?", "2.5 + 3.8 = ?", "7.6 - 4.9 = ?"],
}


class ErrorTracker:
    """错题追踪器"""

    def __init__(self, data_dir: str = "data", error_db_path: str = "error_db.json"):
        self.data_dir = Path(data_dir)
        self.error_db_path = Path(error_db_path)
        self.errors: List[ErrorRecord] = []
        self.student_names: Dict[int, str] = {}
        self.knowledge_points = self._load_knowledge_points()
        self._load_errors()

    def _load_knowledge_points(self) -> Dict:
        """加载知识点体系"""
        from deep_analyzer import KNOWLEDGE_SYSTEM
        return KNOWLEDGE_SYSTEM

    def _load_errors(self):
        """加载错题数据库"""
        if self.error_db_path.exists():
            with open(self.error_db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.errors = [ErrorRecord(**e) for e in data]

    def _save_errors(self):
        """保存错题数据库"""
        data = [e.__dict__ for e in self.errors]
        with open(self.error_db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_error(self, student_id: int, exam_name: str, exam_date: str,
                  semester: str, knowledge_code: str, error_type: str,
                  score: float, error_description: str = "") -> ErrorRecord:
        """添加错题记录"""
        student_name = self.student_names.get(student_id, "Unknown")
        kp_info = self.knowledge_points.get(knowledge_code)
        knowledge_name = kp_info.name if kp_info else knowledge_code

        error = ErrorRecord(
            student_id=student_id,
            student_name=student_name,
            exam_name=exam_name,
            exam_date=exam_date,
            semester=semester,
            knowledge_code=knowledge_code,
            knowledge_name=knowledge_name,
            error_type=error_type,
            score=score,
            error_description=error_description
        )

        self.errors.append(error)
        self._save_errors()
        return error

    def get_student_errors(self, student_id: int, include_mastered: bool = False) -> List[ErrorRecord]:
        """获取指定学生的错题"""
        errors = [e for e in self.errors if e.student_id == student_id]
        if not include_mastered:
            errors = [e for e in errors if not e.mastered]
        return sorted(errors, key=lambda x: x.created_at, reverse=True)

    def get_error_statistics(self, student_id: int) -> Dict:
        """获取错题统计"""
        errors = self.get_student_errors(student_id, include_mastered=True)
        if not errors:
            return {"total": 0}

        # 按错误类型统计
        error_type_stats = {}
        for e in errors:
            error_type_stats[e.error_type] = error_type_stats.get(e.error_type, 0) + 1

        # 按知识点统计
        knowledge_stats = {}
        for e in errors:
            if e.knowledge_code not in knowledge_stats:
                knowledge_stats[e.knowledge_code] = {
                    "name": e.knowledge_name,
                    "count": 0,
                    "mastered": 0
                }
            knowledge_stats[e.knowledge_code]["count"] += 1
            if e.mastered:
                knowledge_stats[e.knowledge_code]["mastered"] += 1

        # 按学期统计
        semester_stats = {}
        for e in errors:
            semester_stats[e.semester] = semester_stats.get(e.semester, 0) + 1

        # 计算复习进度
        total = len(errors)
        mastered = sum(1 for e in errors if e.mastered)
        pending_review = sum(1 for e in errors if not e.mastered and e.review_count > 0)
        new_errors = sum(1 for e in errors if not e.mastered and e.review_count == 0)

        return {
            "total": total,
            "mastered": mastered,
            "pending_review": pending_review,
            "new_errors": new_errors,
            "mastery_rate": round(mastered / total * 100, 1) if total > 0 else 0,
            "error_types": error_type_stats,
            "knowledge_points": knowledge_stats,
            "semesters": semester_stats,
        }

    def get_review_plan(self, student_id: int) -> List[Dict]:
        """
        根据艾宾浩斯遗忘曲线生成复习计划
        返回需要复习的错题列表
        """
        errors = self.get_student_errors(student_id)
        today = datetime.now().date()
        review_items = []

        for error in errors:
            if error.mastered:
                continue

            # 计算上次复习时间
            if error.last_review:
                last_review_date = datetime.strptime(error.last_review, "%Y-%m-%d").date()
                days_since_review = (today - last_review_date).days
            else:
                # 从未复习，从创建日期算起
                created_date = datetime.strptime(error.created_at, "%Y-%m-%d").date()
                days_since_review = (today - created_date).days

            # 检查是否到了复习时间
            next_interval = EBBINGHAUS_INTERVALS[error.review_count] if error.review_count < len(EBBINGHAUS_INTERVALS) else EBBINGHAUS_INTERVALS[-1]

            if days_since_review >= next_interval:
                # 计算推荐复习次数
                priority = error.review_count + 1
                review_items.append({
                    "error": error,
                    "priority": priority,  # 优先级：复习次数少的优先
                    "days_overdue": days_since_review - next_interval,
                    "next_interval": next_interval
                })

        # 按优先级排序
        review_items.sort(key=lambda x: (-x["priority"], -x["days_overdue"]))
        return review_items

    def mark_reviewed(self, error_id: int, mastered: bool = False):
        """标记错题已复习"""
        for error in self.errors:
            if id(error) == error_id or (
                error.student_id == error_id and
                error.knowledge_code == error_id
            ):
                error.review_count += 1
                error.last_review = datetime.now().strftime("%Y-%m-%d")
                if mastered:
                    error.mastered = True
                self._save_errors()
                return True
        return False

    def mark_error_mastered(self, student_id: int, knowledge_code: str):
        """标记某知识点的所有错题已掌握"""
        updated = False
        for error in self.errors:
            if error.student_id == student_id and error.knowledge_code == knowledge_code:
                if not error.mastered:
                    error.mastered = True
                    updated = True
        if updated:
            self._save_errors()

    def get_practice_recommendations(self, student_id: int, limit: int = 10) -> List[Dict]:
        """获取举一反三练习推荐"""
        errors = self.get_student_errors(student_id)
        recommendations = []

        # 按知识点分组，统计错误次数
        knowledge_errors = {}
        for error in errors:
            if not error.mastered:
                if error.knowledge_code not in knowledge_errors:
                    knowledge_errors[error.knowledge_code] = {
                        "name": error.knowledge_name,
                        "count": 0,
                        "error_types": []
                    }
                knowledge_errors[error.knowledge_code]["count"] += 1
                knowledge_errors[error.knowledge_code]["error_types"].append(error.error_type)

        # 按错误次数排序
        sorted_knowledge = sorted(
            knowledge_errors.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:limit]

        for kp_code, data in sorted_knowledge:
            practice_questions = PRACTICE_TEMPLATES.get(kp_code, [])
            if not practice_questions:
                # 生成通用练习题
                practice_questions = self._generate_generic_practice(kp_code)

            recommendations.append({
                "knowledge_code": kp_code,
                "knowledge_name": data["name"],
                "error_count": data["count"],
                "error_types": list(set(data["error_types"])),
                "practice_questions": practice_questions,
                "suggestion": self._get_practice_suggestion(kp_code, data["error_types"])
            })

        return recommendations

    def _generate_generic_practice(self, knowledge_code: str) -> List[str]:
        """生成通用练习题"""
        kp = self.knowledge_points.get(knowledge_code)
        if not kp:
            return ["请查阅教材相关练习"]

        # 根据知识点名称生成建议
        name = kp.name
        return [
            f"复习{name}的核心概念",
            f"完成教材{name}相关练习题",
            f"整理{name}的解题方法",
            f"总结{name}的常见错误类型"
        ]

    def _get_practice_suggestion(self, knowledge_code: str, error_types: List[str]) -> str:
        """获取练习建议"""
        suggestions = []

        if "知识性错误" in error_types:
            suggestions.append("重新学习该知识点的基本概念和例题")
        if "计算错误" in error_types:
            suggestions.append("加强计算练习，提高计算准确性")
        if "审题错误" in error_types:
            suggestions.append("练习圈画关键词，养成仔细读题的习惯")
        if "书写错误" in error_types:
            suggestions.append("规范书写，做完后认真检查")

        return "；".join(suggestions) if suggestions else "针对性练习，查漏补缺"

    def get_error_trend(self, student_id: int) -> List[Dict]:
        """获取错题趋势分析"""
        errors = self.get_student_errors(student_id, include_mastered=True)

        # 按日期分组统计
        date_stats = {}
        for error in errors:
            date = error.created_at[:7]  # YYYY-MM
            if date not in date_stats:
                date_stats[date] = {"new": 0, "mastered": 0}
            date_stats[date]["new"] += 1
            if error.mastered:
                date_stats[date]["mastered"] += 1

        trend = []
        for date in sorted(date_stats.keys()):
            trend.append({
                "date": date,
                "new_errors": date_stats[date]["new"],
                "mastered": date_stats[date]["mastered"],
                "net_increase": date_stats[date]["new"] - date_stats[date]["mastered"]
            })

        return trend

    def export_error_book(self, student_id: int) -> str:
        """导出错题本（Markdown 格式）"""
        errors = self.get_student_errors(student_id)
        stats = self.get_error_statistics(student_id)
        student_name = self.student_names.get(student_id, "Unknown")

        md = f"""# 📕 {student_name} 的错题本

**生成日期**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**统计**: 共{stats['total']}道错题，已掌握{stats['mastered']}道，掌握率{stats['mastery_rate']}%

---

## 📊 错题分布

### 按错误类型
"""
        for error_type, count in stats.get("error_types", {}).items():
            md += f"- **{error_type}**: {count}道\n"

        md += "\n### 按知识点\n"
        for kp_code, data in stats.get("knowledge_points", {}).items():
            md += f"- **{data['name']}**: {data['count']}道（已掌握{data['mastered']}道）\n"

        md += "\n---\n\n## 📝 错题详情\n\n"

        # 按知识点分组
        kp_groups = {}
        for error in errors:
            if error.knowledge_code not in kp_groups:
                kp_groups[error.knowledge_code] = []
            kp_groups[error.knowledge_code].append(error)

        for kp_code, kp_errors in kp_groups.items():
            kp_name = kp_errors[0].knowledge_name if kp_errors else kp_code
            md += f"### 📘 {kp_name}\n\n"

            for i, error in enumerate(kp_errors, 1):
                status = "✅" if error.mastered else "⏳"
                md += f"""**{i}. {error.exam_name}** {status}
- **考试日期**: {error.exam_date}
- **错误类型**: {error.error_type}
- **得分**: {error.score}分
- **记录日期**: {error.created_at}
- **复习次数**: {error.review_count}次
- **错误描述**: {error.error_description or "无"}

"""

        md += "\n---\n\n## 💡 举一反三练习推荐\n\n"
        recommendations = self.get_practice_recommendations(student_id, limit=5)
        for rec in recommendations:
            md += f"### 📌 {rec['knowledge_name']}\n"
            md += f"**建议**: {rec['suggestion']}\n\n"
            md += "**练习题**:\n"
            for q in rec['practice_questions']:
                md += f"- {q}\n"
            md += "\n"

        return md

    def import_from_exam(self, student_id: int, semester: str, exam_name: str,
                         exam_date: str, error_knowledge_map: Dict[str, Dict]):
        """
        从考试结果批量导入错题

        error_knowledge_map: {
            "练习 1": {"knowledge": "G1U03", "error_type": "知识性错误", "score": 65, "description": "..."},
            ...
        }
        """
        for exam, info in error_knowledge_map.items():
            if exam in exam_name or exam_name in exam:
                self.add_error(
                    student_id=student_id,
                    exam_name=exam_name,
                    exam_date=exam_date,
                    semester=semester,
                    knowledge_code=info["knowledge"],
                    error_type=info["error_type"],
                    score=info["score"],
                    error_description=info.get("description", "")
                )

    def set_student_names(self, names: Dict[int, str]):
        """设置学生姓名映射"""
        self.student_names = names


def main():
    """测试"""
    tracker = ErrorTracker()

    # 设置学生姓名
    tracker.set_student_names({
        1001: "张三",
        1002: "李四"
    })

    # 添加测试错题
    tracker.add_error(
        student_id=1001,
        exam_name="单元 3",
        exam_date="2024-09-15",
        semester="1(2) 班上 学期",
        knowledge_code="G1U03",
        error_type="知识性错误",
        score=75,
        error_description="5 以内加减法概念不清"
    )

    tracker.add_error(
        student_id=1001,
        exam_name="练习 5",
        exam_date="2024-09-20",
        semester="1(2) 班上 学期",
        knowledge_code="G1U05",
        error_type="计算错误",
        score=82,
        error_description="6-10 的加减法进位错误"
    )

    # 获取统计
    stats = tracker.get_error_statistics(1001)
    print(f"错题统计：{stats}")

    # 获取复习计划
    plan = tracker.get_review_plan(1001)
    print(f"\n需要复习的错题：{len(plan)}道")

    # 获取练习推荐
    recs = tracker.get_practice_recommendations(1001)
    print(f"\n练习推荐：{len(recs)}个知识点")
    for rec in recs:
        print(f"  - {rec['knowledge_name']}: {rec['practice_questions']}")

    # 导出错题本
    error_book = tracker.export_error_book(1001)
    print(f"\n错题本预览:\n{error_book[:500]}...")


if __name__ == "__main__":
    main()
