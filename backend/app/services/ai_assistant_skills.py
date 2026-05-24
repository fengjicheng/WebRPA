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
    """获取某个模块的描述 + 配置字段示例（自动从本地工作流和当前画布学习）"""
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

    # 从所有本地工作流中找出该 type 的节点作为配置参考
    config_examples: list[dict[str, Any]] = []
    config_field_names: set[str] = set()
    META_FIELDS = {"label", "moduleType", "remark", "customName", "subflowName",
                   "subflowGroupId", "isSubflow", "customModuleId", "isHighlighted",
                   "parameterValues"}
    try:
        folder = _get_workflow_folder()
        seen_count = 0
        for fp in folder.glob("*.json"):
            if seen_count >= 3:
                break
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            for n in (data.get("nodes") or []):
                ntype = n.get("type") or (n.get("data") or {}).get("moduleType")
                if ntype != module_type:
                    continue
                ndata = n.get("data") or {}
                cfg: dict[str, Any] = {}
                for k, v in ndata.items():
                    if k in META_FIELDS:
                        continue
                    if v is None or v == "":
                        continue
                    cfg[k] = v
                    config_field_names.add(k)
                if cfg:
                    config_examples.append({
                        "from_workflow": fp.stem,
                        "label": ndata.get("label") or "",
                        "config": cfg,
                    })
                    seen_count += 1
                    if seen_count >= 3:
                        break
    except Exception:
        pass

    return {
        "type": module_type,
        "description": desc or "（暂无文档）",
        "registered": is_registered,
        "config_field_names": sorted(config_field_names),
        "config_examples": config_examples[:3],
        "tip": (
            "上述 config_field_names 是该模块在历史工作流中实际用过的配置字段名。"
            "config_examples 给出真实样例。需要更精准的字段说明可同时调用 search_in_workflows 查找该模块的全部用法。"
        ) if config_examples else (
            "本地工作流中尚无该模块的使用样例。"
            "建议参考 WebRPA 教学文档或在 build_workflow 时仅传必填字段。"
        ),
    }


