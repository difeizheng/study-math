"""
班级学情看板模块
教师视角的班级整体分析，知识点掌握率热力图
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from database import ExamScoreDAO


@dataclass
class ClassAnalysis:
    """班级分析结果"""
    semester: str
    total_students: int
    class_avg: float
    excellent_rate: float
    pass_rate: float
    knowledge_mastery: Dict[str, float]  # 知识点掌握率
    student_rankings: List[Dict]
    weak_knowledge_points: List[Dict]
    needs_attention_students: List[Dict]


class ClassLearningDashboard:
    """班级学情看板"""

    def __init__(self):
        self.students_df = None
        self.semester_data = {}
        self.student_names = {}
        self.knowledge_points = {}

    def load_data(self, students_df: pd.DataFrame, semester_data: Dict,
                  student_names: Dict[int, str], knowledge_points: Dict):
        """加载数据"""
        self.students_df = students_df
        self.semester_data = semester_data
        self.student_names = student_names
        self.knowledge_points = knowledge_points

    def _normalize_semester_name(self, semester: str) -> str:
        """标准化学期名称，去除 -math_scores 等后缀和数字前缀"""
        import re
        # 匹配格式：10032-1(2) 班上学期数学考试分数 或 1(2) 班上学期
        # 提取如 "1(2) 班上学期" 格式
        match = re.search(r'(\d+\(\d+\).*?学期)', semester)
        if match:
            return match.group(1).replace(' ', '')
        return semester

    def analyze_class_overall(self, semester: str) -> Optional[ClassAnalysis]:
        """
        分析班级整体情况（包含 Excel 成绩 + 录入成绩）

        Args:
            semester: 学期名称

        Returns:
            班级分析结果
        """
        # 标准化学期名称，用于匹配
        normalized_semester = self._normalize_semester_name(semester)

        print(f"[analyze_class_overall] input semester={semester}, normalized={normalized_semester}")
        print(f"[analyze_class_overall] semester_data keys={list(self.semester_data.keys())}")

        # 查找匹配的 Excel 学期数据（支持模糊匹配）
        df = None
        for key in self.semester_data.keys():
            key_normalized = self._normalize_semester_name(key)
            print(f"[analyze_class_overall] checking key={key}, normalized={key_normalized}, match={key_normalized == normalized_semester}")
            if key_normalized == normalized_semester:
                df = self.semester_data[key]
                break

        # 如果没有 Excel 数据，从数据库获取
        if df is None:
            print(f"[analyze_class_overall] Excel data not found, trying database...")
            # 从数据库获取该学期的成绩
            all_scores = ExamScoreDAO.get_all_scores()
            print(f"[analyze_class_overall] all_scores count={len(all_scores)}")
            print(f"[analyze_class_overall] all_scores semesters: {set(s['semester'] for s in all_scores)}")

            semester_scores = [s for s in all_scores if self._normalize_semester_name(s['semester']) == normalized_semester]
            print(f"[analyze_class_overall] semester_scores count={len(semester_scores)}")

            if not semester_scores:
                print(f"[analyze_class_overall] No scores found for semester={semester}")
                return None

            # 获取该学期的所有学生
            student_ids = set(s['student_id'] for s in semester_scores)

            # 获取学生姓名
            from database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, name FROM students WHERE student_id IN ({})".format(','.join('?' * len(student_ids))), list(student_ids))
            students = cursor.fetchall()
            conn.close()

            # 创建 DataFrame
            df = pd.DataFrame([{'学号': sid, '姓名': name} for sid, name in students])

            # 按学号和考试名称组织成绩
            scores_by_student = {}
            for s in semester_scores:
                sid = s['student_id']
                exam = s['exam_name']
                score = s['score']
                if sid not in scores_by_student:
                    scores_by_student[sid] = {}
                scores_by_student[sid][exam] = score

            # 将成绩添加到 DataFrame
            for exam_names in set(s['exam_name'] for s in semester_scores):
                df[exam_names] = df['学号'].apply(lambda sid: scores_by_student.get(int(sid), {}).get(exam_names, np.nan))

        # 获取录入的成绩（从数据库）
        entered_scores = ExamScoreDAO.get_all_scores()
        # 按学号和考试名称组织录入的成绩
        entered_scores_by_student = {}
        for s in entered_scores:
            # 检查是否属于当前学期（使用标准化后的学期名称匹配）
            if self._normalize_semester_name(s['semester']) != normalized_semester:
                continue
            sid = s['student_id']
            if sid not in entered_scores_by_student:
                entered_scores_by_student[sid] = {}
            entered_scores_by_student[sid][s['exam_name']] = s['score']

        total_students = len(df)

        if total_students == 0:
            return None

        # 计算每个学生的平均分（Excel + 录入成绩）
        student_avgs = []
        student_scores_detail = {}

        for _, row in df.iterrows():
            # 检查学号是否有效
            student_id = row.get('学号')
            if pd.isna(student_id):
                continue
            try:
                student_id = int(student_id)
            except (ValueError, TypeError):
                continue

            scores = []
            # 从 Excel 获取成绩
            for col in df.columns:
                if col not in ['学号', '姓名']:
                    val = row[col]
                    if pd.notna(val):
                        try:
                            scores.append(float(val))
                        except (ValueError, TypeError):
                            pass

            # 从录入成绩获取
            if student_id in entered_scores_by_student:
                for exam_name, score in entered_scores_by_student[student_id].items():
                    if score is not None:
                        scores.append(float(score))

            if scores:
                avg = sum(scores) / len(scores)
                student_avgs.append({
                    '学号': student_id,
                    '姓名': row['姓名'],
                    '平均分': round(avg, 2),
                    '考试次数': len(scores)
                })
                student_scores_detail[student_id] = scores

        # 按平均分排序
        student_avgs.sort(key=lambda x: x['平均分'], reverse=True)

        # 添加排名
        for i, s in enumerate(student_avgs, 1):
            s['排名'] = i

        # 计算整体统计（使用实际有效学生数）
        actual_total = len(student_avgs)
        if actual_total == 0:
            return None

        all_avgs = [s['平均分'] for s in student_avgs]
        class_avg = round(np.mean(all_avgs), 2)
        excellent_count = sum(1 for avg in all_avgs if avg >= 90)
        pass_count = sum(1 for avg in all_avgs if avg >= 60)
        excellent_rate = round(excellent_count / actual_total * 100, 1)
        pass_rate = round(pass_count / actual_total * 100, 1)

        # 知识点掌握率分析
        knowledge_mastery = self._analyze_knowledge_mastery(semester, student_scores_detail)

        # 薄弱知识点
        weak_knowledge = self._identify_weak_knowledge(knowledge_mastery)

        # 需要关注的学生
        needs_attention = self._identify_needs_attention(student_avgs, student_scores_detail)

        return ClassAnalysis(
            semester=semester,
            total_students=actual_total,
            class_avg=class_avg,
            excellent_rate=excellent_rate,
            pass_rate=pass_rate,
            knowledge_mastery=knowledge_mastery,
            student_rankings=student_avgs,
            weak_knowledge_points=weak_knowledge,
            needs_attention_students=needs_attention
        )

    def _analyze_knowledge_mastery(self, semester: str,
                                   student_scores_detail: Dict[int, List[float]]) -> Dict[str, float]:
        """
        分析知识点掌握率

        Returns:
            {知识点编码：掌握率 (0-100)}
        """
        knowledge_mastery = {}

        # 简化处理：根据考试类型推断知识点掌握
        semester_df = self.semester_data.get(semester)
        if semester_df is None:
            return knowledge_mastery

        # 提取学期代码
        import re
        code_match = re.search(r'(\d+)-', semester)
        semester_code = code_match.group(1) if code_match else None

        if not semester_code:
            return knowledge_mastery

        # 遍历所有考试列
        for col in semester_df.columns:
            if col in ['学号', '姓名']:
                continue

            # 提取考试名称
            exam_name = col.replace(f"{semester}_", "")

            # 获取该考试对应的知识点
            knowledge_codes = self._map_exam_to_knowledge(exam_name, semester_code)

            # 计算该考试的平均得分率
            scores = semester_df[col].dropna()
            if len(scores) > 0 and knowledge_codes:
                avg_score = scores.mean()
                mastery_rate = avg_score  # 直接用平均分作为掌握率

                for kc in knowledge_codes:
                    knowledge_mastery[kc] = mastery_rate

        return knowledge_mastery

    def _map_exam_to_knowledge(self, exam_name: str, semester_code: str) -> List[str]:
        """考试名称映射到知识点"""
        from deep_analyzer import PRACTICE_MAPPING

        if semester_code not in PRACTICE_MAPPING:
            return []

        practice_map = PRACTICE_MAPPING[semester_code]

        # 提取练习号
        import re
        practice_match = re.search(r'[练习单元](\d+)', exam_name)
        if practice_match:
            practice_num = int(practice_match.group(1))
            if practice_num in practice_map:
                return practice_map[practice_num]

        # 期中/期末
        if "期中" in exam_name:
            return [f"{semester_code}0{i}" for i in range(1, 5)]
        if "期末" in exam_name:
            prefix = f"G{int(semester_code[0])}{'上' if semester_code[3] == '上' else '下'}"
            return [kp for kp in self.knowledge_points.keys() if kp.startswith(prefix)]

        return []

    def _identify_weak_knowledge(self, knowledge_mastery: Dict[str, float],
                                  threshold: float = 75) -> List[Dict]:
        """识别薄弱知识点"""
        weak_points = []

        for kp_code, mastery_rate in knowledge_mastery.items():
            if mastery_rate < threshold:
                kp_info = self.knowledge_points.get(kp_code)
                weak_points.append({
                    'code': kp_code,
                    'name': kp_info.name if kp_info else kp_code,
                    'mastery_rate': round(mastery_rate, 1),
                    'grade': kp_info.grade if kp_info else '未知',
                    'semester': kp_info.semester if kp_info else '未知',
                    'category': kp_info.category if kp_info else '未知'
                })

        # 按掌握率排序
        weak_points.sort(key=lambda x: x['mastery_rate'])
        return weak_points

    def _identify_needs_attention(self, student_avgs: List[Dict],
                                   student_scores_detail: Dict[int, List[float]]) -> List[Dict]:
        """识别需要关注的学生"""
        needs_attention = []

        for student in student_avgs:
            student_id = student['学号']
            avg = student['平均分']
            scores = student_scores_detail.get(student_id, [])

            reasons = []

            # 平均分低于 70
            if avg < 70:
                reasons.append(f"平均分偏低 ({avg}分)")

            # 成绩波动大
            if len(scores) >= 3:
                std = np.std(scores)
                if std > 15:
                    reasons.append(f"成绩波动大 (标准差{std:.1f})")

            # 最近成绩下滑
            if len(scores) >= 3:
                recent_trend = scores[-1] - scores[0]
                if recent_trend < -10:
                    reasons.append(f"成绩下滑 ({recent_trend:.0f}分)")

            if reasons:
                needs_attention.append({
                    '学号': student_id,
                    '姓名': student['姓名'],
                    '平均分': avg,
                    '排名': student['排名'],
                    '原因': reasons
                })

        return needs_attention

    def get_score_distribution(self, semester: str) -> Dict:
        """获取分数段分布（包含录入成绩）"""
        if semester not in self.semester_data:
            return {}

        df = self.semester_data[semester]

        # 获取录入的成绩
        entered_scores = ExamScoreDAO.get_all_scores()
        entered_scores_by_student = {}
        for s in entered_scores:
            if s['semester'] != semester:
                continue
            sid = s['student_id']
            if sid not in entered_scores_by_student:
                entered_scores_by_student[sid] = []
            entered_scores_by_student[sid].append(s['score'])

        distribution = {'90-100': 0, '80-89': 0, '70-79': 0, '60-69': 0, '60 以下': 0}

        for _, row in df.iterrows():
            scores = []
            # 从 Excel 获取成绩
            for col in df.columns:
                if col not in ['学号', '姓名']:
                    val = row[col]
                    if pd.notna(val):
                        try:
                            scores.append(float(val))
                        except (ValueError, TypeError):
                            pass

            # 从录入成绩获取
            student_id = row.get('学号')
            if pd.notna(student_id):
                try:
                    student_id = int(student_id)
                    if student_id in entered_scores_by_student:
                        for score in entered_scores_by_student[student_id]:
                            if score is not None:
                                scores.append(float(score))
                except (ValueError, TypeError):
                    pass

            if scores:
                avg = sum(scores) / len(scores)
                if avg >= 90:
                    distribution['90-100'] += 1
                elif avg >= 80:
                    distribution['80-89'] += 1
                elif avg >= 70:
                    distribution['70-79'] += 1
                elif avg >= 60:
                    distribution['60-69'] += 1
                else:
                    distribution['60 以下'] += 1

        return distribution

    def get_class_comparison(self, semester1: str, semester2: str) -> Dict:
        """对比两个学期的班级表现"""
        analysis1 = self.analyze_class_overall(semester1)
        analysis2 = self.analyze_class_overall(semester2)

        if not analysis1 or not analysis2:
            return {'error': '数据不足'}

        return {
            'semester1': {
                'name': semester1,
                'class_avg': analysis1.class_avg,
                'excellent_rate': analysis1.excellent_rate,
                'pass_rate': analysis1.pass_rate,
                'total_students': analysis1.total_students
            },
            'semester2': {
                'name': semester2,
                'class_avg': analysis2.class_avg,
                'excellent_rate': analysis2.excellent_rate,
                'pass_rate': analysis2.pass_rate,
                'total_students': analysis2.total_students
            },
            'changes': {
                'class_avg_change': round(analysis2.class_avg - analysis1.class_avg, 2),
                'excellent_rate_change': round(analysis2.excellent_rate - analysis1.excellent_rate, 1),
                'pass_rate_change': round(analysis2.pass_rate - analysis1.pass_rate, 1)
            }
        }

    def export_class_report(self, semester: str) -> str:
        """导出班级报告"""
        analysis = self.analyze_class_overall(semester)
        if not analysis:
            return "数据不足"

        md = f"""# 📊 班级学情分析报告

