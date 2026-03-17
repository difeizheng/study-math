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


# 题目模板库（按知识点分类）
QUESTION_TEMPLATES = {
    # ==================== 一年级 ====================
    "G1U03": [
        {"type": "计算题", "text": "计算：{a} + {b} = ?", "difficulty": 1, "answer": "{a+b}"},
        {"type": "计算题", "text": "计算：{a} - {b} = ?", "difficulty": 1, "answer": "{a-b}"},
        {"type": "填空题", "text": "{a} + ( ) = {c}", "difficulty": 2, "answer": "{c-a}"},
        {"type": "填空题", "text": "( ) - {b} = {c}", "difficulty": 2, "answer": "{c+b}"},
    ],
    "G1U05": [
        {"type": "计算题", "text": "计算：{a} + {b} = ?", "difficulty": 2, "answer": "{a+b}"},
        {"type": "计算题", "text": "计算：{a} - {b} = ?", "difficulty": 2, "answer": "{a-b}"},
        {"type": "应用题", "text": "小明有{a}个苹果，小红给了他{b}个，现在有多少个？", "difficulty": 3, "answer": "{a+b}个"},
    ],
    "G1U08": [
        {"type": "计算题", "text": "计算：9 + {a} = ?", "difficulty": 3, "answer": "{9+a}"},
        {"type": "计算题", "text": "计算：8 + {a} = ?", "difficulty": 3, "answer": "{8+a}"},
        {"type": "填空题", "text": "9 + ( ) = 15", "difficulty": 3, "answer": "6"},
        {"type": "应用题", "text": "一班有 9 个男生，又来了{a}个女生，现在一共有多少人？", "difficulty": 4, "answer": "{9+a}人"},
    ],
    "G1D02": [
        {"type": "计算题", "text": "计算：15 - {a} = ?", "difficulty": 3, "answer": "{15-a}"},
        {"type": "计算题", "text": "计算：13 - {a} = ?", "difficulty": 3, "answer": "{13-a}"},
        {"type": "填空题", "text": "17 - ( ) = 9", "difficulty": 4, "answer": "8"},
    ],
    "G1D03": [
        {"type": "填空题", "text": "3 个十和 5 个一组成的数是 ( )", "difficulty": 2, "answer": "35"},
        {"type": "比较题", "text": "比较大小：{a} ○ {b}", "difficulty": 2, "answer": "{'>' if a>b else '<' if a<b else '='}"},
        {"type": "计算题", "text": "计算：{a} + {b} = ?", "difficulty": 3, "answer": "{a+b}"},
    ],
    # ==================== 二年级 ====================
    "G2U04": [
        {"type": "计算题", "text": "计算：{a} × {b} = ?", "difficulty": 3, "answer": "{a*b}"},
        {"type": "填空题", "text": "{a}的{b}倍是 ( )", "difficulty": 3, "answer": "{a*b}"},
        {"type": "应用题", "text": "一个盒子装{a}个苹果，{b}个盒子一共装多少个？", "difficulty": 4, "answer": "{a*b}个"},
    ],
    "G2U06": [
        {"type": "计算题", "text": "计算：7 × {a} = ?", "difficulty": 3, "answer": "{7*a}"},
        {"type": "计算题", "text": "计算：8 × {a} = ?", "difficulty": 3, "answer": "{8*a}"},
        {"type": "计算题", "text": "计算：9 × {a} = ?", "difficulty": 3, "answer": "{9*a}"},
        {"type": "应用题", "text": "每本书{a}元，买{b}本需要多少钱？", "difficulty": 4, "answer": "{a*b}元"},
    ],
    "G2D02": [
        {"type": "计算题", "text": "计算：{a} ÷ {b} = ?", "difficulty": 3, "answer": "{a//b}"},
        {"type": "填空题", "text": "计算：{a} ÷ {b} = {c}，想：{b} 乘 ( ) 等于{a}", "difficulty": 3, "answer": "{c}"},
        {"type": "应用题", "text": "{a}个苹果平均分给{b}个小朋友，每人分几个？", "difficulty": 4, "answer": "{a//b}个"},
    ],
    "G2D05": [
        {"type": "计算题", "text": "计算：{a} + {b} × {c} = ?", "difficulty": 4, "answer": "{a+b*c}"},
        {"type": "计算题", "text": "计算：({a} + {b}) ÷ {c} = ?", "difficulty": 4, "answer": "{(a+b)//c}"},
        {"type": "判断题", "text": "判断：在混合运算中，有括号要先算括号里面的。（ ）", "difficulty": 2, "answer": "√"},
    ],
    "G2D06": [
        {"type": "计算题", "text": "计算：{a} ÷ {b} = ?......?", "difficulty": 4, "answer": "{a//b}......{a%b}"},
        {"type": "填空题", "text": "{a}除以{b}，商是 ( )，余数是 ( )", "difficulty": 4, "answer": "{a//b},{a%b}"},
        {"type": "应用题", "text": "{a}个苹果，每{b}个装一盘，可以装几盘？还剩几个？", "difficulty": 5, "answer": "{a//b}盘，剩{a%b}个"},
    ],
    # ==================== 三年级 ====================
    "G3U02": [
        {"type": "计算题", "text": "计算：{a} + {b} = ?", "difficulty": 3, "answer": "{a+b}"},
        {"type": "计算题", "text": "计算：{a} - {b} = ?", "difficulty": 3, "answer": "{a-b}"},
        {"type": "应用题", "text": "商场上午卖出{a}台电视，下午卖出{b}台，一天共卖出多少台？", "difficulty": 4, "answer": "{a+b}台"},
    ],
    "G3U05": [
        {"type": "填空题", "text": "{a}是{b}的 ( ) 倍", "difficulty": 3, "answer": "{a//b}"},
        {"type": "计算题", "text": "{a}的{b}倍是多少？", "difficulty": 3, "answer": "{a*b}"},
        {"type": "应用题", "text": "小明今年{a}岁，爸爸的年龄是他的{b}倍，爸爸今年多少岁？", "difficulty": 4, "answer": "{a*b}岁"},
    ],
    "G3U06": [
        {"type": "计算题", "text": "计算：{a} × {b} = ?", "difficulty": 4, "answer": "{a*b}"},
        {"type": "计算题", "text": "计算：{ab} × {c} = ?", "difficulty": 4, "answer": "{ab*c}"},
        {"type": "应用题", "text": "一箱苹果有{a}个，{b}箱共有多少个？", "difficulty": 4, "answer": "{a*b}个"},
    ],
    "G3U07": [
        {"type": "计算题", "text": "长方形长{a}厘米，宽{b}厘米，周长是多少？", "difficulty": 4, "answer": "{(a+b)*2}厘米"},
        {"type": "计算题", "text": "正方形边长{a}分米，周长是多少？", "difficulty": 3, "answer": "{a*4}分米"},
        {"type": "填空题", "text": "长方形的周长 = ( ) × 2", "difficulty": 2, "answer": "长 + 宽"},
    ],
    "G3U08": [
        {"type": "计算题", "text": "计算：1/2 + 1/4 = ?", "difficulty": 4, "answer": "3/4"},
        {"type": "计算题", "text": "计算：3/5 - 1/5 = ?", "difficulty": 3, "answer": "2/5"},
        {"type": "填空题", "text": "把一个蛋糕平均分成{a}份，每份是它的 ( ) 分之 ( )", "difficulty": 3, "answer": "{a},1"},
    ],
    "G3D02": [
        {"type": "计算题", "text": "计算：{a} ÷ {b} = ?", "difficulty": 4, "answer": "{a//b}"},
        {"type": "计算题", "text": "计算：{abc} ÷ {a} = ?", "difficulty": 4, "answer": "{abc//a}"},
        {"type": "应用题", "text": "{a}本书平均分给{b}个班，每班分多少本？", "difficulty": 4, "answer": "{a//b}本"},
    ],
    "G3D04": [
        {"type": "计算题", "text": "计算：{a} × {b} = ?", "difficulty": 4, "answer": "{a*b}"},
        {"type": "计算题", "text": "计算：{ab} × {cd} = ?", "difficulty": 5, "answer": "{ab*cd}"},
        {"type": "应用题", "text": "学校买了{a}盒粉笔，每盒{b}元，一共花了多少钱？", "difficulty": 4, "answer": "{a*b}元"},
    ],
    "G3D05": [
        {"type": "计算题", "text": "长方形长{a}米，宽{b}米，面积是多少？", "difficulty": 4, "answer": "{a*b}平方米"},
        {"type": "计算题", "text": "正方形边长{a}分米，面积是多少？", "difficulty": 3, "answer": "{a*a}平方分米"},
        {"type": "填空题", "text": "长方形的面积 = ( ) × ( )", "difficulty": 2, "answer": "长，宽"},
    ],
    "G3D07": [
        {"type": "计算题", "text": "计算：0.{a} + 0.{b} = ?", "difficulty": 3, "answer": "0.{a+b}"},
        {"type": "计算题", "text": "计算：{a}.{b} - {c}.{d} = ?", "difficulty": 4, "answer": "{a+c}.{b-d}"},
        {"type": "比较题", "text": "比较大小：0.{a} ○ 0.{b}", "difficulty": 2, "answer": "{'>' if a>b else '<' if a<b else '='}"},
    ],
}

