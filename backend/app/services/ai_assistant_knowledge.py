"""WebRPA小助手 - 知识库

集中管理所有 WebRPA 相关的"自我认知"：项目介绍、开发者信息、内置模块清单、
常用功能用法等。系统提示词会从这里取材，让小助手能为用户答疑解惑。
"""
from __future__ import annotations

from typing import Any


# ---------- 关于 WebRPA 本身 ----------

WEBRPA_OVERVIEW = """\
WebRPA 是一款面向桌面的可视化 RPA（机器人流程自动化）开发与运行平台。
它通过图形化的工作流编辑器，让用户用拖拽节点的方式编排自动化流程，
覆盖网页操作、桌面应用控制、手机自动化、AI、数据库、文件、媒体处理、PDF、
通知、计划任务、SAP/SSH/邮件/即时通讯（QQ/微信/飞书）等场景。

核心理念：
- 零代码 / 低代码：拖拽即可搭建复杂自动化流程
- 一站式：浏览器、桌面、手机、AI、数据库等能力齐全
- 可观测：每个节点的执行结果、变量、日志都能实时查看
- 可扩展：支持自定义模块、Python/JS 脚本节点、自定义 AI 模型
"""

WEBRPA_AUTHOR = """\
WebRPA 由开发者 青云制作_彭明航 设计与开发。
项目目标是让任何人都能用最简单的方式构建强大的自动化能力。
"""

WEBRPA_FEATURES = """\
WebRPA 的主要功能板块：
1. 工作流编辑器：基于 React Flow 的可视化画布，支持拖拽、复制、粘贴、撤销/重做、对齐分布
2. 元素选择器：浏览器内置 picker 选择网页元素（支持 CSS、XPath、相似元素）
3. 桌面元素拾取：基于 uiautomation 选择 Windows 桌面控件
4. 计划任务：cron 表达式定时执行工作流
5. 触发器：邮件、API、文件监控、热键、概率、定时等触发
6. 数据资产：Excel/CSV 数据循环执行；图像资产作为模板
7. 数据表格：执行结果聚合为表格，支持完整数据导出
8. 自定义模块：把多个节点封装为可复用的子模块
9. 子流程：把工作流嵌套调用
10. 全局配置：浏览器、AI、邮件、数据库、QQ/飞书等的默认配置
11. 工作流市场：在线分享与下载工作流（Workflow Hub）
12. 远程协助：跨设备执行
13. 实时日志：节点级别的执行日志、变量追踪
14. AI 能力：内置 AI 对话、AI 视觉、AI 智能爬虫、AI 元素选择器、AI 生图/生视频等
"""

WEBRPA_FAQ = """\
常见问题：
Q: 如何运行工作流？
A: 在工作流编辑器中点击工具栏的"运行"按钮，或按快捷键 F5（停止用 Shift+F5）。如果在画布中只想运行某个节点，可以右键单击节点选择"运行此节点"。

Q: 怎么搭建第一个工作流？
A: 1) 从左侧模块栏拖入"打开网页"节点；2) 拖入"输入文本"或"点击元素"节点；3) 用元素选择器选择目标；4) 用箭头连接节点；5) 点运行。

Q: 如何使用 AI 大脑模块？
A: 在全局配置的"AI对话"标签里填好 API 地址、API Key、模型名（支持 OpenAI/智谱/Deepseek 等任意 OpenAI 兼容协议）；然后拖入"AI对话"节点，填提示词即可。

Q: 工作流能定时执行吗？
A: 可以。在工具栏点"计划任务"，配置 cron 表达式或简单时间间隔。

Q: 怎么处理 Excel 数据？
A: 通过"数据资产"上传 Excel 文件，工作流会自动按行循环执行；也可以用"读取 Excel"节点手动读取。

Q: 元素选择不准怎么办？
A: 元素选择器支持 CSS、XPath 两种语法，点击元素时按住 Alt 可以选择"相似元素"批量。或者使用"AI 元素选择器"模块，让 AI 帮你定位。

Q: 工作流卡住了怎么办？
A: 工具栏的"停止"按钮会终止当前执行；或按快捷键 Shift+F5。

Q: WebRPA 有哪些全局快捷键？
A: 全局热键（任何窗口下都生效）：
   - F5：运行当前工作流
   - Shift+F5：停止当前工作流
   - F9：开始录制宏
   - F10：停止录制宏
   编辑器内快捷键（焦点在画布时）：
   - Ctrl+S：保存工作流
   - Alt+N：新建工作流
   - Ctrl+F：搜索画布
   - Ctrl+G / F3：跳到下一个搜索结果
   - Ctrl+Shift+G / Shift+F3：跳到上一个搜索结果
   - Ctrl+Z / Ctrl+Y：撤销 / 重做
   - Delete：删除选中节点
   - Ctrl+K：呼出 AI 小助手
"""


# ---------- 模块分类 ----------
# 这里手工维护一个分类表，让小助手知道每个 module_type 是干什么的。
# 由于全部 459 个执行器太多，分类按"领域"组织。

