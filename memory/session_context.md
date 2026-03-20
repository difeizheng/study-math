# 会话上下文 - 2026-03-20

## 当前版本
- **v5.4.0** - 学习习惯分析优化、宏观分析可视化优化

## 架构版本
- **v5.0** - 数据管理重构版
  - 以 DataManager 为中心的统一数据访问架构
  - 所有分析模块通过 DataManager 获取数据
  - 数据源：Excel 导入 + 成绩录入

## 已完成的功能

### v5.4 更新 (2026-03-20)

1. **学习习惯分析优化**
   - 重构为 5 个子标签页：习惯评分、题型分析、时间分布、学习画像、趋势分析
   - 答题时间分布分析
   - 题型正确率对比（计算/应用/选择）
   - 学习习惯画像（粗心型/基础薄弱型/方法不当型/时间不足型/稳步前进型）
   - 时间序列学习行为分析

2. **宏观分析可视化优化**
   - 重构为 4 个子标签页：综合分析、多学期对比、知识盲区热力图、排名趋势
   - 多学期对比视图（最多 4 个学期）
   - 知识盲区热力图（按知识类别和年级）
   - 成绩排名趋势分析

3. **智能组卷 PDF 导出**
   - 添加 PDF 导出功能（使用 reportlab）
   - 支持 Markdown 和 PDF 双格式导出
   - 按难度组卷（基础练习/单元检测/专项突破）
   - 按知识点智能推荐题目
   - 生成答案卡和练习建议

### v5.3 更新 (2026-03-20)

1. **错题追踪本增强**
   - 按知识点和错误类型双筛选
   - 高频错题排行 Top 10
   - PDF 和 Markdown 导出功能

2. **能力成长档案数据源切换**
   - `deep_analyzer.py` 的 `_get_student_merged_scores()` 优先从数据库获取成绩
   - 录入成绩实时反映在档案中

3. **知识点关联图谱完善**
   - `knowledge_graph.get_visualization_figure()` 使用 plotly 绘制图谱
   - 颜色映射：绿 - 优秀/蓝 - 良好/黄 - 中等/红 - 需努力
   - 节点大小根据掌握程度动态调整
   - 支持年级过滤（全部/一年级至六年级）

### 核心架构 (v5.0)
1. **DataManager 统一数据服务层** (data_manager.py)
   - `get_scores()` - 获取成绩数据
   - `get_students()` - 获取学生列表
   - `get_exam_list()` - 获取考试列表
   - `get_scores_by_week()` - 按周次获取成绩
   - `get_knowledge_scores()` - 按知识点获取成绩
   - `import_excel_scores()` - 导入 Excel 成绩
   - `add_exam_score()` - 录入单条成绩

2. **周次 - 知识点映射体系** (knowledge_week_map.py)
   - 覆盖 1-6 年级上下册 (G1U-G6D)
   - `get_week_from_exam_name()` - 从考试名称解析周次
   - `get_knowledge_by_week()` - 根据周次获取知识点
   - `get_week_description()` - 获取周次学习描述

3. **数据流**
   ```
   Excel 导入 → DataManager → 数据库
   成绩录入 → DataManager → 数据库
   ↓
   所有分析模块通过 DataManager 获取数据
   ```

### 时序追踪和轨迹诊断 (v5.1) - deep_analyzer.py

1. **周次追踪视图** (`get_weekly_tracking()`)
   - 按周次追踪学生考试成绩
   - 显示每周学习的知识点
   - 记录错题知识点
   - 自动标记成绩趋势 (上升/下降/警告)

2. **知识点掌握曲线** (`get_knowledge_mastery_curve()`)
   - 追踪每个知识点在不同考试中的掌握情况
   - 按周次排序，形成学习曲线
   - 支持按知识点查看历史成绩

3. **学习轨迹诊断** (`diagnose_learning_trajectory()`)
   - **趋势分析**: 线性回归计算斜率，判断上升/下降/稳定趋势
   - **稳定性分析**: 计算标准差，判断发挥稳定性
   - **问题诊断**:
     - 反复出错的知识点
     - 连续下降警报
     - 低分警报
   - **综合诊断类型**: excellent/normal/needs_attention/warning
   - **学习建议**: 根据诊断结果生成个性化建议

### 分数段自定义配置 (v5.2)

1. **配置管理模块** (score_config.py)
   - `load_score_ranges()` - 加载分数段配置
   - `save_score_ranges()` - 保存分数段配置
   - `reset_to_default()` - 恢复默认配置
   - `get_score_distribution_for_scores()` - 根据配置计算分数分布

2. **默认分数段**
   ```json
   [
     {"name": "90-100 分 (优秀)", "min": 90, "max": 100},
     {"name": "80-89 分 (良好)", "min": 80, "max": 89},
     {"name": "70-79 分 (中等)", "min": 70, "max": 79},
     {"name": "60-69 分 (及格)", "min": 60, "max": 69},
     {"name": "60 分以下 (待提高)", "min": 0, "max": 59}
   ]
   ```

3. **配置保存**
   - 保存到 `data/settings.json`
   - 全局生效，所有学生和学期都使用同一套配置

4. **UI 功能** (app.py - 成绩趋势分析 → 分数分布模块)
   - 可展开的配置面板
   - 支持添加/编辑/删除分数段
   - 修改最低分/最高分时自动更新名称格式
   - 支持名称后缀保留（如 `60-76 分 (及格)`）
   - "💾 保存配置" 和 "🔄 恢复默认" 按钮

5. **图表渲染优化**
   - 使用 `plotly.graph_objects` 替代 `plotly.express`
   - 确保饼图和柱状图数据正确传递

### UI 增强 (app.py)

