"""
智能组卷模块单元测试
"""
import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from paper_generator import SmartPaperGenerator, QUESTION_TEMPLATES, PAPER_STRUCTURES


class TestSmartPaperGenerator(unittest.TestCase):
    """测试智能组卷生成器"""

    @classmethod
    def setUpClass(cls):
        """测试前初始化"""
        cls.generator = SmartPaperGenerator()

    def test_question_templates_coverage(self):
        """测试题目模板覆盖率"""
        # 检查是否有足够的知识点模板
        self.assertGreater(len(QUESTION_TEMPLATES), 30)

        # 检查每个知识点至少有 2 道题目
        for kp_code, templates in QUESTION_TEMPLATES.items():
            self.assertGreaterEqual(
                len(templates), 2,
                f"知识点 {kp_code} 的题目数量不足 2 道"
            )

    def test_paper_structures(self):
        """测试试卷结构配置"""
        # 检查是否有足够的试卷类型
        self.assertGreater(len(PAPER_STRUCTURES), 5)

        # 检查每种试卷类型的必要字段
        required_fields = ["total_score", "duration", "type_distribution"]
        for paper_type, structure in PAPER_STRUCTURES.items():
            for field in required_fields:
                self.assertIn(
                    field, structure,
                    f"试卷类型 {paper_type} 缺少字段 {field}"
                )

    def test_generate_paper(self):
        """测试生成试卷"""
        weak_points = [
            {"knowledge_code": "G2U04", "knowledge_name": "表内乘法（一）", "error_count": 3},
            {"knowledge_code": "G2D02", "knowledge_name": "表内除法（一）", "error_count": 2},
        ]

        paper = self.generator.generate_paper(1001, "张三", weak_points, "专项突破")

        self.assertIsNotNone(paper)
        self.assertEqual(paper.student_name, "张三")
        self.assertEqual(paper.student_id, 1001)
        self.assertGreater(len(paper.questions), 0)
        self.assertGreater(paper.total_score, 0)

    def test_generate_paper_empty(self):
        """测试生成空试卷（无薄弱知识点）"""
        paper = self.generator.generate_paper(1002, "李四", [], "基础练习")

        self.assertIsNotNone(paper)
        self.assertEqual(paper.student_name, "李四")
        self.assertEqual(len(paper.questions), 0)

    def test_export_paper_markdown(self):
        """测试导出 Markdown 格式试卷"""
        weak_points = [
            {"knowledge_code": "G1U03", "knowledge_name": "1-5 的认识和加减法", "error_count": 2},
        ]

        paper = self.generator.generate_paper(1003, "王五", weak_points, "基础练习")
        md_content = self.generator.export_paper_word(paper, export_format="markdown")

        self.assertIn("王五的基础练习练习卷", md_content)
        self.assertIn("生成时间", md_content)
        self.assertIn("参考答案", md_content)

    def test_export_paper_text(self):
        """测试导出纯文本格式试卷"""
        weak_points = [
            {"knowledge_code": "G1U03", "knowledge_name": "1-5 的认识和加减法", "error_count": 2},
        ]

        paper = self.generator.generate_paper(1004, "赵六", weak_points, "基础练习")
        text_content = self.generator.export_paper_word(paper, export_format="text")

        self.assertIn("赵六的基础练习练习卷", text_content)
        self.assertIn("生成时间", text_content)

    def test_export_answer_sheet(self):
        """测试导出答题卡"""
        answer_sheet = self.generator.export_answer_sheet(None)

        self.assertIn("答题卡", answer_sheet)
        self.assertIn("姓名", answer_sheet)
        self.assertIn("学号", answer_sheet)

    def test_get_recommendation(self):
        """测试生成练习建议"""
        weak_points = [
            {"knowledge_code": "G2U04", "knowledge_name": "表内乘法（一）", "error_count": 3},
        ]

        paper = self.generator.generate_paper(1005, "孙七", weak_points, "专项突破")
        recommendation = self.generator.get_recommendation(paper)

        self.assertIn("练习建议", recommendation)
        self.assertIn("建议用时", recommendation)

    def test_get_recommendation_empty(self):
        """测试空试卷的建议"""
        paper = self.generator.generate_paper(1006, "周八", [], "基础练习")
        recommendation = self.generator.get_recommendation(paper)

        self.assertIn("暂无题目", recommendation)


class TestQuestionTypes(unittest.TestCase):
    """测试题型多样性"""

    def test_question_types_variety(self):
        """测试题型种类"""
        all_types = set()
        for templates in QUESTION_TEMPLATES.values():
            for template in templates:
                all_types.add(template["type"])

        # 至少包含 5 种题型
        self.assertGreaterEqual(len(all_types), 5)

        # 检查常见题型是否存在
        expected_types = {"计算题", "填空题", "应用题"}
        for qtype in expected_types:
            self.assertIn(qtype, all_types, f"缺少题型：{qtype}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
