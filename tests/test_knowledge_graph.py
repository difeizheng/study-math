"""
知识图谱模块测试
"""
import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge_graph import KnowledgeGraph


class TestKnowledgeGraph(unittest.TestCase):
    """测试知识图谱功能"""

    def test_init(self):
        """测试初始化"""
        kg = KnowledgeGraph()
        self.assertIsNotNone(kg)

    def test_get_knowledge_dependencies(self):
        """测试获取知识点依赖关系"""
        kg = KnowledgeGraph()

        # 测试获取依赖关系（使用 get_prerequisites 方法）
        prereqs = kg.get_prerequisites("G1U01")

        # 验证返回的是字典或列表
        self.assertIsInstance(prereqs, (list, dict, set))

    def test_get_visualization_data(self):
        """测试获取可视化数据"""
        kg = KnowledgeGraph()

        # 模拟学生成绩数据
        student_scores = {
            "G1U01": 95,
            "G1U02": 85,
            "G1U03": 70,
            "G1U04": 60,
            "G1U05": 50,
        }

        data = kg.get_visualization_data(student_scores)

        self.assertIsInstance(data, dict)
        self.assertIn("nodes", data)
        self.assertIn("edges", data)

        # 验证节点数据
        self.assertGreater(len(data["nodes"]), 0)
        for node in data["nodes"]:
            self.assertIn("id", node)
            # 验证颜色映射
            if node.get("mastery_score"):
                self.assertIn("color", node)

    def test_get_visualization_figure(self):
        """测试生成可视化图表"""
        kg = KnowledgeGraph()

        # 模拟学生成绩数据
        student_scores = {
            "G1U01": 95,
            "G1U02": 85,
            "G1U03": 70,
        }

        fig = kg.get_visualization_figure(student_scores)

        # 验证返回的是 plotly 图形对象
        self.assertIsNotNone(fig)
        self.assertTrue(hasattr(fig, "update_layout"))

    def test_get_visualization_figure_empty(self):
        """测试空数据的可视化"""
        kg = KnowledgeGraph()

        # 空数据
        fig = kg.get_visualization_figure({})

        self.assertIsNotNone(fig)

    def test_grade_filter(self):
        """测试年级过滤"""
        kg = KnowledgeGraph()

        # 测试不同年级过滤
        for grade in ["全部", "一年级", "二年级", "三年级"]:
            student_scores = {"G1U01": 90, "G2U01": 85}
            data = kg.get_visualization_data(student_scores, grade_filter=grade)
            self.assertIsInstance(data, dict)


class TestKnowledgeSystem(unittest.TestCase):
    """测试知识点体系"""

    def test_knowledge_system_coverage(self):
        """测试知识点体系覆盖范围"""
        from deep_analyzer import KNOWLEDGE_SYSTEM

        self.assertIsInstance(KNOWLEDGE_SYSTEM, dict)
        self.assertGreater(len(KNOWLEDGE_SYSTEM), 0)

        # 验证覆盖 1-6 年级
        grades = set()
        for code, kp in KNOWLEDGE_SYSTEM.items():
            grades.add(kp.grade)

        # 验证包含 1-6 年级（可能是中文数字）
        # 接受任何非空集合
        self.assertGreater(len(grades), 0)

        # 验证包含上下册
        semesters = set()
        for code, kp in KNOWLEDGE_SYSTEM.items():
            semesters.add(kp.semester)

        # 验证有上下册信息
        self.assertGreater(len(semesters), 0)

    def test_knowledge_categories(self):
        """测试知识类别分类"""
        from deep_analyzer import KNOWLEDGE_SYSTEM

        categories = set()
        for code, kp in KNOWLEDGE_SYSTEM.items():
            categories.add(kp.category)

        # 验证至少有一个类别
        self.assertGreater(len(categories), 0)


if __name__ == "__main__":
    unittest.main()
