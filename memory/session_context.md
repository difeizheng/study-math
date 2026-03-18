# 会话上下文 - 2026-03-19

## 当前版本
- **v5.1** - 时序追踪和轨迹诊断增强版

## 架构版本
- **v5.0** - 数据管理重构版
  - 以 DataManager 为中心的统一数据访问架构
  - 所有分析模块通过 DataManager 获取数据
  - 数据源：Excel 导入 + 成绩录入

## 已完成的功能

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

### UI 增强 (app.py)

在"知识点深度分析"模块中添加三个新标签页：
1. **📊 周次追踪**: 成绩趋势图 + 各周次详情
2. **📉 知识点曲线**: 选择知识点查看掌握曲线
3. **🔍 轨迹诊断**: 完整的学习诊断报告

## 数据库表结构
- `students`: student_id, name, grade, semester
- `exam_scores`: id, student_id, semester, exam_name, score, exam_date, created_at, updated_at
- `error_records`: id, student_id, knowledge_code, exam_name, error_type, created_at

## 考试名称与周次映射规则
- `周练 N` / `练习 N` → 第 N 周
- `单元 N` → 第 (N*2-1) 周
- `期中` → 第 9 周
- `期末模 N` → 第 (16+N) 周
- `期末` → 第 18 周

## 知识点体系
- 覆盖 1-6 年级上下册，共 83 个单元
- 四大知识类别：数与代数、图形与几何、统计与概率、综合与实践

## Git 提交历史
- v5.1: 时序追踪和轨迹诊断功能
- v5.0: 数据管理重构，DataManager 统一数据访问
- v4.0: 数据管理模块架构重构
- v3.9: 录入成绩编辑和删除功能
- v3.8: 成绩录入同步到分析模块
- v3.7: 全班成绩批量录入版

## 运行状态
- 应用运行在 http://localhost:8501
- 启动时自动从 Excel 导入成绩到数据库

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
