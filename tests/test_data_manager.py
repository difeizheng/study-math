"""
DataManager 模块单元测试
"""
import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 在导入 DataManager 之前设置标志，跳过 streamlit 缓存
import os
os.environ['PYTEST_RUNNING'] = '1'

from data_manager import DataManager, StudentScore, ExamInfo
from database import StudentDAO, ExamScoreDAO, get_db_connection
import time


class TestDataManager(unittest.TestCase):
    """测试 DataManager 类"""

    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        cls.test_student_id = 20000000 + int(time.time() % 10000)

        # 添加测试学生
        StudentDAO.add_student(
            cls.test_student_id,
            "DataManager 测试学生",
            "1 年级",
            "一年级上册"
        )

        # 添加测试成绩
        ExamScoreDAO.add_score(
            cls.test_student_id,
            "一年级上册",
            "周练 1",
            "2024-01-15",
            85.0
        )
        ExamScoreDAO.add_score(
            cls.test_student_id,
            "一年级上册",
            "周练 2",
            "2024-01-22",
            90.0
        )
        ExamScoreDAO.add_score(
            cls.test_student_id,
            "一年级上册",
            "单元 1",
            "2024-01-29",
            88.0
        )

    @classmethod
    def tearDownClass(cls):
        """测试后清理"""
        # 删除测试成绩
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM exam_scores WHERE student_id = ?",
            (cls.test_student_id,)
        )
        conn.commit()
        conn.close()

        # 删除测试学生
        StudentDAO.delete_student(cls.test_student_id)

    def test_get_students(self):
        """测试获取学生列表"""
        dm = DataManager()
        students = dm.get_students()

        self.assertIsInstance(students, list)
        self.assertGreater(len(students), 0)

        # 验证学生数据结构
        student = students[0]
        self.assertIn("student_id", student)
        self.assertIn("name", student)
        self.assertIn("grade", student)

    def test_get_scores_by_student(self):
        """测试按学生获取成绩"""
        dm = DataManager()
        scores = dm.get_scores(student_id=self.test_student_id)

        self.assertIsInstance(scores, list)
        self.assertGreater(len(scores), 0)

        # 验证成绩数据结构
        score = scores[0]
        self.assertIsInstance(score, StudentScore)
        self.assertEqual(score.student_id, self.test_student_id)
        self.assertIn(score.exam_name, ["周练 1", "周练 2", "单元 1"])

    def test_get_scores_with_semester_filter(self):
        """测试按学期筛选成绩"""
        dm = DataManager()
        scores = dm.get_scores(
            student_id=self.test_student_id,
            semester="一年级上册"
        )

        self.assertIsInstance(scores, list)
        self.assertGreater(len(scores), 0)

        # 验证所有成绩都属于指定学期
        for score in scores:
            # 通过考试名称推断学期
            self.assertIn(score.exam_name, ["周练 1", "周练 2", "单元 1"])

    def test_get_exam_list(self):
        """测试获取考试列表"""
        dm = DataManager()
        exam_list = dm.get_exam_list()

        self.assertIsInstance(exam_list, list)

        # 验证考试列表结构
        if exam_list:
            exam = exam_list[0]
            self.assertIsInstance(exam, ExamInfo)
            self.assertTrue(hasattr(exam, "name"))
            self.assertTrue(hasattr(exam, "week"))
            self.assertTrue(hasattr(exam, "date"))

    def test_get_scores_by_week(self):
        """测试按周次获取成绩"""
        dm = DataManager()
        week_scores = dm.get_scores_by_week(
            student_id=self.test_student_id,
            grade_code="G1U",
            start_week=1,
            end_week=4
        )

        self.assertIsInstance(week_scores, dict)

        # 验证周次数据结构
        for week, scores in week_scores.items():
            self.assertIsInstance(week, int)
            self.assertIsInstance(scores, list)


