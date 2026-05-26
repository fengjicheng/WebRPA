"""工作流模板库

让 AI 在面对常见需求时直接复用成熟模板，而不是每次从零搭建。

每个模板包含：
- name: 模板名
- description: 用途
- triggers: 触发关键词（用户提问命中这些词应优先考虑）
- steps: 模板步骤（可直接套到 build_workflow）
"""
from __future__ import annotations

WORKFLOW_TEMPLATES: list[dict] = [
    {
        "name": "网页数据采集（单页）",
        "description": "打开页面 → 等待加载 → 提取列表 → 循环打印",
        "triggers": ["采集", "抓取", "爬", "提取", "扒下来", "拿数据"],
        "steps": [
            {"type": "open_page", "label": "打开页面", "config": {"url": "<URL>"}, "comment": "把 URL 替换为真实地址"},
            {"type": "wait_page_load", "label": "等待加载", "config": {"timeout": 30}},
            {"type": "get_element_info", "label": "采集列表", "config": {"selector": "<列表项 selector>", "attribute": "text", "multiple": True, "variableName": "items"}},
            {"type": "foreach", "label": "遍历列表", "config": {"listVariable": "items", "itemVariable": "item", "indexVariable": "i"}},
            {"type": "print_log", "label": "打印", "config": {"message": "第 {i} 项: {item}"}},
        ],
        "tips": [
            "使用前必须先 probe_page 拿真实 selector",
            "如果是动态渲染页面（React/Vue），把 wait_page_load 换成 wait_element 等具体元素",
        ],
    },
    {
        "name": "API 调用 + 解析数据",
        "description": "请求 API → 解析 JSON → 取字段 → 写到表格",
        "triggers": ["api", "接口", "请求", "调用", "json"],
        "steps": [
            {"type": "api_request", "label": "调 API", "config": {"url": "<URL>", "method": "GET", "resultVariable": "raw"}},
            {"type": "json_parse", "label": "解析 JSON", "config": {"jsonText": "{raw}", "resultVariable": "data"}},
            {"type": "foreach", "label": "遍历记录", "config": {"listVariable": "data.items", "itemVariable": "row"}},
            {"type": "table_add_row", "label": "写入表格", "config": {"row": "{row}"}},
            {"type": "table_export", "label": "导出 Excel", "config": {"filePath": "D:\\\\result.xlsx"}},
        ],
        "tips": ["如果接口返回的是嵌套结构，用 dict_get_path 取字段；如果有分页，外层加一个 loop"],
    },
    {
        "name": "登录后操作",
        "description": "打开登录页 → 输入账号密码 → 点登录 → 等跳转 → 后续业务操作",
        "triggers": ["登录", "登陆", "login"],
        "steps": [
            {"type": "open_page", "label": "打开登录页", "config": {"url": "<登录页 URL>"}},
            {"type": "wait_element", "label": "等输入框", "config": {"selector": "<用户名 selector>", "timeout": 15}},
            {"type": "input_text", "label": "输入用户名", "config": {"selector": "<用户名 selector>", "text": "<用户名>"}},
            {"type": "input_text", "label": "输入密码", "config": {"selector": "<密码 selector>", "text": "<密码>"}},
            {"type": "click_element", "label": "点登录", "config": {"selector": "<登录按钮 selector>"}},
            {"type": "wait_page_load", "label": "等跳转", "config": {"timeout": 30}},
            {"type": "element_visible", "label": "验证登录成功", "config": {"selector": "<登录后才出现的元素>", "resultVariable": "logged_in"}},
        ],
        "tips": ["敏感字段用 input_prompt(inputMode=password) 让用户运行时输入；或者保存为变量"],
    },
    {
        "name": "Excel 批量处理",
        "description": "读 Excel → 遍历每行 → 业务操作 → 写回新 Excel",
        "triggers": ["excel", "表格", "批量", "处理 xlsx"],
        "steps": [
            {"type": "read_excel", "label": "读取 Excel", "config": {"filePath": "<输入 xlsx 路径>", "resultVariable": "rows"}},
            {"type": "foreach", "label": "遍历行", "config": {"listVariable": "rows", "itemVariable": "row", "indexVariable": "i"}},
            {"type": "print_log", "label": "处理日志", "config": {"message": "处理第 {i} 行: {row}"}},
            {"type": "table_add_row", "label": "结果写表", "config": {"row": "{row}"}},
            {"type": "table_export", "label": "导出", "config": {"filePath": "D:\\\\output.xlsx"}},
        ],
        "tips": [],
    },
    {
        "name": "定时数据采集 → 邮件通知",
        "description": "计划任务触发 → 采集 → 整理 → 发邮件",
        "triggers": ["定时", "每天", "每小时", "通知", "邮件"],
        "steps": [
            {"type": "scheduled_task", "label": "每日 9 点", "config": {"scheduleType": "cron", "cronExpression": "0 9 * * *"}},
            {"type": "open_page", "label": "打开页面", "config": {"url": "<URL>"}},
            {"type": "get_element_info", "label": "采集", "config": {"selector": "<selector>", "attribute": "text", "multiple": True, "variableName": "items"}},
            {"type": "string_join", "label": "整理文本", "config": {"listVariable": "items", "separator": "\\n", "resultVariable": "report"}},
            {"type": "send_email", "label": "发送邮件", "config": {"to": "<收件人>", "subject": "<标题>", "body": "{report}"}},
        ],
        "tips": ["scheduled_task 是入口节点，工作流会被注册成计划任务"],
    },
    {
        "name": "PDF 批量处理",
        "description": "列出 PDF → 逐个提取文本 → 汇总到一个 TXT",
        "triggers": ["pdf", "提取文字", "文档"],
        "steps": [
            {"type": "list_files", "label": "列出 PDF", "config": {"folderPath": "<PDF 目录>", "extension": ".pdf", "resultVariable": "pdfs"}},
            {"type": "foreach", "label": "遍历", "config": {"listVariable": "pdfs", "itemVariable": "pdf"}},
            {"type": "pdf_extract_text", "label": "提取文本", "config": {"pdfPath": "{pdf}", "resultVariable": "txt"}},
            {"type": "write_text_file", "label": "追加到汇总", "config": {"path": "D:\\\\summary.txt", "content": "{txt}\\n---\\n", "append": True}},
        ],
        "tips": [],
    },
    {
        "name": "AI 智能问答",
        "description": "用户输入问题 → AI 回答 → 显示通知",
        "triggers": ["ai", "问答", "ChatGPT", "智能回答"],
        "steps": [
            {"type": "input_prompt", "label": "用户输入", "config": {"prompt": "请输入你的问题", "variableName": "question"}},
            {"type": "ai_chat", "label": "AI 回答", "config": {"userPrompt": "{question}", "variableName": "answer"}},
            {"type": "system_notification", "label": "显示", "config": {"title": "AI 回答", "message": "{answer}"}},
        ],
        "tips": [],
    },
    {
        "name": "文件夹监控自动处理",
        "description": "监控文件夹 → 新文件出现 → 自动处理 → 移动到完成目录",
        "triggers": ["监控文件夹", "自动处理", "文件夹监控"],
        "steps": [
            {"type": "file_watcher_trigger", "label": "监控触发", "config": {"watchPath": "<监控目录>", "events": ["created"], "saveToVariable": "file_event"}},
            {"type": "set_variable", "label": "提取路径", "config": {"variableName": "file_path", "value": "{file_event.path}"}},
            {"type": "print_log", "label": "记录", "config": {"message": "处理新文件：{file_path}"}},
            {"type": "move_file", "label": "移到完成", "config": {"source": "{file_path}", "destination": "<完成目录>"}},
        ],
        "tips": [],
    },
    {
        "name": "网页登录验证 + AI 验证码",
        "description": "登录遇验证码 → 截图 → AI 识别 → 填入",
        "triggers": ["验证码", "captcha", "登录验证"],
        "steps": [
            {"type": "open_page", "label": "打开登录页", "config": {"url": "<URL>"}},
            {"type": "input_text", "label": "用户名", "config": {"selector": "<u-sel>", "text": "<u>"}},
            {"type": "input_text", "label": "密码", "config": {"selector": "<p-sel>", "text": "<p>"}},
            {"type": "ocr_captcha", "label": "识别验证码", "config": {"imageSource": "element", "imageSelector": "<captcha-sel>", "resultVariable": "captcha"}},
            {"type": "input_text", "label": "填验证码", "config": {"selector": "<input-sel>", "text": "{captcha}"}},
            {"type": "click_element", "label": "提交", "config": {"selector": "<btn-sel>"}},
        ],
        "tips": ["验证码识别有失败可能，外层加 loop 重试 3 次更稳"],
    },
]


def get_all_templates() -> list[dict]:
    """返回所有模板的简表（只含 name/description/triggers），用于让 AI 快速浏览"""
    return [
        {"name": t["name"], "description": t["description"], "triggers": t["triggers"]}
        for t in WORKFLOW_TEMPLATES
    ]


def find_template(query: str) -> list[dict]:
    """根据用户的需求文本，找匹配的模板"""
    if not query:
        return []
    q = query.lower()
    matches: list[tuple[int, dict]] = []
    for t in WORKFLOW_TEMPLATES:
        score = 0
        for trig in t.get("triggers", []):
            if trig.lower() in q:
                score += 2
        if t["name"].lower() in q or any(w in q for w in t["name"].lower().split()):
            score += 1
        if score > 0:
            matches.append((score, t))
    matches.sort(key=lambda x: -x[0])
    return [m[1] for m in matches[:5]]


def get_template_by_name(name: str) -> dict | None:
    for t in WORKFLOW_TEMPLATES:
        if t["name"] == name:
            return t
    return None