async def skill_search_modules(keyword: str, **_: Any) -> dict[str, Any]:
    """按关键词搜索模块（支持中英文模糊匹配，最多返回 50 条）"""
    if not keyword or not keyword.strip():
        return {"error": "关键词不能为空"}
    keyword = keyword.lower().strip()
    matches: list[dict[str, str]] = []
    for cat, modules in MODULE_CATEGORIES.items():
        for mtype, desc in modules.items():
            if keyword in mtype.lower() or keyword in desc.lower() or keyword in cat.lower():
                matches.append({"category": cat, "type": mtype, "description": desc})
    return {
        "keyword": keyword,
        "count": len(matches),
        "matches": matches[:50],
        "tip": "拿到 type 后用 describe_module 查看配置字段示例，再写 build_workflow",
    }


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
    notes: list[dict] | None = None,
    layout: str = "auto",
    title_note: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """根据有序步骤生成完整工作流（节点 + 边 + 便签 + 智能排版）

    Args:
        name: 工作流名称
        steps: 有序步骤数组，每个元素：
            {
                "type": "open_page",                     # 必填：模块 type
                "label": "打开网页",                      # 可选：节点显示名（推荐写）
                "config": {"url": "..."},                # 可选：节点配置
                "id": "step_open"                        # 可选：自定义 id（用于跳跃连接）
                "next": "step_click",                    # 可选：指定连到哪个 id（默认下一条）
                "section": "登录流程",                    # 可选：分段标题（同 section 在一行/一列）
                "comment": "首先打开登录页面"             # 可选：在该节点旁边自动生成黄色便签
            }
        notes: 显式追加便签（任意位置）
            [{"content": "...", "color": "yellow|blue|green|...",
              "anchor_to": "step_open", "side": "right|top|bottom"}]
            或 [{"content": "...", "x": 100, "y": 200}]
        layout: 'auto' / 'horizontal' / 'grid'。auto 默认按 8 个一行折回
        title_note: 顶部置顶的整体说明便签内容（不传则不生成）

    返回 nodes/edges 数组可被前端 load_workflow_from_data 直接消费。
    """
    if not isinstance(steps, list) or not steps:
        return {"error": "steps 不能为空"}

    # 节点尺寸常量（与前端默认一致）
    NODE_W = 220
    NODE_H = 100
    GAP_X = 80          # 同一行节点之间水平间距
    GAP_Y = 160         # 行间距（足够放置 between-node 的边/标签）
    SECTION_GAP = 60    # 不同 section 之间额外间距
    NOTE_W = 220
    NOTE_H = 100
    NOTE_GAP = 30       # 节点与便签之间的间距

    # 起点（y 留出空间给 title_note + 步骤上方便签）
    START_X = 120.0
    START_Y = 280.0

    # 1) 给每一步分配 id
    step_ids: list[str] = []
    user_ids: dict[str, str] = {}  # 用户给的 id → 实际 id
    for idx, step in enumerate(steps):
        sid = step.get("id") or _make_node_id()
        # 防 id 冲突
        if sid in user_ids.values():
            sid = _make_node_id()
        step_ids.append(sid)
        if step.get("id"):
            user_ids[step["id"]] = sid

    # 2) 决定排版方式：auto = 按 section 分组 + 8 个一行折回
    layout = (layout or "auto").lower()

    # 收集 section 顺序
    section_order: list[str] = []
    section_for_idx: list[str] = []
    for step in steps:
        sec = step.get("section") or ""
        if sec and sec not in section_order:
            section_order.append(sec)
        section_for_idx.append(sec)

    # 计算每个步骤的位置
    positions: list[tuple[float, float]] = []

    if layout == "horizontal":
        # 单行铺开（适合短工作流）
        for idx in range(len(steps)):
            x = START_X + idx * (NODE_W + GAP_X)
            positions.append((x, START_Y))

    elif layout == "grid":
        # 强制网格 4 列
        cols = 4
        for idx in range(len(steps)):
            row = idx // cols
            col = idx % cols
            x = START_X + col * (NODE_W + GAP_X)
            y = START_Y + row * (NODE_H + GAP_Y)
            positions.append((x, y))

    else:
        # auto：按 section 分行；同一 section 横向铺开，超 8 个换行
        # 没有 section 时整体按 8 个一行折回（蛇形）
        if section_order:
            # 不同 section 各占一行（或多行）
            current_y = START_Y
            section_to_pos: dict[int, tuple[float, float]] = {}
            for sec in section_order or [""]:
                sec_indices = [i for i in range(len(steps)) if section_for_idx[i] == sec]
                # 该 section 节点超 8 个则换行
                row_size = 8
                for j, sec_idx in enumerate(sec_indices):
                    row = j // row_size
                    col = j % row_size
                    x = START_X + col * (NODE_W + GAP_X)
                    y = current_y + row * (NODE_H + GAP_Y)
                    section_to_pos[sec_idx] = (x, y)
                # 更新下一段起始 y
                used_rows = (len(sec_indices) - 1) // row_size + 1
                current_y += used_rows * (NODE_H + GAP_Y) + SECTION_GAP
            for i in range(len(steps)):
                # 没标 section 的也归类到""
                positions.append(section_to_pos.get(i, (START_X, START_Y)))
        else:
            # 没有 section：8 个一行蛇形折回
            row_size = 8
            for idx in range(len(steps)):
                row = idx // row_size
                col = idx % row_size
                # 偶数行从左到右，奇数行从右到左 → 蛇形（连线最短）
                if row % 2 == 1:
                    col = row_size - 1 - col
                x = START_X + col * (NODE_W + GAP_X)
                y = START_Y + row * (NODE_H + GAP_Y)
                positions.append((x, y))

    # 3) 生成节点
    nodes: list[dict[str, Any]] = []
    for idx, step in enumerate(steps):
        mtype = step.get("type")
        if not mtype:
            return {"error": f"第 {idx} 步缺少 type 字段"}
        sid = step_ids[idx]
        x, y = positions[idx]
        # 业务配置全部直接展开到 data（NodeData 是扁平结构）
        cfg = step.get("config") or {}
        node_data: dict[str, Any] = {
            "label": step.get("label") or mtype,
            "moduleType": mtype,
        }
        # 备注（remark）会显示在节点底部
        if step.get("comment"):
            # comment 既是 remark，也会单独生成一个便签节点
            node_data["remark"] = step["comment"][:80]
        node_data.update(cfg)

        node = {
            "id": sid,
            "type": mtype,
            "position": {"x": float(x), "y": float(y)},
            "data": node_data,
        }
        nodes.append(node)

    # 4) 生成边（按 next/默认相邻）
    edges: list[dict[str, Any]] = []

    def _resolve_id(ref: str) -> str | None:
        """先在 user_ids 里找，再在 step_ids 里精确找"""
        if not ref:
            return None
        if ref in user_ids:
            return user_ids[ref]
        if ref in step_ids:
            return ref
        return None

    for idx, step in enumerate(steps):
        sid = step_ids[idx]
        next_ref = step.get("next")
        target_id: str | None = None
        if next_ref:
            target_id = _resolve_id(next_ref)
        elif idx < len(steps) - 1:
            target_id = step_ids[idx + 1]

        if target_id and target_id != sid:
            edges.append({
                "id": f"e-{sid}-{target_id}",
                "source": sid,
                "target": target_id,
            })

    # 5) 生成便签（智能排版）
    note_nodes: list[dict[str, Any]] = []

    # 5a) 顶部"工作流说明"便签（如果有）
    if title_note:
        note_nodes.append({
            "id": _make_node_id(),
            "type": "note",
            "position": {"x": float(START_X), "y": 60.0},
            "data": {
                "label": "",
                "moduleType": "note",
                "content": title_note[:600],
                "color": "#bfdbfe",  # 蓝色：整体说明
                "fontSize": 14,
                "fontBold": True,
            },
            "style": {"width": max(NOTE_W * 2, 380), "height": 80},
            "zIndex": -1,
        })

    # 5b) 每个 step 的 comment（如果有）→ 在该节点上方生成小便签
    for idx, step in enumerate(steps):
        if not step.get("comment"):
            continue
        sx, sy = positions[idx]
        # 第一行的 step 上方可能与 title_note 重叠 → 这种情况放到节点右侧
        title_overlap_zone = title_note is not None and sy < 200
        if title_overlap_zone or sy - NOTE_H - NOTE_GAP < 50:
            nx = sx + NODE_W + NOTE_GAP
            ny = sy
        else:
            nx = sx
            ny = sy - NOTE_H - NOTE_GAP
        note_nodes.append({
            "id": _make_node_id(),
            "type": "note",
            "position": {"x": float(nx), "y": float(ny)},
            "data": {
                "label": "",
                "moduleType": "note",
                "content": str(step["comment"])[:300],
                "color": "#fef08a",  # 黄色：步骤注释
                "fontSize": 12,
            },
            "style": {"width": NOTE_W, "height": NOTE_H},
            "zIndex": -1,
        })

    # 5c) 显式追加的 notes
    if notes:
        color_map = {
            "yellow": "#fef08a", "green": "#bbf7d0", "blue": "#bfdbfe",
            "purple": "#ddd6fe", "pink": "#fbcfe8", "orange": "#fed7aa",
            "white": "#ffffff", "gray": "#e5e7eb",
        }
        for n in notes:
            content = (n.get("content") or "").strip()
            if not content:
                continue
            color = color_map.get((n.get("color") or "yellow").lower(), "#fef08a")
            anchor = n.get("anchor_to")
            side = (n.get("side") or "right").lower()
            nx: float
            ny: float
            if anchor:
                anchor_id = _resolve_id(str(anchor))
                if anchor_id and anchor_id in step_ids:
                    aidx = step_ids.index(anchor_id)
                    ax, ay = positions[aidx]
                    if side == "top":
                        nx = ax
                        ny = ay - NOTE_H - NOTE_GAP
                    elif side == "bottom":
                        nx = ax
                        ny = ay + NODE_H + NOTE_GAP
                    elif side == "left":
                        nx = ax - NOTE_W - NOTE_GAP
                        ny = ay
                    else:  # right
                        nx = ax + NODE_W + NOTE_GAP
                        ny = ay
                else:
                    nx = float(n.get("x", START_X))
                    ny = float(n.get("y", START_Y))
            else:
                nx = float(n.get("x", START_X))
                ny = float(n.get("y", START_Y))
            note_nodes.append({
                "id": _make_node_id(),
                "type": "note",
                "position": {"x": nx, "y": ny},
                "data": {
                    "label": "",
                    "moduleType": "note",
                    "content": content[:600],
                    "color": color,
                    "fontSize": int(n.get("font_size", 13)),
                    "fontBold": bool(n.get("bold", False)),
                    "fontItalic": bool(n.get("italic", False)),
                },
                "style": {
                    "width": int(n.get("width", NOTE_W)),
                    "height": int(n.get("height", NOTE_H)),
                },
                "zIndex": -1,
            })

    # 把便签放在节点之前（让 react-flow 渲染顺序合理；前端 zIndex 也设为 -1）
    all_nodes = note_nodes + nodes

    return {
        "name": name,
        "nodes": all_nodes,
        "edges": edges,
        "node_count": len(nodes),
        "note_count": len(note_nodes),
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


async def skill_get_current_workflow(**_: Any) -> dict[str, Any]:
    """获取当前画布上的工作流（前端会随每次对话发送）。
    这个 Skill 主要用于 LLM 显式查询，但实际数据在每轮对话的 system prompt 里已经注入过。
    """
    return {
        "note": "当前画布的节点和边已包含在系统提示词的'当前工作流的状态'部分。如需更详细的节点配置，请使用 client_action 工具的 'get_workflow_detail' 动作。",
    }


async def skill_get_workflow_executors_for_canvas(**_: Any) -> dict[str, Any]:
    """获取所有真实可用的执行器类型，并按知识库分类组织
    （用于 LLM 想要"看清楚有哪些模块"时调用）
    """
    try:
        from app.executors.base import registry as exec_registry
        types = sorted(exec_registry.get_all_types())
    except Exception as e:
        return {"error": str(e)}

    # 把它们映射回知识库分类
    type_to_cat: dict[str, str] = {}
    for cat, modules in MODULE_CATEGORIES.items():
        for mtype in modules:
            type_to_cat[mtype] = cat

    grouped: dict[str, list[str]] = {}
    uncategorized: list[str] = []
    for t in types:
        cat = type_to_cat.get(t)
        if cat:
            grouped.setdefault(cat, []).append(t)
        else:
            uncategorized.append(t)

    return {
        "total": len(types),
        "categorized": grouped,
        "uncategorized": uncategorized,
    }


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


# === 5b. 全量快照类（一次拿到 WebRPA 所有可见状态） ===

async def skill_get_full_snapshot(**_: Any) -> dict[str, Any]:
    """一次性拿到当前 WebRPA 后端全部可见状态：执行器列表、自定义模块、计划任务、本地工作流、最近执行结果。
    用于 LLM 第一次开始任务时获得整体上下文。"""
    snap: dict[str, Any] = {}
    # 1) 执行器
    try:
        from app.executors.base import registry as exec_registry
        types = sorted(exec_registry.get_all_types())
        snap["executors_count"] = len(types)
        snap["executor_types"] = types[:200]
    except Exception as e:
        snap["executors_error"] = str(e)
    # 2) 本地工作流
    try:
        folder = _get_workflow_folder()
        snap["local_workflows"] = [
            fp.stem for fp in sorted(folder.glob("*.json"))
        ]
    except Exception as e:
        snap["local_workflows_error"] = str(e)
    # 3) 自定义模块
    try:
        cm_folder = _get_data_folder() / "custom_modules"
        custom: list[dict[str, Any]] = []
        if cm_folder.exists():
            for fp in sorted(cm_folder.glob("*.json")):
                try:
                    data = json.loads(fp.read_text(encoding="utf-8"))
                    custom.append({
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "category": data.get("category", ""),
                    })
                except Exception:
                    pass
        snap["custom_modules"] = custom
    except Exception as e:
        snap["custom_modules_error"] = str(e)
    # 4) 计划任务
    try:
        fp = _get_data_folder() / "scheduled_tasks.json"
        if fp.exists():
            data = json.loads(fp.read_text(encoding="utf-8"))
            tasks = data if isinstance(data, list) else data.get("tasks", [])
            snap["scheduled_tasks"] = [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "enabled": t.get("enabled"),
                    "trigger_type": t.get("trigger_type") or t.get("triggerType"),
                }
                for t in tasks
            ]
        else:
            snap["scheduled_tasks"] = []
    except Exception as e:
        snap["scheduled_tasks_error"] = str(e)
    # 5) 最近执行结果摘要
    try:
        from app.api.workflows import execution_results
        recents = []
        for wid, r in list(execution_results.items())[-10:]:
            recents.append({
                "workflow_id": wid,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "executed_nodes": r.executed_nodes,
                "failed_nodes": r.failed_nodes,
            })
        snap["recent_executions"] = recents
    except Exception:
        snap["recent_executions"] = []
    # 6) 全局变量
    try:
        from app.services.variable_manager import VariableManager
        # 这里默认全局变量管理器是单例形式，但项目里通常按工作流创建，所以仅返回标记
        snap["note"] = "运行时全局变量请通过 list_global_variables 查询"
    except Exception:
        pass
    return snap


