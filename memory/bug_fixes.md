# Bug 修复记录

## 2026-03-24 修复

### 6. 学期名称解析错误 - UTF-8 编码导致正则匹配失败
**问题**: 上传多个学期的 Excel 文件后，学期选择下拉框只显示一个学期

**原因**: `data_manager.py:341` 中正则表达式 `r'(\d+\(\d+\) 班 [上下] 学期)'` 的 `[上下]` 字符类在 UTF-8 编码下被解释为字节序列（`[\xe4\xb8\x8a\xe4\xb8\x8b]`），而不是两个独立的中文字符，导致无法正确匹配"下"字

**修复**:
- 使用 Unicode 码点变量构建正则表达式
- `ban = '\u73ed'` (班), `xueqi = '\u5b66\u671f'` (学期)
- 新模式：`semester_pattern = r'(\d+\(\d+\)' + ban + '.*?' + xueqi + ')'`
- 现在可以正确解析"1(2) 班上学期"和"1(2) 班下学期"

**文件**: `data_manager.py`

### 7. Excel 导入目录不完整 - uploads 目录文件未被导入
**问题**: 上传到 `data/uploads/` 目录的 Excel 文件在点击"导入 Excel 成绩到数据库"时未被处理

**原因**: `app.py:899` 只遍历 `data/*.xlsx` 文件

**修复**: 添加对 `data/uploads/*.xlsx` 的遍历

**文件**: `app.py`

---

## 2026-03-23 修复

### 1. StudentScore 对象访问错误
**问题**: 宏观分析页面"针对性建议"功能报错 `TypeError: 'StudentScore' object is not subscriptable`

**原因**: `data_manager.get_scores()` 返回 `StudentScore` 对象，但代码用字典方式访问 (`s['score']`)

**修复**:
- 给 `StudentScore` 添加 `exam_date` 和 `semester` 属性
- 修改 `app.py` 中所有字典访问为属性访问

**文件**: `data_manager.py`, `app.py`

### 2. 清理数据后缓存未清除
**问题**: 清理数据库后，左侧栏仍能选择学生，其他模块仍显示数据

**原因**: 分析器缓存 (`students_df`, `student_names`, `semester_data`) 未被清除

**修复**: 清理按钮代码中添加缓存清除逻辑

**文件**: `app.py`

### 3. 清理数据时 database is locked
**问题**: 清理数据库时报错 `sqlite3.OperationalError: database is locked`

**原因**: Streamlit 缓存装饰器持有数据库连接

**修复**:
- 先清除所有缓存再删除数据库
- 直接删除并重建数据库文件（带备份）

**文件**: `app.py`

### 4. 清理后数据"恢复"问题
**问题**: 清理数据库后，点击"清除缓存并刷新"数据又出现

**原因**: Excel 文件仍在 `data` 和 `data/uploads` 目录，刷新时重新加载

**修复**:
- 添加提示说明清理数据库不会删除 Excel 文件
- 改进"移除 Excel 数据"按钮，同时清理两个目录
- 用户需先用清理数据库按钮，再用移除 Excel 按钮才能完全清空

**文件**: `app.py`

### 5. 语法错误 - 字符串引号冲突
**问题**: `SyntaxError: invalid syntax` 在 st.info() 调用处

**原因**: 字符串内部的中文引号 `"` 与外层双引号冲突

**修复**: 使用中文引号 `「」` 替代

**文件**: `app.py`

---

## 提交记录

| Commit | 描述 |
|--------|------|
| 358e752 | fix: 修复宏观分析页面 StudentScore 对象访问错误 |
| 156b36a | fix: 清理数据后清除分析器缓存 |
| 9bd58cc | fix: 清理数据时处理数据库锁定问题 |
| 92e05a8 | fix: 重建数据库方式清理所有数据 |
| 76cd33e | feat: 改进数据清理提示和功能 |
| 2755ce8 | fix: 修复字符串引号语法错误 |

---

## 数据清理正确流程

如需完全清空所有数据：
1. 点击"清理所有数据（含学生）" - 清理数据库
2. 点击"移除 Excel 数据" - 移动 Excel 文件到备份目录
3. 刷新页面 (F5)
