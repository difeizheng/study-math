"""
学生成绩分析系统 - Web 界面 (增强版)
集成人教版小学数学知识点深度分析
"""
import re
from typing import List, Dict
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 导入日志系统
from logger import init_logging, log_error, log_info, get_logger
from database import init_database, StudentDAO, ErrorRecordDAO, ExamScoreDAO, get_db_connection
from score_config import (
    load_score_ranges,
    save_score_ranges,
    reset_to_default,
    DEFAULT_SCORE_RANGES
)
from excel_importer import ExcelDataImporter
from pdf_exporter import PDFExporter
from score_entry import ScoreEntryService
from data_manager import DataManager, get_data_manager

# 初始化数据管理器
data_manager = get_data_manager()

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


# 从 Excel 导入成绩数据到数据库
def import_scores_from_excel():
    """将 Excel 中的成绩数据导入到数据库"""
    from pathlib import Path
    from excel_importer import ExcelDataImporter

    db = get_data_manager()
    imported_count = 0

    # 扫描 data 目录和 data/uploads 子目录
    data_dir = Path("data")
    if not data_dir.exists():
        return

    # 扫描 uploads 子目录（新上传的文件）
    uploads_dir = data_dir / "uploads"
    if uploads_dir.exists():
        for file in sorted(uploads_dir.glob("*.xlsx")):
            try:
                importer = ExcelDataImporter()
                df = importer.load_excel(str(file))
                result = db.import_excel_scores(df, file.name)
                if result.success:
                    imported_count += result.data
            except Exception as e:
                logger.error(f"导入 {file.name} 成绩失败：{e}")

    # 扫描 data 根目录（备份文件）
    for file in sorted(data_dir.glob("*.xlsx")):
        try:
            importer = ExcelDataImporter()
            df = importer.load_excel(str(file))
            result = db.import_excel_scores(df, file.name)
            if result.success:
                imported_count += result.data
        except Exception as e:
            logger.error(f"导入 {file.name} 成绩失败：{e}")

    if imported_count > 0:
        logger.info(f"从 Excel 导入 {imported_count} 条成绩到数据库")


sync_students_from_excel()
import_scores_from_excel()

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
@st.cache_resource(ttl=3600)  # 1 小时后过期
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


def refresh_analyzers():
    """刷新分析器中的录入成绩缓存，确保数据是最新的"""
    analyzer.refresh_entered_scores()
    deep_analyzer.refresh_entered_scores()


# 清除缓存并重新初始化
if st.sidebar.button("🔄 清除缓存并刷新"):
    get_analyzers.clear()
    st.rerun()

analyzer, deep_analyzer, error_tracker, knowledge_graph, ability_portfolio, habit_analyzer, class_dashboard, paper_generator = get_analyzers()
# 每次页面加载时刷新录入成绩缓存
refresh_analyzers()

# 获取所有学期列表（使用标准化后的名称）
SEMESTER_MAP = {analyzer._normalize_semester_name(k): k for k in analyzer.semester_data.keys()}  # 标准化名称 -> 原始名称
ALL_SEMESTERS = list(SEMESTER_MAP.keys())  # 使用标准化后的学期名称

# 标题
st.title("📊 学生成绩分析系统")
st.markdown("### 基于人教版小学数学知识点的深度分析")
st.markdown("---")

# 侧边栏
st.sidebar.header("选择学生")

# 从数据库获取学生列表（真实数据源）
db_students = StudentDAO.get_student_list()
if db_students:
    # 数据库有学生，使用数据库数据
    student_dict = {f"{sid} - {name}": sid for sid, name in db_students}
else:
    # 数据库为空，使用 Excel 数据
    students = analyzer.get_student_list()
    student_dict = {f"{sid} - {name}": sid for sid, name in students}

# 检查是否有可选的学生
if not student_dict:
    st.sidebar.warning("⚠️ 暂无学生数据，请先从 Excel 同步或录入学生信息")
    selected_student_id = None
    selected_student_name = None
else:
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
        default=st.session_state.selected_semesters_state if st.session_state.selected_semesters_state else ALL_SEMESTERS[-1:],  # 默认最后一个学期（最新的）
        key="semester_multiselect"
    )
    # 更新状态
    if selected_semesters:
        st.session_state.selected_semesters_state = selected_semesters