async def skill_list_global_variables(**_: Any) -> dict[str, Any]:
    """读取所有持久化的全局变量"""
    try:
        # WebRPA 把全局变量存储为前端 store 状态，但执行器会持久化到 backend/data/global_vars.json
        fp = _get_data_folder() / "global_vars.json"
        if not fp.exists():
            return {"variables": {}, "note": "目前还没有持久化的全局变量"}
        data = json.loads(fp.read_text(encoding="utf-8"))
        return {"variables": data, "count": len(data) if isinstance(data, dict) else 0}
    except Exception as e:
        return {"error": str(e)}


# === 5c. 计划任务管理（CRUD） ===

async def skill_get_scheduled_task(task_id: str, **_: Any) -> dict[str, Any]:
    """获取某个计划任务的详情"""
    fp = _get_data_folder() / "scheduled_tasks.json"
    if not fp.exists():
        return {"error": "暂无计划任务"}
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        tasks = data if isinstance(data, list) else data.get("tasks", [])
        for t in tasks:
            if t.get("id") == task_id:
                return {"task": t}
        return {"error": f"未找到任务 {task_id}"}
    except Exception as e:
        return {"error": str(e)}


async def skill_get_scheduled_task_logs(task_id: str | None = None, limit: int = 50, **_: Any) -> dict[str, Any]:
    """读取计划任务的执行日志"""
    fp = _get_data_folder() / "scheduled_task_logs.json"
    if not fp.exists():
        return {"logs": [], "count": 0}
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        logs = data if isinstance(data, list) else data.get("logs", [])
        if task_id:
            logs = [l for l in logs if l.get("task_id") == task_id]
        logs = logs[-int(limit):]
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        return {"error": str(e)}


