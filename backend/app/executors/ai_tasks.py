# -*- coding: utf-8 -*-
"""AI 数据处理任务模块执行器

把大模型能力沉淀成"开箱即用"的工作流节点，让用户无需手写提示词就能完成常见 AI 任务：
- ai_extract     结构化信息抽取（从任意文本抽成 JSON）
- ai_classify    文本分类（归入给定类别之一）
- ai_summarize   文本摘要
- ai_translate   文本翻译
- ai_sentiment   情感分析（正面/负面/中性 + 置信度 + 理由）

设计原则：
- 复用与 ai_chat 一致的 OpenAI 兼容调用（apiUrl/apiKey/model/temperature/maxTokens），
  因此前端可直接套用全局 AI 配置，并支持 fallbackModels 失败自动切换。
- 任务模块内置精心设计的提示词，强制结构化输出，并对返回做健壮解析。
"""
import json
import re
from typing import Any

import httpx

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float


def _normalize_chat_url(api_url: str) -> str:
    url = (api_url or "").strip()
    if not url:
        return url
    if "/chat/completions" in url or "/completions" in url:
        return url
    url = url.rstrip("/")
    if not url.endswith("/v1") and "/v1/" not in url:
        return url + "/v1/chat/completions"
    return url + "/chat/completions"


async def _chat_once(config: dict, context: ExecutionContext, system_prompt: str, user_prompt: str) -> tuple[bool, str, str]:
    """发起一次 OpenAI 兼容对话，返回 (success, content, error)。"""
    api_url = context.resolve_value(config.get("apiUrl", ""))
    api_key = context.resolve_value(config.get("apiKey", ""))
    model = context.resolve_value(config.get("model", ""))
    temperature = to_float(config.get("temperature", 0.2), 0.2, context)
    max_tokens = to_int(config.get("maxTokens", 2000), 2000, context)

    if not api_url:
        return False, "", "API地址不能为空（请在全局配置或节点中填写 AI 接口）"
    if not model:
        return False, "", "模型名称不能为空"

    url = _normalize_chat_url(api_url)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    body = {"model": model, "messages": messages, "temperature": temperature,
            "max_tokens": max_tokens, "stream": False}
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(url, json=body, headers=headers)
        if resp.status_code != 200:
            msg = resp.text
            try:
                ed = resp.json()
                if "error" in ed:
                    msg = ed["error"].get("message", msg)
            except Exception:
                pass
            return False, "", f"API请求失败 ({resp.status_code}): {msg}"
        result = resp.json()
        content = ""
        if "choices" in result and result["choices"]:
            m = result["choices"][0].get("message", {}) or {}
            content = m.get("content") or m.get("reasoning_content") or ""
        elif "message" in result:
            content = (result.get("message", {}) or {}).get("content", "")
        if not content:
            return False, "", "AI返回内容为空"
        return True, content.strip(), ""
    except httpx.TimeoutException:
        return False, "", "API请求超时"
    except httpx.ConnectError:
        return False, "", "无法连接到API服务器"
    except Exception as e:
        return False, "", f"AI调用失败: {e}"


async def _chat_with_fallback(config: dict, context: ExecutionContext, system_prompt: str, user_prompt: str) -> tuple[bool, str, str]:
    """带 fallbackModels 的多模型自动切换。"""
    fallbacks = config.get("fallbackModels") or []
    candidates = [config]
    if isinstance(fallbacks, list):
        for fb in fallbacks:
            if isinstance(fb, dict) and fb.get("apiUrl") and fb.get("model"):
                cand = {**config, "apiUrl": fb.get("apiUrl"), "apiKey": fb.get("apiKey", ""), "model": fb.get("model")}
                candidates.append(cand)
    last_err = "所有候选模型均调用失败"
    for cand in candidates:
        ok, content, err = await _chat_once(cand, context, system_prompt, user_prompt)
        if ok:
            return True, content, ""
        last_err = err
    return False, "", last_err


