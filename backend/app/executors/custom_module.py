"""
自定义模块执行器
"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from typing import Dict, Any
import json
from pathlib import Path


# 自定义模块存储目录
CUSTOM_MODULES_DIR = Path("backend/data/custom_modules")


def load_custom_module_definition(module_id: str) -> Dict[str, Any]:
    """加载自定义模块定义"""
    file_path = CUSTOM_MODULES_DIR / f"{module_id}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"自定义模块不存在: {module_id}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@register_executor
class CustomModuleExecutor(ModuleExecutor):
    """自定义模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "custom_module"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        执行自定义模块
        config包含:
        - customModuleId: 自定义模块ID
        - parameterValues: 用户传入的参数值（字典）
        """
        try:
            custom_module_id = config.get('customModuleId')
            if not custom_module_id:
                return ModuleResult(success=False, error="未指定自定义模块ID")
            
            # 加载自定义模块定义
            try:
                module_def = load_custom_module_definition(custom_module_id)
            except FileNotFoundError as e:
                return ModuleResult(success=False, error=str(e))
            
            # 获取用户传入的参数
            user_params = config.get('parameterValues', {})
            
            # 构建参数映射（参数名 -> 参数值）
            parameter_mappings = {}
            for param_def in module_def.get('parameters', []):
                param_name = param_def['name']
                # 优先使用用户传入的值，否则使用默认值
                param_value = user_params.get(param_name, param_def.get('default_value', ''))
                parameter_mappings[param_name] = param_value
            
            # 构建输出映射（输出名 -> 变量名）
            output_mappings = {}
            for output_def in module_def.get('outputs', []):
                output_name = output_def['name']
                # 输出变量名就是输出名本身
                output_mappings[output_name] = output_name
            
            # 获取内部工作流定义
            workflow = module_def.get('workflow', {})
            nodes = workflow.get('nodes', [])
            edges = workflow.get('edges', [])
            
            if not nodes:
                return ModuleResult(success=False, error="自定义模块内部工作流为空")
            
            # 返回特殊标记，让workflow_executor知道这是一个自定义模块
            return ModuleResult(
                success=True,
                message=f"自定义模块 '{module_def.get('display_name')}' 准备执行",
                data={
                    'is_custom_module': True,
                    'module_id': custom_module_id,
                    'module_name': module_def.get('display_name'),
                    'workflow_definition': workflow,
                    'parameter_mappings': parameter_mappings,
                    'output_mappings': output_mappings
                }
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"执行自定义模块失败: {str(e)}")
