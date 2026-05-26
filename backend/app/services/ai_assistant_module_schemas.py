"""模块配置 schema 速查表（给 AI 参考）

为每个 module_type 列出：
- required: 必填字段（列表）
- optional: 推荐配置字段（列表）
- defaults: 默认值（dict，AI 没填时后端会自动补）
- desc: 字段中文说明（dict）
- example: 一个完整的 config 配置样例
- combo: 经常和它搭配的下一个/上一个模块（让 AI 知道怎么联动）

数据来源：基于 frontend/src/store/workflowStore.ts 的 addNode defaultData
+ frontend/src/components/workflow/config-panels/*.tsx 的实际字段
+ backend/app/executors/*.py 的实现
"""
from __future__ import annotations

# 字段说明：
#   selector  CSS / XPath 选择器（点击/输入/获取数据等模块都用）
#   url       网页地址
#   timeout   超时秒数（默认值取自 store；用户配置高级配置时是毫秒）

# 浏览器 / 网页操作 ============================================================

BROWSER_SCHEMAS: dict = {
    "open_page": {
        "required": ["url"],
        "optional": ["timeout", "headless"],
        "defaults": {},
        "desc": {
            "url": "要打开的网页 URL",
            "timeout": "页面加载超时（秒），默认 30",
            "headless": "是否无头模式（在工具栏选有头/无头时使用）",
        },
        "example": {"url": "https://www.baidu.com"},
        "combo": "通常作为工作流第一步；后接 wait_page_load / click_element / input_text",
    },
    "use_opened_page": {
        "required": [],
        "optional": ["urlMatch"],
        "defaults": {},
        "desc": {"urlMatch": "可选：URL 包含此字符串的页面才会被使用"},
        "example": {},
        "combo": "替代 open_page，连接到用户已经打开的浏览器页面",
    },
    "click_element": {
        "required": ["selector"],
        "optional": ["timeout", "doubleClick"],
        "defaults": {},
        "desc": {
            "selector": "CSS 选择器或 XPath，例如 #search-btn 或 .submit",
            "timeout": "等待元素出现的超时（秒）",
            "doubleClick": "是否双击",
        },
        "example": {"selector": "#kw"},
        "combo": "前序通常是 wait_element 或 input_text；后接 wait_page_load",
    },
    "input_text": {
        "required": ["selector", "text"],
        "optional": ["clear", "delay"],
        "defaults": {"clear": True},
        "desc": {
            "selector": "输入框的 CSS / XPath 选择器",
            "text": "要输入的文本，可用 {变量名} 引用变量",
            "clear": "输入前是否先清空（默认 true）",
            "delay": "每个字符的间隔毫秒",
        },
        "example": {"selector": "#kw", "text": "WebRPA"},
        "combo": "通常前面 wait_element，后面 click_element 提交",
    },
    "hover_element": {
        "required": ["selector"],
        "optional": ["timeout"],
        "defaults": {},
        "desc": {"selector": "CSS / XPath 选择器", "timeout": "等待超时秒"},
        "example": {"selector": ".menu-item"},
        "combo": "悬停后下拉菜单出现，再 click_element 触发菜单项",
    },
    "select_dropdown": {
        "required": ["selector"],
        "optional": ["value", "label", "index"],
        "defaults": {},
        "desc": {"selector": "<select> 选择器", "value": "按 value 选", "label": "按显示文本选", "index": "按索引选"},
        "example": {"selector": "#country", "label": "中国"},
        "combo": "",
    },
    "set_checkbox": {
        "required": ["selector", "checked"],
        "optional": [],
        "defaults": {"checked": True},
        "desc": {"selector": "复选框选择器", "checked": "true=勾选，false=取消"},
        "example": {"selector": "#agree", "checked": True},
        "combo": "",
    },
    "scroll_page": {
        "required": [],
        "optional": ["direction", "distance", "selector"],
        "defaults": {"direction": "down", "distance": 500},
        "desc": {"direction": "up/down/left/right/top/bottom", "distance": "像素", "selector": "可选：滚动到指定元素"},
        "example": {"direction": "down", "distance": 800},
        "combo": "动态加载页面常用，后接 wait_element 等新内容出现",
    },
    "wait": {
        "required": ["seconds"],
        "optional": [],
        "defaults": {"seconds": 1},
        "desc": {"seconds": "等待秒数"},
        "example": {"seconds": 2},
        "combo": "调试用；生产环境优先用 wait_element / wait_page_load",
    },
    "wait_element": {
        "required": ["selector"],
        "optional": ["timeout", "state"],
        "defaults": {"timeout": 10, "state": "visible"},
        "desc": {
            "selector": "等待出现的元素选择器",
            "timeout": "最大等待秒数",
            "state": "visible/attached/hidden/detached",
        },
        "example": {"selector": ".result-list", "timeout": 15},
        "combo": "比 wait 更可靠，建议替代 wait",
    },
    "wait_page_load": {
        "required": [],
        "optional": ["timeout", "state"],
        "defaults": {"timeout": 30, "state": "load"},
        "desc": {"timeout": "最大等待秒", "state": "load/domcontentloaded/networkidle"},
        "example": {"timeout": 30},
        "combo": "open_page / click_element 之后保险等加载完",
    },
    "refresh_page": {
        "required": [],
        "optional": [],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "",
    },
    "go_back": {"required": [], "optional": [], "defaults": {}, "desc": {}, "example": {}, "combo": ""},
    "go_forward": {"required": [], "optional": [], "defaults": {}, "desc": {}, "example": {}, "combo": ""},
    "close_page": {"required": [], "optional": [], "defaults": {}, "desc": {}, "example": {}, "combo": "工作流末尾常用"},
    "switch_tab": {
        "required": [],
        "optional": ["index", "urlMatch"],
        "defaults": {},
        "desc": {"index": "按索引切（0 是第一个标签）", "urlMatch": "按 URL 包含切"},
        "example": {"index": 1},
        "combo": "",
    },
    "switch_iframe": {
        "required": ["selector"],
        "optional": [],
        "defaults": {},
        "desc": {"selector": "iframe 元素选择器"},
        "example": {"selector": "iframe[name='login']"},
        "combo": "进入 iframe 后才能操作里面的元素，结束后用 switch_to_main 退出",
    },
    "switch_to_main": {"required": [], "optional": [], "defaults": {}, "desc": {}, "example": {}, "combo": "退出 iframe 回到主页面"},
    "inject_javascript": {
        "required": ["script"],
        "optional": ["saveResult"],
        "defaults": {"saveResult": "js_result"},
        "desc": {
            "script": "JS 代码，return 的值会保存到 saveResult 变量",
            "saveResult": "结果变量名",
        },
        "example": {"script": "return document.title", "saveResult": "page_title"},
        "combo": "拿不到页面信息时的万能方案",
    },
    "handle_dialog": {
        "required": ["action"],
        "optional": ["text"],
        "defaults": {"action": "accept"},
        "desc": {"action": "accept/dismiss", "text": "如果是 prompt 框，要输入的文本"},
        "example": {"action": "accept"},
        "combo": "open_page 之前先 handle_dialog 防止弹框卡住",
    },
    "upload_file": {
        "required": ["selector", "filePath"],
        "optional": [],
        "defaults": {},
        "desc": {"selector": "<input type=file> 选择器", "filePath": "本地文件绝对路径"},
        "example": {"selector": "#fileInput", "filePath": "C:\\\\file.pdf"},
        "combo": "",
    },
    "screenshot": {
        "required": [],
        "optional": ["fileName", "selector", "fullPage", "variableName"],
        "defaults": {"variableName": "screenshot_path", "fullPage": False},
        "desc": {
            "fileName": "保存的文件名（可选，默认按时间戳）",
            "selector": "可选：只截某个元素",
            "fullPage": "是否截整个页面（含滚动区）",
            "variableName": "保存截图路径到变量",
        },
        "example": {"fullPage": True, "variableName": "page_shot"},
        "combo": "",
    },
    "get_element_info": {
        "required": ["selector"],
        "optional": ["attribute", "variableName", "multiple"],
        "defaults": {"variableName": "element_value", "attribute": "text", "multiple": False},
        "desc": {
            "selector": "目标元素选择器",
            "attribute": "text(默认)/value/href/src/innerHTML/data-xxx 等任意属性",
            "multiple": "true=匹配所有元素返回数组",
            "variableName": "结果变量",
        },
        "example": {"selector": ".title", "attribute": "text", "variableName": "page_title"},
        "combo": "数据采集核心，配合 foreach 遍历列表",
    },
    "extract_table_data": {
        "required": ["selector"],
        "optional": ["resultVariable", "headerRow"],
        "defaults": {"resultVariable": "table_data", "headerRow": True},
        "desc": {
            "selector": "<table> 元素选择器",
            "headerRow": "第一行是否表头",
            "resultVariable": "结果变量（数组）",
        },
        "example": {"selector": "table.data-list", "resultVariable": "rows"},
        "combo": "后接 foreach 遍历每行",
    },
    "download_file": {
        "required": ["url"],
        "optional": ["savePath", "fileName", "resultVariable"],
        "defaults": {"resultVariable": "downloaded_path"},
        "desc": {"url": "文件 URL", "savePath": "保存目录", "fileName": "文件名"},
        "example": {"url": "{file_url}", "savePath": "D:\\\\Downloads"},
        "combo": "",
    },
    "drag_element": {
        "required": ["sourceSelector", "targetSelector"],
        "optional": [],
        "defaults": {},
        "desc": {"sourceSelector": "起点元素", "targetSelector": "终点元素"},
        "example": {"sourceSelector": ".item", "targetSelector": ".target"},
        "combo": "",
    },
}

