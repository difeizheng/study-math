"""
数据持久化模块
使用 SQLite 存储学生信息、错题记录、学习习惯分析等数据
"""
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib


# 数据库文件路径
DB_PATH = Path(__file__).parent / "data" / "study_math.db"


def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    # 确保 data 目录存在
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 返回字典格式行
    return conn


def init_database():
    """初始化数据库，创建所有表"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 学生表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            grade TEXT NOT NULL,
            semester TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 错题记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            exam_name TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            knowledge_code TEXT NOT NULL,
            knowledge_name TEXT NOT NULL,
            error_type TEXT NOT NULL,
            error_description TEXT,
            score REAL,
            question_text TEXT,
            student_answer TEXT,
            correct_answer TEXT,
            error_analysis TEXT,
            review_count INTEGER DEFAULT 0,
            last_review_date TEXT,
            next_review_date TEXT,
            is_mastered INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # 学习习惯分析表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            analysis_date TEXT NOT NULL,
            error_distribution TEXT,
            habit_scores TEXT,
            main_issues TEXT,
            suggestions TEXT,
            trends TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # 能力成长档案表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ability_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            analysis_date TEXT NOT NULL,
            ability_scores TEXT,
            overall_level TEXT,
            strongest_ability TEXT,
            weakest_ability TEXT,
            radar_data TEXT,
            report_content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # 错题本导出记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_book_exports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            export_date TEXT NOT NULL,
            export_content TEXT,
            export_format TEXT DEFAULT 'markdown',
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # 考试成绩表（用于存储手动录入的成绩）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            semester TEXT NOT NULL,
            exam_name TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            score REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_student ON error_records(student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_knowledge ON error_records(knowledge_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_date ON error_records(exam_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_student ON habit_analysis(student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ability_student ON ability_records(student_id)")

    conn.commit()
    conn.close()
    print("数据库初始化完成")


# ==================== 学生数据访问对象 ====================

class StudentDAO:
    """学生数据访问对象"""

    @staticmethod
    def add_student(student_id: int, name: str, grade: str, semester: str) -> bool:
        """添加学生"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO students (student_id, name, grade, semester)
                VALUES (?, ?, ?, ?)
            """, (student_id, name, grade, semester))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def get_student(student_id: int) -> Optional[Dict]:
        """获取学生信息"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all_students() -> List[Dict]:
        """获取所有学生"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students ORDER BY grade, semester, student_id")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def update_student(student_id: int, name: str = None, grade: str = None,
                       semester: str = None) -> bool:
        """更新学生信息"""
        conn = get_db_connection()
        updates = []
        values = []

        if name:
            updates.append("name = ?")
            values.append(name)
        if grade:
            updates.append("grade = ?")
            values.append(grade)
        if semester:
            updates.append("semester = ?")
            values.append(semester)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(student_id)

            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE students SET {', '.join(updates)}
                WHERE student_id = ?
            """, values)
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            return success

        conn.close()
        return False

    @staticmethod
    def delete_student(student_id: int) -> bool:
        """删除学生（级联删除相关记录）"""
        conn = get_db_connection()
        cursor = conn.cursor()

        # 先删除相关记录
        cursor.execute("DELETE FROM error_records WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM habit_analysis WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM ability_records WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM error_book_exports WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success


# ==================== 错题记录数据访问对象 ====================

class ErrorRecordDAO:
    """错题记录数据访问对象"""

    @staticmethod
    def add_error_record(student_id: int, exam_name: str, exam_date: str,
                         knowledge_code: str, knowledge_name: str,
                         error_type: str, error_description: str = "",
                         score: float = None, question_text: str = "",
                         student_answer: str = "", correct_answer: str = "",
                         error_analysis: str = "") -> int:
        """添加错题记录"""
        conn = get_db_connection()
        cursor = conn.cursor()

        # 计算下次复习日期（艾宾浩斯遗忘曲线）
        next_review = ErrorRecordDAO._calculate_next_review_date(exam_date, 0)

        cursor.execute("""
            INSERT INTO error_records
            (student_id, exam_name, exam_date, knowledge_code, knowledge_name,
             error_type, error_description, score, question_text, student_answer,
             correct_answer, error_analysis, next_review_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, exam_name, exam_date, knowledge_code, knowledge_name,
              error_type, error_description, score, question_text, student_answer,
              correct_answer, error_analysis, next_review))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id

    @staticmethod
    def get_errors_by_student(student_id: int) -> List[Dict]:
        """获取学生的所有错题"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM error_records
            WHERE student_id = ?
            ORDER BY exam_date DESC, id DESC
        """, (student_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_errors_by_knowledge(student_id: int, knowledge_code: str) -> List[Dict]:
        """获取学生在特定知识点的错题"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM error_records
            WHERE student_id = ? AND knowledge_code = ?
            ORDER BY exam_date DESC
        """, (student_id, knowledge_code))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_review_due_records(student_id: int) -> List[Dict]:
        """获取需要复习的错题"""
        conn = get_db_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT * FROM error_records
            WHERE student_id = ? AND next_review_date <= ? AND is_mastered = 0
            ORDER BY next_review_date ASC
        """, (student_id, today))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def mark_as_reviewed(record_id: int) -> bool:
        """标记为已复习"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE error_records
            SET review_count = review_count + 1,
                last_review_date = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (record_id,))
        conn.commit()
        success = cursor.rowcount > 0

        if success:
            # 更新下次复习日期
            cursor.execute("SELECT review_count, exam_date FROM error_records WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if row:
                review_count = row["review_count"]
                exam_date = row["exam_date"]
                next_review = ErrorRecordDAO._calculate_next_review_date(exam_date, review_count)
                cursor.execute("""
                    UPDATE error_records SET next_review_date = ? WHERE id = ?
                """, (next_review, record_id))
                conn.commit()

        conn.close()
        return success

    @staticmethod
    def mark_as_mastered(record_id: int) -> bool:
        """标记为已掌握"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE error_records
            SET is_mastered = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (record_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    @staticmethod
    def get_error_statistics(student_id: int) -> Dict:
        """获取错题统计信息"""
        conn = get_db_connection()
        cursor = conn.cursor()

        # 总数统计
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_mastered = 1 THEN 1 ELSE 0 END) as mastered,
                   SUM(CASE WHEN is_mastered = 0 THEN 1 ELSE 0 END) as remaining
            FROM error_records WHERE student_id = ?
        """, (student_id,))
        total_stats = cursor.fetchone()

        # 按错误类型统计
        cursor.execute("""
            SELECT error_type, COUNT(*) as count
            FROM error_records WHERE student_id = ?
            GROUP BY error_type
        """, (student_id,))
        error_types = cursor.fetchall()

        # 按知识点统计
        cursor.execute("""
            SELECT knowledge_code, knowledge_name, COUNT(*) as count
            FROM error_records WHERE student_id = ?
            GROUP BY knowledge_code
            ORDER BY count DESC
        """, (student_id,))
        knowledge_stats = cursor.fetchall()

        conn.close()

        return {
            "total": total_stats["total"],
            "mastered": total_stats["mastered"],
            "remaining": total_stats["remaining"],
            "by_error_type": [dict(row) for row in error_types],
            "by_knowledge": [dict(row) for row in knowledge_stats]
        }

    @staticmethod
    def _calculate_next_review_date(exam_date: str, review_count: int) -> str:
        """计算下次复习日期（艾宾浩斯遗忘曲线）"""
        # 复习间隔：1, 2, 4, 7, 15, 30 天
        intervals = [1, 2, 4, 7, 15, 30]

        from datetime import timedelta
        base_date = datetime.strptime(exam_date, "%Y-%m-%d")

        if review_count < len(intervals):
            next_date = base_date + timedelta(days=intervals[review_count])
        else:
            # 超过 6 次复习后，每 30 天复习一次
            next_date = base_date + timedelta(days=30)

        return next_date.strftime("%Y-%m-%d")


# ==================== 学习习惯分析数据访问对象 ====================

class HabitAnalysisDAO:
    """学习习惯分析数据访问对象"""

    @staticmethod
    def save_analysis(student_id: int, analysis_date: str,
                      error_distribution: Dict, habit_scores: Dict,
                      main_issues: List, suggestions: List, trends: Dict) -> int:
        """保存学习习惯分析结果"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO habit_analysis
            (student_id, analysis_date, error_distribution, habit_scores,
             main_issues, suggestions, trends)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, analysis_date,
              json.dumps(error_distribution, ensure_ascii=False),
              json.dumps(habit_scores, ensure_ascii=False),
              json.dumps(main_issues, ensure_ascii=False),
              json.dumps(suggestions, ensure_ascii=False),
              json.dumps(trends, ensure_ascii=False)))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id

    @staticmethod
    def get_latest_analysis(student_id: int) -> Optional[Dict]:
        """获取最新的分析结果"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM habit_analysis
            WHERE student_id = ?
            ORDER BY analysis_date DESC
            LIMIT 1
        """, (student_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            data = dict(row)
            # 解析 JSON 字段
            data["error_distribution"] = json.loads(data["error_distribution"])
            data["habit_scores"] = json.loads(data["habit_scores"])
            data["main_issues"] = json.loads(data["main_issues"])
            data["suggestions"] = json.loads(data["suggestions"])
            data["trends"] = json.loads(data["trends"])
            return data
        return None

    @staticmethod
    def get_analysis_history(student_id: int) -> List[Dict]:
        """获取分析历史"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM habit_analysis
            WHERE student_id = ?
            ORDER BY analysis_date DESC
        """, (student_id,))
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            data = dict(row)
            data["error_distribution"] = json.loads(data["error_distribution"])
            data["habit_scores"] = json.loads(data["habit_scores"])
            result.append(data)
        return result


