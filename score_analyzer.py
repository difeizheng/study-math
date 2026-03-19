"""
成绩分析系统核心模块
用于加载、处理和分析学生数学成绩数据
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

from database import ExamScoreDAO
from score_config import get_score_distribution_for_scores, load_score_ranges


class ScoreAnalyzer:
    """成绩分析器"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.students_df: Optional[pd.DataFrame] = None
        self.semester_data: Dict[str, pd.DataFrame] = {}
        self.student_names: Dict[int, str] = {}
        self.entered_scores_cache: Dict[int, List[Dict]] = {}  # 录入成绩缓存 {学号：[成绩]}
        self.exam_order: List[str] = []  # 保存 Excel 中考试列的原始顺序

    def _normalize_semester_name(self, semester: str) -> str:
        """标准化学期名称，去除 -math_scores 等后缀"""
        import re
        # 匹配格式：10032-1(2) 班上学期数学考试分数 或 1(2) 班上学期
        # 提取如 "1(2) 班上学期" 格式
        match = re.search(r'(\d+\(\d+\).*?学期)', semester)
        if match:
            return match.group(1).replace(' ', '')
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

    def load_all_data(self) -> pd.DataFrame:
        """加载所有学期的数据并合并"""
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

            # 保存原始列顺序（排除学号、姓名）
            original_cols = list(df.columns)
            if len(original_cols) >= 2:
                # 假设前两列是学号和姓名
                exam_cols = original_cols[2:]
                # 添加学期前缀后保存
                self.exam_order = [f"{semester_name}_{col}" for col in exam_cols]

            # 标准化列名
            df = self._normalize_columns(df, semester_name)

            # 存储学生姓名映射
            if '学号' in df.columns and '姓名' in df.columns:
                for _, row in df.iterrows():
                    if pd.notna(row['学号']):
                        self.student_names[int(row['学号'])] = row['姓名']

            all_scores.append(df)
            self.semester_data[semester_name] = df

        # 合并所有数据 - 按学号和姓名分组，将不同学期的数据合并到同一行
        if all_scores:
            # 首先纵向拼接所有数据
            combined_df = pd.concat(all_scores, ignore_index=True)

            # 按学号和姓名分组，将每组的数据合并到一行
            # 使用 first() 保留每个分组的第一行（非空值会覆盖空值）
            self.students_df = combined_df.groupby(['学号', '姓名'], as_index=False).first()

        # 刷新录入成绩缓存
        self.refresh_entered_scores()

        return self.students_df

    def _parse_semester_name(self, filename: str) -> str:
        """从文件名解析学期名称"""
        # 匹配模式：10032-1(2) 班上学期数学考试分数-math_scores.xlsx
        # 使用 .+ 代替 [上下] 以正确匹配中文字符
        match = re.search(r'(\d+-\d+\(\d+\) 班.+学期)', filename)
        if match:
            return match.group(1)
        return filename.replace("-math_scores.xlsx", "")

    def _normalize_columns(self, df: pd.DataFrame, semester: str) -> pd.DataFrame:
        """标准化列名，添加学期前缀"""
        # 确保有学号和姓名列
        if '学号' not in df.columns:
            df.columns = ['学号', '姓名'] + list(df.columns[2:])

        # 清理成绩列中的空值（空格、'nan' 字符串等）
        score_columns = [col for col in df.columns if col not in ['学号', '姓名']]
        for col in score_columns:
            # 将空格、'nan' 字符串等替换为真正的 NaN
            df[col] = df[col].apply(lambda x: None if (isinstance(x, str) and (x.strip() == '' or x.lower() == 'nan')) else x)

        # 为除学号姓名外的所有列添加学期前缀
        rename_dict = {col: f"{semester}_{col}" for col in score_columns}
        df = df.rename(columns=rename_dict)

        return df

    def get_student_list(self) -> List[Tuple[int, str]]:
        """获取所有学生列表"""
        return sorted(self.student_names.items(), key=lambda x: x[0])

    def get_merged_scores(self, student_id: int, semester: str = None) -> Dict[str, float]:
        """获取合并后的成绩（Excel + 录入）"""
        scores = {}

        # 1. 从 Excel 获取成绩
        if self.students_df is not None:
            student_data = self.students_df[self.students_df['学号'] == student_id]
            if not student_data.empty:
                for col in self.students_df.columns:
                    if col not in ['学号', '姓名']:
                        # 如果指定了学期，只返回该学期的成绩
                        if semester:
                            normalized_semester = self._normalize_semester_name(semester)
                            col_semester = self._normalize_semester_name(col.split('_', 1)[0] if '_' in col else col)
                            if col_semester != normalized_semester:
                                continue
                        value = student_data[col].values[0]
                        if pd.notna(value):
                            scores[col] = float(value)

        # 2. 合并录入的成绩
        if student_id in self.entered_scores_cache:
            for es in self.entered_scores_cache[student_id]:
                if semester:
                    # 使用标准化后的学期名称进行模糊匹配
                    normalized_semester = self._normalize_semester_name(semester)
                    es_normalized = self._normalize_semester_name(es['semester'])
                    if es_normalized != normalized_semester:
                        continue
                # 使用标准化后的学期名称构建键名，以便与 Excel 成绩去重
                normalized_es_semester = self._normalize_semester_name(es['semester'])
                key = f"{normalized_es_semester}_{es['exam_name']}"

                # 检查是否已存在（包括使用原始学期名称的 Excel 成绩）
                if key not in scores:
                    # 再检查是否有 Excel 成绩使用相同的标准化名称
                    exam_exists = False
                    for existing_key in scores.keys():
                        existing_norm_semester = self._normalize_semester_name(existing_key.split('_', 1)[0] if '_' in existing_key else existing_key)
                        existing_exam = existing_key.split('_', 1)[1] if '_' in existing_key else existing_key
                        if existing_norm_semester == normalized_es_semester and existing_exam == es['exam_name']:
                            exam_exists = True
                            break
                    if not exam_exists and es['score'] is not None:
                        scores[key] = float(es['score'])

        return scores

    def get_student_scores(self, student_id: int) -> pd.DataFrame:
        """获取指定学生的所有成绩（使用合并后的成绩）"""
        if self.students_df is None:
            return pd.DataFrame()

        # 使用合并后的成绩
        scores = self.get_merged_scores(student_id)

        if not scores:
            return pd.DataFrame()

        return pd.DataFrame([scores])

    def get_score_trend(self, student_id: int, semester: str = None) -> pd.DataFrame:
        """获取学生成绩趋势（包含录入的成绩）"""
        # 获取合并后的成绩
        scores = self.get_merged_scores(student_id, semester)

        trends = []
        for col, value in scores.items():
            if pd.notna(value):
                # 提取学期和考试名称
                parts = col.split('_', 1)
                if len(parts) == 2:
                    raw_sem, exam = parts[0], parts[1]
                    # 使用标准化后的学期名称，确保与前端传入的 semester 参数一致
                    sem = self._normalize_semester_name(raw_sem)
                    trends.append({
                        '学期': sem,
                        '考试': exam,
                        '分数': value,
                        '_sort_key': self._get_exam_sort_key(exam)  # 用于排序
                    })

        df = pd.DataFrame(trends)

        # 按考试顺序排序
        if not df.empty:
            df = df.sort_values('_sort_key').drop('_sort_key', axis=1).reset_index(drop=True)

        return df

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

        # 计算每次考试的统计数据
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

    def calculate_statistics(self, student_id: int, semester: str = None) -> Dict:
        """计算学生统计信息（包含录入的成绩）"""
        # 获取合并后的成绩
        scores = self.get_merged_scores(student_id, semester)

        # 获取所有分数
        all_scores = []
        for col, value in scores.items():
            # 检查是否为有效数字
            if pd.notna(value) and value != ' ':
                try:
                    all_scores.append(float(value))
                except (ValueError, TypeError):
                    pass

        if not all_scores:
            return {}

        scores_array = np.array(all_scores)

        return {
            '平均分': round(float(scores_array.mean()), 2),
            '最高分': round(float(scores_array.max()), 2),
            '最低分': round(float(scores_array.min()), 2),
            '标准差': round(float(scores_array.std()), 2),
            '考试次数': len(all_scores),
            '优秀率': round(float((scores_array >= 90).sum()) / len(all_scores) * 100, 1),
            '及格率': round(float((scores_array >= 60).sum()) / len(all_scores) * 100, 1),
        }

    def compare_students(self, student_ids: List[int]) -> pd.DataFrame:
        """比较多个学生的成绩"""
        if self.students_df is None:
            return pd.DataFrame()

        comparison_data = []
        for sid in student_ids:
            stats = self.calculate_statistics(sid)
            if stats:
                stats['学号'] = sid
                stats['姓名'] = self.student_names.get(sid, 'Unknown')
                comparison_data.append(stats)

        return pd.DataFrame(comparison_data)

    def get_semester_summary(self, semester: str) -> Dict:
        """获取学期汇总统计"""
        if semester not in self.semester_data:
            return {}

        df = self.semester_data[semester]
        summary = {}

        # 找出所有考试列
        exam_cols = [col for col in df.columns if col not in ['学号', '姓名']]

        for exam in exam_cols:
            scores = df[exam].dropna()
            if len(scores) > 0:
                summary[exam] = {
                    '平均分': round(scores.mean(), 2),
                    '最高分': round(scores.max(), 2),
                    '最低分': round(scores.min(), 2),
                    '参加人数': len(scores)
                }

        return summary

    def analyze_weak_areas(self, student_id: int) -> List[Dict]:
        """分析学生薄弱环节（使用合并后的成绩）"""
        # 使用合并后的成绩获取趋势
        trend_df = self.get_score_trend(student_id)
        if trend_df.empty:
            return []

        # 按考试分组，找出表现较差的考试类型
        weak_areas = []
        exam_stats = trend_df.groupby('考试')['分数'].agg(['mean', 'min', 'count'])

        for exam_name in exam_stats.index:
            stats = exam_stats.loc[exam_name]
            avg_score = stats['mean']
            if avg_score < 85:  # 低于 85 分视为薄弱
                weak_areas.append({
                    '考试类型': exam_name,
                    '平均分': round(avg_score, 2),
                    '最低分': round(stats['min'], 2),
                    '考试次数': int(stats['count'])
                })

        return sorted(weak_areas, key=lambda x: x['平均分'])

    def get_score_distribution(self, student_id: int, semester=None) -> Dict:
        """
        获取分数分布（使用合并后的成绩）

        Args:
            student_id: 学生 ID
            semester: 学期名称或学期列表（可选）
                     - str: 只统计该学期
                     - list: 统计选中的多个学期
                     - None: 统计所有学期

        Returns:
            分数段分布字典，如 {'90-100': 15, '80-89': 5, ...}
        """
        # 获取所有成绩（不过滤学期）
        scores = self.get_merged_scores(student_id, semester=None)

        if not scores:
            return {}

        # 收集所有有效分数
        all_scores = []
        for col, value in scores.items():
            if pd.notna(value):
                # 提取学期
                parts = col.split('_', 1)
                if len(parts) == 2:
                    raw_sem = parts[0]
                    col_semester = self._normalize_semester_name(raw_sem)

                    # 根据 semester 参数过滤
                    should_include = False
                    if semester is None:
                        # 不过滤，包含所有
                        should_include = True
                    elif isinstance(semester, str):
                        # 单个学期
                        norm_semester = self._normalize_semester_name(semester)
                        if col_semester == norm_semester:
                            should_include = True
                    elif isinstance(semester, list):
                        # 多个学期
                        norm_semesters = [self._normalize_semester_name(s) for s in semester]
                        if col_semester in norm_semesters:
                            should_include = True

                    if should_include:
                        all_scores.append(value)
                else:
                    # 没有学期信息的成绩，直接加入
                    all_scores.append(value)

        if not all_scores:
            return {}

        # 使用配置的分数段计算分布
        return get_score_distribution_for_scores(all_scores)

    def get_score_alerts(self, student_id: int) -> List[Dict]:
        """获取成绩预警信息（使用合并后的成绩）"""
        alerts = []

        # 使用合并后的成绩
        scores_dict = self.get_merged_scores(student_id)

        if not scores_dict:
            return alerts

        # 获取所有有效分数
        scores = [v for k, v in scores_dict.items() if pd.notna(v)]

        if len(scores) < 3:
            return alerts  # 数据不足，无法预警

        # 1. 退步预警：检查最近 3 次成绩趋势
        recent_scores = scores[-3:] if len(scores) >= 3 else scores
        if len(recent_scores) >= 3:
            if recent_scores[0] > recent_scores[1] > recent_scores[2]:
                alerts.append({
                    'type': '退步预警',
                    'level': 'warning',
                    'message': f'最近 3 次成绩连续下降：{recent_scores[0]}→{recent_scores[1]}→{recent_scores[2]}',
                    'suggestion': '建议关注学习状态，查找原因并及时辅导'
                })
            elif recent_scores[0] - recent_scores[-1] >= 10:
                alerts.append({
                    'type': '退步预警',
                    'level': 'warning',
                    'message': f'近期成绩下滑超过 10 分',
                    'suggestion': '建议分析错题，找出薄弱环节'
                })

        # 2. 波动预警：检查成绩稳定性
        if len(scores) >= 5:
            std_dev = pd.Series(scores).std()
            if std_dev > 15:
                min_score = min(scores)
                max_score = max(scores)
                alerts.append({
                    'type': '波动预警',
                    'level': 'info',
                    'message': f'成绩波动较大（标准差{std_dev:.1f}），最高{max_score}分，最低{min_score}分',
                    'suggestion': '建议分析低分试卷，找出知识盲点'
                })

        # 3. 低分预警
        low_scores = [s for s in scores if s < 70]
        if len(low_scores) >= 2:
            alerts.append({
                'type': '低分预警',
                'level': 'error',
                'message': f'发现{len(low_scores)}次 70 分以下成绩',
                'suggestion': '建议系统复习基础知识，加强练习'
            })

        # 4. 优秀预警（连续高分后的松懈可能）
        high_count = sum(1 for s in scores[-5:] if s >= 95)
        if high_count >= 4 and len(scores) >= 5:
            alerts.append({
                'type': '优秀提醒',
                'level': 'success',
                'message': f'最近 5 次考试中有{high_count}次 95 分以上，表现优秀！',
                'suggestion': '保持良好状态，可适当挑战拓展题目'
            })

        return alerts

    def get_class_analysis(self, semester: str = None) -> Dict:
        """获取班级整体分析（使用合并后的成绩）"""
        if self.students_df is None:
            return {}

        # 获取所有学生
        all_students = self.get_student_list()
        if not all_students:
            return {}

        # 加载自定义分数段配置
        score_ranges = load_score_ranges()

        # 计算班级整体统计
        class_stats = {
            'total_students': len(all_students),
            'scores': [],  # 所有学生的所有成绩（用于直方图）
            'all_scores_for_distribution': [],  # 所有成绩（用于分数段统计）
            'distribution': {r['name']: 0 for r in score_ranges},
            'students_above_90': 0,
            'students_below_60': 0,
        }

        # 每个学生计算平均分（使用合并后的成绩）
        student_avgs = []
        for student_id, name in all_students:
            scores = self.get_merged_scores(student_id, semester)
            score_values = [v for k, v in scores.items() if pd.notna(v)]

            if score_values:
                avg = sum(score_values) / len(score_values)
                student_avgs.append(avg)
                class_stats['scores'].append(avg)

                if avg >= 90:
                    class_stats['students_above_90'] += 1
                if avg < 60:
                    class_stats['students_below_60'] += 1

                # 将该学生的所有成绩加入分数段统计
                for score in score_values:
                    class_stats['all_scores_for_distribution'].append(score)
                    for r in score_ranges:
                        if r['min'] <= score <= r['max']:
                            class_stats['distribution'][r['name']] += 1
                            break

        if student_avgs:
            class_stats['class_avg'] = round(sum(student_avgs) / len(student_avgs), 2)
            class_stats['highest_avg'] = round(max(student_avgs), 2)
            class_stats['lowest_avg'] = round(min(student_avgs), 2)
            class_stats['pass_rate'] = round((1 - class_stats['students_below_60'] / len(student_avgs)) * 100, 1)
            class_stats['excellent_rate'] = round(class_stats['students_above_90'] / len(student_avgs) * 100, 1)
        else:
            class_stats['class_avg'] = 0
            class_stats['highest_avg'] = 0
            class_stats['lowest_avg'] = 0
            class_stats['pass_rate'] = 0
            class_stats['excellent_rate'] = 0

        return class_stats

    def get_score_rank(self, student_id: int, semester: str = None) -> Dict:
        """获取学生班级排名（使用合并后的成绩）"""
        if self.students_df is None:
            return {}

        # 计算该学生平均分（使用合并后的成绩）
        scores = self.get_merged_scores(student_id, semester)
        student_score_values = [v for k, v in scores.items() if pd.notna(v)]

        if not student_score_values:
            return {}

        student_avg = sum(student_score_values) / len(student_score_values)

        # 计算所有学生平均分并排名（使用合并后的成绩）
        all_avgs = []
        for sid, name in self.get_student_list():
            sid_scores = self.get_merged_scores(sid, semester)
            sid_score_values = [v for k, v in sid_scores.items() if pd.notna(v)]
            if sid_score_values:
                avg = sum(sid_score_values) / len(sid_score_values)
                all_avgs.append({'学号': sid, '姓名': name, '平均分': avg})

        # 按平均分降序排名
        all_avgs.sort(key=lambda x: x['平均分'], reverse=True)

        rank = 1
        for i, s in enumerate(all_avgs):
            if s['学号'] == student_id:
                rank = i + 1
                break

        return {
            'rank': rank,
            'total': len(all_avgs),
            'student_avg': round(student_avg, 2),
            'top_10_percent': rank <= len(all_avgs) * 0.1,
            'top_3': rank <= 3,
        }

    def analyze_student_development(self, student_id: int) -> Dict:
        """
        学生学业发展综合分析 (SAI - Student Academic Development Index)
        从定量和定性两个维度进行宏观分析
        使用合并后的成绩（Excel + 录入）
        """
        if self.students_df is None:
            return {'error': '未加载 Excel 数据，请先导入学生成绩'}

        # 获取合并后的所有成绩
        scores_dict = self.get_merged_scores(student_id)

        if not scores_dict:
            return {'error': '该学生没有成绩数据'}

        # 收集所有有效成绩
        scores = []
        score_with_semester = []  # (学期，考试，分数)

        for col, value in scores_dict.items():
            if pd.notna(value):
                try:
                    score = float(value)
                    scores.append(score)
                    # 提取学期和考试名称
                    parts = col.split('_', 1)
                    if len(parts) == 2:
                        sem, exam = parts[0], parts[1]
                        score_with_semester.append((sem, exam, score))
                except (ValueError, TypeError):
                    pass

        if len(scores) < 3:
            return {'error': '数据不足，至少需要 3 次考试成绩'}

        # ========== 定量分析 ==========
        scores_series = pd.Series(scores)

        # 1. 集中趋势
        mean_score = scores_series.mean()
        median_score = scores_series.median()

        # 2. 离散程度
        std_score = scores_series.std()
        cv_score = std_score / mean_score if mean_score > 0 else 0  # 变异系数
        range_score = scores_series.max() - scores_series.min()

        # 3. 分布形态
        from scipy import stats
        skewness = stats.skew(scores) if len(scores) >= 3 else 0
        kurtosis = stats.kurtosis(scores) if len(scores) >= 4 else 0

        # 4. 趋势分析（线性回归斜率）
        if len(scores) >= 2:
            x = np.arange(len(scores))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, scores)
        else:
            slope = 0
            r_value = 0

        # 5. 等级划分
        excellent_rate = (scores_series >= 90).sum() / len(scores) * 100
        pass_rate = (scores_series >= 60).sum() / len(scores) * 100

        # 6. 最近趋势（近 5 次）
        recent_5 = scores[-5:] if len(scores) >= 5 else scores
        recent_avg = sum(recent_5) / len(recent_5)
        prev_avg = sum(scores[:-5]) / len(scores[:-5]) if len(scores) > 5 else mean_score
        trend_change = recent_avg - prev_avg

        # ========== 定性评价 ==========
        # 学业水平等级
        if mean_score >= 90:
            level = '优秀'
            level_desc = '学业成就突出，远超课程标准要求'
        elif mean_score >= 80:
            level = '良好'
            level_desc = '学业成就较好，达到课程标准要求'
        elif mean_score >= 70:
            level = '中等'
            level_desc = '学业成就一般，基本达到课程标准要求'
        elif mean_score >= 60:
            level = '及格'
            level_desc = '学业成就勉强，部分达到课程标准要求'
        else:
            level = '待提高'
            level_desc = '学业成就不足，需加强基础学习'

        # 稳定性评价
        if cv_score < 0.05:
            stability = '非常稳定'
        elif cv_score < 0.10:
            stability = '较稳定'
        elif cv_score < 0.15:
            stability = '一般'
        else:
            stability = '波动较大'

        # 发展趋势评价
        if slope > 2:
            trend = '快速进步'
            trend_desc = '学习状态持续向好，进步明显'
        elif slope > 0:
            trend = '稳步进步'
            trend_desc = '学习状态良好，有进步趋势'
        elif slope > -2:
            trend = '基本稳定'
            trend_desc = '学习状态平稳，需保持警惕'
        elif slope > -5:
            trend = '有所退步'
            trend_desc = '学习状态下滑，需引起重视'
        else:
            trend = '明显退步'
            trend_desc = '学习状态堪忧，需及时干预'

        # 综合发展指数 (SAI)
        # 公式优化：SAI = 0.5*标准化均分 + 0.15*稳定性 + 0.15*趋势 + 0.1*近期趋势 + 0.1*优秀率
        # 增加平均分权重，减少趋势权重，使 SAI 更接近真实水平
        normalized_mean = mean_score / 100  # 标准化到 0-1
        stability_score = max(0, 1 - cv_score)
        trend_score = max(0, min(1, 0.5 + slope / 5))  # 斜率标准化，减小分母使影响更合理
        recent_trend_score = max(0, min(1, 0.5 + trend_change / 5))  # 标准化到 0-1

        sai = (0.50 * normalized_mean +      # 50% 学业水平
               0.15 * stability_score +       # 15% 稳定性
               0.10 * trend_score +           # 10% 长期趋势
               0.10 * recent_trend_score +    # 10% 近期趋势
               0.15 * (excellent_rate / 100)) # 15% 优秀率

        # ========== 综合分析结论 ==========
        analysis_summary = self._generate_macro_analysis(
            level, stability, trend, sai,
            mean_score, cv_score, slope, trend_change
        )

        return {
            'quantitative': {
                'mean': round(mean_score, 2),
                'median': round(median_score, 2),
                'std': round(std_score, 2),
                'cv': round(cv_score, 4),
                'range': round(range_score, 1),
                'skewness': round(skewness, 2),
                'kurtosis': round(kurtosis, 2),
                'slope': round(slope, 3),
                'correlation': round(r_value, 3),
                'excellent_rate': round(excellent_rate, 1),
                'pass_rate': round(pass_rate, 1),
                'recent_avg': round(recent_avg, 2),
                'trend_change': round(trend_change, 2),
            },
            'qualitative': {
                'level': level,
                'level_desc': level_desc,
                'stability': stability,
                'trend': trend,
                'trend_desc': trend_desc,
            },
            'sai': {
                'index': round(sai * 100, 1),
                'grade': self._sai_to_grade(sai),
                'percentile': self._estimate_percentile(sai),
                'components': {  # SAI 组成部分，用于对比分析
                    'mean_score': round(0.50 * normalized_mean * 100, 2),
                    'stability_score': round(0.15 * stability_score * 100, 2),
                    'trend_score': round(0.10 * trend_score * 100, 2),
                    'recent_trend_score': round(0.10 * recent_trend_score * 100, 2),
                    'excellent_rate_score': round(0.15 * (excellent_rate / 100) * 100, 2),
                }
            },
            'sai_raw': {  # 原始数据用于对比
                'normalized_mean': round(normalized_mean, 4),
                'stability_score': round(stability_score, 4),
                'trend_score': round(trend_score, 4),
                'recent_trend_score': round(recent_trend_score, 4),
                'excellent_rate': round(excellent_rate, 1),
            },
            'summary': analysis_summary,
            'recommendations': self._generate_recommendations(
                level, stability, trend, cv_score, slope, trend_change
            )
        }

    def _sai_to_grade(self, sai: float) -> str:
        """将 SAI 指数转换为等级"""
        if sai >= 0.85:
            return 'A+'
        elif sai >= 0.75:
            return 'A'
        elif sai >= 0.65:
            return 'B+'
        elif sai >= 0.55:
            return 'B'
        elif sai >= 0.45:
            return 'C+'
        elif sai >= 0.35:
            return 'C'
        else:
            return 'D'

    def _estimate_percentile(self, sai: float) -> int:
        """估算 SAI 百分位（简化版本）"""
        # 假设 SAI 近似正态分布
        from scipy import stats
        return int(stats.norm.cdf(sai, 0.5, 0.15) * 100)

    def _generate_macro_analysis(self, level: str, stability: str, trend: str,
                                  sai: float, mean: float, cv: float,
                                  slope: float, trend_change: float) -> str:
        """生成宏观分析结论"""
        summary = f"该生学业发展综合指数 (SAI) 为{sai*100:.1f}，属于{level}水平。\n\n"

        # 学业水平描述
        summary += f"【学业成就】平均分{mean:.1f}分，"
        if level == '优秀':
            summary += "表现突出，远超同龄人平均水平。\n"
        elif level == '良好':
            summary += "表现较好，处于同龄人中上水平。\n"
        elif level == '中等':
            summary += "表现一般，达到基本要求。\n"
        else:
            summary += "有较大提升空间。\n"

        # 稳定性描述
        summary += f"【稳定性】成绩{stability}（变异系数{cv:.2f}），"
        if cv < 0.05:
            summary += "学习状态非常稳定，发挥可靠。\n"
        elif cv > 0.15:
            summary += "成绩波动需关注，建议查找原因。\n"
        else:
            summary += "属于正常范围。\n"

        # 趋势描述
        summary += f"【发展趋势】{trend}（斜率{slope:.2f}），"
        if slope > 1:
            summary += "进步势头良好，应继续保持。\n"
        elif slope < -1:
            summary += "需及时分析原因，采取措施。\n"
        else:
            summary += "保持当前状态，适当突破。\n"

        return summary

    def _generate_recommendations(self, level: str, stability: str, trend: str,
                                   cv: float, slope: float, trend_change: float) -> List[str]:
        """生成针对性建议"""
        recommendations = []

        # 基于水平
        if level == '优秀':
            recommendations.append("🎯 保持优势，适当拓展深度学习内容")
            recommendations.append("📚 可尝试奥数等拓展性题目，培养思维深度")
        elif level == '良好':
            recommendations.append("📈 巩固现有基础，争取突破到优秀水平")
            recommendations.append("🎯 分析失分原因，针对性提升")
        elif level == '中等':
            recommendations.append("📚 加强基础知识复习，建立知识网络")
            recommendations.append("💪 增加练习量，提高熟练度")
        else:
            recommendations.append("⚠️ 建议系统复习基础知识")
            recommendations.append("📖 寻求老师或家长辅导，查漏补缺")

        # 基于稳定性
        if cv > 0.15:
            recommendations.append("📊 成绩波动较大，建议分析低分试卷找原因")
            recommendations.append("✅ 建立错题本，定期复习易错点")

        # 基于趋势
        if slope < -1:
            recommendations.append("⚠️ 成绩呈下降趋势，需及时关注学习状态")
            recommendations.append("🔍 排查是否存在学习困难或外部因素影响")
        elif slope > 1 and trend_change > 2:
            recommendations.append("🌟 进步明显，值得肯定和鼓励")
            recommendations.append("📈 总结成功经验，持续保持")

        return recommendations

    def compare_two_students(self, student_id_1: int, student_id_2: int) -> Dict:
        """
        对比两个学生的 SAI 得分，分析差异原因
        """
        macro_1 = self.analyze_student_development(student_id_1)
        macro_2 = self.analyze_student_development(student_id_2)

        if 'error' in macro_1 or 'error' in macro_2:
            return {'error': '数据不足，无法对比'}

        rank_1 = self.get_score_rank(student_id_1)
        rank_2 = self.get_score_rank(student_id_2)

        # SAI 对比
        sai_1 = macro_1['sai']['index']
        sai_2 = macro_2['sai']['index']
        sai_diff = sai_1 - sai_2

        # 找出 SAI 差异的主要原因
        components_1 = macro_1['sai']['components']
        components_2 = macro_2['sai']['components']
        sai_raw_1 = macro_1['sai_raw']
        sai_raw_2 = macro_2['sai_raw']

        # 各维度差异
        diff_analysis = {
            'mean': {
                'student_1': components_1['mean_score'],
                'student_2': components_2['mean_score'],
                'diff': components_1['mean_score'] - components_2['mean_score'],
                'raw_1': sai_raw_1['normalized_mean'],
                'raw_2': sai_raw_2['normalized_mean'],
            },
            'stability': {
                'student_1': components_1['stability_score'],
                'student_2': components_2['stability_score'],
                'diff': components_1['stability_score'] - components_2['stability_score'],
                'cv_1': macro_1['quantitative']['cv'],
                'cv_2': macro_2['quantitative']['cv'],
            },
            'trend': {
                'student_1': components_1['trend_score'],
                'student_2': components_2['trend_score'],
                'diff': components_1['trend_score'] - components_2['trend_score'],
                'slope_1': macro_1['quantitative']['slope'],
                'slope_2': macro_2['quantitative']['slope'],
            },
            'recent_trend': {
                'student_1': components_1['recent_trend_score'],
                'student_2': components_2['recent_trend_score'],
                'diff': components_1['recent_trend_score'] - components_2['recent_trend_score'],
                'change_1': macro_1['quantitative']['trend_change'],
                'change_2': macro_2['quantitative']['trend_change'],
            },
            'excellent_rate': {
                'student_1': components_1['excellent_rate_score'],
                'student_2': components_2['excellent_rate_score'],
                'diff': components_1['excellent_rate_score'] - components_2['excellent_rate_score'],
                'rate_1': sai_raw_1['excellent_rate'],
                'rate_2': sai_raw_2['excellent_rate'],
            },
        }

        # 找出主要差异原因（绝对值最大的前三项）
        sorted_diffs = sorted(
            [(k, abs(v['diff']), v['diff']) for k, v in diff_analysis.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # 生成解释
        higher_sai_id = student_id_1 if sai_diff > 0 else student_id_2
        higher_sai_name = self.student_names.get(higher_sai_id, 'Unknown')
        lower_sai_id = student_id_2 if sai_diff > 0 else student_id_1
        lower_sai_name = self.student_names.get(lower_sai_id, 'Unknown')

        # 分析为什么 SAI 高的学生排名可能更低
        rank_1_num = rank_1['rank']
        rank_2_num = rank_2['rank']

        explanation = []
        if (sai_diff > 0 and rank_1_num > rank_2_num) or (sai_diff < 0 and rank_2_num > rank_1_num):
            explanation.append(f"💡 **为什么 {higher_sai_name} 的 SAI 更高但排名更低？**")
            explanation.append("")
            explanation.append("**SAI 与班级排名的区别：**")
            explanation.append("- **SAI** 是综合评价指数，考虑了平均分、稳定性、发展趋势、优秀率等多个维度")
            explanation.append("- **班级排名** 仅基于平均分，反映的是绝对分数水平")
            explanation.append("")
            explanation.append("**具体原因分析：**")

            # 详细分析
            if diff_analysis['mean']['diff'] * sai_diff < 0:
                # 平均分是反向贡献
                avg_higher = higher_sai_name if diff_analysis['mean']['diff'] > 0 else lower_sai_name
                explanation.append(f"1. **平均分因素**：{avg_higher} 的平均分更高，这是排名领先的主要原因")

            if diff_analysis['stability']['diff'] * sai_diff > 0:
                stability_higher = higher_sai_name if diff_analysis['stability']['diff'] > 0 else lower_sai_name
                cv_better = stability_higher
                explanation.append(f"2. **稳定性因素**：{stability_higher} 的成绩更稳定（变异系数更小），这提升了 SAI 得分")

            if diff_analysis['trend']['diff'] * sai_diff > 0:
                trend_higher = higher_sai_name if diff_analysis['trend']['diff'] > 0 else lower_sai_name
                explanation.append(f"3. **发展趋势**：{trend_higher} 的进步趋势更明显，SAI 给予额外加分")

            if diff_analysis['excellent_rate']['diff'] * sai_diff > 0:
                rate_higher = higher_sai_name if diff_analysis['excellent_rate']['diff'] > 0 else lower_sai_name
                explanation.append(f"4. **优秀率因素**：{rate_higher} 的优秀率更高（90 分以上比例）")

            explanation.append("")
            explanation.append("**结论：**")
            if diff_analysis['mean']['diff'] * sai_diff < 0:
                explanation.append(f"- {lower_sai_name} 虽然平均分更高（排名靠前），但其他维度（如稳定性、发展趋势）不如 {higher_sai_name}")
                explanation.append(f"- {higher_sai_name} 在综合发展方面表现更好，因此 SAI 得分更高")
            else:
                explanation.append(f"- {higher_sai_name} 在多个维度表现优异，SAI 和排名都领先")
        else:
            explanation.append(f"✅ **SAI 与排名一致**：{higher_sai_name} 的 SAI 和排名都更高，表现全面领先")

        return {
            'student_1': {
                'id': student_id_1,
                'name': self.student_names.get(student_id_1, 'Unknown'),
                'sai': sai_1,
                'grade': macro_1['sai']['grade'],
                'rank': rank_1['rank'],
                'macro': macro_1,
            },
            'student_2': {
                'id': student_id_2,
                'name': self.student_names.get(student_id_2, 'Unknown'),
                'sai': sai_2,
                'grade': macro_2['sai']['grade'],
                'rank': rank_2['rank'],
                'macro': macro_2,
            },
            'sai_difference': round(sai_diff, 2),
            'diff_analysis': diff_analysis,
            'sorted_factors': sorted_diffs,
            'explanation': explanation,
        }


def main():
    """测试主函数"""
    analyzer = ScoreAnalyzer()
    analyzer.load_all_data()

    print("加载的学生姓名:")
    for sid, name in analyzer.get_student_list():
        print(f"  {sid}: {name}")

    if analyzer.student_names:
        first_student = list(analyzer.student_names.keys())[0]
        print(f"\n学生 {first_student} ({analyzer.student_names[first_student]}) 的统计:")
        stats = analyzer.calculate_statistics(first_student)
        for k, v in stats.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
