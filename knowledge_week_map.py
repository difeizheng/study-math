"""
人教版小学数学周次 - 知识点映射体系
基于教育部《义务教育数学课程标准》和人教版教材编写
支持 1-6 年级上下册，每学期按 18 周规划
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class WeekRange:
    """周次范围定义"""
    start: int  # 起始周
    end: int  # 结束周
    knowledge_codes: List[str]  # 对应的知识点编码
    description: str  # 学习阶段描述


# 人教版小学数学周次 - 知识点映射表
# 格式：年级学期代码 -> 周次范围 -> 知识点
WEEK_TO_KNOWLEDGE_MAP: Dict[str, Dict[str, WeekRange]] = {
    # ==================== 一年级上册 ====================
    "G1U": {
        "week_1": WeekRange(1, 1, ["G1U01"], "准备课（数一数、比一比）"),
        "week_2": WeekRange(2, 2, ["G1U02"], "位置（上下前后左右）"),
        "week_3-4": WeekRange(3, 4, ["G1U03"], "1-5 的认识和加减法"),
        "week_5": WeekRange(5, 5, ["G1U04"], "认识图形（一）"),
        "week_6-8": WeekRange(6, 8, ["G1U05"], "6-10 的认识和加减法"),
        "week_9": WeekRange(9, 9, [], "期中复习"),
        "week_10-11": WeekRange(10, 11, ["G1U06"], "11-20 各数的认识"),
        "week_12": WeekRange(12, 12, ["G1U07"], "认识钟表"),
        "week_13-15": WeekRange(13, 15, ["G1U08"], "20 以内的进位加法"),
        "week_16-18": WeekRange(16, 18, [], "期末总复习"),
    },

    # ==================== 一年级下册 ====================
    "G1D": {
        "week_1": WeekRange(1, 1, ["G1D01"], "认识图形（二）"),
        "week_2-4": WeekRange(2, 4, ["G1D02"], "20 以内的退位减法"),
        "week_5-7": WeekRange(5, 7, ["G1D03"], "100 以内数的认识"),
        "week_8": WeekRange(8, 8, ["G1D04"], "认识人民币"),
        "week_9": WeekRange(9, 9, [], "期中复习"),
        "week_10-14": WeekRange(10, 14, ["G1D05"], "100 以内的加法和减法"),
        "week_15-18": WeekRange(15, 18, [], "期末总复习"),
    },

    # ==================== 二年级上册 ====================
    "G2U": {
        "week_1-2": WeekRange(1, 2, ["G2U01"], "长度单位（厘米和米）"),
        "week_3-5": WeekRange(3, 5, ["G2U02"], "100 以内的加法和减法（二）"),
        "week_6": WeekRange(6, 6, ["G2U03"], "角的初步认识"),
        "week_7-9": WeekRange(7, 9, ["G2U04"], "表内乘法（一）"),
        "week_9": WeekRange(9, 9, [], "期中复习"),
        "week_10": WeekRange(10, 10, ["G2U05"], "观察物体"),
        "week_11-14": WeekRange(11, 14, ["G2U06"], "表内乘法（二）"),
        "week_15": WeekRange(15, 15, ["G2U07"], "认识时间"),
        "week_16-18": WeekRange(16, 18, [], "期末总复习"),
    },

    # ==================== 二年级下册 ====================
    "G2D": {
        "week_1": WeekRange(1, 1, ["G2D01"], "数据收集整理"),
        "week_2-4": WeekRange(2, 4, ["G2D02"], "表内除法（一）"),
        "week_5": WeekRange(5, 5, ["G2D03"], "图形的运动"),
        "week_6-7": WeekRange(6, 7, ["G2D04"], "表内除法（二）"),
        "week_8": WeekRange(8, 8, [], "期中复习"),
        "week_9": WeekRange(9, 9, ["G2D05"], "混合运算"),
        "week_10-11": WeekRange(10, 11, ["G2D06"], "有余数的除法"),
        "week_12-15": WeekRange(12, 15, ["G2D07"], "万以内数的认识"),
        "week_16-18": WeekRange(16, 18, [], "期末总复习"),
    },

    # ==================== 三年级上册 ====================
    "G3U": {
        "week_1": WeekRange(1, 1, ["G3U01"], "时、分、秒"),
        "week_2-3": WeekRange(2, 3, ["G3U02"], "万以内的加法和减法（一）"),
        "week_4": WeekRange(4, 4, ["G3U03"], "测量"),
        "week_5-7": WeekRange(5, 7, ["G3U04"], "万以内的加法和减法（二）"),
        "week_8": WeekRange(8, 8, [], "期中复习"),
        "week_9": WeekRange(9, 9, ["G3U05"], "倍的认识"),
        "week_10-11": WeekRange(10, 11, ["G3U06"], "多位数乘一位数"),
        "week_12": WeekRange(12, 12, ["G3U07"], "数字编码"),
        "week_13-14": WeekRange(13, 14, ["G3U08"], "长方形和正方形"),
        "week_15": WeekRange(15, 15, ["G3U09"], "分数的初步认识"),
        "week_16-18": WeekRange(16, 18, [], "期末总复习"),
    },

    # ==================== 三年级下册 ====================
    "G3D": {
        "week_1": WeekRange(1, 1, ["G3D01"], "位置与方向（一）"),
        "week_2-3": WeekRange(2, 3, ["G3D02"], "除数是一位数的除法"),
        "week_4": WeekRange(4, 4, [], "复式统计表"),
        "week_5": WeekRange(5, 5, ["G3D03"], "两位数乘两位数"),
        "week_6": WeekRange(6, 6, [], "制作活动日历"),
        "week_7": WeekRange(7, 7, ["G3D04"], "面积"),
        "week_8": WeekRange(8, 8, [], "期中复习"),
        "week_9": WeekRange(9, 9, ["G3D05"], "年、月、日"),
        "week_10": WeekRange(10, 10, [], "我们的校园"),
        "week_11": WeekRange(11, 11, ["G3D06"], "小数的初步认识"),
        "week_12": WeekRange(12, 12, ["G3D07"], "数学广角 - 搭配"),
        "week_13-18": WeekRange(13, 18, [], "期末总复习"),
    },

    # ==================== 四年级上册 ====================
    "G4U": {
        "week_1-2": WeekRange(1, 2, ["G4U01"], "大数的认识"),
        "week_3": WeekRange(3, 3, ["G4U02"], "公顷和平方千米"),
        "week_4-5": WeekRange(4, 5, ["G4U03"], "角的度量"),
        "week_6": WeekRange(6, 6, [], "期中复习"),
        "week_7": WeekRange(7, 7, ["G4U04"], "三位数乘两位数"),
        "week_8": WeekRange(8, 8, ["G4U05"], "平行四边形和梯形"),
        "week_9-10": WeekRange(9, 10, ["G4U06"], "除数是两位数的除法"),
        "week_11": WeekRange(11, 11, ["G4U07"], "统计"),
        "week_12": WeekRange(12, 12, [], "数学广角 - 优化"),
        "week_13-18": WeekRange(13, 18, [], "期末总复习"),
    },

    # ==================== 四年级下册 ====================
    "G4D": {
        "week_1": WeekRange(1, 1, ["G4D01"], "四则运算"),
        "week_2": WeekRange(2, 2, ["G4D02"], "观察物体（二）"),
        "week_3-4": WeekRange(3, 4, ["G4D03"], "运算定律"),
        "week_5": WeekRange(5, 5, [], "期中复习"),
        "week_6": WeekRange(6, 6, ["G4D04"], "小数的意义和性质"),
        "week_7": WeekRange(7, 7, ["G4D05"], "三角形"),
        "week_8-9": WeekRange(8, 9, ["G4D06"], "小数的加法和减法"),
        "week_10": WeekRange(10, 10, ["G4D07"], "图形的运动"),
        "week_11": WeekRange(11, 11, ["G4D08"], "平均数与条形统计图"),
        "week_12": WeekRange(12, 12, [], "数学广角 - 鸡兔同笼"),
        "week_13-18": WeekRange(13, 18, [], "期末总复习"),
    },

    # ==================== 五年级上册 ====================
    "G5U": {
        "week_1-2": WeekRange(1, 2, ["G5U01"], "小数乘法"),
        "week_3": WeekRange(3, 3, ["G5U02"], "位置"),
        "week_4-6": WeekRange(4, 6, ["G5U03"], "小数除法"),
        "week_7": WeekRange(7, 7, [], "期中复习"),
        "week_8": WeekRange(8, 8, ["G5U04"], "可能性"),
        "week_9": WeekRange(9, 9, [], "掷一掷"),
        "week_10-12": WeekRange(10, 12, ["G5U05"], "简易方程"),
        "week_13-14": WeekRange(13, 14, ["G5U06"], "多边形的面积"),
        "week_15": WeekRange(15, 15, ["G5U07"], "因数与倍数"),
        "week_16-18": WeekRange(16, 18, [], "期末总复习"),
    },

    # ==================== 五年级下册 ====================
    "G5D": {
        "week_1": WeekRange(1, 1, ["G5D01"], "观察物体（三）"),
        "week_2-3": WeekRange(2, 3, ["G5D02"], "因数与倍数（二）"),
        "week_4-6": WeekRange(4, 6, ["G5D03"], "长方体和正方体"),
        "week_7": WeekRange(7, 7, [], "期中复习"),
        "week_8-10": WeekRange(8, 10, ["G5D04"], "分数的意义和性质"),
        "week_11": WeekRange(11, 11, ["G5D05"], "分数的加法和减法"),
        "week_12": WeekRange(12, 12, ["G5D06"], "图形的运动（三）"),
        "week_13": WeekRange(13, 13, [], "打电话"),
        "week_14": WeekRange(14, 14, ["G5D07"], "折线统计图"),
        "week_15": WeekRange(15, 15, ["G5D08"], "数学广角 - 找次品"),
        "week_16-18": WeekRange(16, 18, [], "期末总复习"),
    },

    # ==================== 六年级上册 ====================
    "G6U": {
        "week_1-2": WeekRange(1, 2, ["G6U01"], "分数乘法"),
        "week_3": WeekRange(3, 3, ["G6U02"], "位置与方向（二）"),
        "week_4-5": WeekRange(4, 5, ["G6U03"], "分数除法"),
        "week_6": WeekRange(6, 6, [], "期中复习"),
        "week_7": WeekRange(7, 7, ["G6U04"], "比"),
        "week_8-9": WeekRange(8, 9, ["G6U05"], "圆"),
        "week_10": WeekRange(10, 10, [], "确定起跑线"),
        "week_11": WeekRange(11, 11, ["G6U06"], "百分数"),
        "week_12": WeekRange(12, 12, ["G6U07"], "扇形统计图"),
        "week_13": WeekRange(13, 13, [], "数学广角 - 数与形"),
        "week_14-18": WeekRange(14, 18, [], "期末总复习"),
    },

    # ==================== 六年级下册 ====================
    "G6D": {
        "week_1-2": WeekRange(1, 2, ["G6D01"], "负数"),
        "week_3": WeekRange(3, 3, ["G6D02"], "百分数（二）"),
        "week_4-6": WeekRange(4, 6, ["G6D03"], "圆柱与圆锥"),
        "week_7": WeekRange(7, 7, [], "期中复习"),
        "week_8-10": WeekRange(8, 10, ["G6D04"], "比例"),
        "week_11": WeekRange(11, 11, [], "自行车里的数学"),
        "week_12": WeekRange(12, 12, ["G6D05"], "数学广角 - 鸽巢问题"),
        "week_13-18": WeekRange(13, 18, [], "小升初总复习"),
    },
}


def get_week_from_exam_name(exam_name: str) -> int:
    """
    从考试名称中提取周次

    支持的格式:
    - 周练 1, 周练 2, ... -> 第 1 周，第 2 周
    - 第 1 周，第 2 周，... -> 第 1 周，第 2 周
    - 练习 1, 练习 2, ... -> 按顺序映射 (需要额外配置)
    - 期末模 1, 期末模 2 -> 第 16-18 周 (复习周)
    - 期中 -> 第 9 周
    - 期末 -> 第 18 周

    Args:
        exam_name: 考试名称，如"周练 1"、"期末模 2"

    Returns:
        周次数字，无法解析返回 0
    """
    import re

    if not exam_name:
        return 0

    # 周练 N
    match = re.search(r'周练\s*(\d+)', exam_name)
    if match:
        return int(match.group(1))

    # 第 N 周
    match = re.search(r'第\s*(\d+)\s*周', exam_name)
    if match:
        return int(match.group(1))

    # 练习 N (假设练习 1=周练 1)
    match = re.search(r'练习\s*(\d+)', exam_name)
    if match:
        return int(match.group(1))

    # 单元 N (假设每个单元 2 周，单元 1=第 1-2 周)
    match = re.search(r'单元\s*(\d+)', exam_name)
    if match:
        unit_num = int(match.group(1))
        return min(unit_num * 2 - 1, 18)  # 最多 18 周

    # 期末模 N (期末考试模拟，属于复习阶段)
    match = re.search(r'期末 [模|模拟]\s*(\d+)', exam_name)
    if match:
        return 16 + min(int(match.group(1)), 3)  # 第 16-18 周

    # 期中
    if '期中' in exam_name:
        return 9

    # 期末
    if '期末' in exam_name:
        return 18

    return 0


def get_knowledge_by_week(grade_code: str, week: int) -> List[str]:
    """
    根据年级和周次获取对应的知识点编码列表

    Args:
        grade_code: 年级代码，如"G1U"(一年级上册)、"G2D"(二年级下册)
        week: 周次 (1-18)

    Returns:
        知识点编码列表
    """
    if grade_code not in WEEK_TO_KNOWLEDGE_MAP:
        return []

    week_ranges = WEEK_TO_KNOWLEDGE_MAP[grade_code]

    for key, week_range in week_ranges.items():
        if week_range.start <= week <= week_range.end:
            return week_range.knowledge_codes.copy()

    return []


def get_week_description(grade_code: str, week: int) -> str:
    """
    获取指定年级指定周次的学习描述

    Args:
        grade_code: 年级代码
        week: 周次

    Returns:
        学习描述字符串
    """
    if grade_code not in WEEK_TO_KNOWLEDGE_MAP:
        return "未知年级"

    week_ranges = WEEK_TO_KNOWLEDGE_MAP[grade_code]

    for key, week_range in week_ranges.items():
        if week_range.start <= week <= week_range.end:
            return week_range.description

    return "复习或考试时间"


def get_semester_from_code(grade_code: str) -> tuple:
    """
    从年级代码解析年级和学期

    Args:
        grade_code: 年级代码，如"G1U"、"G2D"

    Returns:
        (年级数字，学期) 元组，如 (1, "上")
    """
    if len(grade_code) >= 3:
        grade = int(grade_code[1])
        semester = "上" if grade_code[2] == 'U' else "下"
        return grade, semester
    return 0, ""