# 流程控制 ====================================================================

CONTROL_SCHEMAS: dict = {
    "condition": {
        "required": ["operator"],
        "optional": ["leftValue", "rightValue"],
        "defaults": {"operator": "equals"},
        "desc": {
            "operator": "equals/not_equals/greater/less/contains/starts_with/ends_with/regex_match/is_empty/is_not_empty",
            "leftValue": "左值（可用变量 {var}）",
            "rightValue": "右值",
        },
        "example": {"leftValue": "{count}", "operator": "greater", "rightValue": "10"},
        "combo": "有 2 个出口：true 走「是」分支，false 走「否」分支",
    },
    "loop": {
        "required": ["loopType"],
        "optional": ["loopCount", "indexVariable"],
        "defaults": {"loopType": "count", "loopCount": "10", "indexVariable": "index"},
        "desc": {
            "loopType": "count(固定次数)/while(条件循环)",
            "loopCount": "循环次数",
            "indexVariable": "当前索引变量名",
        },
        "example": {"loopType": "count", "loopCount": "5", "indexVariable": "i"},
        "combo": "loop → 循环体节点 → break_loop / continue_loop / 结束",
    },
    "foreach": {
        "required": ["listVariable"],
        "optional": ["itemVariable", "indexVariable"],
        "defaults": {"itemVariable": "item", "indexVariable": "index"},
        "desc": {
            "listVariable": "要遍历的变量名（不带 {}）",
            "itemVariable": "当前项变量名",
            "indexVariable": "当前索引变量名",
        },
        "example": {"listVariable": "rows", "itemVariable": "row", "indexVariable": "i"},
        "combo": "和 extract_table_data / get_element_info(multiple=true) 配合最常见",
    },
    "foreach_dict": {
        "required": ["dictVariable"],
        "optional": ["keyVariable", "valueVariable"],
        "defaults": {"keyVariable": "key", "valueVariable": "value"},
        "desc": {"dictVariable": "字典变量名", "keyVariable": "键变量", "valueVariable": "值变量"},
        "example": {"dictVariable": "user_info"},
        "combo": "",
    },
    "break_loop": {"required": [], "optional": [], "defaults": {}, "desc": {}, "example": {}, "combo": "在 loop/foreach 中跳出"},
    "continue_loop": {"required": [], "optional": [], "defaults": {}, "desc": {}, "example": {}, "combo": "跳过当前迭代"},
    "stop_workflow": {"required": [], "optional": ["reason"], "defaults": {}, "desc": {"reason": "停止原因"}, "example": {}, "combo": ""},
    "subflow": {
        "required": ["subflowName"],
        "optional": ["parameterValues"],
        "defaults": {},
        "desc": {"subflowName": "子流程名", "parameterValues": "传入的参数（dict）"},
        "example": {"subflowName": "登录流程"},
        "combo": "复用工作流的关键，把重复逻辑做成子流程",
    },
}

# 变量 / 数据 =================================================================

DATA_SCHEMAS: dict = {
    "set_variable": {
        "required": ["variableName", "value"],
        "optional": ["variableType"],
        "defaults": {"variableName": "my_var", "variableType": "string"},
        "desc": {
            "variableName": "变量名",
            "value": "值（可用 {其他变量} 引用）",
            "variableType": "string/number/boolean/array/object",
        },
        "example": {"variableName": "user_name", "value": "张三"},
        "combo": "",
    },
    "increment_decrement": {
        "required": ["variableName", "operation"],
        "optional": ["step"],
        "defaults": {"operation": "increment", "step": "1"},
        "desc": {"operation": "increment/decrement", "step": "步长"},
        "example": {"variableName": "count", "operation": "increment", "step": "1"},
        "combo": "",
    },
    "json_parse": {
        "required": ["jsonText"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "parsed_json"},
        "desc": {"jsonText": "JSON 字符串（常用 {api_response} 引用）", "resultVariable": "结果变量"},
        "example": {"jsonText": "{api_response}", "resultVariable": "data"},
        "combo": "通常 api_request 之后立即 json_parse",
    },
    "base64": {
        "required": ["operation", "input"],
        "optional": ["resultVariable"],
        "defaults": {"operation": "encode", "resultVariable": "base64_result"},
        "desc": {"operation": "encode/decode", "input": "输入"},
        "example": {"operation": "encode", "input": "{file_content}"},
        "combo": "",
    },
    "random_number": {
        "required": [],
        "optional": ["min", "max", "isFloat", "variableName"],
        "defaults": {"min": "1", "max": "100", "isFloat": False, "variableName": "random_num"},
        "desc": {"min": "最小值", "max": "最大值", "isFloat": "是否浮点", "variableName": "结果变量"},
        "example": {"min": "1", "max": "9999"},
        "combo": "",
    },
    "get_time": {
        "required": [],
        "optional": ["format", "variableName"],
        "defaults": {"format": "YYYY-MM-DD HH:mm:ss", "variableName": "current_time"},
        "desc": {"format": "时间格式串", "variableName": "结果变量"},
        "example": {"format": "YYYY-MM-DD"},
        "combo": "",
    },
    "regex_extract": {
        "required": ["text", "pattern"],
        "optional": ["mode", "groupIndex", "resultVariable"],
        "defaults": {"mode": "first", "groupIndex": 0, "resultVariable": "regex_result"},
        "desc": {"text": "源文本", "pattern": "正则表达式", "mode": "first/all/match", "groupIndex": "捕获组索引"},
        "example": {"text": "{html}", "pattern": "<h1>(.+?)</h1>", "groupIndex": 1},
        "combo": "",
    },
    "string_replace": {
        "required": ["text", "search", "replace"],
        "optional": ["resultVariable", "useRegex"],
        "defaults": {"useRegex": False, "resultVariable": "replace_result"},
        "desc": {"text": "源文本", "search": "查找的内容", "replace": "替换为", "useRegex": "是否当正则"},
        "example": {"text": "{raw}", "search": " ", "replace": ""},
        "combo": "",
    },
    "string_split": {
        "required": ["text", "separator"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "split_result"},
        "desc": {"text": "源文本", "separator": "分隔符"},
        "example": {"text": "{csv_line}", "separator": ","},
        "combo": "后接 foreach 遍历分割结果",
    },
    "string_join": {
        "required": ["listVariable", "separator"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "join_result"},
        "desc": {"listVariable": "列表变量名", "separator": "连接符"},
        "example": {"listVariable": "items", "separator": "、"},
        "combo": "",
    },
    "string_concat": {
        "required": ["values"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "concat_result"},
        "desc": {"values": "要拼接的文本（数组或多个字段）"},
        "example": {"values": ["前缀-", "{name}", "-后缀"]},
        "combo": "",
    },
}

# 数据表 / 列表 ===============================================================

LIST_SCHEMAS: dict = {
    "list_operation": {
        "required": ["listVariable", "operation"],
        "optional": ["item", "index", "resultVariable"],
        "defaults": {"resultVariable": "list_result"},
        "desc": {"listVariable": "列表变量", "operation": "append/prepend/insert/remove/reverse/clear", "item": "项", "index": "插入索引"},
        "example": {"listVariable": "items", "operation": "append", "item": "{new_item}"},
        "combo": "",
    },
    "list_get": {
        "required": ["listVariable", "index"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "list_item"},
        "desc": {"listVariable": "列表变量", "index": "下标（0-based，-1 = 最后一个）"},
        "example": {"listVariable": "rows", "index": "0"},
        "combo": "",
    },
    "list_length": {
        "required": ["listVariable"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "list_len"},
        "desc": {"listVariable": "列表变量"},
        "example": {"listVariable": "rows"},
        "combo": "",
    },
    "dict_operation": {
        "required": ["dictVariable", "operation"],
        "optional": ["key", "value", "resultVariable"],
        "defaults": {"resultVariable": "dict_result"},
        "desc": {"operation": "set/delete/clear/merge"},
        "example": {"dictVariable": "user", "operation": "set", "key": "name", "value": "Tom"},
        "combo": "",
    },
    "dict_get": {
        "required": ["dictVariable", "key"],
        "optional": ["resultVariable", "defaultValue"],
        "defaults": {"resultVariable": "dict_value"},
        "desc": {"defaultValue": "key 不存在时返回的兜底值"},
        "example": {"dictVariable": "user", "key": "name"},
        "combo": "",
    },
    "dict_keys": {
        "required": ["dictVariable"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "dict_keys"},
        "desc": {},
        "example": {"dictVariable": "user"},
        "combo": "后接 foreach 遍历键",
    },
    "table_add_row": {
        "required": ["row"],
        "optional": [],
        "defaults": {},
        "desc": {"row": "字典或字段映射"},
        "example": {"row": {"name": "{name}", "age": "{age}"}},
        "combo": "数据采集时常用，工作流末尾导出",
    },
    "table_add_column": {
        "required": ["column"],
        "optional": ["defaultValue"],
        "defaults": {},
        "desc": {"column": "列名"},
        "example": {"column": "新列"},
        "combo": "",
    },
    "table_export": {
        "required": ["filePath"],
        "optional": ["sheetName"],
        "defaults": {"sheetName": "Sheet1"},
        "desc": {"filePath": "导出文件绝对路径（.xlsx 或 .csv）"},
        "example": {"filePath": "D:\\\\result.xlsx"},
        "combo": "工作流末尾把采集到的数据落盘",
    },
}

