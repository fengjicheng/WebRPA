"""网络监听模块执行器 - 支持提前监听和等待API请求"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int
import asyncio
import time
from typing import Dict, List, Optional


# 全局网络监听器存储
_network_monitors: Dict[str, 'NetworkMonitor'] = {}


class NetworkMonitor:
    """网络监听器类"""
    
    def __init__(self, monitor_id: str, page):
        self.monitor_id = monitor_id
        self.page = page
        self.captured_requests: List[Dict] = []
        self.is_active = False
        self._listener = None
    
    def start(self, filter_type: str = "all", url_pattern: str = ""):
        """开始监听"""
        if self.is_active:
            return
        
        self.filter_type = filter_type
        self.url_pattern = url_pattern
        self.captured_requests.clear()
        
        def on_request(request):
            """请求处理函数"""
            try:
                url = request.url
                resource_type = request.resource_type
                
                # 根据过滤类型筛选
                if self.filter_type == "api":
                    # API请求通常是 fetch 或 xhr 类型
                    if resource_type not in ["fetch", "xhr"]:
                        return
                elif self.filter_type == "img":
                    if resource_type != "image":
                        return
                elif self.filter_type == "media":
                    if resource_type not in ["media", "video", "audio"]:
                        return
                elif self.filter_type == "m3u8":
                    if ".m3u8" not in url.lower():
                        return
                # all 类型不过滤
                
                # URL模式匹配
                if self.url_pattern:
                    if self.url_pattern.lower() not in url.lower():
                        return
                
                # 捕获请求信息
                request_info = {
                    "url": url,
                    "method": request.method,
                    "resource_type": resource_type,
                    "timestamp": time.time(),
                    "headers": dict(request.headers) if hasattr(request, 'headers') else {}
                }
                
                self.captured_requests.append(request_info)
            except Exception as e:
                print(f"[NetworkMonitor] 捕获请求异常: {e}")
        
        # 注册监听器
        self._listener = on_request
        self.page.on("request", self._listener)
        self.is_active = True
    
    def stop(self):
        """停止监听"""
        if not self.is_active:
            return
        
        if self._listener and self.page:
            try:
                self.page.remove_listener("request", self._listener)
            except:
                pass
        
        self.is_active = False
        self._listener = None
    
    def get_captured_requests(self) -> List[Dict]:
        """获取捕获的请求列表"""
        return self.captured_requests.copy()
    
    def clear_captured(self):
        """清空捕获的请求"""
        self.captured_requests.clear()


@register_executor
class NetworkMonitorStartExecutor(ModuleExecutor):
    """开始网络监听模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "network_monitor_start"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        开始网络监听，在页面加载前就开始捕获API请求
        
        配置参数:
        - monitorId: 监听器ID（用于后续引用）
        - filterType: 过滤类型（all/api/img/media/m3u8）
        - urlPattern: URL匹配模式（可选，模糊匹配）
        """
        try:
            monitor_id = context.resolve_value(config.get('monitorId', 'default'))
            filter_type = context.resolve_value(config.get('filterType', 'api'))
            url_pattern = context.resolve_value(config.get('urlPattern', ''))
            
            if not monitor_id:
                return ModuleResult(success=False, error="监听器ID不能为空")
            
            # 检查是否有打开的页面
            if context.page is None:
                return ModuleResult(success=False, error="没有打开的页面，请先打开浏览器")
            
            await context.switch_to_latest_page()
            
            # 如果已存在同ID的监听器，先停止
            if monitor_id in _network_monitors:
                old_monitor = _network_monitors[monitor_id]
                old_monitor.stop()
            
            # 创建新的监听器
            monitor = NetworkMonitor(monitor_id, context.page)
            monitor.start(filter_type, url_pattern)
            
            # 存储到全局字典
            _network_monitors[monitor_id] = monitor
            
            filter_desc = f"类型={filter_type}"
            if url_pattern:
                filter_desc += f"，URL包含='{url_pattern}'"
            
            return ModuleResult(
                success=True,
                message=f"网络监听已启动（ID: {monitor_id}，{filter_desc}），将持续捕获请求直到停止",
                data={
                    "monitor_id": monitor_id,
                    "filter_type": filter_type,
                    "url_pattern": url_pattern,
                    "status": "monitoring"
                }
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"启动网络监听失败: {str(e)}")


@register_executor
class NetworkMonitorWaitExecutor(ModuleExecutor):
    """等待API请求模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "network_monitor_wait"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        等待并捕获特定的API请求
        
        配置参数:
        - monitorId: 监听器ID（必须先启动监听）
        - urlPattern: URL匹配模式（必填，用于匹配特定API）
        - timeout: 超时时间（毫秒，默认30000）
        - variableName: 存储变量名（存储捕获的请求信息）
        - stopAfterCapture: 捕获后是否停止监听（默认false）
        - captureMode: 捕获模式（first/all，默认first）
        """
        try:
            monitor_id = context.resolve_value(config.get('monitorId', 'default'))
            url_pattern = context.resolve_value(config.get('urlPattern', ''))
            timeout = to_int(config.get('timeout', 30), 30, context)
            variable_name = config.get('variableName', '')
            stop_after_capture = config.get('stopAfterCapture', False)
            capture_mode = context.resolve_value(config.get('captureMode', 'first'))
            
            if not monitor_id:
                return ModuleResult(success=False, error="监听器ID不能为空")
            
            if not url_pattern:
                return ModuleResult(success=False, error="URL匹配模式不能为空")
            
            # 检查监听器是否存在
            if monitor_id not in _network_monitors:
                return ModuleResult(
                    success=False,
                    error=f"监听器 '{monitor_id}' 不存在，请先使用'开始网络监听'模块启动监听"
                )
            
            monitor = _network_monitors[monitor_id]
            
            if not monitor.is_active:
                return ModuleResult(
                    success=False,
                    error=f"监听器 '{monitor_id}' 未激活，请先使用'开始网络监听'模块启动监听"
                )
            
            # 等待匹配的请求
            start_time = time.time()
            timeout_sec = timeout
            matched_requests = []
            
            while time.time() - start_time < timeout_sec:
                # 检查已捕获的请求
                for req in monitor.captured_requests:
                    url = req.get('url', '')
                    if url_pattern.lower() in url.lower():
                        # 检查是否已经添加过（避免重复）
                        if req not in matched_requests:
                            matched_requests.append(req)
                            
                            # 如果是first模式，找到第一个就退出
                            if capture_mode == 'first':
                                break
                
                # 如果是first模式且已找到，退出等待
                if capture_mode == 'first' and matched_requests:
                    break
                
                # 短暂休眠，避免CPU占用过高
                await asyncio.sleep(0.1)
            
            # 检查是否捕获到请求
            if not matched_requests:
                # 超时未捕获到
                if stop_after_capture:
                    monitor.stop()
                    del _network_monitors[monitor_id]
                
                return ModuleResult(
                    success=False,
                    error=f"等待超时（{timeout}秒），未捕获到匹配的API请求（URL包含: '{url_pattern}'）"
                )
            
            # 存储结果
            if capture_mode == 'first':
                result_data = matched_requests[0]
            else:
                result_data = matched_requests
            
            if variable_name:
                context.set_variable(variable_name, result_data)
            
            # 是否停止监听
            if stop_after_capture:
                monitor.stop()
                del _network_monitors[monitor_id]
            
            count = len(matched_requests)
            mode_desc = "第一个" if capture_mode == 'first' else f"全部{count}个"
            
            return ModuleResult(
                success=True,
                message=f"成功捕获{mode_desc}匹配的API请求（URL包含: '{url_pattern}'）" + 
                        (f"，已存入变量 {{{variable_name}}}" if variable_name else ""),
                data={
                    "monitor_id": monitor_id,
                    "url_pattern": url_pattern,
                    "capture_mode": capture_mode,
                    "count": count,
                    "requests": matched_requests[:5],  # 最多返回前5个
                    "stopped": stop_after_capture
                }
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"等待API请求失败: {str(e)}")


@register_executor
class NetworkMonitorStopExecutor(ModuleExecutor):
    """停止网络监听模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "network_monitor_stop"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        停止网络监听
        
        配置参数:
        - monitorId: 监听器ID
        - variableName: 存储变量名（可选，存储所有捕获的请求）
        """
        try:
            monitor_id = context.resolve_value(config.get('monitorId', 'default'))
            variable_name = config.get('variableName', '')
            
            if not monitor_id:
                return ModuleResult(success=False, error="监听器ID不能为空")
            
            # 检查监听器是否存在
            if monitor_id not in _network_monitors:
                return ModuleResult(
                    success=False,
                    error=f"监听器 '{monitor_id}' 不存在"
                )
            
            monitor = _network_monitors[monitor_id]
            
            # 获取捕获的请求
            captured_requests = monitor.get_captured_requests()
            
            # 停止监听
            monitor.stop()
            del _network_monitors[monitor_id]
            
            # 存储结果
            if variable_name:
                context.set_variable(variable_name, captured_requests)
            
            return ModuleResult(
                success=True,
                message=f"网络监听已停止（ID: {monitor_id}），共捕获 {len(captured_requests)} 个请求" +
                        (f"，已存入变量 {{{variable_name}}}" if variable_name else ""),
                data={
                    "monitor_id": monitor_id,
                    "count": len(captured_requests),
                    "requests": captured_requests[:10]  # 最多返回前10个
                }
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"停止网络监听失败: {str(e)}")
