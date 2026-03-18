"""
智能组卷系统模块
根据薄弱知识点自动生成针对性练习卷
"""
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class Question:
    """题目定义"""
    id: str
    knowledge_code: str
    knowledge_name: str
    question_text: str
    question_type: str  # 选择题/填空题/计算题/应用题
    difficulty: int  # 1-5
    score: int  # 分值
    answer: str
    explanation: str = ""


@dataclass
class ExamPaper:
    """试卷定义"""
    title: str
    student_name: str
    student_id: int
    generated_date: str
    questions: List[Question]
    total_score: int
    duration_minutes: int
    focus_areas: List[str]  # 重点考察知识点


# 题目模板库（按知识点分类）- 增强版
QUESTION_TEMPLATES = {
    # ==================== 一年级上册 ====================
    "G1U01": [  # 准备课
        {"type": "数数题", "text": "数一数，图中有 ( ) 个苹果", "difficulty": 1, "answer": "{a}"},
        {"type": "连线题", "text": "把数量相同的物体连起来", "difficulty": 1, "answer": "略"},
    ],
    "G1U02": [  # 位置
        {"type": "填空题", "text": "小明在小红的 ( ) 面", "difficulty": 2, "answer": "前/后"},
        {"type": "选择题", "text": "小猫在桌子的 ( ) 面。A.上 B.下 C.左", "difficulty": 2, "answer": "B"},
    ],
    "G1U03": [  # 1-5 的认识和加减法
        {"type": "计算题", "text": "计算：{a} + {b} = ?", "difficulty": 1, "answer": "{a+b}"},
        {"type": "计算题", "text": "计算：{a} - {b} = ?", "difficulty": 1, "answer": "{a-b}"},
        {"type": "填空题", "text": "{a} + ( ) = {c}", "difficulty": 2, "answer": "{c-a}"},
        {"type": "填空题", "text": "( ) - {b} = {c}", "difficulty": 2, "answer": "{c+b}"},
        {"type": "比较题", "text": "在○里填上>、<或=：{a} ○ {b}", "difficulty": 1, "answer": "{'>' if a>b else '<' if a<b else '='}"},
        {"type": "应用题", "text": "树上有{a}只鸟，又飞来{b}只，现在有几只？", "difficulty": 2, "answer": "{a+b}只"},
    ],
    "G1U04": [  # 认识图形
        {"type": "填空题", "text": "长方形有 ( ) 条边", "difficulty": 1, "answer": "4"},
        {"type": "选择题", "text": "正方形的四条边 ( )。A.一样长 B.不一样长", "difficulty": 1, "answer": "A"},
        {"type": "数数题", "text": "图中有 ( ) 个三角形", "difficulty": 2, "answer": "{a}"},
    ],
    "G1U05": [  # 6-10 的认识和加减法
        {"type": "计算题", "text": "计算：{a} + {b} = ?", "difficulty": 2, "answer": "{a+b}"},
        {"type": "计算题", "text": "计算：{a} - {b} = ?", "difficulty": 2, "answer": "{a-b}"},
        {"type": "计算题", "text": "计算：{a} + {b} + {c} = ?", "difficulty": 3, "answer": "{a+b+c}"},
        {"type": "计算题", "text": "计算：{a} - {b} - {c} = ?", "difficulty": 3, "answer": "{a-b-c}"},
        {"type": "应用题", "text": "小明有{a}个苹果，小红给了他{b}个，现在有多少个？", "difficulty": 3, "answer": "{a+b}个"},
        {"type": "应用题", "text": "停车场有{a}辆车，开走{b}辆，还剩几辆？", "difficulty": 3, "answer": "{a-b}辆"},
    ],
    "G1U06": [  # 11-20 各数的认识
        {"type": "填空题", "text": "15 里面有 ( ) 个十和 ( ) 个一", "difficulty": 2, "answer": "1,5"},
        {"type": "填空题", "text": "{a}个十和{b}个一组成的数是 ( )", "difficulty": 2, "answer": "{a*10+b}"},
        {"type": "比较题", "text": "比较大小：{a} ○ {b}", "difficulty": 2, "answer": "{'>' if a>b else '<' if a<b else '='}"},
        {"type": "计算题", "text": "计算：10 + {a} = ?", "difficulty": 2, "answer": "{10+a}"},
    ],
    "G1U07": [  # 认识钟表
        {"type": "填空题", "text": "钟面上有 ( ) 个大格", "difficulty": 1, "answer": "12"},
        {"type": "填空题", "text": "时针指向 3，分针指向 12，是 ( ) 时", "difficulty": 2, "answer": "3"},
        {"type": "选择题", "text": "分针走一圈是 ( )。A.1 小时 B.12 小时 C.1 天", "difficulty": 2, "answer": "A"},
    ],
    "G1U08": [  # 20 以内的进位加法
        {"type": "计算题", "text": "计算：9 + {a} = ?", "difficulty": 3, "answer": "{9+a}"},
        {"type": "计算题", "text": "计算：8 + {a} = ?", "difficulty": 3, "answer": "{8+a}"},
        {"type": "计算题", "text": "计算：7 + {a} = ?", "difficulty": 3, "answer": "{7+a}"},
        {"type": "填空题", "text": "9 + ( ) = 15", "difficulty": 3, "answer": "6"},
        {"type": "填空题", "text": "8 + ( ) = 17", "difficulty": 3, "answer": "9"},
        {"type": "应用题", "text": "一班有 9 个男生，又来了{a}个女生，现在一共有多少人？", "difficulty": 4, "answer": "{9+a}人"},
        {"type": "应用题", "text": "小明吃了 8 个饺子，还剩{a}个，原来有多少个？", "difficulty": 4, "answer": "{8+a}个"},
    ],
    # ==================== 一年级下册 ====================
    "G1D01": [  # 认识图形（二）
        {"type": "填空题", "text": "平行四边形有 ( ) 条边", "difficulty": 2, "answer": "4"},
        {"type": "选择题", "text": "两个完全一样的三角形可以拼成一个 ( )。A.正方形 B.长方形 C.平行四边形", "difficulty": 3, "answer": "C"},
        {"type": "数数题", "text": "图中有 ( ) 个正方形", "difficulty": 3, "answer": "{a}"},
    ],
    "G1D02": [  # 20 以内的退位减法
        {"type": "计算题", "text": "计算：15 - {a} = ?", "difficulty": 3, "answer": "{15-a}"},
        {"type": "计算题", "text": "计算：13 - {a} = ?", "difficulty": 3, "answer": "{13-a}"},
        {"type": "计算题", "text": "计算：11 - {a} = ?", "difficulty": 3, "answer": "{11-a}"},
        {"type": "填空题", "text": "17 - ( ) = 9", "difficulty": 4, "answer": "8"},
        {"type": "填空题", "text": "12 - ( ) = 5", "difficulty": 4, "answer": "7"},
        {"type": "应用题", "text": "有{a}个苹果，吃了{b}个，还剩几个？", "difficulty": 3, "answer": "{a-b}个"},
    ],
    "G1D03": [  # 100 以内数的认识
        {"type": "填空题", "text": "3 个十和 5 个一组成的数是 ( )", "difficulty": 2, "answer": "35"},
        {"type": "填空题", "text": "87 里面有 ( ) 个十和 ( ) 个一", "difficulty": 2, "answer": "8,7"},
        {"type": "比较题", "text": "比较大小：{a} ○ {b}", "difficulty": 2, "answer": "{'>' if a>b else '<' if a<b else '='}"},
        {"type": "计算题", "text": "计算：{a} + {b} = ?", "difficulty": 3, "answer": "{a+b}"},
        {"type": "计算题", "text": "计算：{a} - {b} = ?", "difficulty": 3, "answer": "{a-b}"},
        {"type": "填空题", "text": "与 59 相邻的两个数是 ( ) 和 ( )", "difficulty": 3, "answer": "58,60"},
    ],
    "G1D04": [  # 认识人民币
        {"type": "填空题", "text": "1 元 = ( ) 角", "difficulty": 1, "answer": "10"},
        {"type": "填空题", "text": "1 角 = ( ) 分", "difficulty": 1, "answer": "10"},
        {"type": "计算题", "text": "3 元 + 5 元 = ( ) 元", "difficulty": 2, "answer": "8"},
        {"type": "应用题", "text": "小明有{a}元钱，买铅笔花了{b}元，还剩多少钱？", "difficulty": 3, "answer": "{a-b}元"},
    ],
    "G1D05": [  # 100 以内的加法和减法
        {"type": "计算题", "text": "计算：{a} + {b} = ?", "difficulty": 3, "answer": "{a+b}"},
        {"type": "计算题", "text": "计算：{a} - {b} = ?", "difficulty": 3, "answer": "{a-b}"},
        {"type": "计算题", "text": "计算：{a} + {b} + {c} = ?", "difficulty": 4, "answer": "{a+b+c}"},
        {"type": "应用题", "text": "一班有{a}人，二班比一班多{b}人，二班有多少人？", "difficulty": 3, "answer": "{a+b}人"},
        {"type": "应用题", "text": "书包{a}元，文具盒{b}元，一共多少钱？", "difficulty": 3, "answer": "{a+b}元"},
    ],
    # ==================== 二年级上册 ====================
    "G2U01": [  # 长度单位
        {"type": "填空题", "text": "1 米 = ( ) 厘米", "difficulty": 1, "answer": "100"},
        {"type": "填空题", "text": "测量铅笔长度用 ( ) 作单位", "difficulty": 2, "answer": "厘米"},
        {"type": "计算题", "text": "1 米 - 30 厘米 = ( ) 厘米", "difficulty": 3, "answer": "70"},
        {"type": "应用题", "text": "一根绳子长{a}米，剪去{b}米，还剩多少米？", "difficulty": 3, "answer": "{a-b}米"},
    ],
    "G2U02": [  # 100 以内的加法
        {"type": "计算题", "text": "计算：{ab} + {cd} = ?", "difficulty": 3, "answer": "{ab+cd}"},
        {"type": "计算题", "text": "计算：{a} + {bc} = ?", "difficulty": 3, "answer": "{a+bc}"},
        {"type": "应用题", "text": "一班有{a}人，二班有{b}人，两个班一共有多少人？", "difficulty": 3, "answer": "{a+b}人"},
        {"type": "应用题", "text": "小明今年{a}岁，爸爸比他大{b}岁，爸爸今年多少岁？", "difficulty": 3, "answer": "{a+b}岁"},
    ],
    "G2U03": [  # 角的初步认识
        {"type": "填空题", "text": "一个角有 ( ) 个顶点，( ) 条边", "difficulty": 1, "answer": "1,2"},
        {"type": "选择题", "text": "三角板上有 ( ) 个直角。A.1 B.2 C.3", "difficulty": 2, "answer": "A"},
        {"type": "判断题", "text": "角的两条边越长，角就越大。（ ）", "difficulty": 2, "answer": "×"},
    ],
    "G2U04": [  # 表内乘法（一）
        {"type": "计算题", "text": "计算：{a} × {b} = ?", "difficulty": 3, "answer": "{a*b}"},
        {"type": "填空题", "text": "{a}的{b}倍是 ( )", "difficulty": 3, "answer": "{a*b}"},
        {"type": "填空题", "text": "三五 ( )", "difficulty": 2, "answer": "十五"},
        {"type": "填空题", "text": "四六 ( )", "difficulty": 2, "answer": "二十四"},
        {"type": "应用题", "text": "一个盒子装{a}个苹果，{b}个盒子一共装多少个？", "difficulty": 4, "answer": "{a*b}个"},
        {"type": "应用题", "text": "每行种{a}棵树，种了{b}行，一共种多少棵？", "difficulty": 4, "answer": "{a*b}棵"},
    ],
    "G2U05": [  # 观察物体
        {"type": "选择题", "text": "从不同方向观察同一物体，看到的形状 ( )。A.相同 B.不同 C.可能不同", "difficulty": 2, "answer": "C"},
        {"type": "填空题", "text": "观察一个正方体，最多能看到 ( ) 个面", "difficulty": 3, "answer": "3"},
    ],
    "G2U06": [  # 表内乘法（二）
        {"type": "计算题", "text": "计算：7 × {a} = ?", "difficulty": 3, "answer": "{7*a}"},
        {"type": "计算题", "text": "计算：8 × {a} = ?", "difficulty": 3, "answer": "{8*a}"},
        {"type": "计算题", "text": "计算：9 × {a} = ?", "difficulty": 3, "answer": "{9*a}"},
        {"type": "填空题", "text": "七九 ( )", "difficulty": 2, "answer": "六十三"},
        {"type": "填空题", "text": "八九 ( )", "difficulty": 2, "answer": "七十二"},
        {"type": "应用题", "text": "每本书{a}元，买{b}本需要多少钱？", "difficulty": 4, "answer": "{a*b}元"},
        {"type": "应用题", "text": "一组有{a}人，{b}组共有多少人？", "difficulty": 4, "answer": "{a*b}人"},
    ],
    "G2U07": [  # 认识时间
        {"type": "填空题", "text": "1 时 = ( ) 分", "difficulty": 1, "answer": "60"},
        {"type": "填空题", "text": "时针从 12 走到 3，走了 ( ) 时", "difficulty": 2, "answer": "3"},
        {"type": "选择题", "text": "分针从 12 走到 6，走了 ( ) 分。A.6 B.30 C.60", "difficulty": 3, "answer": "B"},
    ],
    # ==================== 二年级下册 ====================
    "G2D01": [  # 数据收集整理
        {"type": "填空题", "text": "用 ( ) 字法记录数据", "difficulty": 1, "answer": "正"},
        {"type": "统计题", "text": "根据统计表，最喜欢 ( ) 的人数最多", "difficulty": 2, "answer": "略"},
        {"type": "计算题", "text": "统计总人数：{a} + {b} + {c} = ?", "difficulty": 2, "answer": "{a+b+c}"},
    ],
    "G2D02": [  # 表内除法（一）
        {"type": "计算题", "text": "计算：{a} ÷ {b} = ?", "difficulty": 3, "answer": "{a//b}"},
        {"type": "填空题", "text": "计算：{a} ÷ {b} = {c}，想：{b} 乘 ( ) 等于{a}", "difficulty": 3, "answer": "{c}"},
        {"type": "填空题", "text": "把{a}平均分成{b}份，每份是 ( )", "difficulty": 3, "answer": "{a//b}"},
        {"type": "应用题", "text": "{a}个苹果平均分给{b}个小朋友，每人分几个？", "difficulty": 4, "answer": "{a//b}个"},
        {"type": "应用题", "text": "{a}米长的绳子，每{b}米剪一段，可以剪几段？", "difficulty": 4, "answer": "{a//b}段"},
    ],
    "G2D03": [  # 图形的运动
        {"type": "选择题", "text": "升国旗是 ( ) 现象。A.平移 B.旋转 C.对称", "difficulty": 2, "answer": "A"},
        {"type": "选择题", "text": "风扇转动是 ( ) 现象。A.平移 B.旋转", "difficulty": 2, "answer": "B"},
        {"type": "判断题", "text": "长方形和正方形都是轴对称图形。（ ）", "difficulty": 2, "answer": "√"},
    ],
    "G2D04": [  # 混合运算
        {"type": "计算题", "text": "计算：{a} + {b} × {c} = ?", "difficulty": 4, "answer": "{a+b*c}"},
        {"type": "计算题", "text": "计算：({a} + {b}) ÷ {c} = ?", "difficulty": 4, "answer": "{(a+b)//c}"},
        {"type": "计算题", "text": "计算：{a} × {b} + {c} = ?", "difficulty": 4, "answer": "{a*b+c}"},
        {"type": "判断题", "text": "判断：在混合运算中，有括号要先算括号里面的。（ ）", "difficulty": 2, "answer": "√"},
        {"type": "判断题", "text": "判断：在没有括号的算式里，乘除法优先于加减法。（ ）", "difficulty": 2, "answer": "√"},
    ],
    "G2D05": [  # 有余数的除法
        {"type": "计算题", "text": "计算：{a} ÷ {b} = ?......?", "difficulty": 4, "answer": "{a//b}......{a%b}"},
        {"type": "填空题", "text": "{a}除以{b}，商是 ( )，余数是 ( )", "difficulty": 4, "answer": "{a//b},{a%b}"},
        {"type": "填空题", "text": "在有余数的除法中，余数必须比除数 ( )", "difficulty": 3, "answer": "小"},
        {"type": "应用题", "text": "{a}个苹果，每{b}个装一盘，可以装几盘？还剩几个？", "difficulty": 5, "answer": "{a//b}盘，剩{a%b}个"},
        {"type": "应用题", "text": "有{a}人，每{b}人坐一桌，需要几张桌子？", "difficulty": 5, "answer": "{(a+b-1)//b}张"},
    ],
    "G2D06": [  # 万以内数的认识
        {"type": "填空题", "text": "10 个一百是 ( )", "difficulty": 2, "answer": "一千"},
        {"type": "填空题", "text": "{a}个千、{b}个百、{c}个十组成的数是 ( )", "difficulty": 3, "answer": "{a*1000+b*100+c*10}"},
        {"type": "比较题", "text": "比较大小：{ab} ○ {cd}", "difficulty": 2, "answer": "{'>' if ab>cd else '<' if ab<cd else '='}"},
        {"type": "计算题", "text": "计算：{a} + {b} = ?", "difficulty": 3, "answer": "{a+b}"},
        {"type": "近似数", "text": "{abc}的近似数是 ( )", "difficulty": 3, "answer": "约{a}百"},
    ],
    # ==================== 三年级上册 ====================
    "G3U01": [  # 时、分、秒
        {"type": "填空题", "text": "1 分 = ( ) 秒", "difficulty": 1, "answer": "60"},
        {"type": "计算题", "text": "2 时 = ( ) 分", "difficulty": 2, "answer": "120"},
        {"type": "应用题", "text": "小明从家到学校用了{a}分钟，往返共需要多少分钟？", "difficulty": 3, "answer": "{a*2}分钟"},
    ],
    "G3U02": [  # 万以内的加法和减法
        {"type": "计算题", "text": "计算：{a} + {b} = ?", "difficulty": 3, "answer": "{a+b}"},
        {"type": "计算题", "text": "计算：{ab} + {cd} = ?", "difficulty": 4, "answer": "{ab+cd}"},
        {"type": "计算题", "text": "计算：{a} - {b} = ?", "difficulty": 3, "answer": "{a-b}"},
        {"type": "应用题", "text": "商场上午卖出{a}台电视，下午卖出{b}台，一天共卖出多少台？", "difficulty": 4, "answer": "{a+b}台"},
        {"type": "应用题", "text": "仓库有{a}吨货物，运走{b}吨，还剩多少吨？", "difficulty": 4, "answer": "{a-b}吨"},
    ],
    "G3U03": [  # 测量
        {"type": "填空题", "text": "1 千米 = ( ) 米", "difficulty": 1, "answer": "1000"},
        {"type": "填空题", "text": "1 吨 = ( ) 千克", "difficulty": 1, "answer": "1000"},
        {"type": "计算题", "text": "5 千米 = ( ) 米", "difficulty": 2, "answer": "5000"},
        {"type": "应用题", "text": "一辆车每小时行{a}千米，{b}小时行多少千米？", "difficulty": 3, "answer": "{a*b}千米"},
    ],
    "G3U04": [  # 万以内的加法和减法（二）
        {"type": "计算题", "text": "计算：{ab} + {cd} = ?", "difficulty": 4, "answer": "{ab+cd}"},
        {"type": "计算题", "text": "计算：{abc} - {ab} = ?", "difficulty": 4, "answer": "{abc-ab}"},
        {"type": "验算题", "text": "计算并验算：{a} + {b} = ?", "difficulty": 4, "answer": "{a+b}"},
        {"type": "应用题", "text": "一本故事书{a}页，看了{b}页，还剩多少页？", "difficulty": 4, "answer": "{a-b}页"},
    ],
    "G3U05": [  # 倍的认识
        {"type": "填空题", "text": "{a}是{b}的 ( ) 倍", "difficulty": 3, "answer": "{a//b}"},
        {"type": "计算题", "text": "{a}的{b}倍是多少？", "difficulty": 3, "answer": "{a*b}"},
        {"type": "应用题", "text": "小明今年{a}岁，爸爸的年龄是他的{b}倍，爸爸今年多少岁？", "difficulty": 4, "answer": "{a*b}岁"},
        {"type": "应用题", "text": "红球有{a}个，是白球的{b}倍，白球有多少个？", "difficulty": 4, "answer": "{a//b}个"},
    ],
    "G3U06": [  # 多位数乘一位数
        {"type": "计算题", "text": "计算：{a} × {b} = ?", "difficulty": 3, "answer": "{a*b}"},
        {"type": "计算题", "text": "计算：{ab} × {c} = ?", "difficulty": 4, "answer": "{ab*c}"},
        {"type": "计算题", "text": "计算：{abc} × {a} = ?", "difficulty": 5, "answer": "{abc*a}"},
        {"type": "应用题", "text": "一箱苹果有{a}个，{b}箱共有多少个？", "difficulty": 4, "answer": "{a*b}个"},
        {"type": "应用题", "text": "每小时加工{a}个零件，{b}小时加工多少个？", "difficulty": 4, "answer": "{a*b}个"},
    ],
    "G3U07": [  # 长方形和正方形
        {"type": "计算题", "text": "长方形长{a}厘米，宽{b}厘米，周长是多少？", "difficulty": 4, "answer": "{(a+b)*2}厘米"},
        {"type": "计算题", "text": "正方形边长{a}分米，周长是多少？", "difficulty": 3, "answer": "{a*4}分米"},
        {"type": "填空题", "text": "长方形的周长 = ( ) × 2", "difficulty": 2, "answer": "长 + 宽"},
        {"type": "填空题", "text": "正方形的周长 = 边长 × ( )", "difficulty": 2, "answer": "4"},
        {"type": "应用题", "text": "一个长方形花坛，长{a}米，宽{b}米，绕花坛走一圈是多少米？", "difficulty": 4, "answer": "{(a+b)*2}米"},
    ],
    "G3U08": [  # 分数的初步认识
        {"type": "计算题", "text": "计算：1/2 + 1/4 = ?", "difficulty": 4, "answer": "3/4"},
        {"type": "计算题", "text": "计算：3/5 - 1/5 = ?", "difficulty": 3, "answer": "2/5"},
        {"type": "计算题", "text": "计算：1/3 + 1/3 = ?", "difficulty": 3, "answer": "2/3"},
        {"type": "填空题", "text": "把一个蛋糕平均分成{a}份，每份是它的 ( ) 分之 ( )", "difficulty": 3, "answer": "{a},1"},
        {"type": "比较题", "text": "比较大小：1/{a} ○ 1/{b}", "difficulty": 3, "answer": "{'>' if a<b else '<' if a>b else '='}"},
        {"type": "应用题", "text": "一个西瓜，小明吃了 1/{a}，小红吃了 1/{a}，两人共吃了多少？", "difficulty": 4, "answer": "2/{a}"},
    ],
    # ==================== 三年级下册 ====================
    "G3D01": [  # 位置与方向
        {"type": "填空题", "text": "太阳从 ( ) 方升起", "difficulty": 1, "answer": "东"},
        {"type": "填空题", "text": "与北相对的方向是 ( )", "difficulty": 1, "answer": "南"},
        {"type": "选择题", "text": "小明面向东，他的后面是 ( )。A.东 B.西 C.南 D.北", "difficulty": 2, "answer": "B"},
    ],
    "G3D02": [  # 除数是一位数的除法
        {"type": "计算题", "text": "计算：{a} ÷ {b} = ?", "difficulty": 4, "answer": "{a//b}"},
        {"type": "计算题", "text": "计算：{abc} ÷ {a} = ?", "difficulty": 4, "answer": "{abc//a}"},
        {"type": "计算题", "text": "计算：{ab} ÷ {c} = ?", "difficulty": 4, "answer": "{ab//c}......{ab%c}"},
        {"type": "应用题", "text": "{a}本书平均分给{b}个班，每班分多少本？", "difficulty": 4, "answer": "{a//b}本"},
        {"type": "应用题", "text": "{a}元钱买{b}支钢笔，平均每支多少钱？", "difficulty": 4, "answer": "{a//b}元"},
    ],
    "G3D03": [  # 统计
        {"type": "统计题", "text": "根据统计表，( ) 的数量最多", "difficulty": 2, "answer": "略"},
        {"type": "计算题", "text": "求平均数：({a} + {b} + {c}) ÷ 3 = ?", "difficulty": 3, "answer": "{(a+b+c)//3}"},
        {"type": "填空题", "text": "条形统计图可以清楚地看出各种数量的 ( )", "difficulty": 2, "answer": "多少"},
    ],
    "G3D04": [  # 两位数乘两位数
        {"type": "计算题", "text": "计算：{a} × {b} = ?", "difficulty": 4, "answer": "{a*b}"},
        {"type": "计算题", "text": "计算：{ab} × {c} = ?", "difficulty": 4, "answer": "{ab*c}"},
        {"type": "计算题", "text": "计算：{ab} × {cd} = ?", "difficulty": 5, "answer": "{ab*cd}"},
        {"type": "应用题", "text": "学校买了{a}盒粉笔，每盒{b}元，一共花了多少钱？", "difficulty": 4, "answer": "{a*b}元"},
        {"type": "应用题", "text": "每排坐{a}人，{b}排可以坐多少人？", "difficulty": 4, "answer": "{a*b}人"},
    ],
    "G3D05": [  # 面积
        {"type": "计算题", "text": "长方形长{a}米，宽{b}米，面积是多少？", "difficulty": 4, "answer": "{a*b}平方米"},
        {"type": "计算题", "text": "正方形边长{a}分米，面积是多少？", "difficulty": 3, "answer": "{a*a}平方分米"},
        {"type": "填空题", "text": "长方形的面积 = ( ) × ( )", "difficulty": 2, "answer": "长，宽"},
        {"type": "填空题", "text": "1 平方米 = ( ) 平方分米", "difficulty": 2, "answer": "100"},
        {"type": "应用题", "text": "教室长{a}米，宽{b}米，铺地砖每平方米需要{c}元，一共需要多少钱？", "difficulty": 5, "answer": "{a*b*c}元"},
    ],
    "G3D06": [  # 年、月、日
        {"type": "填空题", "text": "一年有 ( ) 个月", "difficulty": 1, "answer": "12"},
        {"type": "填空题", "text": "平年 2 月有 ( ) 天", "difficulty": 2, "answer": "28"},
        {"type": "填空题", "text": "闰年 2 月有 ( ) 天", "difficulty": 2, "answer": "29"},
        {"type": "计算题", "text": "从{a}月到{b}月经过了 ( ) 个月", "difficulty": 2, "answer": "{b-a}"},
    ],
    "G3D07": [  # 小数的初步认识
        {"type": "计算题", "text": "计算：0.{a} + 0.{b} = ?", "difficulty": 3, "answer": "0.{a+b}"},
        {"type": "计算题", "text": "计算：{a}.{b} + {c}.{d} = ?", "difficulty": 4, "answer": "{a+c}.{b+d}"},
        {"type": "计算题", "text": "计算：{a}.{b} - {c}.{d} = ?", "difficulty": 4, "answer": "{a-c}.{b-d}"},
        {"type": "比较题", "text": "比较大小：0.{a} ○ 0.{b}", "difficulty": 2, "answer": "{'>' if a>b else '<' if a<b else '='}"},
        {"type": "应用题", "text": "一支铅笔{a}.{b}元，一块橡皮{c}.{d}元，一共多少钱？", "difficulty": 4, "answer": "{a+c}.{b+d}元"},
    ],
    # ==================== 四年级上册 ====================
    "G4U01": [  # 大数的认识
        {"type": "填空题", "text": "10 个一万是 ( )", "difficulty": 2, "answer": "十万"},
        {"type": "填空题", "text": "10 个十万是 ( )", "difficulty": 2, "answer": "一百万"},
        {"type": "填空题", "text": "10 个一百万是 ( )", "difficulty": 2, "answer": "一千万"},
        {"type": "填空题", "text": "10 个一千万是 ( )", "difficulty": 2, "answer": "一亿"},
        {"type": "填空题", "text": "{a}个万和{b}个一组成的数是 ( )", "difficulty": 3, "answer": "{a*10000+b}"},
        {"type": "读数题", "text": "读出下面各数：{abc}{def}", "difficulty": 3, "answer": "略"},
        {"type": "写数题", "text": "写出下面各数：三万五千六百七十八", "difficulty": 3, "answer": "35678"},
        {"type": "比较题", "text": "比较大小：{abc000} ○ {def000}", "difficulty": 2, "answer": "{'>' if abc>def else '<' if abc<def else '='}"},
        {"type": "改写题", "text": "把{abc}0000 改写成用'万'作单位", "difficulty": 3, "answer": "{abc}万"},
        {"type": "近似数", "text": "{abcd}≈ ( ) 万（省略万位后面的尾数）", "difficulty": 4, "answer": "{ab}万"},
    ],
    "G4U02": [  # 公顷和平方千米
        {"type": "填空题", "text": "1 公顷 = ( ) 平方米", "difficulty": 2, "answer": "10000"},
        {"type": "填空题", "text": "1 平方千米 = ( ) 公顷", "difficulty": 2, "answer": "100"},
        {"type": "填空题", "text": "1 平方千米 = ( ) 平方米", "difficulty": 3, "answer": "1000000"},
        {"type": "计算题", "text": "5 公顷 = ( ) 平方米", "difficulty": 3, "answer": "50000"},
        {"type": "计算题", "text": "{a}平方千米 = ( ) 公顷", "difficulty": 3, "answer": "{a*100}公顷"},
        {"type": "应用题", "text": "一块长方形土地长{a}米，宽{b}米，面积是多少公顷？", "difficulty": 4, "answer": "{a*b//10000}公顷"},
    ],
    "G4U03": [  # 角的度量
        {"type": "填空题", "text": "直线有 ( ) 个端点", "difficulty": 1, "answer": "0"},
        {"type": "填空题", "text": "射线有 ( ) 个端点", "difficulty": 1, "answer": "1"},
        {"type": "填空题", "text": "线段有 ( ) 个端点", "difficulty": 1, "answer": "2"},
        {"type": "填空题", "text": "1 周角 = ( ) 平角", "difficulty": 2, "answer": "2"},
        {"type": "填空题", "text": "1 平角 = ( ) 直角", "difficulty": 2, "answer": "2"},
        {"type": "填空题", "text": "1 周角 = ( ) 度", "difficulty": 2, "answer": "360"},
        {"type": "选择题", "text": "大于 90°而小于 180°的角是 ( )。A.锐角 B.直角 C.钝角", "difficulty": 2, "answer": "C"},
        {"type": "计算题", "text": "已知∠1={a}°，它的余角是 ( )°", "difficulty": 3, "answer": "{90-a}°"},
        {"type": "计算题", "text": "已知∠1={a}°，它的补角是 ( )°", "difficulty": 3, "answer": "{180-a}°"},
    ],
    "G4U04": [  # 三位数乘两位数
        {"type": "计算题", "text": "计算：{abc} × {de} = ?", "difficulty": 4, "answer": "{abc*de}"},
        {"type": "计算题", "text": "计算：{ab} × {cd} = ?", "difficulty": 3, "answer": "{ab*cd}"},
        {"type": "计算题", "text": "计算：{a}00 × {b} = ?", "difficulty": 3, "answer": "{a*b}00"},
        {"type": "填空题", "text": "因数末尾有 0 的乘法，可以先把 0 前面的数 ( )，再看两个因数末尾一共有几个 0，就在积的末尾 ( )", "difficulty": 2, "answer": "相乘，添上几个 0"},
        {"type": "应用题", "text": "学校买了{a}套桌椅，每套{bc}元，一共花了多少钱？", "difficulty": 4, "answer": "{a*bc}元"},
        {"type": "应用题", "text": "一列火车每小时行{a}千米，{b}小时行多少千米？", "difficulty": 3, "answer": "{a*b}千米"},
        {"type": "应用题", "text": "某养殖场养鸡{a}只，养的鸭是鸡的{b}倍，养鸭多少只？", "difficulty": 3, "answer": "{a*b}只"},
    ],
    "G4U05": [  # 平行四边形和梯形
        {"type": "填空题", "text": "两组对边分别平行的四边形叫做 ( )", "difficulty": 2, "answer": "平行四边形"},
        {"type": "填空题", "text": "只有一组对边平行的四边形叫做 ( )", "difficulty": 2, "answer": "梯形"},
        {"type": "填空题", "text": "平行四边形具有 ( ) 性", "difficulty": 2, "answer": "不稳定"},
        {"type": "选择题", "text": "长方形和正方形是特殊的 ( )。A.三角形 B.平行四边形 C.梯形", "difficulty": 2, "answer": "B"},
        {"type": "填空题", "text": "两腰相等的梯形叫做 ( ) 梯形", "difficulty": 3, "answer": "等腰"},
        {"type": "填空题", "text": "有一个角是直角的梯形叫做 ( ) 梯形", "difficulty": 3, "answer": "直角"},
    ],
    "G4U06": [  # 除数是两位数的除法
        {"type": "计算题", "text": "计算：{abc} ÷ {ab} = ?", "difficulty": 4, "answer": "{abc//ab}......{abc%ab}"},
        {"type": "计算题", "text": "计算：{abcd} ÷ {ab} = ?", "difficulty": 5, "answer": "{abcd//ab}......{abcd%ab}"},
        {"type": "填空题", "text": "除数是两位数的除法，先看被除数的前 ( ) 位", "difficulty": 2, "answer": "两"},
        {"type": "填空题", "text": "在除法里，被除数和除数同时乘或除以相同的数（0 除外），商 ( )", "difficulty": 3, "answer": "不变"},
        {"type": "应用题", "text": "{a}千克苹果，每箱装{b}千克，需要几个箱子？", "difficulty": 4, "answer": "{(a+b-1)//b}个"},
        {"type": "应用题", "text": "学校有{a}本书，每个班分{b}本，可以分给几个班？", "difficulty": 4, "answer": "{a//b}个班"},
    ],
    "G4U07": [  # 统计
        {"type": "统计题", "text": "根据条形统计图，( ) 的数量最多", "difficulty": 2, "answer": "略"},
        {"type": "统计题", "text": "根据统计表，完成统计图", "difficulty": 3, "answer": "略"},
        {"type": "计算题", "text": "求平均数：({a} + {b} + {c} + {d}) ÷ 4 = ?", "difficulty": 3, "answer": "{(a+b+c+d)//4}"},
    ],
    # ==================== 四年级下册 ====================
    "G4D01": [  # 四则运算
        {"type": "计算题", "text": "计算：{a} + {b} × {c} = ?", "difficulty": 3, "answer": "{a+b*c}"},
        {"type": "计算题", "text": "计算：({a} + {b}) × {c} = ?", "difficulty": 4, "answer": "{(a+b)*c}"},
        {"type": "计算题", "text": "计算：{abc} ÷ ({de} - {fg}) = ?", "difficulty": 4, "answer": "{abc//(de-fg)}"},
        {"type": "判断题", "text": "判断：0 除以任何非 0 的数都得 0。（ ）", "difficulty": 2, "answer": "√"},
        {"type": "判断题", "text": "判断：任何数加 0 都得原数。（ ）", "difficulty": 1, "answer": "√"},
        {"type": "填空题", "text": "在没有括号的算式里，有乘除法和加减法，要先算 ( ) 法", "difficulty": 2, "answer": "乘除"},
    ],
    "G4D02": [  # 观察物体
        {"type": "选择题", "text": "从不同方向观察同一物体，看到的形状 ( )。A.一定相同 B.一定不同 C.可能不同", "difficulty": 2, "answer": "C"},
        {"type": "填空题", "text": "观察一个球体，从任何方向看到的都是 ( ) 形", "difficulty": 2, "answer": "圆"},
    ],
    "G4D03": [  # 运算定律
        {"type": "填空题", "text": "加法交换律：a + b = ( )", "difficulty": 2, "answer": "b + a"},
        {"type": "填空题", "text": "加法结合律：(a + b) + c = ( )", "difficulty": 2, "answer": "a + (b + c)"},
        {"type": "填空题", "text": "乘法交换律：a × b = ( )", "difficulty": 2, "answer": "b × a"},
        {"type": "填空题", "text": "乘法结合律：(a × b) × c = ( )", "difficulty": 2, "answer": "a × (b × c)"},
        {"type": "填空题", "text": "乘法分配律：(a + b) × c = ( )", "difficulty": 3, "answer": "a × c + b × c"},
        {"type": "计算题", "text": "用简便方法计算：{a} × {b} + {a} × {c} = ?", "difficulty": 4, "answer": "{a*(b+c)}"},
        {"type": "计算题", "text": "用简便方法计算：{a} + {b} + {c} = ?（凑整）", "difficulty": 3, "answer": "{a+b+c}"},
    ],
    "G4D04": [  # 小数的意义和性质
        {"type": "填空题", "text": "把 1 平均分成 10 份，每份是 ( )", "difficulty": 2, "answer": "0.1"},
        {"type": "填空题", "text": "0.{a}里面有 ( ) 个 0.1", "difficulty": 2, "answer": "a"},
        {"type": "填空题", "text": "小数的末尾添上 0 或去掉 0，小数的大小 ( )", "difficulty": 2, "answer": "不变"},
        {"type": "比较题", "text": "比较大小：0.{a} ○ 0.{b}", "difficulty": 2, "answer": "{'>' if a>b else '<' if a<b else '='}"},
        {"type": "改写题", "text": "把 0.{a}扩大到它的 10 倍是 ( )", "difficulty": 3, "answer": "{a}"},
        {"type": "改写题", "text": "把{a}缩小到它的 1/10 是 ( )", "difficulty": 3, "answer": "0.{a}"},
    ],
    "G4D05": [  # 三角形
        {"type": "填空题", "text": "三角形有 ( ) 条边，( ) 个角", "difficulty": 1, "answer": "3,3"},
        {"type": "填空题", "text": "三角形的内角和是 ( )°", "difficulty": 2, "answer": "180"},
        {"type": "填空题", "text": "三角形任意两边的和 ( ) 第三边", "difficulty": 2, "answer": "大于"},
        {"type": "选择题", "text": "等边三角形是 ( ) 三角形。A.锐角 B.直角 C.钝角", "difficulty": 2, "answer": "A"},
        {"type": "计算题", "text": "一个等腰三角形，顶角是{a}°，底角是 ( )°", "difficulty": 4, "answer": "{(180-a)//2}°"},
        {"type": "填空题", "text": "按角分类，三角形可以分为 ( ) 三角形、( ) 三角形和 ( ) 三角形", "difficulty": 2, "answer": "锐角，直角，钝角"},
    ],
    "G4D06": [  # 小数的加法和减法
        {"type": "计算题", "text": "计算：{a}.{b} + {c}.{d} = ?", "difficulty": 3, "answer": "{a+c+(b+d)/100:.2f}"},
        {"type": "计算题", "text": "计算：{a}.{bc} - {d}.{ef} = ?", "difficulty": 4, "answer": "{a+d+(bc-ef)/100:.2f}"},
        {"type": "应用题", "text": "小明买书花了{a}.{b}元，买笔花了{c}.{d}元，一共花了多少钱？", "difficulty": 3, "answer": "{a+c+(b+d)/100:.2f}元"},
        {"type": "应用题", "text": "一根绳子长{a}.{b}米，用去{c}.{d}米，还剩多少米？", "difficulty": 3, "answer": "{a-c+(b-d)/100:.2f}米"},
    ],
    "G4D07": [  # 图形的运动
        {"type": "选择题", "text": "正方形有 ( ) 条对称轴。A.2 B.4 C.无数", "difficulty": 2, "answer": "B"},
        {"type": "填空题", "text": "圆有 ( ) 条对称轴", "difficulty": 2, "answer": "无数"},
        {"type": "填空题", "text": "等边三角形有 ( ) 条对称轴", "difficulty": 2, "answer": "3"},
        {"type": "判断题", "text": "长方形和正方形都是轴对称图形。（ ）", "difficulty": 2, "answer": "√"},
    ],
    "G4D08": [  # 平均数与条形统计图
        {"type": "计算题", "text": "求平均数：{a}、{b}、{c}、{d}的平均数是多少？", "difficulty": 3, "answer": "{(a+b+c+d)//4}"},
        {"type": "统计题", "text": "根据统计表完成条形统计图", "difficulty": 3, "answer": "略"},
        {"type": "应用题", "text": "4 名同学共捐书{a}本，平均每人捐书 ( ) 本", "difficulty": 3, "answer": "{a//4}"},
    ],
    # ==================== 五年级上册 ====================
    "G5U01": [  # 小数乘法
        {"type": "计算题", "text": "计算：{a}.{b} × {c} = ?", "difficulty": 3, "answer": "{(a*10+b)*c/10:.1f}"},
        {"type": "计算题", "text": "计算：{ab} × 0.{c} = ?", "difficulty": 3, "answer": "{ab*c/10:.1f}"},
        {"type": "计算题", "text": "计算：{a}.{bc} × {d}.{ef} = ?", "difficulty": 5, "answer": "略"},
        {"type": "填空题", "text": "小数乘整数，先把小数看成 ( )，再按整数乘法计算", "difficulty": 2, "answer": "整数"},
        {"type": "填空题", "text": "一个数（0 除外）乘大于 1 的数，积比原来的数 ( )", "difficulty": 2, "answer": "大"},
        {"type": "应用题", "text": "每千克苹果{a}.{b}元，买{c}千克需要多少钱？", "difficulty": 4, "answer": "{(a*10+b)*c/10:.1f}元"},
    ],
    "G5U02": [  # 位置
        {"type": "填空题", "text": "用数对表示位置时，一般先表示 ( )，再表示 ( )", "difficulty": 2, "answer": "列，行"},
        {"type": "填空题", "text": "小明在教室的位置是 (3, 4)，表示他在第 ( ) 列第 ( ) 行", "difficulty": 2, "answer": "3,4"},
    ],
    "G5U03": [  # 小数除法
        {"type": "计算题", "text": "计算：{abc} ÷ {a} = ?", "difficulty": 3, "answer": "{abc//a}"},
        {"type": "计算题", "text": "计算：{ab} ÷ {c} = ?（保留两位小数）", "difficulty": 4, "answer": "{ab/c:.2f}"},
        {"type": "填空题", "text": "除数是小数的除法，先把除数变成 ( )，再计算", "difficulty": 2, "answer": "整数"},
        {"type": "填空题", "text": "循环小数 0.333...可以记作 ( )", "difficulty": 3, "answer": "0.˙3"},
        {"type": "应用题", "text": "{a}米布做衣服，每件衣服用布{b}米，可以做几件？", "difficulty": 4, "answer": "{a//b}件"},
        {"type": "应用题", "text": "{a}吨货物，每次运{b}吨，需要运几次？", "difficulty": 4, "answer": "{(a+b-1)//b}次"},
    ],
    "G5U04": [  # 可能性
        {"type": "选择题", "text": "抛一枚硬币，正面朝上的可能性是 ( )。A.1/2 B.1/3 C.1/4", "difficulty": 2, "answer": "A"},
        {"type": "填空题", "text": "盒子里有 3 个红球和{a}个白球，摸到红球的可能性 ( ) 摸到白球的可能性", "difficulty": 3, "answer": "{'>' if a<3 else '<' if a>3 else '='}"},
        {"type": "判断题", "text": "可能性的大小与数量有关。（ ）", "difficulty": 2, "answer": "√"},
    ],
    "G5U05": [  # 简易方程
        {"type": "填空题", "text": "用字母表示数，a × 5 可以简写为 ( )", "difficulty": 2, "answer": "5a"},
        {"type": "填空题", "text": "正方形的周长公式 C = ( )", "difficulty": 2, "answer": "4a"},
        {"type": "解方程", "text": "解方程：x + {a} = {b}", "difficulty": 3, "answer": "x={b-a}"},
        {"type": "解方程", "text": "解方程：{a}x = {b}", "difficulty": 3, "answer": "x={b//a}"},
        {"type": "解方程", "text": "解方程：{a}x + {b} = {c}", "difficulty": 4, "answer": "x={(c-b)//a}"},
        {"type": "应用题", "text": "设某数为 x，它的{a}倍加上{b}等于{c}，列方程为 ( )", "difficulty": 4, "answer": "{a}x+{b}={c}"},
    ],
    "G5U06": [  # 多边形的面积
        {"type": "计算题", "text": "平行四边形底{a}米，高{b}米，面积是多少？", "difficulty": 3, "answer": "{a*b}平方米"},
        {"type": "计算题", "text": "三角形底{a}分米，高{b}分米，面积是多少？", "difficulty": 3, "answer": "{a*b//2}平方分米"},
        {"type": "计算题", "text": "梯形上底{a}米，下底{b}米，高{c}米，面积是多少？", "difficulty": 4, "answer": "{(a+b)*c//2}平方米"},
        {"type": "填空题", "text": "平行四边形的面积 = ( ) × ( )", "difficulty": 2, "answer": "底，高"},
        {"type": "填空题", "text": "三角形的面积 = ( ) × ( ) ÷ 2", "difficulty": 2, "answer": "底，高"},
        {"type": "填空题", "text": "两个完全一样的三角形可以拼成一个 ( )", "difficulty": 2, "answer": "平行四边形"},
    ],
    "G5U07": [  # 因数与倍数
        {"type": "填空题", "text": "18 的因数有 ( )", "difficulty": 3, "answer": "1,2,3,6,9,18"},
        {"type": "填空题", "text": "{a}的最小因数是 ( )，最大因数是 ( )", "difficulty": 2, "answer": "1,{a}"},
        {"type": "填空题", "text": "{a}的最小倍数是 ( )", "difficulty": 2, "answer": "{a}"},
        {"type": "判断题", "text": "一个数的倍数一定比它的因数大。（ ）", "difficulty": 3, "answer": "×"},
        {"type": "填空题", "text": "个位上是 0、2、4、( )、( ) 的数是 2 的倍数", "difficulty": 2, "answer": "6,8"},
        {"type": "填空题", "text": "个位上是 0 或 ( ) 的数是 5 的倍数", "difficulty": 2, "answer": "5"},
        {"type": "填空题", "text": "一个数各位上的数的 ( ) 是 3 的倍数，这个数就是 3 的倍数", "difficulty": 3, "answer": "和"},
        {"type": "填空题", "text": "只有 1 和它本身两个因数的数叫做 ( )", "difficulty": 3, "answer": "质数"},
        {"type": "填空题", "text": "除了 1 和它本身还有别的因数的数叫做 ( )", "difficulty": 3, "answer": "合数"},
    ],
    # ==================== 五年级下册 ====================
    "G5D01": [  # 观察物体
        {"type": "选择题", "text": "至少需要 ( ) 个小正方体才能摆出一个稍大一些的正方体。A.2 B.4 C.8", "difficulty": 3, "answer": "C"},
        {"type": "填空题", "text": "从一个方向观察一个正方体，最多能看到 ( ) 个面", "difficulty": 2, "answer": "3"},
    ],
    "G5D02": [  # 因数与倍数（二）
        {"type": "填空题", "text": "24 和 36 的最大公因数是 ( )", "difficulty": 4, "answer": "12"},
        {"type": "填空题", "text": "6 和 8 的最小公倍数是 ( )", "difficulty": 4, "answer": "24"},
        {"type": "填空题", "text": "如果 a 是 b 的倍数，那么 a 和 b 的最大公因数是 ( )", "difficulty": 3, "answer": "b"},
        {"type": "填空题", "text": "如果 a 是 b 的倍数，那么 a 和 b 的最小公倍数是 ( )", "difficulty": 3, "answer": "a"},
        {"type": "计算题", "text": "求{a}和{b}的最大公因数", "difficulty": 4, "answer": "略"},
        {"type": "计算题", "text": "求{a}和{b}的最小公倍数", "difficulty": 4, "answer": "略"},
    ],
    "G5D03": [  # 长方体和正方体
        {"type": "填空题", "text": "长方体有 ( ) 个面，( ) 条棱，( ) 个顶点", "difficulty": 2, "answer": "6,12,8"},
        {"type": "填空题", "text": "正方体是特殊的 ( )", "difficulty": 2, "answer": "长方体"},
        {"type": "计算题", "text": "长方体长{a}厘米，宽{b}厘米，高{c}厘米，棱长总和是多少？", "difficulty": 3, "answer": "{(a+b+c)*4}厘米"},
        {"type": "计算题", "text": "正方体棱长{a}分米，棱长总和是多少？", "difficulty": 2, "answer": "{a*12}分米"},
        {"type": "计算题", "text": "长方体长{a}米，宽{b}米，高{c}米，表面积是多少？", "difficulty": 4, "answer": "{(a*b+b*c+a*c)*2}平方米"},
        {"type": "计算题", "text": "正方体棱长{a}厘米，表面积是多少？", "difficulty": 3, "answer": "{a*a*6}平方厘米"},
        {"type": "计算题", "text": "长方体长{a}米，宽{b}米，高{c}米，体积是多少？", "difficulty": 4, "answer": "{a*b*c}立方米"},
        {"type": "计算题", "text": "正方体棱长{a}分米，体积是多少？", "difficulty": 3, "answer": "{a*a*a}立方分米"},
        {"type": "填空题", "text": "1 立方米 = ( ) 立方分米", "difficulty": 2, "answer": "1000"},
        {"type": "填空题", "text": "1 立方分米 = ( ) 立方厘米", "difficulty": 2, "answer": "1000"},
        {"type": "填空题", "text": "1 升 = ( ) 毫升", "difficulty": 1, "answer": "1000"},
        {"type": "应用题", "text": "一个长方体水箱长{a}米，宽{b}米，高{c}米，能装多少立方米的水？", "difficulty": 4, "answer": "{a*b*c}立方米"},
    ],
    "G5D04": [  # 分数的意义和性质
        {"type": "填空题", "text": "把单位'1'平均分成{a}份，表示这样的{b}份的数是 ( )", "difficulty": 3, "answer": "{b}/{a}"},
        {"type": "填空题", "text": "分数与除法的关系：被除数÷除数 = ( )/( )", "difficulty": 2, "answer": "被除数，除数"},
        {"type": "填空题", "text": "分子比分母小的分数叫做 ( ) 分数", "difficulty": 2, "answer": "真"},
        {"type": "填空题", "text": "分子比分母大或分子和分母相等的分数叫做 ( ) 分数", "difficulty": 2, "answer": "假"},
        {"type": "填空题", "text": "分数的分子和分母同时乘或除以相同的数（0 除外），分数的大小 ( )", "difficulty": 2, "answer": "不变"},
        {"type": "约分题", "text": "把{a}/{ab}约分成最简分数", "difficulty": 4, "answer": "1/{b}"},
        {"type": "通分题", "text": "把 1/{a}和 1/{b}通分", "difficulty": 4, "answer": "略"},
        {"type": "比较题", "text": "比较大小：{a}/{c} ○ {b}/{c}", "difficulty": 3, "answer": "{'>' if a>b else '<' if a<b else '='}"},
    ],
    "G5D05": [  # 分数的加法和减法
        {"type": "计算题", "text": "计算：1/{a} + 2/{a} = ?", "difficulty": 3, "answer": "3/{a}"},
        {"type": "计算题", "text": "计算：{a}/{c} + {b}/{c} = ?", "difficulty": 3, "answer": "{a+b}/{c}"},
        {"type": "计算题", "text": "计算：1/2 + 1/3 = ?", "difficulty": 4, "answer": "5/6"},
        {"type": "计算题", "text": "计算：{a}/{b} - {c}/{d} = ?", "difficulty": 5, "answer": "略"},
        {"type": "应用题", "text": "小明看一本书，第一天看了全书的 1/{a}，第二天看了全书的 1/{b}，两天共看了全书的几分之几？", "difficulty": 4, "answer": "略"},
    ],
    "G5D06": [  # 图形的运动（三）
        {"type": "填空题", "text": "旋转不改变图形的 ( ) 和 ( )", "difficulty": 2, "answer": "形状，大小"},
        {"type": "填空题", "text": "旋转的三要素是：旋转中心、旋转方向和 ( )", "difficulty": 2, "answer": "旋转角度"},
        {"type": "选择题", "text": "钟面上分针的转动是 ( ) 现象。A.平移 B.旋转 C.对称", "difficulty": 2, "answer": "B"},
    ],
    "G5D07": [  # 折线统计图
        {"type": "统计题", "text": "根据统计表完成折线统计图", "difficulty": 3, "answer": "略"},
        {"type": "填空题", "text": "折线统计图不但可以表示出数量的 ( )，还可以表示出数量的 ( ) 变化情况", "difficulty": 2, "answer": "多少，增减"},
    ],
    "G5D08": [  # 数学广角 - 找次品
        {"type": "填空题", "text": "有 3 个零件，其中 1 个是次品（轻一些），用天平至少称 ( ) 次能保证找出次品", "difficulty": 3, "answer": "1"},
        {"type": "填空题", "text": "有 9 个零件，其中 1 个是次品（轻一些），用天平至少称 ( ) 次能保证找出次品", "difficulty": 4, "answer": "2"},
        {"type": "填空题", "text": "找次品时，把物品分成 ( ) 份，称的次数最少", "difficulty": 3, "answer": "3"},
    ],
    # ==================== 六年级上册 ====================
    "G6U01": [  # 分数乘法
        {"type": "计算题", "text": "计算：{a}/{b} × {c}/{d} = ?", "difficulty": 4, "answer": "{a*c}/{b*d}"},
        {"type": "计算题", "text": "计算：{a} × {b}/{c} = ?", "difficulty": 3, "answer": "{a*b}/{c}"},
        {"type": "填空题", "text": "分数乘分数，用分子相乘的积作 ( )，分母相乘的积作 ( )", "difficulty": 2, "answer": "分子，分母"},
        {"type": "填空题", "text": "乘积是 1 的两个数互为 ( )", "difficulty": 2, "answer": "倒数"},
        {"type": "应用题", "text": "一本书{a}页，小明看了全书的 1/{b}，看了多少页？", "difficulty": 4, "answer": "{a//b}页"},
        {"type": "应用题", "text": "某校有学生{a}人，其中女生占{b}/{c}，女生有多少人？", "difficulty": 4, "answer": "{a*b//c}人"},
    ],
    "G6U02": [  # 位置与方向
        {"type": "填空题", "text": "确定物体的位置需要知道 ( ) 和 ( ) 两个条件", "difficulty": 2, "answer": "方向，距离"},
        {"type": "填空题", "text": "东偏北 30°也可以说成北偏东 ( )°", "difficulty": 3, "answer": "60"},
    ],
    "G6U03": [  # 分数除法
        {"type": "计算题", "text": "计算：{a}/{b} ÷ {c}/{d} = ?", "difficulty": 4, "answer": "{a*d}/{b*c}"},
        {"type": "计算题", "text": "计算：{a} ÷ {b}/{c} = ?", "difficulty": 4, "answer": "{a*c}/{b}"},
        {"type": "填空题", "text": "除以一个不等于 0 的数，等于乘这个数的 ( )", "difficulty": 2, "answer": "倒数"},
        {"type": "解方程", "text": "解方程：{a}/{b}x = {c}", "difficulty": 4, "answer": "x={c*b/a}"},
        {"type": "应用题", "text": "已知一个数的{a}/{b}是{c}，求这个数。列式为 ( )", "difficulty": 5, "answer": "{c}÷{a}/{b}"},
    ],
    "G6U04": [  # 比
        {"type": "填空题", "text": "两个数相除又叫做两个数的 ( )", "difficulty": 2, "answer": "比"},
        {"type": "填空题", "text": "比的前项和后项同时乘或除以相同的数（0 除外），比值 ( )", "difficulty": 2, "answer": "不变"},
        {"type": "计算题", "text": "化简比：{a}:{b}", "difficulty": 3, "answer": "略"},
        {"type": "应用题", "text": "把{a}按 2:3 分配，较大部分是 ( )", "difficulty": 4, "answer": "{a*3//5}"},
        {"type": "应用题", "text": "甲乙两数的比是{a}:{b}，甲数是{c}，乙数是 ( )", "difficulty": 4, "answer": "{c*b//a}"},
    ],
    "G6U05": [  # 圆
        {"type": "填空题", "text": "圆的周长总是直径的 ( ) 倍多一些", "difficulty": 2, "answer": "3"},
        {"type": "填空题", "text": "圆的周长公式 C = ( ) 或 C = ( )", "difficulty": 3, "answer": "πd,2πr"},
        {"type": "填空题", "text": "圆的面积公式 S = ( )", "difficulty": 3, "answer": "πr²"},
        {"type": "计算题", "text": "圆的半径是{a}厘米，周长是多少？（π取 3.14）", "difficulty": 3, "answer": "{2*314*a//100}厘米"},
        {"type": "计算题", "text": "圆的半径是{a}分米，面积是多少？（π取 3.14）", "difficulty": 4, "answer": "{314*a*a//100}平方分米"},
        {"type": "填空题", "text": "圆是 ( ) 图形，有 ( ) 条对称轴", "difficulty": 2, "answer": "轴对称，无数"},
    ],
    "G6U06": [  # 百分数
        {"type": "填空题", "text": "表示一个数是另一个数的 ( ) 的数，叫做百分数", "difficulty": 2, "answer": "百分之几"},
        {"type": "填空题", "text": "把小数化成百分数，只要把小数点向 ( ) 移动两位，添上百分号", "difficulty": 2, "answer": "右"},
        {"type": "计算题", "text": "把 0.{a}化成百分数", "difficulty": 2, "answer": "{a*10}%"},
        {"type": "计算题", "text": "{a}% = ( )（填小数）", "difficulty": 2, "answer": "{a/100:.2f}"},
        {"type": "应用题", "text": "某班有学生{a}人，今天出勤{b}人，出勤率是多少？", "difficulty": 4, "answer": "{b*100//a}%"},
        {"type": "应用题", "text": "一件商品原价{a}元，打{b}折出售，现价多少元？", "difficulty": 4, "answer": "{a*b//10}元"},
    ],
    "G6U07": [  # 扇形统计图
        {"type": "统计题", "text": "根据扇形统计图，( ) 占总数的百分比最大", "difficulty": 2, "answer": "略"},
        {"type": "填空题", "text": "扇形统计图可以清楚地表示出各部分数量与 ( ) 之间的关系", "difficulty": 2, "answer": "总数"},
        {"type": "计算题", "text": "某班有{a}人，喜欢足球的占{b}%，喜欢足球的有 ( ) 人", "difficulty": 3, "answer": "{a*b//100}"},
    ],
    # ==================== 六年级下册 ====================
    "G6D01": [  # 负数
        {"type": "填空题", "text": "零上{a}摄氏度记作 ( )°C", "difficulty": 2, "answer": "+{a}"},
        {"type": "填空题", "text": "零下{a}摄氏度记作 ( )°C", "difficulty": 2, "answer": "-{a}"},
        {"type": "比较题", "text": "比较大小：-{a} ○ -{b}", "difficulty": 3, "answer": "{'>' if a<b else '<' if a>b else '='}"},
        {"type": "填空题", "text": "0 既不是 ( ) 数，也不是 ( ) 数", "difficulty": 2, "answer": "正，负"},
        {"type": "应用题", "text": "电梯上升{a}层记作 +{a} 层，下降{b}层记作 ( ) 层", "difficulty": 2, "answer": "-{b}"},
    ],
    "G6D02": [  # 百分数（二）
        {"type": "填空题", "text": "缴纳的税款叫做 ( )", "difficulty": 2, "answer": "应纳税额"},
        {"type": "填空题", "text": "税款与各种收入的比率叫做 ( )", "difficulty": 2, "answer": "税率"},
        {"type": "应用题", "text": "某商店月营业额{a}万元，按{b}%缴纳营业税，应纳税多少万元？", "difficulty": 4, "answer": "{a*b//100}万元"},
        {"type": "应用题", "text": "本金{a}元，年利率{b}%，存{c}年，利息是多少？", "difficulty": 4, "answer": "{a*b*c//100}元"},
        {"type": "填空题", "text": "商品打八五折出售，就是按原价的 ( )%出售", "difficulty": 2, "answer": "85"},
    ],
    "G6D03": [  # 圆柱与圆锥
        {"type": "填空题", "text": "圆柱的侧面积 = ( ) × ( )", "difficulty": 3, "answer": "底面周长，高"},
        {"type": "填空题", "text": "圆柱的表面积 = ( ) + ( ) × 2", "difficulty": 3, "answer": "侧面积，底面积"},
        {"type": "计算题", "text": "圆柱底面半径{a}厘米，高{b}厘米，体积是多少？", "difficulty": 4, "answer": "{314*a*a*b//100}立方厘米"},
        {"type": "填空题", "text": "圆锥的体积 = ( ) × 高 × 1/3", "difficulty": 3, "answer": "底面积"},
        {"type": "计算题", "text": "圆锥底面半径{a}分米，高{b}分米，体积是多少？", "difficulty": 5, "answer": "{314*a*a*b//300}立方分米"},
        {"type": "填空题", "text": "等底等高的圆柱体积是圆锥体积的 ( ) 倍", "difficulty": 3, "answer": "3"},
    ],
    "G6D04": [  # 比例
        {"type": "填空题", "text": "表示两个比 ( ) 的式子叫做比例", "difficulty": 2, "answer": "相等"},
        {"type": "填空题", "text": "在比例里，两个外项的积 ( ) 两个内项的积", "difficulty": 3, "answer": "等于"},
        {"type": "解比例", "text": "解比例：{a}:{b} = {c}:x", "difficulty": 4, "answer": "x={b*c/a}"},
        {"type": "应用题", "text": "图上距离：实际距离 = ( )", "difficulty": 3, "answer": "比例尺"},
        {"type": "填空题", "text": "两种相关联的量，一种量变化，另一种量也随着变化，如果这两种量中相对应的两个数的 ( ) 一定，这两种量就成正比例", "difficulty": 4, "answer": "比值"},
        {"type": "填空题", "text": "如果这两种量中相对应的两个数的 ( ) 一定，这两种量就成反比例", "difficulty": 4, "answer": "积"},
    ],
    "G6D05": [  # 数学广角 - 鸽巢问题
        {"type": "填空题", "text": "{a}只鸽子飞进{b}个鸽巢，总有一个鸽巢至少飞进 ( ) 只鸽子（a>b）", "difficulty": 4, "answer": "{(a+b-1)//b}"},
        {"type": "填空题", "text": "把{a}个苹果放进{b}个抽屉，总有一个抽屉至少放 ( ) 个苹果", "difficulty": 4, "answer": "{(a+b-1)//b}"},
        {"type": "应用题", "text": "5 只鸽子飞进 3 个鸽巢，总有一个鸽巢至少飞进 ( ) 只", "difficulty": 4, "answer": "2"},
    ],
}