# === 5d. 资源管理类 ===

async def skill_list_data_assets(folder: str | None = None, **_: Any) -> dict[str, Any]:
    """列出所有 Excel 数据资源（uploads/excel）"""
    try:
        from app.api.data_assets import data_assets
        items = []
        for a in data_assets.values():
            if folder is not None and a.get("folder") != folder:
                continue
            items.append({
                "id": a.get("id"),
                "name": a.get("name"),
                "folder": a.get("folder", ""),
                "size": a.get("size"),
                "sheets": a.get("sheetNames", []),
            })
        return {"count": len(items), "assets": items}
    except Exception as e:
        return {"error": str(e)}


async def skill_list_image_assets(folder: str | None = None, **_: Any) -> dict[str, Any]:
    """列出所有图像资源（uploads/images）"""
    try:
        from app.api.image_assets import image_assets
        items = []
        for a in image_assets.values():
            if folder is not None and a.get("folder") != folder:
                continue
            items.append({
                "id": a.get("id"),
                "name": a.get("name"),
                "folder": a.get("folder", ""),
                "size": a.get("size"),
                "extension": a.get("extension"),
            })
        return {"count": len(items), "images": items}
    except Exception as e:
        return {"error": str(e)}


async def skill_get_custom_module(module_id: str, **_: Any) -> dict[str, Any]:
    """获取自定义模块的完整定义（包括内部工作流）"""
    folder = _get_data_folder() / "custom_modules"
    if not folder.exists():
        return {"error": "自定义模块目录不存在"}
    fp = folder / f"{module_id}.json"
    try:
        fp.resolve().relative_to(folder.resolve())
    except ValueError:
        return {"error": "非法 module_id"}
    if not fp.exists():
        return {"error": f"未找到模块 {module_id}"}
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        return {"module": data}
    except Exception as e:
        return {"error": str(e)}


# === 5e. 全文搜索（在所有本地工作流和自定义模块里搜文本） ===

async def skill_search_in_workflows(keyword: str, **_: Any) -> dict[str, Any]:
    """在所有本地工作流的 JSON 里搜索关键词（含节点 label、URL、变量名等）"""
    if not keyword.strip():
        return {"error": "关键词不能为空"}
    folder = _get_workflow_folder()
    matches: list[dict[str, Any]] = []
    kw = keyword.lower()
    for fp in sorted(folder.glob("*.json")):
        try:
            text = fp.read_text(encoding="utf-8")
            if kw in text.lower():
                # 找出包含关键词的节点
                data = json.loads(text)
                hits: list[dict[str, Any]] = []
                for n in data.get("nodes", []):
                    n_text = json.dumps(n, ensure_ascii=False).lower()
                    if kw in n_text:
                        hits.append({
                            "id": n.get("id"),
                            "type": n.get("type"),
                            "label": (n.get("data") or {}).get("label", ""),
                        })
                matches.append({
                    "filename": fp.name,
                    "name": fp.stem,
                    "hit_nodes": hits[:10],
                })
        except Exception:
            continue
    return {"keyword": keyword, "files_matched": len(matches), "matches": matches[:20]}


# === 5f. 上下文摘要 / AI 自主任务计划 ===

async def skill_summarize_workflow(filename: str, **_: Any) -> dict[str, Any]:
    """读一个工作流并产出结构化摘要（节点序列 + 入口/出口 + 变量使用）"""
    folder = _get_workflow_folder()
    if not filename.endswith(".json"):
        filename = filename + ".json"
    fp = folder / filename
    try:
        fp.resolve().relative_to(folder.resolve())
    except ValueError:
        return {"error": "非法文件名"}
    if not fp.exists():
        return {"error": "文件不存在"}
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"解析失败: {e}"}

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    in_edges: dict[str, int] = {}
    out_edges: dict[str, int] = {}
    for e in edges:
        in_edges[e.get("target")] = in_edges.get(e.get("target"), 0) + 1
        out_edges[e.get("source")] = out_edges.get(e.get("source"), 0) + 1

    entries = [n.get("id") for n in nodes if in_edges.get(n.get("id"), 0) == 0]
    exits = [n.get("id") for n in nodes if out_edges.get(n.get("id"), 0) == 0]

    # 抽取节点配置中的变量引用
    import re as _re
    var_pattern = _re.compile(r"\{([A-Za-z_][\w]*)\}")
    var_uses: set[str] = set()
    for n in nodes:
        text = json.dumps(n.get("data", {}), ensure_ascii=False)
        for m in var_pattern.findall(text):
            var_uses.add(m)

    # 节点顺序（拓扑近似）
    type_seq = [n.get("type") for n in nodes if n.get("type")]

    return {
        "name": data.get("name", fp.stem),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "entry_nodes": entries[:10],
        "exit_nodes": exits[:10],
        "node_type_sequence": type_seq[:50],
        "variables_used": sorted(var_uses)[:30],
    }


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


# === 7. 系统执行能力（PowerShell + Python 临时脚本） ===

import asyncio as _asyncio
import os as _os
import sys as _sys
import tempfile as _tempfile


def _project_root() -> Path:
    """WebRPA 项目根目录（包含 backend/ 和 Python313/）"""
    # backend/app/services/ai_assistant_skills.py -> backend/app/services -> backend/app -> backend -> 根
    return Path(__file__).parent.parent.parent.parent


