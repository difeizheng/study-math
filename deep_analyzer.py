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
}


class DeepScoreAnalyzer:
    """深度成绩分析器"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.students_df: Optional[pd.DataFrame] = None
        self.semester_data: Dict[str, pd.DataFrame] = {}
        self.student_names: Dict[int, str] = {}
        self.knowledge_points = KNOWLEDGE_SYSTEM

    def load_all_data(self) -> pd.DataFrame:
        """加载所有数据"""
        all_scores = []

        for file in sorted(self.data_dir.glob("*.xlsx")):
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

        return self.students_df

    def _parse_semester_name(self, filename: str) -> str:
        """解析学期名称"""
        match = re.search(r'\d+-(\d+\(\d+\) 班 [上下] 学期)', filename)
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

    def analyze_knowledge_mastery(self, student_id: int) -> Dict[str, Dict]:
        """分析学生对各知识点的掌握程度"""
        if self.students_df is None:
            return {}

        student_data = self.students_df[self.students_df['学号'] == student_id]
        if student_data.empty:
            return {}

        # 统计每个知识点的得分情况
        knowledge_scores: Dict[str, List[float]] = {}

        # 遍历每个学期的数据
        for semester_name, semester_df in self.semester_data.items():
            student_semester = semester_df[semester_df['学号'] == student_id]
            if student_semester.empty:
                continue

            # 遍历该学期的所有考试
            for col in semester_df.columns:
                if col in ['学号', '姓名']:
                    continue

                score = student_semester[col].values[0] if len(student_semester) > 0 else None
                if pd.isna(score):
                    continue

                # 获取考试对应的知识点
                knowledge_points = self.map_exam_to_knowledge(col, semester_name)

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
        """计算基础统计信息"""
        if self.students_df is None:
            return {}

        student_data = self.students_df[self.students_df['学号'] == student_id]
        if student_data.empty:
            return {}

        all_scores = []
        for col in student_data.columns:
            if col not in ['学号', '姓名', '_semester']:
                value = student_data[col].values[0]
                if pd.notna(value):
                    all_scores.append(value)

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
