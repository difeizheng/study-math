"""
成绩录入模块
用于快速录入最近一周的考试成绩和错题
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from database import StudentDAO, ErrorRecordDAO
from logger import get_logger

logger = get_logger("score_entry")


@dataclass
class ExamScore:
    """考试成绩记录"""
    student_id: int
    exam_name: str
    exam_date: str
    score: float
    knowledge_points: List[Dict]  # 知识点列表 [{"code": "...", "name": "...", "score": 85}]


class ScoreEntryService:
    """成绩录入服务"""

    def __init__(self):
        self.knowledge_mapping = self._init_knowledge_mapping()

    def _init_knowledge_mapping(self) -> Dict:
        """初始化知识点映射（根据考试名称推断知识点）"""
        return {
            "练习 1": ["G1U03"],
            "练习 2": ["G1U05"],
            "练习 3": ["G1U08"],
            "练习 4": ["G1D02"],
            "练习 5": ["G1D03"],
            "练习 6": ["G1D05"],
            "期中": [],  # 综合知识点
            "期末": [],  # 综合知识点
        }

    def get_recent_dates(self, days: int = 7) -> List[str]:
        """获取最近 N 天的日期列表"""
        dates = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        return dates

    def get_recent_exams(self) -> List[str]:
        """获取常见的最近考试名称"""
        return [
            "练习 1", "练习 2", "练习 3", "练习 4",
            "练习 5", "练习 6", "练习 7", "练习 8",
            "单元测试（一）", "单元测试（二）", "单元测试（三）",
            "期中考试", "期末考试",
            "周测（1）", "周测（2）", "周测（3）"
        ]

    def entry_score(self, student_id: int, exam_name: str, exam_date: str,
                    score: float, wrong_questions: List[Dict]) -> Dict:
        """
        录入成绩和错题

        Args:
            student_id: 学生 ID
            exam_name: 考试名称
            exam_date: 考试日期
            score: 考试成绩
            wrong_questions: 错题列表 [
                {
                    "knowledge_code": "G1U03",
                    "knowledge_name": "1-5 的认识和加减法",
                    "error_type": "计算粗心",
                    "description": "题目描述",
                    "question_text": "题目内容",
                    "correct_answer": "正确答案"
                }
            ]

        Returns:
            录入结果
        """
        result = {
            "success": True,
            "student_id": student_id,
            "exam_name": exam_name,
            "score": score,
            "error_count": 0,
            "message": ""
        }

        try:
            # 验证学生是否存在
            student = StudentDAO.get_student(student_id)
            if not student:
                result["success"] = False
                result["message"] = f"学生 {student_id} 不存在"
                return result

            # 录入错题
            for wrong_q in wrong_questions:
                ErrorRecordDAO.add_error_record(
                    student_id=student_id,
                    exam_name=exam_name,
                    exam_date=exam_date,
                    knowledge_code=wrong_q.get("knowledge_code", "UNKNOWN"),
                    knowledge_name=wrong_q.get("knowledge_name", "未知知识点"),
                    error_type=wrong_q.get("error_type", "知识性错误"),
                    error_description=wrong_q.get("description", ""),
                    score=score,
                    question_text=wrong_q.get("question_text", ""),
                    correct_answer=wrong_q.get("correct_answer", "")
                )
                result["error_count"] += 1

            result["message"] = f"成绩录入成功！共录入 {result['error_count']} 道错题"
            logger.info(f"成绩录入：学生{student_id}, 考试{exam_name}, 分数{score}, 错题{result['error_count']}道")

        except Exception as e:
            result["success"] = False
            result["message"] = f"录入失败：{str(e)}"
            logger.error(f"成绩录入失败：{e}", exc_info=True)

        return result

    def batch_entry_scores(self, scores: List[Dict]) -> Dict:
        """
        批量录入成绩

        Args:
            scores: 成绩列表 [
                {
                    "student_id": 1001,
                    "exam_name": "练习 1",
                    "exam_date": "2024-01-15",
                    "score": 85,
                    "wrong_questions": [...]
                }
            ]

        Returns:
            批量录入结果
        """
        result = {
            "total": len(scores),
            "success_count": 0,
            "fail_count": 0,
            "total_errors": 0,
            "details": []
        }

        for score_data in scores:
            entry_result = self.entry_score(
                student_id=score_data["student_id"],
                exam_name=score_data["exam_name"],
                exam_date=score_data["exam_date"],
                score=score_data["score"],
                wrong_questions=score_data.get("wrong_questions", [])
            )

            if entry_result["success"]:
                result["success_count"] += 1
                result["total_errors"] += entry_result["error_count"]
            else:
                result["fail_count"] += 1

            result["details"].append(entry_result)

        return result

    def get_student_list(self) -> List[Dict]:
        """获取学生列表"""
        students = StudentDAO.get_all_students()
        return [{"id": s["student_id"], "name": s["name"], "grade": s["grade"]} for s in students]

    def get_common_error_types(self) -> List[str]:
        """获取常见错误类型"""
        return [
            "计算粗心",
            "概念不清",
            "知识性错误",
            "审题不清",
            "公式记错",
            "理解偏差",
            "步骤不全",
            "其他"
        ]

    def entry_class_scores(self, exam_name: str, exam_date: str,
                           student_scores: Dict[int, float],
                           wrong_questions_map: Dict[int, List[Dict]]) -> Dict:
        """
        按学号批量录入全班成绩

        Args:
            exam_name: 考试名称
            exam_date: 考试日期
            student_scores: 学号 - 成绩字典 {学号：分数}
            wrong_questions_map: 学号 - 错题列表字典 {学号：[{...}]}, 可选

        Returns:
            批量录入结果
        """
        result = {
            "total": len(student_scores),
            "success_count": 0,
            "fail_count": 0,
            "total_errors": 0,
            "details": []
        }

        for student_id, score in student_scores.items():
            wrong_qs = wrong_questions_map.get(student_id, [])
            entry_result = self.entry_score(
                student_id=student_id,
                exam_name=exam_name,
                exam_date=exam_date,
                score=score,
                wrong_questions=wrong_qs
            )

            if entry_result["success"]:
                result["success_count"] += 1
                result["total_errors"] += entry_result["error_count"]
            else:
                result["fail_count"] += 1

            result["details"].append(entry_result)

        return result


def main():
    """测试"""
    service = ScoreEntryService()

    # 测试获取最近日期
    dates = service.get_recent_dates()
    print(f"最近 7 天日期：{dates}")

    # 测试获取考试名称
    exams = service.get_recent_exams()
    print(f"常见考试名称：{exams[:5]}")

    # 测试获取学生列表
    students = service.get_student_list()
    print(f"学生列表：{students}")

    # 测试获取错误类型
    error_types = service.get_common_error_types()
    print(f"错误类型：{error_types}")


if __name__ == "__main__":
    main()