def _get_bundled_python_path() -> str:
    """获取 WebRPA 内置的 Python313/python.exe；不存在时回退到当前解释器"""
    py = _project_root() / "Python313" / "python.exe"
    if py.exists():
        return str(py)
    # macOS / Linux 的子目录可能叫 python313/bin/python
    py_unix = _project_root() / "Python313" / "bin" / "python"
    if py_unix.exists():
        return str(py_unix)
    return _sys.executable


async def skill_run_shell_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 60,
    shell: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """执行系统 shell 命令（Windows 默认走 PowerShell，其他平台走默认 shell）。

    Args:
        command: 要执行的命令（多行命令也支持）
        cwd: 工作目录，留空 = 项目根目录
        timeout: 超时秒数，最大 600
        shell: 强制指定 shell：'powershell' / 'cmd' / 'bash' / 'sh'。留空走平台默认
    """
    if not command or not command.strip():
        return {"error": "命令不能为空"}

    timeout = min(max(int(timeout), 1), 600)
    work_dir = cwd or str(_project_root())
    is_windows = _os.name == "nt"

    # 决定使用什么 shell
    s = (shell or "").strip().lower()
    if not s:
        s = "powershell" if is_windows else "bash"

    if s == "powershell":
        # 用 -NoProfile 避免加载用户 profile 拖慢启动
        cmd_args = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-Command", command,
        ]
        shell_kwargs: dict[str, Any] = {}
    elif s == "cmd":
        cmd_args = ["cmd.exe", "/c", command]
        shell_kwargs = {}
    elif s in ("bash", "sh"):
        cmd_args = [s, "-c", command]
        shell_kwargs = {}
    else:
        return {"error": f"不支持的 shell：{shell}"}

    creationflags = 0x08000000 if is_windows else 0  # CREATE_NO_WINDOW

    try:
        process = await _asyncio.create_subprocess_exec(
            *cmd_args,
            cwd=work_dir,
            stdout=_asyncio.subprocess.PIPE,
            stderr=_asyncio.subprocess.PIPE,
            creationflags=creationflags,
            **shell_kwargs,
        )
    except Exception as e:
        return {"error": f"启动子进程失败：{e}"}

    try:
        stdout_b, stderr_b = await _asyncio.wait_for(process.communicate(), timeout=timeout)
    except _asyncio.TimeoutError:
        try:
            process.kill()
            await process.wait()
        except Exception:
            pass
        return {"error": f"命令超时（{timeout} 秒），已强制终止"}

    # Windows 默认 GBK，尝试用 utf-8 + gbk 兜底
    def _decode(b: bytes) -> str:
        if not b:
            return ""
        for enc in ("utf-8", "gbk", "cp936"):
            try:
                return b.decode(enc)
            except UnicodeDecodeError:
                continue
        return b.decode("utf-8", errors="replace")

    stdout = _decode(stdout_b)
    stderr = _decode(stderr_b)
    return_code = process.returncode

    # 截断超长输出
    MAX_LEN = 20000
    truncated = False
    if len(stdout) > MAX_LEN:
        stdout = stdout[:MAX_LEN] + f"\n…（已截断，原长度 {len(stdout_b)} 字节）"
        truncated = True
    if len(stderr) > MAX_LEN:
        stderr = stderr[:MAX_LEN] + f"\n…（已截断，原长度 {len(stderr_b)} 字节）"
        truncated = True

    return {
        "command": command,
        "shell": s,
        "cwd": work_dir,
        "return_code": return_code,
        "success_exit": return_code == 0,
        "stdout": stdout,
        "stderr": stderr,
        "truncated": truncated,
    }


