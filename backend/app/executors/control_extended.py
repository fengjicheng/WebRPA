"""扩展的控制流模块执行器"""

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)


@register_executor
class InfiniteLoopExecutor(ModuleExecutor):
    """无限循环模块执行器"""

    @property
    def module_type(self) -> str:
        return "infinite_loop"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        无限循环模块 - 创建一个无限循环，需要使用"跳出循环"模块来退出
        配置项：
        - indexVariable: 循环索引变量名（默认为loop_index）
        """
        index_variable = config.get('indexVariable', 'loop_index')
        
        # 创建一个非常大的循环次数来模拟无限循环
        # 实际上会受到max_iterations的限制
        loop_state = {
            'type': 'infinite',
            'count': 999999999,  # 设置一个极大的数
            'condition': '',
            'max_iterations': 999999999,
            'index_variable': index_variable,
            'current_index': 0,
            'start_value': 0,
            'end_value': 999999999,
            'step_value': 1,
        }

        context.loop_stack.append(loop_state)
        context.set_variable(index_variable, 0)

        return ModuleResult(
            success=True,
            message="开始无限循环（使用'跳出循环'模块退出）",
            data=loop_state
        )


@register_executor
class ForeachDictExecutor(ModuleExecutor):
    """遍历字典模块执行器"""

    @property
    def module_type(self) -> str:
        return "foreach_dict"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        遍历字典模块 - 遍历字典的键值对
        配置项：
        - dictVariable: 字典变量名
        - keyVariable: 键变量名（默认为key）
        - valueVariable: 值变量名（默认为value）
        - indexVariable: 索引变量名（默认为index）
        """
        dict_variable = config.get('dictVariable', '')
        key_variable = config.get('keyVariable', 'key')
        value_variable = config.get('valueVariable', 'value')
        index_variable = config.get('indexVariable', 'index')
        
        if not dict_variable:
            return ModuleResult(success=False, error="字典变量名不能为空")
        
        dict_data = context.get_variable(dict_variable)
        
        if dict_data is None:
            return ModuleResult(success=False, error=f"变量 '{dict_variable}' 不存在")
        
        if not isinstance(dict_data, dict):
            return ModuleResult(success=False, error=f"变量 '{dict_variable}' 不是字典类型")
        
        # 将字典转换为键值对列表
        items = list(dict_data.items())
        
        loop_state = {
            'type': 'foreach_dict',
            'data': items,
            'key_variable': key_variable,
            'value_variable': value_variable,
            'index_variable': index_variable,
            'current_index': 0,
        }

        context.loop_stack.append(loop_state)

        if len(items) > 0:
            first_key, first_value = items[0]
            context.set_variable(key_variable, first_key)
            context.set_variable(value_variable, first_value)
            context.set_variable(index_variable, 0)

        return ModuleResult(
            success=True,
            message=f"开始遍历字典 (共 {len(items)} 项)",
            data=loop_state
        )


@register_executor
class StopWorkflowExecutor(ModuleExecutor):
    """强制停止工作流执行模块"""

    @property
    def module_type(self) -> str:
        return "stop_workflow"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        强制停止工作流执行 - 立即停止整个工作流，不再执行后续模块
        配置项：
        - stopReason: 停止原因（可选）
        """
        stop_reason = config.get('stopReason', '用户主动停止工作流')
        
        # 设置工作流停止标志
        context.stop_workflow = True
        context.stop_reason = stop_reason
        
        return ModuleResult(
            success=True,
            message=f"工作流已停止: {stop_reason}",
            data={'reason': stop_reason}
        )
