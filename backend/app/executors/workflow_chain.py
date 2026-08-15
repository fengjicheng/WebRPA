"""工作流串联执行器 —— 在一条工作流里调用另一条本地工作流

解决的痛点：
「子流程」只能调用同一张画布内的分组，无法调用另一个工作流文件；
过去用户想实现「工作流1 跑完自动跑工作流2」只能靠计划任务/Webhook 绕，很不直观。

本模块提供 run_workflow_file：
- 直接按文件名调用「工作流保存文件夹」（尊重用户自定义目录 / WebDAV 兜底为本地）里的另一条工作流
- 支持同步等待子工作流跑完（默认）或异步触发后立刻继续
- 支持把当前工作流的变量传给子工作流，并把子工作流的变量回收到当前上下文
- 内置循环调用检测与嵌套深度上限，避免 A→B→A 递归把进程跑爆
- 浏览器配置 / 无头模式默认继承父工作流，保证串联时用同一套浏览器环境
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.executors.base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)

# 嵌套调用深度上限（父→子→孙…），超过即判定为异常递归
MAX_CHAIN_DEPTH = 16


def _resolve_workflow_path(filename: str) -> Path | None:
    """在「当前活动工作流文件夹」中定位工作流文件。

    兼容用户填写：带/不带 .json 后缀、填工作流显示名、填绝对路径。
    """
    name = (filename or "").strip().strip('"')
    if not name:
        return None

    # 1) 绝对路径直接用
    p = Path(name)
    if p.is_absolute():
        if p.is_file():
            return p
        if p.with_suffix(".json").is_file():
            return p.with_suffix(".json")
        return None

    # 2) 活动工作流文件夹（尊重全局配置里的自定义目录）
    try:
        from app.services import workflow_folder as _wf_folder
        folder = Path(_wf_folder.get_active_folder())
    except Exception:
        folder = Path(__file__).parent.parent.parent.parent / "workflows"

    candidates = [name] if name.lower().endswith(".json") else [f"{name}.json", name]
    for cand in candidates:
        target = folder / cand
        # 防路径穿越：必须落在工作流文件夹内
        try:
            target.resolve().relative_to(folder.resolve())
        except Exception:
            continue
        if target.is_file():
            return target

    # 3) 按工作流显示名（JSON 内部 name 字段）兜底匹配
    try:
        for f in folder.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            if str(data.get("name", "")).strip() == name:
                return f
    except Exception:
        pass
    return None


def _build_workflow_object(content: dict, fallback_name: str):
    """把工作流 JSON 还原为后端 Workflow 模型对象。"""
    from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge, Position

    nodes = []
    for n in content.get("nodes", []) or []:
        pos = n.get("position") or {}
        nodes.append(WorkflowNode(
            id=n.get("id", ""),
            # 前端保存的是 moduleType 在 data 里、type 为 moduleNode 的形式，
            # 也可能已是后端格式（type 即 module_type），两种都兼容。
            type=(n.get("data") or {}).get("moduleType") or n.get("type") or "",
            position=Position(x=float(pos.get("x", 0) or 0), y=float(pos.get("y", 0) or 0)),
            data=n.get("data") or {},
            width=n.get("width"),
            height=n.get("height"),
            style=n.get("style"),
        ))
    edges = []
    for e in content.get("edges", []) or []:
        edges.append(WorkflowEdge(
            id=e.get("id", ""),
            source=e.get("source", ""),
            target=e.get("target", ""),
            sourceHandle=e.get("sourceHandle"),
            targetHandle=e.get("targetHandle"),
        ))
    return Workflow(
        id=str(content.get("id") or f"chain_{fallback_name}"),
        name=str(content.get("name") or fallback_name),
        nodes=nodes,
        edges=edges,
    )


async def _emit_subflow(event: str, payload: dict) -> None:
    """向前端推送子工作流监控事件（异常隔离：推送失败绝不影响子工作流执行）。

    复用 workflows.py 里的 safe_emit，保证与手动运行路径同一套 Socket 实例与容错策略。
    """
    try:
        from app.api.workflows import safe_emit
        await safe_emit(event, payload)
    except Exception:
        # 监控是旁路能力，推送失败不能让工作流跟着失败
        pass


def _serialize_graph(workflow) -> dict:
    """把子工作流的图结构精简成前端画布够用的最小载荷。

    只带渲染与高亮必需的字段：节点 id / 模块类型 / 位置 / 标签 / 尺寸，以及连线端点。
    不带完整 data（里面可能有大段脚本、表格数据、base64 图片），否则一条 socket 消息
    就能顶到几 MB，把实时日志通道挤住。
    """
    nodes = []
    for n in workflow.nodes:
        data = n.data or {}
        module_type = data.get("moduleType") or n.type or ""
        nodes.append({
            "id": n.id,
            "moduleType": module_type,
            "label": data.get("label") or module_type,
            "position": {
                "x": float(getattr(n.position, "x", 0) or 0),
                "y": float(getattr(n.position, "y", 0) or 0),
            },
            # 尺寸是可选字段，不同来源的工作流不一定带；缺失时交给前端用默认尺寸渲染
            "width": getattr(n, "width", None),
            "height": getattr(n, "height", None),
        })
    edges = [{
        "id": e.id,
        "source": e.source,
        "target": e.target,
        "sourceHandle": e.sourceHandle,
        "targetHandle": e.targetHandle,
    } for e in workflow.edges]
    return {"nodes": nodes, "edges": edges}


def _make_subflow_callbacks(subflow_id: str) -> dict:
    """产出子工作流的节点事件回调，供监控窗口做「运行到哪个模块就高亮哪个」。

    只挂节点开始/结束两个回调：日志由调用方单独接（还要同时转发到父流程），
    变量更新不推（与手动运行路径一致，密集循环下会挤占通道）。
    """
    async def on_node_start(node_id: str) -> None:
        await _emit_subflow("subflow:node_start", {
            "subflowId": subflow_id,
            "nodeId": node_id,
        })

    async def on_node_complete(node_id: str, result) -> None:
        await _emit_subflow("subflow:node_complete", {
            "subflowId": subflow_id,
            "nodeId": node_id,
            "success": bool(getattr(result, "success", False)),
            "duration": getattr(result, "duration", None),
            "error": getattr(result, "error", None),
        })

    return {"on_node_start": on_node_start, "on_node_complete": on_node_complete}


@register_executor
class RunWorkflowFileExecutor(ModuleExecutor):
    """运行其它工作流（把多条工作流串成一条业务链）"""

    @property
    def module_type(self) -> str:
        return "run_workflow_file"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import asyncio

        filename = context.resolve_value(config.get("workflowFile", "") or config.get("workflow", ""))
        wait_complete = config.get("waitComplete", True)
        if isinstance(wait_complete, str):
            wait_complete = wait_complete.strip().lower() not in ("false", "0", "no", "")
        pass_variables = config.get("passVariables", True)
        if isinstance(pass_variables, str):
            pass_variables = pass_variables.strip().lower() not in ("false", "0", "no", "")
        collect_variables = config.get("collectVariables", True)
        if isinstance(collect_variables, str):
            collect_variables = collect_variables.strip().lower() not in ("false", "0", "no", "")
        result_variable = (config.get("resultVariable") or "").strip()
        stop_on_fail = config.get("stopOnFail", True)
        if isinstance(stop_on_fail, str):
            stop_on_fail = stop_on_fail.strip().lower() not in ("false", "0", "no", "")

        if not filename:
            return ModuleResult(success=False, error="未指定要运行的工作流（workflowFile 为空）")

        wf_path = _resolve_workflow_path(str(filename))
        if not wf_path:
            return ModuleResult(
                success=False,
                error=(
                    f"找不到工作流「{filename}」。请确认它存在于当前「工作流保存文件夹」中"
                    "（全局配置 → 存储 → 工作流保存文件夹），文件名可带或不带 .json。"
                ),
            )

        try:
            content = json.loads(wf_path.read_text(encoding="utf-8"))
        except Exception as e:
            return ModuleResult(success=False, error=f"读取工作流文件失败：{e}")
        if not isinstance(content, dict) or not content.get("nodes"):
            return ModuleResult(success=False, error=f"工作流「{wf_path.name}」内容为空或格式不正确")

        # ---- 循环调用与深度保护（挂在 context 上，跨父子执行器共享）----
        chain_stack: list[str] = list(getattr(context, "_workflow_chain_stack", []) or [])
        key = str(wf_path.resolve()).lower()
        if key in chain_stack:
            chain_desc = " -> ".join(Path(p).name for p in chain_stack)
            return ModuleResult(
                success=False,
                error=f"检测到工作流循环调用：{chain_desc} -> {wf_path.name}。请检查工作流之间的相互调用关系。",
            )
        if len(chain_stack) >= MAX_CHAIN_DEPTH:
            return ModuleResult(
                success=False,
                error=f"工作流嵌套调用层数过深（>{MAX_CHAIN_DEPTH}），已终止以避免无限递归。",
            )

        sub_workflow = _build_workflow_object(content, wf_path.stem)

        # 子工作流沿用父工作流的运行环境（同一浏览器 / 同一无头设置）
        from app.services.workflow_executor import WorkflowExecutor

        # 子工作流监控窗口用的唯一标识：同一父流程里可能并发/嵌套多个子工作流，
        # 前端靠它区分是哪一个窗口在更新。带上父节点 id，便于窗口标题回指来源模块。
        subflow_id = f"sub_{uuid4().hex[:12]}"
        parent_node_id = getattr(context, "_current_node_id", None)

        async def _run_sub() -> dict:
            executor = WorkflowExecutor(
                workflow=sub_workflow,
                headless=getattr(context, "headless", False),
                browser_config=getattr(context, "browser_config", None),
                **_make_subflow_callbacks(subflow_id),
            )
            # 传播调用链，供子工作流内再次调用时做循环检测
            setattr(executor.context, "_workflow_chain_stack", chain_stack + [key])
            # 变量传递：把父工作流当前变量灌入子工作流
            if pass_variables:
                try:
                    for k, v in (context.variables or {}).items():
                        executor.context.set_variable(k, v)
                except Exception:
                    pass
            # 子工作流内的日志：既转发到父工作流日志（统一查看），也推给子流程监控窗口
            try:
                parent_ctx = context

                async def _forward_log(entry) -> None:
                    try:
                        level = getattr(getattr(entry, "level", None), "value", None) or "info"
                        msg = getattr(entry, "message", "")
                        parent_ctx.add_log(
                            level=str(level),
                            message=f"[{sub_workflow.name}] {msg}",
                            node_id=None,
                            duration=getattr(entry, "duration", None),
                        )
                    except Exception:
                        pass
                    await _emit_subflow(
                        "subflow:log",
                        {
                            "subflowId": subflow_id,
                            "level": str(getattr(getattr(entry, "level", None), "value", None) or "info"),
                            "message": getattr(entry, "message", ""),
                            "nodeId": getattr(entry, "node_id", None),
                        },
                    )

                executor.on_log = _forward_log
            except Exception:
                pass

            # 告知前端开一个监控窗口，并把子工作流的图结构一并送过去
            # （父画布上没有子工作流的节点，前端只能靠这份结构把它画出来）
            await _emit_subflow("subflow:started", {
                "subflowId": subflow_id,
                "name": sub_workflow.name,
                "file": wf_path.name,
                "parentNodeId": parent_node_id,
                "depth": len(chain_stack),
                **_serialize_graph(sub_workflow),
            })

            try:
                exec_result = await executor.execute()
            except BaseException as exec_exc:
                # 执行期抛异常时必须补发结束事件，否则监控窗口会一直停在「运行中」，
                # 用户以为还在跑。补发后原样抛出，交给外层生成模块错误信息。
                await _emit_subflow("subflow:completed", {
                    "subflowId": subflow_id,
                    "name": sub_workflow.name,
                    "success": False,
                    "status": "failed",
                    "executedNodes": int(getattr(executor, "executed_nodes", 0) or 0),
                    "failedNodes": int(getattr(executor, "failed_nodes", 0) or 0),
                    "error": str(exec_exc) or exec_exc.__class__.__name__,
                })
                raise

            # ExecutionResult 用 status/error_message 表达结果（不是 success/error）
            status = getattr(exec_result, "status", None)
            status_str = getattr(status, "value", None) or str(status or "")
            ok = status_str == "completed" and int(getattr(exec_result, "failed_nodes", 0) or 0) == 0
            err = getattr(exec_result, "error_message", None) or getattr(executor, "_first_error_message", None)
            sub_vars = {}
            try:
                sub_vars = dict(executor.context.variables or {})
            except Exception:
                sub_vars = {}

            await _emit_subflow("subflow:completed", {
                "subflowId": subflow_id,
                "name": sub_workflow.name,
                "success": ok,
                "status": status_str,
                "executedNodes": int(getattr(executor, "executed_nodes", 0) or 0),
                "failedNodes": int(getattr(executor, "failed_nodes", 0) or 0),
                "error": err,
            })

            return {"success": ok, "error": err, "variables": sub_vars,
                    "executed_nodes": getattr(executor, "executed_nodes", 0),
                    "failed_nodes": getattr(executor, "failed_nodes", 0)}

        # ---- 异步触发：不等子工作流结束，立刻继续父流程 ----
        if not wait_complete:
            try:
                asyncio.create_task(_run_sub())
            except Exception as e:
                return ModuleResult(success=False, error=f"发起工作流「{sub_workflow.name}」失败：{e}")
            return ModuleResult(
                success=True,
                message=f"已异步发起工作流「{sub_workflow.name}」（不等待其完成）",
                data={"workflow": sub_workflow.name, "waited": False},
            )

        # ---- 同步等待：跑完再继续（默认，最符合「1 跑完自动跑 2」的直觉）----
        try:
            res = await _run_sub()
        except Exception as e:
            import traceback
            return ModuleResult(
                success=False,
                error=f"运行工作流「{sub_workflow.name}」异常：{e}\n{traceback.format_exc()}",
            )

        # 回收子工作流变量（子里新产生/更新的变量带回父上下文）
        if collect_variables:
            try:
                for k, v in (res.get("variables") or {}).items():
                    context.set_variable(k, v)
            except Exception:
                pass

        summary = {
            "workflow": sub_workflow.name,
            "file": wf_path.name,
            "success": res.get("success"),
            "executed_nodes": res.get("executed_nodes"),
            "failed_nodes": res.get("failed_nodes"),
            "error": res.get("error"),
        }
        if result_variable:
            context.set_variable(result_variable, summary)

        if res.get("success"):
            return ModuleResult(
                success=True,
                message=(
                    f"工作流「{sub_workflow.name}」执行完成"
                    f"（{res.get('executed_nodes', 0)} 个模块）"
                ),
                data=summary,
            )

        err_text = res.get("error") or "子工作流执行失败"
        if stop_on_fail:
            return ModuleResult(
                success=False,
                error=f"工作流「{sub_workflow.name}」执行失败：{err_text}",
                data=summary,
            )
        # 不因子工作流失败而中断父流程（用户显式选择继续）
        return ModuleResult(
            success=True,
            message=f"工作流「{sub_workflow.name}」执行失败但已按配置继续：{err_text}",
            data=summary,
        )
