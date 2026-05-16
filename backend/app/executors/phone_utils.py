"""手机操作模块的共享工具函数"""
from .base import ExecutionContext
from ..services.adb_manager import get_adb_manager


def ensure_phone_connected(context: ExecutionContext, config: dict = None) -> tuple[bool, str, str]:
    """确保手机已连接，如果未连接则自动连接
    
    Args:
        context: 执行上下文
        config: 模块配置（可选），如果提供且包含device_id，则使用指定设备
        
    Returns:
        (成功与否, 设备ID, 错误信息)
    """
    # 优先使用配置中指定的设备ID
    if config and config.get('deviceId'):
        device_id = context.resolve_value(config.get('deviceId'))
        if device_id and device_id.strip():
            # 验证设备是否存在
            adb = get_adb_manager()
            devices = adb.get_devices()
            device_ids = [d['id'] for d in devices]
            
            if device_id in device_ids:
                # 保存设备ID到上下文（用于后续模块）
                context.phone_device_id = device_id
                return True, device_id, ""
            else:
                return False, "", f"指定的设备 {device_id} 未连接"
    
    # 如果上下文中已经有设备ID，直接返回
    if hasattr(context, 'phone_device_id') and context.phone_device_id:
        return True, context.phone_device_id, ""
    
    # 自动连接第一台设备
    adb = get_adb_manager()
    success, device_id, error = adb.auto_connect_device()
    
    if success and device_id:
        # 保存设备ID到上下文
        context.phone_device_id = device_id
        return True, device_id, ""
    else:
        return False, "", error or "未知错误"
