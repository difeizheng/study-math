"""
学生成绩分析系统 - Web 界面 (增强版)
集成人教版小学数学知识点深度分析
"""
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 导入日志系统
from logger import init_logging, log_error, log_info, get_logger
from database import init_database, StudentDAO, ErrorRecordDAO
from excel_importer import ExcelDataImporter
from pdf_exporter import PDFExporter
from score_entry import ScoreEntryService

# 初始化日志和数据库
init_logging()
init_database()
logger = get_logger("app")

# 从 Excel 导入学生信息到数据库
def sync_students_from_excel():
    """将 Excel 中的学生信息同步到数据库"""
    from pathlib import Path
    from excel_importer import ExcelDataImporter

    data_dir = Path("data")
    if not data_dir.exists():
        return

    importer = ExcelDataImporter()
    synced_count = 0

    for file in sorted(data_dir.glob("*.xlsx")):
        try:
            df = importer.load_excel(str(file))
            semester = "1(2) 班上 学期"  # 默认学期

            # 从文件名提取学期信息
            import re
            semester_match = re.search(r'(\d+)\((\d)\) 班 ([上下]) 学期', file.name)
            if semester_match:
                semester = f"{semester_match.group(1)}({semester_match.group(2)}) 班 {semester_match.group(3)} 学期"

            students = importer.extract_students_from_excel(df, semester)
            synced_count += len(students)
        except Exception as e:
            logger.error(f"同步 {file.name} 失败：{e}")

    if synced_count > 0:
        logger.info(f"从 Excel 同步 {synced_count} 个学生到数据库")

sync_students_from_excel()

# 原有模块导入
from score_analyzer import ScoreAnalyzer
from deep_analyzer import DeepScoreAnalyzer
from error_tracker import ErrorTracker, ERROR_TYPES
from knowledge_graph import KnowledgeGraph
from ability_portfolio import AbilityPortfolio
from study_habit_analyzer import StudyHabitAnalyzer
from class_dashboard import ClassLearningDashboard
from paper_generator import SmartPaperGenerator

# 页面配置
st.set_page_config(
    page_title="学生成绩分析系统",
    page_icon="📊",
    layout="wide"
)

# 初始化分析器
@st.cache_resource
def get_analyzers():
    logger.info("初始化分析器...")
    analyzer = ScoreAnalyzer("data")
    analyzer.load_all_data()
    deep_analyzer = DeepScoreAnalyzer("data")
    deep_analyzer.load_all_data()
    error_tracker = ErrorTracker("data", "error_db.json")
    error_tracker.set_student_names(analyzer.student_names)
    knowledge_graph = KnowledgeGraph()
    ability_portfolio = AbilityPortfolio()
    habit_analyzer = StudyHabitAnalyzer()
    # 从错题追踪器导入数据
    habit_analyzer.import_from_error_tracker(error_tracker)
    # 班级学情看板
    class_dashboard = ClassLearningDashboard()
    class_dashboard.load_data(
        analyzer.students_df,
        analyzer.semester_data,
        analyzer.student_names,
        deep_analyzer.knowledge_points
    )
    # 智能组卷生成器
    paper_generator = SmartPaperGenerator()
    logger.info("分析器初始化完成")
    return analyzer, deep_analyzer, error_tracker, knowledge_graph, ability_portfolio, habit_analyzer, class_dashboard, paper_generator

analyzer, deep_analyzer, error_tracker, knowledge_graph, ability_portfolio, habit_analyzer, class_dashboard, paper_generator = get_analyzers()

# 获取所有学期列表
ALL_SEMESTERS = list(analyzer.semester_data.keys())

# 标题
st.title("📊 学生成绩分析系统")
st.markdown("### 基于人教版小学数学知识点的深度分析")
st.markdown("---")

# 侧边栏
st.sidebar.header("选择学生")
students = analyzer.get_student_list()
student_dict = {f"{sid} - {name}": sid for sid, name in students}
selected_student_name = st.sidebar.selectbox(
    "选择要分析的学生",
    options=list(student_dict.keys())
)
selected_student_id = student_dict[selected_student_name]

# 获取学生信息
student_name = analyzer.student_names.get(selected_student_id, "Unknown")
st.sidebar.info(f"**学号**: {selected_student_id}\n**姓名**: {student_name}")

# 学期选择
st.sidebar.header("选择学期")

# 初始化学期选择状态
if 'selected_semesters_state' not in st.session_state:
    st.session_state.selected_semesters_state = ALL_SEMESTERS

select_all = st.sidebar.checkbox("全选所有学期", value=True, key="select_all_checkbox")

if select_all:
    # 全选模式：直接使用所有学期
    st.session_state.selected_semesters_state = ALL_SEMESTERS
    selected_semesters = ALL_SEMESTERS
    st.sidebar.info(f"已选择全部 {len(ALL_SEMESTERS)} 个学期")
else:
    # 手动选择模式
    selected_semesters = st.sidebar.multiselect(
        "选择要分析的学期",
        options=ALL_SEMESTERS,
        default=st.session_state.selected_semesters_state if st.session_state.selected_semesters_state else ALL_SEMESTERS[:1],
        key="semester_multiselect"
    )
    # 更新状态
    if selected_semesters:
        st.session_state.selected_semesters_state = selected_semesters

# 分析模式选择
st.sidebar.header("分析模式")
analysis_mode = st.sidebar.radio(
    "选择分析类型",
    ["📈 成绩趋势分析", "🧠 知识点深度分析", "📋 诊断报告", "👥 多学生对比", "⚠️ 成绩预警", "📊 班级分析", "🔬 宏观分析", "📕 错题追踪本", "🕸️ 知识点关联图谱", "🌟 能力成长档案", "📝 学习习惯分析", "🏫 班级学情看板", "📄 智能组卷", "📝 成绩录入"],
    index=0
)

st.sidebar.markdown("---")

# 数据管理
st.sidebar.header("数据管理")
with st.sidebar.expander("📂 Excel 数据导入"):
    uploaded_file = st.file_uploader("上传 Excel 成绩表", type=["xlsx", "xls"])
    if uploaded_file:
        try:
            # 保存上传文件
            from pathlib import Path
            data_dir = Path("data/uploads")
            data_dir.mkdir(parents=True, exist_ok=True)
            file_path = data_dir / uploaded_file.name

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 导入数据
            importer = ExcelDataImporter()
            stats = importer.import_errors_from_excel(str(file_path), "1(2) 班上 学期")

            st.success(f"导入成功！")
            st.json({
                "错题数": stats.get('total_errors', 0),
                "学生数": stats.get('students', 0),
                "考试数": stats.get('exams', 0)
            })
            log_info(f"Excel 导入成功：{uploaded_file.name}, 错题数：{stats.get('total_errors', 0)}")
        except Exception as e:
            st.error(f"导入失败：{e}")
            log_error(e, "Excel 导入失败")

st.sidebar.caption("系统版本：v3.7 (全班成绩录入版)")


# 成绩录入
with st.sidebar.expander("📝 录入考试成绩"):
    entry_exam_name = st.selectbox(
        "考试名称",
        ["练习 1", "练习 2", "练习 3", "练习 4",
         "练习 5", "练习 6", "练习 7", "练习 8",
         "单元测试（一）", "单元测试（二）", "单元测试（三）",
         "期中考试", "期末考试",
         "周测（1）", "周测（2）", "周测（3）"]
    )
    entry_exam_date = st.date_input(
        "考试日期",
        value=datetime.now(),
        min_value=datetime.now().replace(day=datetime.now().day - 7)
    )
    entry_score = st.number_input(
        "考试成绩",
        min_value=0.0,
        max_value=100.0,
        step=0.5
    )

    if st.button("录入成绩", type="primary"):
        st.session_state.show_entry_form = True

    if st.session_state.get('show_entry_form', False):
        st.markdown("**添加错题**")
        wrong_knowledge = st.selectbox(
            "知识点",
            ["1-5 的认识和加减法", "6-10 的认识和加减法", "20 以内进位加法", "20 以内退位减法",
             "认识图形", "认识钟表", "人民币", "表内乘法", "表内除法", "混合运算"],
            key="entry_kp"
        )
        wrong_error_type = st.selectbox(
            "错误类型",
            ["计算粗心", "概念不清", "知识性错误", "审题不清", "公式记错", "理解偏差", "步骤不全", "其他"],
            key="entry_error_type"
        )
        wrong_desc = st.text_input("错题描述", key="entry_wrong_desc")

        if st.button("添加错题"):
            # 初始化错题列表
            if 'wrong_questions' not in st.session_state:
                st.session_state.wrong_questions = []

            st.session_state.wrong_questions.append({
                "knowledge_name": wrong_knowledge,
                "error_type": wrong_error_type,
                "description": wrong_desc
            })
            st.success(f"已添加错题：{wrong_knowledge} - {wrong_error_type}")

        if st.session_state.wrong_questions:
            st.markdown("**已添加错题**:")
            for i, wq in enumerate(st.session_state.wrong_questions, 1):
                st.write(f"{i}. {wq['knowledge_name']} - {wq['error_type']}")

            if st.button("确认提交成绩和错题"):
                service = ScoreEntryService()
                result = service.entry_score(
                    student_id=selected_student_id,
                    exam_name=entry_exam_name,
                    exam_date=entry_exam_date.strftime("%Y-%m-%d"),
                    score=entry_score,
                    wrong_questions=st.session_state.wrong_questions
                )

                if result["success"]:
                    st.success(result["message"])
                    st.session_state.wrong_questions = []
                    st.session_state.show_entry_form = False
                else:
                    st.error(result["message"])

        if st.button("取消"):
            st.session_state.show_entry_form = False
            st.session_state.wrong_questions = []