# 试卷结构配置（增强版）
PAPER_STRUCTURES = {
    "基础练习": {
        "total_score": 100,
        "duration": 45,
        "type_distribution": {"计算题": 50, "填空题": 30, "应用题": 20},
        "description": "巩固基础知识，适合日常练习"
    },
    "单元检测": {
        "total_score": 100,
        "duration": 60,
        "type_distribution": {"计算题": 40, "填空题": 25, "判断题": 10, "应用题": 25},
        "description": "单元测试，全面检测本章知识点"
    },
    "专项突破": {
        "total_score": 50,
        "duration": 30,
        "type_distribution": {"计算题": 60, "应用题": 40},
        "description": "针对薄弱知识点的专项训练"
    },
    "期中模拟": {
        "total_score": 100,
        "duration": 90,
        "type_distribution": {"计算题": 35, "填空题": 20, "判断题": 10, "选择题": 15, "应用题": 20},
        "description": "期中考试模拟，综合检测半学期内容"
    },
    "期末模拟": {
        "total_score": 100,
        "duration": 90,
        "type_distribution": {"计算题": 30, "填空题": 20, "判断题": 10, "选择题": 10, "应用题": 30},
        "description": "期末考试模拟，全册知识点综合检测"
    },
    "口算速算": {
        "total_score": 100,
        "duration": 10,
        "type_distribution": {"计算题": 100},
        "description": "10 分钟快速计算训练，提高计算速度和准确率"
    },
    "易错题专练": {
        "total_score": 100,
        "duration": 60,
        "type_distribution": {"计算题": 30, "填空题": 20, "判断题": 15, "应用题": 35},
        "description": "针对高频易错题型的强化训练"
    }
}