**学期**: {analysis.semester}
**分析日期**: {datetime.now().strftime("%Y-%m-%d")}

---

## 📈 整体统计

| 指标 | 数值 |
|------|------|
| 学生总数 | {analysis.total_students}人 |
| 班级平均分 | {analysis.class_avg}分 |
| 优秀率 (≥90) | {analysis.excellent_rate}% |
| 及格率 (≥60) | {analysis.pass_rate}% |

---

## 📊 分数段分布

"""
        dist = self.get_score_distribution(semester)
        for range_name, count in dist.items():
            percentage = round(count / analysis.total_students * 100, 1) if analysis.total_students > 0 else 0
            md += f"- **{range_name}**: {count}人 ({percentage}%)\n"

        md += f"""
---

## 🎯 薄弱知识点 (掌握率<75%)

"""
        if analysis.weak_knowledge_points:
            for i, wp in enumerate(analysis.weak_knowledge_points[:10], 1):
                md += f"{i}. **{wp['name']}** - 掌握率{wp['mastery_rate']}% ({wp['grade']}{wp['semester']})\n"
        else:
            md += "暂无薄弱知识点，全班掌握良好！\n"

        md += f"""
---

## ⚠️ 需要关注的学生

"""
        if analysis.needs_attention_students:
            for student in analysis.needs_attention_students:
                reasons = "；".join(student['原因'])
                md += f"- **{student['姓名']}** (第{student['排名']}名): {reasons}\n"
        else:
            md += "暂无需要特别关注的学生\n"

        md += f"""
---

## 📋 成绩排名 (前 10 名)

| 排名 | 学号 | 姓名 | 平均分 |
|------|------|------|--------|
"""
        for student in analysis.student_rankings[:10]:
            md += f"| {student['排名']} | {student['学号']} | {student['姓名']} | {student['平均分']} |\n"

        md += """
---

## 💡 教学建议

根据分析结果，建议：

1. **针对薄弱知识点**: 安排专项复习课，重点讲解
2. **针对后进生**: 建立帮扶小组，个别辅导
3. **针对波动大学生**: 关注学习状态，及时沟通
4. **保持优势**: 继续巩固已掌握的知识

---

*本报告由学生成绩分析系统自动生成*
"""

        return md


def main():
    """测试"""
    # 这里需要实际数据，简化测试
    print("班级学情看板模块加载成功")


if __name__ == "__main__":
    main()