# AI / 网络 ===================================================================

AI_NET_SCHEMAS: dict = {
    "ai_chat": {
        "required": ["userPrompt"],
        "optional": ["apiUrl", "apiKey", "model", "systemPrompt", "temperature", "maxTokens", "variableName"],
        "defaults": {"temperature": 0.7, "maxTokens": 2000, "variableName": "ai_response"},
        "desc": {
            "userPrompt": "用户提示词，可用 {var} 引用",
            "systemPrompt": "系统提示词（角色设定）",
            "apiUrl/apiKey/model": "通常已在全局配置预填，留空即可",
            "variableName": "保存 AI 回复的变量",
        },
        "example": {"userPrompt": "总结这段：{content}", "variableName": "summary"},
        "combo": "前接 get_element_info 拿到内容；后接 set_variable / table_add_row 落盘",
    },
    "ai_vision": {
        "required": ["userPrompt", "imageSource"],
        "optional": ["imageSelector", "imageUrl", "imageVariable", "model", "variableName", "maxTokens"],
        "defaults": {"imageSource": "element", "variableName": "vision_result", "maxTokens": 1000},
        "desc": {
            "imageSource": "element/screenshot/url/variable",
            "imageSelector": "imageSource=element 时填",
            "imageUrl": "imageSource=url 时填",
            "imageVariable": "imageSource=variable 时填",
            "userPrompt": "对图片提问",
        },
        "example": {"imageSource": "screenshot", "userPrompt": "图片中有几个人？"},
        "combo": "和 screenshot 配合：先截屏再问 AI",
    },
    "api_request": {
        "required": ["url", "method"],
        "optional": ["headers", "body", "params", "resultVariable", "timeout"],
        "defaults": {"method": "GET", "resultVariable": "api_response", "timeout": 30},
        "desc": {
            "method": "GET/POST/PUT/DELETE/PATCH",
            "headers": "请求头（dict）",
            "body": "请求体（JSON 字符串）",
            "params": "查询参数（dict）",
        },
        "example": {"url": "https://api.example.com/data", "method": "GET", "resultVariable": "data"},
        "combo": "后通常接 json_parse 解析返回",
    },
    "send_email": {
        "required": ["to", "subject", "body"],
        "optional": ["senderEmail", "authCode", "smtpServer", "smtpPort", "attachments", "isHtml"],
        "defaults": {"isHtml": False, "smtpPort": 465},
        "desc": {"to": "收件人", "subject": "标题", "body": "正文", "attachments": "附件路径数组"},
        "example": {"to": "user@example.com", "subject": "测试", "body": "Hello"},
        "combo": "全局配置已预填发件人时只需 to/subject/body",
    },
    "read_excel": {
        "required": ["filePath"],
        "optional": ["sheetName", "resultVariable"],
        "defaults": {"resultVariable": "excel_data"},
        "desc": {"filePath": "Excel 文件路径", "sheetName": "Sheet 名（不填取第一个）"},
        "example": {"filePath": "D:\\\\data.xlsx", "resultVariable": "rows"},
        "combo": "后接 foreach 遍历每行",
    },
    "run_command": {
        "required": ["command"],
        "optional": ["resultVariable", "timeout", "shell"],
        "defaults": {"resultVariable": "cmd_output", "timeout": 60, "shell": True},
        "desc": {"command": "命令字符串", "shell": "是否走 shell"},
        "example": {"command": "dir D:\\\\", "resultVariable": "files_list"},
        "combo": "",
    },
    "js_script": {
        "required": ["code"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "js_result"},
        "desc": {"code": "JavaScript 代码（return 的值会保存到 resultVariable）"},
        "example": {"code": "return Math.max({a}, {b})", "resultVariable": "result"},
        "combo": "",
    },
    "python_script": {
        "required": ["code"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "python_result"},
        "desc": {"code": "Python 代码（return 的值会保存到 resultVariable，自动注入所有工作流变量）"},
        "example": {"code": "return sum(rows)", "resultVariable": "total"},
        "combo": "",
    },
    "click_image": {
        "required": ["imagePath"],
        "optional": ["confidence", "timeout", "resultVariable"],
        "defaults": {"confidence": 0.8, "timeout": 10},
        "desc": {"imagePath": "目标图片路径", "confidence": "匹配阈值 0~1"},
        "example": {"imagePath": "D:\\\\btn.png", "confidence": 0.85},
        "combo": "桌面自动化常用，找不到 selector 时用",
    },
    "ocr_captcha": {
        "required": ["imageSource"],
        "optional": ["imageSelector", "imagePath", "resultVariable"],
        "defaults": {"imageSource": "element", "resultVariable": "captcha_text"},
        "desc": {"imageSource": "element/path/screenshot"},
        "example": {"imageSource": "element", "imageSelector": "#captcha"},
        "combo": "前接验证码图片定位，后接 input_text 填入",
    },
}

# 实用工具 ====================================================================

UTIL_SCHEMAS: dict = {
    "print_log": {
        "required": ["message"],
        "optional": ["level"],
        "defaults": {"level": "info"},
        "desc": {"message": "可用 {var} 引用变量", "level": "info/warning/error/success"},
        "example": {"message": "处理到第 {i} 项: {item}"},
        "combo": "调试必备，几乎每一步重要操作后都要 print_log",
    },
    "input_prompt": {
        "required": ["prompt"],
        "optional": ["inputMode", "defaultValue", "variableName"],
        "defaults": {"inputMode": "text", "variableName": "user_input"},
        "desc": {
            "inputMode": "text/password/number/multiline/file/folder/checkbox/slider_int/list",
            "defaultValue": "默认值",
        },
        "example": {"prompt": "请输入用户名", "variableName": "username"},
        "combo": "工作流第一步常用，让用户输入参数",
    },
    "system_notification": {
        "required": ["title", "message"],
        "optional": ["icon", "duration"],
        "defaults": {},
        "desc": {"title": "标题", "message": "正文", "icon": "info/success/warning/error"},
        "example": {"title": "完成", "message": "工作流已运行完毕"},
        "combo": "工作流末尾通知用户结束",
    },
    "play_sound": {
        "required": ["soundFile"],
        "optional": ["volume"],
        "defaults": {"volume": 100},
        "desc": {"soundFile": "音频路径或 system:beep"},
        "example": {"soundFile": "system:beep"},
        "combo": "",
    },
    "set_clipboard": {
        "required": ["content"],
        "optional": [],
        "defaults": {},
        "desc": {"content": "要复制的内容（可用 {var}）"},
        "example": {"content": "{result}"},
        "combo": "",
    },
    "get_clipboard": {
        "required": [],
        "optional": ["variableName"],
        "defaults": {"variableName": "clipboard_content"},
        "desc": {},
        "example": {"variableName": "txt"},
        "combo": "",
    },
}

# 合并所有 schema
_ALL_SCHEMAS: dict[str, dict] = {}
for source in [BROWSER_SCHEMAS, CONTROL_SCHEMAS, DATA_SCHEMAS, LIST_SCHEMAS, AI_NET_SCHEMAS, UTIL_SCHEMAS]:
    _ALL_SCHEMAS.update(source)


def get_module_schema(module_type: str) -> dict | None:
    """查询某个模块的 schema（必填 / 可选 / 默认值 / 字段说明 / 例子 / 联动）"""
    return _ALL_SCHEMAS.get(module_type)


def get_all_module_schemas() -> dict[str, dict]:
    """返回所有内置 schema"""
    return dict(_ALL_SCHEMAS)


def apply_default_config(module_type: str, user_config: dict | None = None) -> dict:
    """合并 schema 默认值 + 用户传的 config，用户值优先"""
    schema = _ALL_SCHEMAS.get(module_type)
    if not schema:
        return user_config or {}
    out = dict(schema.get("defaults") or {})
    if user_config:
        out.update(user_config)
    return out


# ============================================================
# 第二批：文件 / PDF / 媒体 / 加密 / 图像
# ============================================================

