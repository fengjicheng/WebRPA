"""手机输入模块执行器"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .phone_utils import ensure_phone_connected
from ..services.adb_manager import get_adb_manager


@register_executor
class PhoneInputTextExecutor(ModuleExecutor):
    """手机输入文本"""
    
    @property
    def module_type(self) -> str:
        return "phone_input_text"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        text = context.resolve_value(config.get('text', ''))
        auto_enter = config.get('autoEnter', False)  # 是否自动回车
        auto_switch_keyboard = config.get('autoSwitchKeyboard', True)  # 是否自动切换输入法，默认True
        auto_restore_keyboard = config.get('autoRestoreKeyboard', True)  # 是否自动恢复输入法，默认True
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            
            # 检查文本是否包含中文
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
            original_ime = None
            
            # 如果包含中文且启用了自动切换
            if has_chinese and auto_switch_keyboard:
                # 如果包含中文，自动切换到ADBKeyboard
                print(f"[PhoneInputText] 检测到中文，切换到ADBKeyboard")
                success, original_ime, error = adb.switch_to_adbkeyboard(device_id)
                if not success:
                    return ModuleResult(
                        success=False, 
                        error=f"切换到ADBKeyboard失败: {error}\n\n请确保已安装ADBKeyboard应用"
                    )
                
                # 如果启用了自动恢复，保存原输入法ID到context
                if auto_restore_keyboard and original_ime and original_ime != 'com.android.adbkeyboard/.AdbIME':
                    if 'original_ime' not in context.variables:
                        context.variables['original_ime'] = original_ime
                        print(f"[PhoneInputText] 已保存原输入法: {original_ime}")
            elif has_chinese and not auto_switch_keyboard:
                # 包含中文但未启用自动切换，提示用户
                print(f"[PhoneInputText] 检测到中文，但未启用自动切换输入法，请确保手机默认输入法为ADBKeyboard")
            
            # 输入文本
            success, error = adb.input_text(text, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            
            # 如果需要自动回车
            if auto_enter:
                print(f"[PhoneInputText] 自动按下回车键")
                success, error = adb.press_key('KEYCODE_ENTER', device_id)
                if not success:
                    return ModuleResult(success=False, error=f"按下回车键失败: {error}")
            
            message = "已输入文本" + ("并回车" if auto_enter else "")
            return ModuleResult(success=True, message=message)
            
        except Exception as e:
            return ModuleResult(success=False, error=f"输入文本失败: {str(e)}")


@register_executor
class PhonePressKeyExecutor(ModuleExecutor):
    """手机按键"""
    
    @property
    def module_type(self) -> str:
        return "phone_press_key"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        # 兼容旧的 'key' 字段和新的 'keycode' 字段
        keycode = config.get('keycode') or config.get('key')
        if not keycode:
            keycode = 'KEYCODE_HOME'
        
        keycode = context.resolve_value(keycode)
        
        # 如果 keycode 不是以 KEYCODE_ 开头，自动添加前缀（兼容旧格式）
        if keycode and not keycode.startswith('KEYCODE_'):
            keycode = f'KEYCODE_{keycode}'
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            success, error = adb.press_key(keycode, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            return ModuleResult(success=True, message=f"已按下 {keycode}")
        except Exception as e:
            return ModuleResult(success=False, error=f"按键失败: {str(e)}")
