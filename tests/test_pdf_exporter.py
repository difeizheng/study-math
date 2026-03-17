"""
PDF 导出模块单元测试
"""
import unittest
import os
import tempfile
from pathlib import Path
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_exporter import PDFExporter


class TestPDFExporter(unittest.TestCase):
    """测试 PDF 导出器"""

    @classmethod
    def setUpClass(cls):
        """测试前初始化"""
        cls.exporter = PDFExporter()
        cls.test_output_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        """测试后清理"""
        # 清理测试文件
        import shutil
        try:
            shutil.rmtree(cls.test_output_dir)
        except:
            pass

    def test_export_error_report(self):
        """测试导出错题报告"""
        test_records = [
            {
                'exam_name': '练习 1',
                'exam_date': '2024-01-15',
                'knowledge_name': '数的认识',
                'error_type': '计算粗心',
                'score': 75,
                'error_description': '计算时看错数字'
            },
            {
                'exam_name': '练习 2',
                'exam_date': '2024-01-20',
                'knowledge_name': '加减法运算',
                'error_type': '概念不清',
                'score': 68,
                'error_description': '进位加法错误'
            }
        ]

        output_path = os.path.join(self.test_output_dir, "test_error_report.pdf")
        result_path = self.exporter.export_error_report("张三", 1001, test_records, output_path)

        self.assertTrue(os.path.exists(result_path))
        self.assertGreater(os.path.getsize(result_path), 0)

    def test_export_ability_report(self):
        """测试导出能力报告"""
        test_ability = {
            'abilities': {
                '数感': {'score': 85, 'level': '优秀', 'description': '对数的理解和运用'},
                '符号意识': {'score': 78, 'level': '良好', 'description': '符号运用能力'},
                '空间观念': {'score': 72, 'level': '良好', 'description': '空间想象能力'},
                '数据分析观念': {'score': 80, 'level': '良好', 'description': '数据处理能力'},
                '推理能力': {'score': 75, 'level': '良好', 'description': '逻辑推理能力'},
            },
            'strongest': {'name': '数感', 'score': 85},
            'weakest': {'name': '空间观念', 'score': 72},
            'suggestions': ['继续保持数感优势', '加强空间观念训练']
        }

        output_path = os.path.join(self.test_output_dir, "test_ability_report.pdf")
        result_path = self.exporter.export_ability_report("李四", 1002, test_ability, output_path)

        self.assertTrue(os.path.exists(result_path))
        self.assertGreater(os.path.getsize(result_path), 0)

    def test_export_summary_report(self):
        """测试导出综合报告"""
        output_path = os.path.join(self.test_output_dir, "test_summary_report.pdf")
        result_path = self.exporter.export_summary_report(
            "王五", 1003,
            error_count=15,
            ability_level="良好",
            habit_score=82.5,
            output_path=output_path
        )

        self.assertTrue(os.path.exists(result_path))
        self.assertGreater(os.path.getsize(result_path), 0)

    def test_generate_error_suggestions(self):
        """测试错误建议生成"""
        test_records = [
            {'error_type': '计算粗心', 'knowledge_name': '加法'},
            {'error_type': '计算粗心', 'knowledge_name': '减法'},
            {'error_type': '概念不清', 'knowledge_name': '乘法'}
        ]

        suggestions = self.exporter._generate_error_suggestions(test_records)

        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

    def test_get_error_evaluation(self):
        """测试错题数量评价"""
        self.assertEqual(self.exporter._get_error_evaluation(0), "优秀")
        self.assertEqual(self.exporter._get_error_evaluation(5), "良好")
        self.assertEqual(self.exporter._get_error_evaluation(20), "需关注")
        self.assertEqual(self.exporter._get_error_evaluation(50), "需加强")

    def test_get_habit_evaluation(self):
        """测试学习习惯评价"""
        self.assertEqual(self.exporter._get_habit_evaluation(95), "习惯优秀")
        self.assertEqual(self.exporter._get_habit_evaluation(80), "习惯良好")
        self.assertEqual(self.exporter._get_habit_evaluation(65), "习惯一般")
        self.assertEqual(self.exporter._get_habit_evaluation(50), "需改善习惯")


if __name__ == "__main__":
    unittest.main(verbosity=2)