def _extract_json(text: str) -> Any:
    """从模型返回里健壮地抽取 JSON（兼容 ```json 代码块、前后多余文字）。"""
    if not text:
        return None
    s = text.strip()
    # 去掉 ```json ... ``` 围栏
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", s)
    if fence:
        s = fence.group(1).strip()
    # 直接尝试
    try:
        return json.loads(s)
    except Exception:
        pass
    # 截取第一个 { 或 [ 到最后一个 } 或 ]
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        i = s.find(open_ch)
        j = s.rfind(close_ch)
        if i != -1 and j != -1 and j > i:
            try:
                return json.loads(s[i:j + 1])
            except Exception:
                continue
    return None


@register_executor
class AIExtractExecutor(ModuleExecutor):
    """AI 结构化抽取：从任意文本中按指定字段抽取为 JSON 对象"""

    @property
    def module_type(self) -> str:
        return "ai_extract"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        text = context.resolve_value(config.get("inputText", ""))
        fields_raw = context.resolve_value(config.get("fields", ""))
        var = config.get("variableName", "") or config.get("resultVariable", "")
        if not text or not str(text).strip():
            return ModuleResult(success=False, error="待抽取文本(inputText)不能为空")
        if not fields_raw or not str(fields_raw).strip():
            return ModuleResult(success=False, error="请填写要抽取的字段(fields)，如 姓名,电话,地址 或 JSON 描述")
        # 字段可以是逗号分隔，也可以是 JSON（字段名->说明）
        fields_desc = str(fields_raw).strip()
        sys_p = (
            "你是一个严谨的信息抽取引擎。请从用户提供的文本中抽取指定字段，"
            "只输出一个 JSON 对象，键为字段名，值为抽取到的内容；"
            "找不到的字段值用空字符串 \"\"。不要输出任何解释、不要用代码块包裹。"
        )
        user_p = f"【要抽取的字段】\n{fields_desc}\n\n【原始文本】\n{text}"
        ok, content, err = await _chat_with_fallback(config, context, sys_p, user_p)
        if not ok:
            return ModuleResult(success=False, error=err)
        data = _extract_json(content)
        if data is None:
            # 兜底：把原始文本存入变量
            if var:
                context.set_variable(var, content)
            return ModuleResult(success=True, message="已抽取（未解析为JSON，返回原始文本）",
                                data={"raw": content})
        if var:
            context.set_variable(var, data)
        return ModuleResult(success=True, message=f"已抽取 {len(data) if isinstance(data, dict) else ''} 个字段",
                            data={"result": data})


@register_executor
class AIClassifyExecutor(ModuleExecutor):
    """AI 文本分类：把文本归入给定类别之一"""

    @property
    def module_type(self) -> str:
        return "ai_classify"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        text = context.resolve_value(config.get("inputText", ""))
        categories_raw = context.resolve_value(config.get("categories", ""))
        var = config.get("variableName", "") or config.get("resultVariable", "")
        if not text or not str(text).strip():
            return ModuleResult(success=False, error="待分类文本(inputText)不能为空")
        cats = [c.strip() for c in str(categories_raw).replace("，", ",").split(",") if c.strip()]
        if len(cats) < 2:
            return ModuleResult(success=False, error="请提供至少两个类别(categories)，逗号分隔")
        sys_p = (
            "你是一个精准的文本分类器。请把文本归入给定类别中最贴切的一个，"
            "只输出 JSON：{\"category\":\"类别名\",\"confidence\":0~1,\"reason\":\"简短理由\"}。"
            "category 必须严格是给定类别之一，不要新造类别，不要用代码块包裹。"
        )
        user_p = f"【可选类别】{', '.join(cats)}\n\n【文本】\n{text}"
        ok, content, err = await _chat_with_fallback(config, context, sys_p, user_p)
        if not ok:
            return ModuleResult(success=False, error=err)
        data = _extract_json(content)
        category = ""
        if isinstance(data, dict):
            category = str(data.get("category", "")).strip()
        if category not in cats:
            # 兜底：在返回里找哪个类别名出现了
            for c in cats:
                if c in content:
                    category = c
                    break
        if var:
            context.set_variable(var, category or (data if data else content))
        return ModuleResult(success=True, message=f"分类结果: {category or '未识别'}",
                            data={"category": category, "detail": data})