# 全班成绩录入
with st.sidebar.expander("📋 全班成绩录入"):
    st.markdown("**按学号录入全班成绩**")
    class_exam_name = st.text_input(
        "考试名称",
        placeholder="例如：练习 1、单元测试（一）",
        key="class_exam_name"
    )
    class_exam_date = st.date_input(
        "考试日期",
        value=datetime.now(),
        min_value=datetime.now().replace(day=datetime.now().day - 7),
        key="class_exam_date"
    )

    st.markdown("**学号 - 成绩输入**")
    st.caption("格式：学号，分数（每行一个学生）")
    class_scores_text = st.text_area(
        "成绩列表",
        height=150,
        placeholder="1    95\n2    92\n3    95\n4    88",
        key="class_scores_text"
    )

    auto_create_student = st.checkbox(
        "学号不存在时自动创建学生",
        value=False,
        help="勾选后，如果学号不存在，系统会自动创建该学号的学生（默认 1 年级）"
    )

    if st.button("录入全班成绩", type="primary", key="class_entry_btn"):
        if not class_scores_text.strip():
            st.error("请输入成绩数据")
        else:
            # 解析成绩数据（支持空格、Tab、逗号分隔）
            student_scores = {}
            parse_errors = []
            for line in class_scores_text.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                try:
                    # 支持空格、Tab、逗号分隔
                    import re
                    parts = re.split(r'[,，\t\s]+', line, maxsplit=1)
                    if len(parts) >= 1:
                        student_id = int(parts[0].strip())
                        # 成绩可能为空（缺考）
                        if len(parts) >= 2 and parts[1].strip():
                            score = float(parts[1].strip())
                        else:
                            score = 0.0  # 缺考记为 0 分
                        student_scores[student_id] = score
                    else:
                        parse_errors.append(f"格式错误：{line}")
                except ValueError as e:
                    parse_errors.append(f"解析失败：{line} ({str(e)})")

            if parse_errors:
                st.warning(f"解析警告：\n" + "\n".join(parse_errors[:5]))

            if student_scores:
                # 批量录入
                service = ScoreEntryService()
                result = service.entry_class_scores(
                    exam_name=class_exam_name,
                    exam_date=class_exam_date.strftime("%Y-%m-%d"),
                    student_scores=student_scores,
                    wrong_questions_map={},
                    auto_create_student=auto_create_student
                )

                # 显示不存在的学号
                if result.get("invalid_student_ids") and not auto_create_student:
                    st.error(f"以下学号不存在：{', '.join(map(str, result['invalid_student_ids']))}")
                    st.info(f"有效学号：{result['valid_count']}人，无效学号：{result['invalid_count']}人")
                    st.info("如需自动创建这些学号，请勾选'学号不存在时自动创建学生'选项")

                if result.get("students_to_create") and auto_create_student:
                    st.info(f"已自动创建 {len(result['students_to_create'])} 个新学生：{', '.join(map(str, result['students_to_create']))}")

                if result["success_count"] > 0:
                    st.success(f"录入成功！成功{result['success_count']}人，失败{result['fail_count']}人")
                    st.info(f"共录入 {result['total_errors']} 道错题")

                if result.get("message"):
                    st.error(result["message"])

                # 显示详细信息
                with st.expander("查看详情"):
                    for detail in result["details"]:
                        status = "✅" if detail["success"] else "❌"
                        st.write(f"{status} 学号{detail['student_id']}: {detail['message']}")


# PDF 报告导出
with st.sidebar.expander("📄 PDF 报告导出"):
    export_type = st.selectbox(
        "选择报告类型",
        ["错题分析报告", "能力成长报告", "综合总结报告"]
    )

    if st.button("生成 PDF 报告"):
        try:
            exporter = PDFExporter()
            exports_dir = Path("exports")
            exports_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if export_type == "错题分析报告":
                # 获取错题记录
                error_records = ErrorRecordDAO.get_errors_by_student(selected_student_id)
                if error_records:
                    # 转换为字典格式
                    records_dict = []
                    for record in error_records:
                        records_dict.append({
                            'exam_name': record.exam_name,
                            'exam_date': record.exam_date,
                            'knowledge_name': record.knowledge_name,
                            'error_type': record.error_type,
                            'score': record.score,
                            'error_description': record.error_description
                        })

                    output_path = exports_dir / f"错题报告_{student_name}_{timestamp}.pdf"
                    exporter.export_error_report(student_name, selected_student_id, records_dict, str(output_path))
                    st.success(f"错题报告已生成：{output_path}")

                    # 提供下载链接
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="📥 下载错题报告",
                            data=f.read(),
                            file_name=f"错题报告_{student_name}_{timestamp}.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.warning("暂无错题记录")

            elif export_type == "能力成长报告":
                # 获取知识点掌握情况
                from deep_analyzer import DeepScoreAnalyzer
                mastery = deep_analyzer.analyze_single_student(selected_student_id)

                ability_report = ability_portfolio.analyze_all_abilities(mastery)
                output_path = exports_dir / f"能力报告_{student_name}_{timestamp}.pdf"
                exporter.export_ability_report(student_name, selected_student_id, ability_report, str(output_path))
                st.success(f"能力报告已生成：{output_path}")

                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 下载能力报告",
                        data=f.read(),
                        file_name=f"能力报告_{student_name}_{timestamp}.pdf",
                        mime="application/pdf"
                    )

            elif export_type == "综合总结报告":
                # 综合报告
                error_count = len(ErrorRecordDAO.get_errors_by_student(selected_student_id))

                # 能力等级
                from deep_analyzer import DeepScoreAnalyzer
                mastery = deep_analyzer.analyze_single_student(selected_student_id)
                ability_report = ability_portfolio.analyze_all_abilities(mastery)
                ability_level = ability_report.get("overall_level", "中等")

                # 学习习惯得分
                habit_analysis = habit_analyzer.analyze_student_habits(selected_student_id)
                habit_scores = habit_analysis.habit_scores if habit_analysis else {}
                avg_habit_score = sum(habit_scores.values()) / len(habit_scores) if habit_scores else 0

                output_path = exports_dir / f"综合报告_{student_name}_{timestamp}.pdf"
                exporter.export_summary_report(
                    student_name, selected_student_id,
                    error_count, ability_level,
                    avg_habit_score, str(output_path)
                )
                st.success(f"综合报告已生成：{output_path}")

                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 下载综合报告",
                        data=f.read(),
                        file_name=f"综合报告_{student_name}_{timestamp}.pdf",
                        mime="application/pdf"
                    )

        except Exception as e:
            st.error(f"生成 PDF 失败：{e}")
            log_error(e, "PDF 导出失败")


def filter_scores_by_semester(student_id: int, semesters: list) -> dict:
    """按学期筛选成绩数据"""
    if analyzer.students_df is None:
        return {}

    student_data = analyzer.students_df[analyzer.students_df['学号'] == student_id]
    if student_data.empty:
        return {}

    filtered_scores = {}
    for col in student_data.columns:
        if col in ['学号', '姓名']:
            continue

        # 检查该列是否属于选中的学期
        for sem in semesters:
            if col.startswith(sem):
                value = student_data[col].values[0]
                if pd.notna(value):
                    filtered_scores[col] = value
                break

    return filtered_scores


def calculate_filtered_stats(filtered_scores: dict) -> dict:
    """计算筛选后的统计数据"""
    if not filtered_scores:
        return {}

    scores = list(filtered_scores.values())
    scores_array = pd.Series(scores)

    return {
        '平均分': round(scores_array.mean(), 2),
        '最高分': round(scores_array.max(), 2),
        '最低分': round(scores_array.min(), 2),
        '标准差': round(scores_array.std(), 2),
        '考试次数': len(scores),
        '优秀率': round((scores_array >= 90).sum() / len(scores) * 100, 1),
        '及格率': round((scores_array >= 60).sum() / len(scores) * 100, 1),
    }


def get_filtered_trend(student_id: int, semesters: list) -> pd.DataFrame:
    """获取筛选后的成绩趋势"""
    if analyzer.students_df is None:
        return pd.DataFrame()

    student_data = analyzer.students_df[analyzer.students_df['学号'] == student_id]
    if student_data.empty:
        return pd.DataFrame()

    trends = []
    for semester in semesters:
        semester_cols = [col for col in student_data.columns if col.startswith(semester)]

        for col in semester_cols:
            value = student_data[col].values[0]
            if pd.notna(value):
                exam_name = col.replace(f"{semester}_", "")
                trends.append({
                    '学期': semester,
                    '考试': exam_name,
                    '分数': value
                })

    return pd.DataFrame(trends)


def get_filtered_score_distribution(student_id: int, semesters: list) -> dict:
    """获取筛选后的分数分布"""
    filtered_scores = filter_scores_by_semester(student_id, semesters)
    if not filtered_scores:
        return {}

    scores = list(filtered_scores.values())

    return {
        '90-100': len([s for s in scores if s >= 90]),
        '80-89': len([s for s in scores if 80 <= s < 90]),
        '70-79': len([s for s in scores if 70 <= s < 80]),
        '60-69': len([s for s in scores if 60 <= s < 70]),
        '60 以下': len([s for s in scores if s < 60])
    }


