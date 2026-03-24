# 项目历史记忆

## 项目信息
- **项目名称**: Study-Math (学生成绩分析系统)
- **技术栈**: Python + Streamlit + SQLite + Plotly
- **运行地址**: http://192.168.81.59:8501

## 完整版本历史

| 版本 | 日期 | 主要功能 | Git 提交 |
|------|------|----------|----------|
| v5.6.1 | 2026-03-24 | 学期名称解析修复 + Excel 导入目录修复 | 063d164 |
| v5.6 | 2026-03-20 | 性能优化 + 测试覆盖率提升 | 5b11df5 |
| v5.5 | 2026-03-20 | 数据库查询性能优化 | 6b665ca |
| v5.4 | 2026-03-20 | 智能组卷 PDF 导出 | 7f3e73b |
| v5.3 | 2026-03-20 | 学习习惯 + 宏观分析可视化 | e8d65e5 |
| v5.2.2 | - | 错题追踪本 + 能力档案 + 知识图谱 | eb7bfcf |
| v5.2.1 | - | 班级分析分数段分布修复 | 3828947 |
| v5.2 | - | 同步 deep_analyzer.py | cea9b80 |
| v5.1.1 | - | 自定义分数段配置功能 | e679ccc |
| v5.1 | - | 修复 SAI 指数 KeyError | fb9679b |
| v5.0 | - | 时序追踪和轨迹诊断 | d38317d |
| v4.0 | - | 数据管理模块架构重构 | - |

## 核心架构

### 数据流
```
Excel 导入 → DataManager → 数据库 (SQLite)
成绩录入 → DataManager → 数据库
                    ↓
        所有分析模块通过 DataManager 获取数据
```

### 核心模块
| 模块 | 文件 | 说明 |
|------|------|------|
| DataManager | data_manager.py | 统一数据访问层 |
| ScoreAnalyzer | score_analyzer.py | 成绩分析器 |
| DeepAnalyzer | deep_analyzer.py | 深度分析器 |
| ErrorTracker | error_tracker.py | 错题追踪器 |
| KnowledgeGraph | knowledge_graph.py | 知识图谱 |
| PaperGenerator | paper_generator.py | 智能组卷 |
| PDFExporter | pdf_exporter.py | PDF 导出 |

### 数据库表
- `students`: 学生信息表
- `exam_scores`: 考试成绩表（带索引优化）
- `error_records`: 错题记录表

## 功能模块

### 已实现功能 (v5.6)
1. **成绩趋势分析** - 4 线对比图、分数分布饼图/柱状图
2. **宏观综合分析** - SAI 指数、定性/定量分析、多学期对比、知识盲区热力图
3. **错题追踪本** - 艾宾浩斯遗忘曲线、高频错题排行、PDF/Markdown 导出
4. **学习习惯分析** - 5 个子标签页（习惯评分、题型分析、时间分布、学习画像、趋势分析）
5. **能力成长档案** - 五大核心素养评估
6. **知识点关联图谱** - 前后置依赖关系可视化
7. **智能组卷** - 按知识点推荐、PDF/Markdown 双格式导出
8. **班级学情看板** - 全班成绩分析
9. **分数段自定义配置** - 可编辑分数段、全局生效
10. **录入成绩查询** - 增删改查功能

### 测试覆盖
- **总计 65 个测试用例**，100% 通过
- 覆盖 DataManager、Database、ScoreConfig、KnowledgeGraph、PaperGenerator、PDFExporter 等核心模块

## 性能优化
- 数据库索引：4 个（student_id, semester, exam_name, 复合索引）
- 缓存策略：@st.cache_data (5 分钟 TTL)

## 知识体系
- 覆盖 1-6 年级上下册，共 83 个单元
- 四大知识类别：数与代数、图形与几何、统计与概率、综合与实践

## 考试名称 - 周次映射规则
- `周练 N` / `练习 N` → 第 N 周
- `单元 N` → 第 (N*2-1) 周
- `期中` → 第 9 周
- `期末模 N` → 第 (16+N) 周
- `期末` → 第 18 周