# 试卷结构配置
PAPER_STRUCTURES = {
    "基础练习": {
        "total_score": 100,
        "duration": 45,
        "type_distribution": {"计算题": 50, "填空题": 30, "应用题": 20}
    },
    "单元检测": {
        "total_score": 100,
        "duration": 60,
        "type_distribution": {"计算题": 40, "填空题": 25, "判断题": 10, "应用题": 25}
    },
    "专项突破": {
        "total_score": 50,
        "duration": 30,
        "type_distribution": {"计算题": 60, "应用题": 40}
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

    def export_paper_word(self, paper: ExamPaper) -> str:
        """导出试卷为 Word 格式文本"""
        md = f"""# {paper.title}

**生成时间**: {paper.generated_date}
**建议时长**: {paper.duration_minutes}分钟
**总分**: {paper.total_score}分

**重点考察**: {', '.join(paper.focus_areas) if paper.focus_areas else '综合练习'}

---

## 一、计算题（每题 5 分）

"""
        calc_num = 1
        for q in paper.questions:
            if q.question_type == "计算题":
                md += f"{calc_num}. {q.question_text} （    分）\n\n"
                calc_num += 1

        md += "\n## 二、填空题（每题 5 分）\n\n"
        fill_num = 1
        for q in paper.questions:
            if q.question_type == "填空题":
                md += f"{fill_num}. {q.question_text} （    分）\n\n"
                fill_num += 1

        md += "\n## 三、应用题（每题 10 分）\n\n"
        app_num = 1
        for q in paper.questions:
            if q.question_type == "应用题":
                md += f"{app_num}. {q.question_text} （    分）\n\n"
                app_num += 1

        md += "\n---\n\n## 参考答案\n\n"
        for i, q in enumerate(paper.questions, 1):
            md += f"{i}. {q.answer}\n"

        return md

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
