"""
统一数据管理服务层
所有分析模块通过此模块访问数据，不直接访问数据库

数据流:
Excel 导入 → 数据管理模块 → DataManager → 数据库
成绩录入 → 数据管理模块 → DataManager → 数据库
                          ↓
                   所有分析模块通过 DataManager 获取数据
"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

from database import get_db_connection, ExamScoreDAO
from knowledge_week_map import (
    get_week_from_exam_name,
    get_knowledge_by_week,
    get_week_description,
    WEEK_TO_KNOWLEDGE_MAP
)

# 尝试导入 streamlit 缓存（如果可用）
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

logger = logging.getLogger(__name__)


# 缓存装饰器工厂
def _cache_data(func):
    """数据查询缓存装饰器"""
    import os
    # 在测试环境下跳过缓存
    if os.environ.get('PYTEST_RUNNING'):
        return func

    if STREAMLIT_AVAILABLE:
        return st.cache_data(ttl=300)(func)  # 5 分钟缓存
    return func  # 非 Streamlit 环境下直接返回原函数


@dataclass
class ExamInfo:
    """考试信息"""
    name: str  # 考试名称 (如"周练 1"、"期末模 2")
    week: int  # 对应的周次
    date: Optional[str]  # 考试日期
    knowledge_codes: List[str] = field(default_factory=list)  # 对应的知识点编码
    description: str = ""  # 学习阶段描述


@dataclass
class StudentScore:
    """学生成绩记录"""
    student_id: int
    student_name: str
    exam_name: str
    score: float
    week: int  # 对应的周次
    error_knowledge: List[str] = field(default_factory=list)  # 错题知识点
    exam_date: str = ""  # 考试日期
    semester: str = ""  # 学期


@dataclass
class DataManagerResult:
    """数据查询结果"""
    success: bool
    data: Any
    message: str = ""
    exam_list: List[ExamInfo] = field(default_factory=list)
    students: List[Dict] = field(default_factory=list)


class DataManager:
    """
    统一数据管理服务

    提供所有分析模块的数据访问接口:
    - get_scores(): 获取成绩数据
    - get_students(): 获取学生列表
    - get_exam_list(): 获取考试列表
    - get_score_by_week(): 按周次获取成绩
    - get_knowledge_scores(): 按知识点获取成绩
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据管理器

        Args:
            db_path: 数据库路径，默认使用 data/study_math.db
        """
        self.db_path = db_path or "data/study_math.db"
        self._conn = None

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            self._conn = get_db_connection()
        return self._conn

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ==================== 基础数据查询 ====================

    @_cache_data
    def get_students(_self, class_id: Optional[int] = None) -> List[Dict]:
        """
        获取学生列表

        Args:
            class_id: 班级 ID(暂未实现班级过滤)

        Returns:
            学生列表，每个元素包含 student_id, name, grade 等
        """
        conn = _self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, name, grade FROM students ORDER BY student_id")
        rows = cursor.fetchall()
        return [
            {"student_id": row[0], "name": row[1], "grade": row[2]}
            for row in rows
        ]

    @_cache_data
    def get_exam_list(_self) -> List[ExamInfo]:
        """
        获取所有考试列表 (从数据库 + Excel 表头解析)

        Returns:
            ExamInfo 列表，包含考试名称、周次、知识点等信息
        """
        conn = _self._get_connection()
        cursor = conn.cursor()

        # 从 exam_scores 表获取所有考试名称
        cursor.execute("""
            SELECT DISTINCT exam_name, exam_date
            FROM exam_scores
            WHERE exam_name IS NOT NULL
            ORDER BY exam_name
        """)
        rows = cursor.fetchall()

        exam_list = []
        for name, date in rows:
            week = get_week_from_exam_name(name)
            knowledge_codes = []
            description = ""

            # 获取知识点 (需要知道年级，这里先返回空，后续根据学生年级填充)
            if week > 0:
                description = f"第{week}周"

            exam_list.append(ExamInfo(
                name=name,
                week=week,
                date=date,
                knowledge_codes=knowledge_codes,
                description=description
            ))

        return exam_list

    @_cache_data
    def get_scores(
        _self,
        student_id: Optional[int] = None,
        exam_name: Optional[str] = None,
        semester: Optional[str] = None
    ) -> List[StudentScore]:
        """
        获取成绩数据

        Args:
            student_id: 学生 ID(可选)
            exam_name: 考试名称 (可选)
            semester: 学期 (可选，如"一年级上册")

        Returns:
            StudentScore 列表
        """
        conn = _self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT e.student_id, s.name, e.exam_name, e.score, e.exam_date
            FROM exam_scores e
            JOIN students s ON e.student_id = s.id
            WHERE 1=1
        """
        params = []

        if student_id:
            query += " AND e.student_id = ?"
            params.append(student_id)

        if exam_name:
            query += " AND e.exam_name = ?"
            params.append(exam_name)

        if semester:
            query += " AND e.semester = ?"
            params.append(semester)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        scores = []
        for row in rows:
            exam_week = get_week_from_exam_name(row[2])  # row[2] = exam_name

            # 从 error_records 表获取错题知识点
            cursor.execute("""
                SELECT knowledge_code FROM error_records
                WHERE student_id = ? AND exam_name = ?
            """, (row[0], row[2]))
            error_rows = cursor.fetchall()
            error_kp = [r[0] for r in error_rows] if error_rows else []

            scores.append(StudentScore(
                student_id=row[0],
                student_name=row[1],
                exam_name=row[2],
                score=row[3],
                week=exam_week,
                error_knowledge=error_kp,
                exam_date=row[4] or "",
                semester=semester or ""
            ))

        return scores

    # ==================== 周次相关查询 ====================

    def get_scores_by_week(
        self,
        student_id: int,
        grade_code: str,
        start_week: int = 1,
        end_week: int = 18
    ) -> Dict[int, List[StudentScore]]:
        """
        按周次获取学生成绩

        Args:
            student_id: 学生 ID
            grade_code: 年级代码 (如"G1U")
            start_week: 起始周
            end_week: 结束周

        Returns:
            {周次：[成绩记录]} 字典
        """
        all_scores = self.get_scores(student_id=student_id)

        week_scores: Dict[int, List[StudentScore]] = {}
        for week in range(start_week, end_week + 1):
            week_scores[week] = [
                s for s in all_scores
                if s.week == week
            ]

        return week_scores

    def get_knowledge_scores(
        self,
        student_id: int,
        grade_code: str = None
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        按知识点获取成绩 (用于知识点深度分析)

        Args:
            student_id: 学生 ID
            grade_code: 年级代码 (可选，为 None 时返回所有年级)

        Returns:
            {知识点编码：[(考试名称，成绩)]} 字典
        """
        all_scores = self.get_scores(student_id=student_id)
        knowledge_scores: Dict[str, List[Tuple[str, float]]] = {}

        # 如果没有指定年级代码，遍历所有可能的年级代码
        grade_codes = [grade_code] if grade_code else ['G1U', 'G1D', 'G2U', 'G2D', 'G3U', 'G3D', 'G4U', 'G4D', 'G5U', 'G5D', 'G6U', 'G6D']

        for score in all_scores:
            if score.week <= 0:
                continue

            # 遍历所有年级代码，获取知识点
            for gc in grade_codes:
                kp_codes = get_knowledge_by_week(gc, score.week)
                for kp_code in kp_codes:
                    if kp_code not in knowledge_scores:
                        knowledge_scores[kp_code] = []
                    knowledge_scores[kp_code].append((score.exam_name, score.score))

        return knowledge_scores

    # ==================== 数据导入和录入 ====================

    def import_excel_scores(
        self,
        df: pd.DataFrame,
        source_file: str
    ) -> DataManagerResult:
        """
        导入 Excel 成绩数据

        Args:
            df: pandas DataFrame，包含学号、姓名、成绩列
            source_file: 源文件名

        Returns:
            DataManagerResult
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            imported_count = 0
            exam_names = []

            # 从文件名解析学期：如 "10032-1(2) 班上学期 math_scores.xlsx" -> "1(2) 班上学期"
            import re
            semester_match = re.search(r'(\d+\(\d+\) 班 [上下] 学期)', source_file)
            semester = semester_match.group(1) if semester_match else "1(2) 班上学期"

            # 使用默认考试日期
            default_exam_date = "2024-01-01"

            # 标准化列名：假设第 1 列是学号，第 2 列是姓名
            df_copy = df.copy()
            if len(df_copy.columns) >= 2:
                cols = list(df_copy.columns)
                if cols[0] != '学号' or cols[1] != '姓名':
                    new_cols = ['学号', '姓名'] + cols[2:]
                    df_copy.columns = new_cols

            # 解析列名：学号、姓名、考试 1、考试 2...
            score_cols = [col for col in df_copy.columns if col not in ['学号', '姓名']]

            for _, row in df_copy.iterrows():
                # 跳过学号为空的行
                if pd.isna(row.get('学号')):
                    continue

                try:
                    student_id = int(row['学号'])
                except (ValueError, TypeError):
                    continue

                student_name = row.get('姓名', '')
                if pd.isna(student_name):
                    student_name = ''

                # 确保学生存在
                cursor.execute(
                    "SELECT student_id FROM students WHERE student_id = ?",
                    (student_id,)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO students (student_id, name) VALUES (?, ?)",
                        (student_id, student_name)
                    )

                # 导入成绩
                for exam_name in score_cols:
                    score_val = row.get(exam_name)
                    if pd.isna(score_val) or score_val == '':
                        continue

                    try:
                        score = float(score_val)
                    except (ValueError, TypeError):
                        continue

                    # 检查是否已存在
                    cursor.execute("""
                        SELECT id FROM exam_scores
                        WHERE student_id = ? AND semester = ? AND exam_name = ?
                    """, (student_id, semester, exam_name))

                    if cursor.fetchone():
                        # 更新
                        cursor.execute("""
                            UPDATE exam_scores
                            SET score = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE student_id = ? AND semester = ? AND exam_name = ?
                        """, (score, student_id, semester, exam_name))
                    else:
                        # 插入
                        cursor.execute("""
                            INSERT INTO exam_scores
                            (student_id, semester, exam_name, score, exam_date)
                            VALUES (?, ?, ?, ?, ?)
                        """, (student_id, semester, exam_name, score, default_exam_date))

                    imported_count += 1
                    if exam_name not in exam_names:
                        exam_names.append(exam_name)

            conn.commit()

            return DataManagerResult(
                success=True,
                data=imported_count,
                message=f"成功导入 {imported_count} 条成绩记录",
                exam_list=[ExamInfo(name=n, week=get_week_from_exam_name(n), date=default_exam_date) for n in exam_names],
                students=self.get_students()
            )

        except Exception as e:
            logger.error(f"导入 Excel 失败：{e}")
            return DataManagerResult(
                success=False,
                data=0,
                message=f"导入失败：{str(e)}"
            )

    def add_exam_score(
        self,
        student_id: int,
        student_name: str,
        exam_name: str,
        score: float,
        error_knowledge: Optional[List[str]] = None
    ) -> DataManagerResult:
        """
        录入考试成绩

        Args:
            student_id: 学生 ID
            student_name: 学生姓名
            exam_name: 考试名称
            score: 成绩
            error_knowledge: 错题知识点列表

        Returns:
            DataManagerResult
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 确保学生存在
            cursor.execute(
                "SELECT student_id FROM students WHERE student_id = ?",
                (student_id,)
            )
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO students (student_id, name) VALUES (?, ?)",
                    (student_id, student_name)
                )

            # 检查是否已存在
            cursor.execute("""
                SELECT id FROM exam_scores
                WHERE student_id = ? AND exam_name = ?
            """, (student_id, exam_name))

            if cursor.fetchone():
                # 更新成绩
                cursor.execute("""
                    UPDATE exam_scores
                    SET score = ?, exam_date = ?
                    WHERE student_id = ? AND exam_name = ?
                """, (score, datetime.now().strftime("%Y-%m-%d"),
                      student_id, exam_name))
            else:
                # 插入新成绩
                cursor.execute("""
                    INSERT INTO exam_scores
                    (student_id, name, exam_name, score, exam_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (student_id, student_name, exam_name, score,
                      datetime.now().strftime("%Y-%m-%d")))

            # 如果有错题知识点，写入 error_records 表
            if error_knowledge:
                for kp_code in error_knowledge:
                    cursor.execute("""
                        INSERT INTO error_records
                        (student_id, knowledge_code, exam_name, error_type, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (student_id, kp_code, exam_name, "录入错题", datetime.now().strftime("%Y-%m-%d")))

            conn.commit()

            return DataManagerResult(
                success=True,
                data=score,
                message=f"成功录入 {student_name} 的 {exam_name} 成绩：{score}"
            )

        except Exception as e:
            logger.error(f"录入成绩失败：{e}")
            return DataManagerResult(
                success=False,
                data=0,
                message=f"录入失败：{str(e)}"
            )

    # ==================== 统计分析辅助方法 ====================

    def get_score_statistics(self, student_id: int) -> Dict:
        """
        获取学生成绩统计信息

        Args:
            student_id: 学生 ID

        Returns:
            统计信息字典
        """
        scores = self.get_scores(student_id=student_id)

        if not scores:
            return {}

        score_values = [s.score for s in scores]
        import numpy as np

        return {
            "count": len(scores),
            "average": round(np.mean(score_values), 2),
            "max": max(score_values),
            "min": min(score_values),
            "std": round(np.std(score_values), 2),
        }

    def get_weekly_average(self, student_id: int, grade_code: str) -> Dict[int, float]:
        """
        获取学生每周平均分 (用于趋势分析)

        Args:
            student_id: 学生 ID
            grade_code: 年级代码

        Returns:
            {周次：平均分} 字典
        """
        week_scores = self.get_scores_by_week(student_id, grade_code)

        weekly_avg = {}
        for week, scores in week_scores.items():
            if scores:
                weekly_avg[week] = round(
                    sum(s.score for s in scores) / len(scores), 2
                )

        return weekly_avg


# ==================== 快捷函数 ====================

def get_data_manager() -> DataManager:
    """获取 DataManager 实例"""
    return DataManager()
