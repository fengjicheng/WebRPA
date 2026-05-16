# Module executors
from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    LogMessage,
    ExecutorRegistry,
    registry,
    register_executor,
    get_backend_root,
    get_ffmpeg_path,
    get_ffprobe_path,
)

# 导入所有执行器以触发注册
from . import basic
from . import basic_variable  # 变量操作执行器
from . import advanced
from . import advanced_file_ops  # 文件操作执行器
from . import advanced_browser
from . import advanced_image
from . import advanced_keyboard
from . import advanced_pillow
from . import control
from . import control_extended  # 扩展控制流执行器
from . import math_list_ops  # 数学和列表运算执行器
from . import list_advanced  # 列表高级操作执行器
from . import dict_advanced  # 字典高级操作执行器
from . import math_advanced  # 高级数学运算执行器
from . import statistics  # 统计分析执行器
from . import string_convert  # 字符串转换执行器
from . import captcha
from . import data_structure
from . import ai
from . import ai_scraper
from . import ai_firecrawl
from . import table
from . import subflow
from . import database
from . import media
from . import media_record
from . import media_m3u8
from . import qq
from . import wechat
from . import pdf_ops
from . import pdf_convert
from . import document_convert
from . import screen_share
from . import trigger
from . import utility_tools
from . import desktop_automation  # 全新的桌面应用自动化模块（基于 uiautomation）
from . import format_factory
from . import python_script
from . import table_extract
from . import switch_tab
# 手机自动化模块
from . import phone_device
from . import phone_touch
from . import phone_input
from . import phone_screen
from . import phone_app
from . import phone_file
from . import phone_advanced
from . import phone_vision
from . import phone_settings
from . import phone_clipboard
# Webhook请求模块
from . import webhook
# 飞书自动化模块
from . import feishu
# 多数据库支持模块
from . import database_advanced
# 关系型数据库INSERT/UPDATE/DELETE模块
from . import database_relational
from . import database_relational2
# SSH远程操作模块
from . import ssh
from . import sap_automation  # SAP GUI 自动化模块
# AI生图、生视频模块
from . import ai_media
# 概率触发器模块
from . import probability
# 网络监听模块
from . import network_monitor
# Allure测试报告模块
from . import allure
# Apprise多渠道通知模块
from . import notify_apprise

# 调试：打印已注册的执行器
print(f"[DEBUG] 已注册的执行器类型: {registry.get_all_types()}")

__all__ = [
    "ModuleExecutor",
    "ExecutionContext",
    "ModuleResult",
    "LogMessage",
    "ExecutorRegistry",
    "registry",
    "register_executor",
    "get_backend_root",
    "get_ffmpeg_path",
    "get_ffprobe_path",
    "escape_css_selector",
]
