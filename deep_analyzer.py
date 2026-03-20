"""
人教版小学数学知识点深度分析模块
基于教育部课程标准，覆盖 1-3 年级数学知识点
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import re


from database import ExamScoreDAO, get_db_connection
from knowledge_week_map import (
    get_week_from_exam_name,
    get_knowledge_by_week,
    get_week_description,
    WEEK_TO_KNOWLEDGE_MAP
)


@dataclass
class KnowledgePoint:
    """知识点定义"""
    code: str  # 知识点编码
    name: str  # 知识点名称
    grade: str  # 所属年级
    semester: str  # 学期 (上/下)
    category: str  # 知识类别
    exam_mapping: List[str] = field(default_factory=list)  # 对应的考试类型


# 人教版小学数学知识点体系 (1-3 年级)
# 基于教育部《义务教育数学课程标准》编写
KNOWLEDGE_SYSTEM = {
    # ==================== 一年级上册 ====================
    "G1U01": KnowledgePoint("G1U01", "准备课（数一数、比一比）", "一年级", "上", "数与代数",
                           exam_mapping=["练习 1", "单元 1", "练习 2"]),
    "G1U02": KnowledgePoint("G1U02", "位置（上下前后左右）", "一年级", "上", "图形与几何",
                           exam_mapping=["练习 1", "单元 1", "单元 2", "练习 3"]),
    "G1U03": KnowledgePoint("G1U03", "1-5 的认识和加减法", "一年级", "上", "数与代数",
                           exam_mapping=["单元 3", "练习 3", "练习 4", "练习 5", "期中"]),
    "G1U04": KnowledgePoint("G1U04", "认识图形（一）（立体图形）", "一年级", "上", "图形与几何",
                           exam_mapping=["单元 4", "练习 6"]),
    "G1U05": KnowledgePoint("G1U05", "6-10 的认识和加减法", "一年级", "上", "数与代数",
                           exam_mapping=["单元 5", "单元 6", "练习 7", "练习 8", "练习 9"]),
    "G1U06": KnowledgePoint("G1U06", "11-20 各数的认识", "一年级", "上", "数与代数",
                           exam_mapping=["单元 7", "练习 10", "练习 11"]),
    "G1U07": KnowledgePoint("G1U07", "认识钟表（整时、半时）", "一年级", "上", "综合与实践",
                           exam_mapping=["单元 8", "练习 11", "练习 12"]),
    "G1U08": KnowledgePoint("G1U08", "20 以内的进位加法", "一年级", "上", "数与代数",
                           exam_mapping=["单元 9", "练习 13", "练习 14", "练习 15", "期末"]),

    # ==================== 一年级下册 ====================
    "G1D01": KnowledgePoint("G1D01", "认识图形（二）（平面图形）", "一年级", "下", "图形与几何",
                           exam_mapping=["单元 1", "练习 1", "练习 2"]),
    "G1D02": KnowledgePoint("G1D02", "20 以内的退位减法", "一年级", "下", "数与代数",
                           exam_mapping=["单元 2", "练习 3", "练习 4", "期中"]),
    "G1D03": KnowledgePoint("G1D03", "100 以内数的认识", "一年级", "下", "数与代数",
                           exam_mapping=["单元 3", "单元 4", "练习 5", "练习 6", "练习 7"]),
    "G1D04": KnowledgePoint("G1D04", "认识人民币（元角分）", "一年级", "下", "综合与实践",
                           exam_mapping=["单元 5", "练习 8", "练习 9"]),
    "G1D05": KnowledgePoint("G1D05", "100 以内的加法和减法（一）", "一年级", "下", "数与代数",
                           exam_mapping=["单元 6", "单元 7", "练习 10", "练习 11", "练习 12", "期末"]),

    # ==================== 二年级上册 ====================
    "G2U01": KnowledgePoint("G2U01", "长度单位（厘米和米）", "二年级", "上", "图形与几何",
                           exam_mapping=["单元 1", "练习 1", "练习 2"]),
    "G2U02": KnowledgePoint("G2U02", "100 以内的加法和减法（二）", "二年级", "上", "数与代数",
                           exam_mapping=["单元 2", "练习 3", "练习 4", "期中"]),
    "G2U03": KnowledgePoint("G2U03", "角的初步认识", "二年级", "上", "图形与几何",
                           exam_mapping=["单元 3", "练习 5"]),
    "G2U04": KnowledgePoint("G2U04", "表内乘法（一）（2-6 的乘法口诀）", "二年级", "上", "数与代数",
                           exam_mapping=["单元 4", "单元 5", "练习 6", "练习 7", "练习 8"]),
    "G2U05": KnowledgePoint("G2U05", "观察物体（一）", "二年级", "上", "图形与几何",
                           exam_mapping=["单元 6", "练习 9"]),
    "G2U06": KnowledgePoint("G2U06", "表内乘法（二）（7-9 的乘法口诀）", "二年级", "上", "数与代数",
                           exam_mapping=["单元 7", "练习 10", "练习 11", "练习 12", "期末"]),
    "G2U07": KnowledgePoint("G2U07", "认识时间（时分）", "二年级", "上", "综合与实践",
                           exam_mapping=["单元 8", "练习 13", "练习 14"]),

    # ==================== 二年级下册 ====================
    "G2D01": KnowledgePoint("G2D01", "数据收集整理（统计表）", "二年级", "下", "统计与概率",
                           exam_mapping=["单元 1", "练习 1", "练习 2"]),
    "G2D02": KnowledgePoint("G2D02", "表内除法（一）（用乘法口诀求商）", "二年级", "下", "数与代数",
                           exam_mapping=["单元 2", "练习 3", "练习 4", "期中"]),
    "G2D03": KnowledgePoint("G2D03", "图形的运动（一）（平移、旋转、轴对称）", "二年级", "下", "图形与几何",
                           exam_mapping=["单元 3", "练习 5"]),
    "G2D04": KnowledgePoint("G2D04", "表内除法（二）", "二年级", "下", "数与代数",
                           exam_mapping=["单元 4", "练习 6", "练习 7"]),
    "G2D05": KnowledgePoint("G2D05", "混合运算（两级运算）", "二年级", "下", "数与代数",
                           exam_mapping=["单元 5", "练习 8", "练习 9"]),
    "G2D06": KnowledgePoint("G2D06", "有余数的除法", "二年级", "下", "数与代数",
                           exam_mapping=["单元 6", "练习 10", "练习 11"]),
    "G2D07": KnowledgePoint("G2D07", "万以内数的认识", "二年级", "下", "数与代数",
                           exam_mapping=["单元 7", "单元 8", "练习 12", "练习 13", "练习 14", "期末"]),

    # ==================== 三年级上册 ====================
    "G3U01": KnowledgePoint("G3U01", "时、分、秒", "三年级", "上", "综合与实践",
                           exam_mapping=["单元 1", "练习 1", "练习 2"]),
    "G3U02": KnowledgePoint("G3U02", "万以内的加法和减法（一）", "三年级", "上", "数与代数",
                           exam_mapping=["单元 2", "练习 3", "练习 4", "期中"]),
    "G3U03": KnowledgePoint("G3U03", "测量（毫米、分米、千米、吨）", "三年级", "上", "图形与几何",
                           exam_mapping=["单元 3", "练习 5", "练习 6"]),
    "G3U04": KnowledgePoint("G3U04", "万以内的加法和减法（二）", "三年级", "上", "数与代数",
                           exam_mapping=["单元 4", "练习 7", "练习 8"]),
    "G3U05": KnowledgePoint("G3U05", "倍的认识", "三年级", "上", "数与代数",
                           exam_mapping=["单元 5", "练习 9", "练习 10"]),
    "G3U06": KnowledgePoint("G3U06", "多位数乘一位数", "三年级", "上", "数与代数",
                           exam_mapping=["单元 6", "练习 11", "练习 12", "练习 13"]),
    "G3U07": KnowledgePoint("G3U07", "长方形和正方形（周长）", "三年级", "上", "图形与几何",
                           exam_mapping=["单元 7", "练习 14", "练习 15"]),
    "G3U08": KnowledgePoint("G3U08", "分数的初步认识", "三年级", "上", "数与代数",
                           exam_mapping=["单元 8", "练习 16", "练习 17", "期末"]),

    # ==================== 三年级下册 ====================
    "G3D01": KnowledgePoint("G3D01", "位置与方向（一）（东南西北）", "三年级", "下", "图形与几何",
                           exam_mapping=["单元 1", "练习 1", "练习 2"]),
    "G3D02": KnowledgePoint("G3D02", "除数是一位数的除法", "三年级", "下", "数与代数",
                           exam_mapping=["单元 2", "练习 3", "练习 4", "期中"]),
    "G3D03": KnowledgePoint("G3D03", "复式统计表", "三年级", "下", "统计与概率",
                           exam_mapping=["单元 3", "练习 5"]),
    "G3D04": KnowledgePoint("G3D04", "两位数乘两位数", "三年级", "下", "数与代数",
                           exam_mapping=["单元 4", "练习 6", "练习 7", "练习 8"]),
    "G3D05": KnowledgePoint("G3D05", "面积", "三年级", "下", "图形与几何",
                           exam_mapping=["单元 5", "练习 9", "练习 10", "练习 11"]),
    "G3D06": KnowledgePoint("G3D06", "年、月、日", "三年级", "下", "综合与实践",
                           exam_mapping=["单元 6", "练习 12", "练习 13"]),
    "G3D07": KnowledgePoint("G3D07", "小数的初步认识", "三年级", "下", "数与代数",
                           exam_mapping=["单元 7", "练习 14", "练习 15", "期末"]),

    # ==================== 四年级上册 ====================
    "G4U01": KnowledgePoint("G4U01", "大数的认识", "四年级", "上", "数与代数",
                           exam_mapping=["单元 1", "练习 1", "练习 2", "练习 3"]),
    "G4U02": KnowledgePoint("G4U02", "公顷和平方千米", "四年级", "上", "图形与几何",
                           exam_mapping=["单元 2", "练习 4"]),
    "G4U03": KnowledgePoint("G4U03", "角的度量", "四年级", "上", "图形与几何",
                           exam_mapping=["单元 3", "练习 5", "练习 6"]),
    "G4U04": KnowledgePoint("G4U04", "三位数乘两位数", "四年级", "上", "数与代数",
                           exam_mapping=["单元 4", "练习 7", "练习 8", "期中"]),
    "G4U05": KnowledgePoint("G4U05", "平行四边形和梯形", "四年级", "上", "图形与几何",
                           exam_mapping=["单元 5", "练习 9", "练习 10"]),
    "G4U06": KnowledgePoint("G4U06", "除数是两位数的除法", "四年级", "上", "数与代数",
                           exam_mapping=["单元 6", "练习 11", "练习 12", "练习 13"]),
    "G4U07": KnowledgePoint("G4U07", "统计（条形统计图）", "四年级", "上", "统计与概率",
                           exam_mapping=["单元 7", "练习 14", "期末"]),

    # ==================== 四年级下册 ====================
    "G4D01": KnowledgePoint("G4D01", "四则运算", "四年级", "下", "数与代数",
                           exam_mapping=["单元 1", "练习 1", "练习 2"]),
    "G4D02": KnowledgePoint("G4D02", "观察物体（二）", "四年级", "下", "图形与几何",
                           exam_mapping=["单元 2", "练习 3"]),
    "G4D03": KnowledgePoint("G4D03", "运算定律（加法、乘法）", "四年级", "下", "数与代数",
                           exam_mapping=["单元 3", "练习 4", "练习 5", "期中"]),
    "G4D04": KnowledgePoint("G4D04", "小数的意义和性质", "四年级", "下", "数与代数",
                           exam_mapping=["单元 4", "练习 6", "练习 7", "练习 8"]),
    "G4D05": KnowledgePoint("G4D05", "三角形", "四年级", "下", "图形与几何",
                           exam_mapping=["单元 5", "练习 9", "练习 10"]),
    "G4D06": KnowledgePoint("G4D06", "小数的加法和减法", "四年级", "下", "数与代数",
                           exam_mapping=["单元 6", "练习 11", "练习 12"]),
    "G4D07": KnowledgePoint("G4D07", "图形的运动（平移）", "四年级", "下", "图形与几何",
                           exam_mapping=["单元 7", "练习 13"]),
    "G4D08": KnowledgePoint("G4D08", "平均数与条形统计图", "四年级", "下", "统计与概率",
                           exam_mapping=["单元 8", "练习 14", "练习 15", "期末"]),

    # ==================== 五年级上册 ====================
    "G5U01": KnowledgePoint("G5U01", "小数乘法", "五年级", "上", "数与代数",
                           exam_mapping=["单元 1", "练习 1", "练习 2", "练习 3"]),
    "G5U02": KnowledgePoint("G5U02", "位置", "五年级", "上", "图形与几何",
                           exam_mapping=["单元 2", "练习 4"]),
    "G5U03": KnowledgePoint("G5U03", "小数除法", "五年级", "上", "数与代数",
                           exam_mapping=["单元 3", "练习 5", "练习 6", "期中"]),
    "G5U04": KnowledgePoint("G5U04", "可能性", "五年级", "上", "统计与概率",
                           exam_mapping=["单元 4", "练习 7"]),
    "G5U05": KnowledgePoint("G5U05", "简易方程", "五年级", "上", "数与代数",
                           exam_mapping=["单元 5", "练习 8", "练习 9", "练习 10"]),
    "G5U06": KnowledgePoint("G5U06", "多边形的面积", "五年级", "上", "图形与几何",
                           exam_mapping=["单元 6", "练习 11", "练习 12", "练习 13"]),
    "G5U07": KnowledgePoint("G5U07", "因数与倍数", "五年级", "上", "数与代数",
                           exam_mapping=["单元 7", "练习 14", "期末"]),

    # ==================== 五年级下册 ====================
    "G5D01": KnowledgePoint("G5D01", "观察物体（三）", "五年级", "下", "图形与几何",
                           exam_mapping=["单元 1", "练习 1"]),
    "G5D02": KnowledgePoint("G5D02", "因数与倍数（二）", "五年级", "下", "数与代数",
                           exam_mapping=["单元 2", "练习 2", "练习 3"]),
    "G5D03": KnowledgePoint("G5D03", "长方体和正方体", "五年级", "下", "图形与几何",
                           exam_mapping=["单元 3", "练习 4", "练习 5", "期中"]),
    "G5D04": KnowledgePoint("G5D04", "分数的意义和性质", "五年级", "下", "数与代数",
                           exam_mapping=["单元 4", "练习 6", "练习 7", "练习 8"]),
    "G5D05": KnowledgePoint("G5D05", "分数的加法和减法", "五年级", "下", "数与代数",
                           exam_mapping=["单元 5", "练习 9", "练习 10"]),
    "G5D06": KnowledgePoint("G5D06", "图形的运动（旋转）", "五年级", "下", "图形与几何",
                           exam_mapping=["单元 6", "练习 11"]),
    "G5D07": KnowledgePoint("G5D07", "折线统计图", "五年级", "下", "统计与概率",
                           exam_mapping=["单元 7", "练习 12", "练习 13"]),
    "G5D08": KnowledgePoint("G5D08", "数学广角 - 找次品", "五年级", "下", "综合与实践",
                           exam_mapping=["单元 8", "练习 14", "期末"]),

    # ==================== 六年级上册 ====================
    "G6U01": KnowledgePoint("G6U01", "分数乘法", "六年级", "上", "数与代数",
                           exam_mapping=["单元 1", "练习 1", "练习 2", "练习 3"]),
    "G6U02": KnowledgePoint("G6U02", "位置与方向（二）", "六年级", "上", "图形与几何",
                           exam_mapping=["单元 2", "练习 4"]),
    "G6U03": KnowledgePoint("G6U03", "分数除法", "六年级", "上", "数与代数",
                           exam_mapping=["单元 3", "练习 5", "练习 6", "期中"]),
    "G6U04": KnowledgePoint("G6U04", "比", "六年级", "上", "数与代数",
                           exam_mapping=["单元 4", "练习 7"]),
    "G6U05": KnowledgePoint("G6U05", "圆", "六年级", "上", "图形与几何",
                           exam_mapping=["单元 5", "练习 8", "练习 9", "练习 10"]),
    "G6U06": KnowledgePoint("G6U06", "百分数", "六年级", "上", "数与代数",
                           exam_mapping=["单元 6", "练习 11", "练习 12"]),
    "G6U07": KnowledgePoint("G6U07", "扇形统计图", "六年级", "上", "统计与概率",
                           exam_mapping=["单元 7", "练习 13", "期末"]),

    # ==================== 六年级下册 ====================
    "G6D01": KnowledgePoint("G6D01", "负数", "六年级", "下", "数与代数",
                           exam_mapping=["单元 1", "练习 1", "练习 2"]),
    "G6D02": KnowledgePoint("G6D02", "百分数（二）", "六年级", "下", "数与代数",
                           exam_mapping=["单元 2", "练习 3"]),
    "G6D03": KnowledgePoint("G6D03", "圆柱与圆锥", "六年级", "下", "图形与几何",
                           exam_mapping=["单元 3", "练习 4", "练习 5", "期中"]),
    "G6D04": KnowledgePoint("G6D04", "比例", "六年级", "下", "数与代数",
                           exam_mapping=["单元 4", "练习 6", "练习 7", "练习 8"]),
    "G6D05": KnowledgePoint("G6D05", "数学广角 - 鸽巢问题", "六年级", "下", "综合与实践",
                           exam_mapping=["单元 5", "练习 9", "期末"]),
}

# 练习号与知识点的映射关系（用于更精确的匹配）
PRACTICE_MAPPING = {
    # 一年级上册
    "10032": {  # 一上
        1: ["G1U01", "G1U02"], 2: ["G1U01", "G1U02"], 3: ["G1U03"], 4: ["G1U03"],
        5: ["G1U03"], 6: ["G1U04"], 7: ["G1U05"], 8: ["G1U05"], 9: ["G1U05"],
        10: ["G1U06"], 11: ["G1U06", "G1U07"], 12: ["G1U07"], 13: ["G1U08"],
        14: ["G1U08"], 15: ["G1U08"], 16: ["G1U08"],
    },
    # 一年级下册
    "10033": {  # 一下
        1: ["G1D01"], 2: ["G1D01"], 3: ["G1D02"], 4: ["G1D02", "G1D03"],
        5: ["G1D03", "G1D04"], 6: ["G1D03"], 7: ["G1D03"], 8: ["G1D04"],
        9: ["G1D04"], 10: ["G1D05"], 11: ["G1D05"], 12: ["G1D05"],
    },
    # 二年级上册
    "10034": {  # 二上
        1: ["G2U01"], 2: ["G2U01", "G2U02"], 3: ["G2U02", "G2U03"],
        4: ["G2U04"], 5: ["G2U04"], 6: ["G2U05"], 7: ["G2U06"],
        8: ["G2U06"], 9: ["G2U05"], 10: ["G2U06"], 11: ["G2U06"],
        12: ["G2U07"], 13: ["G2U07"], 14: ["G2U07"],
    },
    # 二年级下册
    "10035": {  # 二下
        1: ["G2D01"], 2: ["G2D02"], 3: ["G2D02"], 4: ["G2D04"],
        5: ["G2D05"], 6: ["G2D06"], 7: ["G2D06"], 8: ["G2D05"],
        9: ["G2D05"], 10: ["G2D06"], 11: ["G2D06"], 12: ["G2D07"],
        13: ["G2D07"], 14: ["G2D07"], 15: ["G2D07"], 16: ["G2D07"],
        17: ["G2D07"], 18: ["G2D07"], 19: ["G2D07"], 20: ["G2D07"],
        21: ["G2D07"],
    },
    # 三年级上册
    "10036": {  # 三上
        1: ["G3U01"], 2: ["G3U02"], 3: ["G3U03"], 4: ["G3U04"],
        5: ["G3U05"], 6: ["G3U06"], 7: ["G3U07"], 8: ["G3U08"],
    },
    # 三年级下册
    "10037": {  # 三下
        1: ["G3D01"], 2: ["G3D02"], 3: ["G3D02"], 4: ["G3D04"],
        5: ["G3D05"], 6: ["G3D06"], 7: ["G3D07"], 8: ["G3D07"],
        9: ["G3D04"], 10: ["G3D05"], 11: ["G3D05"], 12: ["G3D06"],
        13: ["G3D06"], 14: ["G3D07"],
    },
    # 四年级上册
    "10038": {  # 四上
        1: ["G4U01"], 2: ["G4U01"], 3: ["G4U01"], 4: ["G4U02"],
        5: ["G4U03"], 6: ["G4U03"], 7: ["G4U04"], 8: ["G4U04"],
        9: ["G4U05"], 10: ["G4U05"], 11: ["G4U06"], 12: ["G4U06"],
        13: ["G4U06"], 14: ["G4U07"],
    },
    # 四年级下册
    "10039": {  # 四下
        1: ["G4D01"], 2: ["G4D02"], 3: ["G4D03"], 4: ["G4D03"],
        5: ["G4D04"], 6: ["G4D04"], 7: ["G4D05"], 8: ["G4D06"],
        9: ["G4D06"], 10: ["G4D07"], 11: ["G4D08"], 12: ["G4D08"],
        13: ["G4D08"], 14: ["G4D08"],
    },
    # 五年级上册
    "10040": {  # 五上
        1: ["G5U01"], 2: ["G5U01"], 3: ["G5U02"], 4: ["G5U03"],
        5: ["G5U03"], 6: ["G5U04"], 7: ["G5U05"], 8: ["G5U05"],
        9: ["G5U05"], 10: ["G5U06"], 11: ["G5U06"], 12: ["G5U06"],
        13: ["G5U07"], 14: ["G5U07"],
    },
    # 五年级下册
    "10041": {  # 五下
        1: ["G5D01"], 2: ["G5D02"], 3: ["G5D02"], 4: ["G5D03"],
        5: ["G5D03"], 6: ["G5D04"], 7: ["G5D04"], 8: ["G5D05"],
        9: ["G5D05"], 10: ["G5D06"], 11: ["G5D07"], 12: ["G5D07"],
        13: ["G5D08"], 14: ["G5D08"],
    },
    # 六年级上册
    "10042": {  # 六上
        1: ["G6U01"], 2: ["G6U01"], 3: ["G6U02"], 4: ["G6U03"],
        5: ["G6U03"], 6: ["G6U04"], 7: ["G6U05"], 8: ["G6U05"],
        9: ["G6U05"], 10: ["G6U06"], 11: ["G6U06"], 12: ["G6U07"],
        13: ["G6U07"],
    },
    # 六年级下册
    "10043": {  # 六下
        1: ["G6D01"], 2: ["G6D01"], 3: ["G6D02"], 4: ["G6D03"],
        5: ["G6D03"], 6: ["G6D04"], 7: ["G6D04"], 8: ["G6D04"],
        9: ["G6D05"],
    },
}

# 知识点类别说明
CATEGORY_MAP = {
    "数与代数": "数的认识与运算，包括整数、小数、分数的认识和加减乘除运算，培养学生数感和运算能力",
    "图形与几何": "空间与图形的认识，包括基本图形、位置方向、测量、面积等，培养空间观念和几何直观",
    "统计与概率": "数据收集、整理、分析，认识统计表和统计图，培养数据分析观念",
    "综合与实践": "数学知识的综合应用，包括时间认识、人民币、问题解决等，培养应用意识和实践能力"
}

# 各年级知识点数量统计
GRADE_STATS = {
    "一年级": {"上": 8, "下": 5},
    "二年级": {"上": 7, "下": 7},
    "三年级": {"上": 8, "下": 7},
    "四年级": {"上": 7, "下": 8},
    "五年级": {"上": 7, "下": 8},
    "六年级": {"上": 7, "下": 5},
}


class DeepScoreAnalyzer:
    """深度成绩分析器"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.students_df: Optional[pd.DataFrame] = None
        self.semester_data: Dict[str, pd.DataFrame] = {}
        self.student_names: Dict[int, str] = {}
        self.knowledge_points = KNOWLEDGE_SYSTEM
        self.entered_scores_cache: Dict[int, List[Dict]] = {}  # 录入成绩缓存
        self.exam_order: List[str] = []  # 保存 Excel 中考试列的原始顺序

    def _normalize_semester_name(self, semester: str) -> str:
        """标准化学期名称，去除 -math_scores 等后缀"""
        import re
        # 匹配如 "10032-1(2) 班上学期" 或 "10037-3(2) 班下学期"，提取 "1(2) 班上学期" 格式
        match = re.search(r'\d+-(\d+\(\d+\)\s*班.+学期)', semester)
        if match:
            # 去除中间空格，统一格式
            return match.group(1).replace(' ', '')
        # 如果没有匹配到，尝试直接匹配 "1(2) 班上学期" 格式
        match2 = re.search(r'(\d+\(\d+\)\s*班.+学期)', semester)
        if match2:
            return match2.group(1).replace(' ', '')
        return semester

    def refresh_entered_scores(self):
        """刷新录入成绩缓存"""
        self.entered_scores_cache = {}
        all_scores = ExamScoreDAO.get_all_scores()
        for s in all_scores:
            sid = s['student_id']
            if sid not in self.entered_scores_cache:
                self.entered_scores_cache[sid] = []
            self.entered_scores_cache[sid].append({
                'semester': s['semester'],
                'exam_name': s['exam_name'],
                'score': s['score'],
                'exam_date': s['exam_date']
            })

    def get_scores(self, student_id: Optional[int] = None) -> List[Dict]:
        """
        获取成绩数据（从数据库）

        Args:
            student_id: 学生 ID（可选）

        Returns:
            成绩记录列表，包含 exam_name, score, week, error_knowledge 等
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        if student_id:
            cursor.execute("""
                SELECT e.student_id, s.name, e.exam_name, e.score, e.exam_date
                FROM exam_scores e
                JOIN students s ON e.student_id = s.student_id
                WHERE e.student_id = ?
            """, (student_id,))
        else:
            cursor.execute("""
                SELECT e.student_id, s.name, e.exam_name, e.score, e.exam_date
                FROM exam_scores e
                JOIN students s ON e.student_id = s.student_id
            """)

        rows = cursor.fetchall()
        conn.close()

        scores = []
        for row in rows:
            exam_week = get_week_from_exam_name(row[2])  # row[2] = exam_name

            # 从 error_records 表获取错题知识点
            cursor2 = get_db_connection().cursor()
            cursor2.execute("""
                SELECT knowledge_code FROM error_records
                WHERE student_id = ? AND exam_name = ?
            """, (row[0], row[2]))
            error_rows = cursor2.fetchall()
            error_kp = [r[0] for r in error_rows] if error_rows else []

            scores.append({
                'student_id': row[0],
                'student_name': row[1],
                'exam_name': row[2],
                'score': row[3],
                'week': exam_week,
                'error_knowledge': error_kp
            })

        return scores

    def _get_exam_sort_key(self, exam_name: str) -> Tuple[int, int]:
        """
        从考试名称提取排序关键字，支持自然排序

        例如：周练 1 -> (1, 1), 周练 10 -> (1, 10), 期末模 1 -> (9, 1)
        返回 (类型权重，序号)，确保周练 2 排在周练 10 前面
        """
        # 定义考试类型权重
        type_weights = {
            '周练': 1,
            '练习': 2,
            '单元': 3,
            '期中': 8,
            '期末模': 9,
            '期末': 10,
        }

        # 匹配考试类型和序号
        for exam_type, weight in type_weights.items():
            if exam_name.startswith(exam_type):
                # 提取序号
                num_part = exam_name[len(exam_type):]
                try:
                    num = int(num_part)
                    return (weight, num)
                except ValueError:
                    return (weight, 0)

        # 如果不匹配任何类型，返回默认值
        return (99, 0)

    def get_class_stats(self, semester: str = None) -> pd.DataFrame:
        """
        获取班级每次考试的统计数据（平均分、最高分、最低分）

        Args:
            semester: 学期名称（可选），如 "1(2) 班上学期"

        Returns:
            DataFrame，包含考试名称、平均分、最高分、最低分
        """
        if self.students_df is None:
            return pd.DataFrame()

        stats = []
        exam_cols = set()

        # 收集所有考试列
        for col in self.students_df.columns:
            if col not in ['学号', '姓名']:
                exam_cols.add(col)

        # 如果指定了学期，过滤
        if semester:
            normalized_semester = self._normalize_semester_name(semester)
            exam_cols = {col for col in exam_cols
                        if self._normalize_semester_name(col.split('_', 1)[0] if '_' in col else col) == normalized_semester}

        # 计算每次考试的统计数据，按自然排序
        for col in sorted(exam_cols, key=lambda x: self._get_exam_sort_key(x.split('_', 1)[1] if '_' in x else x)):
            # 提取考试名称
            exam_name = col.split('_', 1)[1] if '_' in col else col
            sem_name = self._normalize_semester_name(col.split('_', 1)[0] if '_' in col else col)

            # 获取该列所有学生的成绩
            scores = self.students_df[col].dropna()

            if len(scores) > 0:
                stats.append({
                    '学期': sem_name,
                    '考试': exam_name,
                    '平均分': round(scores.mean(), 2),
                    '最高分': scores.max(),
                    '最低分': scores.min(),
                    '参考人数': len(scores)
                })

        return pd.DataFrame(stats)

    def load_all_data(self) -> pd.DataFrame:
        """加载所有数据"""
        all_scores = []

        # 扫描 data 根目录和 uploads 子目录
        excel_files = []

        # 扫描 uploads 子目录（新上传的文件）
        uploads_dir = self.data_dir / "uploads"
        if uploads_dir.exists():
            excel_files.extend(sorted(uploads_dir.glob("*.xlsx")))

        # 扫描 data 根目录（备份文件）
        excel_files.extend(sorted(self.data_dir.glob("*.xlsx")))

        for file in excel_files:
            semester_name = self._parse_semester_name(file.name)
            df = pd.read_excel(file)

            # 标准化列名
            if '学号' not in df.columns:
                df.columns = ['学号', '姓名'] + list(df.columns[2:])

            # 清理成绩列中的空值（空格、'nan' 字符串等）
            score_columns = [col for col in df.columns if col not in ['学号', '姓名']]
            for col in score_columns:
                # 将空格、'nan' 字符串等替换为真正的 NaN
                df[col] = df[col].apply(lambda x: None if (isinstance(x, str) and (x.strip() == '' or x.lower() == 'nan')) else x)

            # 存储学生姓名
            for _, row in df.iterrows():
                if pd.notna(row['学号']):
                    self.student_names[int(row['学号'])] = row['姓名']

            all_scores.append(df)
            self.semester_data[semester_name] = df

        if all_scores:
            # 合并所有数据 - 按学号和姓名分组，将不同学期的数据合并到同一行
            combined_df = pd.concat(all_scores, ignore_index=True)
            self.students_df = combined_df.groupby(['学号', '姓名'], as_index=False).first()

        # 刷新录入成绩缓存
        self.refresh_entered_scores()

        return self.students_df

    def _parse_semester_name(self, filename: str) -> str:
        """解析学期名称"""
        # 使用 .+ 代替 [上下] 以正确匹配中文字符
        match = re.search(r'(\d+-\d+\(\d+\) 班.+学期)', filename)
        if match:
            return match.group(1)
        return filename.replace("-math_scores.xlsx", "")

    def _normalize_exam_name(self, exam_name: str) -> str:
        """标准化考试名称，便于匹配"""
        # 移除下划线和空格
        exam_name = exam_name.replace('_', '').replace(' ', '')
        return exam_name

    def map_exam_to_knowledge(self, exam_name: str, semester: str = None) -> List[str]:
        """将考试名称映射到知识点"""
        if not exam_name:
            return []

        # 提取学期编号（如 10032 表示一上）
        semester_code = None
        if semester:
            code_match = re.search(r'(\d+)-', semester)
            if code_match:
                semester_code = code_match.group(1)

        # 提取练习号/单元号
        practice_match = re.search(r'[练习单元月考模拟](\d+)', exam_name)
        if practice_match:
            practice_num = int(practice_match.group(1))
            # 使用练习号映射
            if semester_code and semester_code in PRACTICE_MAPPING:
                practice_map = PRACTICE_MAPPING[semester_code]
                if practice_num in practice_map:
                    return practice_map[practice_num]

        # 精确匹配知识点名称
        for kp_code, kp in self.knowledge_points.items():
            for exam_mapping in kp.exam_mapping:
                if exam_mapping in exam_name:
                    return [kp_code]

        # 特殊考试类型：期中/期末/期末模考
        if "期中" in exam_name or "期中复习" in exam_name:
            # 返回该学期前半部分的知识点
            if semester:
                grade_match = re.search(r'(\d+)\([上下]\)', semester)
                if grade_match:
                    grade = int(grade_match.group(1))
                    semester_part = "上" if "上" in semester else "下"
                    prefix = f"G{grade}{semester_part}"
                    return [f"{prefix}0{i}" for i in range(1, 5)]  # 前 4 个单元

        if "期末" in exam_name or "期末模" in exam_name:
            # 返回该学期所有知识点
            if semester:
                grade_match = re.search(r'(\d+)\([上下]\)', semester)
                if grade_match:
                    grade = int(grade_match.group(1))
                    semester_part = "上" if "上" in semester else "下"
                    prefix = f"G{grade}{semester_part}"
                    return [kp for kp in self.knowledge_points.keys() if kp.startswith(prefix)]

        # 月考：根据月份推断范围
        month_match = re.search(r'月考 (\d+)', exam_name)
        if month_match and semester:
            month = int(month_match.group(1))
            grade_match = re.search(r'(\d+)\([上下]\)', semester)
            if grade_match:
                grade = int(grade_match.group(1))
                semester_part = "上" if "上" in semester else "下"
                prefix = f"G{grade}{semester_part}"
                # 根据月考月份返回对应范围的知识点
                start_unit = min(month, 8)
                return [f"{prefix}0{i}" for i in range(max(1, start_unit-1), start_unit+1)]

        # 模拟考试：综合性考试，返回该学期所有知识点
        if "模拟" in exam_name:
            if semester:
                grade_match = re.search(r'(\d+)\([上下]\)', semester)
                if grade_match:
                    grade = int(grade_match.group(1))
                    semester_part = "上" if "上" in semester else "下"
                    prefix = f"G{grade}{semester_part}"
                    return [kp for kp in self.knowledge_points.keys() if kp.startswith(prefix)]

        # 复习练习
        if "复习" in exam_name:
            # 返回该学期所有知识点
            if semester:
                grade_match = re.search(r'(\d+)\([上下]\)', semester)
                if grade_match:
                    grade = int(grade_match.group(1))
                    semester_part = "上" if "上" in semester else "下"
                    prefix = f"G{grade}{semester_part}"
                    return [kp for kp in self.knowledge_points.keys() if kp.startswith(prefix)]

        # 如果没有匹配到，根据学期返回对应的单元范围
        if semester and semester_code and semester_code in PRACTICE_MAPPING:
            # 默认返回该学期的所有知识点
            grade_match = re.search(r'(\d+)\([上下]\)', semester)
            if grade_match:
                grade = int(grade_match.group(1))
                semester_part = "上" if "上" in semester else "下"
                prefix = f"G{grade}{semester_part}"
                return [kp for kp in self.knowledge_points.keys() if kp.startswith(prefix)]

        return []

    def _get_student_merged_scores(self, student_id: int) -> Dict[str, Tuple[str, float]]:
        """获取学生合并后的成绩 {考试列名：(学期，分数)}"""
        scores = {}

        # 1. 优先从数据库获取成绩（DataManager 数据源）
        db_scores = self.get_scores(student_id=student_id)
        for db_score in db_scores:
            exam_name = db_score['exam_name']
            semester = self._get_semester_from_exam_name(exam_name)
            if exam_name not in scores and db_score['score'] is not None:
                scores[exam_name] = (semester, float(db_score['score']))

        # 2. 合并录入的成绩（从 ExamScoreDAO）
        if student_id in self.entered_scores_cache:
            for es in self.entered_scores_cache[student_id]:
                key = es['exam_name']
                if key not in scores and es['score'] is not None:
                    scores[key] = (es['semester'], float(es['score']))

        # 3. 如果数据库为空，从 Excel 获取成绩（向后兼容）
        if not scores and self.students_df is not None:
            student_data = self.students_df[self.students_df['学号'] == student_id]
            if not student_data.empty:
                for col in self.students_df.columns:
                    if col not in ['学号', '姓名']:
                        value = student_data[col].values[0]
                        if pd.notna(value):
                            # 提取学期
                            parts = col.split('_', 1)
                            if len(parts) == 2:
                                semester = parts[0]
                                scores[col] = (semester, float(value))

        return scores

    def _get_semester_from_exam_name(self, exam_name: str) -> str:
        """从考试名称或录入成绩中获取学期信息"""
        # 尝试从录入成绩缓存中查找学期
        for sid, scores in self.entered_scores_cache.items():
            for es in scores:
                if es['exam_name'] == exam_name:
                    return es['semester']
        # 默认返回空字符串
        return ""

    def analyze_knowledge_mastery(self, student_id: int) -> Dict[str, Dict]:
        """分析学生对各知识点的掌握程度（使用合并后的成绩）"""
        if self.students_df is None:
            return {}

        # 获取合并后的成绩
        merged_scores = self._get_student_merged_scores(student_id)

        if not merged_scores:
            return {}

        # 统计每个知识点的得分情况
        knowledge_scores: Dict[str, List[float]] = {}

        # 遍历所有成绩
        for col, (semester, score) in merged_scores.items():
            # 获取考试对应的知识点
            knowledge_points = self.map_exam_to_knowledge(col, semester)

            # 将分数分配到对应知识点
            for kp in knowledge_points:
                if kp not in knowledge_scores:
                    knowledge_scores[kp] = []
                knowledge_scores[kp].append(score)

        # 计算每个知识点的掌握度
        mastery = {}
        for kp, scores in knowledge_scores.items():
            if scores:
                kp_info = self.knowledge_points.get(kp)
                if kp_info:
                    mastery[kp] = {
                        'name': kp_info.name,
                        'grade': kp_info.grade,
                        'semester': kp_info.semester,
                        'category': kp_info.category,
                        'avg_score': round(np.mean(scores), 2),
                        'min_score': round(min(scores), 2),
                        'max_score': round(max(scores), 2),
                        'exam_count': len(scores),
                        'mastery_level': self._get_mastery_level(np.mean(scores))
                    }

        return mastery

    def _get_mastery_level(self, score: float) -> str:
        """根据分数判断掌握水平"""
        if score >= 95:
            return "精通"
        elif score >= 90:
            return "熟练掌握"
        elif score >= 80:
            return "基本掌握"
        elif score >= 70:
            return "部分掌握"
        elif score >= 60:
            return "初步了解"
        else:
            return "需要加强"

    def analyze_category_performance(self, student_id: int) -> Dict[str, Dict]:
        """分析各大知识类别的表现"""
        mastery = self.analyze_knowledge_mastery(student_id)

        category_scores: Dict[str, List[float]] = {cat: [] for cat in CATEGORY_MAP}

        for kp, data in mastery.items():
            cat = data['category']
            if cat in category_scores:
                category_scores[cat].append(data['avg_score'])

        category_performance = {}
        for cat, scores in category_scores.items():
            if scores:
                category_performance[cat] = {
                    'description': CATEGORY_MAP[cat],
                    'avg_score': round(np.mean(scores), 2),
                    'knowledge_count': len(scores),
                    'performance': self._get_performance_level(np.mean(scores))
                }

        return category_performance

    def _get_performance_level(self, score: float) -> str:
        """获取表现等级"""
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "中等"
        elif score >= 60:
            return "及格"
        else:
            return "需努力"

    def get_weak_knowledge_points(self, student_id: int, threshold: float = 80) -> List[Dict]:
        """获取薄弱知识点"""
        mastery = self.analyze_knowledge_mastery(student_id)

        weak_points = []
        for kp, data in mastery.items():
            if data['avg_score'] < threshold:
                weak_points.append({
                    'code': kp,
                    'name': data['name'],
                    'grade': data['grade'],
                    'semester': data['semester'],
                    'category': data['category'],
                    'score': data['avg_score'],
                    'level': data['mastery_level'],
                    'recommendation': self._get_recommendation(kp, data['avg_score'])
                })

        return sorted(weak_points, key=lambda x: x['score'])

    def _get_recommendation(self, knowledge_code: str, score: float) -> str:
        """获取学习建议"""
        kp = self.knowledge_points.get(knowledge_code)
        if not kp:
            return "建议系统复习"

        base_recommendation = f"【{kp.name}】"
        if score < 60:
            return base_recommendation + "需要重新学习基础概念，多做基础练习题"
        elif score < 70:
            return base_recommendation + "建议加强练习，重点理解核心概念和解题方法"
        elif score < 80:
            return base_recommendation + "巩固已学知识，适当提高练习难度"
        else:
            return base_recommendation + "保持练习状态，挑战综合应用题"

    def get_learning_path(self, student_id: int) -> List[Dict]:
        """生成个性化学习路径"""
        weak_points = self.get_weak_knowledge_points(student_id, threshold=85)

        # 按年级和学期排序
        grade_order = {"一年级": 1, "二年级": 2, "三年级": 3}
        semester_order = {"上": 1, "下": 2}

        weak_points.sort(key=lambda x: (
            grade_order.get(x['grade'], 0),
            semester_order.get(x['semester'], 0),
            x['score']
        ))

        return weak_points

    def get_grade_progress(self, student_id: int) -> Dict[str, Dict]:
        """分析各年级知识掌握进度"""
        mastery = self.analyze_knowledge_mastery(student_id)

        grade_data: Dict[str, Dict[str, List]] = {
            "一年级": {"scores": [], "names": []},
            "二年级": {"scores": [], "names": []},
            "三年级": {"scores": [], "names": []}
        }

        for kp, data in mastery.items():
            grade = data['grade']
            if grade in grade_data:
                grade_data[grade]["scores"].append(data['avg_score'])
                grade_data[grade]["names"].append(data['name'])

        progress = {}
        for grade, data in grade_data.items():
            if data["scores"]:
                scores = data["scores"]
                progress[grade] = {
                    'avg_score': round(np.mean(scores), 2),
                    'knowledge_points': len(scores),
                    'mastered': len([s for s in scores if s >= 80]),
                    'weak': len([s for s in scores if s < 80]),
                    'mastery_rate': round(len([s for s in scores if s >= 80]) / len(scores) * 100, 1)
                }

        return progress

    def _calculate_basic_stats(self, student_id: int) -> Dict:
        """计算基础统计信息（使用合并后的成绩）"""
        if self.students_df is None:
            return {}

        # 使用合并后的成绩
        merged_scores = self._get_student_merged_scores(student_id)

        if not merged_scores:
            return {}

        all_scores = [score for _, (_, score) in merged_scores.items()]

        if not all_scores:
            return {}

        scores_array = np.array(all_scores)
        return {
            '平均分': round(scores_array.mean(), 2),
            '最高分': round(scores_array.max(), 2),
            '最低分': round(scores_array.min(), 2),
            '标准差': round(scores_array.std(), 2),
            '考试次数': len(all_scores),
            '优秀率': round((scores_array >= 90).sum() / len(all_scores) * 100, 1),
            '及格率': round((scores_array >= 60).sum() / len(all_scores) * 100, 1),
        }

    def generate_report(self, student_id: int) -> str:
        """生成诊断报告"""
        stats = self._calculate_basic_stats(student_id)
        category_perf = self.analyze_category_performance(student_id)
        weak_points = self.get_weak_knowledge_points(student_id)
        grade_progress = self.get_grade_progress(student_id)

        student_name = self.student_names.get(student_id, 'Unknown')

        report = f"""# 📊 数学学习诊断报告

