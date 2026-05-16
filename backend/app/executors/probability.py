"""概率触发器模块执行器"""
import random
from app.executors.base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor


@register_executor
class ProbabilityTriggerExecutor(ModuleExecutor):
    """概率触发器执行器"""
    
    @property
    def module_type(self) -> str:
        return "probability_trigger"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """根据概率选择执行路径"""
        try:
            # 获取概率配置（百分比）
            probability = float(config.get('probability', 50))
            
            # 验证概率范围
            if not 0 <= probability <= 100:
                return ModuleResult(
                    success=False,
                    message="概率值必须在0-100之间",
                    error="概率值无效"
                )
            
            # 生成随机数（0-100）
            random_value = random.uniform(0, 100)
            
            # 判断是否触发路径1
            if random_value < probability:
                branch = "path1"
                message = f"触发路径1（概率: {probability}%, 随机值: {random_value:.2f}）"
            else:
                branch = "path2"
                message = f"触发路径2（概率: {100-probability}%, 随机值: {random_value:.2f}）"
            
            return ModuleResult(
                success=True,
                message=message,
                branch=branch,
                data={
                    'probability': probability,
                    'random_value': random_value,
                    'selected_path': branch
                }
            )
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[ProbabilityTriggerExecutor] 执行失败: {error_detail}")
            return ModuleResult(
                success=False,
                message=f"概率触发器执行失败: {str(e)}",
                error=str(e)
            )