MODULE_CATEGORIES: dict[str, dict[str, str]] = {
    "网页基础": {
        "open_page": "打开网页（URL、新标签或当前标签）",
        "click_element": "点击网页元素（按选择器）",
        "hover_element": "鼠标悬停在元素上",
        "input_text": "在输入框填入文本",
        "get_element_info": "读取元素文本、属性、HTML",
        "wait_element": "等待元素出现",
        "wait_image": "等待屏幕上某图像出现",
        "wait_page_load": "等待页面加载完成",
        "page_load_complete": "判断页面加载是否完成",
        "close_page": "关闭浏览器标签页",
        "switch_iframe": "切换到 iframe 内部",
        "switch_to_main": "从 iframe 切回主页面",
        "use_opened_page": "使用已打开的浏览器页面",
        "switch_tab": "切换浏览器标签",
        "refresh_page": "刷新当前页面",
        "go_back": "浏览器后退",
        "go_forward": "浏览器前进",
        "scroll_page": "滚动页面",
        "screenshot": "对当前页面或元素截图",
        "save_image": "把网页中的图片保存到本地",
    },
    "网页高级": {
        "select_dropdown": "选择下拉框选项",
        "set_checkbox": "勾选/取消勾选复选框",
        "drag_element": "拖拽元素到目标位置",
        "upload_file": "网页文件上传",
        "download_file": "网页文件下载",
        "handle_dialog": "处理浏览器对话框（alert/confirm）",
        "inject_javascript": "在页面里注入并执行 JS",
        "js_script": "执行一段 JS 脚本（拿到返回值）",
        "get_child_elements": "获取子元素列表",
        "get_sibling_elements": "获取兄弟元素列表",
        "element_exists": "判断元素是否存在",
        "element_visible": "判断元素是否可见",
        "drag_image": "通过图像识别拖拽",
        "image_exists": "判断屏幕上某图像是否存在",
        "click_image": "通过图像识别点击屏幕",
        "click_text": "通过 OCR 识别屏幕文字并点击",
        "hover_text": "通过 OCR 识别屏幕文字并悬停",
        "hover_image": "通过图像识别后悬停",
        "network_capture": "抓取网页网络请求",
        "network_monitor_start": "开始监听网络请求",
        "network_monitor_wait": "等待匹配的网络请求",
        "network_monitor_stop": "停止网络监听",
    },
    "流程控制": {
        "condition": "条件判断（if/else 分支）",
        "loop": "循环 N 次",
        "foreach": "遍历列表",
        "foreach_dict": "遍历字典",
        "infinite_loop": "无限循环（需配合 break）",
        "break_loop": "跳出循环",
        "continue_loop": "跳过当前循环迭代",
        "stop_workflow": "停止整个工作流",
        "subflow": "调用子工作流",
        "group": "节点分组（用于组织画布）",
        "wait": "暂停 N 秒",
    },
    "变量与数据": {
        "set_variable": "设置/创建变量",
        "increment_decrement": "数值变量自增/自减",
        "json_parse": "解析 JSON 字符串",
        "base64": "Base64 编解码",
        "regex_extract": "用正则表达式提取文本",
        "string_replace": "字符串替换",
        "string_split": "字符串分割",
        "string_join": "字符串拼接",
        "string_concat": "字符串连接",
        "string_trim": "字符串去空白",
        "string_case": "大小写转换",
        "string_substring": "截取子串",
    },
    "AI": {
        "ai_chat": "AI 对话（OpenAI 兼容协议）",
        "ai_vision": "AI 视觉理解（多模态）",
        "ai_smart_scraper": "AI 智能爬虫（自然语言提取网页数据）",
        "ai_element_selector": "AI 自动定位网页元素",
        "ai_generate_image": "AI 生成图片",
        "ai_generate_video": "AI 生成视频",
        "firecrawl_scrape": "Firecrawl 抓取单页",
        "firecrawl_map": "Firecrawl 站点地图",
        "firecrawl_crawl": "Firecrawl 全站爬取",
    },
    "鼠标键盘": {
        "real_mouse_click": "真实鼠标点击屏幕坐标",
        "real_mouse_move": "真实鼠标移动",
        "real_mouse_drag": "真实鼠标拖拽",
        "real_mouse_scroll": "真实鼠标滚轮",
        "real_keyboard": "真实键盘输入/快捷键",
        "keyboard_action": "键盘动作（按下、释放、组合键）",
        "get_mouse_position": "获取当前鼠标位置",
    },
    "桌面自动化": {
        "desktop_app_connect": "连接已打开的桌面程序",
        "desktop_app_start": "启动桌面程序",
        "desktop_app_close": "关闭桌面程序",
        "desktop_window_activate": "激活窗口（置顶）",
        "desktop_window_state": "最大化/最小化/还原窗口",
        "desktop_window_move": "移动窗口位置",
        "desktop_window_resize": "调整窗口大小",
        "desktop_find_control": "查找 UI 控件",
        "desktop_click_control": "点击 UI 控件",
        "desktop_input_control": "向 UI 控件输入文本",
        "desktop_get_text": "读取控件文本",
        "desktop_select_combo": "选择下拉框",
        "desktop_send_keys": "向桌面程序发送按键",
    },
    "文件": {
        "list_files": "列出目录文件",
        "copy_file": "复制文件",
        "move_file": "移动文件",
        "delete_file": "删除文件",
        "rename_file": "重命名文件",
        "rename_folder": "重命名文件夹",
        "create_folder": "创建文件夹",
        "file_exists": "判断文件是否存在",
        "get_file_info": "获取文件信息",
        "read_text_file": "读取文本文件",
        "write_text_file": "写入文本文件",
        "file_hash_compare": "对比两个文件 Hash",
        "file_diff_compare": "对比两个文件差异",
        "folder_hash_compare": "对比两个文件夹 Hash",
        "folder_diff_compare": "对比两个文件夹差异",
    },
    "Excel/数据表": {
        "read_excel": "读取 Excel",
        "table_add_row": "数据表格添加行",
        "table_add_column": "数据表格添加列",
        "table_set_cell": "设置单元格",
        "table_get_cell": "读取单元格",
        "table_delete_row": "删除行",
        "table_clear": "清空数据表格",
        "table_export": "导出表格",
        "extract_table_data": "从网页提取表格",
    },
    "PDF": {
        "pdf_merge": "合并 PDF",
        "pdf_split": "拆分 PDF",
        "pdf_extract_text": "提取 PDF 文本",
        "pdf_extract_images": "提取 PDF 图像",
        "pdf_to_images": "PDF 转图片",
        "images_to_pdf": "图片转 PDF",
        "pdf_to_word": "PDF 转 Word",
        "pdf_encrypt": "PDF 加密",
        "pdf_decrypt": "PDF 解密",
        "pdf_add_watermark": "PDF 加水印",
        "pdf_compress": "PDF 压缩",
        "pdf_get_info": "获取 PDF 信息",
    },
    "媒体": {
        "screenshot_screen": "屏幕截图",
        "screen_record": "屏幕录制",
        "camera_capture": "摄像头拍照",
        "camera_record": "摄像头录像",
        "format_convert": "音视频格式转换",
        "compress_image": "压缩图片",
        "compress_video": "压缩视频",
        "image_ocr": "图像 OCR 识别",
        "qr_generate": "生成二维码",
        "qr_decode": "识别二维码",
        "audio_to_text": "语音转文字",
        "text_to_speech": "文字转语音",
        "play_music": "播放音频",
        "play_video": "播放视频",
        "view_image": "查看图片",
        "face_recognition": "人脸识别",
        "download_m3u8": "M3U8/HLS 流媒体下载",
        "ytdlp_download": "在线视频下载（YouTube/B站/抖音/Twitter 等 1000+ 站点，基于 yt-dlp）",
        "ytdlp_download_audio": "在线音频下载并转码（mp3/wav/m4a/flac，基于 yt-dlp）",
        "ytdlp_get_info": "查询在线视频元数据（标题/作者/时长/封面/简介，不下载本体）",
        "ytdlp_list_formats": "列出在线视频所有可用清晰度与编码格式",
        "ytdlp_download_subtitle": "下载在线视频字幕（支持自动生成字幕，srt/vtt/ass）",
        "ytdlp_download_playlist": "批量下载播放列表/频道/合集",
    },
    "数据库": {
        "db_connect": "连接 MySQL",
        "db_query": "MySQL 查询",
        "db_execute": "MySQL 执行",
        "db_insert": "MySQL 插入",
        "db_update": "MySQL 更新",
        "db_delete": "MySQL 删除",
        "db_close": "断开 MySQL",
        "oracle_connect": "Oracle 连接",
        "oracle_query": "Oracle 查询",
        "postgresql_connect": "PostgreSQL 连接",
        "postgresql_query": "PostgreSQL 查询",
        "sqlserver_connect": "SQL Server 连接",
        "sqlite_connect": "SQLite 连接",
        "mongodb_find": "MongoDB 查询",
        "redis_get": "Redis 读取",
        "redis_set": "Redis 写入",
    },
    "网络": {
        "api_request": "HTTP 请求",
        "send_email": "发送邮件",
        "webhook_request": "Webhook 请求",
    },
    "通知": {
        "notify_dingtalk": "钉钉通知",
        "notify_wecom": "企业微信通知",
        "notify_feishu": "飞书通知",
        "notify_discord": "Discord 通知",
        "notify_telegram": "Telegram 通知",
        "notify_bark": "Bark 通知",
        "notify_serverchan": "Server酱通知",
        "notify_pushplus": "PushPlus 通知",
        "notify_webhook": "通用 Webhook 通知",
    },
    "QQ/微信": {
        "qq_send_message": "QQ 发送消息（基于 NapCat）",
        "qq_send_image": "QQ 发送图片",
        "qq_send_file": "QQ 发送文件",
        "qq_get_friends": "获取 QQ 好友列表",
        "qq_get_groups": "获取 QQ 群列表",
        "wechat_send_message": "微信发送消息",
        "wechat_send_file": "微信发送文件",
    },
    "飞书": {
        "feishu_bitable_write": "飞书多维表格写入",
        "feishu_bitable_read": "飞书多维表格读取",
        "feishu_sheet_write": "飞书电子表格写入",
        "feishu_sheet_read": "飞书电子表格读取",
    },
    "手机自动化": {
        "phone_tap": "手机点击坐标",
        "phone_swipe": "手机滑动",
        "phone_input_text": "手机输入文字",
        "phone_press_key": "手机按键",
        "phone_screenshot": "手机截图",
        "phone_install_app": "安装 APK",
        "phone_start_app": "启动 App",
        "phone_click_image": "通过图像识别点击手机屏幕",
        "phone_click_text": "通过 OCR 点击手机屏幕文字",
    },
    "触发器": {
        "webhook_trigger": "Webhook 触发器",
        "hotkey_trigger": "全局热键触发",
        "file_watcher_trigger": "文件变化触发",
        "email_trigger": "邮件触发",
        "api_trigger": "API 轮询触发",
        "image_trigger": "屏幕图像触发",
        "sound_trigger": "声音触发",
        "face_trigger": "人脸触发",
        "gesture_trigger": "鼠标手势触发",
        "element_change_trigger": "元素变化触发",
        "scheduled_task": "计划任务（cron）",
        "probability_trigger": "概率触发",
    },
    "系统/工具": {
        "shutdown_system": "关机/重启",
        "lock_screen": "锁屏",
        "set_clipboard": "写剪贴板",
        "get_clipboard": "读剪贴板",
        "system_notification": "系统通知",
        "play_sound": "播放系统提示音",
        "input_prompt": "弹出输入框等用户输入",
        "macro_recorder": "录制宏",
        "export_log": "导出执行日志",
        "print_log": "在日志面板输出",
        "run_command": "执行系统命令",
        "python_script": "执行 Python 脚本",
        "random_number": "生成随机数",
        "get_time": "获取当前时间",
        "timestamp_converter": "时间戳转换",
        "uuid_generator": "生成 UUID",
        "md5_encrypt": "MD5 加密",
        "sha_encrypt": "SHA 加密",
        "url_encode_decode": "URL 编解码",
        "random_password_generator": "生成随机密码",
        "share_folder": "共享文件夹",
        "share_file": "共享文件",
        "stop_share": "停止共享",
        "note": "备注节点（不执行任何动作）",
        "custom_module": "自定义模块（用户封装的子流程）",
    },
    "SAP": {
        "sap_login": "SAP GUI 登录",
        "sap_logout": "SAP GUI 注销",
        "sap_run_tcode": "运行 SAP 事务码",
        "sap_set_field_value": "设置 SAP 字段",
        "sap_click_button": "点击 SAP 按钮",
        "sap_read_gridview": "读取 SAP 网格视图",
    },
    "SSH": {
        "ssh_connect": "SSH 连接",
        "ssh_execute_command": "SSH 执行命令",
        "ssh_upload_file": "SSH 上传文件",
        "ssh_download_file": "SSH 下载文件",
        "ssh_disconnect": "SSH 断开",
    },
    "测试": {
        "allure_init": "Allure 报告初始化",
        "allure_start_test": "Allure 开始测试",
        "allure_add_step": "Allure 添加步骤",
        "allure_stop_test": "Allure 停止测试",
        "allure_generate_report": "Allure 生成报告",
    },
    # ============ 以下为 v2 完整补全：覆盖所有内置模块 ============
    "图像处理（高级）": {
        "image_resize": "图像缩放（按比例或固定宽高）",
        "image_crop": "图像裁剪（指定矩形区域）",
        "image_rotate": "图像旋转",
        "image_flip": "图像翻转（水平/垂直）",
        "image_blur": "图像模糊（高斯模糊）",
        "image_sharpen": "图像锐化",
        "image_brightness": "图像亮度调节",
        "image_contrast": "图像对比度调节",
        "image_color_balance": "图像色彩平衡（RGB 调整）",
        "image_convert_format": "图像格式转换（PNG/JPG/WEBP/BMP/GIF）",
        "image_format_convert": "图像批量格式转换",
        "image_add_text": "图像添加文字",
        "image_merge": "图像合并/拼接",
        "image_thumbnail": "生成缩略图",
        "image_filter": "图像滤镜（怀旧/锐化/边缘检测等）",
        "image_get_info": "获取图像信息（尺寸/格式/EXIF）",
        "image_remove_bg": "AI 自动抠图去背景",
        "image_grayscale": "图像转灰度",
        "image_round_corners": "图像加圆角",
        "bwm_embed_text": "盲水印·把文本以肉眼不可见方式嵌入图像（频域 DWT-DCT-SVD），常用于版权追溯/防泄漏，输出 wm_bit_len 给提取端使用",
        "bwm_extract_text": "盲水印·从图像中提取出之前嵌入的文本，需要相同的两个密码 + 嵌入时的 wm_bit_len",
        "bwm_embed_image": "盲水印·把一张小水印图（推荐黑白二值图）以隐式方式嵌入到载体图，输出水印图尺寸 [h,w] 给提取端使用",
        "bwm_extract_image": "盲水印·从图像中还原出之前嵌入的水印图，需要相同的两个密码 + 嵌入时返回的 [h,w]",
    },
    "视频/音频（高级）": {
        "trim_video": "视频裁剪（截取时间段）",
        "merge_media": "合并多个视频/音频",
        "rotate_video": "视频旋转/翻转",
        "video_speed": "视频倍速（加速/减速）",
        "extract_frame": "从视频中提取帧（封面/关键帧）",
        "extract_audio": "从视频中提取音频",
        "add_subtitle": "给视频添加字幕（烧录或软字幕）",
        "add_watermark": "给视频添加水印",
        "adjust_volume": "调整音频/视频音量",
        "resize_video": "视频分辨率缩放",
        "video_format_convert": "视频格式转换",
        "audio_format_convert": "音频格式转换",
        "video_to_audio": "视频转音频",
        "video_to_gif": "视频转 GIF 动图",
        "batch_format_convert": "批量格式转换（文件夹）",
    },
    "列表/字典/数学（完整）": {
        "list_sum": "列表求和",
        "list_average": "列表平均值",
        "list_max": "列表最大值",
        "list_min": "列表最小值",
        "list_sort": "列表排序",
        "list_unique": "列表去重",
        "list_slice": "列表切片",
        "list_reverse": "列表反转",
        "list_find": "列表查找元素",
        "list_count": "列表统计某元素出现次数",
        "list_filter": "列表过滤（按条件）",
        "list_map": "列表映射（每项应用函数/模板）",
        "list_merge": "列表合并",
        "list_flatten": "列表扁平化（多维转一维）",
        "list_chunk": "列表分块（按 N 个一组）",
        "list_remove_empty": "列表移除空元素",
        "list_intersection": "列表交集",
        "list_union": "列表并集",
        "list_difference": "列表差集",
        "list_cartesian_product": "列表笛卡尔积",
        "list_shuffle": "列表打乱",
        "list_sample": "列表随机抽样",
        "list_operation": "列表通用操作（增/删/改）",
        "list_get": "列表按下标取值",
        "list_length": "列表长度",
        "list_export": "列表导出文件",
        "list_to_string_advanced": "列表转字符串（支持模板）",
        "dict_merge": "字典合并",
        "dict_filter": "字典按键过滤",
        "dict_map_values": "字典值映射",
        "dict_invert": "字典键值反转",
        "dict_sort": "字典排序",
        "dict_deep_copy": "字典深拷贝",
        "dict_get_path": "按路径取嵌套字典值（如 a.b.c）",
        "dict_flatten": "字典扁平化",
        "dict_operation": "字典通用操作",
        "dict_get": "字典按键取值",
        "dict_keys": "获取字典所有键",
        "math_log": "数学对数",
        "math_trig": "三角函数（sin/cos/tan）",
        "math_exp": "指数运算",
        "math_gcd": "最大公约数",
        "math_lcm": "最小公倍数",
        "math_factorial": "阶乘",
        "math_permutation": "排列数",
        "math_percentage": "百分比计算",
        "math_clamp": "数值裁剪到区间",
        "math_random_advanced": "高级随机数（正态分布等）",
        "math_round": "四舍五入",
        "math_base_convert": "进制转换（2/8/10/16）",
        "math_floor": "向下取整",
        "math_modulo": "取模",
        "math_abs": "绝对值",
        "math_sqrt": "平方根",
        "math_power": "幂运算",
    },
    "统计分析": {
        "stat_median": "中位数",
        "stat_mode": "众数",
        "stat_variance": "方差",
        "stat_stdev": "标准差",
        "stat_percentile": "百分位数",
        "stat_normalize": "归一化（0-1）",
        "stat_standardize": "标准化（Z-score）",
    },
    "CSV/格式": {
        "csv_parse": "解析 CSV 字符串/文件为列表",
        "csv_generate": "生成 CSV 字符串/文件",
        "ocr_captcha": "OCR 识别验证码（图片/文字）",
        "slider_captcha": "滑块验证码自动通过",
    },
    "桌面自动化（完整）": {
        "desktop_app_get_info": "获取桌面程序信息",
        "desktop_app_wait_ready": "等待桌面程序就绪",
        "desktop_window_capture": "桌面窗口截图",
        "desktop_window_list": "枚举所有桌面窗口",
        "desktop_window_topmost": "窗口置顶/取消置顶",
        "desktop_wait_control": "等待桌面控件出现",
        "desktop_get_control_info": "获取桌面控件信息",
        "desktop_get_control_tree": "获取桌面控件树",
        "desktop_control_info": "获取控件信息（别名）",
        "desktop_control_tree": "获取控件树（别名）",
        "desktop_get_property": "读取桌面控件属性",
        "desktop_set_value": "设置桌面控件值",
        "desktop_drag_control": "拖动桌面控件",
        "desktop_scroll_control": "滚动桌面控件",
        "desktop_menu_click": "点击桌面菜单项",
        "desktop_checkbox": "桌面复选框操作",
        "desktop_radio": "桌面单选按钮操作",
        "desktop_list_operate": "桌面列表控件操作",
        "desktop_dialog_handle": "桌面对话框处理（确认/取消）",
    },
    "PDF（完整）": {
        "pdf_delete_pages": "PDF 删除指定页面",
        "pdf_insert_pages": "PDF 插入页面",
        "pdf_reorder_pages": "PDF 重排页面顺序",
        "pdf_rotate": "PDF 旋转页面",
    },
    "文档转换（完整）": {
        "markdown_to_html": "Markdown 转 HTML",
        "markdown_to_pdf": "Markdown 转 PDF",
        "markdown_to_docx": "Markdown 转 DOCX",
        "markdown_to_epub": "Markdown 转 EPUB",
        "html_to_markdown": "HTML 转 Markdown",
        "html_to_docx": "HTML 转 DOCX",
        "docx_to_markdown": "DOCX 转 Markdown",
        "docx_to_html": "DOCX 转 HTML",
        "epub_to_markdown": "EPUB 转 Markdown",
        "latex_to_pdf": "LaTeX 转 PDF",
        "rst_to_html": "reStructuredText 转 HTML",
        "org_to_html": "Org-mode 转 HTML",
        "universal_doc_convert": "通用文档转换（基于 pandoc，支持几十种格式互转）",
    },
    "数据库（完整）": {
        "mongodb_connect": "MongoDB 连接",
        "mongodb_disconnect": "MongoDB 断开",
        "mongodb_insert": "MongoDB 插入",
        "mongodb_update": "MongoDB 更新",
        "mongodb_delete": "MongoDB 删除",
        "oracle_disconnect": "Oracle 断开",
        "oracle_execute": "Oracle 执行 SQL",
        "oracle_insert": "Oracle 插入",
        "oracle_update": "Oracle 更新",
        "oracle_delete": "Oracle 删除",
        "postgresql_disconnect": "PostgreSQL 断开",
        "postgresql_execute": "PostgreSQL 执行 SQL",
        "postgresql_insert": "PostgreSQL 插入",
        "postgresql_update": "PostgreSQL 更新",
        "postgresql_delete": "PostgreSQL 删除",
        "sqlserver_query": "SQL Server 查询",
        "sqlserver_disconnect": "SQL Server 断开",
        "sqlserver_execute": "SQL Server 执行 SQL",
        "sqlserver_insert": "SQL Server 插入",
        "sqlserver_update": "SQL Server 更新",
        "sqlserver_delete": "SQL Server 删除",
        "sqlite_query": "SQLite 查询",
        "sqlite_disconnect": "SQLite 断开",
        "sqlite_execute": "SQLite 执行 SQL",
        "sqlite_insert": "SQLite 插入",
        "sqlite_update": "SQLite 更新",
        "sqlite_delete": "SQLite 删除",
        "redis_connect": "Redis 连接",
        "redis_disconnect": "Redis 断开",
        "redis_del": "Redis 删除键",
        "redis_hget": "Redis Hash 取值",
        "redis_hset": "Redis Hash 设值",
    },
    "通知（完整）": {
        "notify_slack": "Slack 通知",
        "notify_msteams": "Microsoft Teams 通知",
        "notify_pushover": "Pushover 推送",
        "notify_pushbullet": "PushBullet 推送",
        "notify_gotify": "Gotify 自建推送",
        "notify_ntfy": "ntfy.sh 推送",
        "notify_matrix": "Matrix 即时通讯通知",
        "notify_rocketchat": "Rocket.Chat 通知",
    },
    "手机自动化（完整）": {
        "phone_long_press": "手机长按",
        "phone_start_mirror": "启动手机投屏",
        "phone_stop_mirror": "停止手机投屏",
        "phone_install_app": "安装 APK",
        "phone_stop_app": "停止 APP",
        "phone_uninstall_app": "卸载 APP",
        "phone_push_file": "把文件推送到手机",
        "phone_pull_file": "从手机拉取文件",
        "phone_wait_image": "等待手机屏幕出现指定图像",
        "phone_image_exists": "判断手机屏幕是否存在某图像",
        "phone_set_volume": "设置手机音量",
        "phone_set_brightness": "设置手机屏幕亮度",
        "phone_set_clipboard": "设置手机剪贴板",
        "phone_get_clipboard": "读取手机剪贴板",
    },
    "QQ（完整）": {
        "qq_get_group_members": "获取 QQ 群成员列表",
        "qq_get_login_info": "获取 QQ 登录信息",
        "qq_wait_message": "等待 QQ 消息",
    },
    "SAP（完整）": {
        "sap_get_field_value": "读取 SAP 字段值",
        "sap_get_status_message": "读取 SAP 状态栏消息",
        "sap_get_title": "读取 SAP 窗口标题",
        "sap_close_warning": "关闭 SAP 警告对话框",
        "sap_set_checkbox": "勾选/取消 SAP 复选框",
        "sap_select_combobox": "选择 SAP 下拉框",
        "sap_select_tab": "切换 SAP 选项卡",
        "sap_send_vkey": "向 SAP 发送虚拟键",
        "sap_set_focus": "设置 SAP 控件焦点",
        "sap_export_gridview_excel": "导出 SAP 网格视图为 Excel",
        "sap_maximize_window": "最大化 SAP 窗口",
    },
    "触发器（完整）": {
        "mouse_trigger": "鼠标触发器（点击/按键监听）",
    },
    "颜色/编码工具": {
        "rgb_to_hsv": "RGB 转 HSV",
        "rgb_to_cmyk": "RGB 转 CMYK",
        "hex_to_cmyk": "HEX 转 CMYK",
    },
    "屏幕共享/打印": {
        "start_screen_share": "开始屏幕共享",
        "stop_screen_share": "停止屏幕共享",
        "printer_call": "调用系统打印机打印",
        "window_focus": "切换窗口焦点",
    },
}


