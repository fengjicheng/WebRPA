# -*- coding: utf-8 -*-
"""子工作流执行监控事件（subflow:*）的单元测试。

「运行其它工作流」过去是后端静默跑完，父画布上只有一个节点在转。现在后端会推送
subflow:started / node_start / node_complete / log / completed 五类事件，
前端据此独立开一个只读画布窗口显示子工作流执行到哪一步。

这里锁住三件容易回退的事：
1. started 载荷是**精简**图结构——不能把节点 data 原样带上，否则大段脚本 / base64 图片
   会让一条 socket 消息顶到几 MB，把实时日志通道挤住。
2. 子工作流执行期**抛异常**时也必须补发 completed，否则监控窗口会永远停在「运行中」。
3. 推送失败绝不能影响子工作流执行本身（监控是旁路能力）。
"""
import json
from types import SimpleNamespace

import pytest

from app.executors import workflow_chain as wc
from app.executors.base import ExecutionContext
from app.models.workflow import Workflow, WorkflowEdge, WorkflowNode

pytestmark = pytest.mark.unit


@pytest.fixture()
def emitted(monkeypatch):
    """拦截 safe_emit，按顺序记录 (事件名, 载荷)。

    _emit_subflow 是在调用时才 from app.api.workflows import safe_emit，
    所以替换模块属性即可生效，无需改动被测代码。
    """
    import app.api.workflows as workflows_api

    records: list[tuple[str, dict]] = []

    async def fake_safe_emit(event, payload):
        records.append((event, payload))

    monkeypatch.setattr(workflows_api, "safe_emit", fake_safe_emit)
    return records


def _sub_workflow_file(tmp_path):
    """落一个真实的子工作流文件到磁盘（用绝对路径调用，绕开工作流文件夹配置）。

    节点 data 里刻意塞一段超长脚本，用于验证 started 载荷不会把它带出去。
    """
    huge_script = "x" * 5000
    content = {
        "id": "sub",
        "name": "子流程A",
        "nodes": [
            {
                "id": "n1",
                "type": "moduleNode",
                "position": {"x": 10, "y": 20},
                "data": {"moduleType": "log", "label": "打印", "code": huge_script},
            },
            {
                "id": "n2",
                "type": "moduleNode",
                "position": {"x": 10, "y": 140},
                "data": {"moduleType": "wait", "label": "等待"},
            },
        ],
        "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
    }
    path = tmp_path / "sub_flow.json"
    path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    return path, huge_script


class _FakeExecutor:
    """假子工作流执行器。

    只替换「跑图」这一件事，context 用真实的 ExecutionContext，
    这样变量传递 / 回收走的是真实实现，不会被替身掩盖。
    """

    def __init__(self, workflow=None, headless=False, browser_config=None,
                 on_node_start=None, on_node_complete=None):
        self.workflow = workflow
        self.context = ExecutionContext()
        self.on_node_start = on_node_start
        self.on_node_complete = on_node_complete
        self.on_log = None
        self.executed_nodes = 2
        self.failed_nodes = 0
        self.raise_on_execute: BaseException | None = None

    async def execute(self):
        if self.raise_on_execute is not None:
            raise self.raise_on_execute
        self.context.set_variable("子流程产出", 42)
        return SimpleNamespace(status="completed", failed_nodes=0, error_message=None)


class _ExecutorSpy:
    """假 WorkflowExecutor 的创建入口，兼作用例侧的配置口。

    用例可在调用被测代码前设置 raise_on_execute，让子工作流执行期抛异常。
    """

    def __init__(self):
        self.instances: list[_FakeExecutor] = []
        self.raise_on_execute: BaseException | None = None

    def __call__(self, **kwargs):
        inst = _FakeExecutor(**kwargs)
        inst.raise_on_execute = self.raise_on_execute
        self.instances.append(inst)
        return inst


@pytest.fixture()
def fake_executor(monkeypatch):
    """把 WorkflowExecutor 换成假实现，并把创建出的实例暴露给用例。"""
    import app.services.workflow_executor as we_mod

    spy = _ExecutorSpy()
    monkeypatch.setattr(we_mod, "WorkflowExecutor", spy)
    return spy


async def _run(path, context=None):
    executor = wc.RunWorkflowFileExecutor()
    ctx = context or ExecutionContext()
    return await executor.execute({"workflowFile": str(path)}, ctx)


def test_serialize_graph_only_carries_render_fields():
    """精简载荷：只带 id/moduleType/label/position/尺寸，节点 data 一律不带"""
    wf = Workflow(
        id="w", name="w",
        nodes=[WorkflowNode(
            id="n1", type="moduleNode", position={"x": 1.5, "y": 2.5},
            data={"moduleType": "log", "label": "打印", "code": "y" * 3000},
        )],
        edges=[WorkflowEdge(id="e1", source="n1", target="n1")],
    )
    payload = wc._serialize_graph(wf)

    assert set(payload) == {"nodes", "edges"}
    node = payload["nodes"][0]
    assert set(node) == {"id", "moduleType", "label", "position", "width", "height"}
    assert node["position"] == {"x": 1.5, "y": 2.5}
    # 整份载荷里不能出现节点 data 的任何痕迹
    assert "y" * 3000 not in json.dumps(payload, ensure_ascii=False)
    assert set(payload["edges"][0]) == {"id", "source", "target", "sourceHandle", "targetHandle"}


