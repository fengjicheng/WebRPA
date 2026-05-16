"""鼠标手势识别服务"""
import threading
import time
from typing import Optional, Callable, List, Tuple
from pynput import mouse
from enum import Enum


class GestureDirection(Enum):
    """手势方向"""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    UP_LEFT = "up_left"
    UP_RIGHT = "up_right"
    DOWN_LEFT = "down_left"
    DOWN_RIGHT = "down_right"


class MouseGestureService:
    """鼠标手势识别服务"""
    
    def __init__(self):
        self.is_running = False
        self.listener: Optional[mouse.Listener] = None
        self.gesture_callback: Optional[Callable[[str, List[GestureDirection]], None]] = None
        
        # 手势识别参数
        self.min_distance = 50  # 最小移动距离（像素）
        self.gesture_timeout = 2.0  # 手势超时时间（秒）
        
        # 手势记录
        self.gesture_points: List[Tuple[int, int]] = []
        self.gesture_start_time: float = 0
        self.is_gesturing = False
        self.gesture_button: Optional[mouse.Button] = None
        
        print("[MouseGestureService] 服务已初始化")
    
    def _calculate_direction(self, start: Tuple[int, int], end: Tuple[int, int]) -> Optional[GestureDirection]:
        """计算两点之间的方向"""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        # 计算距离
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance < self.min_distance:
            return None
        
        # 计算角度（弧度）
        import math
        angle = math.atan2(dy, dx)
        angle_deg = math.degrees(angle)
        
        # 根据角度判断方向（8个方向）
        # 右: -22.5 ~ 22.5
        # 右下: 22.5 ~ 67.5
        # 下: 67.5 ~ 112.5
        # 左下: 112.5 ~ 157.5
        # 左: 157.5 ~ -157.5
        # 左上: -157.5 ~ -112.5
        # 上: -112.5 ~ -67.5
        # 右上: -67.5 ~ -22.5
        
        if -22.5 <= angle_deg < 22.5:
            return GestureDirection.RIGHT
        elif 22.5 <= angle_deg < 67.5:
            return GestureDirection.DOWN_RIGHT
        elif 67.5 <= angle_deg < 112.5:
            return GestureDirection.DOWN
        elif 112.5 <= angle_deg < 157.5:
            return GestureDirection.DOWN_LEFT
        elif angle_deg >= 157.5 or angle_deg < -157.5:
            return GestureDirection.LEFT
        elif -157.5 <= angle_deg < -112.5:
            return GestureDirection.UP_LEFT
        elif -112.5 <= angle_deg < -67.5:
            return GestureDirection.UP
        elif -67.5 <= angle_deg < -22.5:
            return GestureDirection.UP_RIGHT
        
        return None
    
    def _recognize_gesture(self, points: List[Tuple[int, int]]) -> List[GestureDirection]:
        """识别手势路径"""
        if len(points) < 2:
            return []
        
        directions = []
        last_direction = None
        
        # 简化路径：每隔一定距离采样一个点
        simplified_points = [points[0]]
        for i in range(1, len(points)):
            dx = points[i][0] - simplified_points[-1][0]
            dy = points[i][1] - simplified_points[-1][1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance >= self.min_distance:
                simplified_points.append(points[i])
        
        # 识别方向序列
        for i in range(len(simplified_points) - 1):
            direction = self._calculate_direction(simplified_points[i], simplified_points[i + 1])
            if direction and direction != last_direction:
                directions.append(direction)
                last_direction = direction
        
        return directions
    
    def _gesture_to_string(self, directions: List[GestureDirection], button: mouse.Button) -> str:
        """将手势转换为字符串表示"""
        if not directions:
            return ""
        
        # 按钮前缀
        button_prefix = ""
        if button == mouse.Button.left:
            button_prefix = "left_"
        elif button == mouse.Button.right:
            button_prefix = "right_"
        elif button == mouse.Button.middle:
            button_prefix = "middle_"
        
        # 方向序列
        direction_str = "_".join([d.value for d in directions])
        
        return f"{button_prefix}{direction_str}"
    
    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool):
        """鼠标点击事件处理"""
        if pressed:
            # 开始手势
            self.is_gesturing = True
            self.gesture_button = button
            self.gesture_points = [(x, y)]
            self.gesture_start_time = time.time()
        else:
            # 结束手势
            if self.is_gesturing and self.gesture_button == button:
                self.gesture_points.append((x, y))
                
                # 识别手势
                directions = self._recognize_gesture(self.gesture_points)
                
                # 如果有有效的手势方向，触发回调
                if directions:
                    gesture_str = self._gesture_to_string(directions, button)
                    print(f"[MouseGesture] 识别到手势: {gesture_str}")
                    
                    if self.gesture_callback:
                        try:
                            self.gesture_callback(gesture_str, directions)
                        except Exception as e:
                            print(f"[MouseGesture] 回调函数执行失败: {e}")
                
                # 重置状态
                self.is_gesturing = False
                self.gesture_button = None
                self.gesture_points = []
    
    def _on_move(self, x: int, y: int):
        """鼠标移动事件处理"""
        if self.is_gesturing:
            # 检查超时
            if time.time() - self.gesture_start_time > self.gesture_timeout:
                print("[MouseGesture] 手势超时，已取消")
                self.is_gesturing = False
                self.gesture_button = None
                self.gesture_points = []
                return
            
            # 记录轨迹点
            self.gesture_points.append((x, y))
    
    def start(self, callback: Callable[[str, List[GestureDirection]], None], 
              min_distance: int = 50, gesture_timeout: float = 2.0) -> bool:
        """启动手势识别
        
        Args:
            callback: 手势识别回调函数，参数为(gesture_str, directions)
            min_distance: 最小移动距离（像素）
            gesture_timeout: 手势超时时间（秒）
        """
        if self.is_running:
            print("[MouseGesture] 手势识别已在运行中")
            return False
        
        self.gesture_callback = callback
        self.min_distance = min_distance
        self.gesture_timeout = gesture_timeout
        
        # 启动监听器
        self.listener = mouse.Listener(
            on_click=self._on_click,
            on_move=self._on_move
        )
        self.listener.start()
        self.is_running = True
        
        print(f"[MouseGesture] 手势识别已启动 (最小距离: {min_distance}px, 超时: {gesture_timeout}s)")
        return True
    
    def stop(self) -> bool:
        """停止手势识别"""
        if not self.is_running:
            print("[MouseGesture] 手势识别未在运行")
            return False
        
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        self.is_running = False
        self.is_gesturing = False
        self.gesture_button = None
        self.gesture_points = []
        
        print("[MouseGesture] 手势识别已停止")
        return True
    
    def get_status(self) -> dict:
        """获取识别状态"""
        return {
            "is_running": self.is_running,
            "is_gesturing": self.is_gesturing,
            "min_distance": self.min_distance,
            "gesture_timeout": self.gesture_timeout
        }


# 全局单例
_mouse_gesture_service: Optional[MouseGestureService] = None


def get_mouse_gesture_service() -> MouseGestureService:
    """获取鼠标手势服务单例"""
    global _mouse_gesture_service
    if _mouse_gesture_service is None:
        _mouse_gesture_service = MouseGestureService()
    return _mouse_gesture_service
