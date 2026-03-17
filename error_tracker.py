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

# 导入数据库模块
from database import ErrorRecordDAO, StudentDAO


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

    def __init__(self, data_dir: str = "data", error_db_path: str = None):
        """
        初始化错题追踪器

        Args:
            data_dir: 数据目录
            error_db_path: 旧版 JSON 数据库路径（保留兼容性，实际使用 SQLite）
        """
        self.data_dir = Path(data_dir)
        self.error_db_path = Path(error_db_path) if error_db_path else None
        self.errors: List[ErrorRecord] = []  # 保留用于兼容
        self.student_names: Dict[int, str] = {}
        self.knowledge_points = self._load_knowledge_points()
        self._load_students()
        self._load_errors_compat()

    def _load_knowledge_points(self) -> Dict:
        """加载知识点体系"""
        from deep_analyzer import KNOWLEDGE_SYSTEM
        return KNOWLEDGE_SYSTEM

    def _load_students(self):
        """从数据库加载学生信息"""
        students = StudentDAO.get_all_students()
        for s in students:
            self.student_names[s["student_id"]] = s["name"]

    def _load_errors_compat(self):
        """从旧版 JSON 数据库加载错题（兼容性）"""
        if self.error_db_path and self.error_db_path.exists():
            with open(self.error_db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.errors = [ErrorRecord(**e) for e in data]
            # 迁移到 SQLite
            self._migrate_to_sqlite()

    def _migrate_to_sqlite(self):
        """迁移旧版 JSON 数据到 SQLite"""
        for error in self.errors:
            ErrorRecordDAO.add_error_record(
                student_id=error.student_id,
                exam_name=error.exam_name,
                exam_date=error.exam_date,
                knowledge_code=error.knowledge_code,
                knowledge_name=error.knowledge_name,
                error_type=error.error_type,
                error_description=error.error_description,
                score=error.score
            )
        # 迁移后重命名旧文件
        if self.error_db_path and self.error_db_path.exists():
            backup_path = self.error_db_path.with_suffix('.json.bak')
            self.error_db_path.rename(backup_path)

    def add_error(self, student_id: int, exam_name: str, exam_date: str,
                  semester: str, knowledge_code: str, error_type: str,
                  score: float, error_description: str = "") -> int:
        """添加错题记录"""
        # 更新学生姓名缓存
        if student_id not in self.student_names:
            student = StudentDAO.get_student(student_id)
            if student:
                self.student_names[student_id] = student["name"]

        record_id = ErrorRecordDAO.add_error_record(
            student_id=student_id,
            exam_name=exam_name,
            exam_date=exam_date,
            knowledge_code=knowledge_code,
            knowledge_name=self.knowledge_points.get(knowledge_code, type('obj', (object,), {'name': knowledge_code})).name,
            error_type=error_type,
            error_description=error_description,
            score=score
        )
        return record_id

    def get_student_errors(self, student_id: int, include_mastered: bool = False) -> List[Dict]:
        """获取指定学生的错题"""
        errors = ErrorRecordDAO.get_errors_by_student(student_id)
        if not include_mastered:
            errors = [e for e in errors if not e["is_mastered"]]
        return errors

    def get_error_statistics(self, student_id: int) -> Dict:
        """获取错题统计"""
        stats = ErrorRecordDAO.get_error_statistics(student_id)
        return stats

    def get_review_plan(self, student_id: int) -> List[Dict]:
        """
        根据艾宾浩斯遗忘曲线生成复习计划
        返回需要复习的错题列表
        """
        errors = ErrorRecordDAO.get_review_due_records(student_id)
        review_items = []

        for error in errors:
            review_items.append({
                "error": error,
                "priority": error["review_count"] + 1,
                "days_overdue": 0,
                "next_interval": EBBINGHAUS_INTERVALS[min(error["review_count"], len(EBBINGHAUS_INTERVALS)-1)]
            })

        # 按优先级排序
        review_items.sort(key=lambda x: (-x["priority"], -x["days_overdue"]))
        return review_items

    def mark_reviewed(self, record_id: int, mastered: bool = False):
        """标记错题已复习"""
        if mastered:
            ErrorRecordDAO.mark_as_mastered(record_id)
        else:
            ErrorRecordDAO.mark_as_reviewed(record_id)
        return True

    def mark_error_mastered(self, student_id: int, knowledge_code: str):
        """标记某知识点的所有错题已掌握"""
        # 获取该知识点的所有错题
        errors = ErrorRecordDAO.get_errors_by_knowledge(student_id, knowledge_code)
        for error in errors:
            ErrorRecordDAO.mark_as_mastered(error["id"])

    def get_practice_recommendations(self, student_id: int, limit: int = 10) -> List[Dict]:
        """获取举一反三练习推荐"""
        stats = ErrorRecordDAO.get_error_statistics(student_id)
        recommendations = []

        # 按知识点统计的错误次数排序
        sorted_knowledge = sorted(
            stats.get("by_knowledge", []),
            key=lambda x: x["count"],
            reverse=True
        )[:limit]

        for kp_data in sorted_knowledge:
            kp_code = kp_data["knowledge_code"]
            kp_name = kp_data["knowledge_name"]
            error_count = kp_data["count"]

            practice_questions = PRACTICE_TEMPLATES.get(kp_code, [])
            if not practice_questions:
                practice_questions = self._generate_generic_practice(kp_code)

            recommendations.append({
                "knowledge_code": kp_code,
                "knowledge_name": kp_name,
                "error_count": error_count,
                "error_types": [],
                "practice_questions": practice_questions,
                "suggestion": self._get_practice_suggestion(kp_code, [])
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
        for kp_data in stats.get("by_knowledge", []):
            md += f"- **{kp_data['knowledge_name']}**: {kp_data['count']}道\n"

        md += "\n---\n\n## 📝 错题详情\n\n"

        # 按知识点分组
        kp_groups = {}
        for error in errors:
            kp_code = error["knowledge_code"]
            if kp_code not in kp_groups:
                kp_groups[kp_code] = []
            kp_groups[kp_code].append(error)

        for kp_code, kp_errors in kp_groups.items():
            kp_name = kp_errors[0].get("knowledge_name", kp_code) if kp_errors else kp_code
            md += f"### 📘 {kp_name}\n\n"

            for i, error in enumerate(kp_errors, 1):
                status = "✅" if error.get("is_mastered", False) else "⏳"
                md += f"""**{i}. {error.get('exam_name', '未知')}** {status}
- **考试日期**: {error.get('exam_date', '未知')}
- **错误类型**: {error.get('error_type', '未知')}
- **得分**: {error.get('score', '未知')}分
- **错误描述**: {error.get('error_description', '无')}

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
