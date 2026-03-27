# Study-Math 项目记忆索引

## 记忆文件列表

- [MEMORY.md](MEMORY.md) - 项目主记忆，包含版本历史和架构概述
- [bug_fixes_v6.0.2.md](bug_fixes_v6.0.2.md) - v6.0.2 成绩趋势分析排序修复
- [bug_fixes_v6.0.1.md](bug_fixes_v6.0.1.md) - v6.0.1 宏观分析 Bug 修复
- [bug_fixes.md](bug_fixes.md) - v5.6.2 及之前版本 Bug 修复记录
- [project_history.md](project_history.md) - 项目历史和版本信息
- [refactoring_v5.6.md](refactoring_v5.6.md) - v5.6 代码架构重构
- [question_bank_expansion.md](question_bank_expansion.md) - 智能组卷题库扩充

## 当前版本
- **v6.0.2** - 成绩趋势分析排序修复（2026-03-27）

## 快速链接
- Git Tag: v6.0.2
- 提交：62bbf20

## 当前版本
- **v4.0** - 数据管理架构重构版（2026-03-18）

## 最新架构变更

### 数据管理模块新结构
```
侧边栏
├── 选择学生
├── 选择学期
├── 分析模式
│   ├── 📈 成绩趋势分析
│   ├── 🧠 知识点深度分析
│   ├── 📋 诊断报告
│   ├── 👥 多学生对比
│   ├── ⚠️ 成绩预警
│   ├── 📊 班级分析
│   ├── 🔬 宏观分析
│   ├── 📕 错题追踪本
│   ├── 🕸️ 知识点关联图谱
│   ├── 🌟 能力成长档案
│   ├── 📝 学习习惯分析
│   ├── 🏫 班级学情看板
│   ├── 📄 智能组卷
│   ├── 📝 成绩录入
│   ├── 📊 录入成绩查询
│   └── ⚙️ 数据管理 ← 新增主模式
```

### 数据管理子菜单（点击后右侧展示内容）
1. **📂 Excel 数据导入** - 上传并导入 Excel 成绩数据文件
2. **📁 导入文件管理** - 管理已导入的 Excel 文件（查看列表、删除文件）
3. **📊 导入数据管理** - 浏览 Excel 成绩数据（自动过滤空列）
4. **⚙️ 系统数据设置** - 管理系统数据库（清理数据、同步学生）

## 关键功能实现

### 导入数据管理 - 空列过滤
```python
# 只保留至少有一个学生有成绩的考试列
score_cols = [col for col in df.columns if col not in ['学号', '姓名']]
valid_cols = ['学号', '姓名']
for col in score_cols:
    if df[col].notna().any():
        valid_cols.append(col)
df_filtered = df[valid_cols]
```
- 显示绿色提示：有成绩的考试列表
- 显示蓝色提示：隐藏的空考次数量

### 核心代码位置
- `app.py` 第 165-420 行：数据管理模块主逻辑
- `app.py` 第 167-171 行：分析模式 radio 选择器（包含⚙️ 数据管理）
- `app.py` 第 178-417 行：数据管理子菜单和内容

## 数据库表结构
- `students` - 学生信息表
- `exam_scores` - 录入成绩表
- `error_records` - 错题记录表

## 应用运行状态
- 运行地址：http://localhost:8501
- 启动命令：`streamlit run app.py --server.headless=true --server.address=0.0.0.0 --server.port=8501`

## Git 提交历史
- v4.0: 数据管理架构重构（侧边栏 expander → 独立模块 + 子菜单）
- v3.12: 数据管理增强版
- v3.9: 成绩录入编辑和删除功能
- v3.8: 成绩录入同步到分析模块
- v3.7: 全班成绩批量录入功能

## 重要修复记录
1. 修复 `get_db_connection` 未导入错误
2. 修复 `error_entries` 表名错误（应为 `error_records`）
3. 修复 `_parse_semester_name` 正则表达式无法匹配中文字符问题
4. 修复 `get_score_trend` 返回的学期名称未标准化问题
