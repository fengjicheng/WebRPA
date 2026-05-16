"""
自定义模块API
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import json
import os
from pathlib import Path
from datetime import datetime

from app.models.custom_module import (
    CustomModule,
    CustomModuleCreate,
    CustomModuleUpdate,
    CustomModuleListResponse
)

router = APIRouter(prefix="/api/custom-modules", tags=["custom-modules"])

# 自定义模块存储目录
CUSTOM_MODULES_DIR = Path("backend/data/custom_modules")
CUSTOM_MODULES_DIR.mkdir(parents=True, exist_ok=True)


def _get_module_file_path(module_id: str) -> Path:
    """获取模块文件路径"""
    return CUSTOM_MODULES_DIR / f"{module_id}.json"


def _load_module(module_id: str) -> Optional[CustomModule]:
    """加载单个模块"""
    file_path = _get_module_file_path(module_id)
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return CustomModule(**data)
    except Exception as e:
        print(f"[CustomModules] 加载模块失败 {module_id}: {e}")
        return None


def _save_module(module: CustomModule):
    """保存模块"""
    file_path = _get_module_file_path(module.id)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(module.dict(), f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        print(f"[CustomModules] 保存模块失败 {module.id}: {e}")
        raise


def _load_all_modules() -> List[CustomModule]:
    """加载所有模块"""
    modules = []
    for file_path in CUSTOM_MODULES_DIR.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                modules.append(CustomModule(**data))
        except Exception as e:
            print(f"[CustomModules] 加载模块失败 {file_path}: {e}")
    return modules


@router.get("/", response_model=CustomModuleListResponse)
async def list_custom_modules(
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """获取自定义模块列表"""
    try:
        modules = _load_all_modules()
        
        # 过滤分类
        if category:
            modules = [m for m in modules if m.category == category]
        
        # 搜索过滤
        if search:
            search_lower = search.lower()
            modules = [
                m for m in modules
                if search_lower in m.display_name.lower() or
                   search_lower in m.name.lower() or
                   search_lower in m.description.lower() or
                   any(search_lower in tag.lower() for tag in m.tags)
            ]
        
        # 按更新时间倒序排序
        modules.sort(key=lambda x: x.updated_at, reverse=True)
        
        return CustomModuleListResponse(
            modules=modules,
            total=len(modules)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模块列表失败: {str(e)}")


@router.get("/{module_id}", response_model=CustomModule)
async def get_custom_module(module_id: str):
    """获取单个自定义模块"""
    module = _load_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    return module


@router.post("/", response_model=CustomModule)
async def create_custom_module(module_data: CustomModuleCreate):
    """创建自定义模块"""
    try:
        print(f"[CustomModules] 收到创建模块请求: {module_data.name}")
        print(f"[CustomModules] 模块数据: display_name={module_data.display_name}, category={module_data.category}")
        print(f"[CustomModules] 参数数量: {len(module_data.parameters)}, 输出数量: {len(module_data.outputs)}")
        print(f"[CustomModules] 工作流节点数: {len(module_data.workflow.get('nodes', []))}, 边数: {len(module_data.workflow.get('edges', []))}")
        
        # 验证工作流数据
        if not module_data.workflow:
            print("[CustomModules] ❌ 工作流数据为空")
            raise HTTPException(status_code=400, detail="工作流数据不能为空")
        
        if 'nodes' not in module_data.workflow or not module_data.workflow['nodes']:
            print("[CustomModules] ❌ 工作流节点为空")
            raise HTTPException(status_code=400, detail="工作流必须包含至少一个节点")
        
        # 验证节点数据完整性
        for i, node in enumerate(module_data.workflow['nodes']):
            if not isinstance(node, dict):
                print(f"[CustomModules] ❌ 节点 {i} 不是字典类型: {type(node)}")
                raise HTTPException(status_code=400, detail=f"节点 {i} 数据格式错误")
            
            required_fields = ['id', 'type', 'position', 'data']
            missing_fields = [f for f in required_fields if f not in node]
            if missing_fields:
                print(f"[CustomModules] ❌ 节点 {i} 缺少必需字段: {missing_fields}")
                print(f"[CustomModules] 节点数据: {node}")
                raise HTTPException(status_code=400, detail=f"节点 {i} 缺少必需字段: {', '.join(missing_fields)}")
        
        # 生成模块ID
        import uuid
        module_id = f"custom_{module_data.name}_{uuid.uuid4().hex[:8]}"
        print(f"[CustomModules] 生成模块ID: {module_id}")
        
        # 检查名称是否已存在
        existing_modules = _load_all_modules()
        if any(m.name == module_data.name for m in existing_modules):
            print(f"[CustomModules] ❌ 模块名称已存在: {module_data.name}")
            raise HTTPException(status_code=400, detail=f"模块名称 '{module_data.name}' 已存在")
        
        # 创建模块
        module = CustomModule(
            id=module_id,
            name=module_data.name,
            display_name=module_data.display_name,
            description=module_data.description,
            icon=module_data.icon,
            color=module_data.color,
            category=module_data.category,
            parameters=module_data.parameters,
            outputs=module_data.outputs,
            workflow=module_data.workflow,
            tags=module_data.tags,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        print(f"[CustomModules] 模块对象创建成功，准备保存")
        
        # 保存
        _save_module(module)
        
        print(f"[CustomModules] ✅ 模块保存成功: {module_id}")
        
        return module
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[CustomModules] ❌ 创建模块异常: {str(e)}")
        print(f"[CustomModules] 异常详情:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"创建模块失败: {str(e)}")


@router.put("/{module_id}", response_model=CustomModule)
async def update_custom_module(module_id: str, update_data: CustomModuleUpdate):
    """更新自定义模块"""
    try:
        # 加载现有模块
        module = _load_module(module_id)
        if not module:
            raise HTTPException(status_code=404, detail="模块不存在")
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(module, key, value)
        
        module.updated_at = datetime.now()
        
        # 保存
        _save_module(module)
        
        return module
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新模块失败: {str(e)}")


@router.delete("/{module_id}")
async def delete_custom_module(module_id: str):
    """删除自定义模块"""
    try:
        file_path = _get_module_file_path(module_id)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="模块不存在")
        
        # 删除文件
        file_path.unlink()
        
        return {"success": True, "message": "模块已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除模块失败: {str(e)}")


@router.post("/{module_id}/duplicate", response_model=CustomModule)
async def duplicate_custom_module(module_id: str, new_name: str):
    """复制自定义模块"""
    try:
        # 加载原模块
        original = _load_module(module_id)
        if not original:
            raise HTTPException(status_code=404, detail="模块不存在")
        
        # 生成新ID
        import uuid
        new_id = f"custom_{new_name}_{uuid.uuid4().hex[:8]}"
        
        # 创建副本
        duplicate = CustomModule(
            id=new_id,
            name=new_name,
            display_name=f"{original.display_name} (副本)",
            description=original.description,
            icon=original.icon,
            category=original.category,
            parameters=original.parameters,
            outputs=original.outputs,
            workflow=original.workflow,
            tags=original.tags,
            author=original.author,
            version=original.version,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存
        _save_module(duplicate)
        
        return duplicate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"复制模块失败: {str(e)}")


@router.post("/{module_id}/increment-usage")
async def increment_module_usage(module_id: str):
    """增加模块使用次数"""
    try:
        module = _load_module(module_id)
        if not module:
            raise HTTPException(status_code=404, detail="模块不存在")
        
        module.usage_count += 1
        _save_module(module)
        
        return {"success": True, "usage_count": module.usage_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新使用次数失败: {str(e)}")
