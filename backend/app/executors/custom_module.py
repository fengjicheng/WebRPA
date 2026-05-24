"""
自定义模块执行器
"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from typing import Dict, Any
import json
from pathlib import Path
import os
import re


# 自定义模块存储目录（使用绝对路径，避免依赖 cwd）
# 该目录与 custom_modules.py API 保持一致
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
CUSTOM_MODULES_DIR = _BACKEND_DIR / "data" / "custom_modules"


# 校验 module_id 是否合法（与 api/custom_modules.py 保持一致：字母/数字/下划线/连字符/中文）
_MODULE_ID_PATTERN = re.compile(r'^[A-Za-z0-9_\-\u4e00-\u9fa5]+$')


def load_custom_module_definition(module_id: str) -> Dict[str, Any]:
    """加载自定义模块定义
    
    防御措施：
    - 校验 module_id 只能包含安全字符
    - 用 resolve() 后比较前缀防止路径穿越
    """
    if not module_id or len(module_id) > 200 or not _MODULE_ID_PATTERN.match(module_id):
        raise FileNotFoundError(f"自定义模块ID无效: {module_id}")
    
    base = CUSTOM_MODULES_DIR.resolve()
    file_path = (CUSTOM_MODULES_DIR / f"{module_id}.json").resolve()
    
    # 防止路径穿越：要求 file_path 在 base 内
    try:
        file_path.relative_to(base)
    except ValueError:
        raise FileNotFoundError(f"自定义模块路径不安全: {module_id}")
    
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