class SmartPaperGenerator:
    """智能组卷生成器"""

    def __init__(self):
        self.question_templates = QUESTION_TEMPLATES
        self.paper_structures = PAPER_STRUCTURES

    def generate_paper(self, student_id: int, student_name: str,
                       weak_knowledge_points: List[Dict],
                       paper_type: str = "专项突破") -> ExamPaper:
        """
        生成针对性练习卷

        Args:
            student_id: 学生 ID
            student_name: 学生姓名
            weak_knowledge_points: 薄弱知识点列表
            paper_type: 试卷类型（基础练习/单元检测/专项突破）

        Returns:
            生成的试卷
        """
        if not weak_knowledge_points:
            return self._generate_empty_paper(student_id, student_name, paper_type)

        structure = self.paper_structures.get(paper_type, self.paper_structures["专项突破"])

        questions = []
        question_id = 1

        # 根据薄弱知识点分配题目
        total_points = len(weak_knowledge_points)

        for i, kp in enumerate(weak_knowledge_points):
            # 计算该知识点应分配的题目数量
            kp_weight = kp.get("error_count", 1)
            num_questions = max(2, int(structure["total_score"] / 10 * kp_weight / total_points))

            # 获取该知识点的题目模板
            templates = self.question_templates.get(kp["knowledge_code"], [])
            if not templates:
                continue

            # 生成题目
            for j in range(min(num_questions, len(templates))):
                template = templates[j % len(templates)]
                question = self._instantiate_question(
                    template=template,
                    knowledge_code=kp["knowledge_code"],
                    knowledge_name=kp.get("knowledge_name", kp["knowledge_code"]),
                    question_id=f"Q{question_id}"
                )
                if question:
                    questions.append(question)
                    question_id += 1

        # 按难度排序
        questions.sort(key=lambda q: q.difficulty)

        # 计算总分
        total_score = sum(q.score for q in questions)

        # 生成试卷
        paper = ExamPaper(
            title=f"{student_name}的{paper_type}练习卷",
            student_name=student_name,
            student_id=student_id,
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            questions=questions,
            total_score=total_score,
            duration_minutes=structure["duration"],
            focus_areas=[kp["knowledge_name"] for kp in weak_knowledge_points[:5]]
        )

        return paper

    def _instantiate_question(self, template: Dict, knowledge_code: str,
                              knowledge_name: str, question_id: str) -> Optional[Question]:
        """实例化一道题目（填充具体数值）"""
        try:
            # 生成随机数
            a = random.randint(1, 9)
            b = random.randint(1, 9)
            c = a + b
            ab = random.randint(10, 99)
            cd = random.randint(10, 99)
            abc = random.randint(100, 999)

            # 填充题目文本
            text = template["text"].format(
                a=a, b=b, c=c, ab=ab, cd=cd, abc=abc
            )

            # 计算答案
            try:
                answer = template["answer"].format(
                    a=a, b=b, c=c, ab=ab, cd=cd, abc=abc
                )
            except (KeyError, ValueError):
                answer = "略"

            return Question(
                id=question_id,
                knowledge_code=knowledge_code,
                knowledge_name=knowledge_name,
                question_text=text,
                question_type=template["type"],
                difficulty=template["difficulty"],
                score=template["difficulty"] * 5,  # 难度×5 作为分值
                answer=answer,
                explanation=""
            )
        except Exception as e:
            return None

    def _generate_empty_paper(self, student_id: int, student_name: str,
                               paper_type: str) -> ExamPaper:
        """生成空白试卷（无薄弱知识点时）"""
        return ExamPaper(
            title=f"{student_name}的{paper_type}练习卷",
            student_name=student_name,
            student_id=student_id,
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            questions=[],
            total_score=0,
            duration_minutes=30,
            focus_areas=[]
        )

    def export_paper_word(self, paper: ExamPaper, export_format: str = "markdown") -> str:
        """导出试卷为 Word/Markdown 格式文本"""
        if export_format == "markdown":
            return self._export_as_markdown(paper)
        else:
            return self._export_as_text(paper)

    def _export_as_markdown(self, paper: ExamPaper) -> str:
        """导出为 Markdown 格式"""
        # 按题型分类
        questions_by_type = {}
        for q in paper.questions:
            qtype = q.question_type
            if qtype not in questions_by_type:
                questions_by_type[qtype] = []
            questions_by_type[qtype].append(q)

        # 题型顺序和分值配置
        type_config = {
            "计算题": ("一", 5),
            "填空题": ("二", 5),
            "选择题": ("三", 3),
            "判断题": ("四", 2),
            "应用题": ("五", 10),
            "比较题": ("六", 3),
            "数数题": ("七", 3),
            "统计题": ("八", 5),
            "验算题": ("九", 5),
            "近似数": ("十", 3),
        }

        md = f"""# {paper.title}

**生成时间**: {paper.generated_date}
**建议时长**: {paper.duration_minutes}分钟
**总分**: {paper.total_score}分

**重点考察**: {', '.join(paper.focus_areas) if paper.focus_areas else '综合练习'}

---

"""
        # 按题型输出
        type_order = ["计算题", "填空题", "选择题", "判断题", "应用题", "比较题", "数数题", "统计题", "验算题", "近似数"]
        section_num = 1

        for qtype in type_order:
            if qtype in questions_by_type and questions_by_type[qtype]:
                questions = questions_by_type[qtype]
                # 获取题型配置
                config = type_config.get(qtype, (str(section_num), 5))
                type_name = config[0] if isinstance(config[0], str) else str(section_num)
                score_per_question = config[1]

                md += f"## {type_name}、{qtype}（每题{score_per_question}分）\n\n"

                for i, q in enumerate(questions, 1):
                    md += f"{i}. {q.question_text} （    分）\n\n"

                md += "\n"
                section_num += 1

        md += "\n---\n\n## 参考答案\n\n"
        for i, q in enumerate(paper.questions, 1):
            md += f"{i}. {q.answer}\n"

        return md

    def _export_as_text(self, paper: ExamPaper) -> str:
        """导出为纯文本格式"""
        text = f"""{paper.title}

生成时间：{paper.generated_date}
建议时长：{paper.duration_minutes}分钟
总分：{paper.total_score}分

重点考察：{', '.join(paper.focus_areas) if paper.focus_areas else '综合练习'}

"""
        calc_num = 1
        fill_num = 1
        app_num = 1

        for q in paper.questions:
            if q.question_type == "计算题":
                text += f"{calc_num}. {q.question_text}\n"
                calc_num += 1
            elif q.question_type == "填空题":
                text += f"{fill_num}. {q.question_text}\n"
                fill_num += 1
            elif q.question_type == "应用题":
                text += f"{app_num}. {q.question_text}\n"
                app_num += 1
            else:
                text += f"- {q.question_text}\n"

        text += "\n参考答案:\n"
        for i, q in enumerate(paper.questions, 1):
            text += f"{i}. {q.answer}\n"

        return text

    def export_answer_sheet(self, paper: ExamPaper) -> str:
        """导出答题卡"""
        md = f"""# 答题卡

**姓名**: __________  **学号**: __________  **日期**: __________

---

| 题号 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|------|---|---|---|---|---|---|---|---|---|---|
| 答案 |   |   |   |   |   |   |   |   |   |    |
| 得分 |   |   |   |   |   |   |   |   |   |    |

| 题号 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|------|----|----|----|----|----|----|----|----|----|----|
| 答案 |    |    |    |    |    |    |    |    |    |    |
| 得分 |    |    |    |    |    |    |    |    |    |    |

---

**总分**: __________

**家长签名**: __________
"""
        return md

    def get_recommendation(self, paper: ExamPaper) -> str:
        """生成练习建议"""
        if not paper.questions:
            return "暂无题目，建议先进行知识点诊断"

        # 统计难度分布
        difficulties = [q.difficulty for q in paper.questions]
        avg_difficulty = sum(difficulties) / len(difficulties)

        # 统计知识点分布
        kp_count = {}
        for q in paper.questions:
            kp_count[q.knowledge_name] = kp_count.get(q.knowledge_name, 0) + 1

        suggestion = f"""## 练习建议

**试卷难度**: {'⭐' * int(avg_difficulty)} ({avg_difficulty:.1f}/5)

**知识点分布**:
"""
        for kp, count in sorted(kp_count.items(), key=lambda x: -x[1]):
            suggestion += f"- {kp}: {count}题\n"

        suggestion += f"""
**完成建议**:
1. 建议用时：{paper.duration_minutes}分钟
2. 先做基础题，再做提高题
3. 做完后认真对答案，整理错题
4. 错题要分析原因，及时复习
"""
        return suggestion


def main():
    """测试"""
    generator = SmartPaperGenerator()

    # 模拟薄弱知识点
    weak_points = [
        {"knowledge_code": "G2U04", "knowledge_name": "表内乘法（一）", "error_count": 3},
        {"knowledge_code": "G2D02", "knowledge_name": "表内除法（一）", "error_count": 2},
    ]

    # 生成试卷
    paper = generator.generate_paper(1001, "张三", weak_points, "专项突破")

    print(f"试卷标题：{paper.title}")
    print(f"题目数量：{len(paper.questions)}")
    print(f"总分：{paper.total_score}")
    print(f"重点考察：{paper.focus_areas}")

    # 导出
    md = generator.export_paper_word(paper)
    print(f"\n试卷预览:\n{md[:500]}...")


if __name__ == "__main__":
    main()