# ==================== 能力成长档案数据访问对象 ====================

class AbilityRecordDAO:
    """能力成长档案数据访问对象"""

    @staticmethod
    def save_record(student_id: int, analysis_date: str,
                    ability_scores: Dict, overall_level: str,
                    strongest_ability: str, weakest_ability: str,
                    radar_data: List, report_content: str) -> int:
        """保存能力成长记录"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ability_records
            (student_id, analysis_date, ability_scores, overall_level,
             strongest_ability, weakest_ability, radar_data, report_content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, analysis_date,
              json.dumps(ability_scores, ensure_ascii=False),
              overall_level, strongest_ability, weakest_ability,
              json.dumps(radar_data, ensure_ascii=False),
              report_content))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id

    @staticmethod
    def get_latest_record(student_id: int) -> Optional[Dict]:
        """获取最新的能力记录"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ability_records
            WHERE student_id = ?
            ORDER BY analysis_date DESC
            LIMIT 1
        """, (student_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            data = dict(row)
            data["ability_scores"] = json.loads(data["ability_scores"])
            data["radar_data"] = json.loads(data["radar_data"])
            return data
        return None

    @staticmethod
    def get_record_history(student_id: int) -> List[Dict]:
        """获取能力记录历史"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ability_records
            WHERE student_id = ?
            ORDER BY analysis_date DESC
        """, (student_id,))
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            data = dict(row)
            data["ability_scores"] = json.loads(data["ability_scores"])
            data["radar_data"] = json.loads(data["radar_data"])
            result.append(data)
        return result


# ==================== 考试成绩数据访问对象 ====================

class ExamScoreDAO:
    """考试成绩数据访问对象"""

    @staticmethod
    def add_score(student_id: int, semester: str, exam_name: str,
                  exam_date: str, score: float) -> int:
        """添加考试成绩"""
        conn = get_db_connection()
        cursor = conn.cursor()

        # 先检查是否已存在相同记录
        cursor.execute("""
            SELECT id FROM exam_scores
            WHERE student_id = ? AND semester = ? AND exam_name = ? AND exam_date = ?
        """, (student_id, semester, exam_name, exam_date))

        existing = cursor.fetchone()

        if existing:
            # 更新已有记录
            cursor.execute("""
                UPDATE exam_scores SET score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (score, existing["id"]))
            record_id = existing["id"]
        else:
            # 插入新记录
            cursor.execute("""
                INSERT INTO exam_scores (student_id, semester, exam_name, exam_date, score)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, semester, exam_name, exam_date, score))
            record_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return record_id

    @staticmethod
    def get_scores_by_student(student_id: int, semester: str = None) -> List[Dict]:
        """获取学生的考试成绩"""
        conn = get_db_connection()
        cursor = conn.cursor()

        if semester:
            cursor.execute("""
                SELECT * FROM exam_scores
                WHERE student_id = ? AND semester = ?
                ORDER BY exam_date DESC
            """, (student_id, semester))
        else:
            cursor.execute("""
                SELECT * FROM exam_scores
                WHERE student_id = ?
                ORDER BY semester, exam_date DESC
            """, (student_id,))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_scores_by_semester(semester: str, exam_name: str) -> List[Dict]:
        """获取某学期某考试的成绩列表"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, s.name as student_name
            FROM exam_scores e
            JOIN students s ON e.student_id = s.student_id
            WHERE e.semester = ? AND e.exam_name = ?
            ORDER BY e.score DESC
        """, (semester, exam_name))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_all_scores() -> List[Dict]:
        """获取所有成绩"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, s.name as student_name
            FROM exam_scores e
            JOIN students s ON e.student_id = s.student_id
            ORDER BY e.semester, e.exam_name, e.score DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


# 初始化数据库
if __name__ == "__main__":
    init_database()
    print("数据库已创建：", DB_PATH)