# 分析模式选择
st.sidebar.header("分析模式")
analysis_mode = st.sidebar.radio(
    "选择分析类型",
    ["📈 成绩趋势分析", "🧠 知识点深度分析", "📋 诊断报告", "👥 多学生对比", "⚠️ 成绩预警", "📊 班级分析", "🔬 宏观分析", "📕 错题追踪本", "🕸️ 知识点关联图谱", "🌟 能力成长档案", "📝 学习习惯分析", "🏫 班级学情看板", "📄 智能组卷", "📝 成绩录入", "📊 录入成绩查询", "⚙️ 数据管理"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption("系统版本：v5.0 (数据管理重构版)")


# ==================== 数据管理模块 ====================
if analysis_mode == "⚙️ 数据管理":
    # 数据管理子菜单
    data_mgmt_mode = st.sidebar.radio(
        "数据管理功能",
        ["📂 Excel 数据导入", "📁 导入文件管理", "📊 数据总览", "📝 成绩录入", "⚙️ 系统数据设置"],
        index=0
    )

    st.markdown("---")

    # ========== 子菜单 1: Excel 数据导入 ==========
    if data_mgmt_mode == "📂 Excel 数据导入":
        st.header("📂 Excel 数据导入")
        st.markdown("上传并导入 Excel 格式的成绩数据文件")

        uploaded_file = st.file_uploader("选择 Excel 成绩表文件", type=["xlsx", "xls"])

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

                st.success("导入成功！")
                st.json({
                    "错题数": stats.get('total_errors', 0),
                    "学生数": stats.get('students', 0),
                    "考试数": stats.get('exams', 0)
                })
                log_info(f"Excel 导入成功：{uploaded_file.name}, 错题数：{stats.get('total_errors', 0)}")
            except Exception as e:
                st.error(f"导入失败：{e}")
                log_error(e, "Excel 导入失败")
        else:
            st.info("请在上方选择 Excel 文件进行上传导入")
            st.markdown("""
            **支持的文件格式：**
            - Excel 2007+ (.xlsx)
            - Excel 97-2003 (.xls)

            **文件命名规范：**
            - 文件名应包含班级和学期信息，如：`10032-1(2) 班上 学期数学考试分数-math_scores.xlsx`
            """)

    # ========== 子菜单 2: 导入文件管理 ==========
    elif data_mgmt_mode == "📁 导入文件管理":
        st.header("📁 导入文件管理")
        st.markdown("管理已导入的 Excel 数据文件")

        from pathlib import Path
        data_dir = Path("data")
        excel_files = list(data_dir.glob("*.xlsx"))

        # 统计信息
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Excel 文件数量", len(excel_files))
        with col2:
            total_size = sum(ef.stat().st_size for ef in excel_files)
            st.metric("总文件大小", f"{round(total_size / 1024, 2)} KB")

        if excel_files:
            st.subheader("Excel 文件列表")
            excel_info = []
            for ef in sorted(excel_files, key=lambda x: x.stat().st_mtime, reverse=True):
                file_size = ef.stat().st_size
                file_time = datetime.fromtimestamp(ef.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                excel_info.append({
                    "文件名": ef.name,
                    "大小 (KB)": round(file_size / 1024, 2),
                    "修改时间": file_time
                })

            excel_df = pd.DataFrame(excel_info)
            st.dataframe(excel_df, use_container_width=True, height=300)

            st.divider()

            # 删除文件操作
            st.subheader("删除文件")
            delete_excel_name = st.selectbox(
                "选择要删除的 Excel 文件",
                options=[""] + [ef.name for ef in excel_files],
                key="delete_excel_select"
            )

            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                if st.button("🗑️ 删除选中的 Excel 文件", type="secondary", use_container_width=True):
                    if delete_excel_name:
                        try:
                            file_to_delete = data_dir / delete_excel_name
                            file_to_delete.unlink()
                            st.success(f"已删除文件：{delete_excel_name}")
                            log_info(f"删除 Excel 文件：{delete_excel_name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"删除失败：{e}")
                            log_error(e, f"删除 Excel 文件失败：{delete_excel_name}")
                    else:
                        st.warning("请选择要删除的文件")
        else:
            st.info("暂无 Excel 文件")

    # ========== 子菜单 3: 数据总览 ==========
    elif data_mgmt_mode == "📊 数据总览":
        st.header("📊 数据总览")
        st.markdown("查看所有成绩数据（Excel 导入 + 成绩录入）")

        # 使用 DataManager 获取统一数据
        try:
            # 统计信息
            all_scores = data_manager.get_scores()
            students = data_manager.get_students()
            exam_list = data_manager.get_exam_list()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("学生总数", len(students))
            with col2:
                st.metric("考试次数", len(exam_list))
            with col3:
                st.metric("成绩记录数", len(all_scores))

            st.divider()

            # 考试列表（带周次信息）
            st.subheader("📋 考试列表")

            # 获取所有学期列表用于过滤
            from database import ExamScoreDAO
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT semester FROM exam_scores ORDER BY semester")
            all_semesters = [row[0] for row in cursor.fetchall()]
            conn.close()

            # 学期过滤
            semester_filter = st.selectbox(
                "选择学期",
                options=["全部"] + all_semesters,
                key="exam_semester_filter"
            )

            if exam_list:
                # 如果有学期选择，获取该学期的考试列表
                if semester_filter != "全部":
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DISTINCT exam_name
                        FROM exam_scores
                        WHERE semester = ?
                        ORDER BY exam_name
                    """, (semester_filter,))
                    filtered_exams = set(row[0] for row in cursor.fetchall())
                    conn.close()

                    # 过滤考试列表
                    filtered_exam_list = [e for e in exam_list if e.name in filtered_exams]
                else:
                    filtered_exam_list = exam_list

                exam_data = []
                for exam in filtered_exam_list:
                    exam_data.append({
                        "考试名称": exam.name,
                        "周次": f"第{exam.week}周" if exam.week > 0 else "-",
                        "日期": exam.date or "-",
                        "学期": semester_filter if semester_filter != "全部" else "-"
                    })
                st.dataframe(pd.DataFrame(exam_data), use_container_width=True, height=200)

                if semester_filter != "全部":
                    st.caption(f"已显示学期：**{semester_filter}** 的考试 ({len(filtered_exam_list)}个)")
            else:
                st.info("暂无考试数据")

            st.divider()

            # 成绩明细
            st.subheader("📝 成绩明细")

            # 成绩明细过滤条件
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                # 学生过滤
                student_options = ["全部学生"] + [f"{s['student_id']} - {s['name']}" for s in students]
                student_filter = st.selectbox(
                    "选择学生",
                    options=student_options,
                    key="score_student_filter"
                )
            with col_filter2:
                # 考试名称过滤
                exam_name_filter = st.text_input(
                    "考试名称",
                    placeholder="如：练习 1、期末模 1",
                    key="score_exam_filter"
                )

            if all_scores:
                # 应用过滤条件
                filtered_scores = all_scores

                # 学期过滤
                if semester_filter != "全部":
                    # 先获取该学期的所有考试名称
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DISTINCT exam_name
                        FROM exam_scores
                        WHERE semester = ?
                    """, (semester_filter,))
                    semester_exams = set(row[0] for row in cursor.fetchall())
                    conn.close()
                    filtered_scores = [s for s in filtered_scores if s.exam_name in semester_exams]

                # 学生过滤
                if student_filter != "全部学生":
                    selected_sid = int(student_filter.split(" - ")[0])
                    filtered_scores = [s for s in filtered_scores if s.student_id == selected_sid]

                # 考试名称过滤
                if exam_name_filter.strip():
                    filtered_scores = [s for s in filtered_scores
                                       if exam_name_filter.strip() in s.exam_name]

                # 获取成绩对应的学期信息
                conn = get_db_connection()
                cursor = conn.cursor()

                score_data = []
                for s in filtered_scores[:200]:  # 限制显示 200 条
                    # 查询该成绩所属学期
                    cursor.execute("""
                        SELECT DISTINCT semester FROM exam_scores
                        WHERE exam_name = ? AND student_id = ?
                    """, (s.exam_name, s.student_id))
                    row = cursor.fetchone()
                    semester_val = row[0] if row else "-"

                    score_data.append({
                        "学期": semester_val,
                        "学号": s.student_id,
                        "姓名": s.student_name,
                        "考试名称": s.exam_name,
                        "周次": f"第{s.week}周" if s.week > 0 else "-",
                        "成绩": s.score,
                    })
                conn.close()

                st.dataframe(pd.DataFrame(score_data), use_container_width=True, height=400)

                # 显示过滤统计
                filter_info = []
                if semester_filter != "全部":
                    filter_info.append(f"学期：{semester_filter}")
                if student_filter != "全部学生":
                    filter_info.append(f"学生：{student_filter}")
                if exam_name_filter.strip():
                    filter_info.append(f"考试：{exam_name_filter}")

                if filter_info:
                    st.caption(f"过滤条件：{', '.join(filter_info)} | 显示 {len(score_data)} 条记录")
            else:
                st.info("暂无成绩数据")
        except Exception as e:
            st.error(f"加载失败：{e}")
            logger.error(f"数据总览加载失败：{e}")

    # ========== 子菜单 4: 系统数据设置 ==========
    elif data_mgmt_mode == "⚙️ 系统数据设置":
        st.header("⚙️ 系统数据设置")
        st.markdown("管理系统数据库中的成绩和学生数据")

        from database import ExamScoreDAO, StudentDAO

        # 数据状态
        st.subheader("数据状态")
        db_score_count = len(ExamScoreDAO.get_all_scores())
        db_student_count = len(StudentDAO.get_all_students())

        col1, col2 = st.columns(2)
        with col1:
            st.metric("录入成绩条数", db_score_count)
        with col2:
            st.metric("学生总数", db_student_count)

        st.divider()

        # 数据清理
        st.subheader("数据清理")

        st.caption("⚠️ 注意：清理操作仅删除数据库中的录入成绩，Excel 文件中的数据不会被删除。清理后请刷新页面（F5）以查看效果。")

        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("🗑️ 清理所有录入成绩", type="secondary", use_container_width=True):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM exam_scores")
                    cursor.execute("DELETE FROM error_records")
                    conn.commit()
                    conn.close()
                    st.success("已清理所有录入成绩！请刷新页面（F5）重新加载数据。")
                    log_info("用户清理了所有录入成绩")

                    # 使用 session_state 标记需要重新加载
                    st.session_state['data_changed'] = True

                except Exception as e:
                    st.error(f"清理失败：{e}")
                    log_error(e, "清理录入成绩失败")

        with col_btn2:
            if st.button("🗑️ 清理所有数据（含学生）", type="secondary", use_container_width=True):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM exam_scores")
                    cursor.execute("DELETE FROM error_records")
                    cursor.execute("DELETE FROM students")
                    conn.commit()
                    conn.close()
                    st.success("已清理所有数据！请刷新页面（F5）重新开始。")
                    log_info("用户清理了所有数据")

                    # 使用 session_state 标记需要重新加载
                    st.session_state['data_changed'] = True

                except Exception as e:
                    st.error(f"清理失败：{e}")
                    log_error(e, "清理所有数据失败")

        with col_btn3:
            # 移动 Excel 文件到备份目录
            if st.button("📁 移除 Excel 数据", type="secondary", use_container_width=True):
                try:
                    import shutil
                    backup_dir = Path("data_backup")
                    backup_dir.mkdir(exist_ok=True)

                    moved_count = 0
                    for excel_file in Path("data").glob("*.xlsx"):
                        shutil.move(str(excel_file), str(backup_dir / excel_file.name))
                        moved_count += 1

                    st.success(f"已将 {moved_count} 个 Excel 文件移动到 data_backup 目录！刷新页面后生效。")
                    log_info(f"用户移除了 {moved_count} 个 Excel 文件到备份目录")
                    st.session_state['data_changed'] = True

                except Exception as e:
                    st.error(f"操作失败：{e}")
                    log_error(e, "移除 Excel 数据失败")

        # 刷新数据按钮
        if st.button("🔄 重新加载数据", type="primary", use_container_width=True):
            try:
                # 重新初始化分析器
                analyzer.load_all_data()
                deep_analyzer.load_all_data()
                refresh_analyzers()

                st.success("数据已重新加载！")
                log_info("用户重新加载了数据")
                st.rerun()

            except Exception as e:
                st.error(f"加载失败：{e}")
                log_error(e, "重新加载数据失败")

        st.divider()

        # 数据同步
        st.subheader("数据同步")

        # 显示当前数据源状态
        excel_files = list(Path("data").glob("*.xlsx"))
        st.info(f"📂 Data 目录中有 {len(excel_files)} 个 Excel 文件")

        col_sync1, col_sync2 = st.columns(2)

        with col_sync1:
            if st.button("📥 从 Excel 同步学生信息", type="primary", use_container_width=True):
                try:
                    temp_analyzer = ScoreAnalyzer()
                    temp_analyzer.load_all_data()

                    # 同步学生到数据库
                    count = 0
                    for sid, name in temp_analyzer.student_names.items():
                        if not StudentDAO.get_student(sid):
                            # 从学期名称推断年级和学期
                            grade = "1"
                            semester = "上"
                            for sem_key in temp_analyzer.semester_data.keys():
                                match = re.search(r'(\d) 年级 ([上下]) 学期', sem_key)
                                if match:
                                    grade = match.group(1)
                                    semester = match.group(2)
                                break

                            StudentDAO.add_student(sid, name, f"{grade}年级", semester)
                            count += 1

                    st.success(f"已同步 {count} 个学生到数据库！请刷新页面查看。")
                    log_info(f"从 Excel 同步学生信息：{count}人")
                except Exception as e:
                    st.error(f"同步失败：{e}")
                    log_error(e, "从 Excel 同步学生失败")

        with col_sync2:
            if st.button("📊 导入 Excel 成绩到数据库", type="primary", use_container_width=True):
                try:
                    from excel_importer import ExcelDataImporter

                    data_dir = Path("data")
                    total_imported = 0
                    imported_files = []

                    for file in sorted(data_dir.glob("*.xlsx")):
                        try:
                            importer = ExcelDataImporter()
                            df = importer.load_excel(str(file))

                            # 使用 DataManager 导入成绩
                            result = data_manager.import_excel_scores(df, file.name)

                            if result.success:
                                total_imported += result.data
                                imported_files.append(f"{file.name}: {result.data}条")
                        except Exception as e:
                            logger.error(f"导入 {file.name} 失败：{e}")

                    if total_imported > 0:
                        st.success(f"成功导入 {total_imported} 条成绩记录到数据库！")
                        with st.expander("查看详情"):
                            st.write("\n".join(imported_files))
                        log_info(f"批量导入 Excel 成绩：{total_imported}条")
                    else:
                        st.info("没有导入新数据（可能已存在）")
                except Exception as e:
                    st.error(f"导入失败：{e}")
                    log_error(e, "批量导入 Excel 成绩失败")

    # ========== 子菜单 5: 成绩录入 ==========
    elif data_mgmt_mode == "📝 成绩录入":
        st.header("📝 成绩录入")
        st.markdown("录入学生考试成绩和错题信息")

        # 选择录入方式
        entry_type = st.radio(
            "录入方式",
            ["📝 单个学生录入", "📋 全班批量录入"],
            horizontal=True
        )

        if entry_type == "📝 单个学生录入":
            # 单个学生成绩录入
            service = ScoreEntryService()

            col1, col2 = st.columns(2)
            with col1:
                entry_sid = st.number_input("学号", min_value=1, value=1)
            with col2:
                entry_sname = st.text_input("学生姓名", value="")

            entry_exam_name = st.text_input(
                "考试名称",
                placeholder="如：周练 1、期末模 2",
                value="周练 1"
            )
            entry_exam_date = st.date_input(
                "考试日期",
                value=datetime.now()
            )
            entry_score = st.number_input(
                "考试成绩",
                min_value=0.0,
                max_value=100.0,
                step=0.5,
                value=90.0
            )

            # 错题录入
            st.subheader("错题信息（可选）")
            add_error = st.checkbox("添加错题")

            error_knowledge = []
            if add_error:
                kp_options = list(deep_analyzer.knowledge_points.keys())
                selected_kp = st.multiselect(
                    "错题知识点",
                    options=kp_options,
                    format_func=lambda x: f"{x} - {deep_analyzer.knowledge_points[x].name}"
                )
                error_knowledge = selected_kp

            if st.button("提交录入", type="primary"):
                if not entry_sname:
                    st.warning("请输入学生姓名")
                else:
                    result = data_manager.add_exam_score(
                        student_id=entry_sid,
                        student_name=entry_sname,
                        exam_name=entry_exam_name,
                        score=entry_score,
                        error_knowledge=error_knowledge
                    )

                    if result.success:
                        st.success(result.message)
                        st.rerun()
                    else:
                        st.error(result.message)

        elif entry_type == "📋 全班批量录入":
            st.markdown("**按学号 + 成绩格式批量录入**")

            batch_exam_name = st.text_input(
                "考试名称",
                placeholder="如：周练 1、期末模 2",
                value="周练 1",
                key="batch_exam"
            )
            batch_exam_date = st.date_input(
                "考试日期",
                value=datetime.now(),
                key="batch_date"
            )

            st.markdown("**成绩列表（格式：学号 分数，每行一个）**")
            st.caption("支持空格、Tab、逗号分隔")

            batch_scores = st.text_area(
                "成绩列表",
                placeholder="1 95\n2 88\n3 92",
                height=200,
                key="batch_scores"
            )

            auto_create = st.checkbox("学号不存在时自动创建学生", value=True)

            if st.button("批量提交", type="primary"):
                if not batch_exam_name:
                    st.warning("请输入考试名称")
                elif not batch_scores.strip():
                    st.warning("请输入成绩列表")
                else:
                    # 解析成绩列表
                    lines = batch_scores.strip().split('\n')
                    success_count = 0
                    error_lines = []

                    for i, line in enumerate(lines, 1):
                        line = line.strip()
                        if not line:
                            continue

                        # 解析：学号 分数
                        parts = re.split(r'[\s,，\t]+', line, maxsplit=1)
                        if len(parts) < 2:
                            error_lines.append(f"第{i}行：格式错误")
                            continue

                        try:
                            sid = int(parts[0].strip())
                            score = float(parts[1].strip())

                            # 获取学生姓名（如果存在）
                            sname = ""
                            existing = StudentDAO.get_student(sid)
                            if existing:
                                sname = existing['name']
                            elif auto_create:
                                sname = f"学生{sid}"
                            else:
                                error_lines.append(f"第{i}行：学号{sid}不存在")
                                continue

                            result = data_manager.add_exam_score(
                                student_id=sid,
                                student_name=sname,
                                exam_name=batch_exam_name,
                                score=score,
                                error_knowledge=None
                            )

                            if result.success:
                                success_count += 1
                            else:
                                error_lines.append(f"第{i}行：{result.message}")

                        except Exception as e:
                            error_lines.append(f"第{i}行：解析错误 - {e}")

                    if success_count > 0:
                        st.success(f"成功录入 {success_count} 条成绩")
                    if error_lines:
                        st.warning("\n".join(error_lines[:10]))
                        if len(error_lines) > 10:
                            st.warning(f"还有 {len(error_lines) - 10} 条错误未显示")


# ==================== 成绩数据查询与维护 ====================
if analysis_mode == "📊 录入成绩查询":
    st.header("📊 录入成绩查询与维护")
    st.markdown("查询和管理系统中所有录入的成绩数据")

    # 查询条件
    col1, col2 = st.columns(2)
    with col1:
        query_student_id = st.number_input("学号", min_value=0, value=0, key="query_sid")
    with col2:
        query_semester = st.text_input("学期", placeholder="如：10037-3(2) 班下学期", key="query_sem")

    query_exam = st.text_input("考试名称", placeholder="如：周练 1", key="query_exam")

    # 查询按钮
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
    with col_btn1:
        do_query = st.button("🔍 查询", type="primary", use_container_width=True)
    with col_btn2:
        show_all = st.button("显示全部", use_container_width=True)

    # 执行查询
    if do_query or show_all:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 构建查询条件
        conditions = []
        params = []

        if query_student_id > 0:
            conditions.append("student_id = ?")
            params.append(query_student_id)

        if query_semester.strip():
            conditions.append("semester LIKE ?")
            params.append(f"%{query_semester.strip()}%")

        if query_exam.strip():
            conditions.append("exam_name LIKE ?")
            params.append(f"%{query_exam.strip()}%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor.execute(f"""
            SELECT id, student_id, semester, exam_name, exam_date, score, created_at
            FROM exam_scores
            WHERE {where_clause}
            ORDER BY semester, exam_name, student_id
        """, params)

        rows = cursor.fetchall()
        conn.close()

        if rows:
            st.success(f"找到 {len(rows)} 条记录")

            # 转换为 DataFrame
            df = pd.DataFrame(rows, columns=["ID", "学号", "学期", "考试名称", "考试日期", "分数", "创建时间"])

            # 显示数据表格
            st.dataframe(df, use_container_width=True, height=400)

            # 批量操作
            st.subheader("批量操作")
            col_op1, col_op2 = st.columns(2)

            with col_op1:
                # 选择要删除的记录 ID
                ids_to_delete = st.multiselect(
                    "选择要删除的记录 ID",
                    options=df["ID"].tolist(),
                    format_func=lambda x: f"ID:{x}"
                )

                if st.button("🗑️ 删除选中记录", type="secondary", use_container_width=True):
                    if ids_to_delete:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(f"DELETE FROM exam_scores WHERE id IN ({','.join(['?']*len(ids_to_delete))})", ids_to_delete)
                        conn.commit()
                        deleted = cursor.rowcount
                        conn.close()
                        st.success(f"已删除 {deleted} 条记录")
                        st.rerun()
                    else:
                        st.warning("请选择要删除的记录")

            with col_op2:
                # 按学号删除
                delete_sid = st.number_input("删除指定学号的所有成绩", min_value=0, value=0, key="del_sid")
                if st.button("🗑️ 删除该学号所有成绩", type="secondary", use_container_width=True):
                    if delete_sid > 0:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM exam_scores WHERE student_id = ?", (delete_sid,))
                        conn.commit()
                        deleted = cursor.rowcount
                        conn.close()
                        st.success(f"已删除 {deleted} 条记录")
                        st.rerun()
                    else:
                        st.warning("请输入学号")

            # 统计信息
            st.subheader("统计信息")
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("记录总数", len(rows))
            with col_stat2:
                st.metric("平均分", round(df["分数"].mean(), 2) if not df.empty else 0)
            with col_stat3:
                st.metric("最高分", df["分数"].max() if not df.empty else 0)
        else:
            st.info("没有找到符合条件的记录")

    # 显示所有成绩数据的快速预览
    st.divider()
    st.subheader("📋 数据快速预览")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT semester, exam_name, COUNT(*) as count, AVG(score) as avg_score
        FROM exam_scores
        GROUP BY semester, exam_name
        ORDER BY semester, exam_name
    """)
    summary_rows = cursor.fetchall()
    conn.close()

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows, columns=["学期", "考试名称", "记录数", "平均分"])
        st.dataframe(summary_df, use_container_width=True, height=200)
    else:
        st.info("暂无录入成绩数据")

# ==================== 分析模式主逻辑 ====================

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


# ==================== 模式 1: 成绩趋势分析 ====================
if analysis_mode == "📈 成绩趋势分析":
    st.header("📈 成绩趋势分析")
    st.markdown(f"当前分析学期：**{', '.join(selected_semesters)}**")

    # 统计卡片 - 使用 analyzer 的合并成绩方法
    stats = analyzer.calculate_statistics(selected_student_id, selected_semesters[0] if len(selected_semesters) == 1 else None)

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

    # 成绩趋势图 - 使用 analyzer 的方法
    trend_df = analyzer.get_score_trend(selected_student_id, selected_semesters[0] if len(selected_semesters) == 1 else None)
    class_stats_df = analyzer.get_class_stats(selected_semesters[0] if len(selected_semesters) == 1 else None)

    if not trend_df.empty:
        semesters = trend_df['学期'].unique()

        tabs = st.tabs([f"{sem}" for sem in semesters] + ["总体对比"])

        for i, semester in enumerate(semesters):
            with tabs[i]:
                sem_data = trend_df[trend_df['学期'] == semester].reset_index(drop=True)
                class_data = class_stats_df[class_stats_df['学期'] == semester].reset_index(drop=True) if not class_stats_df.empty else pd.DataFrame()

                if not sem_data.empty:
                    fig = go.Figure()

                    # 1. 班级最低分
                    if not class_data.empty:
                        fig.add_trace(go.Scatter(
                            x=class_data['考试'].tolist(),
                            y=class_data['最低分'].tolist(),
                            mode='lines+markers',
                            name='班级最低分',
                            line=dict(width=2, color='#ff9999', dash='dash'),
                            marker=dict(size=6)
                        ))

                    # 2. 班级平均分
                    if not class_data.empty:
                        fig.add_trace(go.Scatter(
                            x=class_data['考试'].tolist(),
                            y=class_data['平均分'].tolist(),
                            mode='lines+markers',
                            name='班级平均分',
                            line=dict(width=2, color='#66b3ff', dash='dash'),
                            marker=dict(size=8)
                        ))

                    # 3. 班级最高分
                    if not class_data.empty:
                        fig.add_trace(go.Scatter(
                            x=class_data['考试'].tolist(),
                            y=class_data['最高分'].tolist(),
                            mode='lines+markers',
                            name='班级最高分',
                            line=dict(width=2, color='#99ff99', dash='dash'),
                            marker=dict(size=6)
                        ))

                    # 4. 选中学生的成绩（最上层，实线突出）
                    fig.add_trace(go.Scatter(
                        x=sem_data['考试'].tolist(),
                        y=sem_data['分数'].tolist(),
                        mode='lines+markers',
                        name=student_name,
                        line=dict(width=3, color='#ff6666'),
                        marker=dict(size=10)
                    ))

                    fig.add_hline(y=90, line_dash="dash", line_color="green",
                                 annotation_text="优秀线 (90)", annotation_position="right")
                    fig.add_hline(y=60, line_dash="dash", line_color="red",
                                 annotation_text="及格线 (60)", annotation_position="right")

                    fig.update_layout(
                        xaxis_title="考试",
                        yaxis_title="分数",
                        yaxis_range=[0, 100],
                        height=500,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
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

    # 分数分布 - 使用 analyzer 的方法
    st.header("📊 分数分布")

    # 分数段设置（可展开）
    with st.expander("⚙️ 分数段设置", expanded=False):
        st.caption("自定义成绩分数段划分，设置后全局生效（所有学生和学期都适用）")

        # 加载当前配置
        current_ranges = load_score_ranges()

        # 使用 session_state 管理编辑中的配置
        if 'editing_score_ranges' not in st.session_state:
            st.session_state.editing_score_ranges = [r.copy() for r in current_ranges]

        # 显示当前配置的分数段
        st.write("**当前分数段配置:**")

        # 回调函数：根据 min/max 自动更新名称
        def auto_update_name(idx):
            r = st.session_state.editing_score_ranges[idx]
            new_min = st.session_state.get(f"range_min_{idx}", r['min'])
            new_max = st.session_state.get(f"range_max_{idx}", r['max'])
            current_name = st.session_state.get(f"range_name_{idx}", r['name'])

            # 检查名称是否是自动格式（如 "60-76 分" 或 "60-76 分 (及格)"）
            auto_pattern = r'^\d+-\d+分 (\([^)]+\))?$'
            is_auto_name = re.match(auto_pattern, current_name) is not None

            # 如果是自动格式，则更新名称
            if is_auto_name:
                # 提取括号中的后缀（如果有）
                suffix_match = re.search(r'(\([^)]+\))$', current_name)
                suffix = suffix_match.group(1) if suffix_match else ''
                st.session_state.editing_score_ranges[idx]['name'] = f"{new_min}-{new_max}分{suffix}"

        # 为每个分数段创建编辑行
        ranges_to_delete = []

        for i, r in enumerate(st.session_state.editing_score_ranges):
            cols = st.columns([2, 1, 1, 1])
            with cols[0]:
                st.text_input(
                    "名称",
                    value=r['name'],
                    key=f"range_name_{i}",
                    label_visibility="collapsed",
                    on_change=lambda idx=i: auto_update_name(idx)
                )
                # 同步名称值
                st.session_state.editing_score_ranges[i]['name'] = st.session_state[f"range_name_{i}"]
            with cols[1]:
                st.number_input(
                    "最低分",
                    min_value=0,
                    max_value=100,
                    value=r['min'],
                    key=f"range_min_{i}",
                    label_visibility="collapsed",
                    on_change=lambda idx=i: auto_update_name(idx)
                )
                # 同步 min 值
                st.session_state.editing_score_ranges[i]['min'] = st.session_state[f"range_min_{i}"]
            with cols[2]:
                st.number_input(
                    "最高分",
                    min_value=0,
                    max_value=100,
                    value=r['max'],
                    key=f"range_max_{i}",
                    label_visibility="collapsed",
                    on_change=lambda idx=i: auto_update_name(idx)
                )
                # 同步 max 值
                st.session_state.editing_score_ranges[i]['max'] = st.session_state[f"range_max_{i}"]
            with cols[3]:
                if st.button("🗑️", key=f"delete_range_{i}"):
                    ranges_to_delete.append(i)

        # 删除标记的分数段（倒序删除以避免索引错乱）
        for i in sorted(ranges_to_delete, reverse=True):
            st.session_state.editing_score_ranges.pop(i)
            st.rerun()

        # 添加新分数段按钮
        col_add, _ = st.columns([1, 3])
        with col_add:
            if st.button("➕ 添加分数段", use_container_width=True):
                st.session_state.editing_score_ranges.append({
                    "name": f"新分数段{len(st.session_state.editing_score_ranges) + 1}",
                    "min": 0,
                    "max": 59
                })
                st.rerun()

        # 操作按钮
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 保存配置", use_container_width=True, key="save_ranges"):
                if save_score_ranges(st.session_state.editing_score_ranges):
                    st.success("保存成功！配置已全局生效")
                    # 立即刷新页面，重新加载配置
                    st.rerun()
                else:
                    st.error("保存失败")
        with col2:
            if st.button("🔄 恢复默认", use_container_width=True, key="reset_ranges"):
                if reset_to_default():
                    st.session_state.editing_score_ranges = [r.copy() for r in DEFAULT_SCORE_RANGES]
                    st.success("已恢复默认")
                    st.rerun()

    # 根据选择的学期数量决定传入参数
    if len(selected_semesters) == 1:
        target_semester = selected_semesters[0]
        st.caption(f"📊 当前显示：{student_name} - {target_semester} 的成绩分布")
    elif len(selected_semesters) > 1:
        target_semester = selected_semesters
        st.caption(f"📊 当前显示：{student_name} - {len(selected_semesters)} 个学期的综合成绩分布")
    else:
        target_semester = None
        st.caption(f"📊 当前显示：{student_name} - 所有学期的综合成绩分布")

    score_dist = analyzer.get_score_distribution(selected_student_id, target_semester)

    # 显示当前使用的分数段配置提示
    active_ranges = load_score_ranges()
    st.caption(f"📋 当前使用 {len(active_ranges)} 个分数段：{' | '.join([r['name'] for r in active_ranges])}")

    # 调试：显示配置详情
    st.caption(f"📋 分数段详情：{active_ranges}")
    st.caption(f"📋 计算结果：{score_dist}")

    if score_dist:
        col1, col2 = st.columns(2)

        # 转换为 DataFrame 以避免 plotly 参数冲突
        import pandas as pd
        import plotly.graph_objects as go
        total_count = sum(score_dist.values())

        # 过滤掉 0 值的分数段，只展示有成绩的分数段
        filtered_dist = {k: v for k, v in score_dist.items() if v > 0}

        if filtered_dist:
            # 直接使用列表，不使用 DataFrame
            labels = list(filtered_dist.keys())
            values = list(filtered_dist.values())

            with col1:
                colors = ['#2ecc71', '#3498db', '#f1c40f', '#e67e22', '#e74c3c'][:len(filtered_dist)]
                # 使用 go.Pie 确保数据正确传递
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    marker_colors=colors
                )])
                fig.update_traces(
                    textposition='outside',
                    textinfo='percent+label',
                    texttemplate='%{label}<br>%{value} (%{percent})'
                )
                fig.update_layout(title=f"成绩分数段分布 (共{total_count}次成绩)")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # 使用 go.Bar 确保数据正确传递
                fig_bar = go.Figure(data=[go.Bar(
                    x=labels,
                    y=values,
                    marker_color=colors,
                    text=values,
                    textposition='outside'
                )])
                fig_bar.update_layout(
                    title="各分数段成绩分布",
                    xaxis_title='分数段',
                    yaxis_title='次数',
                    yaxis=dict(dtick=1),
                    showlegend=False
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("暂无成绩数据")

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

    # ==================== 时序追踪和轨迹诊断 ====================
    st.markdown("---")
    st.subheader("📈 时序追踪与轨迹诊断")
    st.markdown("基于周次的成绩追踪和学习轨迹诊断")

    # 年级选择
    grade_options = {
        "一年级上册": "G1U",
        "一年级下册": "G1D",
        "二年级上册": "G2U",
        "二年级下册": "G2D",
        "三年级上册": "G3U",
        "三年级下册": "G3D",
        "四年级上册": "G4U",
        "四年级下册": "G4D",
        "五年级上册": "G5U",
        "五年级下册": "G5D",
        "六年级上册": "G6U",
        "六年级下册": "G6D"
    }
    selected_grade = st.selectbox("选择年级学期", options=list(grade_options.keys()), index=0)
    grade_code = grade_options[selected_grade]

    tab1, tab2, tab3 = st.tabs(["📊 周次追踪", "📉 知识点曲线", "🔍 轨迹诊断"])

    with tab1:
        st.markdown("### 周次成绩追踪")
        st.markdown("按周次查看学生的考试成绩、对应知识点和错题情况")

        tracking_data = deep_analyzer.get_weekly_tracking(selected_student_id, grade_code)

        if tracking_data:
            # 过滤有考试的周次
            valid_tracking = [t for t in tracking_data if t.get("exam_count", 0) > 0]

            if valid_tracking:
                # 趋势图
                trend_data = [(t["week"], t["avg_score"], t["trend_flag"]) for t in valid_tracking]
                weeks = [t[0] for t in trend_data]
                scores = [t[1] for t in trend_data]
                trends = [t[2] for t in trend_data]

                # 创建趋势图
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=weeks,
                    y=scores,
                    mode='lines+markers',
                    name='成绩趋势',
                    line=dict(color='blue', width=3),
                    marker=dict(size=10, color='red')
                ))

                fig.update_layout(
                    title="周次成绩趋势图",
                    xaxis_title="周次",
                    yaxis_title="分数",
                    yaxis_range=[0, 100],
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

                # 详细数据
                st.markdown("### 各周次详情")
                for record in valid_tracking:
                    with st.expander(f"第{record['week']}周 - {record['description']} (平均分：{record['avg_score']})"):
                        # 考试详情
                        if record.get("exams"):
                            st.markdown("**考试列表**:")
                            for exam in record["exams"]:
                                score_color = "🟢" if exam["score"] >= 85 else "🟡" if exam["score"] >= 70 else "🔴"
                                st.write(f"{score_color} {exam['exam_name']}: {exam['score']}分")

                        # 知识点
                        if record.get("knowledge_names"):
                            st.markdown("**学习知识点**:")
                            for kp_name in record["knowledge_names"]:
                                st.write(f"- {kp_name}")

                        # 错题知识点
                        if record.get("error_knowledge"):
                            st.warning(f"**错题知识点**: {', '.join(record['error_knowledge'])}")

                        # 趋势标记
                        trend_emoji = {"up": "📈", "down": "📉", "warning": "⚠️", "normal": "➡️"}.get(record["trend_flag"], "")
                        st.caption(f"趋势：{trend_emoji}")
            else:
                st.info(f"该年级学期暂无考试记录，请选择其他年级学期")
        else:
            st.info("暂无追踪数据")

    with tab2:
        st.markdown("### 知识点掌握曲线")
        st.markdown("追踪每个知识点在不同考试中的掌握情况")

        curve_data = deep_analyzer.get_knowledge_mastery_curve(selected_student_id, grade_code)

        if curve_data:
            # 选择要查看的知识点
            kp_options = {
                f"{deep_analyzer.knowledge_points.get(kp, {}).name}": kp
                for kp in curve_data.keys()
                if kp in deep_analyzer.knowledge_points
            }

            if kp_options:
                selected_kp_name = st.selectbox("选择知识点", options=list(kp_options.keys()))
                selected_kp_code = kp_options[selected_kp_name]

                kp_curve = curve_data[selected_kp_code]

                if kp_curve:
                    # 绘制曲线
                    fig = go.Figure()

                    fig.add_trace(go.Scatter(
                        x=[p["week"] for p in kp_curve],
                        y=[p["score"] for p in kp_curve],
                        mode='lines+markers',
                        name=selected_kp_name,
                        line=dict(color='green', width=3),
                        marker=dict(size=12)
                    ))

                    fig.update_layout(
                        title=f"{selected_kp_name} - 掌握曲线",
                        xaxis_title="周次",
                        yaxis_title="分数",
                        yaxis_range=[0, 100],
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # 数据表
                    curve_df = pd.DataFrame(kp_curve)
                    st.dataframe(curve_df, use_container_width=True, hide_index=True)
                else:
                    st.info("该知识点暂无数据")
            else:
                st.info("暂无知识点数据")
        else:
            st.info("暂无知识点曲线数据")

    with tab3:
        st.markdown("### 学习轨迹诊断")
        st.markdown("基于时序数据分析学习趋势，诊断学习问题")

        if st.button("开始轨迹诊断", type="primary"):
            diagnosis = deep_analyzer.diagnose_learning_trajectory(selected_student_id, grade_code)

            if diagnosis.get("status") == "insufficient_data":
                st.warning(diagnosis.get("message", "数据不足"))
            else:
                trajectory = diagnosis.get("trajectory_analysis", {})

                # 综合诊断结果
                diagnosis_type = diagnosis.get("diagnosis_type", "normal")
                diagnosis_emoji = {
                    "excellent": "🌟",
                    "needs_attention": "⚠️",
                    "warning": "❗",
                    "normal": "✅"
                }.get(diagnosis_type, "📊")

                st.markdown(f"### {diagnosis_emoji} 诊断结果：{diagnosis_type}")

                # 趋势分析
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("平均分", trajectory.get("avg_score", 0))
                with col2:
                    st.metric("最高分", trajectory.get("max_score", 0))
                with col3:
                    st.metric("最低分", trajectory.get("min_score", 0))
                with col4:
                    st.metric("考试次数", trajectory.get("exam_count", 0))

                st.markdown("#### 趋势分析")
                trend_col, stability_col = st.columns(2)

                with trend_col:
                    trend_emoji = {
                        "rising": "📈",
                        "declining": "📉",
                        "stable": "➡️"
                    }.get(trajectory.get("trend_type", ""), "📊")
                    st.markdown(f"**趋势类型**: {trend_emoji} {trajectory.get('trend_desc', '')}")
                    st.caption(f"斜率：{trajectory.get('slope', 0)}")

                with stability_col:
                    stability_emoji = {
                        "very_stable": "🟢",
                        "stable": "🟡",
                        "fluctuating": "🟠",
                        "unstable": "🔴"
                    }.get(trajectory.get("stability", ""), "📊")
                    st.markdown(f"**稳定性**: {stability_emoji} {trajectory.get('stability_desc', '')}")
                    st.caption(f"标准差：{trajectory.get('std_dev', 0)}")

                # 问题诊断
                issues = diagnosis.get("issues", [])
                if issues:
                    st.markdown("#### ⚠️ 发现的问题")
                    for issue in issues:
                        with st.expander(f"❌ {issue['desc']}"):
                            if "details" in issue:
                                for detail in issue["details"]:
                                    kp_info = deep_analyzer.knowledge_points.get(detail[0], {})
                                    kp_name = getattr(kp_info, 'name', detail[0]) if hasattr(kp_info, 'name') else detail[0]
                                    st.write(f"- {kp_name}: 出错 {detail[1]} 次")
                            if "weeks" in issue:
                                st.write(f"发生在第 {', '.join(map(str, issue['weeks']))} 周")

                # 建议
                recommendations = diagnosis.get("recommendations", [])
                if recommendations:
                    st.markdown("#### 💡 学习建议")
                    for i, rec in enumerate(recommendations, 1):
                        st.markdown(f"{i}. {rec}")

                # 追踪摘要
                tracking_summary = diagnosis.get("tracking_summary", {})
                if tracking_summary:
                    with st.expander("📋 追踪摘要"):
                        st.write(f"- 总周次数：{tracking_summary.get('total_weeks', 0)}")
                        st.write(f"- 有考试的周次：{tracking_summary.get('valid_weeks', 0)}")
                        st.write(f"- 首次考试：第{tracking_summary.get('first_exam_week', 'N/A')}周")
                        st.write(f"- 最近考试：第{tracking_summary.get('last_exam_week', 'N/A')}周")

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

    # 检查是否有可选的学生
    if not student_dict:
        st.warning("⚠️ 暂无学生数据，无法进行对比分析")
    else:
        # 设置默认值，确保默认值在选项中
        default_students = []
        if selected_student_name and selected_student_name in student_dict:
            default_students = [selected_student_name]

        compare_students = st.multiselect(
            "选择要对比的学生（2-5 名）",
            options=list(student_dict.keys()),
            default=default_students,
            max_selections=5
        )

        # 基础统计对比
        st.subheader("📊 基础统计对比")

        if len(compare_students) >= 2:
            compare_ids = [student_dict[name] for name in compare_students]
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
        else:
            st.info("👈 请选择至少 2 名学生进行对比分析")

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
    # 使用 analyzer 的方法计算排名（已包含录入的成绩）
    rank_info = analyzer.get_score_rank(selected_student_id, selected_semesters[0] if len(selected_semesters) == 1 else None)
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
        # 获取班级分析数据（已包含 Excel 和录入的成绩）
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

            # 分数段设置（可展开）
            with st.expander("⚙️ 分数段设置", expanded=False):
                st.caption("自定义成绩分数段划分，设置后全局生效（所有学生和学期都适用）")

                # 加载当前配置
                current_ranges = load_score_ranges()

                # 使用 session_state 管理编辑中的配置
                if 'editing_score_ranges_class' not in st.session_state:
                    st.session_state.editing_score_ranges_class = [r.copy() for r in current_ranges]

                # 显示当前配置的分数段
                st.write("**当前分数段配置:**")

                # 回调函数：根据 min/max 自动更新名称
                def auto_update_name_class(idx):
                    r = st.session_state.editing_score_ranges_class[idx]
                    new_min = st.session_state.get(f"class_range_min_{idx}", r['min'])
                    new_max = st.session_state.get(f"class_range_max_{idx}", r['max'])
                    current_name = st.session_state.get(f"class_range_name_{idx}", r['name'])

                    # 检查名称是否是自动格式
                    auto_pattern = r'^\d+-\d+分 (\([^)]+\))?$'
                    is_auto_name = re.match(auto_pattern, current_name) is not None

                    # 如果是自动格式，则更新名称
                    if is_auto_name:
                        suffix_match = re.search(r'(\([^)]+\))$', current_name)
                        suffix = suffix_match.group(1) if suffix_match else ''
                        st.session_state.editing_score_ranges_class[idx]['name'] = f"{new_min}-{new_max}分{suffix}"

                # 为每个分数段创建编辑行
                ranges_to_delete = []

                for i, r in enumerate(st.session_state.editing_score_ranges_class):
                    cols = st.columns([2, 1, 1, 1])
                    with cols[0]:
                        st.text_input(
                            "名称",
                            value=r['name'],
                            key=f"class_range_name_{i}",
                            label_visibility="collapsed",
                            on_change=lambda idx=i: auto_update_name_class(idx)
                        )
                        st.session_state.editing_score_ranges_class[i]['name'] = st.session_state[f"class_range_name_{i}"]
                    with cols[1]:
                        st.number_input(
                            "最低分",
                            min_value=0,
                            max_value=100,
                            value=r['min'],
                            key=f"class_range_min_{i}",
                            label_visibility="collapsed",
                            on_change=lambda idx=i: auto_update_name_class(idx)
                        )
                        st.session_state.editing_score_ranges_class[i]['min'] = st.session_state[f"class_range_min_{i}"]
                    with cols[2]:
                        st.number_input(
                            "最高分",
                            min_value=0,
                            max_value=100,
                            value=r['max'],
                            key=f"class_range_max_{i}",
                            label_visibility="collapsed",
                            on_change=lambda idx=i: auto_update_name_class(idx)
                        )
                        st.session_state.editing_score_ranges_class[i]['max'] = st.session_state[f"class_range_max_{i}"]
                    with cols[3]:
                        if st.button("🗑️", key=f"delete_class_range_{i}"):
                            ranges_to_delete.append(i)

                # 删除标记的分数段
                for i in sorted(ranges_to_delete, reverse=True):
                    st.session_state.editing_score_ranges_class.pop(i)
                    st.rerun()

                # 添加新分数段按钮
                col_add, _ = st.columns([1, 3])
                with col_add:
                    if st.button("➕ 添加分数段", use_container_width=True):
                        st.session_state.editing_score_ranges_class.append({
                            "name": f"新分数段{len(st.session_state.editing_score_ranges_class) + 1}",
                            "min": 0,
                            "max": 59
                        })
                        st.rerun()

                # 操作按钮
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 保存配置", use_container_width=True, key="save_class_ranges"):
                        if save_score_ranges(st.session_state.editing_score_ranges_class):
                            st.success("保存成功！配置已全局生效")
                            st.rerun()
                        else:
                            st.error("保存失败")
                with col2:
                    if st.button("🔄 恢复默认", use_container_width=True, key="reset_class_ranges"):
                        if reset_to_default():
                            st.session_state.editing_score_ranges_class = [r.copy() for r in DEFAULT_SCORE_RANGES]
                            st.success("已恢复默认")
                            st.rerun()

            # 重新计算分布数据（使用保存后的配置）
            active_ranges = load_score_ranges()

            # 重新计算每个分数段的人数（使用所有学生的所有成绩）
            dist_data = {}
            for r in active_ranges:
                dist_data[r['name']] = 0

            # 使用 all_scores_for_distribution 中的所有成绩进行分数段统计
            for score in class_stats.get('all_scores_for_distribution', []):
                for r in active_ranges:
                    if r['min'] <= score <= r['max']:
                        dist_data[r['name']] += 1
                        break

            dist_labels = list(dist_data.keys())
            dist_values = list(dist_data.values())

            # 计算总人次
            total_scores = sum(dist_values)

            # 显示当前使用的分数段配置提示
            st.caption(f"📋 当前使用 {len(active_ranges)} 个分数段：{' | '.join([r['name'] for r in active_ranges])}")
            st.caption(f"📊 统计范围：{class_stats['total_students']} 名学生的所有成绩，共 {total_scores} 人次")

            if dist_values:
                col1, col2 = st.columns(2)

                # 过滤掉 0 值的分数段
                filtered_dist = {k: v for k, v in dist_data.items() if v > 0}

                if filtered_dist:
                    labels = list(filtered_dist.keys())
                    values = list(filtered_dist.values())
                    colors = ['#2ecc71', '#3498db', '#f1c40f', '#e67e22', '#e74c3c'][:len(filtered_dist)]

                    with col1:
                        # 饼图 - 使用 go.Pie
                        fig = go.Figure(data=[go.Pie(
                            labels=labels,
                            values=values,
                            hole=0.3,
                            marker_colors=colors
                        )])
                        fig.update_traces(
                            textposition='outside',
                            textinfo='percent+label',
                            texttemplate='%{label}<br>%{value} (%{percent})'
                        )
                        fig.update_layout(title=f"成绩分数段分布 (共{total_scores}人次)")
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        # 柱状图 - 使用 go.Bar
                        fig_bar = go.Figure(data=[go.Bar(
                            x=labels,
                            y=values,
                            marker_color=colors,
                            text=values,
                            textposition='outside'
                        )])
                        fig_bar.update_layout(
                            title="各分数段成绩分布",
                            xaxis_title='分数段',
                            yaxis_title='人数',
                            yaxis=dict(dtick=1),
                            showlegend=False
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("暂无成绩数据")

            st.markdown("---")

            # 成绩分布直方图
            st.subheader("📈 成绩分布直方图")

            if class_stats.get('scores') and len(class_stats['scores']) > 0:
                # 使用 go.Histogram 渲染直方图
                fig_hist = go.Figure(data=[go.Histogram(
                    x=class_stats['scores'],
                    nbinsx=20,
                    marker_color='#3498db'
                )])
                fig_hist.update_layout(
                    title='学生平均分分布直方图',
                    xaxis_title='平均分',
                    yaxis_title='人数',
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("暂无成绩数据")

            # 详细数据表
            with st.expander("📋 查看详细数据表"):
                # 获取该学期所有学生成绩（包含录入成绩）
                semester_df = analyzer.semester_data.get(selected_semester)

                # 获取录入的成绩（从数据库）
                entered_scores = ExamScoreDAO.get_all_scores()
                entered_scores_by_student = {}
                for s in entered_scores:
                    if s['semester'] != selected_semester:
                        continue
                    sid = s['student_id']
                    if sid not in entered_scores_by_student:
                        entered_scores_by_student[sid] = []
                    entered_scores_by_student[sid].append(s['score'])

                if semester_df is not None:
                    # 计算每个学生的平均分（Excel + 录入成绩）
                    student_avgs = []
                    for _, row in semester_df.iterrows():
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
                        for col in semester_df.columns:
                            if col not in ['学号', '姓名']:
                                val = row[col]
                                if pd.notna(val):
                                    try:
                                        scores.append(float(val))
                                    except (ValueError, TypeError):
                                        pass

                        # 从录入成绩获取
                        if student_id in entered_scores_by_student:
                            for score in entered_scores_by_student[student_id]:
                                if score is not None:
                                    scores.append(float(score))

                        if scores:
                            student_avgs.append({
                                '学号': student_id,
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
            # 使用 analyzer 的方法获取排名（已包含录入的成绩）
            rank1 = analyzer.get_score_rank(selected_student_id, selected_semesters[0] if len(selected_semesters) == 1 else None)
            rank2 = analyzer.get_score_rank(selected_student_id_2, selected_semesters[0] if len(selected_semesters) == 1 else None)

            # 更新排名信息
            if rank1:
                compare_data['student_1']['rank'] = rank1['rank']
            if rank2:
                compare_data['student_2']['rank'] = rank2['rank']

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
            trend_df = analyzer.get_score_trend(selected_student_id, selected_semesters[0] if len(selected_semesters) == 1 else None)

            if trend_df is not None and not trend_df.empty:
                # 添加序号
                trend_df['序号'] = range(1, len(trend_df) + 1)

                # 实际成绩点
                scatter_trace = go.Scatter(
                    x=trend_df['序号'].tolist(),
                    y=trend_df['分数'].tolist(),
                    mode='markers',
                    name='实际成绩',
                    marker=dict(size=10, color='#3498db')
                )

                fig = go.Figure(data=[scatter_trace])

                # 趋势线
                from scipy import stats
                x = trend_df['序号'].values
                y = trend_df['分数'].values
                if len(x) >= 2:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    trend_line = slope * x + intercept

                    trend_trace = go.Scatter(
                        x=x.tolist(),
                        y=trend_line.tolist(),
                        mode='lines',
                        name=f'趋势线 (斜率={slope:.2f})',
                        line=dict(color='#e74c3c', width=2, dash='dash')
                    )
                    fig.add_trace(trend_trace)

                fig.update_layout(
                    xaxis_title="考试次序",
                    yaxis_title="分数",
                    yaxis_range=[0, 100],
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无成绩数据，无法生成趋势图")

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
            # 设置默认值，确保默认值在选项中
            default_students = []
            if selected_student_name and selected_student_name in student_dict:
                default_students = [selected_student_name]

            compare_students = st.multiselect(
                "选择要对比的学生（2 名）",
                options=list(student_dict.keys()),
                default=default_students,
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

    # 直接在页面顶部显示调试信息
    import re
    test_str1 = '1(2) 班上学期'
    test_str2 = '10032-1(2) 班上学期数学考试分数'
    pattern = r'(\d+\(\d+\).*?学期)'
    r1 = re.search(pattern, test_str1)
    r2 = re.search(pattern, test_str2)
    st.write(f"**📋 正则测试:** '{test_str1}' -> '{r1.group(1) if r1 else None}' | '{test_str2}' -> '{r2.group(1) if r2 else None}'")

    st.markdown("教师视角的班级整体学习情况分析")

    # 学期选择
    selected_semester = st.selectbox(
        "选择要分析的学期",
        options=ALL_SEMESTERS,
        index=0
    )

    if selected_semester:
        # 调试：显示学期数据和录入成绩
        st.caption(f"📋 调试：selected_semester={selected_semester}")
        st.caption(f"📋 调试：analyzer.semester_data keys={list(analyzer.semester_data.keys())}")
        st.caption(f"📋 调试：analyzer.students_df shape={analyzer.students_df.shape if analyzer.students_df is not None else None}")

        # 测试标准化函数
        import re
        norm_pattern = r'(\d+\(\d+\).*?学期)'
        norm_selected = re.search(norm_pattern, selected_semester)
        norm_excel = re.search(norm_pattern, '10032-1(2) 班上学期数学考试分数')
        norm_selected_result = norm_selected.group(1).replace(' ', '') if norm_selected else None
        norm_excel_result = norm_excel.group(1).replace(' ', '') if norm_excel else None

        st.caption(f"📋 调试：norm_selected={norm_selected_result}, norm_excel={norm_excel_result}, match={norm_selected_result == norm_excel_result}")

        # 获取班级分析
        class_analysis = class_dashboard.analyze_class_overall(selected_semester)

        # 调试：显示分析结果
        st.caption(f"📋 调试：class_analysis={class_analysis}")

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

            if dist:
                # 转换为 DataFrame 以避免 plotly 参数冲突
                df_dist = pd.DataFrame({
                    '分数段': list(dist.keys()),
                    '人数': list(dist.values())
                })

                col1, col2 = st.columns(2)

                with col1:
                    # 柱状图
                    fig_bar = px.bar(
                        df_dist,
                        x='分数段',
                        y='人数',
                        labels={"x": "分数段", "y": "人数"},
                        title="各分数段人数分布",
                        color='人数',
                        color_continuous_scale="YlGnBu"
                    )
                    fig_bar.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_bar, use_container_width=True)

                with col2:
                    # 饼图
                    colors = ["#e74c3c", "#e67e22", "#f1c40f", "#3498db", "#2ecc71"]
                    fig_pie = px.pie(
                        values=df_dist['人数'],
                        names=df_dist['分数段'],
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


# ==================== 模式 14: 录入成绩查询 ====================
if analysis_mode == "📊 录入成绩查询":
    st.header("📊 录入成绩查询")
    st.markdown("查看手动录入的成绩记录")

    # 学期筛选
    filter_semester = st.selectbox(
        "选择学期",
        options=["全部"] + ALL_SEMESTERS,
        index=0
    )

    # 管理功能
    manage_mode = st.checkbox("✏️ 编辑模式", value=False)

    # 查询成绩
    if filter_semester == "全部":
        all_scores = ExamScoreDAO.get_all_scores()
    else:
        # 按学期和考试名称查询
        exam_names = set()
        all_scores = ExamScoreDAO.get_all_scores()
        all_scores = [s for s in all_scores if s.get('semester') == filter_semester]

    if all_scores:
        # 按学期和考试名称分组显示
        semesters = set(s['semester'] for s in all_scores)

        for sem in sorted(semesters):
            st.markdown(f"### {sem}")
            sem_scores = [s for s in all_scores if s['semester'] == sem]

            # 按考试名称分组
            exam_groups = {}
            for s in sem_scores:
                exam_name = s['exam_name']
                if exam_name not in exam_groups:
                    exam_groups[exam_name] = []
                exam_groups[exam_name].append(s)

            for exam_name, scores in exam_groups.items():
                with st.expander(f"📋 {exam_name} - {len(scores)} 人", expanded=False):
                    # 显示表格
                    df = pd.DataFrame(scores)
                    display_df = df[['student_name', 'student_id', 'score', 'exam_date', 'id']].copy()
                    display_df.columns = ['姓名', '学号', '分数', '考试日期', '记录 ID']
                    display_df = display_df.sort_values('分数', ascending=False)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                    # 编辑模式
                    if manage_mode:
                        st.markdown("**编辑成绩：**")

                        # 批量操作
                        st.markdown("**批量操作：**")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"🗑️ 删除此次考试 ({len(scores)}条记录)", type="secondary", key=f"del_exam_{exam_name}"):
                                # 删除该考试的所有记录
                                deleted = 0
                                for s in scores:
                                    if ExamScoreDAO.delete_score(s['id']):
                                        deleted += 1
                                st.success(f"已删除 {deleted} 条记录")
                                st.rerun()
                        with col2:
                            # 导出成绩
                            csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                label="📥 导出成绩 CSV",
                                data=csv_data,
                                file_name=f"{exam_name}_成绩.csv",
                                mime="text/csv"
                            )

                        st.markdown("---")

                        # 单个成绩编辑
                        for s in scores:
                            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                            with col1:
                                st.write(f"{s['student_name']} (学号{s['student_id']})")
                            with col2:
                                new_score = st.number_input(
                                    "分数",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=float(s['score']),
                                    step=0.5,
                                    key=f"edit_{s['id']}"
                                )
                            with col3:
                                if st.button("保存", key=f"save_{s['id']}"):
                                    if ExamScoreDAO.update_score(s['id'], new_score):
                                        st.success("更新成功")
                                        st.rerun()
                                    else:
                                        st.error("更新失败")
                            with col4:
                                if st.button("🗑️ 删除", key=f"del_{s['id']}", type="secondary"):
                                    if ExamScoreDAO.delete_score(s['id']):
                                        st.success("已删除")
                                        st.rerun()
                                    else:
                                        st.error("删除失败")
                            st.markdown("---")
    else:
        st.info("暂无录入成绩")

    # 显示最近录入统计
    st.markdown("---")
    st.subheader("📈 录入统计")

    if all_scores:
        # 按学生统计
        student_count = len(set(s['student_id'] for s in all_scores))
        exam_count = len(set((s['semester'], s['exam_name']) for s in all_scores))
        avg_score = sum(s['score'] for s in all_scores if s['score']) / len(all_scores)

        col1, col2, col3 = st.columns(3)
        col1.metric("录入学生数", str(student_count))
        col2.metric("录入考试数", str(exam_count))
        col3.metric("平均分", f"{avg_score:.1f}")
    else:
        st.write("暂无统计数据")
