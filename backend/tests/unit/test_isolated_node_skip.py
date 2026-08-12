# -*- coding: utf-8 -*-
"""孤立节点不参与执行的回归测试。

背景（一次真实故障）：
起始节点原先判定为「所有没有入边的节点」，把既无入边也无出边的孤立节点也算进去。
这类节点多是拖进画布忘记连线、或删连线后遗留的废弃节点，一旦被当成起始节点，
就会与真正的起始节点**并行**执行，抢在变量赋值之前跑。用户遇到的表现是：
流程本该「设置变量 → 点击元素」，孤立的点击节点提前执行，此时 {菜单产品} 还没值，
未解析的字面量 "{菜单产品}" 被当成 CSS 选择器，报 Unsupported token "{"，
而且因为是竞态，同一个工作流时好时坏。

同时必须保住的兼容行为：整图没有任何连线时（单节点工作流等）节点仍要执行。
"""
import pytest

from app.models.workflow import Workflow, WorkflowEdge, WorkflowNode
from app.services.workflow_parser import WorkflowParser


def _wf(node_ids, edges):
    return Workflow(
        id="w", name="w",
        nodes=[
            WorkflowNode(id=n, type="set_variable", position={"x": 0, "y": 0}, data={})
            for n in node_ids
        ],
        edges=[
            WorkflowEdge(id=f"e{i}", source=s, target=t)
            for i, (s, t) in enumerate(edges)
        ],
    )


@pytest.fixture()
def parser():
    return WorkflowParser()


def test_isolated_node_is_not_a_start_node(parser):
    """有连线的流程里，孤立节点不得作为起始节点（否则会与真正起点并行、造成变量竞态）"""
    graph = parser.parse(_wf(["a", "b", "orphan"], [("a", "b")]))
    assert graph.start_nodes == ["a"]
    assert graph.isolated_nodes == ["orphan"]


def test_single_node_workflow_still_runs(parser):
    """整图无连线时保持原行为：单节点工作流必须照常执行"""
    graph = parser.parse(_wf(["only"], []))
    assert graph.start_nodes == ["only"]
    assert graph.isolated_nodes == []


def test_multiple_disconnected_branches_all_start(parser):
    """两条互不相连但各自有连线的流程，起点都要保留"""
    graph = parser.parse(_wf(["a", "b", "c", "d"], [("a", "b"), ("c", "d")]))
    assert sorted(graph.start_nodes) == ["a", "c"]
    assert graph.isolated_nodes == []


def test_all_nodes_isolated_keeps_running(parser):
    """整图全是孤立节点且无任何连线：保持原行为，全部执行（不能把合法用法禁掉）"""
    graph = parser.parse(_wf(["x", "y", "z"], []))
    assert sorted(graph.start_nodes) == ["x", "y", "z"]
    assert graph.isolated_nodes == []


def test_isolated_node_excluded_from_execution_order(parser):
    """孤立节点既不是起点，也不该出现在任何节点的后继里"""
    graph = parser.parse(_wf(["a", "b", "orphan"], [("a", "b")]))
    reachable = set(graph.start_nodes)
    for nid in list(reachable):
        reachable.update(graph.get_next_nodes(nid))
    assert "orphan" not in reachable
