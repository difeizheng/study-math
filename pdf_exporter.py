"""
PDF 报告导出模块
生成学生错题报告、能力分析报告的 PDF 文件
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from datetime import datetime
import os
from typing import Dict, List, Optional
from pathlib import Path

from logger import get_logger

logger = get_logger("pdf_exporter")


class PDFExporter:
    """PDF 报告导出器"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._register_chinese_font()

    def _register_chinese_font(self):
        """注册中文字体"""
        # 尝试注册系统字体
        font_paths = [
            r"C:\Windows\Fonts\simhei.ttf",  # 黑体
            r"C:\Windows\Fonts\simsun.ttc",  # 宋体
            r"C:\Windows\Fonts\msyh.ttf",    # 微软雅黑
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('SimHei', font_path))
                    logger.info(f"注册中文字体：{font_path}")
                    break
                except Exception as e:
                    logger.warning(f"注册字体失败：{e}")
        else:
            logger.warning("未找到中文字体，使用默认字体")

    def _get_chinese_style(self, font_size: int = 12, alignment: str = 'left'):
        """获取中文样式"""
        align_map = {'left': TA_LEFT, 'center': TA_CENTER, 'justify': TA_JUSTIFY}

        try:
            return ParagraphStyle(
                name='ChineseStyle',
                parent=self.styles['Normal'],
                fontName='SimHei',
                fontSize=font_size,
                alignment=align_map.get(alignment, TA_LEFT),
                leading=font_size * 1.5,
                spaceAfter=10
            )
        except:
            return ParagraphStyle(
                name='FallbackStyle',
                parent=self.styles['Normal'],
                fontSize=font_size,
                alignment=align_map.get(alignment, TA_LEFT),
                leading=font_size * 1.5,
                spaceAfter=10
            )

    def export_error_report(self, student_name: str, student_id: int,
                           error_records: List[Dict], output_path: str) -> str:
        """
        导出错题报告 PDF

        Args:
            student_name: 学生姓名
            student_id: 学号
            error_records: 错题记录列表
            output_path: 输出文件路径

        Returns:
            生成的 PDF 文件路径
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        story = []

        # 标题
        title_style = self._get_chinese_style(18, 'center')
        story.append(Paragraph(f"{student_name}的错题分析报告", title_style))
        story.append(Spacer(1, 0.5*cm))

        # 基本信息
        info_style = self._get_chinese_style(10)
        story.append(Paragraph(f"学号：{student_id}", info_style))
        story.append(Paragraph(f"生成日期：{datetime.now().strftime('%Y-%m-%d')}", info_style))
        story.append(Paragraph(f"错题总数：{len(error_records)}道", info_style))
        story.append(Spacer(1, 1*cm))

        # 按知识点分类统计
        if error_records:
            story.append(Paragraph("知识点分布统计", self._get_chinese_style(14)))
            story.append(Spacer(1, 0.5*cm))

            kp_stats = {}
            for record in error_records:
                kp_name = record.get('knowledge_name', '未知')
                kp_stats[kp_name] = kp_stats.get(kp_name, 0) + 1

            # 创建统计表
            stats_data = [['知识点', '错题数量']]
            for kp_name, count in sorted(kp_stats.items(), key=lambda x: x[1], reverse=True):
                stats_data.append([kp_name, str(count)])

            stats_table = Table(stats_data, colWidths=[4*cm, 2*cm])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 1*cm))

            # 分页符
            story.append(PageBreak())

            # 详细错题列表
            story.append(Paragraph("错题详细分析", self._get_chinese_style(14)))
            story.append(Spacer(1, 0.5*cm))

            for i, record in enumerate(error_records[:50], 1):  # 限制最多 50 道
                error_style = self._get_chinese_style(11)
                story.append(Paragraph(f"<b>第{i}题</b>", error_style))

                # 错题信息表格
                error_data = [
                    ['考试名称:', record.get('exam_name', '')],
                    ['考试日期:', record.get('exam_date', '')],
                    ['知识点:', record.get('knowledge_name', '')],
                    ['错误类型:', record.get('error_type', '')],
                    ['得分:', str(record.get('score', ''))],
                ]

                if record.get('error_description'):
                    error_data.append(['错误描述:', record.get('error_description')])

                error_table = Table(error_data, colWidths=[2.5*cm, 4.5*cm])
                error_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ]))
                story.append(error_table)
                story.append(Spacer(1, 0.5*cm))

                # 每 10 题分页
                if i % 10 == 0 and i < len(error_records):
                    story.append(PageBreak())

        # 学习建议
        story.append(Paragraph("学习建议", self._get_chinese_style(14)))
        story.append(Spacer(1, 0.5*cm))

        suggestions = self._generate_error_suggestions(error_records)
        for sug in suggestions:
            story.append(Paragraph(f"• {sug}", self._get_chinese_style(11)))
            story.append(Spacer(1, 0.2*cm))

        # 构建 PDF
        doc.build(story)
        logger.info(f"错题报告 PDF 已生成：{output_path}")
        return output_path

    def export_ability_report(self, student_name: str, student_id: int,
                             ability_report: Dict, output_path: str) -> str:
        """
        导出能力分析 PDF

        Args:
            student_name: 学生姓名
            student_id: 学号
            ability_report: 能力分析报告
            output_path: 输出文件路径

        Returns:
            生成的 PDF 文件路径
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        story = []

        # 标题
        title_style = self._get_chinese_style(18, 'center')
        story.append(Paragraph(f"{student_name}的数学能力成长报告", title_style))
        story.append(Spacer(1, 0.5*cm))

        # 基本信息
        info_style = self._get_chinese_style(10)
        story.append(Paragraph(f"学号：{student_id}", info_style))
        story.append(Paragraph(f"生成日期：{datetime.now().strftime('%Y-%m-%d')}", info_style))
        story.append(Spacer(1, 1*cm))

        # 五大核心素养得分
        story.append(Paragraph("五大核心素养得分", self._get_chinese_style(14)))
        story.append(Spacer(1, 0.5*cm))

        abilities = ability_report.get('abilities', {})
        if abilities:
            # 能力得分表
            ability_data = [['核心素养', '得分', '等级', '简要描述']]
            for ability_name, data in abilities.items():
                ability_data.append([
                    ability_name,
                    str(data.get('score', 0)),
                    data.get('level', ''),
                    data.get('description', '')[:25] + '...'
                ])

            ability_table = Table(ability_data, colWidths=[2.5*cm, 1.5*cm, 1.5*cm, 4*cm])
            ability_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(ability_table)
            story.append(Spacer(1, 1*cm))

        # 最强和最弱能力
        story.append(Paragraph("能力亮点分析", self._get_chinese_style(14)))
        story.append(Spacer(1, 0.5*cm))

        strongest = ability_report.get('strongest', {})
        weakest = ability_report.get('weakest', {})

        if strongest:
            story.append(Paragraph(f"<b>最强能力：</b>{strongest.get('name', '')} ({strongest.get('score', 0)}分)",
                                 self._get_chinese_style(11)))
            story.append(Spacer(1, 0.3*cm))

        if weakest:
            story.append(Paragraph(f"<b>需加强：</b>{weakest.get('name', '')} ({weakest.get('score', 0)}分)",
                                 self._get_chinese_style(11)))
            story.append(Spacer(1, 1*cm))

        # 个性化建议
        story.append(Paragraph("个性化发展建议", self._get_chinese_style(14)))
        story.append(Spacer(1, 0.5*cm))

        suggestions = ability_report.get('suggestions', [])
        for i, sug in enumerate(suggestions, 1):
            story.append(Paragraph(f"{i}. {sug}", self._get_chinese_style(11)))
            story.append(Spacer(1, 0.3*cm))

        # 构建 PDF
        doc.build(story)
        logger.info(f"能力报告 PDF 已生成：{output_path}")
        return output_path

    def _generate_error_suggestions(self, error_records: List[Dict]) -> List[str]:
        """根据错题生成学习建议"""
        suggestions = []

        if not error_records:
            return ["暂无错题记录，请继续保持！"]

        # 统计错误类型
        error_types = {}
        for record in error_records:
            etype = record.get('error_type', '未知')
            error_types[etype] = error_types.get(etype, 0) + 1

        # 根据错误类型生成建议
        max_error_type = max(error_types.items(), key=lambda x: x[1])
        if max_error_type[0] == '计算粗心':
            suggestions.append("计算粗心是主要问题，建议每天进行 10 分钟口算练习，提高计算准确性")
        elif max_error_type[0] == '概念不清':
            suggestions.append("概念理解不足，建议重新学习相关知识点，结合图形和实例加深理解")
        elif max_error_type[0] == '知识性错误':
            suggestions.append("知识点掌握不牢固，建议系统复习相关章节，多做基础练习题")
        else:
            suggestions.append("建议针对错题涉及的知识点进行专项复习")

        # 统计知识点分布
        kp_counts = {}
        for record in error_records:
            kp = record.get('knowledge_name', '未知')
            kp_counts[kp] = kp_counts.get(kp, 0) + 1

        if kp_counts:
            top_kp = max(kp_counts.items(), key=lambda x: x[1])
            suggestions.append(f"知识点「{top_kp[0]}」错误最多，建议重点复习")

        suggestions.append("建议建立错题本，定期复习错题，避免重复犯错")
        suggestions.append("做题时注意审题，圈画关键词，减少因理解偏差导致的错误")

        return suggestions

    def export_summary_report(self, student_name: str, student_id: int,
                             error_count: int, ability_level: str,
                             habit_score: float, output_path: str) -> str:
        """
        导出综合总结报告 PDF

        Args:
            student_name: 学生姓名
            student_id: 学号
            error_count: 错题数量
            ability_level: 能力等级
            habit_score: 学习习惯得分
            output_path: 输出文件路径

        Returns:
            生成的 PDF 文件路径
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        story = []

        # 封面标题
        title_style = self._get_chinese_style(20, 'center')
        story.append(Paragraph(f"学习成长综合报告", title_style))
        story.append(Spacer(1, 2*cm))

        # 学生信息卡片
        card_style = self._get_chinese_style(14)
        story.append(Paragraph(f"学生姓名：{student_name}", card_style))
        story.append(Paragraph(f"学号：{student_id}", card_style))
        story.append(Paragraph(f"报告日期：{datetime.now().strftime('%Y-%m-%d')}", card_style))
        story.append(Spacer(1, 2*cm))

        # 核心指标
        story.append(Paragraph("核心学习指标", self._get_chinese_style(16)))
        story.append(Spacer(1, 1*cm))

        summary_data = [
            ['指标', '数值', '评价'],
            ['错题总数', str(error_count), self._get_error_evaluation(error_count)],
            ['能力等级', ability_level, self._get_level_evaluation(ability_level)],
            ['学习习惯得分', f"{habit_score:.1f}分", self._get_habit_evaluation(habit_score)],
        ]

        summary_table = Table(summary_data, colWidths=[3*cm, 3*cm, 3*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
            ('TOPPADDING', (0, 0), (-1, 0), 15),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('ROWHEIGHT', (0, 1), (-1, -1), 1.2*cm),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 2*cm))

        # 综合评价
        story.append(Paragraph("综合评价与建议", self._get_chinese_style(16)))
        story.append(Spacer(1, 0.5*cm))

        overall_suggestions = self._generate_overall_suggestions(error_count, ability_level, habit_score)
        for sug in overall_suggestions:
            story.append(Paragraph(f"• {sug}", self._get_chinese_style(11)))
            story.append(Spacer(1, 0.3*cm))

        # 构建 PDF
        doc.build(story)
        logger.info(f"综合报告 PDF 已生成：{output_path}")
        return output_path

    def _get_error_evaluation(self, count: int) -> str:
        """错题数量评价"""
        if count == 0:
            return "优秀"
        elif count <= 10:
            return "良好"
        elif count <= 30:
            return "需关注"
        else:
            return "需加强"

    def _get_level_evaluation(self, level: str) -> str:
        """能力等级评价"""
        evaluations = {
            '优秀': '表现突出，继续保持',
            '良好': '稳中有进，潜力可期',
            '中等': '基础扎实，有待提升',
            '需努力': '制定计划，迎头赶上'
        }
        return evaluations.get(level, '持续进步')

    def _get_habit_evaluation(self, score: float) -> str:
        """学习习惯评价"""
        if score >= 90:
            return "习惯优秀"
        elif score >= 75:
            return "习惯良好"
        elif score >= 60:
            return "习惯一般"
        else:
            return "需改善习惯"

    def _generate_overall_suggestions(self, error_count: int, ability_level: str,
                                     habit_score: float) -> List[str]:
        """生成综合评价建议"""
        suggestions = []

        # 基于错题数量
        if error_count > 30:
            suggestions.append("错题数量较多，建议系统梳理知识薄弱点，制定专项提升计划")
        elif error_count > 10:
            suggestions.append("错题数量适中，继续保持错题整理和定期复习的习惯")
        else:
            suggestions.append("错题控制得很好，可适当挑战更高难度的题目")

        # 基于能力等级
        if ability_level == '优秀':
            suggestions.append("综合能力突出，可参加数学拓展活动或竞赛训练")
        elif ability_level == '良好':
            suggestions.append("整体发展良好，针对弱项进行专项练习可进一步提升")

        # 基于习惯得分
        if habit_score < 70:
            suggestions.append("学习习惯有待改善，建议制定规律的学习计划")
        elif habit_score >= 85:
            suggestions.append("学习习惯良好，这是持续进步的重要保障")

        suggestions.append("保持积极的学习态度，相信通过努力一定能取得更大进步")

        return suggestions


def main():
    """测试"""
    exporter = PDFExporter()

    # 模拟数据
    test_records = [
        {'exam_name': '练习 1', 'exam_date': '2024-01-15',
         'knowledge_name': '数的认识', 'error_type': '计算粗心',
         'score': 75, 'error_description': '计算时看错数字'},
        {'exam_name': '练习 2', 'exam_date': '2024-01-20',
         'knowledge_name': '加减法运算', 'error_type': '概念不清',
         'score': 68, 'error_description': '进位加法错误'},
    ]

    test_ability = {
        'abilities': {
            '数感': {'score': 85, 'level': '优秀', 'description': '对数的理解和运用'},
            '符号意识': {'score': 78, 'level': '良好', 'description': '符号运用能力'},
            '空间观念': {'score': 72, 'level': '良好', 'description': '空间想象能力'},
            '数据分析观念': {'score': 80, 'level': '良好', 'description': '数据处理能力'},
            '推理能力': {'score': 75, 'level': '良好', 'description': '逻辑推理能力'},
        },
        'strongest': {'name': '数感', 'score': 85},
        'weakest': {'name': '空间观念', 'score': 72},
        'suggestions': ['继续保持数感优势', '加强空间观念训练']
    }

    # 测试导出
    output_dir = Path(__file__).parent / "exports"
    output_dir.mkdir(exist_ok=True)

    error_pdf = exporter.export_error_report("张三", 1001, test_records,
                                             str(output_dir / "error_report.pdf"))
    print(f"错题报告：{error_pdf}")

    ability_pdf = exporter.export_ability_report("张三", 1001, test_ability,
                                                 str(output_dir / "ability_report.pdf"))
    print(f"能力报告：{ability_pdf}")

    summary_pdf = exporter.export_summary_report("张三", 1001, 15, "良好", 82.5,
                                                 str(output_dir / "summary_report.pdf"))
    print(f"综合报告：{summary_pdf}")


if __name__ == "__main__":
    main()
