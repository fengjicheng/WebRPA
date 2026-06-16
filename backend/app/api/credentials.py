# -*- coding: utf-8 -*-
"""凭据库 API：管理本地加密凭据（口令、API Key、数据库密码等）。

安全约定：
- 列表接口只返回打码后的字段，绝不返回明文。
- 明文仅在工作流运行期由后端 credential_manager.get_field 解密注入。
"""
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import credential_manager

router = APIRouter(prefix="/api/credentials", tags=["credentials"])


class CredentialUpsert(BaseModel):
    name: str
    fields: Dict[str, str]
    description: Optional[str] = ""


class CredentialRename(BaseModel):
    old_name: str
    new_name: str


@router.get("")
async def list_credentials():
    """列出所有凭据（字段值打码）"""
    return {"success": True, "credentials": credential_manager.list_credentials()}


@router.get("/names")
async def credential_names():
    """仅返回凭据名列表（供节点配置的下拉选择）"""
    return {"success": True, "names": credential_manager.credential_names()}


@router.post("")
async def upsert_credential(req: CredentialUpsert):
    """新增或更新凭据。字段值留空表示保留原值（编辑场景）。"""
    try:
        res = credential_manager.upsert_credential(req.name, req.fields, req.description or "")
        return {"success": True, **res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rename")
async def rename_credential(req: CredentialRename):
    try:
        ok = credential_manager.rename_credential(req.old_name, req.new_name)
        if not ok:
            raise HTTPException(status_code=404, detail="凭据不存在")
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{name}")
async def delete_credential(name: str):
    ok = credential_manager.delete_credential(name)
    if not ok:
        raise HTTPException(status_code=404, detail="凭据不存在")
    return {"success": True}
