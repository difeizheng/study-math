"""
数据库模块单元测试
"""
import unittest
import sqlite3
import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import (
    get_db_connection,
    StudentDAO, ErrorRecordDAO, HabitAnalysisDAO, AbilityRecordDAO
)


class TestStudentDAO(unittest.TestCase):
    """测试学生数据访问对象"""

    def test_add_and_get_student(self):
        """测试添加和获取学生"""
        import time
        student_id = 9999000 + int(time.time() % 10000)  # 生成唯一 ID
        name = "测试学生"
        grade = "1 年级"
        semester = "上"

        # 添加学生
        result = StudentDAO.add_student(student_id, name, grade, semester)
        self.assertTrue(result)

        # 查询学生
        student = StudentDAO.get_student(student_id)
        self.assertIsNotNone(student)
        self.assertEqual(student["name"], name)
        self.assertEqual(student["grade"], grade)

    def test_get_all_students(self):
        """测试获取所有学生"""
        students = StudentDAO.get_all_students()
        self.assertIsInstance(students, list)
        self.assertGreater(len(students), 0)

    def test_delete_student(self):
        """测试删除学生"""
        import time
        student_id = 8888000 + int(time.time() % 10000)
        StudentDAO.add_student(student_id, "删除测试", "1 年级", "上")

        # 删除学生
        result = StudentDAO.delete_student(student_id)
        self.assertTrue(result)

        # 验证已删除
        student = StudentDAO.get_student(student_id)
        self.assertIsNone(student)


class TestErrorRecordDAO(unittest.TestCase):
    """测试错题记录数据访问对象"""

    def test_add_error_record(self):
        """测试添加错题记录"""
        import time
        student_id = 10011000 + int(time.time() % 10000)

        # 先添加学生
        StudentDAO.add_student(student_id, "错题测试学生", "1 年级", "上")

        record_id = ErrorRecordDAO.add_error_record(
            student_id=student_id,
            exam_name="练习 1",
            exam_date="2024-01-15",
            knowledge_code="G1U03",
            knowledge_name="1-5 的认识和加减法",
            error_type="计算粗心",
            error_description="测试错题",
            score=75.0
        )
        self.assertTrue(record_id > 0)

    def test_get_errors_by_student(self):
        """测试按学生获取错题"""
        import time
        student_id = 10012000 + int(time.time() % 10000)

        # 先添加学生和错题
        StudentDAO.add_student(student_id, "错题测试学生 2", "1 年级", "上")
        ErrorRecordDAO.add_error_record(
            student_id=student_id,
            exam_name="练习 1",
            exam_date="2024-01-15",
            knowledge_code="G1U03",
            knowledge_name="1-5 的认识和加减法",
            error_type="计算粗心",
            error_description="测试错题",
            score=75.0
        )

        errors = ErrorRecordDAO.get_errors_by_student(student_id)
        self.assertIsInstance(errors, list)
        self.assertGreater(len(errors), 0)

    def test_get_errors_by_knowledge(self):
        """测试按知识点获取错题"""
        import time
        student_id = 10013000 + int(time.time() % 10000)

        StudentDAO.add_student(student_id, "错题测试学生 3", "1 年级", "上")
        ErrorRecordDAO.add_error_record(
            student_id=student_id,
            exam_name="练习 1",
            exam_date="2024-01-15",
            knowledge_code="G1U03",
            knowledge_name="1-5 的认识和加减法",
            error_type="计算粗心",
            error_description="测试错题",
            score=75.0
        )

        errors = ErrorRecordDAO.get_errors_by_knowledge(student_id, "G1U03")
        self.assertIsInstance(errors, list)


class TestHabitAnalysisDAO(unittest.TestCase):
    """测试学习习惯分析数据访问对象"""

    def test_save_and_get_analysis(self):
        """测试保存和获取习惯分析"""
        import time
        student_id = 10021000 + int(time.time() % 10000)

        # 先添加学生
        StudentDAO.add_student(student_id, "习惯测试学生", "2 年级", "上")

        habit_scores = {
            "学习时间管理": 80.0,
            "错题整理习惯": 75.0,
            "审题习惯": 70.0,
            "计算规范": 85.0,
            "专注力": 90.0
        }

        record_id = HabitAnalysisDAO.save_analysis(
            student_id=student_id,
            analysis_date="2024-01-15",
            error_distribution={"加法": 5, "减法": 3},
            habit_scores=habit_scores,
            main_issues=["审题不仔细"],
            suggestions=["建议加强审题训练"],
            trends={"学习时间管理": [75.0, 78.0, 80.0]}
        )
        self.assertTrue(record_id > 0)

        # 获取最新分析
        analysis = HabitAnalysisDAO.get_latest_analysis(student_id)
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis["student_id"], student_id)


class TestAbilityRecordDAO(unittest.TestCase):
    """测试能力档案数据访问对象"""

    def test_save_and_get_record(self):
        """测试保存和获取能力记录"""
        import time
        student_id = 10031000 + int(time.time() % 10000)

        # 先添加学生
        StudentDAO.add_student(student_id, "能力测试学生", "3 年级", "上")

        ability_scores = {
            "数感": 85.0,
            "符号意识": 78.0,
            "空间观念": 72.0,
            "数据分析观念": 80.0,
            "推理能力": 75.0
        }

        record_id = AbilityRecordDAO.save_record(
            student_id=student_id,
            analysis_date="2024-01-15",
            ability_scores=ability_scores,
            overall_level="良好",
            strongest_ability="数感",
            weakest_ability="空间观念",
            radar_data=[{"ability": "数感", "score": 85}],
            report_content="测试报告"
        )
        self.assertTrue(record_id > 0)

        # 获取最新记录
        record = AbilityRecordDAO.get_latest_record(student_id)
        self.assertIsNotNone(record)
        self.assertEqual(record["student_id"], student_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
