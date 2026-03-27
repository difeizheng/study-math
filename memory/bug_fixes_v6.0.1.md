---
name: v6.0.1 宏观分析 Bug 修复记录
description: v6.0.1 版本宏观分析模块完整 Bug 修复清单和解决方案
type: project
---

# v6.0.1 Bug 修复记录 (2026-03-27)

## 修复概览

本次修复主要针对宏观分析模块的多个运行时错误，包括类型错误、属性访问错误和 Plotly 图表配置错误。

---

## Bug 清单

### 1. 知识点掌握度数据结构错误
**错误**: `TypeError: '<' not supported between instances of 'dict' and 'int'`

**位置**: `app.py:2864` 个性化推荐模块

**原因**: `analyze_knowledge_mastery()` 返回嵌套字典 `{code: {avg_score, ...}}`，但代码将其当作简单分数使用

**修复**:
```python
# 修改前
mastery_for_rec = {code: score for code, score in mastery_data.items()}

# 修改后
mastery_for_rec = {code: info.get('avg_score', 50) for code, info in mastery_data.items()}
```

---

### 2. StudentScore 对象访问错误 - 成绩趋势图
**错误**: `TypeError: 'StudentScore' object is not subscriptable`

**位置**: `app.py:3478, 3522` 成绩变化趋势、成绩预测模块

**原因**: `data_manager.get_scores()` 返回 `StudentScore` 对象，但代码使用字典访问方式

**修复**:
```python
# 修改前
exam_scores_list = [float(s['score']) for s in sorted_scores]

# 修改后
exam_scores_list = [float(getattr(s, 'score', 0)) for s in sorted_scores]
```

**防御性编程**: 使用 `getattr()` 替代直接属性访问，增强容错性

---

### 3. QuestionScoreAnalyzer 初始化错误
**错误**: `TypeError: QuestionScoreAnalyzer.__init__() takes 1 positional argument but 2 were given`

**位置**: `app.py:3674` 试卷分析模块

**原因**: `QuestionScoreAnalyzer` 构造函数不接受参数，但调用时传入了 `knowledge_points`

**修复**:
```python
# 修改前
question_analyzer = QuestionScoreAnalyzer(deep_analyzer.knowledge_points)

# 修改后
question_analyzer = QuestionScoreAnalyzer()
```

---

### 4. ExamScoreDAO 返回类型不一致
**错误**: `AttributeError: 'dict' object has no attribute 'exam_name'`

**位置**: `app.py:3679` 试卷质量分析

**原因**: `ExamScoreDAO.get_scores_by_student()` 返回 `List[Dict]`，但代码使用对象属性访问

**修复**:
```python
# 修改前
exam_name = ec.exam_name
exam_groups[exam_name].append(float(ec.score))

# 修改后
exam_name = ec['exam_name']
exam_groups[exam_name].append(float(ec['score']))
```

**注意**: `ExamScoreDAO` 方法返回字典，`DataManager.get_scores()` 返回 `StudentScore` 对象

---

### 5. Plotly Scatterpolar fillopacity 属性错误
**错误**: `ValueError: Invalid property specified for object of type plotly.graph_objs.Scatterpolar: 'fillopacity'`

**位置**: `exam_analysis.py:153`, `class_analysis_ext.py:234`

**原因**: Plotly `Scatterpolar` 不支持 `fillopacity` 属性

**修复**:
```python
# 修改前
fig.add_trace(go.Scatterpolar(..., fill='toself', fillopacity=0.3))

# 修改后
fig.add_trace(go.Scatterpolar(..., fill='toself', opacity=0.3))
```

---

### 6. Plotly go.Area 图表类型不存在
**错误**: `AttributeError: module 'plotly.graph_objects' has no attribute 'Area'`

**位置**: `class_analysis_ext.py:386` 分数段分布演化图表

**原因**: Plotly 没有 `go.Area` 类型，应使用 `go.Scatter` + 堆叠配置

**修复**:
```python
# 修改前
fig.add_trace(go.Area(...))

# 修改后
fig.add_trace(go.Scatter(
    ...,
    stackgroup='one',
    fill='tonext',
    line=dict(width=0.5, color=...),
    fillcolor=...
))
```

同时移除无效的 `area_groupnorm='percent'` 参数

---

### 7. Plotly Scatter color 属性错误
**错误**: `ValueError: Invalid property specified for object of type plotly.graph_objs.Scatter: 'color'`

**位置**: `class_analysis_ext.py:392`

**原因**: `go.Scatter` 不支持 `color` 属性

**修复**:
```python
# 修改前
line=dict(width=0.5),
color=range_colors[range_name]

# 修改后
line=dict(width=0.5, color=range_colors[range_name]),
fillcolor=range_colors[range_name]
```

---

## 新增功能

### 调试模式开关

在侧边栏添加"🔧 调试模式"复选框，可以自由开关调试信息显示：

```python
# 侧边栏调试开关
st.sidebar.checkbox("🔧 调试模式", value=False, key="debug_mode")

# 条件显示调试信息
if st.session_state.get('debug_mode', False):
    st.caption(f"📋 调试：...")
```

**好处**:
- 开发调试时可以查看详细数据
- 正常使用时隐藏调试信息，保持页面整洁

---

## 数据访问模式总结

| 数据源 | 返回类型 | 访问方式 |
|--------|----------|----------|
| `DataManager.get_scores()` | `List[StudentScore]` | 属性访问 `s.score` |
| `ExamScoreDAO.get_scores_by_student()` | `List[Dict]` | 字典访问 `s['score']` |
| `ExamScoreDAO.get_all_scores()` | `List[Dict]` | 字典访问 `s['score']` |
| `deep_analyzer.analyze_knowledge_mastery()` | `Dict[str, Dict]` | 嵌套字典 `info.get('avg_score')` |

---

## 提交信息

- **Commit**: d64fa89
- **Tag**: v6.0.1
- **日期**: 2026-03-27

---

## 测试建议

修复后应测试以下功能：
1. ✅ 宏观分析 - 个性化学习推荐
2. ✅ 宏观分析 - 成绩变化趋势
3. ✅ 宏观分析 - 成绩预测与预警
4. ✅ 宏观分析 - 试卷质量分析
5. ✅ 班级分析 - 标准分转换
6. ✅ 班级分析 - 分数段分布演化