# v2: 完整模块清单单独维护，build 时检查覆盖率
ALL_REGISTERED_MODULES_V2_HINT = (
    "WebRPA 共注册了 460+ 个执行器模块，AI 助手已掌握全部模块的 module_type。"
    "若 LLM 不确定某模块的精确配置参数，应调用 describe_module 或 get_module_full_info 查询。"
)


def get_module_summary() -> str:
    """生成所有模块的简短描述（用于系统提示词）"""
    lines: list[str] = []
    for cat, modules in MODULE_CATEGORIES.items():
        lines.append(f"\n## {cat}")
        for mtype, desc in modules.items():
            lines.append(f"- `{mtype}`: {desc}")
    return "\n".join(lines)


def get_all_known_module_types() -> set[str]:
    """返回知识库中所有已知的 module_type"""
    result: set[str] = set()
    for modules in MODULE_CATEGORIES.values():
        result.update(modules.keys())
    return result


def find_module_description(module_type: str) -> str | None:
    """查找单个模块的描述"""
    for modules in MODULE_CATEGORIES.values():
        if module_type in modules:
            return modules[module_type]
    return None


def build_system_prompt(
    *,
    user_extra_prompt: str = "",
    enable_tools: bool = True,
    workflow_summary: str = "",
    memory_summary: str = "",
) -> str:
    """构建给 LLM 的系统提示词"""
    parts: list[str] = []

    parts.append("""你是「WebRPA小助手」，一个内置在 WebRPA（一款桌面端可视化 RPA 自动化平台）中的全能 AI 助手。

你的职责：
1. 像产品专家一样，回答任何关于 WebRPA 的问题（功能在哪、模块怎么用、为什么不工作等）
2. 主动帮用户搭建工作流：能新建/打开/保存/运行工作流，能添加/修改/删除节点，能配置全局设置
3. 能调用工具操作 WebRPA 的方方面面，所有用户能在 WebRPA 界面里做的事，你都能代用户做
4. 用专业但友好的语气，必要时主动给出建议（例如"使用元素选择器可以避免选错"）

回答原则：
- 用中文回复，简洁清晰，不啰嗦
- 当用户问"怎么做"时，优先调用工具替他完成，而不是只口头说步骤
- 当工具调用失败时，分析原因并向用户解释，提出替代方案
- 当用户的需求模糊时，先简短反问澄清
- 引用模块名时使用反引号，比如 `click_element`、`ai_chat`
- 回复消息、设计工作流、打印日志、命名节点时可以自由使用 emoji（区别于 WebRPA 前端 UI 元素本身禁用 emoji 这条产品规范）

【关键】节点的"模块名"和"业务备注"是两个东西，绝不要混淆：
- **label（模块名）**：节点头部那个粗体大字（如「打开网页」「点击元素」），它是只读的，
  WebRPA 会按 module_type 自动从模块映射表查出官方中文名。**你绝不要试图改 label**，
  那样画布上就会显示错误的模块名（比如把"打开网页"改成"打开淘宝首页"是错的）。
- **name（业务备注）**：模块名右侧括号里的小字，由用户/AI 自由命名，用来说明这个节点的业务作用。
  画布会显示成「<官方模块名> (<name>)」，例如：「打开网页 (登录页)」。
  AI 给节点起业务名时**必须用 name 字段**，不能用 label。
- 给 build_workflow / build_node / add_nodes 传节点数据时，请只传 module_type + name + config，
  不要主动写 label。如果非要写，前端也会自动忽略并按 module_type 还原成官方名。

【关键】查日志时用对工具：
- 当用户问"日志里写了什么 / 帮我看看刚才执行的日志 / 出错在哪一步"时，**必须用** `client_action(action='get_logs')`
  来获取底栏日志面板用户真实看到的逐条日志（含 level/message/time/nodeId/duration），
  这才是用户实际能看到的内容。
- `get_recent_logs` 工具只返回执行汇总（节点数/失败数等），**拿不到用户看到的逐条日志**，
  不要用它代替 `client_action(get_logs)`。
""")

    parts.append("\n# 关于 WebRPA\n")
    parts.append(WEBRPA_OVERVIEW)
    parts.append(WEBRPA_AUTHOR)
    parts.append(WEBRPA_FEATURES)

    parts.append("\n# 内置模块清单（节点 type → 用途）\n")
    parts.append(
        "WebRPA 共 465 个内置执行器，按领域分为 30+ 个分类。"
        "下面是完整清单（左边是 module_type，必须严格使用此精确字符串作为 build_workflow 的 step.type）：\n"
    )
    parts.append(get_module_summary())

    parts.append("\n# 常见问答\n")
    parts.append(WEBRPA_FAQ)

    if memory_summary:
        parts.append("\n# 来自历史对话的长期记忆\n")
        parts.append(memory_summary)

    if workflow_summary:
        parts.append("\n# 当前工作流的状态\n")
        parts.append(workflow_summary)

    if enable_tools:
        parts.append("""
# 工具调用（Skills）

你拥有一组 Skills（工具）可以直接操作 WebRPA。
- 在合适的时机请调用工具，不要让用户手动操作能用工具完成的事
- 一次回复可以连续调用多个工具
- 工具调用结果会作为下一轮上下文回到你这里
- 如果工具失败，分析错误并尝试修复或换一个方案

# 推荐工作流程

1. 当用户提出涉及"现有工作流"、"已经有的"、"项目里"等字眼的需求时，先调用 `get_full_snapshot` 拿到整体上下文
2. 当用户描述要做的事但没有明说节点时，先用 `search_modules` 搜出可能的模块
3. **关键：用户让你"搭建/创建/做一个工作流"时，必须调用 `build_workflow` 一次性产出节点+边**。
   后台会自动把 build_workflow 的结果装入画布（你不需要再手动调 load_workflow_from_data）。
4. **生成工作流时务必兼顾"功能正确"和"排版美观、可读性高"**：
   - 总是为整个工作流写 `title_note`，简述用途+前置条件，会变成顶部蓝色置顶便签
   - 关键步骤为 step 写 `comment`，会自动生成黄色便签贴在节点上方，让用户一眼看懂在做什么
   - 流程过长（>8 步）时把步骤分到不同 `section`（例如「准备阶段」「数据采集」「数据处理」「输出」），避免一长串
   - 一行最多 8 个节点，超过会自动折回；优先靠 section 分行而不是堆在一起
   - 节点 `label` 务必用中文动词短语（例如「打开登录页」、「输入账号」），而不是英文 type
   - 在重要分支/循环/容易出错的地方追加 `notes` 提示
5. 涉及具体修改时尽量用 `client_action` 的细粒度动作（add_nodes/update_node_config/connect_nodes 等），让用户能在画布上实时看到变化
6. 操作前先用 `client_action(action="get_workflow_detail")` 拿到画布的精确状态，避免猜测
7. 长期偏好（"我习惯用 Edge"、"项目目录在 D:\\Tools"）请用 `remember` 写入；下次会话开始时自动有 `recall` 摘要
8. 涉及到批量操作时优先调用 `client_action(action="find_nodes_by_type")` 拿到节点 id 后再批量处理
9. **效率优先：可以同时调用多个无依赖的工具**（例如同时 search_modules('键盘') 和 search_modules('循环')），后端会并行执行
10. 关键节点完成后，可以调用 `client_action(action="show_toast", payload={message:"...", type:"success"})` 给用户一个明显的提示

# 网页自动化的硬性纪律（必读）

涉及"打开网页 / 抓取网页元素 / 填表单 / 点击网页按钮"的工作流，必须按照下面流程：

1. **先 probe → 再造工作流**。在调用 `build_workflow` 之前，必须先调 `probe_page(url=...)`（或用 `get_page_dom_snapshot` 看用户当前页面）。绝对不要凭空猜 selector。
2. probe_page 返回的 `selector_hints` 里就是推荐 selector；列表型目标看 `top_lists`，搜索框看 `search_input`，主标题看 `main_heading`。
3. 拿不准时再调一次 `suggest_selector(target_description="百度热榜列表")`，它会综合骨架+启发式给出按 confidence 排序的候选。
4. 把拿到的 selector 直接填进 `click_element` / `get_text` / `fill_input` / `get_attribute` 等模块的 selector 字段，再用 build_workflow 落地。
5. 如果 probe_page 失败（playwright 没装、网络超时等），降级用 `fetch_page_html(url=...)` 看静态 HTML，从中找规律。
6. 每次完成网页类工作流后，提醒用户也可以用 WebRPA 自带的「元素拾取器」Alt+点击进一步精确选取，作为补充。

举例：用户说"打开百度首页，把热榜内容打印出来"，正确做法是：
  ① 调 `probe_page(url="https://www.baidu.com")`
  ② 看 selector_hints.baidu_hot_item_text_candidates 拿到 `.title-content-title` 之类的真实 selector
  ③ 调 `build_workflow` 生成 [打开页面 → 等待元素 → 获取列表文本（多个） → 循环打印]
绝对不能跳过 ① 直接编 selector！
""")

    if user_extra_prompt:
        parts.append("\n# 用户附加指令\n")
        parts.append(user_extra_prompt)

    return "\n".join(parts)