FILE_MEDIA_SCHEMAS: dict = {
    # 文件管理
    "list_files": {
        "required": ["folderPath"],
        "optional": ["recursive", "extension", "resultVariable"],
        "defaults": {"recursive": False, "resultVariable": "files_list"},
        "desc": {
            "folderPath": "目标文件夹路径",
            "recursive": "是否递归子文件夹",
            "extension": "只列出指定扩展名（如 .xlsx，留空全部）",
            "resultVariable": "结果变量（数组）",
        },
        "example": {"folderPath": "D:\\\\data", "extension": ".xlsx", "resultVariable": "files"},
        "combo": "后接 foreach 遍历每个文件",
    },
    "copy_file": {
        "required": ["source", "destination"],
        "optional": ["overwrite"],
        "defaults": {"overwrite": True},
        "desc": {"source": "源文件路径", "destination": "目标路径", "overwrite": "是否覆盖已存在文件"},
        "example": {"source": "{file_path}", "destination": "D:\\\\backup\\\\"},
        "combo": "",
    },
    "move_file": {
        "required": ["source", "destination"],
        "optional": ["overwrite"],
        "defaults": {"overwrite": True},
        "desc": {"source": "源", "destination": "目标"},
        "example": {"source": "{file}", "destination": "D:\\\\done\\\\"},
        "combo": "",
    },
    "delete_file": {
        "required": ["path"],
        "optional": [],
        "defaults": {},
        "desc": {"path": "要删除的文件或文件夹路径"},
        "example": {"path": "D:\\\\temp.txt"},
        "combo": "",
    },
    "rename_file": {
        "required": ["path", "newName"],
        "optional": [],
        "defaults": {},
        "desc": {"path": "原文件路径", "newName": "新文件名（不含目录）"},
        "example": {"path": "{old_path}", "newName": "renamed.txt"},
        "combo": "",
    },
    "create_folder": {
        "required": ["folderPath"],
        "optional": [],
        "defaults": {},
        "desc": {"folderPath": "要创建的文件夹路径"},
        "example": {"folderPath": "D:\\\\new_folder"},
        "combo": "",
    },
    "rename_folder": {
        "required": ["oldPath", "newPath"],
        "optional": [],
        "defaults": {},
        "desc": {"oldPath": "原文件夹路径", "newPath": "新文件夹路径"},
        "example": {"oldPath": "D:\\\\a", "newPath": "D:\\\\b"},
        "combo": "",
    },
    "file_exists": {
        "required": ["path"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "file_exists"},
        "desc": {"path": "文件路径"},
        "example": {"path": "{file}", "resultVariable": "ok"},
        "combo": "前置检查，后接 condition 分支",
    },
    "get_file_info": {
        "required": ["path"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "file_info"},
        "desc": {"path": "文件路径"},
        "example": {"path": "{file}"},
        "combo": "返回大小/修改时间/扩展名等",
    },
    "read_text_file": {
        "required": ["path"],
        "optional": ["encoding", "resultVariable"],
        "defaults": {"encoding": "utf-8", "resultVariable": "file_content"},
        "desc": {"path": "文本文件路径", "encoding": "utf-8/gbk/auto"},
        "example": {"path": "D:\\\\readme.txt", "resultVariable": "txt"},
        "combo": "",
    },
    "write_text_file": {
        "required": ["path", "content"],
        "optional": ["encoding", "append"],
        "defaults": {"encoding": "utf-8", "append": False},
        "desc": {"path": "保存路径", "content": "内容", "append": "是否追加"},
        "example": {"path": "D:\\\\out.txt", "content": "{result}"},
        "combo": "",
    },
    "file_hash_compare": {
        "required": ["file1", "file2"],
        "optional": ["algorithm", "resultVariable"],
        "defaults": {"algorithm": "md5", "resultVariable": "hash_compare_result"},
        "desc": {"algorithm": "md5/sha1/sha256"},
        "example": {"file1": "{a}", "file2": "{b}"},
        "combo": "",
    },
    "file_diff_compare": {
        "required": ["file1", "file2"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "diff_compare_result"},
        "desc": {},
        "example": {"file1": "{a}", "file2": "{b}"},
        "combo": "",
    },

    # PDF 处理
    "pdf_extract_text": {
        "required": ["pdfPath"],
        "optional": ["pageRange", "resultVariable"],
        "defaults": {"resultVariable": "pdf_text"},
        "desc": {"pdfPath": "PDF 路径", "pageRange": "页码范围如 1-5（留空全部）"},
        "example": {"pdfPath": "{pdf}", "resultVariable": "txt"},
        "combo": "",
    },
    "pdf_merge": {
        "required": ["pdfPaths", "outputPath"],
        "optional": [],
        "defaults": {},
        "desc": {"pdfPaths": "PDF 数组（多个文件）", "outputPath": "合并后保存路径"},
        "example": {"pdfPaths": ["a.pdf", "b.pdf"], "outputPath": "D:\\\\merged.pdf"},
        "combo": "",
    },
    "pdf_split": {
        "required": ["pdfPath", "outputDir"],
        "optional": ["pageRanges"],
        "defaults": {},
        "desc": {"pageRanges": "可选：分割段落 [[1,3],[4,6]]"},
        "example": {"pdfPath": "{pdf}", "outputDir": "D:\\\\out"},
        "combo": "",
    },
    "pdf_add_watermark": {
        "required": ["pdfPath", "watermarkText", "outputPath"],
        "optional": ["fontSize", "color", "opacity"],
        "defaults": {"fontSize": 36, "color": "#888888", "opacity": 0.3},
        "desc": {"watermarkText": "水印文字"},
        "example": {"pdfPath": "{pdf}", "watermarkText": "机密", "outputPath": "D:\\\\wm.pdf"},
        "combo": "",
    },
    "pdf_to_images": {
        "required": ["pdfPath", "outputDir"],
        "optional": ["dpi", "imageFormat", "resultVariable"],
        "defaults": {"dpi": 150, "imageFormat": "png", "resultVariable": "pdf_images_paths"},
        "desc": {"dpi": "图片分辨率", "imageFormat": "png/jpg"},
        "example": {"pdfPath": "{pdf}", "outputDir": "D:\\\\imgs"},
        "combo": "",
    },
    "images_to_pdf": {
        "required": ["imagePaths", "outputPath"],
        "optional": [],
        "defaults": {},
        "desc": {"imagePaths": "图片路径数组"},
        "example": {"imagePaths": ["a.png", "b.png"], "outputPath": "D:\\\\out.pdf"},
        "combo": "",
    },
    "pdf_extract_images": {
        "required": ["pdfPath", "outputDir"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "pdf_images"},
        "desc": {},
        "example": {"pdfPath": "{pdf}", "outputDir": "D:\\\\imgs"},
        "combo": "",
    },
    "pdf_get_info": {
        "required": ["pdfPath"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "pdf_info"},
        "desc": {},
        "example": {"pdfPath": "{pdf}"},
        "combo": "返回 页数/作者/标题 等",
    },
    "pdf_to_word": {
        "required": ["pdfPath", "outputPath"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "word_path"},
        "desc": {},
        "example": {"pdfPath": "{pdf}", "outputPath": "D:\\\\out.docx"},
        "combo": "",
    },

    # 媒体 / 视频音频
    "format_convert": {
        "required": ["inputPath", "outputFormat"],
        "optional": ["mediaType", "resultVariable"],
        "defaults": {"mediaType": "video", "outputFormat": "mp4", "resultVariable": "converted_path"},
        "desc": {"mediaType": "video/audio/image", "outputFormat": "目标格式后缀"},
        "example": {"inputPath": "{file}", "outputFormat": "mp4"},
        "combo": "",
    },
    "compress_image": {
        "required": ["inputPath"],
        "optional": ["quality", "outputPath", "resultVariable"],
        "defaults": {"quality": 80, "resultVariable": "compressed_image"},
        "desc": {"quality": "1-100"},
        "example": {"inputPath": "{img}", "quality": 70},
        "combo": "",
    },
    "compress_video": {
        "required": ["inputPath"],
        "optional": ["preset", "crf", "outputPath", "resultVariable"],
        "defaults": {"preset": "medium", "crf": 23, "resultVariable": "compressed_video"},
        "desc": {"preset": "ultrafast/fast/medium/slow", "crf": "18-28，越大越压缩"},
        "example": {"inputPath": "{video}"},
        "combo": "",
    },
    "extract_audio": {
        "required": ["videoPath"],
        "optional": ["audioFormat", "audioBitrate", "outputPath", "resultVariable"],
        "defaults": {"audioFormat": "mp3", "audioBitrate": "192k", "resultVariable": "extracted_audio"},
        "desc": {},
        "example": {"videoPath": "{video}"},
        "combo": "",
    },
    "trim_video": {
        "required": ["videoPath", "startTime", "endTime"],
        "optional": ["outputPath", "resultVariable"],
        "defaults": {"startTime": "00:00:00", "resultVariable": "trimmed_video"},
        "desc": {"startTime": "开始时间 hh:mm:ss", "endTime": "结束时间"},
        "example": {"videoPath": "{video}", "startTime": "00:00:10", "endTime": "00:00:30"},
        "combo": "",
    },
    "merge_media": {
        "required": ["paths"],
        "optional": ["mergeType", "outputPath", "resultVariable"],
        "defaults": {"mergeType": "video", "resultVariable": "merged_file"},
        "desc": {"mergeType": "video/audio", "paths": "路径数组"},
        "example": {"paths": ["a.mp4", "b.mp4"]},
        "combo": "",
    },
    "extract_frame": {
        "required": ["videoPath", "time"],
        "optional": ["outputPath", "resultVariable"],
        "defaults": {"resultVariable": "frame_image"},
        "desc": {"time": "提取时刻 hh:mm:ss 或秒数"},
        "example": {"videoPath": "{video}", "time": "00:00:05"},
        "combo": "",
    },
    "qr_generate": {
        "required": ["text", "outputPath"],
        "optional": ["size", "errorCorrection", "resultVariable"],
        "defaults": {"size": 256, "errorCorrection": "M", "resultVariable": "qr_image"},
        "desc": {"errorCorrection": "L/M/Q/H"},
        "example": {"text": "https://example.com", "outputPath": "D:\\\\qr.png"},
        "combo": "",
    },
    "qr_decode": {
        "required": ["imagePath"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "qr_text"},
        "desc": {},
        "example": {"imagePath": "{qr}"},
        "combo": "",
    },

    # 加密 / 编码
    "md5_encrypt": {
        "required": ["text"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "md5_hash"},
        "desc": {"text": "要加密的文本"},
        "example": {"text": "{password}"},
        "combo": "",
    },
    "sha_encrypt": {
        "required": ["text", "algorithm"],
        "optional": ["resultVariable"],
        "defaults": {"algorithm": "sha256", "resultVariable": "sha_hash"},
        "desc": {"algorithm": "sha1/sha256/sha512"},
        "example": {"text": "{data}", "algorithm": "sha256"},
        "combo": "",
    },
    "url_encode_decode": {
        "required": ["text", "operation"],
        "optional": ["resultVariable"],
        "defaults": {"operation": "encode", "resultVariable": "url_result"},
        "desc": {"operation": "encode/decode"},
        "example": {"text": "{url}", "operation": "encode"},
        "combo": "",
    },
    "uuid_generator": {
        "required": [],
        "optional": ["version", "resultVariable"],
        "defaults": {"version": "4", "resultVariable": "uuid"},
        "desc": {"version": "1/4"},
        "example": {},
        "combo": "",
    },
    "random_password_generator": {
        "required": [],
        "optional": ["length", "includeUppercase", "includeNumbers", "includeSymbols", "resultVariable"],
        "defaults": {"length": 16, "includeUppercase": True, "includeNumbers": True, "includeSymbols": True, "resultVariable": "generated_password"},
        "desc": {},
        "example": {"length": 20},
        "combo": "",
    },
    "timestamp_converter": {
        "required": ["input", "operation"],
        "optional": ["format", "resultVariable"],
        "defaults": {"operation": "to_datetime", "format": "YYYY-MM-DD HH:mm:ss", "resultVariable": "timestamp_result"},
        "desc": {"operation": "to_timestamp / to_datetime"},
        "example": {"input": "2025-01-01", "operation": "to_timestamp"},
        "combo": "",
    },
}