async def test_started_and_completed_emitted_once_on_success(tmp_path, emitted, fake_executor):
    """正常执行：started 在 completed 之前，各恰好一次，且同一个 subflowId"""
    path, huge_script = _sub_workflow_file(tmp_path)

    result = await _run(path)
    assert result.success is True

    events = [e for e, _ in emitted]
    assert events.count("subflow:started") == 1
    assert events.count("subflow:completed") == 1
    assert events.index("subflow:started") < events.index("subflow:completed")

    started = dict(emitted[events.index("subflow:started")][1])
    completed = dict(emitted[events.index("subflow:completed")][1])
    assert started["subflowId"] == completed["subflowId"]
    assert started["subflowId"].startswith("sub_")
    assert started["name"] == "子流程A"
    assert started["file"] == path.name
    assert started["depth"] == 0
    assert [n["id"] for n in started["nodes"]] == ["n1", "n2"]
    # 大段脚本不得随 started 出去
    assert huge_script not in json.dumps(started, ensure_ascii=False)

    assert completed["success"] is True
    assert completed["status"] == "completed"
    assert completed["executedNodes"] == 2
    assert completed["failedNodes"] == 0


async def test_completed_emitted_when_execution_raises(tmp_path, emitted, fake_executor):
    """执行期抛异常也必须补发 completed，否则监控窗口会永远停在「运行中」"""
    path, _ = _sub_workflow_file(tmp_path)
    fake_executor.raise_on_execute = RuntimeError("浏览器启动失败")

    result = await _run(path)

    # 模块本身按失败返回（异常信息回流到父流程）
    assert result.success is False
    assert "浏览器启动失败" in (result.error or "")

    events = [e for e, _ in emitted]
    assert events.count("subflow:started") == 1
    assert events.count("subflow:completed") == 1, "异常出口漏发 completed，监控窗口会一直转圈"

    completed = dict(emitted[events.index("subflow:completed")][1])
    assert completed["success"] is False
    assert completed["status"] == "failed"
    assert "浏览器启动失败" in str(completed["error"])


async def test_node_callbacks_payload(tmp_path, emitted, fake_executor):
    """节点回调载荷：node_start 带 subflowId/nodeId；node_complete 另带 success/duration/error"""
    path, _ = _sub_workflow_file(tmp_path)
    await _run(path)

    inst = fake_executor.instances[0]
    await inst.on_node_start("n1")
    await inst.on_node_complete("n1", SimpleNamespace(success=False, duration=1.25, error="点击失败"))

    start = next(p for e, p in emitted if e == "subflow:node_start")
    assert set(start) == {"subflowId", "nodeId"}
    assert start["nodeId"] == "n1"

    done = next(p for e, p in emitted if e == "subflow:node_complete")
    assert set(done) == {"subflowId", "nodeId", "success", "duration", "error"}
    assert done["success"] is False
    assert done["duration"] == 1.25
    assert done["error"] == "点击失败"
    assert done["subflowId"] == start["subflowId"]


async def test_log_forwarded_to_parent_and_monitor(tmp_path, emitted, fake_executor):
    """子工作流日志既转发到父上下文（带子流程名前缀），也推给监控窗口"""
    path, _ = _sub_workflow_file(tmp_path)
    parent = ExecutionContext()
    await _run(path, parent)

    inst = fake_executor.instances[0]
    await inst.on_log(SimpleNamespace(
        level=SimpleNamespace(value="warning"), message="元素未找到", node_id="n2", duration=0.5,
    ))

    parent_logs = parent.get_logs()
    assert any(log["message"] == "[子流程A] 元素未找到" for log in parent_logs)

    log_payload = next(p for e, p in emitted if e == "subflow:log")
    assert set(log_payload) == {"subflowId", "level", "message", "nodeId"}
    assert log_payload["level"] == "warning"
    assert log_payload["message"] == "元素未找到"
    assert log_payload["nodeId"] == "n2"


async def test_emit_failure_does_not_break_execution(tmp_path, monkeypatch, fake_executor):
    """监控是旁路能力：safe_emit 恒抛异常时子工作流仍要正常跑完"""
    import app.api.workflows as workflows_api

    async def boom(event, payload):
        raise RuntimeError("socket 断开")

    monkeypatch.setattr(workflows_api, "safe_emit", boom)
    path, _ = _sub_workflow_file(tmp_path)

    parent = ExecutionContext()
    result = await _run(path, parent)

    assert result.success is True
    # 变量回收链路未被推送异常打断
    assert parent.variables.get("子流程产出") == 42
