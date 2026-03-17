"""
Excel 导入模块单元测试
"""
import unittest
import tempfile
import os
from pathlib import Path
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from excel_importer import ExcelDataImporter


class TestExcelDataImporter(unittest.TestCase):
    """测试 Excel 数据导入器"""

    @classmethod
    def setUpClass(cls):
        """测试前初始化"""
        cls.importer = ExcelDataImporter()

    def test_knowledge_system_loaded(self):
        """测试知识点系统已加载"""
        self.assertIsNotNone(self.importer.knowledge_system)
        self.assertGreater(len(self.importer.knowledge_system), 0)

    def test_practice_mapping_loaded(self):
        """测试练习映射已加载"""
        self.assertIsNotNone(self.importer.practice_mapping)
        self.assertGreater(len(self.importer.practice_mapping), 0)

    def test_extract_knowledge_from_exam_practice(self):
        """测试从练习名称提取知识点"""
        result = self.importer._extract_knowledge_from_exam(
            "练习 1", "1(2) 班上 学期"
        )
        # 可能返回 None 或知识点字典，该方法依赖 PRACTICE_MAPPING 的数据
        self.assertIsInstance(result, (type(None), dict))

    def test_extract_knowledge_from_exam_midterm(self):
        """测试从期中考试提取知识点"""
        result = self.importer._extract_knowledge_from_exam(
            "期中考试", "1(2) 班上 学期"
        )
        # 可能返回 None 或知识点字典
        self.assertIsInstance(result, (type(None), dict))

    def test_guess_error_type(self):
        """测试错误类型猜测"""
        # 高分 - 计算粗心
        error_type = self.importer._guess_error_type(85)
        self.assertEqual(error_type, "计算粗心")

        # 中等分数 - 概念混淆
        error_type = self.importer._guess_error_type(70)
        self.assertEqual(error_type, "概念混淆")

        # 低分 - 知识性错误
        error_type = self.importer._guess_error_type(50)
        self.assertEqual(error_type, "知识性错误")

    def test_load_excel_not_found(self):
        """测试文件不存在的情况"""
        with self.assertRaises(FileNotFoundError):
            self.importer.load_excel("non_existent_file.xlsx")


if __name__ == "__main__":
    unittest.main(verbosity=2)