_ALL_SCHEMAS.update(FILE_MEDIA_SCHEMAS)


# ============================================================
# 第三批：触发器 / 计划任务 / 桌面 / 通知 / 数据库
# ============================================================

TRIGGER_DESKTOP_SCHEMAS: dict = {
    # 触发器（用于把工作流变成被动响应式）
    "webhook_trigger": {
        "required": [],
        "optional": ["path", "method", "saveToVariable"],
        "defaults": {"path": "/webhook", "method": "POST", "saveToVariable": "webhook_data"},
        "desc": {"path": "Webhook 路径", "method": "GET/POST", "saveToVariable": "保存请求数据的变量"},
        "example": {"path": "/order-callback", "method": "POST"},
        "combo": "工作流第一个节点；后接 json_parse 解析 webhook_data",
    },
    "hotkey_trigger": {
        "required": ["hotkey"],
        "optional": [],
        "defaults": {},
        "desc": {"hotkey": "快捷键组合，如 Ctrl+Shift+A"},
        "example": {"hotkey": "Ctrl+Alt+R"},
        "combo": "",
    },
    "file_watcher_trigger": {
        "required": ["watchPath"],
        "optional": ["events", "fileTypes", "saveToVariable"],
        "defaults": {"events": ["created", "modified"], "saveToVariable": "file_event"},
        "desc": {"watchPath": "监控的文件夹", "events": "数组：created/modified/deleted/moved", "fileTypes": "扩展名过滤"},
        "example": {"watchPath": "D:\\\\inbox", "events": ["created"]},
        "combo": "",
    },
    "email_trigger": {
        "required": [],
        "optional": ["pollInterval", "filterFrom", "filterSubject", "saveToVariable"],
        "defaults": {"pollInterval": 60, "saveToVariable": "email_data"},
        "desc": {"pollInterval": "轮询间隔秒"},
        "example": {"filterFrom": "boss@company.com"},
        "combo": "",
    },
    "api_trigger": {
        "required": [],
        "optional": ["path", "saveToVariable"],
        "defaults": {"path": "/api/trigger", "saveToVariable": "api_response"},
        "desc": {},
        "example": {"path": "/run-now"},
        "combo": "",
    },
    "mouse_trigger": {
        "required": ["region"],
        "optional": ["button", "saveToVariable"],
        "defaults": {"button": "left", "saveToVariable": "mouse_position"},
        "desc": {"region": "触发区域 {x,y,width,height}", "button": "left/right/middle"},
        "example": {"region": {"x": 0, "y": 0, "width": 100, "height": 100}},
        "combo": "",
    },
    "image_trigger": {
        "required": ["imagePath"],
        "optional": ["confidence", "interval", "saveToVariable"],
        "defaults": {"confidence": 0.8, "interval": 2, "saveToVariable": "image_position"},
        "desc": {"imagePath": "目标图片", "interval": "扫描间隔秒"},
        "example": {"imagePath": "D:\\\\target.png"},
        "combo": "",
    },
    "sound_trigger": {
        "required": ["threshold"],
        "optional": ["saveToVariable"],
        "defaults": {"threshold": 50, "saveToVariable": "sound_volume"},
        "desc": {"threshold": "声音阈值 dB"},
        "example": {"threshold": 70},
        "combo": "",
    },
    "face_trigger": {
        "required": [],
        "optional": ["cameraIndex", "saveToVariable"],
        "defaults": {"cameraIndex": 0, "saveToVariable": "face_detected"},
        "desc": {"cameraIndex": "摄像头索引"},
        "example": {},
        "combo": "",
    },
    "gesture_trigger": {
        "required": ["gestureType"],
        "optional": ["timeout", "cameraIndex", "saveToVariable"],
        "defaults": {"timeout": 60000, "cameraIndex": 0, "saveToVariable": "gesture_info"},
        "desc": {"gestureType": "wave/thumbs_up/peace 等", "timeout": "超时毫秒"},
        "example": {"gestureType": "wave"},
        "combo": "",
    },
    "element_change_trigger": {
        "required": ["selector"],
        "optional": ["interval", "saveNewElementSelector", "saveChangeInfo"],
        "defaults": {"interval": 5, "saveNewElementSelector": "new_element_selector", "saveChangeInfo": "element_change_info"},
        "desc": {"selector": "监控的父元素 selector", "interval": "扫描间隔秒"},
        "example": {"selector": ".comments"},
        "combo": "用于监控网页评论新增、商品上架等",
    },
    "probability_trigger": {
        "required": ["probability"],
        "optional": [],
        "defaults": {"probability": 50},
        "desc": {"probability": "百分比 0-100，路径1 概率"},
        "example": {"probability": 30},
        "combo": "AB 测试 / 灰度分流；有两个出口 path1 和 path2",
    },

    # 计划任务节点
    "scheduled_task": {
        "required": ["scheduleType"],
        "optional": ["cronExpression", "intervalSeconds", "specificTime"],
        "defaults": {"scheduleType": "interval", "intervalSeconds": 300},
        "desc": {"scheduleType": "interval/cron/specific", "cronExpression": "如 0 9 * * *"},
        "example": {"scheduleType": "cron", "cronExpression": "0 9 * * *"},
        "combo": "工作流入口节点",
    },

    # 桌面应用自动化
    "desktop_app_start": {
        "required": ["appPath"],
        "optional": ["arguments", "waitReady"],
        "defaults": {"waitReady": True},
        "desc": {"appPath": "EXE 路径", "arguments": "命令行参数"},
        "example": {"appPath": "C:\\\\app.exe"},
        "combo": "",
    },
    "desktop_app_close": {
        "required": [],
        "optional": ["processName", "force"],
        "defaults": {"force": False},
        "desc": {"processName": "进程名", "force": "强制结束"},
        "example": {"processName": "notepad.exe"},
        "combo": "",
    },
    "desktop_click_control": {
        "required": ["controlSelector"],
        "optional": ["clickType"],
        "defaults": {"clickType": "left"},
        "desc": {"controlSelector": "控件选择器", "clickType": "left/right/double"},
        "example": {"controlSelector": "Button:确定"},
        "combo": "",
    },
    "desktop_input_control": {
        "required": ["controlSelector", "text"],
        "optional": ["clear"],
        "defaults": {"clear": True},
        "desc": {},
        "example": {"controlSelector": "Edit:用户名", "text": "{username}"},
        "combo": "",
    },
    "desktop_get_text": {
        "required": ["controlSelector"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "control_text"},
        "desc": {},
        "example": {"controlSelector": "Text:状态"},
        "combo": "",
    },
    "desktop_window_capture": {
        "required": ["windowTitle"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "window_screenshot"},
        "desc": {"windowTitle": "窗口标题（部分匹配）"},
        "example": {"windowTitle": "记事本"},
        "combo": "",
    },

    # 通知
    "system_notification": {
        "required": ["title", "message"],
        "optional": ["icon", "duration"],
        "defaults": {},
        "desc": {"icon": "info/success/warning/error"},
        "example": {"title": "完成", "message": "工作流执行成功"},
        "combo": "",
    },
    "text_to_speech": {
        "required": ["text"],
        "optional": ["voice", "rate", "volume"],
        "defaults": {"rate": 1.0, "volume": 1.0},
        "desc": {"voice": "声音名（可选）", "rate": "语速 0.1-10", "volume": "音量 0-1"},
        "example": {"text": "工作流已完成"},
        "combo": "",
    },
    "play_sound": {
        "required": ["soundFile"],
        "optional": ["volume"],
        "defaults": {"volume": 100},
        "desc": {"soundFile": "音频路径或 system:beep"},
        "example": {"soundFile": "system:beep"},
        "combo": "",
    },

    # 数据库（核心模块）
    "db_connect": {
        "required": ["host", "user", "password", "database"],
        "optional": ["port", "charset", "connectionVariable"],
        "defaults": {"port": 3306, "charset": "utf8mb4", "connectionVariable": "db_conn"},
        "desc": {"host": "MySQL 主机", "port": "默认 3306"},
        "example": {"host": "localhost", "user": "root", "password": "{db_pwd}", "database": "test"},
        "combo": "成功后用 db_query / db_execute；最后用 db_close 关闭",
    },
    "db_query": {
        "required": ["connectionVariable", "sql"],
        "optional": ["params", "resultVariable"],
        "defaults": {"connectionVariable": "db_conn", "resultVariable": "query_result"},
        "desc": {"sql": "SELECT 语句", "params": "参数化查询参数"},
        "example": {"connectionVariable": "db_conn", "sql": "SELECT * FROM users WHERE age > %s", "params": ["18"]},
        "combo": "",
    },
    "db_execute": {
        "required": ["connectionVariable", "sql"],
        "optional": ["params", "resultVariable"],
        "defaults": {"connectionVariable": "db_conn", "resultVariable": "execute_result"},
        "desc": {"sql": "INSERT/UPDATE/DELETE 等"},
        "example": {"connectionVariable": "db_conn", "sql": "DELETE FROM logs WHERE id = %s", "params": ["{log_id}"]},
        "combo": "",
    },
    "db_insert": {
        "required": ["connectionVariable", "table", "data"],
        "optional": ["resultVariable"],
        "defaults": {"connectionVariable": "db_conn", "resultVariable": "insert_result"},
        "desc": {"table": "表名", "data": "字段映射 dict"},
        "example": {"connectionVariable": "db_conn", "table": "users", "data": {"name": "{n}"}},
        "combo": "",
    },
    "db_close": {
        "required": ["connectionVariable"],
        "optional": [],
        "defaults": {"connectionVariable": "db_conn"},
        "desc": {},
        "example": {"connectionVariable": "db_conn"},
        "combo": "",
    },
}