# ==================== 模式 1: 成绩趋势分析 ====================
if analysis_mode == "📈 成绩趋势分析":
    st.header("📈 成绩趋势分析")
    st.markdown(f"当前分析学期：**{', '.join(selected_semesters)}**")

    # 统计卡片
    filtered_scores = filter_scores_by_semester(selected_student_id, selected_semesters)
    stats = calculate_filtered_stats(filtered_scores)

    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("平均分", f"{stats['平均分']}",
                     delta=f"{stats['优秀率']}% 优秀率" if stats['优秀率'] >= 80 else None)
        with col2:
            st.metric("最高分", f"{stats['最高分']}")
        with col3:
            st.metric("最低分", f"{stats['最低分']}")
        with col4:
            st.metric("标准差", f"{stats['标准差']}")

    st.markdown("---")

    # 成绩趋势图
    trend_df = get_filtered_trend(selected_student_id, selected_semesters)
    if not trend_df.empty:
        semesters = trend_df['学期'].unique()

        tabs = st.tabs([f"{sem}" for sem in semesters] + ["总体对比"])

        for i, semester in enumerate(semesters):
            with tabs[i]:
                sem_data = trend_df[trend_df['学期'] == semester]
                if not sem_data.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=sem_data['考试'],
                        y=sem_data['分数'],
                        mode='lines+markers',
                        name=semester,
                        line=dict(width=3, color='#1f77b4'),
                        marker=dict(size=10)
                    ))

                    fig.add_hline(y=90, line_dash="dash", line_color="green",
                                 annotation_text="优秀线 (90)")
                    fig.add_hline(y=60, line_dash="dash", line_color="red",
                                 annotation_text="及格线 (60)")

                    fig.update_layout(
                        xaxis_title="考试",
                        yaxis_title="分数",
                        yaxis_range=[0, 100],
                        height=400
                    )
                    fig.update_xaxes(tickangle=45)

                    st.plotly_chart(fig, use_container_width=True)

        # 总体对比
        with tabs[-1]:
            semester_avg = trend_df.groupby('学期')['分数'].agg(['mean', 'min', 'max']).reset_index()

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=semester_avg['学期'],
                y=semester_avg['mean'],
                name='平均分',
                marker_color='steelblue'
            ))
            fig.add_trace(go.Scatter(
                x=semester_avg['学期'],
                y=semester_avg['max'],
                name='最高分',
                mode='lines+markers',
                line=dict(color='green', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=semester_avg['学期'],
                y=semester_avg['min'],
                name='最低分',
                mode='lines+markers',
                line=dict(color='red', width=2)
            ))

            fig.update_layout(
                title="各学期成绩对比",
                xaxis_title="学期",
                yaxis_title="分数",
                yaxis_range=[0, 100],
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # 分数分布
    st.header("📊 分数分布")
    score_dist = get_filtered_score_distribution(selected_student_id, selected_semesters)
    if score_dist:
        col1, col2 = st.columns(2)

        with col1:
            colors = ['#2ecc71', '#3498db', '#f1c40f', '#e67e22', '#e74c3c']
            fig = px.pie(
                values=list(score_dist.values()),
                names=list(score_dist.keys()),
                title=f"分数段分布 (共{sum(score_dist.values())}次考试)",
                color_discrete_sequence=colors
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                x=list(score_dist.keys()),
                y=list(score_dist.values()),
                labels={'x': '分数段', 'y': '次数'},
                title="各分数段考试次数",
                color=list(score_dist.values()),
                color_continuous_scale='YlGnBu'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# ==================== 模式 2: 知识点深度分析 ====================
elif analysis_mode == "🧠 知识点深度分析":
    st.header("🧠 知识点深度分析")
    st.markdown("基于人教版小学数学知识点体系，分析学生对各知识点的掌握情况")
    st.info(f"📌 当前分析学期：**{', '.join(selected_semesters)}**")

    # 知识领域分析
    st.subheader("📚 四大知识领域表现")
    category_perf = deep_analyzer.analyze_category_performance(selected_student_id)

    if category_perf:
        cols = st.columns(2)
        for i, (cat, data) in enumerate(category_perf.items()):
            with cols[i % 2]:
                cat_icon = {
                    "数与代数": "🔢",
                    "图形与几何": "📐",
                    "统计与概率": "📊",
                    "综合与实践": "🔧"
                }.get(cat, "📖")

                st.markdown(f"### {cat_icon} {cat}")
                st.markdown(f"**能力描述**: {data['description']}")

                # 进度条
                progress = data['avg_score'] / 100
                st.progress(progress)
                st.metric("平均分", data['avg_score'], delta=f"表现：{data['performance']}")
                st.caption(f"涉及知识点：{data['knowledge_count']}个")

    st.markdown("---")

    # 各年级掌握进度
    st.subheader("📈 各年级知识掌握进度")
    grade_progress = deep_analyzer.get_grade_progress(selected_student_id)

    if grade_progress:
        for grade, data in grade_progress.items():
            emoji = "✅" if data['mastery_rate'] >= 80 else "⚠️" if data['mastery_rate'] >= 60 else "❌"

            with st.expander(f"{emoji} {grade} - 平均分：{data['avg_score']} (掌握率：{data['mastery_rate']}%)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("已掌握知识点", f"{data['mastered']}/{data['knowledge_points']}")
                with col2:
                    st.metric("需加强知识点", data['weak'])

                # 雷达图数据
                st.progress(data['mastery_rate'] / 100)

    st.markdown("---")

    # 知识点掌握详情
    st.subheader("🎯 知识点掌握详情")
    mastery = deep_analyzer.analyze_knowledge_mastery(selected_student_id)

    if mastery:
        # 转换为 DataFrame
        mastery_data = []
        for kp_code, data in mastery.items():
            mastery_data.append({
                '知识点编码': kp_code,
                '知识点名称': data['name'],
                '年级': data['grade'],
                '学期': data['semester'],
                '类别': data['category'],
                '平均分': data['avg_score'],
                '掌握程度': data['mastery_level']
            })

        mastery_df = pd.DataFrame(mastery_data)

        # 筛选器
        col1, col2 = st.columns(2)
        with col1:
            grade_filter = st.multiselect(
                "年级筛选",
                options=["一年级", "二年级", "三年级"],
                default=["一年级", "二年级", "三年级"]
            )
        with col2:
            sort_option = st.selectbox("排序方式", ["按分数升序", "按分数降序", "按年级"])

        if grade_filter:
            mastery_df = mastery_df[mastery_df['年级'].isin(grade_filter)]

        if sort_option == "按分数升序":
            mastery_df = mastery_df.sort_values('平均分')
        elif sort_option == "按分数降序":
            mastery_df = mastery_df.sort_values('平均分', ascending=False)

        st.dataframe(
            mastery_df[['知识点名称', '年级', '学期', '平均分', '掌握程度']],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    # 薄弱知识点
    st.subheader("⚠️ 薄弱知识点 (需加强)")
    weak_points = deep_analyzer.get_weak_knowledge_points(selected_student_id, threshold=85)

    if weak_points:
        for wp in weak_points:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 2])
                with col1:
                    st.markdown(f"**{wp['name']}**")
                    st.caption(f"{wp['grade']}{wp['semester']} | {wp['category']}")
                with col2:
                    st.metric("", f"{wp['score']}分")
                with col3:
                    st.info(wp['recommendation'])
                st.divider()
    else:
        st.success("🎉 所有知识点掌握良好，暂无明显薄弱环节！")

# ==================== 模式 3: 诊断报告 ====================
elif analysis_mode == "📋 诊断报告":
    st.header("📋 学习诊断报告")
    st.info(f"📌 当前分析学期：**{', '.join(selected_semesters)}**")

    if st.button("生成诊断报告", type="primary"):
        with st.spinner("正在生成诊断报告..."):
            report = deep_analyzer.generate_report(selected_student_id)

            # 添加学期信息到报告
            report = f"""# 📊 数学学习诊断报告

**分析学期**: {', '.join(selected_semesters)}

""" + report

            # 下载按钮
            st.download_button(
                label="📥 下载报告",
                data=report,
                file_name=f"{student_name}_数学学习诊断报告.md",
                mime="text/markdown"
            )

            st.markdown("---")
            st.markdown(report)

# ==================== 模式 4: 多学生对比 ====================
elif analysis_mode == "👥 多学生对比":
    st.header("👥 多学生对比分析")
    st.info(f"📌 当前分析学期：**{', '.join(selected_semesters)}**")

    compare_students = st.multiselect(
        "选择要对比的学生（2-5 名）",
        options=list(student_dict.keys()),
        default=[selected_student_name],
        max_selections=5
    )

    if len(compare_students) >= 2:
        compare_ids = [student_dict[name] for name in compare_students]

        # 基础统计对比
        st.subheader("📊 基础统计对比")
        comparison_df = analyzer.compare_students(compare_ids)

        if not comparison_df.empty:
            # 对比图表
            fig = go.Figure()

            for _, row in comparison_df.iterrows():
                fig.add_trace(go.Bar(
                    name=f"{row['姓名']}",
                    x=['平均分', '最高分', '最低分'],
                    y=[row['平均分'], row['最高分'], row['最低分']]
                ))

            fig.update_layout(
                title="学生成绩对比",
                barmode='group',
                yaxis_range=[0, 100],
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            # 数据表
            display_df = comparison_df[['姓名', '学号', '平均分', '最高分', '最低分', '标准差', '优秀率', '及格率']].copy()
            display_df.columns = ['姓名', '学号', '平均分', '最高分', '最低分', '标准差', '优秀率 (%)', '及格率 (%)']
            st.dataframe(display_df, use_container_width=True, hide_index=True)

        # 知识领域对比
        st.subheader("🧠 知识领域对比")
        category_data = []
        for sid in compare_ids:
            name = analyzer.student_names.get(sid, 'Unknown')
            cat_perf = deep_analyzer.analyze_category_performance(sid)
            for cat, data in cat_perf.items():
                category_data.append({
                    '学生': name,
                    '知识领域': cat,
                    '平均分': data['avg_score'],
                    '表现': data['performance']
                })

        if category_data:
            category_df = pd.DataFrame(category_data)

            fig = px.bar(
                category_df,
                x='学生',
                y='平均分',
                color='知识领域',
                barmode='group',
                title="各学生知识领域平均分对比",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

        # 雷达图对比
        st.subheader("🎯 能力雷达图")
        if len(compare_ids) <= 4:
            # 获取第一个学生的知识领域作为雷达图维度
            first_cat_perf = deep_analyzer.analyze_category_performance(compare_ids[0])
            categories = list(first_cat_perf.keys()) if first_cat_perf else []

            if categories:
                fig = go.Figure()

                for sid in compare_ids:
                    name = analyzer.student_names.get(sid, 'Unknown')
                    cat_perf = deep_analyzer.analyze_category_performance(sid)

                    values = [cat_perf.get(cat, {}).get('avg_score', 0) for cat in categories]
                    values.append(values[0])  # 闭合雷达图

                    fig.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories + [categories[0]],
                        fill='toself',
                        name=name
                    ))

                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )),
                    showlegend=True,
                    title="知识领域能力雷达图",
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)

