# 学生成绩分析系统 - 项目记忆

## 项目概览
- **名称**: 学生成绩分析系统 (Study Math)
- **技术栈**: Python + Streamlit + SQLite + Excel
- **功能**: 小学数学成绩分析、知识点追踪、错题管理、学习习惯分析

## 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 成绩分析 | `score_analyzer.py` | Excel 成绩加载、统计分析 |
| 深度分析 | `deep_analyzer.py` | 知识点掌握分析、年级追踪 |
| 数据管理 | `data_manager.py` | 统一数据访问层、StudentScore 数据类 |
| 错题追踪 | `error_tracker.py` | 错题记录、艾宾浩斯复习计划 |
| 习惯分析 | `study_habit_analyzer.py` | 学习习惯画像、题型分析 |
| 基类 | `analyzer_base.py` | 公共方法提取、减少代码重复 |
| 知识可视化 | `knowledge_viz.py` | 知识图谱、能力雷达图、错题归因 |
| 成绩预测 | `score_prediction.py` | 线性回归/指数平滑预测、智能预警 |
| 班级分析 | `class_analysis_ext.py` | 标准分转换、分数段演化、多班级对比 |
| 个性推荐 | `practice_recommendation.py` | 练习题推荐、学习路径规划 |
| 试卷分析 | `exam_analysis.py` | 难度/区分度/信度分析、智能组卷 |
| 家校沟通 | `home_school_communication.py` | 学情报告、进步幅度、对比基准 |
| 数据导入导出 | `data_import_export.py` | Excel/JSON/CSV 导出、OCR 识别、API 对接 |
| 教育测量 | `educational_metrics.py` | IRT 项目反应理论、增值评价、多维度能力 |
| 交互体验 | `interactive_viz.py` | 动态趋势动画、交互仪表盘、移动端优化 |
| 学习行为 | `learning_behavior.py` | 答题时间分析、复习效果、习惯画像 |

## 重要修复 (2026-03-24) - v5.6.2