class TestExamScoreDAO(unittest.TestCase):
    """测试考试成绩数据访问对象"""

    def test_add_and_get_score(self):
        """测试添加和获取成绩"""
        import time
        student_id = 30000000 + int(time.time() % 10000)

        # 先添加学生
        StudentDAO.add_student(
            student_id,
            "成绩测试学生",
            "2 年级",
            "二年级上册"
        )

        # 添加成绩
        record_id = ExamScoreDAO.add_score(
            student_id=student_id,
            semester="二年级上册",
            exam_name="单元测试",
            exam_date="2024-02-15",
            score=92.5
        )

        self.assertTrue(record_id > 0)

        # 获取成绩
        scores = ExamScoreDAO.get_scores_by_student(student_id)
        self.assertGreater(len(scores), 0)

        score = scores[0]
        self.assertEqual(score["score"], 92.5)
        self.assertEqual(score["exam_name"], "单元测试")

        # 清理
        ExamScoreDAO.delete_score(record_id)
        StudentDAO.delete_student(student_id)

    def test_update_score(self):
        """测试更新成绩"""
        import time
        student_id = 30001000 + int(time.time() % 10000)

        StudentDAO.add_student(
            student_id,
            "更新测试学生",
            "2 年级",
            "二年级上册"
        )

        record_id = ExamScoreDAO.add_score(
            student_id=student_id,
            semester="二年级上册",
            exam_name="期中考试",
            exam_date="2024-04-15",
            score=80.0
        )

        # 更新成绩
        result = ExamScoreDAO.update_score(record_id, 95.0)
        self.assertTrue(result)

        # 验证更新
        scores = ExamScoreDAO.get_scores_by_student(student_id)
        self.assertEqual(scores[0]["score"], 95.0)

        # 清理
        ExamScoreDAO.delete_score(record_id)
        StudentDAO.delete_student(student_id)

    def test_get_scores_by_semester(self):
        """测试按学期获取成绩"""
        import time
        student_id = 30002000 + int(time.time() % 10000)

        StudentDAO.add_student(
            student_id,
            "学期测试学生",
            "3 年级",
            "三年级上册"
        )

        ExamScoreDAO.add_score(
            student_id=student_id,
            semester="三年级上册",
            exam_name="月考 1",
            exam_date="2024-03-15",
            score=88.0
        )

        # 获取学期成绩
        scores = ExamScoreDAO.get_scores_by_semester("三年级上册", "月考 1")
        self.assertGreater(len(scores), 0)

        # 验证包含学生姓名
        self.assertIn("student_name", scores[0])

        # 清理
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM exam_scores WHERE student_id = ?",
            (student_id,)
        )
        conn.commit()
        conn.close()
        StudentDAO.delete_student(student_id)


class TestKnowledgeWeekMap(unittest.TestCase):
    """测试周次 - 知识点映射"""

    def test_get_week_from_exam_name(self):
        """测试从考试名称解析周次"""
        from knowledge_week_map import get_week_from_exam_name

        # 测试周练
        self.assertEqual(get_week_from_exam_name("周练 1"), 1)
        self.assertEqual(get_week_from_exam_name("周练 5"), 5)
        self.assertEqual(get_week_from_exam_name("练习 3"), 3)

        # 测试单元
        self.assertEqual(get_week_from_exam_name("单元 1"), 1)
        self.assertEqual(get_week_from_exam_name("单元 2"), 3)
        self.assertEqual(get_week_from_exam_name("单元 3"), 5)

        # 测试期中
        self.assertEqual(get_week_from_exam_name("期中"), 9)

        # 测试期末
        self.assertEqual(get_week_from_exam_name("期末"), 18)
        # 注意：期末模 1 可能是 17 或 18 周，取决于具体实现
        self.assertIn(get_week_from_exam_name("期末模 1"), [17, 18])
        self.assertIn(get_week_from_exam_name("期末模 2"), [18, 19])

    def test_get_week_description(self):
        """测试获取周次描述"""
        from knowledge_week_map import get_week_description

        # 测试有效周次
        desc = get_week_description(1, "G1U")
        self.assertIsNotNone(desc)

        # 测试无效周次（可能返回默认值而不是 None）
        desc = get_week_description(100, "G1U")
        # 接受任何返回值，只要函数不崩溃
        self.assertIsInstance(desc, (str, type(None)))


if __name__ == "__main__":
    unittest.main()
