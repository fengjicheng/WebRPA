"""
桌面元素选择器服务 - 基于 uiautomation 库
提供类似 Inspect.exe 的元素选择功能
"""
import asyncio
import threading
import time
from typing import Optional, Dict, Any, List, Callable
import traceback

try:
    import uiautomation as auto
    import win32gui
    import win32api
    import win32con
    UIAUTOMATION_AVAILABLE = True
except ImportError:
    UIAUTOMATION_AVAILABLE = False
    print("[DesktopElementPicker] uiautomation 或 win32 相关库未安装")


class DesktopElementPicker:
    """桌面元素选择器 - 使用 uiautomation 库"""
    
    def __init__(self):
        self.is_picking = False
        self.current_element = None
        self.picker_thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable] = None
        self.last_rect = None
        self.highlight_window = None
        
    def start_picking(self, callback: Callable):
        """开始元素选择模式"""
        if not UIAUTOMATION_AVAILABLE:
            raise RuntimeError("uiautomation 未安装，无法使用桌面元素选择器")
        
        if self.is_picking:
            return
        
        self.is_picking = True
        self.callback = callback
        
        # 启动鼠标监听线程
        self.picker_thread = threading.Thread(target=self._picker_loop, daemon=True)
        self.picker_thread.start()
        print("[DesktopElementPicker] 元素选择器已启动")
    
    def stop_picking(self):
        """停止元素选择模式"""
        self.is_picking = False
        self.current_element = None
        self.last_rect = None
        
        # 销毁高亮窗口
        if self.highlight_window:
            try:
                self.highlight_window.destroy()
            except:
                pass
            self.highlight_window = None
        
        print("[DesktopElementPicker] 元素选择器已停止")
    
    def _picker_loop(self):
        """元素选择主循环"""
        try:
            last_check_time = 0
            last_highlighted_rect = None
            
            # 创建高亮窗口（使用tkinter）
            try:
                import tkinter as tk
                self.highlight_window = tk.Tk()
                self.highlight_window.withdraw()  # 隐藏主窗口
                self.highlight_window.attributes('-topmost', True)
                self.highlight_window.attributes('-alpha', 0.3)  # 半透明
                self.highlight_window.overrideredirect(True)  # 无边框
                
                # 创建画布
                canvas = tk.Canvas(self.highlight_window, bg='red', highlightthickness=3, highlightbackground='red')
                canvas.pack(fill=tk.BOTH, expand=True)
                
                has_highlight = True
                print("[DesktopElementPicker] 高亮窗口创建成功")
            except Exception as e:
                has_highlight = False
                print(f"[DesktopElementPicker] 无法创建高亮窗口: {e}")
                traceback.print_exc()
            
            while self.is_picking:
                current_time = time.time()
                
                # 检测ESC退出
                if win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000:
                    self.stop_picking()
                    break
                
                # 检测Ctrl+点击捕获
                if win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000:
                    if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                        if self.current_element:
                            self._capture_element(self.current_element)
                            self.stop_picking()
                            time.sleep(0.2)  # 防止重复触发
                            continue
                
                # 每50ms检测一次鼠标位置
                if current_time - last_check_time < 0.05:
                    time.sleep(0.01)
                    if has_highlight and self.highlight_window:
                        try:
                            self.highlight_window.update()
                        except:
                            pass
                    continue
                
                last_check_time = current_time
                
                # 获取鼠标位置
                try:
                    x, y = win32api.GetCursorPos()
                    
                    # 获取鼠标下的元素
                    element = auto.ControlFromPoint(x, y)
                    
                    if element and element.Exists(0, 0):
                        # 排除浏览器窗口（WebRPA自己的界面）
                        # 方法1：检查窗口类名是否是浏览器类
                        skip_element = False
                        try:
                            # 获取顶层窗口
                            window = element.GetTopLevelControl()
                            if window:
                                window_class = window.ClassName
                                window_title = window.Name
                                
                                # 浏览器窗口类名列表
                                browser_classes = [
                                    'Chrome_WidgetWin_1',  # Chrome/Edge
                                    'MozillaWindowClass',  # Firefox
                                    'ApplicationFrameWindow',  # UWP应用
                                ]
                                
                                # 如果是浏览器窗口，检查标题
                                if any(cls in window_class for cls in browser_classes):
                                    # 如果标题包含WebRPA相关关键词，跳过
                                    if window_title and any(keyword in window_title for keyword in ["WebRPA", "localhost", "127.0.0.1", "5173"]):
                                        skip_element = True
                        except:
                            pass
                        
                        # 如果是WebRPA窗口，清空当前元素并跳过高亮
                        if skip_element:
                            self.current_element = None
                            # 隐藏高亮窗口
                            if has_highlight and self.highlight_window:
                                try:
                                    self.highlight_window.withdraw()
                                except:
                                    pass
                            time.sleep(0.01)
                            continue
                        
                        # 检查是否是新元素
                        if not self.current_element or element.NativeWindowHandle != self.current_element.NativeWindowHandle:
                            self.current_element = element
                            print(f"[DesktopElementPicker] 检测到新元素: {element.Name or element.ControlTypeName}")
                            
                            # 更新高亮显示
                            if has_highlight and self.highlight_window:
                                try:
                                    rect = element.BoundingRectangle
                                    rect_tuple = (rect.left, rect.top, rect.width(), rect.height())
                                    
                                    if rect_tuple != last_highlighted_rect:
                                        last_highlighted_rect = rect_tuple
                                        print(f"[DesktopElementPicker] 更新高亮位置: {rect_tuple}")
                                        self.highlight_window.geometry(f"{rect.width()}x{rect.height()}+{rect.left}+{rect.top}")
                                        self.highlight_window.deiconify()
                                        self.highlight_window.update()
                                except Exception as e:
                                    print(f"[DesktopElementPicker] 更新高亮失败: {e}")
                                    pass
                        
                except Exception as e:
                    # 忽略获取元素时的错误
                    pass
                
                time.sleep(0.01)
            
            # 清理高亮窗口
            if has_highlight and self.highlight_window:
                try:
                    self.highlight_window.destroy()
                    self.highlight_window = None
                except:
                    pass
                
        except Exception as e:
            print(f"[DesktopElementPicker] 选择器循环异常: {e}")
            traceback.print_exc()
        finally:
            self.is_picking = False
    
    def _capture_element(self, element):
        """捕获元素信息"""
        try:
            # 提取元素信息
            info = self._extract_element_info(element)
            
            # 回调返回元素信息
            if self.callback:
                # 在新线程中调用回调，避免阻塞
                threading.Thread(target=self.callback, args=(info,), daemon=True).start()
                
            print(f"[DesktopElementPicker] 已捕获元素: {info.get('name', '(无名称)')}")
            
        except Exception as e:
            print(f"[DesktopElementPicker] 捕获元素失败: {e}")
            traceback.print_exc()
    
    def _extract_element_info(self, element) -> Dict[str, Any]:
        """提取元素完整信息"""
        try:
            info = {
                'name': '',
                'class_name': '',
                'control_type': '',
                'automation_id': '',
                'handle': 0,
                'rectangle': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'is_visible': False,
                'is_enabled': False,
                'is_offscreen': False,
                'has_keyboard_focus': False,
                'path': [],
                'selectors': [],
                'patterns': []
            }
            
            # 基本属性
            try:
                info['name'] = element.Name or ''
            except:
                pass
            
            try:
                info['class_name'] = element.ClassName or ''
            except:
                pass
            
            try:
                info['control_type'] = element.ControlTypeName or ''
            except:
                pass
            
            try:
                info['automation_id'] = element.AutomationId or ''
            except:
                pass
            
            try:
                info['handle'] = element.NativeWindowHandle
            except:
                pass
            
            # 位置信息
            try:
                rect = element.BoundingRectangle
                info['rectangle'] = {
                    'x': rect.left,
                    'y': rect.top,
                    'width': rect.width(),
                    'height': rect.height()
                }
            except:
                pass
            
            # 状态信息
            try:
                info['is_visible'] = element.IsVisible
            except:
                pass
            
            try:
                info['is_enabled'] = element.IsEnabled
            except:
                pass
            
            try:
                info['is_offscreen'] = element.IsOffscreen
            except:
                pass
            
            try:
                info['has_keyboard_focus'] = element.HasKeyboardFocus
            except:
                pass
            
            # 支持的模式
            try:
                patterns = []
                if hasattr(element, 'GetValuePattern'):
                    try:
                        element.GetValuePattern()
                        patterns.append('Value')
                    except:
                        pass
                
                if hasattr(element, 'GetTogglePattern'):
                    try:
                        element.GetTogglePattern()
                        patterns.append('Toggle')
                    except:
                        pass
                
                if hasattr(element, 'GetSelectionItemPattern'):
                    try:
                        element.GetSelectionItemPattern()
                        patterns.append('SelectionItem')
                    except:
                        pass
                
                if hasattr(element, 'GetScrollPattern'):
                    try:
                        element.GetScrollPattern()
                        patterns.append('Scroll')
                    except:
                        pass
                
                if hasattr(element, 'GetTextPattern'):
                    try:
                        element.GetTextPattern()
                        patterns.append('Text')
                    except:
                        pass
                
                info['patterns'] = patterns
            except:
                pass
            
            # 元素路径
            info['path'] = self._get_element_path(element)
            
            # 生成选择器策略
            info['selectors'] = self._generate_selectors(element, info)
            
            return info
            
        except Exception as e:
            print(f"[DesktopElementPicker] 提取元素信息失败: {e}")
            traceback.print_exc()
            return {}
    
    def _get_element_path(self, element) -> List[Dict[str, str]]:
        """获取元素的完整路径"""
        path = []
        current = element
        max_depth = 10  # 限制最大深度
        
        for _ in range(max_depth):
            try:
                path.insert(0, {
                    'name': current.Name or '(无名称)',
                    'class_name': current.ClassName or '(无类名)',
                    'control_type': current.ControlTypeName or '(未知)',
                    'automation_id': current.AutomationId or ''
                })
                
                # 获取父元素
                parent = current.GetParentControl()
                if not parent or not parent.Exists(0, 0):
                    break
                current = parent
            except:
                break
        
        return path
    
    def _generate_selectors(self, element, info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成多种元素选择器策略"""
        selectors = []
        
        # 策略1: AutomationId（最稳定）
        if info.get('automation_id'):
            selectors.append({
                'type': 'automation_id',
                'value': info['automation_id'],
                'priority': 1,
                'description': '通过自动化ID定位（最稳定）',
                'config': {
                    'controlType': info.get('control_type', ''),
                    'automationId': info['automation_id']
                }
            })
        
        # 策略2: Name + ControlType（推荐）
        if info.get('name'):
            selectors.append({
                'type': 'name_and_type',
                'name': info['name'],
                'control_type': info.get('control_type', ''),
                'priority': 2,
                'description': '通过名称和控件类型定位（推荐）',
                'config': {
                    'controlType': info.get('control_type', ''),
                    'name': info['name']
                }
            })
        
        # 策略3: ClassName（备选）
        if info.get('class_name'):
            selectors.append({
                'type': 'class_name',
                'class_name': info['class_name'],
                'priority': 3,
                'description': '通过类名定位（备选）',
                'config': {
                    'controlType': info.get('control_type', ''),
                    'className': info['class_name']
                }
            })
        
        # 策略4: 完整路径（最精确）
        if info.get('path') and len(info['path']) > 1:
            path_str = ' -> '.join([f"{p['name']} ({p['control_type']})" for p in info['path'][-3:]])
            selectors.append({
                'type': 'full_path',
                'path': info['path'],
                'priority': 4,
                'description': f'通过路径定位: {path_str}',
                'config': {
                    'searchDepth': len(info['path']),
                    'path': info['path']
                }
            })
        
        # 策略5: Handle（直接定位，但不稳定）
        if info.get('handle'):
            selectors.append({
                'type': 'handle',
                'handle': info['handle'],
                'priority': 5,
                'description': '通过窗口句柄定位（仅当前会话有效）',
                'config': {
                    'handle': info['handle']
                }
            })
        
        return selectors


# 全局单例
_picker_instance: Optional[DesktopElementPicker] = None


def get_desktop_element_picker() -> DesktopElementPicker:
    """获取桌面元素选择器单例"""
    global _picker_instance
    if _picker_instance is None:
        _picker_instance = DesktopElementPicker()
    return _picker_instance