async def skill_run_python_script(
    code: str,
    timeout: int = 120,
    args: list[str] | None = None,
    extra_env: dict[str, str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """写一段 Python 代码到临时文件，使用 WebRPA 内置 Python 3.13 运行，
    拿到 stdout/stderr/returncode 后**自动销毁临时文件**。

    Args:
        code: 完整可执行的 Python 源码（应当能独立运行，包含必要的 import）
        timeout: 超时秒数，最大 1800
        args: 传给脚本的命令行参数（sys.argv[1:]）
        extra_env: 追加到进程环境变量的键值对
    """
    if not code or not code.strip():
        return {"error": "Python 代码不能为空"}

    timeout = min(max(int(timeout), 1), 1800)
    py_exe = _get_bundled_python_path()

    # 写临时脚本文件（带 BOM 头，确保 Windows Python 用 UTF-8 解码）
    tmp_dir = Path(_tempfile.gettempdir()) / "webrpa_ai_scripts"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    script_path = tmp_dir / f"ai_script_{uuid.uuid4().hex[:10]}.py"

    # 强制声明 utf-8（避免 Windows 默认 cp1252 解码报错）
    final_code = "# -*- coding: utf-8 -*-\nimport sys\ntry:\n    sys.stdout.reconfigure(encoding='utf-8')\n    sys.stderr.reconfigure(encoding='utf-8')\nexcept Exception:\n    pass\n\n" + code

    try:
        script_path.write_text(final_code, encoding="utf-8")
    except Exception as e:
        return {"error": f"写入临时脚本失败：{e}"}

    is_windows = _os.name == "nt"
    creationflags = 0x08000000 if is_windows else 0
    cmd_args = [py_exe, "-X", "utf8", str(script_path)]
    if args:
        cmd_args.extend(str(a) for a in args)

    env = dict(_os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if extra_env:
        for k, v in extra_env.items():
            env[str(k)] = str(v)

    try:
        process = await _asyncio.create_subprocess_exec(
            *cmd_args,
            cwd=str(_project_root()),
            stdout=_asyncio.subprocess.PIPE,
            stderr=_asyncio.subprocess.PIPE,
            env=env,
            creationflags=creationflags,
        )
    except Exception as e:
        try:
            script_path.unlink(missing_ok=True)
        except Exception:
            pass
        return {"error": f"启动 Python 子进程失败：{e}"}

    timed_out = False
    try:
        stdout_b, stderr_b = await _asyncio.wait_for(process.communicate(), timeout=timeout)
    except _asyncio.TimeoutError:
        timed_out = True
        try:
            process.kill()
            await process.wait()
        except Exception:
            pass
        stdout_b = b""
        stderr_b = f"超时（{timeout} 秒），进程已被强制终止".encode()

    # 自动销毁临时文件
    try:
        script_path.unlink(missing_ok=True)
    except Exception:
        pass

    def _decode(b: bytes) -> str:
        if not b:
            return ""
        for enc in ("utf-8", "gbk", "cp936"):
            try:
                return b.decode(enc)
            except UnicodeDecodeError:
                continue
        return b.decode("utf-8", errors="replace")

    stdout = _decode(stdout_b)
    stderr = _decode(stderr_b)
    return_code = process.returncode if not timed_out else -9

    # 截断
    MAX_LEN = 30000
    truncated = False
    if len(stdout) > MAX_LEN:
        stdout = stdout[:MAX_LEN] + f"\n…（已截断，原长度 {len(stdout_b)} 字节）"
        truncated = True
    if len(stderr) > MAX_LEN:
        stderr = stderr[:MAX_LEN] + f"\n…（已截断，原长度 {len(stderr_b)} 字节）"
        truncated = True

    return {
        "python_path": py_exe,
        "return_code": return_code,
        "timed_out": timed_out,
        "success_exit": return_code == 0 and not timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "truncated": truncated,
        "script_lifecycle": "已自动销毁",
    }


async def skill_check_python_environment(**_: Any) -> dict[str, Any]:
    """快速验证 WebRPA 内置 Python 是否可用，返回版本与已安装的关键包"""
    py_exe = _get_bundled_python_path()
    check_code = (
        "import sys, platform, json\n"
        "info = {\n"
        "    'python_version': sys.version,\n"
        "    'platform': platform.platform(),\n"
        "    'executable': sys.executable,\n"
        "    'prefix': sys.prefix,\n"
        "}\n"
        "available = []\n"
        "for pkg in ['requests', 'pandas', 'numpy', 'openpyxl', 'pillow', 'PIL', 'bs4', 'lxml', 'playwright', 'httpx', 'aiohttp', 'fastapi', 'uvicorn']:\n"
        "    try:\n"
        "        __import__(pkg)\n"
        "        available.append(pkg)\n"
        "    except Exception:\n"
        "        pass\n"
        "info['available_packages'] = available\n"
        "print(json.dumps(info, ensure_ascii=False))\n"
    )
    res = await skill_run_python_script(code=check_code, timeout=20)
    if res.get("success_exit") and res.get("stdout"):
        try:
            parsed = json.loads(res["stdout"].strip().splitlines()[-1])
            return {"python_executable": py_exe, **parsed}
        except Exception:
            pass
    return {
        "python_executable": py_exe,
        "raw_stdout": res.get("stdout", ""),
        "raw_stderr": res.get("stderr", ""),
        "error": "无法解析 Python 环境信息",
    }


# ---------- 注册所有 Skills ----------

def _register_all() -> None:
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
        description=(
            "根据有序步骤生成一个完整工作流（节点 + 边 + 智能排版 + 自动便签注释）。"
            "后端会做以下事情：①自动按 8 个一行折回排版避免拥挤 ②为带 comment 的步骤自动生成黄色便签贴在节点旁 "
            "③可选 title_note 在画布顶部生成蓝色「工作流说明」便签 ④可选 notes 数组追加任意位置便签 "
            "⑤同 section 字段会被分到一行，使工作流逻辑清晰可读。"
            "前端调用此工具后会**自动把结果装入画布**，无需再调 load_workflow_from_data。"
            "强烈建议为每一步写 label（节点显示名）和 comment（注释，会变成便签）。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "工作流名称"},
                "title_note": {
                    "type": "string",
                    "description": "顶部置顶的整体说明便签（蓝色，加粗），简述这个工作流是干什么的、需要什么前置条件",
                },
                "layout": {
                    "type": "string",
                    "description": "排版方式：auto(默认)/horizontal(单行)/grid(4列网格)",
                    "enum": ["auto", "horizontal", "grid"],
                },
                "steps": {
                    "type": "array",
                    "description": "有序步骤。前后步骤会自动连线；可用 next 跳跃，可用 section 分组",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "description": "节点 module_type，例如 open_page/click_element"},
                            "label": {"type": "string", "description": "节点显示名（推荐写中文，例如「打开登录页」）"},
                            "config": {"type": "object", "description": "节点配置字段"},
                            "id": {
                                "type": "string",
                                "description": "可选自定义 id（仅当本步骤会被其他步骤跳跃连接时才需要）",
                            },
                            "next": {
                                "type": "string",
                                "description": "可选指定下一节点 id（不写则连到下一个步骤）",
                            },
                            "section": {
                                "type": "string",
                                "description": "可选分段标题。同 section 的步骤会被排在一行/同一区域",
                            },
                            "comment": {
                                "type": "string",
                                "description": "可选注释。会自动生成黄色便签贴在节点上方，方便用户快速理解",
                            },
                        },
                        "required": ["type"],
                    },
                },
                "notes": {
                    "type": "array",
                    "description": "显式追加便签。任意位置 / 锚定到某个步骤旁",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "color": {
                                "type": "string",
                                "enum": ["yellow", "green", "blue", "purple", "pink", "orange", "white", "gray"],
                            },
                            "anchor_to": {
                                "type": "string",
                                "description": "锚定到某个步骤的 id（写自定义 id 或步骤索引 id）",
                            },
                            "side": {
                                "type": "string",
                                "enum": ["top", "right", "bottom", "left"],
                            },
                            "x": {"type": "number", "description": "未锚定时的绝对 x 坐标"},
                            "y": {"type": "number", "description": "未锚定时的绝对 y 坐标"},
                            "width": {"type": "number"},
                            "height": {"type": "number"},
                            "font_size": {"type": "integer"},
                            "bold": {"type": "boolean"},
                            "italic": {"type": "boolean"},
                        },
                        "required": ["content"],
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
        name="list_canvas_executors",
        description="列出所有真实可用的执行器类型，并按 WebRPA 的知识库分类组织（建议用这个代替 list_executors，能看到分类）",
        parameters={"type": "object", "properties": {}},
        handler=skill_get_workflow_executors_for_canvas,
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

    # 全量快照与扩展查询
    registry.register(Skill(
        name="get_full_snapshot",
        description=(
            "一次性获取后端全部可见状态：执行器列表、本地工作流名、自定义模块、计划任务、最近执行结果。"
            "推荐 LLM 在开始任务前先调用一次，以便对项目当前状态有整体认识。"
        ),
        parameters={"type": "object", "properties": {}},
        handler=skill_get_full_snapshot,
    ))
    registry.register(Skill(
        name="list_global_variables",
        description="读取后端持久化的全局变量",
        parameters={"type": "object", "properties": {}},
        handler=skill_list_global_variables,
    ))
    registry.register(Skill(
        name="get_scheduled_task",
        description="获取某个计划任务的完整定义（trigger 配置、关联工作流等）",
        parameters={
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
        handler=skill_get_scheduled_task,
    ))
    registry.register(Skill(
        name="get_scheduled_task_logs",
        description="读取计划任务的执行日志",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "可选，只看某个任务的"},
                "limit": {"type": "integer", "default": 50},
            },
        },
        handler=skill_get_scheduled_task_logs,
    ))
    registry.register(Skill(
        name="list_data_assets",
        description="列出所有 Excel 资源（uploads/excel）",
        parameters={
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "可选，只看某子目录"}
            },
        },
        handler=skill_list_data_assets,
    ))
    registry.register(Skill(
        name="list_image_assets",
        description="列出所有图像资源（uploads/images）",
        parameters={
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "可选，只看某子目录"}
            },
        },
        handler=skill_list_image_assets,
    ))
    registry.register(Skill(
        name="get_custom_module",
        description="读取一个自定义模块的完整定义（包含其内部工作流）",
        parameters={
            "type": "object",
            "properties": {"module_id": {"type": "string"}},
            "required": ["module_id"],
        },
        handler=skill_get_custom_module,
    ))
    registry.register(Skill(
        name="search_in_workflows",
        description="在所有本地工作流文件里搜索文本（节点 label、URL、变量名等）",
        parameters={
            "type": "object",
            "properties": {"keyword": {"type": "string"}},
            "required": ["keyword"],
        },
        handler=skill_search_in_workflows,
    ))
    registry.register(Skill(
        name="summarize_workflow",
        description="读取一个本地工作流并产出结构化摘要（入口/出口节点、节点序列、用到的变量等）",
        parameters={
            "type": "object",
            "properties": {"filename": {"type": "string"}},
            "required": ["filename"],
        },
        handler=skill_summarize_workflow,
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

    # === 系统执行能力（PowerShell + Python 临时脚本） ===
    registry.register(Skill(
        name="run_shell_command",
        description=(
            "执行系统 shell 命令并返回 stdout/stderr/return_code。"
            "Windows 下默认使用 PowerShell。可用于：查询系统信息、列文件、操作 git、调用 cli 工具等。"
            "高风险（如 rm -rf、del /q、Remove-Item -Recurse、reg delete、format 等）需要在确认后再执行。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "完整命令字符串（支持多行）"},
                "cwd": {"type": "string", "description": "工作目录，留空则在 WebRPA 项目根目录执行"},
                "timeout": {"type": "integer", "description": "超时秒数（默认 60，最大 600）"},
                "shell": {
                    "type": "string",
                    "description": "强制指定 shell：powershell / cmd / bash / sh。Windows 默认 powershell",
                    "enum": ["powershell", "cmd", "bash", "sh"],
                },
            },
            "required": ["command"],
        },
        handler=skill_run_shell_command,
        requires_approval=True,
    ))
    registry.register(Skill(
        name="run_python_script",
        description=(
            "把一段 Python 代码写到临时脚本，使用 WebRPA 内置 Python 3.13 运行，"
            "拿到运行结果后**自动销毁**该临时脚本（三步走：写入 → 运行 → 销毁）。"
            "适合做：数据处理、文件批量操作、网络请求、JSON/CSV/Excel 解析、算法计算、调用第三方库等。"
            "注意：脚本默认 utf-8 编码，可直接 print 中文；不要在脚本里写绝对依赖外部状态的代码。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "完整可运行的 Python 源码（含必要的 import）"},
                "timeout": {"type": "integer", "description": "超时秒数（默认 120，最大 1800）"},
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "传给脚本的命令行参数（脚本里通过 sys.argv[1:] 读取）",
                },
                "extra_env": {
                    "type": "object",
                    "description": "追加到子进程的环境变量字典",
                },
            },
            "required": ["code"],
        },
        handler=skill_run_python_script,
        requires_approval=True,
    ))
    registry.register(Skill(
        name="check_python_environment",
        description="检查 WebRPA 内置 Python 是否可用、列出版本和已安装的常用库",
        parameters={"type": "object", "properties": {}},
        handler=skill_check_python_environment,
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
            "请前端执行一个 WebRPA 操作。这是小助手操作前端最重要的工具，可用 action 完整列表：\n\n"
            "【工作流操作】\n"
            "- new_workflow: 新建空白工作流\n"
            "- load_workflow: 加载本地工作流（payload.filename）\n"
            "- load_workflow_from_data: 直接载入完整工作流到画布（payload.name, payload.nodes, payload.edges）\n"
            "- save_workflow: 保存当前工作流\n"
            "- run_workflow: 有头模式运行当前工作流\n"
            "- run_workflow_headless: 无头模式运行当前工作流\n"
            "- stop_workflow: 停止当前工作流\n"
            "- export_workflow: 导出工作流（payload.format='json'|'playwright'|'markdown'）\n"
            "- rename_workflow: 重命名当前工作流（payload.name）\n"
            "- get_workflow_detail: 拿到当前画布的完整 nodes/edges/variables（节点配置详情）\n"
            "- get_logs: 获取最近日志（payload.limit, 默认 100）\n"
            "- get_collected_data: 获取当前数据表格内容\n\n"
            "【节点】\n"
            "- add_nodes: 把节点加入画布（payload.nodes, payload.edges）\n"
            "- delete_node: 删除单个节点（payload.node_id）\n"
            "- delete_nodes: 批量删除节点（payload.node_ids）\n"
            "- update_node_config: 更新节点配置（payload.node_id, payload.config）\n"
            "- focus_node: 聚焦/选中节点（payload.node_id）\n"
            "- toggle_node_disabled: 启用/禁用节点（payload.node_ids）\n"
            "- align_nodes: 对齐已选中的节点（payload.type='left'|'center'|'right'|'top'|'middle'|'bottom'|'distribute-horizontal'|'distribute-vertical'）\n"
            "- copy_nodes: 复制节点到剪贴板（payload.node_ids）\n"
            "- paste_nodes: 粘贴剪贴板节点（payload.position 可选）\n"
            "- move_node: 把节点移动到指定坐标（payload.node_id, payload.x, payload.y）\n"
            "- rename_node: 修改节点显示名（payload.node_id, payload.label）\n"
            "- find_nodes_by_type: 查找所有指定 type 的节点 id（payload.type）\n"
            "- connect_nodes: 创建节点之间的连线（payload.source, payload.target, payload.source_handle 可选, payload.target_handle 可选）\n"
            "- disconnect_edge: 删除指定连线（payload.edge_id）\n"
            "- select_all_nodes: 选中画布所有节点\n"
            "- clear_selection: 取消所有节点选中\n"
            "- fit_view: 自动缩放画布让所有节点可见\n"
            "- run_single_node: 单独运行某节点（仅支持调试场景）（payload.node_id）\n"
            "- undo / redo: 撤销 / 重做\n\n"
            "【变量】\n"
            "- add_variable: 新增变量（payload.name, payload.value, payload.type, payload.scope）\n"
            "- update_variable: 更新变量值（payload.name, payload.value）\n"
            "- delete_variable: 删除变量（payload.name）\n"
            "- rename_variable: 重命名变量（payload.old_name, payload.new_name）\n"
            "- list_variables: 列出所有变量\n\n"
            "【日志/数据/资源】\n"
            "- clear_logs: 清空日志\n"
            "- clear_data: 清空数据表格\n"
            "- export_logs: 下载日志为文本文件\n"
            "- download_data: 下载数据表为 CSV\n"
            "- upload_excel / upload_image: 触发文件选择上传\n"
            "- set_verbose_log: 切换详细日志（payload.enabled=true|false）\n"
            "- set_max_log_count: 设置日志最大条数（payload.count）\n"
            "- add_log: 添加自定义日志条目（payload.level, payload.message）\n\n"
            "【底栏 Tab 切换】\n"
            "- switch_bottom_panel: 切换底栏 tab（payload.tab='logs'|'data'|'variables'|'assets'|'images'）\n\n"
            "【弹窗 / 面板 - 打开/关闭】\n"
            "- open_global_config / close_global_config: 全局配置对话框\n"
            "- open_local_workflow_dialog / close_local_workflow_dialog: 本地工作流（打开列表）\n"
            "- open_scheduled_tasks / close_scheduled_tasks: 计划任务\n"
            "- open_documentation / close_documentation: 使用文档\n"
            "- open_workflow_hub / close_workflow_hub: 工作流仓库\n"
            "- open_auto_browser / close_auto_browser: 自动化浏览器\n"
            "- open_phone_mirror / close_phone_mirror: 手机投屏\n"
            "- open_variable_tracking / close_variable_tracking: 变量追踪面板\n"
            "- open_export_dialog: 打开导出对话框\n"
            "- open_module_search: 打开画布顶部模块搜索框\n"
            "- take_screenshot: 触发系统截图工具\n\n"
            "【全局配置】\n"
            "- get_global_config: 读取当前全部全局配置\n"
            "- update_global_config: 更新某段配置（payload.section, payload.values）\n"
            "  section 可选：system / ai / aiAssistant / aiScraper / email / browser / database / qq / feishu / display / workflow\n\n"
            "【提示】\n"
            "- show_toast: 显示提示消息（payload.message, payload.type）\n\n"
            "调用方式示例：\n"
            "  {action: 'switch_bottom_panel', payload: {tab: 'data'}}\n"
            "  {action: 'run_workflow_headless'}\n"
            "  {action: 'export_workflow', payload: {format: 'playwright'}}\n"
            "前端会同步执行并返回结果，你可以基于返回结果继续后续动作。"
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

def _coerce_arguments(skill: "Skill", arguments: dict[str, Any]) -> dict[str, Any]:
    """LLM 偶尔会把数组/对象类型的参数二次 JSON 序列化为字符串。
    根据 skill 的 parameters schema 自动把字符串还原成对应的 list/dict。

    若解析失败会在 dict 中添加 _coerce_warnings 字段，但保留原值，由 handler 报错。
    """
    if not isinstance(arguments, dict):
        return arguments
    props = (skill.parameters or {}).get("properties") or {}
    if not isinstance(props, dict):
        return arguments
    fixed = dict(arguments)
    warnings: list[str] = []
    for key, schema in props.items():
        if key not in fixed:
            continue
        v = fixed[key]
        expected = schema.get("type") if isinstance(schema, dict) else None
        if expected in ("array", "object") and isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                fixed[key] = [] if expected == "array" else {}
                continue
            # 尝试 1：直接 json.loads
            try:
                parsed = json.loads(stripped)
                fixed[key] = parsed
                continue
            except Exception:
                pass
            # 尝试 2：去掉可能的代码块 ``` 或前后空白
            cleaned = stripped
            if cleaned.startswith("```"):
                # 去掉 ```json / ``` 头尾
                cleaned = cleaned.split("```", 2)
                cleaned = cleaned[1] if len(cleaned) > 1 else stripped
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip().rstrip("`").strip()
            try:
                parsed = json.loads(cleaned)
                fixed[key] = parsed
                continue
            except Exception as e:
                warnings.append(f"参数 {key} 应为 {expected}，但传入了无法解析的字符串：{e}")
    if warnings:
        # 日志记录，让用户能从 backend stdout 看到原因
        for w in warnings:
            print(f"[execute_skill] {skill.name}: {w}")
    return fixed


async def execute_skill(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """调度执行某个 Skill"""
    skill = registry.get(name)
    if skill is None:
        return {"error": f"未知工具: {name}"}
    try:
        # 兼容部分 LLM 把 array/object 参数二次序列化为字符串的 bug
        coerced = _coerce_arguments(skill, arguments or {})
        result = await skill.handler(**coerced)
        return {"success": True, "result": result}
    except TypeError as e:
        return {"error": f"参数错误: {e}"}
    except Exception as e:
        return {"error": f"执行失败: {e}"}