# ==================== 模式 5: 成绩预警 ====================
elif analysis_mode == "⚠️ 成绩预警":
    st.header("⚠️ 成绩预警")
    st.markdown("智能监测学生学习状态，及时发现潜在问题")

    alerts = analyzer.get_score_alerts(selected_student_id)

    if not alerts:
        st.success("✅ 暂无预警，该学生学习状态良好！")
    else:
        for alert in alerts:
            icon = {"warning": "⚠️", "error": "🔴", "info": "ℹ️", "success": "✅"}.get(alert['level'], "📌")

            with st.container():
                st.markdown(f"### {icon} {alert['type']}")
                st.info(alert['message'])
                st.success(f"💡 **建议**: {alert['suggestion']}")
                st.divider()

    # 学习建议
    st.subheader("📝 个性化学习建议")

    # 获取薄弱知识点
    weak_points = deep_analyzer.get_weak_knowledge_points(selected_student_id, threshold=85)

    if weak_points:
        st.markdown("**需要加强的知识点：**")
        for i, wp in enumerate(weak_points[:5], 1):
            with st.expander(f"{i}. {wp['name']} - {wp['score']}分 ({wp['level']})"):
                st.markdown(f"**年级**: {wp['grade']}{wp['semester']}")
                st.markdown(f"**类别**: {wp['category']}")
                st.markdown(f"**学习建议**: {wp['recommendation']}")
    else:
        st.markdown("✅ 所有知识点掌握良好！")

    # 排名信息
    st.subheader("🏆 班级排名")
    rank_info = analyzer.get_score_rank(selected_student_id)
    if rank_info:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("班级排名", f"第{rank_info['rank']}名")
        with col2:
            st.metric("总人数", f"{rank_info['total']}人")
        with col3:
            if rank_info['top_3']:
                st.metric("表现", "🌟 前 3 名")
            elif rank_info['top_10_percent']:
                st.metric("表现", "👍 前 10%")
            else:
                st.metric("表现", "💪 继续加油")

# ==================== 模式 6: 班级分析 ====================
elif analysis_mode == "📊 班级分析":
    st.header("📊 班级整体分析")
    st.markdown("查看班级整体学习情况和成绩分布")

    # 学期选择
    selected_semester = st.selectbox(
        "选择要分析的学期",
        options=ALL_SEMESTERS,
        index=0
    )

    if selected_semester:
        class_stats = analyzer.get_class_analysis(selected_semester)

        if class_stats:
            # 统计卡片
            st.subheader("📈 整体统计")
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("学生总数", class_stats['total_students'])
            with col2:
                st.metric("班级平均分", class_stats['class_avg'])
            with col3:
                st.metric("优秀率", f"{class_stats['excellent_rate']}%")
            with col4:
                st.metric("及格率", f"{class_stats['pass_rate']}%")
            with col5:
                st.metric("分数极差", round(class_stats['highest_avg'] - class_stats['lowest_avg'], 1))

            st.markdown("---")

            # 分数段分布
            st.subheader("📊 分数段分布")

            dist_data = list(class_stats['distribution'].items())
            dist_labels = [item[0] for item in dist_data]
            dist_values = [item[1] for item in dist_data]

            col1, col2 = st.columns(2)

            with col1:
                # 柱状图
                fig_bar = px.bar(
                    x=dist_labels,
                    y=dist_values,
                    labels={'x': '分数段', 'y': '人数'},
                    title='各分数段人数分布',
                    color=dist_values,
                    color_continuous_scale='YlGnBu'
                )
                fig_bar.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                # 饼图
                colors = ['#e74c3c', '#e67e22', '#f1c40f', '#3498db', '#2ecc71']
                fig_pie = px.pie(
                    values=dist_values,
                    names=dist_labels,
                    title='分数段占比',
                    color_discrete_sequence=colors
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("---")

            # 成绩分布直方图
            st.subheader("📈 成绩分布直方图")

            if class_stats['scores']:
                fig_hist = px.histogram(
                    class_stats['scores'],
                    nbins=20,
                    labels={'value': '平均分', 'count': '人数'},
                    title='学生平均分分布直方图',
                    color_discrete_sequence=['#3498db']
                )
                fig_hist.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_hist, use_container_width=True)

            # 详细数据表
            with st.expander("📋 查看详细数据表"):
                # 获取该学期所有学生成绩
                semester_df = analyzer.semester_data.get(selected_semester)
                if semester_df is not None:
                    # 计算每个学生的平均分
                    student_avgs = []
                    for _, row in semester_df.iterrows():
                        scores = []
                        for col in semester_df.columns:
                            if col not in ['学号', '姓名']:
                                val = row[col]
                                if pd.notna(val):
                                    try:
                                        scores.append(float(val))
                                    except (ValueError, TypeError):
                                        pass
                        if scores:
                            student_avgs.append({
                                '学号': int(row['学号']),
                                '姓名': row['姓名'],
                                '平均分': round(sum(scores) / len(scores), 2),
                                '最高分': max(scores),
                                '最低分': min(scores),
                                '考试次数': len(scores)
                            })

                    # 按平均分降序排列
                    student_avgs.sort(key=lambda x: x['平均分'], reverse=True)

                    # 添加排名
                    for i, s in enumerate(student_avgs, 1):
                        s['排名'] = i

                    # 显示表格
                    df_display = pd.DataFrame(student_avgs)
                    st.dataframe(
                        df_display[['排名', '学号', '姓名', '平均分', '最高分', '最低分', '考试次数']],
                        use_container_width=True,
                        hide_index=True
                    )

