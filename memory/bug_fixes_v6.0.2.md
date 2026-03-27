---
name: v6.0.2 成绩趋势分析排序修复
description: v6.0.2 版本成绩趋势分析学期和考试排序问题修复
type: project
---

# v6.0.2 Bug 修复记录 (2026-03-27)

## 修复概览

本次修复主要针对成绩趋势分析模块的学期和考试排序问题，以及多个页面重复选择学生的问题。

---

## Bug 清单

### 1. 学期 tab 排序错误
**问题**: 学期 tab 未按年级和学期类型正确排序

**原因**: `_sort_semesters` 方法使用 Unicode 码点构建正则表达式，但实际匹配时无法正确匹配中文字符

**修复**:
```python
# 修改前 - 使用 Unicode 码点构建正则
ban = '\u73ed'
shang = '\u4e0a'
xia = '\u4e0b'
pattern = r'(\d+)\((\d+)\)' + ban + r'(' + shang + r'|' + xia + r')' + xue + qi
match = re.search(pattern, semester)

# 修改后 - 使用简单字符串匹配
def semester_sort_key(semester: str) -> Tuple[int, int]:
    match = re.match(r'(\d+)\(', semester)
    if match:
        grade = int(match.group(1))
        semester_order = 0 if '上学期' in semester else 1
        return (grade, semester_order)
    return (999, 999)
```

**文件**: `analyzer_base.py:51-87`

---

### 2. 考试名称 x 轴排序错误
**问题**: 成绩趋势图的 x 轴考试名称未按 Excel 列原始顺序显示

**原因**:
1. `get_merged_scores` 遍历 `self.students_df.columns` 的顺序不确定
2. `exam_order` 只包含最后一个 Excel 文件的列，其他学期的列索引为 999

**修复**:
```python
# get_merged_scores - 按 exam_order 顺序遍历
for col in self.exam_order:
    if col in self.students_df.columns and col not in ['学号', '姓名']:
        # 获取成绩
        ...

# get_score_trend - 按学期分组排序
for col, value in scores.items():
    if col in self.exam_order:
        exam_index = self.exam_order.index(col)
    else:
        # 在该学期的 exam_order 中查找
        for sem_name, sem_df in self.semester_data.items():
            exam_cols = [c for c in sem_df.columns if c not in ['学号', '姓名']]
            if exam in exam_cols:
                exam_index = exam_cols.index(exam)
                break

# get_class_stats - 按学期分组，每个学期内按原始列顺序排序
for sem_name in self._sort_semesters(list(semester_groups.keys())):
    sem_cols = semester_groups[sem_name]
    # 获取该学期的原始列顺序
    for raw_sem_name, sem_df in self.semester_data.items():
        if self._normalize_semester_name(raw_sem_name) == sem_name:
            original_order = [c for c in sem_df.columns if c not in ['学号', '姓名']]
            break
```

**文件**: `score_analyzer.py:27-73, 101-130`, `analyzer_base.py:137-177`

---

### 3. 多个页面重复选择学生
**问题**: 家校沟通、教育测量指标、交互体验、学习行为分析页面有独立的学生选择框，与侧边栏重复

**修复**: 移除各页面的学生选择框，统一使用侧边栏已选择的学生

```python
# 修改前
student_names = sorted(list(analyzer.student_names.values()))
selected_student_name = st.selectbox("选择学生", student_names)
selected_student_id = get_student_id_by_name(selected_student_name)

# 修改后
if not selected_student_id:
    st.warning("请先在侧边栏选择学生")
else:
    st.info(f"当前分析学生：**{student_name}** (学号：{selected_student_id})")
```

**文件**: `app.py`
- 家校沟通：第 5154 行
- 教育测量指标：第 5468 行
- 交互体验：第 5655 行
- 学习行为分析：第 5811 行

---

### 4. 交互体验页面 NameError
**问题**: `NameError: name 'student_names' is not defined`

**位置**: `app.py:5752` 交互体验 - 两人对比模式

**原因**: 移除学生选择框后，`student_names` 变量未定义

**修复**:
```python
# 修改前
compare_students = st.multiselect(
    "选择两个学生进行对比",
    student_names,  # 未定义
    max_selections=2
)

# 修改后
student_names_list = sorted(list(analyzer.student_names.values()))
compare_students = st.multiselect(
    "选择两个学生进行对比",
    student_names_list,
    max_selections=2
)
```

**文件**: `app.py:5748-5754`

---

## 排序规则

### 学期排序
1. 先按年级排序（1 班 → 2 班 → 3 班...）
2. 同一年级内，上学期在前，下学期在后

例如：`1(2) 班上学期 < 1(2) 班下学期 < 2(2) 班上学期 < 2(2) 班下学期`

### 考试排序
- 按 Excel 列的原始顺序（从左到右，即时间顺序）
- 不同学期的考试分别按各自学期的原始顺序排序

---

## 测试建议

修复后应测试以下功能：
1. ✅ 成绩趋势分析 - 学期 tab 按正确顺序显示
2. ✅ 成绩趋势分析 - 考试名称 x 轴按 Excel 列顺序显示
3. ✅ 班级统计（平均分/最高分/最低分）与个人成绩顺序一致
4. ✅ 家校沟通 - 使用侧边栏学生选择
5. ✅ 教育测量指标 - 使用侧边栏学生选择
6. ✅ 交互体验 - 使用侧边栏学生选择，两人对比功能正常
7. ✅ 学习行为分析 - 使用侧边栏学生选择

---

## 提交信息

- **Commit**: 62bbf20
- **Tag**: v6.0.2
- **日期**: 2026-03-27
