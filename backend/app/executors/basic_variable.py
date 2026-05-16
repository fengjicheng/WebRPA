"""基础模块执行器 - 变量和工具相关"""
import asyncio
import re

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor, escape_css_selector, pw_wait_for_element
from .type_utils import to_int, to_float


@register_executor
class GetTimeExecutor(ModuleExecutor):
    """获取时间模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "get_time"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from datetime import datetime
        
        time_format = context.resolve_value(config.get('timeFormat', 'datetime'))
        custom_format = context.resolve_value(config.get('customFormat', ''))
        variable_name = config.get('variableName', '')
        
        if not variable_name:
            return ModuleResult(success=False, error="变量名不能为空")
        
        try:
            now = datetime.now()
            
            if time_format == 'datetime':
                result = now.strftime('%Y-%m-%d %H:%M:%S')
            elif time_format == 'date':
                result = now.strftime('%Y-%m-%d')
            elif time_format == 'time':
                result = now.strftime('%H:%M:%S')
            elif time_format == 'timestamp':
                result = int(now.timestamp() * 1000)
            elif time_format == 'iso8601':
                # ISO 8601 格式：2024-03-15T14:30:45.123456+08:00
                result = now.isoformat()
            elif time_format == 'iso8601_utc':
                # ISO 8601 UTC格式：2024-03-15T06:30:45.123456Z
                from datetime import timezone
                result = now.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
            elif time_format == 'custom' and custom_format:
                result = now.strftime(custom_format)
            else:
                result = now.strftime('%Y-%m-%d %H:%M:%S')
            
            context.set_variable(variable_name, result)
            
            return ModuleResult(success=True, message=f"已获取时间: {result}", data={'value': result})
        except Exception as e:
            return ModuleResult(success=False, error=f"获取时间失败: {str(e)}")


@register_executor
class IncrementDecrementExecutor(ModuleExecutor):
    """自增自减模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "increment_decrement"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        自增自减模块 - 对变量进行自增或自减操作
        配置项：
        - variableName: 变量名
        - operation: 操作类型（increment/decrement）
        - step: 步长（默认为1）
        """
        variable_name = context.resolve_value(config.get('variableName', ''))
        operation = context.resolve_value(config.get('operation', 'increment'))
        step = context.resolve_value(config.get('step', 1))
        
        if not variable_name:
            return ModuleResult(success=False, error="变量名不能为空")
        
        try:
            # 转换步长为数字
            if isinstance(step, str):
                try:
                    if '.' in step:
                        step = float(step)
                    else:
                        step = int(step)
                except ValueError:
                    return ModuleResult(success=False, error=f"步长必须是数字: {step}")
            
            # 获取当前变量值
            current_value = context.get_variable(variable_name)
            
            # 如果变量不存在，初始化为0
            if current_value is None:
                current_value = 0
            
            # 转换当前值为数字
            if isinstance(current_value, str):
                try:
                    if '.' in current_value:
                        current_value = float(current_value)
                    else:
                        current_value = int(current_value)
                except ValueError:
                    return ModuleResult(success=False, error=f"变量 '{variable_name}' 的值不是数字: {current_value}")
            
            # 确保当前值是数字类型
            if not isinstance(current_value, (int, float)):
                return ModuleResult(success=False, error=f"变量 '{variable_name}' 的值不是数字类型")
            
            # 执行自增或自减
            if operation == 'increment':
                new_value = current_value + step
                operation_label = "自增"
            elif operation == 'decrement':
                new_value = current_value - step
                operation_label = "自减"
            else:
                return ModuleResult(success=False, error=f"未知的操作类型: {operation}")
            
            # 保存新值
            context.set_variable(variable_name, new_value)
            
            return ModuleResult(
                success=True,
                message=f"{operation_label}: {variable_name} = {current_value} → {new_value} (步长: {step})",
                data={'variable': variable_name, 'old_value': current_value, 'new_value': new_value, 'step': step}
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"自增自减失败: {str(e)}")