_ALL_SCHEMAS.update(TRIGGER_DESKTOP_SCHEMAS)


# ============================================================
# 第四批：手机/QQ/微信/SAP/SSH/飞书/AI 媒体/盲水印/通知
# ============================================================

EXTRA_SCHEMAS: dict = {
    # 手机自动化
    "phone_tap": {
        "required": ["x", "y"],
        "optional": ["deviceId"],
        "defaults": {},
        "desc": {"x": "横坐标", "y": "纵坐标", "deviceId": "设备 ID（多设备时用）"},
        "example": {"x": 540, "y": 960},
        "combo": "用拾取按钮拿坐标更准",
    },
    "phone_swipe": {
        "required": ["x1", "y1", "x2", "y2"],
        "optional": ["duration", "deviceId"],
        "defaults": {"duration": 300},
        "desc": {"duration": "滑动毫秒"},
        "example": {"x1": 540, "y1": 1500, "x2": 540, "y2": 500},
        "combo": "",
    },
    "phone_long_press": {
        "required": ["x", "y"],
        "optional": ["duration", "deviceId"],
        "defaults": {"duration": 1000},
        "desc": {"duration": "长按毫秒"},
        "example": {"x": 540, "y": 960, "duration": 1500},
        "combo": "",
    },
    "phone_input_text": {
        "required": ["text"],
        "optional": ["deviceId"],
        "defaults": {},
        "desc": {"text": "输入文本（手机已 ADB 输入法支持中文）"},
        "example": {"text": "{username}"},
        "combo": "通常前面 phone_tap 点中输入框",
    },
    "phone_press_key": {
        "required": ["keyCode"],
        "optional": ["deviceId"],
        "defaults": {},
        "desc": {"keyCode": "如 BACK/HOME/MENU/ENTER"},
        "example": {"keyCode": "BACK"},
        "combo": "",
    },
    "phone_screenshot": {
        "required": [],
        "optional": ["savePath", "deviceId", "resultVariable"],
        "defaults": {"resultVariable": "phone_screenshot"},
        "desc": {},
        "example": {"savePath": "D:\\\\phone.png"},
        "combo": "",
    },
    "phone_click_image": {
        "required": ["imagePath"],
        "optional": ["confidence", "timeout", "deviceId", "resultVariable"],
        "defaults": {"confidence": 0.85, "timeout": 10, "resultVariable": "phone_image_clicked"},
        "desc": {},
        "example": {"imagePath": "D:\\\\target.png"},
        "combo": "",
    },
    "phone_wait_image": {
        "required": ["imagePath"],
        "optional": ["timeout", "deviceId", "resultVariable"],
        "defaults": {"timeout": 30, "resultVariable": "phone_image_found"},
        "desc": {},
        "example": {"imagePath": "D:\\\\splash.png"},
        "combo": "",
    },
    "phone_start_app": {
        "required": ["packageName"],
        "optional": ["deviceId"],
        "defaults": {},
        "desc": {"packageName": "如 com.tencent.mm"},
        "example": {"packageName": "com.tencent.mm"},
        "combo": "",
    },
    "phone_stop_app": {
        "required": ["packageName"],
        "optional": ["deviceId"],
        "defaults": {},
        "desc": {},
        "example": {"packageName": "com.tencent.mm"},
        "combo": "",
    },
    "phone_install_app": {
        "required": ["apkPath"],
        "optional": ["deviceId"],
        "defaults": {},
        "desc": {"apkPath": "本地 APK 路径"},
        "example": {"apkPath": "D:\\\\app.apk"},
        "combo": "",
    },
    "phone_set_clipboard": {
        "required": ["text"],
        "optional": ["deviceId"],
        "defaults": {},
        "desc": {},
        "example": {"text": "{value}"},
        "combo": "",
    },
    "phone_get_clipboard": {
        "required": [],
        "optional": ["deviceId", "resultVariable"],
        "defaults": {"resultVariable": "phone_clipboard_content"},
        "desc": {},
        "example": {},
        "combo": "",
    },

    # QQ 机器人
    "qq_send_message": {
        "required": ["target", "message"],
        "optional": ["messageType", "resultVariable"],
        "defaults": {"messageType": "private", "resultVariable": "qq_msg_result"},
        "desc": {"messageType": "private/group", "target": "QQ 号或群号", "message": "消息内容"},
        "example": {"target": "10001", "message": "你好"},
        "combo": "",
    },
    "qq_send_image": {
        "required": ["target", "imagePath"],
        "optional": ["messageType", "resultVariable"],
        "defaults": {"messageType": "private", "resultVariable": "qq_img_result"},
        "desc": {},
        "example": {"target": "10001", "imagePath": "D:\\\\img.png"},
        "combo": "",
    },
    "qq_send_file": {
        "required": ["target", "filePath"],
        "optional": ["messageType", "resultVariable"],
        "defaults": {"messageType": "private", "resultVariable": "qq_file_result"},
        "desc": {},
        "example": {"target": "10001", "filePath": "D:\\\\report.pdf"},
        "combo": "",
    },
    "qq_wait_message": {
        "required": [],
        "optional": ["sourceType", "matchMode", "matchText", "timeout", "resultVariable"],
        "defaults": {"sourceType": "any", "matchMode": "contains", "timeout": 60, "resultVariable": "qq_received"},
        "desc": {"sourceType": "any/private/group", "matchMode": "contains/equals/regex", "matchText": "匹配字符串"},
        "example": {"matchMode": "contains", "matchText": "查询订单"},
        "combo": "QQ 机器人对话流程：等消息 → 解析 → 回复",
    },
    "qq_get_friends": {
        "required": [],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "qq_friends"},
        "desc": {},
        "example": {},
        "combo": "",
    },
    "qq_get_groups": {
        "required": [],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "qq_groups"},
        "desc": {},
        "example": {},
        "combo": "",
    },

    # 微信
    "wechat_send_message": {
        "required": ["target", "message"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "wechat_msg_result"},
        "desc": {"target": "好友/群聊名"},
        "example": {"target": "文件传输助手", "message": "提醒"},
        "combo": "",
    },
    "wechat_send_file": {
        "required": ["target", "filePath"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "wechat_file_result"},
        "desc": {},
        "example": {"target": "文件传输助手", "filePath": "D:\\\\f.zip"},
        "combo": "",
    },

    # SSH
    "ssh_connect": {
        "required": ["host", "username", "password"],
        "optional": ["port", "connectionVariable"],
        "defaults": {"port": 22, "connectionVariable": "ssh_conn"},
        "desc": {},
        "example": {"host": "192.168.1.100", "username": "root", "password": "{pwd}"},
        "combo": "成功后 ssh_execute_command；最后 ssh_disconnect",
    },
    "ssh_execute_command": {
        "required": ["connectionVariable", "command"],
        "optional": ["timeout", "resultVariable"],
        "defaults": {"connectionVariable": "ssh_conn", "timeout": 60, "resultVariable": "ssh_output"},
        "desc": {},
        "example": {"connectionVariable": "ssh_conn", "command": "df -h"},
        "combo": "",
    },
    "ssh_upload_file": {
        "required": ["connectionVariable", "localPath", "remotePath"],
        "optional": [],
        "defaults": {"connectionVariable": "ssh_conn"},
        "desc": {},
        "example": {"connectionVariable": "ssh_conn", "localPath": "D:\\\\a.txt", "remotePath": "/tmp/a.txt"},
        "combo": "",
    },
    "ssh_download_file": {
        "required": ["connectionVariable", "remotePath", "localPath"],
        "optional": [],
        "defaults": {"connectionVariable": "ssh_conn"},
        "desc": {},
        "example": {"connectionVariable": "ssh_conn", "remotePath": "/var/log/x.log", "localPath": "D:\\\\x.log"},
        "combo": "",
    },
    "ssh_disconnect": {
        "required": ["connectionVariable"],
        "optional": [],
        "defaults": {"connectionVariable": "ssh_conn"},
        "desc": {},
        "example": {"connectionVariable": "ssh_conn"},
        "combo": "",
    },

    # SAP
    "sap_login": {
        "required": ["client", "username", "password"],
        "optional": ["language"],
        "defaults": {"language": "ZH"},
        "desc": {"client": "客户端代码", "language": "EN/ZH"},
        "example": {"client": "100", "username": "{u}", "password": "{p}"},
        "combo": "",
    },
    "sap_run_tcode": {
        "required": ["tcode"],
        "optional": [],
        "defaults": {},
        "desc": {"tcode": "事务码如 VA01"},
        "example": {"tcode": "VA01"},
        "combo": "",
    },
    "sap_set_field_value": {
        "required": ["fieldId", "value"],
        "optional": [],
        "defaults": {},
        "desc": {"fieldId": "SAP 字段 ID", "value": "要填的值"},
        "example": {"fieldId": "VBAK-AUART", "value": "OR"},
        "combo": "",
    },
    "sap_get_field_value": {
        "required": ["fieldId"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "field_value"},
        "desc": {},
        "example": {"fieldId": "VBAK-VBELN"},
        "combo": "",
    },
    "sap_click_button": {
        "required": ["buttonId"],
        "optional": [],
        "defaults": {},
        "desc": {},
        "example": {"buttonId": "btn[8]"},
        "combo": "",
    },
    "sap_logout": {"required": [], "optional": [], "defaults": {}, "desc": {}, "example": {}, "combo": ""},

    # 飞书
    "feishu_bitable_read": {
        "required": ["appToken", "tableId"],
        "optional": ["viewId", "resultVariable"],
        "defaults": {"resultVariable": "bitable_data"},
        "desc": {"appToken": "多维表格 token", "tableId": "数据表 ID"},
        "example": {"appToken": "...", "tableId": "..."},
        "combo": "",
    },
    "feishu_bitable_write": {
        "required": ["appToken", "tableId", "records"],
        "optional": [],
        "defaults": {},
        "desc": {"records": "记录数组"},
        "example": {"appToken": "...", "tableId": "...", "records": [{"name": "Tom"}]},
        "combo": "",
    },

    # AI 媒体
    "ai_generate_image": {
        "required": ["prompt"],
        "optional": ["model", "size", "outputPath", "resultVariable"],
        "defaults": {"size": "1024x1024", "resultVariable": "generated_image"},
        "desc": {"prompt": "图片描述"},
        "example": {"prompt": "一只可爱的猫"},
        "combo": "",
    },
    "ai_generate_video": {
        "required": ["prompt"],
        "optional": ["model", "duration", "outputPath", "resultVariable"],
        "defaults": {"resultVariable": "generated_video"},
        "desc": {},
        "example": {"prompt": "海浪冲击沙滩"},
        "combo": "",
    },
    "audio_to_text": {
        "required": ["audioPath"],
        "optional": ["language", "resultVariable"],
        "defaults": {"language": "auto", "resultVariable": "audio_text"},
        "desc": {"language": "auto/zh/en"},
        "example": {"audioPath": "D:\\\\record.mp3"},
        "combo": "",
    },

    # 盲水印
    "bwm_embed_text": {
        "required": ["inputImagePath", "outputImagePath", "watermarkText", "passwordWm", "passwordImg"],
        "optional": ["resultVariable"],
        "defaults": {"passwordWm": 1, "passwordImg": 1, "resultVariable": "wm_bit_len"},
        "desc": {
            "watermarkText": "要嵌入的文本",
            "passwordWm": "水印密码",
            "passwordImg": "图像密码",
            "resultVariable": "保存 wm_bit_len，提取时必须用",
        },
        "example": {"inputImagePath": "{img}", "outputImagePath": "D:\\\\wm.png", "watermarkText": "© 我"},
        "combo": "嵌入 → 输出 wm_bit_len；提取时用 bwm_extract_text 配合相同密码 + wm_bit_len",
    },
    "bwm_extract_text": {
        "required": ["inputImagePath", "wmBitLen", "passwordWm", "passwordImg"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "extracted_text"},
        "desc": {"wmBitLen": "嵌入时返回的 bit 长度"},
        "example": {"inputImagePath": "D:\\\\wm.png", "wmBitLen": "{wm_bit_len}", "passwordWm": 1, "passwordImg": 1},
        "combo": "",
    },
    "bwm_embed_image": {
        "required": ["inputImagePath", "outputImagePath", "watermarkImagePath", "passwordWm", "passwordImg"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "wm_image_shape"},
        "desc": {"watermarkImagePath": "水印图（推荐黑白二值图）"},
        "example": {"inputImagePath": "{img}", "outputImagePath": "D:\\\\wm.png", "watermarkImagePath": "D:\\\\sig.png"},
        "combo": "",
    },
    "bwm_extract_image": {
        "required": ["inputImagePath", "outputImagePath", "wmShape", "passwordWm", "passwordImg"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "extracted_wm_path"},
        "desc": {"wmShape": "嵌入时返回的 [h,w]"},
        "example": {"inputImagePath": "D:\\\\wm.png", "outputImagePath": "D:\\\\out.png", "wmShape": "{wm_image_shape}"},
        "combo": "",
    },
}

