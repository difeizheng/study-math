"""
分数段配置模块测试
"""
import unittest
import sys
import json
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from score_config import (
    load_score_ranges,
    save_score_ranges,
    reset_to_default,
    get_score_distribution_for_scores,
    DEFAULT_SCORE_RANGES
)


class TestScoreConfig(unittest.TestCase):
    """测试分数段配置功能"""

    def test_load_score_ranges(self):
        """测试加载分数段配置"""
        ranges = load_score_ranges()

        self.assertIsInstance(ranges, list)
        self.assertGreater(len(ranges), 0)

        # 验证配置结构
        for r in ranges:
            self.assertIn("name", r)
            self.assertIn("min", r)
            self.assertIn("max", r)

    def test_default_score_ranges(self):
        """测试默认分数段配置"""
        self.assertIsInstance(DEFAULT_SCORE_RANGES, list)
        self.assertGreater(len(DEFAULT_SCORE_RANGES), 0)

        # 验证默认配置包含 5 个分数段
        self.assertEqual(len(DEFAULT_SCORE_RANGES), 5)

        # 验证优秀分数段
        excellent = DEFAULT_SCORE_RANGES[0]
        self.assertEqual(excellent["min"], 90)
        self.assertEqual(excellent["max"], 100)
        self.assertIn("优秀", excellent["name"])

        # 验证待提高分数段
        low = DEFAULT_SCORE_RANGES[-1]
        self.assertEqual(low["min"], 0)
        self.assertEqual(low["max"], 59)
        self.assertIn("待提高", low["name"])

    def test_get_score_distribution_for_scores(self):
        """测试分数分布计算"""
        # 准备测试数据
        scores = [95, 88, 76, 65, 55, 92, 85, 78, 62, 48]

        # 使用默认配置计算分布
        distribution = get_score_distribution_for_scores(scores)

        self.assertIsInstance(distribution, dict)

        # 验证总人数匹配
        total = sum(distribution.values())
        self.assertEqual(total, len(scores))

    def test_get_score_distribution_empty(self):
        """测试空数据的分数分布"""
        scores = []
        distribution = get_score_distribution_for_scores(scores)

        self.assertIsInstance(distribution, dict)

        # 验证所有计数为 0
        for count in distribution.values():
            self.assertEqual(count, 0)

    def test_get_score_distribution_boundary(self):
        """测试边界分数的分布"""
        # 测试边界值
        scores = [90, 80, 70, 60, 59]

        distribution = get_score_distribution_for_scores(scores)

        # 验证 90 分属于优秀段
        excellent_key = next(k for k in distribution.keys() if "优秀" in k)
        self.assertEqual(distribution[excellent_key], 1)

        # 验证 59 分属于待提高段
        low_key = next(k for k in distribution.keys() if "待提高" in k)
        self.assertEqual(distribution[low_key], 1)


class TestScoreConfigSaveLoad(unittest.TestCase):
    """测试分数段配置的保存和加载"""

    def test_save_and_load_score_ranges(self):
        """测试保存和加载配置"""
        # 自定义配置
        custom_ranges = [
            {"name": "90-100 分", "min": 90, "max": 100},
            {"name": "70-89 分", "min": 70, "max": 89},
            {"name": "0-69 分", "min": 0, "max": 69},
        ]

        # 保存配置
        result = save_score_ranges(custom_ranges)
        self.assertTrue(result)

        # 加载配置
        loaded = load_score_ranges()
        self.assertEqual(len(loaded), len(custom_ranges))

        # 恢复默认配置
        result = reset_to_default()
        self.assertTrue(result)

        # 验证已恢复默认
        default = load_score_ranges()
        self.assertEqual(len(default), len(DEFAULT_SCORE_RANGES))


if __name__ == "__main__":
    unittest.main()
