"""
知识点关联图谱模块
展示知识点之间的前后置依赖关系，帮助发现知识断层的根源
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
import json
from pathlib import Path


@dataclass
class KnowledgeNode:
    """知识点节点"""
    code: str
    name: str
    grade: str
    semester: str
    category: str
    # 前置知识点（学习该知识点前需要掌握的知识）
    prerequisites: List[str] = field(default_factory=list)
    # 后置知识点（该知识点是哪些知识的基础）
    dependencies: List[str] = field(default_factory=list)
    # 重要程度 (1-5)
    importance: int = 3
    # 难度等级 (1-5)
    difficulty: int = 3


# 知识点依赖关系定义
# 格式："知识点编码": ["前置知识 1", "前置知识 2", ...]
KNOWLEDGE_DEPENDENCIES = {
    # ==================== 一年级上册 ====================
    "G1U01": [],  # 准备课，无前置知识
    "G1U02": [],  # 位置，无前置知识
    "G1U03": ["G1U01"],  # 1-5 的认识和加减法，需要准备课基础
    "G1U04": [],  # 认识图形（一），相对独立
    "G1U05": ["G1U03"],  # 6-10 的认识和加减法，需要 1-5 基础
    "G1U06": ["G1U03"],  # 11-20 各数的认识，需要 1-5 基础
    "G1U07": [],  # 认识钟表，相对独立
    "G1U08": ["G1U05", "G1U06"],  # 20 以内的进位加法，需要 6-10 和 11-20 基础

    # ==================== 一年级下册 ====================
    "G1D01": ["G1U04"],  # 认识图形（二），需要立体图形基础
    "G1D02": ["G1U08"],  # 20 以内的退位减法，需要进位加法基础
    "G1D03": ["G1U06"],  # 100 以内数的认识，需要 11-20 基础
    "G1D04": [],  # 认识人民币，相对独立
    "G1D05": ["G1U03", "G1U05"],  # 100 以内的加法和减法（一），需要基础加减法

    # ==================== 二年级上册 ====================
    "G2U01": [],  # 长度单位，相对独立
    "G2U02": ["G1D05"],  # 100 以内的加法和减法（二），需要一年级加减法基础
    "G2U03": [],  # 角的初步认识，相对独立
    "G2U04": ["G1U05"],  # 表内乘法（一），需要 6-10 的认识基础
    "G2U05": [],  # 观察物体，相对独立
    "G2U06": ["G2U04"],  # 表内乘法（二），需要乘法（一）基础
    "G2U07": ["G1U07"],  # 认识时间，需要认识钟表基础

    # ==================== 二年级下册 ====================
    "G2D01": [],  # 数据收集整理，相对独立
    "G2D02": ["G2U04", "G2U06"],  # 表内除法（一），需要乘法基础
    "G2D03": [],  # 图形的运动，相对独立
    "G2D04": ["G2D02"],  # 表内除法（二），需要除法（一）基础
    "G2D05": ["G2U04", "G2U06"],  # 混合运算，需要乘法基础
    "G2D06": ["G2D02", "G2U06"],  # 有余数的除法，需要除法和乘法基础
    "G2D07": ["G1D03"],  # 万以内数的认识，需要 100 以内数的认识基础

    # ==================== 三年级上册 ====================
    "G3U01": ["G2U07"],  # 时、分、秒，需要认识时间基础
    "G3U02": ["G2U02"],  # 万以内的加法和减法（一），需要 100 以内加减法基础
    "G3U03": ["G2U01"],  # 测量，需要长度单位基础
    "G3U04": ["G3U02"],  # 万以内的加法和减法（二），需要（一）基础
    "G3U05": ["G2U04", "G2U06"],  # 倍的认识，需要乘法基础
    "G3U06": ["G2U04", "G2U06", "G1U05"],  # 多位数乘一位数，需要表内乘法基础
    "G3U07": ["G1U04", "G1D01"],  # 长方形和正方形，需要图形认识基础
    "G3U08": [],  # 分数的初步认识，相对独立但重要

    # ==================== 三年级下册 ====================
    "G3D01": ["G1U02"],  # 位置与方向，需要位置基础
    "G3D02": ["G2D02", "G2D04"],  # 除数是一位数的除法，需要表内除法基础
    "G3D03": ["G2D01"],  # 复式统计表，需要数据收集整理基础
    "G3D04": ["G3U06"],  # 两位数乘两位数，需要多位数乘一位数基础
    "G3D05": ["G3U07"],  # 面积，需要长方形和正方形基础
    "G3D06": ["G3U01"],  # 年、月、日，需要时分秒基础
    "G3D07": ["G3U08"],  # 小数的初步认识，需要分数基础
}

# 知识点重要程度评级 (1-5)
KNOWLEDGE_IMPORTANCE = {
    # 核心基础知识点（重要性 5）
    "G1U03": 5,  # 1-5 的认识和加减法 - 数学基础
    "G1U05": 5,  # 6-10 的认识和加减法 - 计算基础
    "G1U08": 5,  # 20 以内的进位加法 - 计算核心
    "G1D02": 5,  # 20 以内的退位减法 - 计算核心
    "G2U04": 5,  # 表内乘法（一）- 乘法基础
    "G2U06": 5,  # 表内乘法（二）- 乘法核心
    "G2D02": 5,  # 表内除法（一）- 除法基础
    "G3U06": 5,  # 多位数乘一位数 - 乘法进阶
    "G3D02": 5,  # 除数是一位数的除法 - 除法进阶
    "G3U08": 5,  # 分数的初步认识 - 数的概念扩展

    # 重要知识点（重要性 4）
    "G1D03": 4,  # 100 以内数的认识
    "G1D05": 4,  # 100 以内的加法和减法
    "G2U02": 4,  # 100 以内的加法和减法（二）
    "G2D07": 4,  # 万以内数的认识
    "G3U02": 4,  # 万以内的加法和减法（一）
    "G3U04": 4,  # 万以内的加法和减法（二）
    "G3D04": 4,  # 两位数乘两位数
    "G3D05": 4,  # 面积

    # 一般知识点（重要性 3）
    "G1U01": 3,
    "G1U02": 3,
    "G1U04": 3,
    "G1U06": 3,
    "G1U07": 3,
    "G1D01": 3,
    "G1D04": 3,
    "G2U01": 3,
    "G2U03": 3,
    "G2U05": 3,
    "G2U07": 3,
    "G2D01": 3,
    "G2D03": 3,
    "G2D04": 3,
    "G2D05": 3,
    "G2D06": 3,
    "G3U01": 3,
    "G3U03": 3,
    "G3U05": 3,
    "G3U07": 3,
    "G3D01": 3,
    "G3D03": 3,
    "G3D06": 3,
    "G3D07": 3,
}

# 知识点难度评级 (1-5)
KNOWLEDGE_DIFFICULTY = {
    # 高难度知识点
    "G1U08": 4,  # 20 以内的进位加法
    "G1D02": 4,  # 20 以内的退位减法
    "G2U04": 4,  # 表内乘法（一）- 乘法概念抽象
    "G2D02": 4,  # 表内除法（一）- 除法概念抽象
    "G2D05": 4,  # 混合运算 - 运算顺序
    "G2D06": 4,  # 有余数的除法 - 抽象概念
    "G3U08": 4,  # 分数的初步认识 - 新概念
    "G3D04": 4,  # 两位数乘两位数 - 复杂计算
    "G3D05": 4,  # 面积 - 抽象概念

    # 中等难度
    "G1D03": 3,
    "G1D05": 3,
    "G2U02": 3,
    "G2U06": 3,
    "G2D04": 3,
    "G2D07": 3,
    "G3U02": 3,
    "G3U04": 3,
    "G3U06": 3,
    "G3U07": 3,
    "G3D02": 3,

    # 较低难度
    "G1U01": 2,
    "G1U02": 2,
    "G1U03": 2,
    "G1U04": 2,
    "G1U05": 2,
    "G1U06": 2,
    "G1U07": 2,
    "G1D01": 2,
    "G1D04": 2,
    "G2U01": 2,
    "G2U03": 2,
    "G2U05": 2,
    "G2U07": 2,
    "G2D01": 2,
    "G2D03": 2,
    "G3U01": 2,
    "G3U03": 2,
    "G3U05": 2,
    "G3D01": 2,
    "G3D03": 2,
    "G3D06": 2,
    "G3D07": 2,
}


class KnowledgeGraph:
    """知识点关联图谱"""

    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self._build_graph()

    def _build_graph(self):
        """构建知识图谱"""
        from deep_analyzer import KNOWLEDGE_SYSTEM

        # 创建所有节点
        for code, kp in KNOWLEDGE_SYSTEM.items():
            self.nodes[code] = KnowledgeNode(
                code=code,
                name=kp.name,
                grade=kp.grade,
                semester=kp.semester,
                category=kp.category,
                importance=KNOWLEDGE_IMPORTANCE.get(code, 3),
                difficulty=KNOWLEDGE_DIFFICULTY.get(code, 3),
            )

        # 建立依赖关系
        for code, prereqs in KNOWLEDGE_DEPENDENCIES.items():
            if code in self.nodes:
                self.nodes[code].prerequisites = prereqs

        # 建立后置依赖（被依赖关系）
        for code, prereqs in KNOWLEDGE_DEPENDENCIES.items():
            for prereq in prereqs:
                if prereq in self.nodes:
                    self.nodes[prereq].dependencies.append(code)

    def get_prerequisites(self, knowledge_code: str, recursive: bool = False) -> List[str]:
        """
        获取知识点的前置知识

        Args:
            knowledge_code: 知识点编码
            recursive: 是否递归获取所有前置知识（包括间接前置）
        """
        if knowledge_code not in self.nodes:
            return []

        if not recursive:
            return self.nodes[knowledge_code].prerequisites

        # 递归获取所有前置知识
        all_prereqs = set()
        to_visit = list(self.nodes[knowledge_code].prerequisites)

        while to_visit:
            current = to_visit.pop()
            if current not in all_prereqs and current in self.nodes:
                all_prereqs.add(current)
                to_visit.extend(self.nodes[current].prerequisites)

        return list(all_prereqs)

    def get_dependencies(self, knowledge_code: str, recursive: bool = False) -> List[str]:
        """
        获取知识点的后置知识（依赖该知识的其他知识）

        Args:
            knowledge_code: 知识点编码
            recursive: 是否递归获取所有后置知识
        """
        if knowledge_code not in self.nodes:
            return []

        if not recursive:
            return self.nodes[knowledge_code].dependencies

        # 递归获取所有后置知识
        all_deps = set()
        to_visit = list(self.nodes[knowledge_code].dependencies)

        while to_visit:
            current = to_visit.pop()
            if current not in all_deps and current in self.nodes:
                all_deps.add(current)
                to_visit.extend(self.nodes[current].dependencies)

        return list(all_deps)

    def get_learning_path(self, knowledge_code: str) -> List[str]:
        """
        获取学习某个知识点的推荐路径（前置知识的合理学习顺序）
        使用拓扑排序确保先学前置知识
        """
        if knowledge_code not in self.nodes:
            return []

        # 获取所有前置知识
        all_prereqs = self.get_prerequisites(knowledge_code, recursive=True)
        all_prereqs.append(knowledge_code)

        # 拓扑排序
        in_degree = {code: 0 for code in all_prereqs}

        # 计算入度
        for code in all_prereqs:
            for prereq in self.nodes[code].prerequisites:
                if prereq in all_prereqs:
                    in_degree[code] += 1

        # Kahn 算法
        queue = [code for code in all_prereqs if in_degree[code] == 0]
        result = []

        while queue:
            # 优先选择重要性高的
            queue.sort(key=lambda x: -self.nodes[x].importance)
            current = queue.pop(0)
            result.append(current)

            for dep in self.nodes[current].dependencies:
                if dep in all_prereqs:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

        return result

    def analyze_weak_point_impact(self, weak_knowledge_codes: List[str]) -> Dict:
        """
        分析薄弱知识点的影响范围

        Args:
            weak_knowledge_codes: 薄弱的知识点编码列表

        Returns:
            影响分析结果
        """
        impact = {
            "direct_impact": [],  # 直接影响的知识点
            "indirect_impact": [],  # 间接影响的知识点
            "affected_categories": set(),  # 影响的知识类别
            "risk_level": "low",  # 风险等级
        }

        all_affected = set()

        for weak_code in weak_knowledge_codes:
            if weak_code not in self.nodes:
                continue

            # 获取所有后置依赖（受影响的知识点）
            deps = self.get_dependencies(weak_code, recursive=True)
            all_affected.update(deps)

            # 直接影响的知识点
            impact["direct_impact"].extend(self.nodes[weak_code].dependencies)

        # 去重
        impact["direct_impact"] = list(set(impact["direct_impact"]))
        impact["indirect_impact"] = list(all_affected - set(impact["direct_impact"]))

        # 统计影响的知识类别
        for code in all_affected:
            if code in self.nodes:
                impact["affected_categories"].add(self.nodes[code].category)
        impact["affected_categories"] = list(impact["affected_categories"])

        # 评估风险等级
        total_affected = len(all_affected)
        if total_affected >= 10:
            impact["risk_level"] = "high"
        elif total_affected >= 5:
            impact["risk_level"] = "medium"
        else:
            impact["risk_level"] = "low"

        return impact

    def find_root_cause(self, target_knowledge: str, mastered_knowledge: List[str]) -> Dict:
        """
        找出学习困难的根本原因（哪个前置知识没掌握好）

        Args:
            target_knowledge: 目标知识点（学不会的那个）
            mastered_knowledge: 已掌握的知识点编码列表

        Returns:
            根本原因分析
        """
        if target_knowledge not in self.nodes:
            return {"error": "知识点不存在"}

        mastered_set = set(mastered_knowledge)
        result = {
            "target": target_knowledge,
            "target_name": self.nodes[target_knowledge].name,
            "missing_prerequisites": [],  # 缺失的前置知识
            "root_causes": [],  # 根本原因（最底层的缺失知识）
            "learning_suggestion": [],  # 学习建议
        }

        # 获取所有前置知识
        all_prereqs = self.get_prerequisites(target_knowledge, recursive=True)

        # 找出缺失的前置知识
        for prereq in all_prereqs:
            if prereq not in mastered_set:
                result["missing_prerequisites"].append({
                    "code": prereq,
                    "name": self.nodes[prereq].name,
                    "grade": self.nodes[prereq].grade,
                    "semester": self.nodes[prereq].semester,
                })

        # 找出根本原因（没有前置知识的缺失知识）
        for missing in result["missing_prerequisites"]:
            prereqs_of_missing = self.nodes[missing["code"]].prerequisites
            # 如果前置知识都已掌握或为空，则这是根本原因
            if all(p in mastered_set for p in prereqs_of_missing):
                result["root_causes"].append(missing)

        # 生成学习建议
        if result["root_causes"]:
            result["learning_suggestion"] = [
                f"建议先复习以下基础知识：",
            ]
            for rc in result["root_causes"]:
                result["learning_suggestion"].append(
                    f"  - {rc['name']}（{rc['grade']}{rc['semester']}）"
                )
            result["learning_suggestion"].append(
                f"掌握后再学习《{self.nodes[target_knowledge].name}》会更容易"
            )
        else:
            result["learning_suggestion"] = [
                "所有前置知识已掌握，建议：",
                "1. 多做基础练习题",
                "2. 理解概念本质",
                "3. 总结解题方法"
            ]

        return result

    def get_knowledge_chain(self, knowledge_code: str) -> List[Dict]:
        """
        获取知识点的完整知识链（从最基础到当前知识点）
        """
        if knowledge_code not in self.nodes:
            return []

        learning_path = self.get_learning_path(knowledge_code)
        chain = []

        for code in learning_path:
            if code in self.nodes:
                node = self.nodes[code]
                chain.append({
                    "code": code,
                    "name": node.name,
                    "grade": node.grade,
                    "semester": node.semester,
                    "importance": node.importance,
                    "difficulty": node.difficulty,
                    "category": node.category,
                })

        return chain

    def export_graph_json(self) -> str:
        """导出图谱为 JSON 格式（用于可视化）"""
        nodes = []
        edges = []

        for code, node in self.nodes.items():
            nodes.append({
                "id": code,
                "label": node.name[:20] + "..." if len(node.name) > 20 else node.name,
                "grade": node.grade,
                "semester": node.semester,
                "category": node.category,
                "importance": node.importance,
                "difficulty": node.difficulty,
            })

            # 添加依赖关系边
            for prereq in node.prerequisites:
                edges.append({
                    "source": prereq,
                    "target": code,
                    "type": "prerequisite"
                })

        return json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2)

    def get_recommended_learning_order(self, mastered_knowledge: List[str],
                                       grade_filter: Optional[str] = None) -> List[Dict]:
        """
        根据已掌握的知识，推荐下一步学习的内容

        Args:
            mastered_knowledge: 已掌握的知识点编码列表
            grade_filter: 年级过滤（如"二年级"）

        Returns:
            推荐学习的知识点列表
        """
        mastered_set = set(mastered_knowledge)
        recommendations = []

        for code, node in self.nodes.items():
            if grade_filter and node.grade != grade_filter:
                continue
            if code in mastered_set:
                continue

            # 检查所有前置知识是否已掌握
            prereqs = self.nodes[code].prerequisites
            if all(p in mastered_set for p in prereqs):
                recommendations.append({
                    "code": code,
                    "name": node.name,
                    "grade": node.grade,
                    "semester": node.semester,
                    "category": node.category,
                    "importance": node.importance,
                    "difficulty": node.difficulty,
                    "readiness": 100 if not prereqs else round(len([p for p in prereqs if p in mastered_set]) / len(prereqs) * 100)
                })

        # 按重要性和难度排序（优先学重要且不太难的）
        recommendations.sort(key=lambda x: (-x["importance"], x["difficulty"]))

        return recommendations


def main():
    """测试"""
    graph = KnowledgeGraph()

    # 测试获取前置知识
    print("G2D06 (有余数的除法) 的前置知识:")
    prereqs = graph.get_prerequisites("G2D06", recursive=True)
    for p in prereqs:
        print(f"  - {p}: {graph.nodes[p].name}")

    # 测试学习路径
    print("\n学习 G3D05 (面积) 的推荐路径:")
    path = graph.get_learning_path("G3D05")
    for i, code in enumerate(path, 1):
        print(f"  {i}. {graph.nodes[code].name}")

    # 测试影响分析
    print("\n薄弱知识点 G1U05 的影响:")
    impact = graph.analyze_weak_point_impact(["G1U05"])
    print(f"  直接影响：{impact['direct_impact']}")
    print(f"  风险等级：{impact['risk_level']}")

    # 测试根本原因分析
    print("\n学习 G3D05 困难的根本原因分析:")
    root_cause = graph.find_root_cause("G3D05", ["G1U01", "G1U02", "G1U03"])
    print(f"  缺失的前置知识：{root_cause['missing_prerequisites']}")
    print(f"  根本原因：{root_cause['root_causes']}")
    print(f"  学习建议：{root_cause['learning_suggestion']}")


if __name__ == "__main__":
    main()