_ALL_SCHEMAS.update(EXTRA_SCHEMAS)


# ============================================================
# 第五批：高级数学/统计/列表/字典 + 多渠道通知 + Allure 测试
# ============================================================

ADVANCED_MATH_SCHEMAS: dict = {
    # 列表高级
    "list_sum": {
        "required": ["listVariable"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "sum_result"},
        "desc": {"listVariable": "数字列表变量名"},
        "example": {"listVariable": "prices"},
        "combo": "",
    },
    "list_average": {
        "required": ["listVariable"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "average_result"},
        "desc": {},
        "example": {"listVariable": "scores"},
        "combo": "",
    },
    "list_max": {
        "required": ["listVariable"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "max_value"},
        "desc": {},
        "example": {"listVariable": "scores"},
        "combo": "",
    },
    "list_min": {
        "required": ["listVariable"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "min_value"},
        "desc": {},
        "example": {"listVariable": "scores"},
        "combo": "",
    },
    "list_sort": {
        "required": ["listVariable"],
        "optional": ["order", "resultVariable"],
        "defaults": {"order": "asc", "resultVariable": "sorted_list"},
        "desc": {"order": "asc/desc"},
        "example": {"listVariable": "items"},
        "combo": "",
    },
    "list_unique": {
        "required": ["listVariable"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "unique_list"},
        "desc": {},
        "example": {"listVariable": "items"},
        "combo": "",
    },
    "list_count": {
        "required": ["listVariable", "target"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "count_result"},
        "desc": {"target": "要统计的值"},
        "example": {"listVariable": "items", "target": "apple"},
        "combo": "",
    },
    "list_filter": {
        "required": ["listVariable", "filterCondition"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "filtered_list"},
        "desc": {"filterCondition": "Python 表达式，item 是当前项"},
        "example": {"listVariable": "scores", "filterCondition": "item > 60"},
        "combo": "",
    },
    "list_map": {
        "required": ["listVariable", "expression"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "mapped_list"},
        "desc": {"expression": "Python 表达式"},
        "example": {"listVariable": "prices", "expression": "item * 1.1"},
        "combo": "",
    },
    "list_slice": {
        "required": ["listVariable", "start"],
        "optional": ["end", "resultVariable"],
        "defaults": {"resultVariable": "sliced_list"},
        "desc": {"start": "起始索引", "end": "结束索引（可选）"},
        "example": {"listVariable": "items", "start": "0", "end": "10"},
        "combo": "",
    },
    "list_reverse": {
        "required": ["listVariable"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "reversed_list"},
        "desc": {},
        "example": {"listVariable": "items"},
        "combo": "",
    },
    "list_merge": {
        "required": ["lists"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "merged_list"},
        "desc": {"lists": "列表数组（变量名数组）"},
        "example": {"lists": ["list_a", "list_b"]},
        "combo": "",
    },
    "list_to_string_advanced": {
        "required": ["listVariable", "separator"],
        "optional": ["resultVariable"],
        "defaults": {"separator": ",", "resultVariable": "joined_string"},
        "desc": {},
        "example": {"listVariable": "items", "separator": "、"},
        "combo": "",
    },

    # 字典高级
    "dict_merge": {
        "required": ["dicts"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "merged_dict"},
        "desc": {"dicts": "字典变量名数组"},
        "example": {"dicts": ["a", "b"]},
        "combo": "",
    },
    "dict_filter": {
        "required": ["dictVariable", "filterCondition"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "filtered_dict"},
        "desc": {"filterCondition": "Python 表达式，key/value 可用"},
        "example": {"dictVariable": "scores", "filterCondition": "value > 60"},
        "combo": "",
    },
    "dict_invert": {
        "required": ["dictVariable"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "inverted_dict"},
        "desc": {},
        "example": {"dictVariable": "name_to_id"},
        "combo": "",
    },
    "dict_sort": {
        "required": ["dictVariable"],
        "optional": ["sortBy", "order", "resultVariable"],
        "defaults": {"sortBy": "key", "order": "asc", "resultVariable": "sorted_dict"},
        "desc": {"sortBy": "key/value"},
        "example": {"dictVariable": "scores", "sortBy": "value", "order": "desc"},
        "combo": "",
    },
    "dict_get_path": {
        "required": ["dictVariable", "path"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "path_value"},
        "desc": {"path": "点路径，如 user.address.city"},
        "example": {"dictVariable": "data", "path": "user.name"},
        "combo": "",
    },
    "dict_flatten": {
        "required": ["dictVariable"],
        "optional": ["separator", "resultVariable"],
        "defaults": {"separator": ".", "resultVariable": "flat_dict"},
        "desc": {},
        "example": {"dictVariable": "nested"},
        "combo": "",
    },

    # 数学
    "math_round": {
        "required": ["value"],
        "optional": ["digits", "resultVariable"],
        "defaults": {"digits": 0, "resultVariable": "round_result"},
        "desc": {"digits": "小数位数"},
        "example": {"value": "{x}", "digits": 2},
        "combo": "",
    },
    "math_floor": {"required": ["value"], "optional": ["resultVariable"], "defaults": {"resultVariable": "floor_result"}, "desc": {}, "example": {"value": "{x}"}, "combo": ""},
    "math_modulo": {"required": ["a", "b"], "optional": ["resultVariable"], "defaults": {"resultVariable": "modulo_result"}, "desc": {}, "example": {"a": "{x}", "b": "10"}, "combo": ""},
    "math_abs": {"required": ["value"], "optional": ["resultVariable"], "defaults": {"resultVariable": "abs_result"}, "desc": {}, "example": {"value": "{x}"}, "combo": ""},
    "math_sqrt": {"required": ["value"], "optional": ["resultVariable"], "defaults": {"resultVariable": "sqrt_result"}, "desc": {}, "example": {"value": "{x}"}, "combo": ""},
    "math_power": {"required": ["base", "exponent"], "optional": ["resultVariable"], "defaults": {"resultVariable": "power_result"}, "desc": {}, "example": {"base": "{x}", "exponent": "2"}, "combo": ""},
    "math_percentage": {
        "required": ["value", "total"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "percentage"},
        "desc": {},
        "example": {"value": "30", "total": "100"},
        "combo": "",
    },
    "math_random_advanced": {
        "required": [],
        "optional": ["min", "max", "decimals", "resultVariable"],
        "defaults": {"min": "0", "max": "1", "decimals": 0, "resultVariable": "random_advanced"},
        "desc": {"decimals": "小数位"},
        "example": {"min": "1", "max": "100"},
        "combo": "",
    },

    # 统计
    "stat_median": {"required": ["listVariable"], "optional": ["resultVariable"], "defaults": {"resultVariable": "median"}, "desc": {}, "example": {"listVariable": "scores"}, "combo": ""},
    "stat_mode": {"required": ["listVariable"], "optional": ["resultVariable"], "defaults": {"resultVariable": "mode"}, "desc": {}, "example": {"listVariable": "scores"}, "combo": ""},
    "stat_variance": {"required": ["listVariable"], "optional": ["resultVariable"], "defaults": {"resultVariable": "variance"}, "desc": {}, "example": {"listVariable": "scores"}, "combo": ""},
    "stat_stdev": {"required": ["listVariable"], "optional": ["resultVariable"], "defaults": {"resultVariable": "stdev"}, "desc": {}, "example": {"listVariable": "scores"}, "combo": ""},
    "csv_parse": {
        "required": ["csvText"],
        "optional": ["delimiter", "hasHeader", "resultVariable"],
        "defaults": {"delimiter": ",", "hasHeader": True, "resultVariable": "csv_data"},
        "desc": {},
        "example": {"csvText": "{file_content}"},
        "combo": "",
    },
    "csv_generate": {
        "required": ["data"],
        "optional": ["delimiter", "resultVariable"],
        "defaults": {"delimiter": ",", "resultVariable": "csv_text"},
        "desc": {"data": "字典数组"},
        "example": {"data": "{rows}"},
        "combo": "",
    },

    # 多渠道通知
    "notify_dingtalk": {
        "required": ["webhook", "message"],
        "optional": ["secret", "atAll"],
        "defaults": {"atAll": False},
        "desc": {"webhook": "钉钉机器人 webhook", "secret": "签名密钥（可选）"},
        "example": {"webhook": "https://oapi.dingtalk.com/...", "message": "{report}"},
        "combo": "",
    },
    "notify_wecom": {
        "required": ["webhook", "message"],
        "optional": ["msgType"],
        "defaults": {"msgType": "text"},
        "desc": {"webhook": "企业微信机器人 webhook", "msgType": "text/markdown"},
        "example": {"webhook": "https://qyapi.weixin.qq.com/...", "message": "..."},
        "combo": "",
    },
    "notify_feishu": {
        "required": ["webhook", "message"],
        "optional": ["secret", "msgType"],
        "defaults": {"msgType": "text"},
        "desc": {},
        "example": {"webhook": "https://open.feishu.cn/...", "message": "..."},
        "combo": "",
    },
    "notify_telegram": {
        "required": ["botToken", "chatId", "message"],
        "optional": ["parseMode"],
        "defaults": {"parseMode": "Markdown"},
        "desc": {},
        "example": {"botToken": "...", "chatId": "...", "message": "..."},
        "combo": "",
    },
    "notify_bark": {
        "required": ["barkUrl", "title", "message"],
        "optional": ["sound"],
        "defaults": {},
        "desc": {"barkUrl": "Bark 推送 URL"},
        "example": {"barkUrl": "https://api.day.app/xxx", "title": "提醒", "message": "工作流完成"},
        "combo": "",
    },
    "notify_slack": {
        "required": ["webhook", "message"],
        "optional": ["channel"],
        "defaults": {},
        "desc": {},
        "example": {"webhook": "...", "message": "..."},
        "combo": "",
    },
    "notify_serverchan": {
        "required": ["sendKey", "title", "message"],
        "optional": [],
        "defaults": {},
        "desc": {"sendKey": "Server酱 send key"},
        "example": {"sendKey": "SCT...", "title": "提醒", "message": "..."},
        "combo": "",
    },

    # Allure 测试报告
    "allure_init": {
        "required": ["resultsPath"],
        "optional": ["projectName", "resultVariable"],
        "defaults": {"resultVariable": "allure_initialized"},
        "desc": {"resultsPath": "结果目录绝对路径"},
        "example": {"resultsPath": "D:\\\\allure-results", "projectName": "我的项目"},
        "combo": "测试流程入口",
    },
    "allure_start_test": {
        "required": ["testName"],
        "optional": ["description", "severity", "tags", "resultVariable"],
        "defaults": {"severity": "normal", "resultVariable": "test_id"},
        "desc": {"severity": "blocker/critical/normal/minor/trivial"},
        "example": {"testName": "登录测试"},
        "combo": "",
    },
    "allure_add_step": {
        "required": ["stepName", "status"],
        "optional": ["description"],
        "defaults": {"status": "passed"},
        "desc": {"status": "passed/failed/skipped/broken"},
        "example": {"stepName": "输入用户名", "status": "passed"},
        "combo": "",
    },
    "allure_add_attachment": {
        "required": ["filePath"],
        "optional": ["name"],
        "defaults": {},
        "desc": {},
        "example": {"filePath": "D:\\\\screenshot.png", "name": "失败截图"},
        "combo": "",
    },
    "allure_stop_test": {
        "required": [],
        "optional": [],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "",
    },
    "allure_generate_report": {
        "required": ["resultsPath", "reportPath"],
        "optional": ["resultVariable"],
        "defaults": {"resultVariable": "report_path"},
        "desc": {},
        "example": {"resultsPath": "D:\\\\allure-results", "reportPath": "D:\\\\allure-report"},
        "combo": "测试流程末尾",
    },
}

_ALL_SCHEMAS.update(ADVANCED_MATH_SCHEMAS)