@register_executor
class AISummarizeExecutor(ModuleExecutor):
    """AI 文本摘要：把长文本压缩成摘要（可指定字数与风格）"""

    @property
    def module_type(self) -> str:
        return "ai_summarize"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        text = context.resolve_value(config.get("inputText", ""))
        max_words = to_int(config.get("maxWords", 200), 200, context)
        style = context.resolve_value(config.get("style", "")) or ""
        var = config.get("variableName", "") or config.get("resultVariable", "")
        if not text or not str(text).strip():
            return ModuleResult(success=False, error="待摘要文本(inputText)不能为空")
        style_hint = f"风格要求：{style}。" if style else ""
        sys_p = (
            f"你是一个专业的摘要助手。请用中文把文本浓缩成不超过 {max_words} 字的摘要，"
            f"保留关键信息与结论，去掉冗余。{style_hint}只输出摘要正文，不要前缀、不要解释。"
        )
        ok, content, err = await _chat_with_fallback(config, context, sys_p, str(text))
        if not ok:
            return ModuleResult(success=False, error=err)
        if var:
            context.set_variable(var, content)
        disp = content[:100] + "…" if len(content) > 100 else content
        return ModuleResult(success=True, message=f"摘要: {disp}", data={"summary": content})


@register_executor
class AITranslateExecutor(ModuleExecutor):
    """AI 翻译：把文本翻译成目标语言"""

    @property
    def module_type(self) -> str:
        return "ai_translate"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        text = context.resolve_value(config.get("inputText", ""))
        target_lang = context.resolve_value(config.get("targetLang", "英文")) or "英文"
        var = config.get("variableName", "") or config.get("resultVariable", "")
        if not text or not str(text).strip():
            return ModuleResult(success=False, error="待翻译文本(inputText)不能为空")
        sys_p = (
            f"你是一个专业翻译。请把用户文本准确、地道地翻译成{target_lang}，"
            "保留原文的格式与换行。只输出译文，不要原文、不要解释、不要拼音。"
        )
        ok, content, err = await _chat_with_fallback(config, context, sys_p, str(text))
        if not ok:
            return ModuleResult(success=False, error=err)
        if var:
            context.set_variable(var, content)
        disp = content[:100] + "…" if len(content) > 100 else content
        return ModuleResult(success=True, message=f"译文: {disp}", data={"translation": content, "targetLang": target_lang})


@register_executor
class AISentimentExecutor(ModuleExecutor):
    """AI 情感分析：判断文本情感倾向（正面/负面/中性）"""

    @property
    def module_type(self) -> str:
        return "ai_sentiment"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        text = context.resolve_value(config.get("inputText", ""))
        var = config.get("variableName", "") or config.get("resultVariable", "")
        if not text or not str(text).strip():
            return ModuleResult(success=False, error="待分析文本(inputText)不能为空")
        sys_p = (
            "你是情感分析引擎。判断文本的情感倾向，只输出 JSON："
            "{\"sentiment\":\"正面|负面|中性\",\"score\":-1~1,\"confidence\":0~1,\"reason\":\"简短理由\"}。"
            "score 越接近 1 越正面，越接近 -1 越负面。不要用代码块包裹。"
        )
        ok, content, err = await _chat_with_fallback(config, context, sys_p, str(text))
        if not ok:
            return ModuleResult(success=False, error=err)
        data = _extract_json(content)
        sentiment = ""
        if isinstance(data, dict):
            sentiment = str(data.get("sentiment", "")).strip()
        if not sentiment:
            for s in ("正面", "负面", "中性"):
                if s in content:
                    sentiment = s
                    break
        if var:
            context.set_variable(var, data if data else {"sentiment": sentiment, "raw": content})
        return ModuleResult(success=True, message=f"情感: {sentiment or '未识别'}",
                            data={"sentiment": sentiment, "detail": data})