**学生**: {student_name} (学号：{student_id})

---

## 一、整体表现

| 指标 | 数值 | 评价 |
|------|------|------|
| 平均分 | {stats.get('平均分', 'N/A')} | {self._eval_score(stats.get('平均分', 0))} |
| 最高分 | {stats.get('最高分', 'N/A')} | - |
| 最低分 | {stats.get('最低分', 'N/A')} | - |
| 标准差 | {stats.get('标准差', 'N/A')} | {self._eval_std(stats.get('标准差', 0))} |
| 优秀率 | {stats.get('优秀率', 'N/A')}% | - |
| 考试次数 | {stats.get('考试次数', 0)} | - |

---

## 二、知识领域分析

"""
        for cat, data in category_perf.items():
            cat_name = cat.replace("数与代数", "🔢 数与代数").replace("图形与几何", "📐 图形与几何").replace("统计与概率", "📊 统计与概率").replace("综合与实践", "🔧 综合与实践")
            report += f"""### {cat_name}
- **能力描述**: {data['description']}
- **平均分**: {data['avg_score']}
- **知识点数量**: {data['knowledge_count']}
- **表现等级**: {data['performance']}

"""

        report += """---

## 三、各年级掌握进度

"""
        for grade, data in grade_progress.items():
            emoji = "✅" if data['mastery_rate'] >= 80 else "⚠️" if data['mastery_rate'] >= 60 else "❌"
            report += f"""### {emoji} {grade}
