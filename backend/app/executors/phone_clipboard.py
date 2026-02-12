"""手机剪贴板模块执行器"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .phone_utils import ensure_phone_connected
from ..services.adb_manager import get_adb_manager


@register_executor
class PhoneSetClipboardExecutor(ModuleExecutor):
    """手机写入剪贴板"""
    
    @property
    def module_type(self) -> str:
        return "phone_set_clipboard"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        text = context.resolve_value(config.get('text', ''))
        
        if not text:
            return ModuleResult(success=False, error="剪贴板内容不能为空")
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            success, error = adb.set_clipboard(text, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            return ModuleResult(success=True, message=f"已写入剪贴板")
        except Exception as e:
            return ModuleResult(success=False, error=f"写入剪贴板失败: {str(e)}")


@register_executor
class PhoneGetClipboardExecutor(ModuleExecutor):
    """手机读取剪贴板"""
    
    @property
    def module_type(self) -> str:
        return "phone_get_clipboard"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        variable_name = config.get('variableName', 'phone_clipboard')
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            success, content, error = adb.get_clipboard(device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            
            # 保存到变量
            context.set_variable(variable_name, content)
            
            return ModuleResult(
                success=True, 
                message=f"已读取剪贴板内容到变量 {variable_name}",
                data={variable_name: content}
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"读取剪贴板失败: {str(e)}")
