"""断言/检查点模块执行器

用于流程稳定性工程：在流程关键节点插入断言，校验变量/页面元素/表达式是否满足预期。
不满足时可选择「中断流程 / 仅警告继续 / 静默继续」，并把结果布尔值写入变量。

模块类型: assert_checkpoint
"""
from __future__ import annotations

import re

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
    format_selector,
)


def _to_number(value):
    """尽力把值转成数字，失败返回 None"""
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return value
        s = str(value).strip().replace(',', '')
        if s == '':
            return None
        return float(s)
    except (ValueError, TypeError):
        return None


def _is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ''
    if isinstance(value, (list, dict, tuple)):
        return len(value) == 0
    return False


def _compare(left, right, operator: str):
    """按运算符比较左右值，返回 (结果bool, 错误信息或None)"""
    op = (operator or '==').strip()

    if op in ('==', 'equals'):
        return str(left) == str(right), None
    if op in ('!=', 'not_equals'):
        return str(left) != str(right), None
    if op in ('isEmpty', 'is_empty'):
        return _is_empty(left), None
    if op in ('isNotEmpty', 'is_not_empty'):
        return not _is_empty(left), None
    if op in ('contains',):
        return str(right) in str(left), None
    if op in ('not_contains',):
        return str(right) not in str(left), None
    if op in ('startswith', 'starts_with'):
        return str(left).startswith(str(right)), None
    if op in ('endswith', 'ends_with'):
        return str(left).endswith(str(right)), None
    if op in ('matches', 'regex'):
        try:
            return re.search(str(right), str(left)) is not None, None
        except re.error as e:
            return False, f"正则表达式无效: {e}"
    if op in ('>', '<', '>=', '<='):
        ln, rn = _to_number(left), _to_number(right)
        if ln is None or rn is None:
            return False, f"运算符 '{op}' 需要数值，但左值='{left}'、右值='{right}' 无法转为数字"
        if op == '>':
            return ln > rn, None
        if op == '<':
            return ln < rn, None
        if op == '>=':
            return ln >= rn, None
        return ln <= rn, None
    return False, f"未知运算符: {op}"


@register_executor
class AssertCheckpointExecutor(ModuleExecutor):
    """断言/检查点：校验变量、页面元素或表达式是否满足预期"""

    @property
    def module_type(self) -> str:
        return "assert_checkpoint"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        check_type = (context.resolve_value(config.get('checkType', 'variable')) or 'variable').strip()
        on_fail = (config.get('onFail', 'stop') or 'stop').strip()  # stop / warn / continue
        var_name = config.get('variableName', '') or ''
        label = config.get('message', '') or ''

        passed = False
        detail = ''
        err = None

        if check_type == 'variable':
            passed, detail, err = await self._check_variable(config, context)
        elif check_type == 'element':
            passed, detail, err = await self._check_element(config, context)
        elif check_type == 'expression':
            passed, detail, err = self._check_expression(config, context)
        else:
            return ModuleResult(success=False, error=f"未知检查类型: {check_type}")

        if err:
            return ModuleResult(success=False, error=err)

        if var_name:
            context.set_variable(var_name, passed)

        title = label or detail
        if passed:
            return ModuleResult(success=True, message=f"断言通过: {title}", data={'passed': True, 'detail': detail})

        # 断言失败
        fail_msg = f"断言失败: {title}"
        if on_fail == 'stop':
            return ModuleResult(success=False, error=fail_msg, data={'passed': False, 'detail': detail})
        try:
            await context.send_progress(fail_msg, "warning")
        except Exception:
            pass
        return ModuleResult(success=True, message=f"{fail_msg}（已设为继续）", data={'passed': False, 'detail': detail}, skipped=(on_fail == 'continue'))


    async def _check_variable(self, config: dict, context: ExecutionContext):
        """校验变量/字面量与期望值的关系"""
        raw_left = config.get('actualValue')
        if raw_left in (None, ''):
            raw_left = config.get('leftValue', '')
        raw_right = config.get('expectedValue')
        if raw_right is None:
            raw_right = config.get('rightValue', '')
        operator = (config.get('operator', '==') or '==').strip()

        left = context.resolve_value(raw_left)
        right = context.resolve_value(raw_right)
        ok, err = _compare(left, right, operator)
        if err:
            return False, '', err
        detail = f"{left!r} {operator} {right!r}"
        if operator in ('isEmpty', 'is_empty', 'isNotEmpty', 'is_not_empty'):
            detail = f"{left!r} {operator}"
        return ok, detail, None

    def _check_expression(self, config: dict, context: ExecutionContext):
        """校验表达式真值：解析 {变量} 后判断是否为真"""
        raw = config.get('expression', '')
        value = context.resolve_value(raw)
        if isinstance(value, str):
            s = value.strip().lower()
            if s in ('false', '0', 'no', '', 'none', 'null'):
                ok = False
            elif s in ('true', '1', 'yes'):
                ok = True
            else:
                ok = True
        elif isinstance(value, (int, float)):
            ok = value != 0
        elif isinstance(value, (list, dict, tuple)):
            ok = len(value) > 0
        elif value is None:
            ok = False
        else:
            ok = bool(value)
        return ok, f"表达式 {raw!r} → {value!r}", None


    async def _check_element(self, config: dict, context: ExecutionContext):
        """校验页面元素状态（需先打开网页）"""
        if context.page is None:
            return False, '', "没有打开的页面，请先使用'打开网页'模块"
        selector = context.resolve_value(config.get('selector', '') or config.get('leftValue', ''))
        if not selector:
            return False, '', "元素选择器不能为空"
        element_check = (config.get('elementCheck', 'exists') or 'exists').strip()
        expected_text = context.resolve_value(config.get('expectedText', ''))

        try:
            await context.switch_to_latest_page()
            locator = context.page.locator(format_selector(selector))
            count = await locator.count()

            if element_check == 'exists':
                return count > 0, f"元素 {selector!r} 存在", None
            if element_check == 'not_exists':
                return count == 0, f"元素 {selector!r} 不存在", None
            if element_check == 'visible':
                vis = count > 0 and await locator.first.is_visible()
                return vis, f"元素 {selector!r} 可见", None
            if element_check == 'hidden':
                vis = count > 0 and await locator.first.is_visible()
                return (not vis), f"元素 {selector!r} 隐藏", None

            text = ''
            if count > 0:
                text = (await locator.first.inner_text()) or ''
            if element_check == 'text_contains':
                return str(expected_text) in text, f"元素文本包含 {expected_text!r}（实际 {text[:50]!r}）", None
            if element_check == 'text_equals':
                return text.strip() == str(expected_text).strip(), f"元素文本等于 {expected_text!r}（实际 {text[:50]!r}）", None
            return False, '', f"未知元素检查: {element_check}"
        except Exception as e:
            return False, '', f"元素断言异常: {e}"