- 平均分：{data['avg_score']}
- 已掌握：{data['mastered']}/{data['knowledge_points']} ({data['mastery_rate']}%)
- 需加强：{data['weak']} 个知识点

"""

        report += """---

## 四、薄弱环节

"""
        if weak_points:
            for i, wp in enumerate(weak_points[:10], 1):
                report += f"""**{i}. {wp['name']}** ({wp['grade']}{wp['semester']})
   - 得分：{wp['score']} | 掌握程度：{wp['level']}
   - 建议：{wp['recommendation']}

"""
        else:
            report += "🎉 所有知识点掌握良好，暂无明显薄弱环节！\n\n"

        report += """---

## 五、学习建议

"""
        if weak_points:
            top_weak = weak_points[:3]
            report += "根据分析结果，建议优先加强以下知识点：\n\n"
            for wp in top_weak:
                report += f"- [ ] {wp['name']} ({wp['score']}分)\n"
        else:
            report += "当前学习状态优秀，建议：\n\n- 保持现有学习节奏\n- 适当挑战拓展题目\n- 注重知识的综合运用\n"

        return report

    def _eval_score(self, score: float) -> str:
        """评价分数"""
        if score >= 90:
            return "🌟 优秀"
        elif score >= 80:
            return "👍 良好"
        elif score >= 70:
            return "👌 中等"
        elif score >= 60:
            return "💪 及格"
        else:
            return "📚 需努力"

    def _eval_std(self, std: float) -> str:
        """评价标准差"""
        if std < 5:
            return "发挥非常稳定"
        elif std < 10:
            return "发挥较稳定"
        else:
            return "波动较大，需注意"

    # ==================== 时序追踪和轨迹诊断 ====================

    def get_weekly_tracking(self, student_id: int, grade_code: str, start_week: int = 1, end_week: int = 18) -> List[Dict]:
        """
        获取学生周次追踪数据（时序追踪视图）

        Args:
            student_id: 学生 ID
            grade_code: 年级代码 (如"G1U")
            start_week: 起始周
            end_week: 结束周

        Returns:
            周次追踪数据列表，包含每周成绩、知识点、掌握程度等
        """
        all_scores = self.get_scores(student_id=student_id)

        tracking_data = []

        for week in range(start_week, end_week + 1):
            # 获取该周次的考试
            week_exams = [s for s in all_scores if s['week'] == week]

            # 获取该周次的知识点
            knowledge_codes = get_knowledge_by_week(grade_code, week)
            week_desc = get_week_description(grade_code, week)

            week_record = {
                "week": week,
                "description": week_desc,
                "exam_count": len(week_exams),
                "exams": [],
                "avg_score": None,
                "knowledge_codes": knowledge_codes,
                "knowledge_names": [
                    self.knowledge_points.get(kp).name
                    for kp in knowledge_codes
                    if kp in self.knowledge_points
                ],
                "error_knowledge": [],
                "trend_flag": "normal"  # normal, up, down, warning
            }

            if week_exams:
                scores = [s['score'] for s in week_exams]
                week_record["avg_score"] = round(sum(scores) / len(scores), 2)
                week_record["exams"] = [
                    {
                        "exam_name": s['exam_name'],
                        "score": s['score'],
                        "error_knowledge": s['error_knowledge']
                    }
                    for s in week_exams
                ]

                # 收集错题知识点
                all_errors = []
                for s in week_exams:
                    all_errors.extend(s['error_knowledge'])
                week_record["error_knowledge"] = list(set(all_errors))

            tracking_data.append(week_record)

        # 计算趋势标记
        for i, record in enumerate(tracking_data):
            if i == 0:
                continue

            prev_score = tracking_data[i-1].get("avg_score")
            curr_score = record.get("avg_score")

            if prev_score is not None and curr_score is not None:
                diff = curr_score - prev_score
                if diff > 5:
                    record["trend_flag"] = "up"
                elif diff < -5:
                    record["trend_flag"] = "down"
                elif diff < 0:
                    record["trend_flag"] = "warning"

        return tracking_data

    def get_knowledge_mastery_curve(self, student_id: int, grade_code: str) -> Dict[str, List[Dict]]:
        """
        获取知识点掌握曲线数据

        Args:
            student_id: 学生 ID
            grade_code: 年级代码

        Returns:
            {知识点编码：[{"week": 周次，"score": 分数，"exam_name": 考试名称}]} 字典
        """
        all_scores = self.get_scores(student_id=student_id)

        knowledge_curve = {}

        for score_record in all_scores:
            if score_record.week <= 0:
                continue

            # 获取该周次对应的知识点
            kp_codes = get_knowledge_by_week(grade_code, score_record.week)

            for kp_code in kp_codes:
                if kp_code not in knowledge_curve:
                    knowledge_curve[kp_code] = []

                knowledge_curve[kp_code].append({
                    "week": score_record.week,
                    "score": score_record.score,
                    "exam_name": score_record.exam_name
                })

        # 按周次排序
        for kp_code in knowledge_curve:
            knowledge_curve[kp_code].sort(key=lambda x: x["week"])

        return knowledge_curve

    def diagnose_learning_trajectory(self, student_id: int, grade_code: str) -> Dict:
        """
        诊断学生学习轨迹

        Args:
            student_id: 学生 ID
            grade_code: 年级代码

        Returns:
            轨迹诊断报告，包含趋势分析、问题诊断、改进建议
        """
        tracking_data = self.get_weekly_tracking(student_id, grade_code)

        # 过滤有考试的周次
        valid_weeks = [w for w in tracking_data if w.get("avg_score") is not None]

        if len(valid_weeks) < 2:
            return {
                "status": "insufficient_data",
                "message": "数据不足，至少需要 2 次考试才能进行轨迹诊断"
            }

        # 计算趋势
        scores = [w["avg_score"] for w in valid_weeks]
        weeks = [w["week"] for w in valid_weeks]

        # 线性回归分析趋势
        n = len(scores)
        sum_x = sum(weeks)
        sum_y = sum(scores)
        sum_xy = sum(w * s for w, s in zip(weeks, scores))
        sum_x2 = sum(w ** 2 for w in weeks)

        # 斜率（趋势）
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0

        # 计算波动性
        avg_score = sum(scores) / n
        variance = sum((s - avg_score) ** 2 for s in scores) / n
        std_dev = variance ** 0.5

        # 判断趋势类型
        if slope > 2:
            trend_type = "rising"  # 上升型
            trend_desc = "成绩呈上升趋势，学习效果好"
        elif slope < -2:
            trend_type = "declining"  # 下降型
            trend_desc = "成绩呈下降趋势，需关注学习状态"
        else:
            trend_type = "stable"  # 稳定型
            trend_desc = "成绩相对稳定"

        # 判断波动性
        if std_dev < 5:
            stability = "very_stable"  # 非常稳定
            stability_desc = "发挥非常稳定"
        elif std_dev < 10:
            stability = "stable"  # 较稳定
            stability_desc = "发挥较稳定"
        elif std_dev < 15:
            stability = "fluctuating"  # 波动型
            stability_desc = "成绩波动较大，需关注"
        else:
            stability = "unstable"  # 不稳定
            stability_desc = "成绩波动很大，需重点关注"

        # 诊断问题
        issues = []
        recommendations = []

        # 分析错题知识点
        all_errors = []
        for w in tracking_data:
            all_errors.extend(w.get("error_knowledge", []))

        error_freq = {}
        for err in all_errors:
            error_freq[err] = error_freq.get(err, 0) + 1

        # 高频错题知识点
        high_freq_errors = [(kp, freq) for kp, freq in sorted(error_freq.items(), key=lambda x: x[1], reverse=True) if freq >= 2]

        if high_freq_errors:
            issues.append({
                "type": "recurring_weakness",
                "desc": f"发现 {len(high_freq_errors)} 个反复出错的知识点",
                "details": high_freq_errors[:5]
            })
            recommendations.append("针对高频错题知识点进行专项训练，建立错题本定期复习")

        # 连续下降
        decline_streak = 0
        max_decline = 0
        for i in range(1, len(scores)):
            if scores[i] < scores[i-1]:
                decline_streak += 1
                max_decline = max(max_decline, decline_streak)
            else:
                decline_streak = 0

        if max_decline >= 3:
            issues.append({
                "type": "continuous_decline",
                "desc": f"曾出现连续{max_decline}次成绩下降"
            })
            recommendations.append("分析连续下降期间学习内容难度变化，调整学习方法")

        # 低分警报
        low_scores = [w for w in valid_weeks if w["avg_score"] < 70]
        if low_scores:
            issues.append({
                "type": "low_scores",
                "desc": f"有 {len(low_scores)} 次考试低于 70 分",
                "weeks": [w["week"] for w in low_scores]
            })
            recommendations.append("针对低分考试的知识点进行复习巩固")

        # 综合诊断
        diagnosis_type = "normal"
        if trend_type == "declining" and stability in ["fluctuating", "unstable"]:
            diagnosis_type = "needs_attention"  # 需要关注
        elif trend_type == "declining" or stability == "unstable":
            diagnosis_type = "warning"  # 警告
        elif trend_type == "rising" and stability in ["stable", "very_stable"]:
            diagnosis_type = "excellent"  # 优秀

        # 生成综合建议
        if trend_type == "rising":
            recommendations.append("保持当前学习状态，适当拓展提升")
        elif trend_type == "stable":
            recommendations.append("分析薄弱知识点，寻求突破点")

        if stability == "unstable":
            recommendations.append("加强基础练习，提高稳定性")

        return {
            "status": "success",
            "trajectory_analysis": {
                "trend_type": trend_type,
                "trend_desc": trend_desc,
                "slope": round(slope, 3),
                "stability": stability,
                "stability_desc": stability_desc,
                "std_dev": round(std_dev, 2),
                "avg_score": round(avg_score, 2),
                "max_score": max(scores),
                "min_score": min(scores),
                "exam_count": n
            },
            "issues": issues,
            "recommendations": recommendations,
            "diagnosis_type": diagnosis_type,
            "tracking_summary": {
                "total_weeks": len(tracking_data),
                "valid_weeks": len(valid_weeks),
                "first_exam_week": valid_weeks[0]["week"] if valid_weeks else None,
                "last_exam_week": valid_weeks[-1]["week"] if valid_weeks else None
            }
        }


def main():
    """测试"""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    analyzer = DeepScoreAnalyzer("data")
    analyzer.load_all_data()

    print("加载的学生:", len(analyzer.student_names))

    if analyzer.student_names:
        first_student = list(analyzer.student_names.keys())[0]
        print(f"\n分析学生：{first_student} ({analyzer.student_names[first_student]})")

        report = analyzer.generate_report(first_student)
        print(report.encode('utf-8', errors='ignore').decode('utf-8'))


if __name__ == "__main__":
    main()
