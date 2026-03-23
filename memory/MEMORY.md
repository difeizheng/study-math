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
