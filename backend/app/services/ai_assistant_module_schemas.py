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