6. **学期名称解析错误** - UTF-8 编码导致正则匹配失败
   - `data_manager.py` 中 `r'(\d+\(\d+\) 班 [上下] 学期)'` 无法正确匹配多字节中文字符
   - 使用 Unicode 码点构建正则：`ban='\u73ed'`, `xueqi='\u5b66\u671f'`
   - 新模式：`r'(\d+\(\d+\)' + ban + '.*?' + xueqi + ')'
   - 现在可以正确区分"上学期"和"下学期"

7. **Excel 导入目录不完整** - uploads 目录文件未被导入
   - `app.py` 中"导入 Excel 成绩到数据库"只遍历 `data/*.xlsx`
   - 添加对 `data/uploads/*.xlsx` 的遍历
   - 上传的文件现在可以正确导入

8. **学期选择顺序错误** - 学期未按照年级排序
   - `analyzer_base.py` 添加 `_sort_semesters()` 方法
   - 排序规则：先按年级 (1 班→2 班→3 班)，同一年级上学期在前、下学期在后
   - `app.py` 中 `ALL_SEMESTERS` 使用排序后的列表
   - 现在正确显示：1(2) 班上学期 → 1(2) 班下学期 → 2(2) 班上学期

9. **知识点深度分析字典访问错误** - `'dict' object has no attribute 'week'`
   - `deep_analyzer.py` 中 `get_knowledge_mastery_curve()` 使用对象属性访问
   - 但 `get_scores()` 返回字典列表
   - 改为字典访问：`score_record['week']`, `score_record['score']`

## 重要修复 (2026-03-23)

1. **StudentScore 对象访问错误** - 字典访问改为属性访问
   - 添加 `exam_date` 和 `semester` 属性到 StudentScore
   - 修复 app.py 中所有 `s['score']` 为 `s.score`

2. **清理数据缓存未清除** - 添加缓存清理逻辑
   - 清理按钮代码中清除 analyzer、deep_analyzer 缓存

3. **database is locked** - 删除重建数据库方式
   - 不再使用 DELETE 语句，直接删除并重建数据库文件
   - 清理前自动备份数据库（带时间戳）

4. **清理后数据"恢复"** - Excel 文件需手动移除
   - 提示用户清理数据库不会删除 Excel 文件
   - "移除 Excel 数据"按钮同时清理 data 和 data/uploads 目录

5. **语法错误** - 字符串引号冲突
   - 中文引号 `「」` 替代双引号避免冲突

## 数据清理流程

完全清空数据：
1. "清理所有数据（含学生）"按钮 → 清理数据库
2. "移除 Excel 数据"按钮 → 移动 Excel 到 backup
3. 刷新页面 (F5)

## 架构特点

- **BaseAnalyzer 基类**: 提取 9 个公共方法，减少 300 行重复代码
- **DataManager 统一访问**: 所有分析器通过 DataManager 访问数据
- **Streamlit 缓存**: 使用 `@st.cache_data` 装饰器优化性能
- **PWA 支持**: 支持移动端添加到主屏幕

## 测试
- 65 个单元测试，覆盖数据管理、导入、分析等模块
- 运行：`python -m pytest tests/ -v`

## 扩展功能实现 (2026-03-24 ~ 2026-03-25)

### 已实现

1. **知识点掌握度可视化** (`knowledge_viz.py`)
   - 知识图谱追踪（前后置依赖关系可视化）
   - 能力雷达图（数与代数、图形与几何、统计与概率、综合与实践）
   - 错题归因分析（概念不清、计算错误、审题问题、粗心大意）

2. **成绩预测与预警** (`score_prediction.py`)
   - 线性回归预测（scipy.stats.linregress）
   - 指数平滑预测（alpha 平滑系数）
   - 智能预警系统（成绩下滑、低分、波动大、危险状态）
   - 目标达成分析（进度追踪、预计达成考试次数）

3. **班级/年级维度分析** (`class_analysis_ext.py`)
   - 标准分转换（Z 分数、T 分数、百分位、等级 A/B/C/D/E）
   - 分数段分布演化（堆叠面积图追踪趋势）
   - 多班级对比（雷达图、热力图）

4. **个性化推荐** (`practice_recommendation.py`)
   - 练习题推荐（根据薄弱知识点和掌握度）
   - 学习路径规划（基于知识依赖关系的拓扑排序）
   - 相似题推荐（基于题目类型和难度）

5. **试卷分析** (`exam_analysis.py`)
   - 试卷质量分析：难度系数、区分度、信度
   - 题目得分率分析：错误率 TOP10、得分热力图
   - 智能组卷：根据学生水平推荐题目和难度分布

6. **家校沟通功能** (`home_school_communication.py`)
   - 学情报告自动生成（PDF/JSON 格式）
   - 进步幅度展示（前后半期对比、趋势分析）
   - 对比基准说明（与班级平均分对比、百分位排名）

7. **数据导入导出** (`data_import_export.py`)
   - Excel/JSON/CSV 格式导出
   - OCR 识别成绩单（模拟实现，支持集成百度/腾讯 OCR）
   - API 对接器（与其他教育系统数据交换）

8. **教育测量学指标** (`educational_metrics.py`)
   - IRT 项目反应理论（3PL 模型，难度/区分度/猜测参数）
   - 增值评价（实际增长 vs 预期增长，效能等级）
   - 多维度能力模型（知识、技能、推理、应用、反思五维）

9. **交互体验优化** (`interactive_viz.py`)
   - 动态趋势动画（播放/暂停控制，滑块进度）
   - 交互式仪表盘（综合概览、两人对比）
   - 移动端适配优化（响应式布局、PWA 支持）

10. **学习行为分析** (`learning_behavior.py`)
    - 答题时间分析（效率评分、节奏判断、时段分布）
    - 复习效果追踪（艾宾浩斯遗忘曲线、保持率）
    - 学习习惯画像（坚持度、专注度、毅力评分）

## 版本历史

### v6.0.0 (2026-03-25) - 扩展功能完整版
**新增功能**: 完成全部 10 个扩展功能模块
- 家校沟通、数据导入导出、教育测量指标、交互体验、学习行为分析

**Bug 修复**:
- `get_student_id` 方法不存在 → 添加 `get_student_id_by_name()` 辅助函数
- 字典访问错误 → `.score` 改为 `['score']`
- DataFrame 列名错误 → `'name'` 改为 `'姓名'`
- 知识点掌握度数据结构转换 → 提取 `avg_score`
- Plotly indicator domain 错误 → 移除 `row/col` 属性

**新增文件** (10 个模块):
- `knowledge_viz.py`, `score_prediction.py`, `class_analysis_ext.py`
- `practice_recommendation.py`, `exam_analysis.py`
- `home_school_communication.py`, `data_import_export.py`
- `educational_metrics.py`, `interactive_viz.py`, `learning_behavior.py`

### v6.0.2 (2026-03-27) - 成绩趋势分析排序修复
**Bug 修复** (4 个):
1. 学期 tab 排序错误 → 使用简单字符串匹配提取年级和学期类型
2. 考试名称 x 轴排序错误 → 按 Excel 列原始顺序排序，按学期分组处理
3. 多个页面重复选择学生 → 统一使用侧边栏学生选择框
4. 交互体验页面 NameError → 使用 analyzer.student_names 获取学生列表

**修改文件**:
- `analyzer_base.py` - 修复 `_sort_semesters` 和 `get_class_stats` 方法
- `score_analyzer.py` - 修复 `get_score_trend` 和 `get_merged_scores` 排序逻辑
- `app.py` - 移除 4 个页面的重复学生选择框

**提交**: 62bbf20 | **Tag**: v6.0.2

### v6.0.1 (2026-03-27) - 宏观分析 Bug 修复版
**Bug 修复** (7 个):
1. 知识点掌握度数据结构错误 → 提取 `avg_score`
2. StudentScore 对象访问错误 → 使用 `getattr()` 防御性访问
3. QuestionScoreAnalyzer 初始化参数错误 → 移除参数
4. ExamScoreDAO 返回字典 → 改用 `['score']` 访问
5. Plotly Scatterpolar `fillopacity` → 改为 `opacity`
6. Plotly `go.Area` 不存在 → 改为 `go.Scatter` + `stackgroup`
7. Plotly Scatter `color` 属性 → 改为 `line.color` + `fillcolor`

**新增功能**:
- 调试模式开关：侧边栏"🔧 调试模式"复选框，控制调试信息显示/隐藏

**提交**: d64fa89 | **Tag**: v6.0.1

### v5.6.2 (2026-03-24)

