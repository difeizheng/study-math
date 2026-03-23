# Study-Math 项目记忆 - v5.6 代码架构重构

## 当前版本
- **v5.6.0** - 代码架构重构完成（2026-03-23）

## 架构重构详情 (v5.6)

### 新增基类：BaseAnalyzer
**文件**: `analyzer_base.py`

**目的**: 提取 `ScoreAnalyzer` 和 `DeepScoreAnalyzer` 的公共方法，减少代码重复

**包含方法** (9 个):
1. `_normalize_semester_name()` - 标准化学期名称
2. `_get_exam_sort_key()` - 考试名称排序
3. `refresh_entered_scores()` - 刷新录入成绩缓存
4. `get_class_stats()` - 班级统计数据
5. `_parse_semester_name()` - 解析学期名称
6. `_normalize_columns()` - 标准化列名
7. `load_excel_data()` - 加载 Excel 数据
8. `get_student_list()` - 获取学生列表
9. `__init__()` - 初始化公共属性

### 继承关系
```
BaseAnalyzer (analyzer_base.py)
├── ScoreAnalyzer (score_analyzer.py)
│   └── 特有方法: get_merged_scores(), get_score_trend(), calculate_statistics() 等
└── DeepScoreAnalyzer (deep_analyzer.py)
    └── 特有方法: get_scores(), map_exam_to_knowledge(), analyze_knowledge_mastery() 等
```

### 移除的重复代码
两个子类各移除了约 150 行重复代码：
- `_normalize_semester_name()` (两个文件中定义相同)
- `_get_exam_sort_key()` (两个文件中定义相同)
- `refresh_entered_scores()` (两个文件中定义相同)
- `get_class_stats()` (两个文件中定义相同)
- `_parse_semester_name()` (两个文件中定义相同)
- `_normalize_columns()` (两个文件中定义相同)
- `load_excel_data()` / `load_all_data()` (两个文件中逻辑相同)
- `get_student_list()` (两个文件中定义相同)

### 代码质量提升
- **代码重复率**: 降低约 30%（移除约 300 行重复代码）
- **类型注解**: 完整保留
- **测试覆盖**: 65 个测试全部通过

## 核心架构 (v5.0) - 保持不变

### 数据流
```
Excel 导入 → DataManager → 数据库
成绩录入 → DataManager → 数据库
                    ↓
        所有分析模块通过 DataManager 获取数据
```

### 核心模块
| 模块 | 文件 | 说明 |
|------|------|------|
| BaseAnalyzer | analyzer_base.py | 分析器基类（新增） |
| DataManager | data_manager.py | 统一数据访问层 |
| ScoreAnalyzer | score_analyzer.py | 成绩分析器（继承 BaseAnalyzer） |
| DeepAnalyzer | deep_analyzer.py | 深度分析器（继承 BaseAnalyzer） |

## Git 提交历史
- v5.6: 代码架构重构（提取 BaseAnalyzer 基类，移除重复代码）
- v5.5: 提升测试覆盖率（65 个测试通过）
- v5.5: 数据库查询性能优化
- v5.4: 智能组卷 PDF 导出
- v5.3: 学习习惯 + 宏观分析可视化

## 待办任务状态
- [x] 代码架构重构 (v5.5) - 已完成
- [x] 测试覆盖率提升 (v5.5) - 已完成
- [x] 性能优化 (v5.5) - 已完成

## 运行状态
- 应用运行在 http://192.168.81.59:8501
- 所有 65 个测试通过