# ==================== 模式 7: 宏观综合分析 ====================
elif analysis_mode == "🔬 宏观分析":
    st.header("🔬 宏观综合分析")
    st.markdown("基于教育测量学的定量与定性综合分析")

    # 添加对比功能选择
    compare_mode = st.checkbox("🔍 启用两人对比模式", value=False)

    if compare_mode:
        # 选择第二个学生进行对比
        selected_student_name_2 = st.sidebar.selectbox(
            "选择要对比的学生",
            options=list(student_dict.keys()),
            key="compare_student_select"
        )
        selected_student_id_2 = student_dict[selected_student_name_2]

        # 获取对比数据
        compare_data = analyzer.compare_two_students(selected_student_id, selected_student_id_2)

        if 'error' in compare_data:
            st.error(compare_data['error'])
        else:
            st.subheader("📊 SAI 对比总览")

            student_1 = compare_data['student_1']
            student_2 = compare_data['student_2']

            # 对比卡片
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"#### {student_1['name']}")
                st.metric("SAI 指数", f"{student_1['sai']}")
                st.metric("SAI 等级", student_1['grade'])
                st.metric("班级排名", f"第{student_1['rank']}名")

            with col2:
                st.markdown("#### 差异")
                sai_diff = compare_data['sai_difference']
                if sai_diff > 0:
                    st.metric("SAI 差异", f"+{sai_diff}", delta=f"{student_1['name']}更高")
                elif sai_diff < 0:
                    st.metric("SAI 差异", f"{sai_diff}", delta=f"{student_2['name']}更高")
                else:
                    st.metric("SAI 差异", "持平")

                rank_diff = student_1['rank'] - student_2['rank']
                if rank_diff > 0:
                    st.metric("排名差异", f"+{rank_diff}", delta=f"{student_2['name']}领先")
                elif rank_diff < 0:
                    st.metric("排名差异", f"{rank_diff}", delta=f"{student_1['name']}领先")
                else:
                    st.metric("排名差异", "持平")

            with col3:
                st.markdown(f"#### {student_2['name']}")
                st.metric("SAI 指数", f"{student_2['sai']}")
                st.metric("SAI 等级", student_2['grade'])
                st.metric("班级排名", f"第{student_2['rank']}名")

            st.markdown("---")

            # SAI 构成对比（堆叠柱状图）
            st.subheader("📊 SAI 构成对比")

            components_data = {
                '维度': ['学业水平\n(50%)', '稳定性\n(15%)', '趋势\n(10%)', '近期趋势\n(10%)', '优秀率\n(15%)'],
                student_1['name']: [
                    compare_data['diff_analysis']['mean']['student_1'],
                    compare_data['diff_analysis']['stability']['student_1'],
                    compare_data['diff_analysis']['trend']['student_1'],
                    compare_data['diff_analysis']['recent_trend']['student_1'],
                    compare_data['diff_analysis']['excellent_rate']['student_1'],
                ],
                student_2['name']: [
                    compare_data['diff_analysis']['mean']['student_2'],
                    compare_data['diff_analysis']['stability']['student_2'],
                    compare_data['diff_analysis']['trend']['student_2'],
                    compare_data['diff_analysis']['recent_trend']['student_2'],
                    compare_data['diff_analysis']['excellent_rate']['student_2'],
                ],
            }

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name=student_1['name'],
                y=components_data['维度'],
                x=components_data[student_1['name']],
                orientation='h',
                marker_color='#3498db'
            ))
            fig.add_trace(go.Bar(
                name=student_2['name'],
                y=components_data['维度'],
                x=components_data[student_2['name']],
                orientation='h',
                marker_color='#e74c3c'
            ))

            fig.update_layout(
                barmode='group',
                height=400,
                xaxis_title="得分",
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

            # 详细数据对比
            st.subheader("📋 详细数据对比")

            comp_data = compare_data['diff_analysis']
            对比_df = pd.DataFrame({
                '维度': ['学业水平', '稳定性', '发展趋势', '近期趋势', '优秀率'],
                student_1['name']: [
                    f"{comp_data['mean']['student_1']:.1f}",
                    f"{comp_data['stability']['student_1']:.1f} (CV={comp_data['stability']['cv_1']:.3f})",
                    f"{comp_data['trend']['student_1']:.1f} (斜率={comp_data['trend']['slope_1']:.3f})",
                    f"{comp_data['recent_trend']['student_1']:.1f} (Δ={comp_data['recent_trend']['change_1']:.1f})",
                    f"{comp_data['excellent_rate']['student_1']:.1f}%",
                ],
                student_2['name']: [
                    f"{comp_data['mean']['student_2']:.1f}",
                    f"{comp_data['stability']['student_2']:.1f} (CV={comp_data['stability']['cv_2']:.3f})",
                    f"{comp_data['trend']['student_2']:.1f} (斜率={comp_data['trend']['slope_2']:.3f})",
                    f"{comp_data['recent_trend']['student_2']:.1f} (Δ={comp_data['recent_trend']['change_2']:.1f})",
                    f"{comp_data['excellent_rate']['student_2']:.1f}%",
                ],
            })
            st.dataframe(对比_df, use_container_width=True, hide_index=True)

            st.markdown("---")

            # 差异原因分析
            st.subheader("💡 差异原因分析")

            for line in compare_data['explanation']:
                if line:
                    st.markdown(line)

            st.markdown("---")

            # 各维度优势分析
            st.subheader("📈 各维度优势对比")

            sorted_factors = compare_data['sorted_factors']
            for i, (factor, diff_abs, diff) in enumerate(sorted_factors, 1):
                factor_names = {
                    'mean': '学业水平（平均分）',
                    'stability': '成绩稳定性',
                    'trend': '发展趋势（斜率）',
                    'recent_trend': '近期趋势',
                    'excellent_rate': '优秀率',
                }
                higher_name = student_1['name'] if diff > 0 else student_2['name']
                lower_name = student_2['name'] if diff > 0 else student_1['name']

                with st.expander(f"{i}. {factor_names[factor]}: {higher_name} 领先 {abs(diff):.1f}分"):
                    if factor == 'mean':
                        st.write(f"- {student_1['name']}: {comp_data['mean']['raw_1']:.4f} (标准化)")
                        st.write(f"- {student_2['name']}: {comp_data['mean']['raw_2']:.4f} (标准化)")
                    elif factor == 'stability':
                        st.write(f"- {student_1['name']}: CV={comp_data['stability']['cv_1']:.4f}")
                        st.write(f"- {student_2['name']}: CV={comp_data['stability']['cv_2']:.4f}")
                        st.info("变异系数越小，成绩越稳定")
                    elif factor == 'trend':
                        st.write(f"- {student_1['name']}: 斜率={comp_data['trend']['slope_1']:.3f}")
                        st.write(f"- {student_2['name']}: 斜率={comp_data['trend']['slope_2']:.3f}")
                        st.info("斜率>0 表示进步，<0 表示退步")
                    elif factor == 'recent_trend':
                        st.write(f"- {student_1['name']}: 近期变化={comp_data['recent_trend']['change_1']:.2f}")
                        st.write(f"- {student_2['name']}: 近期变化={comp_data['recent_trend']['change_2']:.2f}")
                    elif factor == 'excellent_rate':
                        st.write(f"- {student_1['name']}: {comp_data['excellent_rate']['rate_1']:.1f}%")
                        st.write(f"- {student_2['name']}: {comp_data['excellent_rate']['rate_2']:.1f}%")

            # 显示单个学生的详细分析
            st.markdown("---")
            st.subheader(f"📊 {student_1['name']} 详细分析")
            with st.expander(f"查看 {student_1['name']} 的完整分析报告"):
                macro_1 = student_1['macro']
                st.markdown(macro_1['summary'].replace('\n', '\n\n'))
                st.markdown("**建议：**")
                for rec in macro_1['recommendations']:
                    st.markdown(f"- {rec}")

            st.subheader(f"📊 {student_2['name']} 详细分析")
            with st.expander(f"查看 {student_2['name']} 的完整分析报告"):
                macro_2 = student_2['macro']
                st.markdown(macro_2['summary'].replace('\n', '\n\n'))
                st.markdown("**建议：**")
                for rec in macro_2['recommendations']:
                    st.markdown(f"- {rec}")

    else:
        # 单人分析模式（原有逻辑）
        # 获取综合分析数据
        macro_data = analyzer.analyze_student_development(selected_student_id)

        if 'error' in macro_data:
            st.error(macro_data['error'])
        else:
            # SAI 指数卡片
            st.subheader("📊 学业发展指数 (SAI)")
            sai = macro_data['sai']

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                # SAI 等级
                grade_colors = {'A+': '#2ecc71', 'A': '#3498db', 'B+': '#f1c40f', 'B': '#e67e22', 'C+': '#e74c3c', 'C': '#c0392b', 'D': '#922b21'}
                grade = sai['grade']
                color = grade_colors.get(grade, '#95a5a6')

                st.markdown(f"""
                <div style='background-color: {color}; padding: 15px; border-radius: 10px; text-align: center;'>
                    <h2 style='color: white; margin: 0;'>{grade}</h2>
                    <p style='color: white; margin: 5px 0 0 0;'>综合等级</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.metric("SAI 指数", f"{sai['index']}/100")
            with col3:
                st.metric("预估百分位", f"Top {sai['percentile']}%")
            with col4:
                qual = macro_data['qualitative']
                st.metric("学业水平", qual['level'])

            # 定性分析结论
            st.subheader("📝 综合分析结论")
            st.info(macro_data['summary'].replace('\n', '\n\n'))

            st.markdown("---")

            # 定量分析详情
            st.subheader("📈 定量分析指标")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 集中趋势")
                quant = macro_data['quantitative']
                st.metric("平均分", quant['mean'])
                st.metric("中位数", quant['median'])

                st.markdown("#### 离散程度")
                st.metric("标准差", quant['std'])
                st.metric("变异系数 (CV)", f"{quant['cv']:.4f}")
                st.metric("极差", quant['range'])

            with col2:
                st.markdown("#### 分布形态")
                st.metric("偏度", quant['skewness'],
                         delta="左偏" if quant['skewness'] < -0.5 else "右偏" if quant['skewness'] > 0.5 else "对称")
                st.metric("峰度", quant['kurtosis'],
                         delta="尖峰" if quant['kurtosis'] > 0 else "平峰" if quant['kurtosis'] < 0 else "正常")

                st.markdown("#### 发展趋势")
                st.metric("斜率", quant['slope'],
                         delta="进步" if quant['slope'] > 0 else "退步" if quant['slope'] < 0 else "稳定")
                st.metric("相关系数", quant['correlation'])

            # 趋势图
            st.markdown("---")
            st.subheader("📈 成绩趋势与拟合线")

            # 获取成绩趋势数据
            trend_df = analyzer.get_score_trend(selected_student_id)
            if not trend_df.empty:
                # 添加序号
                trend_df['序号'] = range(1, len(trend_df) + 1)

            fig = go.Figure()

            # 实际成绩点
            fig.add_trace(go.Scatter(
                x=trend_df['序号'],
                y=trend_df['分数'],
                mode='markers',
                name='实际成绩',
                marker=dict(size=10, color='#3498db')
            ))

            # 趋势线
            from scipy import stats
            x = trend_df['序号'].values
            y = trend_df['分数'].values
            if len(x) >= 2:
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                trend_line = slope * x + intercept

                fig.add_trace(go.Scatter(
                    x=x,
                    y=trend_line,
                    mode='lines',
                    name=f'趋势线 (斜率={slope:.2f})',
                    line=dict(color='#e74c3c', width=2, dash='dash')
                ))

            fig.update_layout(
                xaxis_title="考试次序",
                yaxis_title="分数",
                yaxis_range=[0, 100],
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 定性分析
        st.subheader("📋 定性评价")
        qual = macro_data['qualitative']

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**学业成就等级**")
            st.info(f"{qual['level']}\n\n{qual['level_desc']}")
        with col2:
            st.markdown(f"**成绩稳定性**")
            stability_emoji = "✅" if "稳定" in qual['stability'] else "⚠️" if "波动" in qual['stability'] else "👌"
            st.info(f"{stability_emoji} {qual['stability']}")
        with col3:
            st.markdown(f"**发展趋势**")
            trend_emoji = "📈" if "进步" in qual['trend'] else "📉" if "退步" in qual['trend'] else "➡️"
            st.info(f"{trend_emoji} {qual['trend']}")

        st.markdown("---")

        # 建议
        st.subheader("💡 针对性建议")
        for i, rec in enumerate(macro_data['recommendations'], 1):
            st.markdown(f"{i}. {rec}")

# ==================== 模式 8: 错题追踪本 ====================
elif analysis_mode == "📕 错题追踪本":
    st.header("📕 错题追踪本")
    st.markdown("基于艾宾浩斯遗忘曲线，科学管理错题复习")

    # 错题统计卡片
    stats = error_tracker.get_error_statistics(selected_student_id)

    if stats.get("total", 0) == 0:
        st.info("📌 暂无错题记录。点击下方'添加错题'按钮开始记录。")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("错题总数", stats["total"])
        with col2:
            st.metric("已掌握", stats["mastered"], delta=f"掌握率{stats['mastery_rate']}%")
        with col3:
            st.metric("待复习", stats["pending_review"])
        with col4:
            st.metric("新错题", stats["new_errors"])

    st.markdown("---")

    # 子菜单
    error_tab1, error_tab2, error_tab3, error_tab4, error_tab5 = st.tabs([
        "📝 添加错题", "📊 错题统计", "📅 复习计划", "📕 错题本", "💡 举一反三"
    ])

    # ========== 标签 1: 添加错题 ==========
    with error_tab1:
        st.subheader("📝 添加错题记录")

        with st.form("add_error_form"):
            col1, col2 = st.columns(2)

            with col1:
                # 选择学期
                exam_semester = st.selectbox("选择学期", options=ALL_SEMESTERS)
                # 考试名称
                exam_name = st.text_input("考试名称", placeholder="如：单元 3、练习 5、期中")
                # 考试日期
                exam_date = st.date_input("考试日期", value=datetime.now())

            with col2:
                # 选择知识点
                from deep_analyzer import KNOWLEDGE_SYSTEM
                kp_options = {f"{kp.name} ({kp.grade}{kp.semester})": code for code, kp in KNOWLEDGE_SYSTEM.items()}
                selected_kp_name = st.selectbox("选择知识点", options=list(kp_options.keys()))
                selected_kp_code = kp_options[selected_kp_name]

                # 错误类型
                error_type = st.selectbox("错误类型", options=list(ERROR_TYPES.keys()))
                # 得分
                error_score = st.slider("得分 (0-100)", 0, 100, 70)

            # 错误描述
            error_description = st.text_area("错误描述（可选）", placeholder="描述具体错误情况，如：计算进位错误、概念不清等")

            submitted = st.form_submit_button("✅ 添加错题", type="primary")

            if submitted:
                if not exam_name:
                    st.error("请填写考试名称")
                else:
                    from datetime import datetime
                    error_tracker.add_error(
                        student_id=selected_student_id,
                        exam_name=exam_name,
                        exam_date=exam_date.strftime("%Y-%m-%d"),
                        semester=exam_semester,
                        knowledge_code=selected_kp_code,
                        error_type=error_type,
                        score=error_score,
                        error_description=error_description
                    )
                    st.success("✅ 错题已添加!")
                    st.rerun()

    # ========== 标签 2: 错题统计 ==========
    with error_tab2:
        st.subheader("📊 错题分布统计")

        if stats.get("total", 0) > 0:
            # 错误类型分布
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 按错误类型")
                error_type_dist = stats.get("error_types", {})
                if error_type_dist:
                    fig = px.pie(
                        values=list(error_type_dist.values()),
                        names=list(error_type_dist.keys()),
                        title="错误类型分布"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### 按知识点")
                kp_dist = {data["name"]: data["count"] for kp_code, data in stats.get("knowledge_points", {}).items()}
                if kp_dist:
                    fig = px.bar(
                        x=list(kp_dist.keys()),
                        y=list(kp_dist.values()),
                        labels={"x": "知识点", "y": "错题数"},
                        title="知识点错题分布"
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

            # 详细数据表
            st.markdown("#### 各知识点掌握情况")
            kp_data = []
            for kp_code, data in stats.get("knowledge_points", {}).items():
                kp_data.append({
                    "知识点": data["name"],
                    "错题数": data["count"],
                    "已掌握": data["mastered"],
                    "未掌握": data["count"] - data["mastered"],
                    "掌握率": f"{round(data['mastered']/data['count']*100, 1) if data['count'] > 0 else 0}%"
                })

            if kp_data:
                st.dataframe(pd.DataFrame(kp_data), use_container_width=True, hide_index=True)
        else:
            st.info("暂无统计数据")

    # ========== 标签 3: 复习计划 ==========
    with error_tab3:
        st.subheader("📅 今日复习计划")

        review_plan = error_tracker.get_review_plan(selected_student_id)

        if review_plan:
            st.info(f"📌 今日需要复习 {len(review_plan)} 道错题")

            for i, item in enumerate(review_plan, 1):
                error = item["error"]
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.markdown(f"**{i}. {error.knowledge_name}**")
                        st.caption(f"来源：{error.exam_name} | 错误类型：{error.error_type}")

                    with col2:
                        st.metric("复习次数", f"{error.review_count}次")

                    with col3:
                        overdue = item["days_overdue"]
                        if overdue > 0:
                            st.error(f"逾期{overdue}天")
                        else:
                            st.success("到期")

                    with col4:
                        # 复习按钮
                        if st.button("✅ 已复习", key=f"review_{id(error)}"):
                            error_tracker.mark_error_mastered(error.student_id, error.knowledge_code)
                            st.success("已标记为复习!")
                            st.rerun()

                    st.divider()
        else:
            st.success("🎉 没有需要复习的错题！")
            st.info("新添加的错题会根据艾宾浩斯遗忘曲线自动安排复习时间")

    # ========== 标签 4: 错题本 ==========
    with error_tab4:
        st.subheader("📕 我的错题本")

        if stats.get("total", 0) > 0:
            # 筛选器
            filter_type = st.selectbox(
                "筛选错误类型",
                options=["全部"] + list(ERROR_TYPES.keys())
            )

            # 获取错题列表
            errors = error_tracker.get_student_errors(selected_student_id)

            if filter_type != "全部":
                errors = [e for e in errors if e.error_type == filter_type]

            # 显示错题
            for i, error in enumerate(errors, 1):
                with st.expander(f"{i}. {error.knowledge_name} - {error.exam_name} ({error.error_type})"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"""
                        **考试日期**: {error.exam_date}
                        **记录日期**: {error.created_at}
                        **得分**: {error.score}分
                        """)

                    with col2:
                        st.markdown(f"""
                        **复习次数**: {error.review_count}次
                        **最后复习**: {error.last_review or '未复习'}
                        **状态**: {'✅ 已掌握' if error.mastered else '⏳ 未掌握'}
                        """)

                    if error.error_description:
                        st.markdown(f"**错误描述**: {error.error_description}")

            # 导出按钮
            st.markdown("---")
            error_book = error_tracker.export_error_book(selected_student_id)
            st.download_button(
                label="📥 导出错题本 (Markdown)",
                data=error_book,
                file_name=f"{student_name}_错题本.md",
                mime="text/markdown"
            )
        else:
            st.info("暂无错题记录")

    # ========== 标签 5: 举一反三 ==========
    with error_tab5:
        st.subheader("💡 举一反三练习推荐")

        recommendations = error_tracker.get_practice_recommendations(selected_student_id)

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                with st.container():
                    st.markdown(f"**{i}. {rec['knowledge_name']}**")
                    st.caption(f"错误次数：{rec['error_count']} | 错误类型：{', '.join(rec['error_types'])}")

                    st.info(f"💡 **建议**: {rec['suggestion']}")

                    st.markdown("**📝 练习题**:")
                    for q in rec['practice_questions']:
                        st.markdown(f"- {q}")

                    st.divider()
        else:
            st.success("🎉 没有薄弱知识点，继续保持!")

# ==================== 模式 9: 知识点关联图谱 ====================
elif analysis_mode == "🕸️ 知识点关联图谱":
    st.header("🕸️ 知识点关联图谱")
    st.markdown("展示知识点之间的前后置依赖关系，帮助发现知识断层的根源")

    # 子菜单
    kg_tab1, kg_tab2, kg_tab3, kg_tab4 = st.tabs([
        "🔍 查询知识点", "📊 掌握情况分析", "🎯 学习路径推荐", "🔗 依赖关系图"
    ])

    # ========== 标签 1: 查询知识点 ==========
    with kg_tab1:
        st.subheader("🔍 查询知识点")

        # 选择知识点
        from deep_analyzer import KNOWLEDGE_SYSTEM
        kp_options = {f"{kp.name} ({kp.grade}{kp.semester})": code for code, kp in KNOWLEDGE_SYSTEM.items()}
        selected_kp_name = st.selectbox("选择知识点", options=list(kp_options.keys()), key="kg_select")
        selected_kp_code = kp_options[selected_kp_name]

        kp_info = knowledge_graph.nodes.get(selected_kp_code)
        if kp_info:
            # 基本信息
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("年级", kp_info.grade)
            with col2:
                st.metric("学期", kp_info.semester)
            with col3:
                st.metric("类别", kp_info.category)
            with col4:
                st.metric("重要性", "⭐" * kp_info.importance)

            st.markdown("---")

            # 前置知识
            st.markdown("### 📚 前置知识（需要先掌握）")
            prereqs = knowledge_graph.get_prerequisites(selected_kp_code, recursive=True)
            if prereqs:
                for code in prereqs:
                    node = knowledge_graph.nodes.get(code)
                    if node:
                        status_icon = "✅" if code in [] else "📖"
                        st.markdown(f"{status_icon} **{node.name}** - {node.grade}{node.semester}")
            else:
                st.info("该知识点无前置要求，可直接学习")

            st.markdown("---")

            # 后置知识
            st.markdown("### 📖 后置知识（学完后可以继续）")
            deps = knowledge_graph.get_dependencies(selected_kp_code, recursive=True)
            if deps:
                for code in deps:
                    node = knowledge_graph.nodes.get(code)
                    if node:
                        st.markdown(f"➡️ **{node.name}** - {node.grade}{node.semester}")
            else:
                st.info("该知识点是终极目标，无后续依赖")

    # ========== 标签 2: 掌握情况分析 ==========
    with kg_tab2:
        st.subheader("📊 知识点掌握情况分析")
        st.markdown("分析薄弱知识点对后续学习的影响")

        # 获取学生的薄弱知识点
        weak_points = deep_analyzer.get_weak_knowledge_points(selected_student_id, threshold=85)

        if weak_points:
            st.warning(f"发现 {len(weak_points)} 个薄弱知识点（得分<85 分）")

            # 选择要分析的薄弱知识点
            weak_options = {f"{wp['name']} ({wp['score']}分)": wp['code'] for wp in weak_points}
            selected_weak = st.selectbox("选择要分析的薄弱知识点", options=list(weak_options.keys()))
            selected_weak_code = weak_options[selected_weak]

            # 分析影响
            impact = knowledge_graph.analyze_weak_point_impact([selected_weak_code])

            col1, col2, col3 = st.columns(3)
            with col1:
                risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(impact["risk_level"], "⚪")
                st.metric("影响范围风险", f"{risk_emoji} {impact['risk_level'].upper()}")
            with col2:
                st.metric("直接影响知识点", len(impact["direct_impact"]))
            with col3:
                st.metric("间接影响知识点", len(impact["indirect_impact"]))

            if impact["direct_impact"]:
                st.markdown("**🔴 直接受影响的知识点：**")
                for code in impact["direct_impact"]:
                    node = knowledge_graph.nodes.get(code)
                    if node:
                        st.markdown(f"  - {node.name} ({node.grade}{node.semester})")

            if impact["indirect_impact"]:
                st.markdown("**🟡 间接受影响的知识点：**")
                for code in impact["indirect_impact"][:10]:  # 最多显示 10 个
                    node = knowledge_graph.nodes.get(code)
                    if node:
                        st.markdown(f"  - {node.name} ({node.grade}{node.semester})")
                if len(impact["indirect_impact"]) > 10:
                    st.markdown(f"  ... 还有 {len(impact['indirect_impact']) - 10} 个")
        else:
            st.success("🎉 所有知识点掌握良好（>=85 分），无明显薄弱环节！")

    # ========== 标签 3: 学习路径推荐 ==========
    with kg_tab3:
        st.subheader("🎯 学习路径推荐")

        # 分析学生已掌握的知识点（>=85 分）
        mastery = deep_analyzer.analyze_knowledge_mastery(selected_student_id)
        mastered_knowledge = [code for code, data in mastery.items() if data["avg_score"] >= 85]

        st.info(f"已掌握 {len(mastered_knowledge)} 个知识点（>=85 分）")

        # 年级过滤
        grade_filter = st.selectbox(
            "选择推荐范围",
            options=["全部", "一年级", "二年级", "三年级"]
        )
        grade_value = None if grade_filter == "全部" else grade_filter

        # 获取推荐
        recommendations = knowledge_graph.get_recommended_learning_order(
            mastered_knowledge,
            grade_filter=grade_value
        )

        if recommendations:
            st.success(f"推荐学习 {len(recommendations)} 个知识点")

            for i, rec in enumerate(recommendations[:15], 1):
                with st.container():
                    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])

                    with col1:
                        st.markdown(f"**{i}. {rec['name']}**")
                        st.caption(f"{rec['grade']}{rec['semester']} | {rec['category']}")

                    with col2:
                        importance = "⭐" * rec["importance"]
                        st.markdown(importance)

                    with col3:
                        difficulty = "🔥" * rec["difficulty"]
                        st.markdown(difficulty)

                    with col4:
                        readiness = rec.get('readiness', 0)
                        if readiness >= 100:
                            st.success("可学习")
                        else:
                            st.caption(f"准备度{readiness}%")

                    st.divider()
        else:
            st.info("没有更多推荐，已掌握所有知识点！")

        # 针对特定知识点的学习路径
        st.markdown("---")
        st.subheader("📋 查询特定知识点的完整学习路径")

        target_kp = st.selectbox(
            "选择目标知识点",
            options=list(kp_options.keys()),
            key="learning_path_select"
        )
        target_code = kp_options[target_kp]

        if target_code:
            learning_path = knowledge_graph.get_learning_path(target_code)

            if learning_path:
                st.markdown(f"**学习《{knowledge_graph.nodes[target_code].name}》的推荐路径：**")

                for i, code in enumerate(learning_path, 1):
                    node = knowledge_graph.nodes.get(code)
                    if node:
                        is_target = code == target_code
                        prefix = "🎯" if is_target else f"{i}."
                        importance_bar = "⭐" * node.importance
                        st.markdown(f"{prefix} **{node.name}** {importance_bar}")
            else:
                st.info("该知识点无前置要求")

    # ========== 标签 4: 依赖关系图 ==========
    with kg_tab4:
        st.subheader("🔗 知识点依赖关系可视化")

        # 选择要查看的年级
        view_grade = st.selectbox(
            "选择要查看的年级",
            options=["全部", "一年级", "二年级", "三年级"]
        )

        # 生成图谱数据
        graph_data = knowledge_graph.export_graph_json()

        st.code(graph_data[:1000] + "...", language="json")
        st.info("💡 完整 JSON 数据已生成，可用于前端可视化库（如 D3.js、ECharts）绘制知识图谱")

        # 简单的文字版依赖图
        st.markdown("---")
        st.markdown("### 📝 文字版依赖关系")

        # 按类别分组显示
        categories = ["数与代数", "图形与几何", "统计与概率", "综合与实践"]

        for category in categories:
            with st.expander(f"📌 {category}"):
                for code, node in knowledge_graph.nodes.items():
                    if node.category == category:
                        if view_grade == "全部" or node.grade == view_grade:
                            prereqs = node.prerequisites
                            prereq_names = [knowledge_graph.nodes[p].name[:10] for p in prereqs if p in knowledge_graph.nodes]
                            if prereq_names:
                                st.markdown(f"**{node.name}** ← 需要先学：{', '.join(prereq_names)}")
                            else:
                                st.markdown(f"**{node.name}** ← 无前置要求")

# ==================== 模式 10: 能力成长档案 ====================
elif analysis_mode == "🌟 能力成长档案":
    st.header("🌟 能力成长档案")
    st.markdown("基于五大核心素养的学生数学能力发展评估")

    # 获取知识点掌握情况
    mastery = deep_analyzer.analyze_knowledge_mastery(selected_student_id)

    if not mastery:
        st.warning("暂无足够的知识点数据进行分析")
    else:
        # 能力分析
        ability_report = ability_portfolio.analyze_all_abilities(mastery)

        # 综合评级卡片
        st.subheader("📊 综合能力评级")
        overall_level = ability_report["overall_level"]
        level_emoji = {"优秀": "🌟", "良好": "👍", "中等": "👌", "需努力": "💪"}.get(overall_level, "📌")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("综合评级", f"{level_emoji} {overall_level}")
        with col2:
            strongest = ability_report.get("strongest", {})
            st.metric("最强能力", strongest.get("name", "-"))
        with col3:
            weakest = ability_report.get("weakest", {})
            st.metric("需加强", weakest.get("name", "-"))

        st.markdown("---")

        # 雷达图
        st.subheader("🎯 五大核心素养雷达图")

        radar_data = ability_report["radar_data"]
        categories = [item["ability"] for item in radar_data]
        values = [item["score"] for item in radar_data]

        # 闭合雷达图
        values_closed = values + [values[0]]
        categories_closed = categories + [categories[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            name='能力得分',
            line_color='#3498db',
            marker=dict(size=8, color='#3498db')
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            height=500,
            title="数学核心素养能力雷达图"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 各能力详细得分
        st.subheader("📈 各能力详细分析")

        for ability_name, data in ability_report["abilities"].items():
            icon = {"数感": "🔢", "符号意识": "🔣", "空间观念": "📐",
                    "数据分析观念": "📊", "推理能力": "🧠"}.get(ability_name, "📌")

            with st.expander(f"{icon} {ability_name} - {data['score']}分 ({data['level']})"):
                st.markdown(f"**能力描述**: {data['description']}")
                st.markdown("**子能力构成**:")
                for sub in data["sub_abilities"]:
                    st.markdown(f"- {sub}")
                st.markdown(f"**涉及知识点数量**: {data['knowledge_count']}个")

                # 进度条
                progress = data["score"] / 100
                st.progress(progress)

        st.markdown("---")

        # 个性化建议
        st.subheader("💡 个性化发展建议")
        suggestions = ability_portfolio._generate_suggestions(ability_report)
        for i, sug in enumerate(suggestions, 1):
            st.markdown(f"{i}. {sug}")

        st.markdown("---")

        # 导出报告
        st.subheader("📥 导出成长档案")

        growth_report = ability_portfolio.generate_growth_report(
            student_name, selected_student_id, mastery
        )

        st.download_button(
            label="📥 下载成长档案 (Markdown)",
            data=growth_report,
            file_name=f"{student_name}_能力成长档案.md",
            mime="text/markdown"
        )

        # 对比功能
        st.markdown("---")
        st.subheader("👥 能力对比")

        compare_mode = st.checkbox("启用两人能力对比模式")

        if compare_mode:
            # 选择对比学生
            compare_students = st.multiselect(
                "选择要对比的学生（2 名）",
                options=list(student_dict.keys()),
                default=[selected_student_name],
                max_selections=2
            )

            if len(compare_students) == 2:
                compare_ids = [student_dict[name] for name in compare_students]

                # 获取两个学生的知识点掌握
                mastery_1 = deep_analyzer.analyze_knowledge_mastery(compare_ids[0])
                mastery_2 = deep_analyzer.analyze_knowledge_mastery(compare_ids[1])

                name_1 = analyzer.student_names.get(compare_ids[0], "学生 1")
                name_2 = analyzer.student_names.get(compare_ids[1], "学生 2")

                # 对比分析
                comparison = ability_portfolio.compare_two_students(mastery_1, mastery_2, name_1, name_2)

                # 对比雷达图
                fig = go.Figure()

                for trace in comparison["radar_comparison"]["traces"]:
                    values_closed = trace["values"] + [trace["values"][0]]
                    categories_closed = comparison["radar_comparison"]["categories"] + [comparison["radar_comparison"]["categories"][0]]

                    fig.add_trace(go.Scatterpolar(
                        r=values_closed,
                        theta=categories_closed,
                        fill='toself',
                        name=trace["name"]
                    ))

                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )),
                    showlegend=True,
                    height=500,
                    title="学生能力对比雷达图"
                )
                st.plotly_chart(fig, use_container_width=True)

                # 对比分析文字
                st.markdown("**对比分析**:")
                for analysis in comparison["analysis"]:
                    st.markdown(f"- {analysis}")

# ==================== 模式 11: 学习习惯分析 ====================
elif analysis_mode == "📝 学习习惯分析":
    st.header("📝 学习习惯分析")
    st.markdown("分析学生的答题习惯，识别粗心错误 vs 知识性错误，给出针对性建议")

    # 快速提示
    st.subheader("📌 今日提醒")
    tips = habit_analyzer.get_quick_tips(selected_student_id)
    for tip in tips:
        st.info(tip)

    st.markdown("---")

    # 习惯维度评分
    analysis = habit_analyzer.analyze_student_habits(selected_student_id)

    st.subheader("📊 学习习惯评分")

    col1, col2 = st.columns(2)

    with col1:
        # 雷达图
        habit_names = list(analysis.habit_scores.keys())
        habit_values = list(analysis.habit_scores.values())

        # 闭合雷达图
        values_closed = habit_values + [habit_values[0]]
        categories_closed = habit_names + [habit_names[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            name='习惯得分',
            line_color='#2ecc71',
            marker=dict(size=8)
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            height=400,
            title="学习习惯雷达图"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 习惯得分卡片
        st.markdown("**各维度评分**:")
        for habit, score in analysis.habit_scores.items():
            level = "🌟" if score >= 85 else "👍" if score >= 70 else "👌" if score >= 55 else "💪"
            st.markdown(f"- **{habit}**: {score} {level}")

        st.markdown("---")

        # 错误类型分布
        st.markdown("**错误类型分布**:")
        if analysis.error_distribution:
            for error_type, count in analysis.error_distribution.items():
                st.markdown(f"- {error_type}: {count}次")
        else:
            st.info("暂无错误记录数据")

    st.markdown("---")

    # 主要问题
    st.subheader("⚠️ 主要问题")
    if analysis.main_issues:
        for i, issue in enumerate(analysis.main_issues, 1):
            st.warning(issue)
    else:
        st.success("🎉 暂无明显问题，学习习惯良好！")

    st.markdown("---")

    # 改进建议
    st.subheader("💡 改进建议")
    for i, sug in enumerate(analysis.suggestions, 1):
        st.success(sug)

    st.markdown("---")

    # 趋势分析
    st.subheader("📈 习惯变化趋势")
    if any(analysis.trends.values()):
        for habit, values in analysis.trends.items():
            if values and len(values) >= 2:
                trend = values[-1] - values[0]
                trend_icon = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
                st.markdown(f"- **{habit}**: {values[0]:.1f} → {values[-1]:.1f} {trend_icon} ({trend:+.1f})")
    else:
        st.info("数据不足，无法分析趋势")

    st.markdown("---")

    # 导出报告
    st.subheader("📥 导出报告")
    habit_report = habit_analyzer.generate_habit_report(selected_student_id, student_name)
    st.download_button(
        label="📥 下载习惯分析报告 (Markdown)",
        data=habit_report,
        file_name=f"{student_name}_学习习惯分析报告.md",
        mime="text/markdown"
    )

# ==================== 模式 12: 班级学情看板 ====================
elif analysis_mode == "🏫 班级学情看板":
    st.header("🏫 班级学情看板")
    st.markdown("教师视角的班级整体学习情况分析")

    # 学期选择
    selected_semester = st.selectbox(
        "选择要分析的学期",
        options=ALL_SEMESTERS,
        index=0
    )

    if selected_semester:
        # 获取班级分析
        class_analysis = class_dashboard.analyze_class_overall(selected_semester)

        if class_analysis:
            # 统计卡片
            st.subheader("📊 整体统计")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("学生总数", f"{class_analysis.total_students}人")
            with col2:
                st.metric("班级平均分", f"{class_analysis.class_avg}分")
            with col3:
                st.metric("优秀率", f"{class_analysis.excellent_rate}%")
            with col4:
                st.metric("及格率", f"{class_analysis.pass_rate}%")

            st.markdown("---")

            # 分数段分布
            st.subheader("📊 分数段分布")
            dist = class_dashboard.get_score_distribution(selected_semester)

            col1, col2 = st.columns(2)

            with col1:
                # 柱状图
                fig_bar = px.bar(
                    x=list(dist.keys()),
                    y=list(dist.values()),
                    labels={"x": "分数段", "y": "人数"},
                    title="各分数段人数分布",
                    color=list(dist.values()),
                    color_continuous_scale="YlGnBu"
                )
                fig_bar.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                # 饼图
                colors = ["#e74c3c", "#e67e22", "#f1c40f", "#3498db", "#2ecc71"]
                fig_pie = px.pie(
                    values=list(dist.values()),
                    names=list(dist.keys()),
                    title="分数段占比",
                    color_discrete_sequence=colors
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("---")

            # 知识点掌握率热力图
            st.subheader("🎯 知识点掌握率热力图")

            if class_analysis.knowledge_mastery:
                # 按类别分组
                category_data = {}
                for kp_code, mastery in class_analysis.knowledge_mastery.items():
                    kp_info = deep_analyzer.knowledge_points.get(kp_code)
                    if kp_info:
                        category = kp_info.category
                        if category not in category_data:
                            category_data[category] = []
                        category_data[category].append({
                            "code": kp_code,
                            "name": kp_info.name,
                            "mastery": mastery
                        })

                # 显示每个类别的热力图
                for category, items in category_data.items():
                    st.markdown(f"#### {category}")
                    heatmap_df = pd.DataFrame(items)
                    if not heatmap_df.empty:
                        fig = px.imshow(
                            [[item["mastery"] for item in items]],
                            labels=dict(x="知识点", y="掌握率", color="掌握率"),
                            x=[item["name"][:15] + "..." if len(item["name"]) > 15 else item["name"] for item in items],
                            y=[""],
                            color_continuous_scale="RdYlGn",
                            range_color=[0, 100]
                        )
                        fig.update_layout(height=200)
                        st.plotly_chart(fig, use_container_width=True)

                        # 详细数据
                        with st.expander("查看详细数据"):
                            detail_df = pd.DataFrame(items)
                            detail_df.columns = ["知识点编码", "知识点名称", "掌握率"]
                            st.dataframe(detail_df, use_container_width=True, hide_index=True)

            st.markdown("---")

            # 薄弱知识点
            st.subheader("⚠️ 薄弱知识点 (掌握率<75%)")
            if class_analysis.weak_knowledge_points:
                weak_df = pd.DataFrame(class_analysis.weak_knowledge_points[:15])
                weak_df.columns = ["编码", "名称", "掌握率", "年级", "学期", "类别"]
                st.dataframe(weak_df, use_container_width=True, hide_index=True)
            else:
                st.success("🎉 暂无薄弱知识点，全班掌握良好！")

            st.markdown("---")

            # 需要关注的学生
            st.subheader("📋 需要关注的学生")
            if class_analysis.needs_attention_students:
                for student in class_analysis.needs_attention_students:
                    reasons = "；".join(student["原因"])
                    st.warning(f"**{student['姓名']}** (第{student['排名']}名): {reasons}")
            else:
                st.success("🎉 暂无需要特别关注的学生")

            st.markdown("---")

            # 成绩排名
            with st.expander("📊 查看完整成绩排名"):
                rank_df = pd.DataFrame(class_analysis.student_rankings)
                rank_df = rank_df[["排名", "学号", "姓名", "平均分", "考试次数"]]
                st.dataframe(rank_df, use_container_width=True, hide_index=True)

            # 导出报告
            st.markdown("---")
            st.subheader("📥 导出班级报告")
            class_report = class_dashboard.export_class_report(selected_semester)
            st.download_button(
                label="📥 下载班级学情报告 (Markdown)",
                data=class_report,
                file_name=f"{selected_semester}_班级学情分析报告.md",
                mime="text/markdown"
            )
        else:
            st.error("该学期无数据")

# ==================== 模式 13: 智能组卷 ====================
elif analysis_mode == "📄 智能组卷":
    st.header("📄 智能组卷系统")
    st.markdown("根据薄弱知识点自动生成针对性练习卷")

    # 选择试卷类型
    paper_type = st.selectbox(
        "选择试卷类型",
        options=["专项突破", "基础练习", "单元检测"],
        index=0
    )

    st.info(f"📌 试卷类型：**{paper_type}** - 系统将根据学生的薄弱知识点自动生成针对性练习")

    # 获取薄弱知识点
    weak_points = deep_analyzer.get_weak_knowledge_points(selected_student_id, threshold=85)

    if not weak_points:
        st.success("🎉 所有知识点掌握良好（>=85 分）！")
        st.info("系统将生成综合练习卷，巩固所学知识")
        # 生成综合练习
        weak_points_for_paper = []
    else:
        st.warning(f"发现 {len(weak_points)} 个薄弱知识点（<85 分）")

        # 显示薄弱知识点选择
        st.markdown("**选择要重点练习的知识点：**")
        selected_weak = st.multiselect(
            "选择知识点（不选则全部包含）",
            options=[f"{wp['name']} ({wp['score']}分)" for wp in weak_points],
            default=[f"{wp['name']} ({wp['score']}分)" for wp in weak_points[:5]]
        )

        # 构建练习卷所需数据
        weak_points_for_paper = []
        for wp in weak_points:
            label = f"{wp['name']} ({wp['score']}分)"
            if label in selected_weak or not selected_weak:
                weak_points_for_paper.append({
                    "knowledge_code": wp["code"],
                    "knowledge_name": wp["name"],
                    "error_count": max(1, int((85 - wp["score"]) / 5))  # 根据分数差距计算权重
                })

    # 生成试卷按钮
    if st.button("📝 生成练习卷", type="primary"):
        with st.spinner("正在生成试卷..."):
            # 生成试卷
            paper = paper_generator.generate_paper(
                student_id=selected_student_id,
                student_name=student_name,
                weak_knowledge_points=weak_points_for_paper,
                paper_type=paper_type
            )

            if not paper.questions:
                st.warning("暂无可生成的题目，请尝试其他知识点或试卷类型")
            else:
                # 显示试卷信息
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("题目数量", len(paper.questions))
                with col2:
                    st.metric("总分", paper.total_score)
                with col3:
                    st.metric("建议时长", f"{paper.duration_minutes}分钟")

                st.markdown(f"**重点考察**: {', '.join(paper.focus_areas)}")

                st.markdown("---")

                # 按题型显示
                question_types = {}
                for q in paper.questions:
                    if q.question_type not in question_types:
                        question_types[q.question_type] = []
                    question_types[q.question_type].append(q)

                type_order = ["计算题", "填空题", "判断题", "应用题"]
                type_titles = {"计算题": "一、计算题", "填空题": "二、填空题",
                              "判断题": "三、判断题", "应用题": "四、应用题"}

                for qtype in type_order:
                    if qtype in question_types:
                        st.subheader(type_titles.get(qtype, qtype))
                        for i, q in enumerate(question_types[qtype], 1):
                            st.markdown(f"**{i}.** {q.question_text} **({q.score}分)**")

                st.markdown("---")

                # 答案部分
                with st.expander("📝 查看参考答案"):
                    st.markdown("**参考答案：**")
                    for i, q in enumerate(paper.questions, 1):
                        st.markdown(f"{i}. {q.answer}")

                # 导出试卷
                st.markdown("---")
                st.subheader("📥 导出试卷")

                col1, col2 = st.columns(2)

                with col1:
                    paper_md = paper_generator.export_paper_word(paper)
                    st.download_button(
                        label="📥 下载试卷 (Markdown)",
                        data=paper_md,
                        file_name=f"{student_name}_{paper_type}练习卷.md",
                        mime="text/markdown"
                    )

                with col2:
                    answer_sheet = paper_generator.export_answer_sheet(paper)
                    st.download_button(
                        label="📥 下载答题卡 (Markdown)",
                        data=answer_sheet,
                        file_name=f"{student_name}_答题卡.md",
                        mime="text/markdown"
                    )

                # 练习建议
                st.markdown("---")
                st.subheader("💡 练习建议")
                recommendation = paper_generator.get_recommendation(paper)
                st.markdown(recommendation)

# 页脚
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("📚 基于人教版小学数学知识点体系")
with col2:
    st.caption(f"📅 可选学期：{len(ALL_SEMESTERS)}个")
with col3:
    st.caption("🧠 覆盖四大知识领域深度分析")
