"""
Excel 数据导入模块
从 Excel 成绩表自动提取错题和知识点掌握情况
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

from database import StudentDAO, ErrorRecordDAO
from deep_analyzer import KNOWLEDGE_SYSTEM, PRACTICE_MAPPING


class ExcelDataImporter:
    """Excel 数据导入器"""

    def __init__(self):
        self.knowledge_system = KNOWLEDGE_SYSTEM
        self.practice_mapping = PRACTICE_MAPPING

    def load_excel(self, file_path: str) -> pd.DataFrame:
        """加载 Excel 文件"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")

        # 自动识别 Excel 格式
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)

        return df

    def extract_students_from_excel(self, df: pd.DataFrame,
                                     semester: str) -> List[Dict]:
        """
        从 Excel 中提取学生信息

        Args:
            df: Excel 数据框
            semester: 学期名称（如 "1(2) 班上 学期"）

        Returns:
            学生信息列表
        """
        students = []

        # 支持多种列名："学号"、"序号"、"学生 ID"等
        student_id_col = None
        name_col = None

        for col in df.columns:
            if '学号' in col or '序号' in col or '学生 ID' in col:
                student_id_col = col
            if '姓名' in col or '名字' in col:
                name_col = col

        if not student_id_col or not name_col:
            return students

        # 提取年级信息
        grade_match = re.search(r'(\d)\(', semester)
        grade = f"{int(grade_match.group(1))}年级" if grade_match else "未知"

        semester_name = "上" if "上" in semester else "下" if "下" in semester else "未知"

        for _, row in df.iterrows():
            try:
                student_id = int(row[student_id_col])
                name = str(row[name_col])

                # 检查是否已存在
                existing = StudentDAO.get_student(student_id)
                if not existing:
                    StudentDAO.add_student(student_id, name, grade, semester_name)
                    students.append({
                        'student_id': student_id,
                        'name': name,
                        'grade': grade,
                        'semester': semester_name
                    })
            except (ValueError, TypeError):
                continue

        return students

    def import_errors_from_excel(self, file_path: str, semester: str,
                                  error_threshold: float = 85) -> Dict:
        """
        从 Excel 成绩表导入错题

        Args:
            file_path: Excel 文件路径
            semester: 学期名称
            error_threshold: 错题阈值（低于此分数视为错题）

        Returns:
            导入统计信息
        """
        df = self.load_excel(file_path)
        import_stats = {
            'total_errors': 0,
            'students': 0,
            'exams': 0
        }

        # 提取学生信息
        students = self.extract_students_from_excel(df, semester)
        import_stats['students'] = len(students)

        # 获取考试列（排除学号/序号、姓名）
        id_cols = ['学号', '序号', '学生 ID', '姓名', '名字']
        exam_columns = [col for col in df.columns if col not in id_cols]
        import_stats['exams'] = len(exam_columns)

        # 找到学号列名
        student_id_col = None
        for col in df.columns:
            if '学号' in col or '序号' in col or '学生 ID' in col:
                student_id_col = col
                break

        # 遍历每个学生
        for _, row in df.iterrows():
            try:
                student_id = int(row.get(student_id_col)) if student_id_col else None
                if student_id is None:
                    continue
            except (ValueError, TypeError):
                continue

            # 遍历每个考试
            for exam_col in exam_columns:
                score = row.get(exam_col)
                if pd.isna(score):
                    continue

                try:
                    score = float(score)
                except (ValueError, TypeError):
                    continue

                # 如果分数低于阈值，记录为错题
                if score < error_threshold:
                    # 从考试名称推断知识点
                    knowledge_info = self._extract_knowledge_from_exam(exam_col, semester)

                    if knowledge_info:
                        ErrorRecordDAO.add_error_record(
                            student_id=student_id,
                            exam_name=exam_col,
                            exam_date=datetime.now().strftime("%Y-%m-%d"),
                            knowledge_code=knowledge_info['code'],
                            knowledge_name=knowledge_info['name'],
                            error_type=self._guess_error_type(score),
                            error_description=f"考试得分：{score}分",
                            score=score
                        )
                        import_stats['total_errors'] += 1

        return import_stats

    def _extract_knowledge_from_exam(self, exam_name: str,
                                      semester: str) -> Optional[Dict]:
        """从考试名称推断知识点"""
        # 提取学期代码
        code_match = re.search(r'(\d+)-', semester)
        semester_code = code_match.group(1) if code_match else None

        if not semester_code:
            return None

        # 从练习号推断知识点
        practice_match = re.search(r'[练习单元](\d+)', exam_name)
        if practice_match:
            practice_num = int(practice_match.group(1))

            # 查找对应的知识点
            if semester_code in self.practice_mapping:
                practice_map = self.practice_mapping[semester_code]
                if practice_num in practice_map:
                    kp_codes = practice_map[practice_num]
                    if kp_codes:
                        first_code = kp_codes[0]
                        kp_info = self.knowledge_system.get(first_code)
                        return {
                            'code': first_code,
                            'name': kp_info.name if kp_info else first_code
                        }

        # 期中/期末考试
        if "期中" in exam_name:
            # 返回该学期前几个知识点
            prefix = f"G{semester_code[0]}{'U' if '上' in semester else 'D'}"
            for code, kp in self.knowledge_system.items():
                if code.startswith(prefix):
                    return {'code': code, 'name': kp.name}

        if "期末" in exam_name:
            # 返回该学期综合知识点
            prefix = f"G{semester_code[0]}{'U' if '上' in semester else 'D'}"
            for code, kp in reversed(list(self.knowledge_system.items())):
                if code.startswith(prefix):
                    return {'code': code, 'name': kp.name}

        return None

    def _guess_error_type(self, score: float) -> str:
        """根据分数猜测错误类型"""
        if score >= 80:
            return "计算粗心"  # 分数较高，可能是粗心
        elif score >= 60:
            return "概念混淆"  # 中等分数，可能是概念不清
        else:
            return "知识性错误"  # 低分，可能是知识性错误

    def batch_import(self, data_dir: str) -> Dict:
        """
        批量导入 data 目录下的所有 Excel 文件

        Args:
            data_dir: 数据目录路径

        Returns:
            导入统计信息
        """
        data_path = Path(data_dir)
        if not data_path.exists():
            return {'error': '目录不存在'}

        total_stats = {
            'files_processed': 0,
            'total_errors': 0,
            'total_students': 0,
            'total_exams': 0
        }

        # 查找所有 Excel 文件
        excel_files = list(data_path.glob('*.xlsx')) + list(data_path.glob('*.xls'))

        for file_path in excel_files:
            # 从文件名提取学期信息
            filename = file_path.name
            semester_match = re.search(r'(\d+)\((\d)\) 班 ([上下]) 学期', filename)

            if semester_match:
                grade = semester_match.group(1)
                semester = f"{grade}({semester_match.group(2)}) 班 {semester_match.group(3)} 学期"

                try:
                    stats = self.import_errors_from_excel(str(file_path), semester)
                    total_stats['files_processed'] += 1
                    total_stats['total_errors'] += stats.get('total_errors', 0)
                    total_stats['total_students'] += stats.get('students', 0)
                    total_stats['total_exams'] += stats.get('exams', 0)
                except Exception as e:
                    print(f"导入 {filename} 失败：{e}")
            else:
                print(f"跳过文件 {filename}：无法识别学期信息")

        return total_stats


def main():
    """测试"""
    from database import init_database
    init_database()

    importer = ExcelDataImporter()

    # 测试批量导入
    data_dir = Path(__file__).parent / "data"
    if data_dir.exists():
        stats = importer.batch_import(str(data_dir))
        print(f"批量导入完成：{stats}")
    else:
        print(f"数据目录不存在：{data_dir}")


if __name__ == "__main__":
    main()
