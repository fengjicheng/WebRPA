"""WPS 多维表格自动化模块执行器

对标飞书多维表格模块，接入金山 WPS 开放平台（open.wps.cn）的多维表格（dbsheet）能力。

鉴权：WPS 开放平台使用 应用 AK/SK + WPS-4 HMAC-SHA256 签名。
用户需要先在 https://open.wps.cn 创建应用，拿到 AK / SK。

注意：WPS 多维表格的 records 接口路径与字段可能随 WPS 平台版本调整，
本执行器把 base_url / 接口路径做成可配置（baseUrl 字段），方便按实际文档微调。
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Optional, Dict, List

import httpx

from app.executors.base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor


DEFAULT_WPS_BASE = "https://openapi.wps.cn"


class WpsClient:
    """WPS 开放平台 API 客户端（WPS-4 ak/sk 签名）"""

    def __init__(self, ak: str, sk: str, base_url: str = DEFAULT_WPS_BASE):
        self.ak = ak
        self.sk = sk
        self.base_url = (base_url or DEFAULT_WPS_BASE).rstrip("/")

    def _sign_headers(self, method: str, uri: str, body_bytes: bytes,
                      content_type: str = "application/json") -> Dict[str, str]:
        """生成 WPS-4 签名头。

        规范化串： method + uri + content_type + date + content_md5
        再做 sha256，最后用 sk 做 hmac-sha256，hex 输出。
        """
        date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        content_md5 = hashlib.md5(body_bytes or b"").hexdigest()
        canonical = f"{method.upper()}{uri}{content_type}{date}{content_md5}"
        sha256_hex = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        signature = hmac.new(
            self.sk.encode("utf-8"),
            sha256_hex.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "Content-Type": content_type,
            "Date": date,
            "Content-Md5": content_md5,
            "Authorization": f"WPS-4 {self.ak}:{signature}",
        }

    async def request(self, method: str, uri: str, json_body: Optional[dict] = None,
                     params: Optional[dict] = None) -> Dict:
        body_bytes = b""
        if json_body is not None:
            body_bytes = json.dumps(json_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers = self._sign_headers(method, uri, body_bytes)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(
                method=method,
                url=f"{self.base_url}{uri}",
                headers=headers,
                content=body_bytes if json_body is not None else None,
                params=params,
            )
            try:
                return resp.json()
            except Exception:
                return {"_status": resp.status_code, "_text": resp.text}


def _is_ok(result: dict) -> bool:
    """WPS 返回判定：code==0 或 result=='ok' 视为成功"""
    if not isinstance(result, dict):
        return False
    if result.get("code") in (0, "0", None) and "error" not in result:
        return result.get("code") == 0 or result.get("result") in ("ok", None)
    return result.get("code") == 0


@register_executor
class WpsBitableWriteExecutor(ModuleExecutor):
    """WPS 多维表格写入执行器"""

    @property
    def module_type(self) -> str:
        return "wps_bitable_write"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            ak = context.resolve_value(config.get("ak", ""))
            sk = context.resolve_value(config.get("sk", ""))
            base_url = context.resolve_value(config.get("baseUrl", "")) or DEFAULT_WPS_BASE
            file_id = context.resolve_value(config.get("fileId", ""))
            sheet_id = context.resolve_value(config.get("sheetId", ""))

            if not all([ak, sk, file_id, sheet_id]):
                return ModuleResult(success=False, message="WPS 配置不完整（需要 AK、SK、文件ID、表ID）", error="配置不完整")

            # 准备要写入的记录
            data_source = config.get("dataSource", "manual")
            if data_source == "manual":
                fields = config.get("fields", {})
                record = {k: context.resolve_value(v) for k, v in fields.items()}
                records = [record]
            else:
                variable_name = config.get("variableName", "")
                data = context.get_variable(variable_name)
                if not data:
                    return ModuleResult(success=False, message=f"变量 {variable_name} 不存在或为空", error="数据源为空")
                records = [data] if isinstance(data, dict) else (data if isinstance(data, list) else None)
                if records is None:
                    return ModuleResult(success=False, message="数据格式错误，应为字典或字典列表", error="数据格式错误")

            client = WpsClient(ak, sk, base_url)
            uri = f"/v7/dbsheets/{file_id}/sheets/{sheet_id}/records"
            payload = {"records": [{"fields": r} for r in records]}
            result = await client.request("POST", uri, json_body=payload)

            if _is_ok(result):
                return ModuleResult(success=True, message=f"成功写入 {len(records)} 条记录", data={"count": len(records), "response": result})
            return ModuleResult(success=False, message=f"WPS 多维表格写入失败: {result.get('msg') or result.get('error') or result}", error=str(result))
        except Exception as e:
            import traceback
            print(f"[WpsBitableWriteExecutor] 执行失败: {traceback.format_exc()}")
            return ModuleResult(success=False, message=f"WPS 多维表格写入失败: {e}", error=str(e))


@register_executor
class WpsBitableReadExecutor(ModuleExecutor):
    """WPS 多维表格读取执行器"""

    @property
    def module_type(self) -> str:
        return "wps_bitable_read"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            ak = context.resolve_value(config.get("ak", ""))
            sk = context.resolve_value(config.get("sk", ""))
            base_url = context.resolve_value(config.get("baseUrl", "")) or DEFAULT_WPS_BASE
            file_id = context.resolve_value(config.get("fileId", ""))
            sheet_id = context.resolve_value(config.get("sheetId", ""))
            variable_name = config.get("variableName", "wps_data")

            if not all([ak, sk, file_id, sheet_id]):
                return ModuleResult(success=False, message="WPS 配置不完整（需要 AK、SK、文件ID、表ID）", error="配置不完整")

            client = WpsClient(ak, sk, base_url)
            uri = f"/v7/dbsheets/{file_id}/sheets/{sheet_id}/records"

            all_records: List[dict] = []
            offset = 0
            page_size = 200
            while True:
                result = await client.request("GET", uri, params={"limit": page_size, "offset": offset})
                if not _is_ok(result):
                    return ModuleResult(success=False, message=f"读取 WPS 多维表格失败: {result.get('msg') or result.get('error') or result}", error=str(result))
                data = result.get("data", result)
                items = data.get("records") or data.get("items") or []
                for item in items:
                    all_records.append(item.get("fields", item))
                if len(items) < page_size:
                    break
                offset += page_size
                if offset > 100000:  # 安全上限
                    break

            context.set_variable(variable_name, all_records)
            return ModuleResult(success=True, message=f"成功读取 {len(all_records)} 条记录", data={"count": len(all_records), "records": all_records})
        except Exception as e:
            import traceback
            print(f"[WpsBitableReadExecutor] 执行失败: {traceback.format_exc()}")
            return ModuleResult(success=False, message=f"WPS 多维表格读取失败: {e}", error=str(e))
