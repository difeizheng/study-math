"""
分析器基类模块
提取 ScoreAnalyzer 和 DeepScoreAnalyzer 的公共方法，减少代码重复
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

from database import ExamScoreDAO


class BaseAnalyzer:
    """
    分析器基类

    提供公共方法供 ScoreAnalyzer 和 DeepScoreAnalyzer 继承：
    - _normalize_semester_name(): 标准化学期名称
    - _get_exam_sort_key(): 考试名称排序
    - refresh_entered_scores(): 刷新录入成绩缓存
    - get_class_stats(): 班级统计数据
    - _parse_semester_name(): 解析学期名称
    - _normalize_columns(): 标准化列名
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.students_df: Optional[pd.DataFrame] = None
        self.semester_data: Dict[str, pd.DataFrame] = {}
        self.student_names: Dict[int, str] = {}
        self.entered_scores_cache: Dict[int, List[Dict]] = {}
        self.exam_order: List[str] = []

    def _normalize_semester_name(self, semester: str) -> str:
        """
        标准化学期名称，去除 -math_scores 等后缀

        Args:
            semester: 学期名称，如 "10032-1(2) 班上学期数学考试分数"

        Returns:
            标准化后的学期名称，如 "1(2) 班上学期"
        """
        match = re.search(r'(\d+\(\d+\).*?学期)', semester)
        if match:
            return match.group(1).replace(' ', '')
        return semester

    def _sort_semesters(self, semesters: List[str]) -> List[str]:
        """
        对学期列表进行排序，按年级和学期类型排序

        排序规则：
        1. 先按年级排序（1 班 -> 2 班 -> 3 班...）
        2. 同一年级内，上学期在前，下学期在后

        例如：1(2) 班上学期 < 1(2) 班下学期 < 2(2) 班上学期 < 2(2) 班下学期

        Args:
            semesters: 学期名称列表

        Returns:
            排序后的学期列表
        """
        def semester_sort_key(semester: str) -> Tuple[int, int]:
            # 提取年级和学期类型
            # 匹配格式："1(2) 班上学期" 或 "10(1) 班下学期"
            match = re.search(r'(\d+)\(\d+\)\s*班 ([上下]) 学期', semester)
            if match:
                grade = int(match.group(1))  # 年级
                semester_type = match.group(2)  # '上' or '下'
                # 上学期=0, 下学期=1，确保上学期在前
                semester_order = 0 if semester_type == '上' else 1
                return (grade, semester_order)
            # 无法解析的返回最大值，排到最后
            return (999, 999)

        return sorted(semesters, key=semester_sort_key)

    def _get_exam_sort_key(self, exam_name: str) -> Tuple[int, int]:
        """
        从考试名称提取排序关键字，支持自然排序

        例如：周练 1 -> (1, 1), 周练 10 -> (1, 10), 期末模 1 -> (9, 1)
        返回 (类型权重，序号)，确保周练 2 排在周练 10 前面

        Args:
            exam_name: 考试名称

        Returns:
            (类型权重，序号) 元组
        """
        type_weights = {
            '周练': 1,
            '练习': 2,
            '单元': 3,
            '期中': 8,
            '期末模': 9,
            '期末': 10,
        }

        for exam_type, weight in type_weights.items():
            if exam_name.startswith(exam_type):
                num_part = exam_name[len(exam_type):]
                try:
                    num = int(num_part)
                    return (weight, num)
                except ValueError:
                    return (weight, 0)

        return (99, 0)

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

        for col in self.students_df.columns:
            if col not in ['学号', '姓名']:
                exam_cols.add(col)

        if semester:
            normalized_semester = self._normalize_semester_name(semester)
            exam_cols = {
                col for col in exam_cols
                if self._normalize_semester_name(col.split('_', 1)[0] if '_' in col else col) == normalized_semester
            }

        for col in sorted(exam_cols, key=lambda x: self._get_exam_sort_key(x.split('_', 1)[1] if '_' in x else x)):
            exam_name = col.split('_', 1)[1] if '_' in col else col
            sem_name = self._normalize_semester_name(col.split('_', 1)[0] if '_' in col else col)

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

    def _parse_semester_name(self, filename: str) -> str:
        """
        从文件名解析学期名称

        Args:
            filename: Excel 文件名

        Returns:
            学期名称
        """
        match = re.search(r'(\d+-\d+\(\d+\) 班.+学期)', filename)
        if match:
            return match.group(1)
        return filename.replace("-math_scores.xlsx", "")

    def _normalize_columns(self, df: pd.DataFrame, semester: str) -> pd.DataFrame:
        """
        标准化列名，添加学期前缀

        Args:
            df: Excel 数据 DataFrame
            semester: 学期名称

        Returns:
            标准化后的 DataFrame
        """
        if '学号' not in df.columns:
            df.columns = ['学号', '姓名'] + list(df.columns[2:])

        score_columns = [col for col in df.columns if col not in ['学号', '姓名']]
        for col in score_columns:
            df[col] = df[col].apply(
                lambda x: None if (isinstance(x, str) and (x.strip() == '' or x.lower() == 'nan')) else x
            )

        rename_dict = {col: f"{semester}_{col}" for col in score_columns}
        df = df.rename(columns=rename_dict)

        return df

    def load_excel_data(self) -> pd.DataFrame:
        """
        加载所有 Excel 数据并合并

        Returns:
            合并后的学生数据 DataFrame
        """
        all_scores = []
        excel_files = []

        uploads_dir = self.data_dir / "uploads"
        if uploads_dir.exists():
            excel_files.extend(sorted(uploads_dir.glob("*.xlsx")))

        excel_files.extend(sorted(self.data_dir.glob("*.xlsx")))

        for file in excel_files:
            semester_name = self._parse_semester_name(file.name)
            df = pd.read_excel(file)

            original_cols = list(df.columns)
            if len(original_cols) >= 2:
                exam_cols = original_cols[2:]
                self.exam_order = [f"{semester_name}_{col}" for col in exam_cols]

            df = self._normalize_columns(df, semester_name)

            if '学号' in df.columns and '姓名' in df.columns:
                for _, row in df.iterrows():
                    if pd.notna(row['学号']):
                        self.student_names[int(row['学号'])] = row['姓名']

            all_scores.append(df)
            self.semester_data[semester_name] = df

        if all_scores:
            combined_df = pd.concat(all_scores, ignore_index=True)
            self.students_df = combined_df.groupby(['学号', '姓名'], as_index=False).first()

        self.refresh_entered_scores()

        return self.students_df

    def get_student_list(self) -> List[Tuple[int, str]]:
        """
        获取所有学生列表

        Returns:
            学生列表 [(学号，姓名), ...]
        """
        return sorted(self.student_names.items(), key=lambda x: x[0])
