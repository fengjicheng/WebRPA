"""WebRPA小助手 - Skills 工具系统

把 WebRPA 的核心能力包装为 OpenAI Function Calling 形式的工具，
让 AI 助手可以像 Hermes Agent 一样自主操作 WebRPA。
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Awaitable

from app.services.ai_assistant_knowledge import (
    MODULE_CATEGORIES,
    find_module_description,
    get_all_known_module_types,
)


# ---------- Skill 定义 ----------

class Skill:
    """一个 Skill 工具的定义"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., Awaitable[Any]],
        *,
        requires_approval: bool = False,
    ) -> None:
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.requires_approval = requires_approval

    def to_openai_tool(self) -> dict[str, Any]:
        """导出为 OpenAI tools 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class SkillRegistry:
    """Skill 注册表"""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def to_openai_tools(self) -> list[dict[str, Any]]:
        return [s.to_openai_tool() for s in self._skills.values()]

    def names(self) -> list[str]:
        return list(self._skills.keys())


registry = SkillRegistry()


# ---------- 后端数据访问层（Skill 内部用） ----------

def _get_workflow_folder() -> Path:
    """工作流默认存储目录（与 local_workflows.py 的逻辑保持一致）"""
    project_root = Path(__file__).parent.parent.parent.parent
    folder = project_root / "workflows"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _get_data_folder() -> Path:
    """后端数据目录"""
    folder = Path("backend/data")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


# ---------- Skills 实现 ----------

# === 1. 模块信息查询类 ===

async def skill_list_module_categories(**_: Any) -> dict[str, Any]:
    """列出 WebRPA 内置模块的所有分类"""
    return {
        "categories": list(MODULE_CATEGORIES.keys()),
        "total_modules": sum(len(m) for m in MODULE_CATEGORIES.values()),
    }


async def skill_list_modules_in_category(category: str, **_: Any) -> dict[str, Any]:
    """列出某个分类下的所有模块"""
    if category not in MODULE_CATEGORIES:
        return {
            "error": f"未知分类: {category}",
            "available_categories": list(MODULE_CATEGORIES.keys()),
        }
    return {
        "category": category,
        "modules": [
            {"type": mtype, "description": desc}
            for mtype, desc in MODULE_CATEGORIES[category].items()
        ],
    }


async def skill_describe_module(module_type: str, **_: Any) -> dict[str, Any]:
    """获取某个模块的描述"""
    desc = find_module_description(module_type)

    # 检查执行器是否真实注册
    is_registered = False
    try:
        from app.executors.base import registry as exec_registry
        is_registered = module_type in exec_registry.get_all_types()
    except Exception:
        pass

    if desc is None and not is_registered:
        return {
            "error": f"未找到模块 {module_type}，它可能不存在或拼写错误",
        }
    return {
        "type": module_type,
        "description": desc or "（暂无文档）",
        "registered": is_registered,
    }


async def skill_search_modules(keyword: str, **_: Any) -> dict[str, Any]:
    """按关键词搜索模块"""
    keyword = keyword.lower().strip()
    matches: list[dict[str, str]] = []
    for cat, modules in MODULE_CATEGORIES.items():
        for mtype, desc in modules.items():
            if keyword in mtype.lower() or keyword in desc.lower():
                matches.append({"category": cat, "type": mtype, "description": desc})
    return {"keyword": keyword, "count": len(matches), "matches": matches[:30]}


# === 2. 工作流文件管理类 ===

async def skill_list_workflows(**_: Any) -> dict[str, Any]:
    """列出本地保存的所有工作流文件"""
    folder = _get_workflow_folder()
    items: list[dict[str, Any]] = []
    for fp in sorted(folder.glob("*.json")):
        try:
            stat = fp.stat()
            items.append({
                "filename": fp.name,
                "name": fp.stem,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        except Exception as e:
            items.append({"filename": fp.name, "error": str(e)})
    return {"folder": str(folder), "count": len(items), "workflows": items}


async def skill_read_workflow(filename: str, **_: Any) -> dict[str, Any]:
    """读取一个工作流文件的内容"""
    folder = _get_workflow_folder()
    if not filename.endswith(".json"):
        filename = filename + ".json"
    fp = folder / filename
    # 防路径穿越
    try:
        fp.resolve().relative_to(folder.resolve())
    except ValueError:
        return {"error": "非法的文件名"}
    if not fp.exists():
        return {"error": f"文件不存在: {filename}"}
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"读取失败: {e}"}
    # 给个轻量摘要（节点过多时不返回完整内容）
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    summary = {
        "name": data.get("name", fp.stem),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_types": sorted({n.get("type") for n in nodes if n.get("type")}),
    }
    if len(nodes) <= 30:
        summary["nodes"] = nodes
        summary["edges"] = edges
    return summary


async def skill_save_workflow_file(
    filename: str, nodes: list, edges: list, name: str | None = None, **_: Any
) -> dict[str, Any]:
    """把工作流保存到本地文件"""
    folder = _get_workflow_folder()
    if not filename.endswith(".json"):
        filename = filename + ".json"
    fp = folder / filename
    try:
        fp.resolve().relative_to(folder.resolve())
    except ValueError:
        return {"error": "非法的文件名"}

    payload = {
        "name": name or fp.stem,
        "nodes": nodes,
        "edges": edges,
        "saved_at": datetime.now().isoformat(),
    }
    try:
        fp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        return {"error": f"保存失败: {e}"}
    return {"success": True, "path": str(fp), "node_count": len(nodes)}


async def skill_delete_workflow(filename: str, **_: Any) -> dict[str, Any]:
    """删除一个本地工作流文件（高危操作，需用户批准）"""
    folder = _get_workflow_folder()
    if not filename.endswith(".json"):
        filename = filename + ".json"
    fp = folder / filename
    try:
        fp.resolve().relative_to(folder.resolve())
    except ValueError:
        return {"error": "非法的文件名"}
    if not fp.exists():
        return {"error": "文件不存在"}
    try:
        fp.unlink()
    except Exception as e:
        return {"error": f"删除失败: {e}"}
    return {"success": True, "deleted": filename}


# === 3. 节点/工作流构造类（生成节点 JSON 让前端应用） ===

def _make_node_id() -> str:
    return uuid.uuid4().hex[:10]


async def skill_build_node(
    module_type: str,
    config: dict | None = None,
    label: str | None = None,
    position: dict | None = None,
    **_: Any,
) -> dict[str, Any]:
    """构造一个节点 JSON（前端可直接 addNode 进画布）"""
    node = {
        "id": _make_node_id(),
        "type": module_type,
        "position": position or {"x": 200.0, "y": 200.0},
        "data": {
            "label": label or module_type,
            "config": config or {},
        },
    }
    return {"node": node}


async def skill_build_workflow(
    name: str,
    steps: list[dict],
    **_: Any,
) -> dict[str, Any]:
    """根据顺序步骤生成完整工作流（节点 + 边）

    steps: 形如 [{"type": "open_page", "label": "打开网页", "config": {"url": "..."}}, ...]
    会按顺序依次连接相邻节点。
    """
    if not isinstance(steps, list) or not steps:
        return {"error": "steps 不能为空"}

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for idx, step in enumerate(steps):
        mtype = step.get("type")
        if not mtype:
            return {"error": f"第 {idx} 步缺少 type 字段"}
        node = {
            "id": _make_node_id(),
            "type": mtype,
            "position": {"x": 200.0 + (idx % 4) * 280.0, "y": 200.0 + (idx // 4) * 200.0},
            "data": {
                "label": step.get("label") or mtype,
                "config": step.get("config") or {},
            },
        }
        nodes.append(node)
        if idx > 0:
            edges.append({
                "id": f"e-{nodes[idx - 1]['id']}-{node['id']}",
                "source": nodes[idx - 1]["id"],
                "target": node["id"],
            })

    return {
        "name": name,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


# === 4. 系统状态查询类 ===

async def skill_list_executors(**_: Any) -> dict[str, Any]:
    """列出所有已注册的执行器（实际能跑的模块类型）"""
    try:
        from app.executors.base import registry as exec_registry
        types = sorted(exec_registry.get_all_types())
        return {"count": len(types), "types": types}
    except Exception as e:
        return {"error": str(e)}


async def skill_list_custom_modules(**_: Any) -> dict[str, Any]:
    """列出所有用户创建的自定义模块"""
    folder = _get_data_folder() / "custom_modules"
    if not folder.exists():
        return {"count": 0, "modules": []}
    items: list[dict[str, Any]] = []
    for fp in sorted(folder.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            items.append({
                "id": data.get("id"),
                "name": data.get("name"),
                "description": data.get("description", ""),
                "category": data.get("category", ""),
            })
        except Exception:
            pass
    return {"count": len(items), "modules": items}


async def skill_list_scheduled_tasks(**_: Any) -> dict[str, Any]:
    """列出所有计划任务"""
    fp = _get_data_folder() / "scheduled_tasks.json"
    if not fp.exists():
        return {"count": 0, "tasks": []}
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        # 数据结构兼容
        if isinstance(data, list):
            tasks = data
        elif isinstance(data, dict):
            tasks = data.get("tasks", [])
        else:
            tasks = []
        return {"count": len(tasks), "tasks": tasks}
    except Exception as e:
        return {"error": str(e)}


async def skill_get_recent_logs(workflow_id: str | None = None, limit: int = 50, **_: Any) -> dict[str, Any]:
    """获取最近的工作流执行日志（如果有的话）"""
    try:
        from app.api.workflows import execution_results, variable_tracking_store
    except Exception as e:
        return {"error": f"无法访问日志: {e}"}

    if workflow_id and workflow_id in execution_results:
        result = execution_results[workflow_id]
        return {
            "workflow_id": workflow_id,
            "status": result.status.value if hasattr(result.status, "value") else str(result.status),
            "executed_nodes": result.executed_nodes,
            "failed_nodes": result.failed_nodes,
            "error_message": result.error_message,
        }

    # 没指定 workflow_id 就返回所有运行结果摘要
    summaries = []
    for wid, result in list(execution_results.items())[-int(limit):]:
        summaries.append({
            "workflow_id": wid,
            "status": result.status.value if hasattr(result.status, "value") else str(result.status),
            "executed_nodes": result.executed_nodes,
            "failed_nodes": result.failed_nodes,
        })
    return {"count": len(summaries), "executions": summaries}


# === 5. 长期记忆类 ===

def _get_memory_file() -> Path:
    folder = _get_data_folder() / "ai_assistant"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "long_term_memory.json"


def _load_memory() -> list[dict[str, Any]]:
    fp = _get_memory_file()
    if not fp.exists():
        return []
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_memory(items: list[dict[str, Any]]) -> None:
    fp = _get_memory_file()
    fp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


async def skill_remember(content: str, tags: list[str] | None = None, **_: Any) -> dict[str, Any]:
    """把一条长期记忆写入存档（用户的偏好、习惯、重要约定等）"""
    if not content.strip():
        return {"error": "记忆内容不能为空"}
    items = _load_memory()
    entry = {
        "id": uuid.uuid4().hex[:10],
        "content": content.strip(),
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
    }
    items.append(entry)
    # 上限 500 条，超过删最早
    if len(items) > 500:
        items = items[-500:]
    _save_memory(items)
    return {"success": True, "entry": entry, "total": len(items)}


async def skill_recall(keyword: str = "", limit: int = 10, **_: Any) -> dict[str, Any]:
    """查询长期记忆（按关键词或返回最近的若干条）"""
    items = _load_memory()
    if keyword:
        kw = keyword.lower()
        filtered = [
            i for i in items
            if kw in i.get("content", "").lower() or kw in " ".join(i.get("tags", [])).lower()
        ]
    else:
        filtered = items
    filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"count": len(filtered), "entries": filtered[: int(limit)]}


async def skill_forget(memory_id: str, **_: Any) -> dict[str, Any]:
    """删除一条长期记忆"""
    items = _load_memory()
    new_items = [i for i in items if i.get("id") != memory_id]
    if len(new_items) == len(items):
        return {"error": "未找到该记忆"}
    _save_memory(new_items)
    return {"success": True, "remaining": len(new_items)}


# === 6. 全局配置查询（只读，写入交给前端） ===

async def skill_get_global_config_keys(**_: Any) -> dict[str, Any]:
    """列出 WebRPA 全局配置中可配置的字段"""
    return {
        "categories": [
            {"key": "system", "items": ["checkUpdateOnStartup", "autoDetectClipboardScreenshot"]},
            {"key": "ai", "items": ["apiUrl", "apiKey", "model", "temperature", "maxTokens", "systemPrompt"]},
            {"key": "aiAssistant", "items": ["apiUrl", "apiKey", "model", "temperature", "maxTokens", "systemPrompt", "enableTools", "autoApprove"]},
            {"key": "aiScraper", "items": ["llmProvider", "apiUrl", "llmModel", "apiKey"]},
            {"key": "email", "items": ["senderEmail", "authCode", "smtpServer", "smtpPort"]},
            {"key": "browser", "items": ["type", "executablePath", "userDataDir", "fullscreen", "autoCloseBrowser", "launchArgs"]},
            {"key": "database", "items": ["host", "port", "user", "password", "database"]},
            {"key": "qq", "items": ["apiUrl", "accessToken"]},
            {"key": "feishu", "items": ["appId", "appSecret"]},
        ],
        "note": "实际写入由前端 globalConfigStore 完成。如需修改，请使用 update_global_config 工具，前端会接收并应用。",
    }


# ---------- 注册所有 Skills ----------

def _register_all() -> None:
    """注册全部 Skills"""

    # 模块信息
    registry.register(Skill(
        name="list_module_categories",
        description="列出 WebRPA 中所有内置模块的分类",
        parameters={"type": "object", "properties": {}},
        handler=skill_list_module_categories,
    ))
    registry.register(Skill(
        name="list_modules_in_category",
        description="列出某个分类下的所有模块",
        parameters={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "分类名（如：网页基础、AI、流程控制、PDF 等）",
                }
            },
            "required": ["category"],
        },
        handler=skill_list_modules_in_category,
    ))
    registry.register(Skill(
        name="describe_module",
        description="查询某个模块的用途和说明",
        parameters={
            "type": "object",
            "properties": {
                "module_type": {
                    "type": "string",
                    "description": "模块的 type 标识，例如 click_element、ai_chat、pdf_merge",
                }
            },
            "required": ["module_type"],
        },
        handler=skill_describe_module,
    ))
    registry.register(Skill(
        name="search_modules",
        description="按关键词搜索模块（中英文都行）",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["keyword"],
        },
        handler=skill_search_modules,
    ))

    # 工作流文件
    registry.register(Skill(
        name="list_workflows",
        description="列出本地保存的所有工作流文件",
        parameters={"type": "object", "properties": {}},
        handler=skill_list_workflows,
    ))
    registry.register(Skill(
        name="read_workflow",
        description="读取一个本地工作流文件的内容（节点过多时只返回摘要）",
        parameters={
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "工作流文件名（可省略 .json 后缀）"}
            },
            "required": ["filename"],
        },
        handler=skill_read_workflow,
    ))
    registry.register(Skill(
        name="save_workflow_file",
        description="把一个完整工作流（包含节点和边）保存到本地文件",
        parameters={
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "name": {"type": "string", "description": "工作流的显示名"},
                "nodes": {"type": "array", "items": {"type": "object"}},
                "edges": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["filename", "nodes", "edges"],
        },
        handler=skill_save_workflow_file,
    ))
    registry.register(Skill(
        name="delete_workflow",
        description="删除一个本地工作流文件（不可恢复）",
        parameters={
            "type": "object",
            "properties": {
                "filename": {"type": "string"}
            },
            "required": ["filename"],
        },
        handler=skill_delete_workflow,
        requires_approval=True,
    ))

    # 节点/工作流构造
    registry.register(Skill(
        name="build_node",
        description="构造一个节点 JSON，前端会把它加入到当前画布",
        parameters={
            "type": "object",
            "properties": {
                "module_type": {"type": "string", "description": "节点类型，例如 open_page"},
                "config": {"type": "object", "description": "节点的配置字段（具体字段视模块而定）"},
                "label": {"type": "string", "description": "节点显示名称"},
                "position": {
                    "type": "object",
                    "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
                },
            },
            "required": ["module_type"],
        },
        handler=skill_build_node,
    ))
    registry.register(Skill(
        name="build_workflow",
        description="根据有序的步骤数组生成完整的工作流（节点+边按顺序串联），前端可直接载入到画布",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "工作流名称"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "description": "节点 module_type"},
                            "label": {"type": "string"},
                            "config": {"type": "object"},
                        },
                        "required": ["type"],
                    },
                },
            },
            "required": ["name", "steps"],
        },
        handler=skill_build_workflow,
    ))

    # 系统状态
    registry.register(Skill(
        name="list_executors",
        description="列出后端实际注册的所有执行器类型（这是当前运行环境真正能跑的模块）",
        parameters={"type": "object", "properties": {}},
        handler=skill_list_executors,
    ))
    registry.register(Skill(
        name="list_custom_modules",
        description="列出所有用户自定义模块",
        parameters={"type": "object", "properties": {}},
        handler=skill_list_custom_modules,
    ))
    registry.register(Skill(
        name="list_scheduled_tasks",
        description="列出所有计划任务",
        parameters={"type": "object", "properties": {}},
        handler=skill_list_scheduled_tasks,
    ))
    registry.register(Skill(
        name="get_recent_logs",
        description="获取最近的工作流执行结果摘要",
        parameters={
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "工作流 ID（可选）"},
                "limit": {"type": "integer", "default": 50},
            },
        },
        handler=skill_get_recent_logs,
    ))

    # 长期记忆
    registry.register(Skill(
        name="remember",
        description="把一条信息写入长期记忆，例如用户的偏好、常用 API Key 名称、习惯做法等。后续会话可通过 recall 查询",
        parameters={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "要记住的内容"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["content"],
        },
        handler=skill_remember,
    ))
    registry.register(Skill(
        name="recall",
        description="从长期记忆中查找相关条目",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "关键词（留空则返回最近若干条）"},
                "limit": {"type": "integer", "default": 10},
            },
        },
        handler=skill_recall,
    ))
    registry.register(Skill(
        name="forget",
        description="删除一条长期记忆",
        parameters={
            "type": "object",
            "properties": {"memory_id": {"type": "string"}},
            "required": ["memory_id"],
        },
        handler=skill_forget,
        requires_approval=True,
    ))

    # 全局配置
    registry.register(Skill(
        name="get_global_config_keys",
        description="列出 WebRPA 全局配置可用的字段。需要修改时使用 client_action 工具让前端执行",
        parameters={"type": "object", "properties": {}},
        handler=skill_get_global_config_keys,
    ))

    # === 7. 客户端操作（标记型 Skills） ===
    # 这些工具不在后端真正执行，只是把意图返回给前端，由前端 SkillDispatcher 完成。
    # 让 LLM 知道"调这个工具就能让前端做事"。

    async def _client_action_stub(action: str, payload: dict | None = None, **_: Any) -> dict[str, Any]:
        return {
            "client_action": action,
            "payload": payload or {},
            "note": "此动作将由前端执行；前端确认完成后会回传执行结果",
        }

    registry.register(Skill(
        name="client_action",
        description=(
            "请前端执行一个 WebRPA 操作。可用 action 列表：\n"
            "- new_workflow：清空画布开始新工作流\n"
            "- load_workflow：加载本地工作流（payload.filename）\n"
            "- save_workflow：保存当前工作流（payload.filename）\n"
            "- run_workflow：运行当前工作流\n"
            "- stop_workflow：停止当前工作流\n"
            "- add_nodes：把节点加入画布（payload.nodes, payload.edges）\n"
            "- delete_node：删除节点（payload.node_id）\n"
            "- update_node_config：更新节点配置（payload.node_id, payload.config）\n"
            "- update_global_config：更新全局配置（payload.section, payload.values）\n"
            "- open_global_config：打开全局配置对话框\n"
            "- open_local_workflow_dialog：打开本地工作流对话框\n"
            "- open_scheduled_tasks：打开计划任务面板\n"
            "- open_documentation：打开使用文档\n"
            "- focus_node：聚焦到某个节点（payload.node_id）\n"
            "- show_toast：显示一条提示消息（payload.message, payload.type）\n"
            "调用时把 action 和必要的 payload 一起传过来，前端会做对应的事。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "动作名"},
                "payload": {"type": "object", "description": "动作参数"},
            },
            "required": ["action"],
        },
        handler=_client_action_stub,
    ))


_register_all()


# ---------- 公共调度入口 ----------

async def execute_skill(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """调度执行某个 Skill"""
    skill = registry.get(name)
    if skill is None:
        return {"error": f"未知工具: {name}"}
    try:
        result = await skill.handler(**arguments)
        return {"success": True, "result": result}
    except TypeError as e:
        return {"error": f"参数错误: {e}"}
    except Exception as e:
        return {"error": f"执行失败: {e}"}
