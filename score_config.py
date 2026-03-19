"""
分数段配置管理模块
"""
import json
from pathlib import Path
from typing import Dict, List, Optional


# 默认分数段配置
DEFAULT_SCORE_RANGES = [
    {"name": "90-100 分 (优秀)", "min": 90, "max": 100},
    {"name": "80-89 分 (良好)", "min": 80, "max": 89},
    {"name": "70-79 分 (中等)", "min": 70, "max": 79},
    {"name": "60-69 分 (及格)", "min": 60, "max": 69},
    {"name": "60 分以下 (待提高)", "min": 0, "max": 59},
]

CONFIG_FILE_PATH = Path("data/settings.json")


def load_score_ranges() -> List[Dict]:
    """
    加载分数段配置

    Returns:
        分数段配置列表
    """
    if not CONFIG_FILE_PATH.exists():
        return DEFAULT_SCORE_RANGES.copy()

    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            ranges = config.get('score_ranges', DEFAULT_SCORE_RANGES)
            return ranges if ranges else DEFAULT_SCORE_RANGES.copy()
    except (json.JSONDecodeError, IOError):
        return DEFAULT_SCORE_RANGES.copy()


def save_score_ranges(ranges: List[Dict]) -> bool:
    """
    保存分数段配置

    Args:
        ranges: 分数段配置列表

    Returns:
        是否保存成功
    """
    try:
        # 确保 data 目录存在
        CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # 加载现有配置
        if CONFIG_FILE_PATH.exists():
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}

        # 更新分数段配置
        config['score_ranges'] = ranges

        # 保存配置
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return True
    except (IOError, json.JSONEncodeError) as e:
        print(f"保存配置失败：{e}")
        return False


def reset_to_default() -> bool:
    """
    恢复默认分数段配置

    Returns:
        是否成功
    """
    return save_score_ranges(DEFAULT_SCORE_RANGES.copy())


def get_score_distribution_for_scores(scores: List[float]) -> Dict[str, int]:
    """
    根据配置的分数段计算分数分布

    Args:
        scores: 成绩列表

    Returns:
        分数段分布字典 {分数段名称：次数}
    """
    ranges = load_score_ranges()
    distribution = {r['name']: 0 for r in ranges}

    for score in scores:
        for r in ranges:
            if r['min'] <= score <= r['max']:
                distribution[r['name']] += 1
                break  # 分数段可能重叠，只计入第一个匹配的

    return distribution