在"成绩趋势分析"模块中：
- **📈 成绩趋势图**: 4 线对比（学生成绩、班级平均分、班级最高分、班级最低分）
- **📊 分数分布**: 饼图 + 柱状图，支持自定义分数段配置

## 数据库表结构
- `students`: student_id, name, grade, semester
- `exam_scores`: id, student_id, semester, exam_name, score, exam_date, created_at, updated_at
- `error_records`: id, student_id, knowledge_code, exam_name, error_type, created_at

## Git 提交历史
- v5.4: 学习习惯分析优化、宏观分析可视化优化
- v5.3: 完成高优先级任务（错题追踪本增强、能力档案数据源切换、知识图谱完善）
- v5.2.2: 班级分析分数段分布和学期名称匹配
- v5.2.1: 同步 deep_analyzer.py 与 score_analyzer.py 的一致性
- v5.2: 自定义分数段配置功能
- v5.1.1: 修复 SAI 指数 KeyError 错误
- v5.1: 时序追踪和轨迹诊断功能
- v5.0: 数据管理重构，DataManager 统一数据访问
- v4.0: 数据管理模块架构重构
- v3.9: 录入成绩编辑和删除功能
- v3.8: 成绩录入同步到分析模块
- v3.7: 全班成绩批量录入版

## 运行状态
- 应用运行在 http://192.168.81.59:8501
- 启动时自动从 Excel 导入成绩到数据库

## 已修复的问题 (2026-03-20) - v5.2.2

### 1. AttributeError: 'dict' object has no attribute 'week'
- **位置**: deep_analyzer.py 第 1024 行 get_weekly_tracking() 方法
- **原因**: get_scores() 返回字典列表，但代码使用对象属性访问方式 (s.week)
- **修复**: 将 `s.week` 改为 `s['week']`，`s.score` 改为 `s['score']` 等

### 2. NameError: name 'compare_ids' is not defined
- **位置**: app.py 第 1835 行、1864 行等多处
- **原因**: compare_ids 只在 if 条件内定义，但在条件外被使用
- **修复**: 将使用 compare_ids 和 comparison_df 的代码都移到 `if len(compare_students) >= 2:` 条件内

### 3. 班级分析分数段分布统计错误
- **问题**: 分数段基于学生平均分统计，而非所有成绩
- **修复**:
  - score_analyzer.py: 使用 `all_scores_for_distribution` 统计所有成绩
  - app.py: 添加分数段配置面板（与成绩趋势分析一致）
  - 使用 go.Histogram 渲染直方图

### 4. 宏观分析成绩趋势图无数据
- **原因**: get_score_trend() 调用时未传入学期参数
- **修复**: 传入 `selected_semesters[0]` 参数

### 5. 班级学情看板无数据
- **原因**: _normalize_semester_name() 正则表达式不匹配带数字前缀的学期名
- **修复**: 统一使用 `r'(\d+\(\d+\).*? 学期)'` 模式，匹配 `10032-1(2) 班上学期` 和 `1(2) 班上学期`

## 已修复的问题 (2026-03-19)

### 1. NameError: Tuple is not defined
- **位置**: database.py 第 187 行
- **原因**: typing 导入缺少 Tuple
- **修复**: `from typing import Optional, List, Dict, Any, Tuple`

### 2. AttributeError: 'DeepScoreAnalyzer' object has no attribute 'get_scores'
- **位置**: deep_analyzer.py 第 869 行 get_weekly_tracking() 方法
- **原因**: 时序追踪功能调用了不存在的 get_scores 方法
- **修复**: 添加 get_scores() 方法到 DeepScoreAnalyzer 类，从数据库获取成绩数据

### 3. StreamlitAPIException: Multiselect default value must exist in options
- **位置**: app.py 第 1593 行和第 2843 行
- **原因**: 当学生列表为空时，default 值不在选项中
- **修复**: 添加条件检查，只有当 selected_student_name 在 student_dict 中才设置为默认值

### 4. KeyError: 'sai' - 学业发展指数错误
- **位置**: app.py 第 2135 行
- **原因**: analyze_student_development() 返回空字典 {} 而非错误字典
- **修复**: score_analyzer.py:476 - 将 `return {}` 改为 `return {'error': '未加载 Excel 数据，请先导入学生成绩'}`

### 5. 数据清理模块无效
- **问题**: 点击清理按钮后数据无变化
- **原因**: 只清理数据库，未清理 Excel 缓存
- **修复**: 添加移除 Excel 数据按钮和重新加载按钮

### 6. 侧边栏学生列表异常
- **问题**: 清理数据库后仍能选择学生
- **修复**: 优先从数据库读取学生，数据库为空时使用 Excel，完全无数据时显示警告

### 7. 饼图显示比例错误
- **问题**: 饼图显示 1:1 比例而非实际数据比例 (如 19:1)
- **原因**: plotly.express 的 px.pie 参数传递问题
- **修复**: 使用 plotly.graph_objects 的 go.Pie 直接传递 labels 和 values 列表

### 8. 分数段配置功能
- **需求**: 用户可自定义分数段，修改 min/max 时自动更新名称
- **实现**:
  - 创建 score_config.py 配置管理模块
  - 在成绩分布模块添加可展开配置面板
  - 使用回调函数自动更新名称格式
  - 支持保留名称后缀（如 "60-76 分 (及格)"）

## 考试名称与周次映射规则
- `周练 N` / `练习 N` → 第 N 周
- `单元 N` → 第 (N*2-1) 周
- `期中` → 第 9 周
- `期末模 N` → 第 (16+N) 周
- `期末` → 第 18 周

## 知识点体系
- 覆盖 1-6 年级上下册，共 83 个单元
- 四大知识类别：数与代数、图形与几何、统计与概率、综合与实践

## 当前服务 PID
- Streamlit 运行在端口 8501
