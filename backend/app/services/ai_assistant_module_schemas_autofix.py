"""
AI 助手 schema 自动修复补丁(由 _autofix_schemas.py 生成)。

ai_assistant_module_schemas.py 加载完所有原始 schema 后,会 import 这个模块,
用真实代码字段名覆盖那些 required 错误的 schema(共 338 个)。

不要手动修改本文件,运行 backend/_autofix_schemas.py 重新生成。
"""
from __future__ import annotations

# 这些 schema 的字段名是从真实执行器代码自动扫描得到的,与 config.get('xxx') 完全对齐
AUTOFIX_SCHEMAS: dict = {
    "wait": {
        "required": [],
        "optional": [
            "duration",
            "selector",
            "state",
            "waitDuration",
            "waitTime",
            "waitTimeout",
            "waitType"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "调试用；生产环境优先用 wait_element / wait_page_load"
    },
    "switch_iframe": {
        "required": [],
        "optional": [
            "iframeIndex",
            "iframeName",
            "iframeSelector",
            "locateBy"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "进入 iframe 后才能操作里面的元素，结束后用 switch_to_main 退出"
    },
    "inject_javascript": {
        "required": [],
        "optional": [
            "injectMode",
            "javascriptCode",
            "saveResult",
            "targetIndex",
            "targetUrl"
        ],
        "defaults": {
            "saveResult": "js_result"
        },
        "desc": {
            "saveResult": "结果变量名"
        },
        "example": {
            "saveResult": "page_title"
        },
        "combo": "拿不到页面信息时的万能方案"
    },
    "handle_dialog": {
        "required": [],
        "optional": [
            "dialogAction",
            "promptText",
            "saveMessage",
            "text"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "open_page 之前先 handle_dialog 防止弹框卡住"
    },
    "extract_table_data": {
        "required": [],
        "optional": [
            "excelPath",
            "exportToExcel",
            "headerRow",
            "includeHeader",
            "resultVariable",
            "tableSelector",
            "variableName"
        ],
        "defaults": {
            "headerRow": True
        },
        "desc": {
            "headerRow": "第一行是否表头"
        },
        "example": {},
        "combo": "后接 foreach 遍历每行"
    },
    "download_file": {
        "required": [],
        "optional": [
            "downloadMode",
            "downloadUrl",
            "fileName",
            "resultVariable",
            "savePath",
            "triggerSelector",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "savePath": "保存目录",
            "fileName": "文件名"
        },
        "example": {
            "savePath": "D:\\\\Downloads"
        },
        "combo": ""
    },
    "set_variable": {
        "required": [
            "variableName"
        ],
        "optional": [
            "variableType",
            "variableValue"
        ],
        "defaults": {
            "variableName": "my_var"
        },
        "desc": {
            "variableName": "变量名"
        },
        "example": {
            "variableName": "user_name"
        },
        "combo": ""
    },
    "json_parse": {
        "required": [],
        "optional": [
            "columnName",
            "jsonPath",
            "resultVariable",
            "sourceVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "通常 api_request 之后立即 json_parse"
    },
    "base64": {
        "required": [
            "operation"
        ],
        "optional": [
            "fileName",
            "filePath",
            "inputBase64",
            "inputText",
            "outputPath",
            "resultVariable",
            "variableName"
        ],
        "defaults": {
            "operation": "encode"
        },
        "desc": {
            "operation": "encode/decode"
        },
        "example": {
            "operation": "encode"
        },
        "combo": ""
    },
    "regex_extract": {
        "required": [
            "pattern"
        ],
        "optional": [
            "extractMode",
            "groupIndex",
            "ignoreCase",
            "inputText",
            "mode",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "pattern": "正则表达式"
        },
        "example": {
            "pattern": "<h1>(.+?)</h1>"
        },
        "combo": ""
    },
    "string_replace": {
        "required": [],
        "optional": [
            "inputText",
            "replaceAll",
            "replaceMode",
            "replaceValue",
            "resultVariable",
            "searchValue",
            "useRegex",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "string_split": {
        "required": [
            "separator"
        ],
        "optional": [
            "inputText",
            "maxSplit",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "separator": "分隔符"
        },
        "example": {
            "separator": ","
        },
        "combo": "后接 foreach 遍历分割结果"
    },
    "string_concat": {
        "required": [],
        "optional": [
            "resultVariable",
            "string1",
            "string2",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "list_operation": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "index",
            "item",
            "listAction",
            "listIndex",
            "listValue",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "list_result"
        },
        "desc": {
            "listVariable": "列表变量"
        },
        "example": {
            "listVariable": "items"
        },
        "combo": ""
    },
    "list_get": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "listIndex",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "listVariable": "列表变量"
        },
        "example": {
            "listVariable": "rows"
        },
        "combo": ""
    },
    "dict_operation": {
        "required": [
            "dictVariable"
        ],
        "optional": [
            "dictAction",
            "dictKey",
            "dictValue",
            "key",
            "resultVariable",
            "value"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "dictVariable": "user"
        },
        "combo": ""
    },
    "dict_get": {
        "required": [
            "dictVariable"
        ],
        "optional": [
            "defaultValue",
            "dictKey",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "defaultValue": "key 不存在时返回的兜底值"
        },
        "example": {
            "dictVariable": "user"
        },
        "combo": ""
    },
    "table_add_row": {
        "required": [],
        "optional": [
            "rowData"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "数据采集时常用，工作流末尾导出"
    },
    "table_add_column": {
        "required": [],
        "optional": [
            "columnName",
            "defaultValue"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "table_export": {
        "required": [],
        "optional": [
            "exportFormat",
            "fileNamePattern",
            "savePath",
            "sheetName",
            "variableName"
        ],
        "defaults": {
            "sheetName": "Sheet1"
        },
        "desc": {},
        "example": {},
        "combo": "工作流末尾把采集到的数据落盘"
    },
    "api_request": {
        "required": [],
        "optional": [
            "body",
            "followRedirects",
            "headers",
            "params",
            "requestBody",
            "requestCookies",
            "requestHeaders",
            "requestMethod",
            "requestTimeout",
            "requestUrl",
            "resultVariable",
            "timeout",
            "variableName",
            "verifySSL"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "后通常接 json_parse 解析返回"
    },
    "send_email": {
        "required": [],
        "optional": [
            "attachments",
            "authCode",
            "emailContent",
            "emailSubject",
            "isHtml",
            "recipientEmail",
            "senderEmail",
            "smtpPort",
            "smtpServer"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "全局配置已预填发件人时只需 to/subject/body"
    },
    "read_excel": {
        "required": [],
        "optional": [
            "cellAddress",
            "columnIndex",
            "endCell",
            "fileName",
            "readMode",
            "resultVariable",
            "rowIndex",
            "sheetName",
            "startCell",
            "startCol",
            "startRow",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "sheetName": "Sheet 名（不填取第一个）"
        },
        "example": {},
        "combo": "后接 foreach 遍历每行"
    },
    "ocr_captcha": {
        "required": [],
        "optional": [
            "autoSubmit",
            "imagePath",
            "imageSelector",
            "inputSelector",
            "resultVariable",
            "submitSelector",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "imageSelector": "#captcha"
        },
        "combo": "前接验证码图片定位，后接 input_text 填入"
    },
    "system_notification": {
        "required": [],
        "optional": [
            "duration",
            "icon",
            "notifyMessage",
            "notifyTitle"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "play_sound": {
        "required": [],
        "optional": [
            "beepCount",
            "beepInterval",
            "volume"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "set_clipboard": {
        "required": [],
        "optional": [
            "contentType",
            "imagePath",
            "textContent"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "copy_file": {
        "required": [],
        "optional": [
            "overwrite",
            "resultVariable",
            "sourcePath",
            "targetPath"
        ],
        "defaults": {
            "overwrite": True
        },
        "desc": {
            "overwrite": "是否覆盖已存在文件"
        },
        "example": {},
        "combo": ""
    },
    "move_file": {
        "required": [],
        "optional": [
            "overwrite",
            "resultVariable",
            "sourcePath",
            "targetPath"
        ],
        "defaults": {
            "overwrite": True
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "delete_file": {
        "required": [],
        "optional": [
            "deleteType",
            "filePath"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "rename_file": {
        "required": [
            "newName"
        ],
        "optional": [
            "sourcePath",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "newName": "新文件名（不含目录）"
        },
        "example": {
            "newName": "renamed.txt"
        },
        "combo": ""
    },
    "rename_folder": {
        "required": [],
        "optional": [
            "newName",
            "resultVariable",
            "sourcePath"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "file_exists": {
        "required": [],
        "optional": [
            "filePath",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "file_exists"
        },
        "desc": {},
        "example": {
            "resultVariable": "ok"
        },
        "combo": "前置检查，后接 condition 分支"
    },
    "get_file_info": {
        "required": [],
        "optional": [
            "filePath",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "file_info"
        },
        "desc": {},
        "example": {},
        "combo": "返回大小/修改时间/扩展名等"
    },
    "read_text_file": {
        "required": [],
        "optional": [
            "encoding",
            "filePath",
            "resultVariable"
        ],
        "defaults": {
            "encoding": "utf-8",
            "resultVariable": "file_content"
        },
        "desc": {
            "encoding": "utf-8/gbk/auto"
        },
        "example": {
            "resultVariable": "txt"
        },
        "combo": ""
    },
    "write_text_file": {
        "required": [
            "content"
        ],
        "optional": [
            "append",
            "encoding",
            "filePath",
            "resultVariable",
            "writeMode"
        ],
        "defaults": {
            "encoding": "utf-8"
        },
        "desc": {
            "content": "内容"
        },
        "example": {
            "content": "{result}"
        },
        "combo": ""
    },
    "file_hash_compare": {
        "required": [],
        "optional": [
            "algorithm",
            "file1Path",
            "file2Path",
            "hashAlgorithm",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "hash_compare_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "file_diff_compare": {
        "required": [],
        "optional": [
            "file1Path",
            "file2Path",
            "outputFormat",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "diff_compare_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "pdf_merge": {
        "required": [
            "outputPath"
        ],
        "optional": [
            "pdfFiles",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {
            "outputPath": "合并后保存路径"
        },
        "example": {
            "outputPath": "D:\\\\merged.pdf"
        },
        "combo": ""
    },
    "images_to_pdf": {
        "required": [
            "outputPath"
        ],
        "optional": [
            "images",
            "pageSize",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "outputPath": "D:\\\\out.pdf"
        },
        "combo": ""
    },
    "pdf_to_word": {
        "required": [
            "pdfPath"
        ],
        "optional": [
            "outputDir",
            "pageRange",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "word_path"
        },
        "desc": {},
        "example": {
            "pdfPath": "{pdf}"
        },
        "combo": ""
    },
    "extract_audio": {
        "required": [],
        "optional": [
            "audioBitrate",
            "audioFormat",
            "inputPath",
            "outputPath",
            "resultVariable"
        ],
        "defaults": {
            "audioFormat": "mp3",
            "audioBitrate": "192k",
            "resultVariable": "extracted_audio"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "trim_video": {
        "required": [
            "startTime",
            "endTime"
        ],
        "optional": [
            "inputPath",
            "outputPath",
            "resultVariable"
        ],
        "defaults": {
            "startTime": "00:00:00",
            "resultVariable": "trimmed_video"
        },
        "desc": {
            "startTime": "开始时间 hh:mm:ss",
            "endTime": "结束时间"
        },
        "example": {
            "startTime": "00:00:10",
            "endTime": "00:00:30"
        },
        "combo": ""
    },
    "merge_media": {
        "required": [],
        "optional": [
            "audioMode",
            "audioPath",
            "audioVolume",
            "inputFiles",
            "mergeType",
            "originalVolume",
            "outputPath",
            "resultVariable",
            "videoPath"
        ],
        "defaults": {
            "mergeType": "video",
            "resultVariable": "merged_file"
        },
        "desc": {
            "mergeType": "video/audio"
        },
        "example": {},
        "combo": ""
    },
    "extract_frame": {
        "required": [],
        "optional": [
            "imageFormat",
            "inputPath",
            "outputPath",
            "resultVariable",
            "timestamp"
        ],
        "defaults": {
            "resultVariable": "frame_image"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "qr_generate": {
        "required": [],
        "optional": [
            "content",
            "errorCorrection",
            "outputDir",
            "resultVariable",
            "size"
        ],
        "defaults": {
            "size": 256,
            "errorCorrection": "M",
            "resultVariable": "qr_image"
        },
        "desc": {
            "errorCorrection": "L/M/Q/H"
        },
        "example": {},
        "combo": ""
    },
    "qr_decode": {
        "required": [],
        "optional": [
            "inputPath",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "qr_text"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "md5_encrypt": {
        "required": [],
        "optional": [
            "encoding",
            "inputText",
            "outputFormat",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "md5_hash"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "sha_encrypt": {
        "required": [],
        "optional": [
            "encoding",
            "inputText",
            "outputFormat",
            "resultVariable",
            "shaType"
        ],
        "defaults": {
            "resultVariable": "sha_hash"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "url_encode_decode": {
        "required": [
            "operation"
        ],
        "optional": [
            "encoding",
            "inputText",
            "resultVariable"
        ],
        "defaults": {
            "operation": "encode",
            "resultVariable": "url_result"
        },
        "desc": {
            "operation": "encode/decode"
        },
        "example": {
            "operation": "encode"
        },
        "combo": ""
    },
    "timestamp_converter": {
        "required": [
            "operation"
        ],
        "optional": [
            "datetimeFormat",
            "format",
            "inputValue",
            "resultVariable",
            "timestampUnit"
        ],
        "defaults": {
            "operation": "to_datetime",
            "resultVariable": "timestamp_result"
        },
        "desc": {
            "operation": "to_timestamp / to_datetime"
        },
        "example": {
            "operation": "to_timestamp"
        },
        "combo": ""
    },
    "mouse_trigger": {
        "required": [],
        "optional": [
            "button",
            "gesturePattern",
            "gestureTimeout",
            "minGestureDistance",
            "moveDistance",
            "saveToVariable",
            "timeout",
            "triggerType"
        ],
        "defaults": {
            "saveToVariable": "mouse_position"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "sound_trigger": {
        "required": [],
        "optional": [
            "checkInterval",
            "saveToVariable",
            "timeout",
            "volumeThreshold"
        ],
        "defaults": {
            "saveToVariable": "sound_volume"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "gesture_trigger": {
        "required": [],
        "optional": [
            "cameraIndex",
            "debugWindow",
            "gestureName",
            "saveToVariable",
            "timeout"
        ],
        "defaults": {
            "timeout": 60000,
            "cameraIndex": 0,
            "saveToVariable": "gesture_info"
        },
        "desc": {
            "timeout": "超时毫秒"
        },
        "example": {},
        "combo": ""
    },
    "desktop_click_control": {
        "required": [],
        "optional": [
            "clickType",
            "controlInfo",
            "controlVariable",
            "simulate"
        ],
        "defaults": {
            "clickType": "left"
        },
        "desc": {
            "clickType": "left/right/double"
        },
        "example": {},
        "combo": ""
    },
    "desktop_input_control": {
        "required": [
            "text"
        ],
        "optional": [
            "clear",
            "clearBefore",
            "controlInfo",
            "controlVariable",
            "inputMethod"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "text": "{username}"
        },
        "combo": ""
    },
    "desktop_get_text": {
        "required": [],
        "optional": [
            "controlInfo",
            "controlVariable",
            "resultVariable",
            "saveToVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_window_capture": {
        "required": [],
        "optional": [
            "appVariable",
            "resultVariable",
            "savePath",
            "saveToVariable",
            "windowHandle"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "db_query": {
        "required": [
            "sql"
        ],
        "optional": [
            "connectionName",
            "params",
            "resultVariable",
            "singleRow",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "sql": "SELECT 语句"
        },
        "example": {
            "sql": "SELECT * FROM users WHERE age > %s"
        },
        "combo": ""
    },
    "db_execute": {
        "required": [
            "sql"
        ],
        "optional": [
            "connectionName",
            "params",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "sql": "INSERT/UPDATE/DELETE 等"
        },
        "example": {
            "sql": "DELETE FROM logs WHERE id = %s"
        },
        "combo": ""
    },
    "db_insert": {
        "required": [
            "table",
            "data"
        ],
        "optional": [
            "connectionName",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "table": "表名",
            "data": "字段映射 dict"
        },
        "example": {
            "table": "users",
            "data": {
                "name": "{n}"
            }
        },
        "combo": ""
    },
    "db_close": {
        "required": [],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "phone_press_key": {
        "required": [],
        "optional": [
            "deviceId",
            "key",
            "keycode"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "qq_send_message": {
        "required": [
            "message"
        ],
        "optional": [
            "messageType",
            "resultVariable",
            "targetId"
        ],
        "defaults": {
            "messageType": "private",
            "resultVariable": "qq_msg_result"
        },
        "desc": {
            "messageType": "private/group",
            "message": "消息内容"
        },
        "example": {
            "message": "你好"
        },
        "combo": ""
    },
    "qq_send_image": {
        "required": [
            "imagePath"
        ],
        "optional": [
            "messageType",
            "resultVariable",
            "targetId",
            "text"
        ],
        "defaults": {
            "messageType": "private",
            "resultVariable": "qq_img_result"
        },
        "desc": {},
        "example": {
            "imagePath": "D:\\\\img.png"
        },
        "combo": ""
    },
    "qq_send_file": {
        "required": [
            "filePath"
        ],
        "optional": [
            "folderId",
            "messageType",
            "resultVariable",
            "targetId"
        ],
        "defaults": {
            "messageType": "private",
            "resultVariable": "qq_file_result"
        },
        "desc": {},
        "example": {
            "filePath": "D:\\\\report.pdf"
        },
        "combo": ""
    },
    "ssh_execute_command": {
        "required": [
            "command"
        ],
        "optional": [
            "connectionName",
            "errorVariable",
            "exitCodeVariable",
            "outputVariable",
            "resultVariable",
            "timeout"
        ],
        "defaults": {
            "timeout": 60
        },
        "desc": {},
        "example": {
            "command": "df -h"
        },
        "combo": ""
    },
    "ssh_upload_file": {
        "required": [
            "localPath",
            "remotePath"
        ],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "localPath": "D:\\\\a.txt",
            "remotePath": "/tmp/a.txt"
        },
        "combo": ""
    },
    "ssh_download_file": {
        "required": [
            "remotePath",
            "localPath"
        ],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "remotePath": "/var/log/x.log",
            "localPath": "D:\\\\x.log"
        },
        "combo": ""
    },
    "ssh_disconnect": {
        "required": [],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "feishu_bitable_write": {
        "required": [
            "appToken",
            "tableId"
        ],
        "optional": [
            "appId",
            "appSecret",
            "dataSource",
            "fields",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "appToken": "...",
            "tableId": "..."
        },
        "combo": ""
    },
    "audio_to_text": {
        "required": [],
        "optional": [
            "inputPath",
            "language",
            "modelSize",
            "resultVariable"
        ],
        "defaults": {
            "language": "auto",
            "resultVariable": "audio_text"
        },
        "desc": {
            "language": "auto/zh/en"
        },
        "example": {},
        "combo": ""
    },
    "bwm_embed_text": {
        "required": [
            "passwordWm",
            "passwordImg"
        ],
        "optional": [
            "imagePath",
            "outputPath",
            "resultVariable",
            "text"
        ],
        "defaults": {
            "passwordWm": 1,
            "passwordImg": 1,
            "resultVariable": "wm_bit_len"
        },
        "desc": {
            "passwordWm": "水印密码",
            "passwordImg": "图像密码",
            "resultVariable": "保存 wm_bit_len，提取时必须用"
        },
        "example": {},
        "combo": "嵌入 → 输出 wm_bit_len；提取时用 bwm_extract_text 配合相同密码 + wm_bit_len"
    },
    "bwm_extract_text": {
        "required": [
            "wmBitLen",
            "passwordWm",
            "passwordImg"
        ],
        "optional": [
            "imagePath",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "extracted_text"
        },
        "desc": {
            "wmBitLen": "嵌入时返回的 bit 长度"
        },
        "example": {
            "wmBitLen": "{wm_bit_len}",
            "passwordWm": 1,
            "passwordImg": 1
        },
        "combo": ""
    },
    "bwm_embed_image": {
        "required": [
            "passwordWm",
            "passwordImg"
        ],
        "optional": [
            "imagePath",
            "outputPath",
            "resultVariable",
            "watermarkPath"
        ],
        "defaults": {
            "resultVariable": "wm_image_shape"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "bwm_extract_image": {
        "required": [
            "passwordWm",
            "passwordImg"
        ],
        "optional": [
            "imagePath",
            "outputPath",
            "resultVariable",
            "wmHeight",
            "wmWidth"
        ],
        "defaults": {
            "resultVariable": "extracted_wm_path"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "list_count": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "resultVariable",
            "searchValue"
        ],
        "defaults": {
            "resultVariable": "count_result"
        },
        "desc": {},
        "example": {
            "listVariable": "items"
        },
        "combo": ""
    },
    "list_filter": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "compareValue",
            "filterType",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "filtered_list"
        },
        "desc": {},
        "example": {
            "listVariable": "scores"
        },
        "combo": ""
    },
    "list_map": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "operand",
            "operation",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "mapped_list"
        },
        "desc": {},
        "example": {
            "listVariable": "prices"
        },
        "combo": ""
    },
    "list_slice": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "end",
            "endIndex",
            "resultVariable",
            "startIndex"
        ],
        "defaults": {
            "resultVariable": "sliced_list"
        },
        "desc": {},
        "example": {
            "listVariable": "items"
        },
        "combo": ""
    },
    "list_merge": {
        "required": [],
        "optional": [
            "listVariables",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "merged_list"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "dict_merge": {
        "required": [],
        "optional": [
            "dictVariables",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "merged_dict"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "dict_filter": {
        "required": [
            "dictVariable"
        ],
        "optional": [
            "filterKeys",
            "filterMode",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "filtered_dict"
        },
        "desc": {},
        "example": {
            "dictVariable": "scores"
        },
        "combo": ""
    },
    "math_round": {
        "required": [],
        "optional": [
            "decimals",
            "digits",
            "numberValue",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "round_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_floor": {
        "required": [],
        "optional": [
            "numberValue",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "floor_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_modulo": {
        "required": [],
        "optional": [
            "dividend",
            "divisor",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "modulo_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_abs": {
        "required": [],
        "optional": [
            "numberValue",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "abs_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_sqrt": {
        "required": [],
        "optional": [
            "numberValue",
            "resultVariable",
            "root"
        ],
        "defaults": {
            "resultVariable": "sqrt_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_percentage": {
        "required": [],
        "optional": [
            "calcType",
            "resultVariable",
            "value1",
            "value2"
        ],
        "defaults": {
            "resultVariable": "percentage"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "csv_parse": {
        "required": [],
        "optional": [
            "csvString",
            "delimiter",
            "hasHeader",
            "resultVariable"
        ],
        "defaults": {
            "delimiter": ",",
            "hasHeader": True,
            "resultVariable": "csv_data"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "csv_generate": {
        "required": [],
        "optional": [
            "delimiter",
            "includeHeader",
            "listVariable",
            "resultVariable"
        ],
        "defaults": {
            "delimiter": ",",
            "resultVariable": "csv_text"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_dingtalk": {
        "required": [],
        "optional": [
            "accessToken",
            "atAll",
            "secret"
        ],
        "defaults": {},
        "desc": {
            "secret": "签名密钥（可选）"
        },
        "example": {},
        "combo": ""
    },
    "notify_wecom": {
        "required": [],
        "optional": [
            "agentId",
            "corpId",
            "corpSecret",
            "msgType"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_feishu": {
        "required": [],
        "optional": [
            "msgType",
            "secret",
            "webhookToken"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_telegram": {
        "required": [
            "botToken",
            "chatId"
        ],
        "optional": [
            "parseMode"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "botToken": "...",
            "chatId": "..."
        },
        "combo": ""
    },
    "notify_bark": {
        "required": [],
        "optional": [
            "deviceKey",
            "sound"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_slack": {
        "required": [],
        "optional": [
            "channel",
            "tokenA",
            "tokenB",
            "tokenC"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_serverchan": {
        "required": [],
        "optional": [
            "sendkey"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "allure_init": {
        "required": [],
        "optional": [
            "projectName",
            "resultVariable",
            "suiteName",
            "testSuite"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "测试流程入口"
    },
    "allure_generate_report": {
        "required": [],
        "optional": [
            "autoOpen",
            "reportDir",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "测试流程末尾"
    },
    "image_crop": {
        "required": [
            "inputPath"
        ],
        "optional": [
            "bottom",
            "left",
            "outputPath",
            "resultVariable",
            "right",
            "top"
        ],
        "defaults": {
            "resultVariable": "cropped_image"
        },
        "desc": {},
        "example": {
            "inputPath": "{img}"
        },
        "combo": ""
    },
    "image_flip": {
        "required": [
            "inputPath"
        ],
        "optional": [
            "flipMode",
            "outputPath",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "flipped_image"
        },
        "desc": {},
        "example": {
            "inputPath": "{img}"
        },
        "combo": ""
    },
    "image_add_text": {
        "required": [
            "inputPath",
            "text"
        ],
        "optional": [
            "color",
            "fontColor",
            "fontPath",
            "fontSize",
            "outputPath",
            "positionX",
            "positionY",
            "resultVariable"
        ],
        "defaults": {
            "fontSize": 24,
            "resultVariable": "text_image"
        },
        "desc": {},
        "example": {
            "inputPath": "{img}",
            "text": "© WebRPA"
        },
        "combo": ""
    },
    "ai_element_selector": {
        "required": [
            "url"
        ],
        "optional": [
            "apiKey",
            "apiUrl",
            "azureEndpoint",
            "elementDescription",
            "llmModel",
            "llmProvider",
            "resultVariable",
            "variableName",
            "verbose",
            "waitTime"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "url": "{url}"
        },
        "combo": ""
    },
    "rgb_to_hsv": {
        "required": [],
        "optional": [
            "b",
            "g",
            "r",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "hsv_color"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "rgb_to_cmyk": {
        "required": [],
        "optional": [
            "b",
            "g",
            "r",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "cmyk_color"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "hex_to_cmyk": {
        "required": [],
        "optional": [
            "hexColor",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "cmyk_color"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "screen_record": {
        "required": [
            "duration"
        ],
        "optional": [
            "filename",
            "fps",
            "outputFolder",
            "quality",
            "resultVariable"
        ],
        "defaults": {
            "fps": 30,
            "resultVariable": "recorded_video"
        },
        "desc": {
            "duration": "录制秒数"
        },
        "example": {
            "duration": 10
        },
        "combo": ""
    },
    "real_mouse_drag": {
        "required": [],
        "optional": [
            "button",
            "duration",
            "endX",
            "endY",
            "startX",
            "startY"
        ],
        "defaults": {
            "duration": 0.5
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "real_mouse_scroll": {
        "required": [],
        "optional": [
            "direction",
            "scrollAmount",
            "scrollCount",
            "scrollInterval",
            "x",
            "y"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "keyboard_action": {
        "required": [],
        "optional": [
            "delay",
            "holdDuration",
            "keySequence",
            "keys",
            "pressMode",
            "selector",
            "targetType"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "click_text": {
        "required": [],
        "optional": [
            "clickButton",
            "clickType",
            "matchMode",
            "occurrence",
            "resultVariable",
            "searchRegion",
            "targetText",
            "timeout",
            "waitTimeout"
        ],
        "defaults": {
            "resultVariable": "text_clicked"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "macro_recorder": {
        "required": [],
        "optional": [
            "baseX",
            "baseY",
            "loopCount",
            "mode",
            "playKeyboard",
            "playMouseClick",
            "playMouseMove",
            "playSpeed",
            "recordedData",
            "repeatCount",
            "speed",
            "useRelativePosition"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "工作流中插入宏回放：先 record 模式录制，再用 play 模式回放"
    },
    "oracle_connect": {
        "required": [
            "host",
            "username",
            "password"
        ],
        "optional": [
            "connectionName",
            "connectionVariable",
            "port",
            "serviceName"
        ],
        "defaults": {
            "port": 1521
        },
        "desc": {},
        "example": {
            "host": "192.168.1.100",
            "username": "scott",
            "password": "{p}"
        },
        "combo": ""
    },
    "oracle_query": {
        "required": [
            "sql"
        ],
        "optional": [
            "connectionName",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "sql": "SELECT * FROM dual"
        },
        "combo": ""
    },
    "oracle_execute": {
        "required": [
            "sql"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "sql": "INSERT INTO ..."
        },
        "combo": ""
    },
    "oracle_disconnect": {
        "required": [],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "postgresql_query": {
        "required": [
            "sql"
        ],
        "optional": [
            "connectionName",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "sql": "SELECT NOW()"
        },
        "combo": ""
    },
    "postgresql_disconnect": {
        "required": [],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "mongodb_connect": {
        "required": [
            "database"
        ],
        "optional": [
            "connectionName",
            "connectionVariable",
            "host",
            "password",
            "port",
            "username"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "database": "test"
        },
        "combo": ""
    },
    "mongodb_find": {
        "required": [
            "collection"
        ],
        "optional": [
            "connectionName",
            "filter",
            "limit",
            "query",
            "resultVariable",
            "variableName"
        ],
        "defaults": {
            "limit": 100
        },
        "desc": {},
        "example": {
            "collection": "users"
        },
        "combo": ""
    },
    "mongodb_disconnect": {
        "required": [],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "sqlserver_connect": {
        "required": [
            "username",
            "password",
            "database"
        ],
        "optional": [
            "connectionName",
            "connectionVariable",
            "driver",
            "host",
            "port"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "username": "sa",
            "password": "{p}",
            "database": "test"
        },
        "combo": ""
    },
    "sqlserver_query": {
        "required": [
            "sql"
        ],
        "optional": [
            "connectionName",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "sql": "SELECT GETDATE()"
        },
        "combo": ""
    },
    "sqlserver_disconnect": {
        "required": [],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "sqlite_connect": {
        "required": [],
        "optional": [
            "connectionName",
            "connectionVariable",
            "databasePath"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "sqlite_query": {
        "required": [
            "sql"
        ],
        "optional": [
            "connectionName",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "sql": "SELECT * FROM users"
        },
        "combo": ""
    },
    "sqlite_disconnect": {
        "required": [],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "redis_get": {
        "required": [
            "key"
        ],
        "optional": [
            "connectionName",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "key": "session:1"
        },
        "combo": ""
    },
    "redis_set": {
        "required": [
            "key",
            "value"
        ],
        "optional": [
            "connectionName",
            "expire",
            "expiry"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "key": "k",
            "value": "{v}"
        },
        "combo": ""
    },
    "redis_disconnect": {
        "required": [],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "string_trim": {
        "required": [],
        "optional": [
            "inputText",
            "mode",
            "resultVariable",
            "trimMode",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "string_case": {
        "required": [],
        "optional": [
            "caseMode",
            "inputText",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "string_substring": {
        "required": [],
        "optional": [
            "end",
            "endIndex",
            "inputText",
            "length",
            "resultVariable",
            "startIndex",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "list_chunk": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "chunkSize",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "chunks"
        },
        "desc": {},
        "example": {
            "listVariable": "items"
        },
        "combo": "分批处理大列表用"
    },
    "list_intersection": {
        "required": [],
        "optional": [
            "list1Variable",
            "list2Variable",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "intersection"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "list_difference": {
        "required": [],
        "optional": [
            "list1Variable",
            "list2Variable",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "difference"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "note": {
        "required": [],
        "optional": [
            "color",
            "fontBold",
            "fontSize"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "list_sample": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "resultVariable",
            "sampleCount"
        ],
        "defaults": {
            "resultVariable": "sample_list"
        },
        "desc": {},
        "example": {
            "listVariable": "items"
        },
        "combo": ""
    },
    "list_find": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "resultVariable",
            "searchValue"
        ],
        "defaults": {
            "resultVariable": "find_index"
        },
        "desc": {},
        "example": {
            "listVariable": "items"
        },
        "combo": ""
    },
    "list_union": {
        "required": [],
        "optional": [
            "list1Variable",
            "list2Variable",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "union_list"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "list_cartesian_product": {
        "required": [],
        "optional": [
            "listVariables",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "cartesian"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_log": {
        "required": [],
        "optional": [
            "base",
            "logType",
            "numberValue",
            "resultVariable"
        ],
        "defaults": {
            "base": "e",
            "resultVariable": "log_result"
        },
        "desc": {
            "base": "底数 e/2/10/任意数字"
        },
        "example": {
            "base": "10"
        },
        "combo": ""
    },
    "math_trig": {
        "required": [],
        "optional": [
            "angleUnit",
            "numberValue",
            "resultVariable",
            "trigType"
        ],
        "defaults": {
            "resultVariable": "trig_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_exp": {
        "required": [],
        "optional": [
            "numberValue",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "exp_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_gcd": {
        "required": [],
        "optional": [
            "numbers",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "gcd_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_lcm": {
        "required": [],
        "optional": [
            "numbers",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "lcm_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_factorial": {
        "required": [],
        "optional": [
            "numberValue",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "factorial_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_clamp": {
        "required": [],
        "optional": [
            "maxValue",
            "minValue",
            "numberValue",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "clamped_value"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "math_base_convert": {
        "required": [
            "fromBase",
            "toBase"
        ],
        "optional": [
            "numberValue",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "base_result"
        },
        "desc": {
            "fromBase": "源进制 2/8/10/16",
            "toBase": "目标进制"
        },
        "example": {
            "fromBase": "16",
            "toBase": "10"
        },
        "combo": ""
    },
    "dict_map_values": {
        "required": [
            "dictVariable"
        ],
        "optional": [
            "operand",
            "operation",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "mapped_dict"
        },
        "desc": {},
        "example": {
            "dictVariable": "scores"
        },
        "combo": ""
    },
    "table_set_cell": {
        "required": [],
        "optional": [
            "cellValue",
            "columnName",
            "rowIndex"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "table_get_cell": {
        "required": [],
        "optional": [
            "columnName",
            "resultVariable",
            "rowIndex",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "table_delete_row": {
        "required": [],
        "optional": [
            "rowIndex"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_discord": {
        "required": [],
        "optional": [
            "avatar",
            "username",
            "webhookId",
            "webhookToken"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_msteams": {
        "required": [],
        "optional": [
            "title",
            "webhookUrl"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_pushover": {
        "required": [
            "userKey"
        ],
        "optional": [
            "apiToken",
            "priority",
            "title"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "userKey": "u..."
        },
        "combo": ""
    },
    "notify_pushbullet": {
        "required": [
            "accessToken"
        ],
        "optional": [
            "targetEmail"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "accessToken": "..."
        },
        "combo": ""
    },
    "notify_gotify": {
        "required": [],
        "optional": [
            "hostname",
            "priority",
            "title",
            "token"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_pushplus": {
        "required": [
            "token"
        ],
        "optional": [
            "channel"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "token": "..."
        },
        "combo": ""
    },
    "notify_webhook": {
        "required": [],
        "optional": [
            "headers",
            "method",
            "webhookUrl"
        ],
        "defaults": {
            "method": "POST"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_ntfy": {
        "required": [
            "topic"
        ],
        "optional": [
            "hostname",
            "priority",
            "serverUrl",
            "title"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "topic": "alerts"
        },
        "combo": ""
    },
    "notify_matrix": {
        "required": [],
        "optional": [
            "hostname",
            "password",
            "room",
            "user"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "notify_rocketchat": {
        "required": [],
        "optional": [
            "channel",
            "hostname",
            "password",
            "room",
            "user"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_app_connect": {
        "required": [],
        "optional": [
            "backend",
            "connectType",
            "connectValue",
            "saveToVariable",
            "timeout"
        ],
        "defaults": {
            "timeout": 30
        },
        "desc": {},
        "example": {},
        "combo": "替代 desktop_app_start：连接到已经打开的应用"
    },
    "desktop_window_activate": {
        "required": [],
        "optional": [
            "appVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_find_control": {
        "required": [],
        "optional": [
            "appVariable",
            "automationId",
            "className",
            "controlPath",
            "controlType",
            "findType",
            "name",
            "resultVariable",
            "saveToVariable",
            "searchDepth",
            "timeout",
            "windowHandle"
        ],
        "defaults": {
            "timeout": 10
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_control_info": {
        "required": [],
        "optional": [
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_wait_control": {
        "required": [],
        "optional": [
            "controlInfo",
            "state",
            "timeout",
            "waitType"
        ],
        "defaults": {
            "timeout": 30
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_set_value": {
        "required": [
            "value"
        ],
        "optional": [
            "controlInfo",
            "controlVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "value": "10"
        },
        "combo": ""
    },
    "desktop_select_combo": {
        "required": [],
        "optional": [
            "controlInfo",
            "controlVariable",
            "selectBy",
            "selectValue"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_checkbox": {
        "required": [
            "checked"
        ],
        "optional": [
            "controlInfo",
            "controlVariable"
        ],
        "defaults": {
            "checked": True
        },
        "desc": {},
        "example": {
            "checked": True
        },
        "combo": ""
    },
    "desktop_radio": {
        "required": [],
        "optional": [
            "controlInfo",
            "controlVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_drag_control": {
        "required": [],
        "optional": [
            "controlInfo",
            "controlVariable",
            "dragMode",
            "targetX",
            "targetY"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_get_property": {
        "required": [],
        "optional": [
            "controlInfo",
            "controlVariable",
            "propertyName",
            "resultVariable",
            "saveToVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_dialog_handle": {
        "required": [],
        "optional": [
            "buttonName",
            "dialogTitle",
            "text",
            "timeout",
            "waitAppear"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_list_operate": {
        "required": [
            "operation"
        ],
        "optional": [
            "controlInfo",
            "controlVariable",
            "item",
            "itemIndex",
            "itemName",
            "saveToVariable"
        ],
        "defaults": {
            "operation": "select"
        },
        "desc": {
            "operation": "select/get_items"
        },
        "example": {
            "operation": "select"
        },
        "combo": ""
    },
    "rotate_video": {
        "required": [],
        "optional": [
            "inputPath",
            "outputPath",
            "resultVariable",
            "rotateType"
        ],
        "defaults": {
            "resultVariable": "rotated_video"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "video_speed": {
        "required": [
            "speed"
        ],
        "optional": [
            "adjustAudio",
            "inputPath",
            "outputPath",
            "resultVariable"
        ],
        "defaults": {
            "speed": 1.5,
            "resultVariable": "speed_video"
        },
        "desc": {
            "speed": "倍速 0.5/2.0 等"
        },
        "example": {
            "speed": 2.0
        },
        "combo": ""
    },
    "add_subtitle": {
        "required": [],
        "optional": [
            "inputPath",
            "outputPath",
            "resultVariable",
            "subtitleFile"
        ],
        "defaults": {
            "resultVariable": "subtitled_video"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "adjust_volume": {
        "required": [
            "volume"
        ],
        "optional": [
            "inputPath",
            "outputPath",
            "resultVariable"
        ],
        "defaults": {
            "volume": 1.0,
            "resultVariable": "adjusted_audio"
        },
        "desc": {
            "volume": "1.0=原音量"
        },
        "example": {
            "volume": 1.5
        },
        "combo": ""
    },
    "resize_video": {
        "required": [
            "width",
            "height"
        ],
        "optional": [
            "inputPath",
            "keepAspect",
            "outputPath",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "resized_video"
        },
        "desc": {},
        "example": {
            "width": 1280,
            "height": 720
        },
        "combo": ""
    },
    "video_to_audio": {
        "required": [],
        "optional": [
            "bitrate",
            "inputPath",
            "outputFormat",
            "outputPath",
            "resultVariable",
            "sampleRate"
        ],
        "defaults": {
            "outputFormat": "mp3",
            "resultVariable": "audio_path"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "video_to_gif": {
        "required": [],
        "optional": [
            "duration",
            "fps",
            "inputPath",
            "outputPath",
            "resultVariable",
            "startTime",
            "width"
        ],
        "defaults": {
            "fps": 15,
            "resultVariable": "gif_path"
        },
        "desc": {},
        "example": {
            "startTime": "00:00:00",
            "duration": "5"
        },
        "combo": ""
    },
    "batch_format_convert": {
        "required": [
            "outputFormat"
        ],
        "optional": [
            "filePattern",
            "fileType",
            "inputFolder",
            "outputDir",
            "outputFolder",
            "recursive",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "outputFormat": "mp4"
        },
        "combo": ""
    },
    "add_watermark": {
        "required": [
            "watermarkType"
        ],
        "optional": [
            "fontColor",
            "fontSize",
            "inputPath",
            "mediaType",
            "opacity",
            "outputPath",
            "position",
            "resultVariable",
            "watermarkImage",
            "watermarkText"
        ],
        "defaults": {
            "watermarkType": "text",
            "position": "bottom-right",
            "resultVariable": "watermarked_file"
        },
        "desc": {
            "watermarkType": "text/image",
            "position": "top-left/top-right/bottom-left/bottom-right/center"
        },
        "example": {
            "watermarkType": "text",
            "watermarkText": "© WebRPA"
        },
        "combo": ""
    },
    "face_recognition": {
        "required": [],
        "optional": [
            "resultVariable",
            "sourceImage",
            "targetImage",
            "tolerance"
        ],
        "defaults": {
            "resultVariable": "face_match_result"
        },
        "desc": {},
        "example": {},
        "combo": "有 true/false 两个出口"
    },
    "slider_captcha": {
        "required": [
            "sliderSelector"
        ],
        "optional": [
            "backgroundSelector",
            "gapSelector",
            "targetDistance"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "sliderSelector": ".slider"
        },
        "combo": ""
    },
    "db_update": {
        "required": [
            "table",
            "data"
        ],
        "optional": [
            "connectionName",
            "params",
            "resultVariable",
            "variableName",
            "where"
        ],
        "defaults": {},
        "desc": {
            "table": "表名",
            "data": "字段更新 dict",
            "where": "WHERE 条件 SQL"
        },
        "example": {
            "table": "users",
            "data": {
                "name": "Tom"
            },
            "where": "id = %s"
        },
        "combo": ""
    },
    "db_delete": {
        "required": [
            "table"
        ],
        "optional": [
            "connectionName",
            "params",
            "resultVariable",
            "variableName",
            "where"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "table": "logs",
            "where": "id < %s"
        },
        "combo": ""
    },
    "oracle_insert": {
        "required": [
            "data"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "resultVariable",
            "tableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "data": {
                "NAME": "Tom"
            }
        },
        "combo": ""
    },
    "oracle_update": {
        "required": [
            "data"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable",
            "tableName",
            "where"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "data": {
                "NAME": "Tom"
            },
            "where": "ID = :1"
        },
        "combo": ""
    },
    "oracle_delete": {
        "required": [],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable",
            "tableName",
            "where"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "postgresql_execute": {
        "required": [
            "sql"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "sql": "UPDATE users SET active = %s"
        },
        "combo": ""
    },
    "postgresql_insert": {
        "required": [
            "data"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "resultVariable",
            "tableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "data": {
                "name": "Tom"
            }
        },
        "combo": ""
    },
    "postgresql_update": {
        "required": [
            "data"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable",
            "tableName",
            "where"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "data": {
                "active": False
            },
            "where": "id = %s"
        },
        "combo": ""
    },
    "postgresql_delete": {
        "required": [],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable",
            "tableName",
            "where"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "mongodb_insert": {
        "required": [
            "collection",
            "document"
        ],
        "optional": [
            "connectionName",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {
            "document": "要插入的字典或字典数组"
        },
        "example": {
            "collection": "users",
            "document": {
                "name": "Tom"
            }
        },
        "combo": ""
    },
    "mongodb_update": {
        "required": [
            "collection",
            "update"
        ],
        "optional": [
            "connectionName",
            "multi",
            "query",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {
            "update": "更新文档（含 $set）"
        },
        "example": {
            "collection": "users",
            "update": {
                "$set": {
                    "age": 20
                }
            }
        },
        "combo": ""
    },
    "mongodb_delete": {
        "required": [
            "collection"
        ],
        "optional": [
            "connectionName",
            "multi",
            "query",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "collection": "logs"
        },
        "combo": ""
    },
    "sqlserver_execute": {
        "required": [
            "sql"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "sql": "UPDATE users SET status = ?"
        },
        "combo": ""
    },
    "sqlserver_insert": {
        "required": [
            "data"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "resultVariable",
            "tableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "data": {
                "name": "Tom"
            }
        },
        "combo": ""
    },
    "sqlserver_update": {
        "required": [
            "data"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable",
            "tableName",
            "where"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "data": {
                "active": False
            },
            "where": "id = ?"
        },
        "combo": ""
    },
    "sqlserver_delete": {
        "required": [],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable",
            "tableName",
            "where"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "sqlite_execute": {
        "required": [
            "sql"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "sql": "UPDATE users SET active = ?"
        },
        "combo": ""
    },
    "sqlite_insert": {
        "required": [
            "data"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "resultVariable",
            "tableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "data": {
                "name": "Tom"
            }
        },
        "combo": ""
    },
    "sqlite_update": {
        "required": [
            "data"
        ],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable",
            "tableName",
            "where"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "data": {
                "active": False
            },
            "where": "id = ?"
        },
        "combo": ""
    },
    "sqlite_delete": {
        "required": [],
        "optional": [
            "autoCommit",
            "connectionName",
            "params",
            "resultVariable",
            "tableName",
            "where"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "redis_del": {
        "required": [
            "key"
        ],
        "optional": [
            "connectionName",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "key": "session:1"
        },
        "combo": ""
    },
    "redis_hget": {
        "required": [
            "key",
            "field"
        ],
        "optional": [
            "connectionName",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "key": "user:1",
            "field": "name"
        },
        "combo": ""
    },
    "redis_hset": {
        "required": [
            "key",
            "field",
            "value"
        ],
        "optional": [
            "connectionName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "key": "user:1",
            "field": "name",
            "value": "Tom"
        },
        "combo": ""
    },
    "get_sibling_elements": {
        "required": [],
        "optional": [
            "direction",
            "elementSelector",
            "includeSelf",
            "resultVariable",
            "siblingType",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "hover_text": {
        "required": [],
        "optional": [
            "hoverDuration",
            "matchMode",
            "occurrence",
            "resultVariable",
            "searchRegion",
            "targetText",
            "timeout",
            "waitTimeout"
        ],
        "defaults": {
            "resultVariable": "text_hovered"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "pdf_encrypt": {
        "required": [
            "pdfPath",
            "outputPath"
        ],
        "optional": [
            "ownerPassword",
            "permissions",
            "resultVariable",
            "userPassword"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "pdfPath": "{pdf}",
            "outputPath": "D:\\\\enc.pdf"
        },
        "combo": ""
    },
    "pdf_rotate": {
        "required": [
            "pdfPath"
        ],
        "optional": [
            "outputPath",
            "pageRange",
            "resultVariable",
            "rotation"
        ],
        "defaults": {},
        "desc": {
            "pageRange": "页范围如 1-3"
        },
        "example": {
            "pdfPath": "{pdf}"
        },
        "combo": ""
    },
    "pdf_delete_pages": {
        "required": [
            "pdfPath",
            "outputPath"
        ],
        "optional": [
            "pageRange",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "pdfPath": "{pdf}",
            "outputPath": "D:\\\\out.pdf"
        },
        "combo": ""
    },
    "pdf_insert_pages": {
        "required": [
            "pdfPath",
            "outputPath"
        ],
        "optional": [
            "insertPdf",
            "insertPosition",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "pdfPath": "{a}",
            "outputPath": "D:\\\\merged.pdf"
        },
        "combo": ""
    },
    "pdf_reorder_pages": {
        "required": [
            "pdfPath",
            "outputPath"
        ],
        "optional": [
            "pageOrder",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "pdfPath": "{pdf}",
            "outputPath": "D:\\\\reordered.pdf"
        },
        "combo": ""
    },
    "play_music": {
        "required": [],
        "optional": [
            "audioUrl",
            "loop",
            "volume",
            "waitForEnd"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "play_video": {
        "required": [],
        "optional": [
            "fullscreen",
            "videoUrl",
            "volume",
            "waitForEnd"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "view_image": {
        "required": [],
        "optional": [
            "autoClose",
            "displayTime",
            "imageUrl",
            "title"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "ytdlp_download_playlist": {
        "required": [],
        "optional": [
            "audioFormat",
            "audioOnly",
            "container",
            "format",
            "maxItems",
            "outputFilename",
            "outputPath",
            "playlistItems",
            "quality",
            "resultVariable",
            "skipExisting",
            "timeout",
            "url"
        ],
        "defaults": {
            "resultVariable": "downloaded_playlist"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "image_filter": {
        "required": [
            "inputPath"
        ],
        "optional": [
            "filterType",
            "outputPath",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "filtered_image"
        },
        "desc": {},
        "example": {
            "inputPath": "{img}"
        },
        "combo": ""
    },
    "image_merge": {
        "required": [
            "outputPath"
        ],
        "optional": [
            "direction",
            "imagePaths",
            "resultVariable",
            "spacing"
        ],
        "defaults": {
            "direction": "horizontal",
            "resultVariable": "merged_image"
        },
        "desc": {
            "direction": "horizontal/vertical/grid"
        },
        "example": {
            "outputPath": "D:\\\\merged.png"
        },
        "combo": ""
    },
    "desktop_get_control_info": {
        "required": [],
        "optional": [
            "controlInfo",
            "controlVariable",
            "resultVariable",
            "saveToVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_scroll_control": {
        "required": [
            "direction"
        ],
        "optional": [
            "amount",
            "controlInfo",
            "controlVariable"
        ],
        "defaults": {
            "direction": "down",
            "amount": 3
        },
        "desc": {
            "direction": "up/down",
            "amount": "滚动次数"
        },
        "example": {
            "direction": "down"
        },
        "combo": ""
    },
    "desktop_window_topmost": {
        "required": [],
        "optional": [
            "appVariable",
            "topmost"
        ],
        "defaults": {
            "topmost": True
        },
        "desc": {
            "topmost": "true=置顶 false=取消"
        },
        "example": {
            "topmost": True
        },
        "combo": ""
    },
    "phone_click_text": {
        "required": [],
        "optional": [
            "clickType",
            "deviceId",
            "matchMode",
            "occurrence",
            "resultVariable",
            "targetText",
            "timeout",
            "waitTimeout"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "phone_set_brightness": {
        "required": [],
        "optional": [
            "brightness",
            "deviceId"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "phone_set_volume": {
        "required": [],
        "optional": [
            "deviceId",
            "streamType",
            "volume"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "folder_hash_compare": {
        "required": [],
        "optional": [
            "algorithm",
            "folder1Path",
            "folder2Path",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "folder_hash_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "folder_diff_compare": {
        "required": [],
        "optional": [
            "folder1Path",
            "folder2Path",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "folder_diff_result"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "export_log": {
        "required": [],
        "optional": [
            "format",
            "includeDuration",
            "includeLevel",
            "includeTimestamp",
            "logFormat",
            "outputPath",
            "resultVariable"
        ],
        "defaults": {
            "includeTimestamp": True,
            "includeLevel": True,
            "includeDuration": False
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "list_export": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "appendMode",
            "encoding",
            "format",
            "outputPath",
            "separator"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "listVariable": "items"
        },
        "combo": ""
    },
    "open_page": {
        "required": [
            "url"
        ],
        "optional": [
            "executablePath",
            "fullscreen",
            "headless",
            "launchArgs",
            "openMode",
            "timeout",
            "type",
            "waitUntil"
        ],
        "defaults": {},
        "desc": {
            "url": "要打开的网页 URL"
        },
        "example": {
            "url": "https://www.baidu.com"
        },
        "combo": "通常作为工作流第一步；后接 wait_page_load / click_element / input_text"
    },
    "use_opened_page": {
        "required": [],
        "optional": [
            "action",
            "url",
            "urlMatch",
            "waitUntil"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "替代 open_page，连接到用户已经打开的浏览器页面"
    },
    "click_element": {
        "required": [
            "selector"
        ],
        "optional": [
            "clickType",
            "doubleClick",
            "timeout",
            "waitForSelector"
        ],
        "defaults": {},
        "desc": {
            "selector": "CSS 选择器或 XPath，例如 #search-btn 或 .submit",
            "timeout": "等待元素出现的超时（秒）"
        },
        "example": {
            "selector": "#kw"
        },
        "combo": "前序通常是 wait_element 或 input_text；后接 wait_page_load"
    },
    "input_text": {
        "required": [
            "selector",
            "text"
        ],
        "optional": [
            "clear",
            "clearBefore",
            "delay",
            "timeout"
        ],
        "defaults": {},
        "desc": {
            "selector": "输入框的 CSS / XPath 选择器",
            "text": "要输入的文本，可用 {变量名} 引用变量"
        },
        "example": {
            "selector": "#kw",
            "text": "WebRPA"
        },
        "combo": "通常前面 wait_element，后面 click_element 提交"
    },
    "select_dropdown": {
        "required": [
            "selector"
        ],
        "optional": [
            "index",
            "label",
            "selectBy",
            "timeout",
            "value"
        ],
        "defaults": {},
        "desc": {
            "selector": "<select> 选择器",
            "value": "按 value 选"
        },
        "example": {
            "selector": "#country"
        },
        "combo": ""
    },
    "wait_element": {
        "required": [
            "selector"
        ],
        "optional": [
            "state",
            "timeout",
            "waitCondition",
            "waitTimeout"
        ],
        "defaults": {},
        "desc": {
            "selector": "等待出现的元素选择器"
        },
        "example": {
            "selector": ".result-list"
        },
        "combo": "比 wait 更可靠，建议替代 wait"
    },
    "wait_page_load": {
        "required": [],
        "optional": [
            "state",
            "timeout",
            "waitUntil"
        ],
        "defaults": {
            "timeout": 30
        },
        "desc": {
            "timeout": "最大等待秒"
        },
        "example": {
            "timeout": 30
        },
        "combo": "open_page / click_element 之后保险等加载完"
    },
    "screenshot": {
        "required": [],
        "optional": [
            "fileName",
            "fileNamePattern",
            "fullPage",
            "savePath",
            "screenshotType",
            "selector",
            "variableName"
        ],
        "defaults": {
            "variableName": "screenshot_path"
        },
        "desc": {
            "selector": "可选：只截某个元素",
            "variableName": "保存截图路径到变量"
        },
        "example": {
            "variableName": "page_shot"
        },
        "combo": ""
    },
    "get_element_info": {
        "required": [
            "selector"
        ],
        "optional": [
            "attribute",
            "columnName",
            "multiple",
            "timeout",
            "variableName"
        ],
        "defaults": {
            "variableName": "element_value",
            "attribute": "text"
        },
        "desc": {
            "selector": "目标元素选择器",
            "attribute": "text(默认)/value/href/src/innerHTML/data-xxx 等任意属性",
            "variableName": "结果变量"
        },
        "example": {
            "selector": ".title",
            "attribute": "text",
            "variableName": "page_title"
        },
        "combo": "数据采集核心，配合 foreach 遍历列表"
    },
    "stop_workflow": {
        "required": [],
        "optional": [
            "reason",
            "stopReason"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "subflow": {
        "required": [
            "subflowName"
        ],
        "optional": [
            "parameterValues",
            "subflowGroupId"
        ],
        "defaults": {},
        "desc": {
            "subflowName": "子流程名"
        },
        "example": {
            "subflowName": "登录流程"
        },
        "combo": "复用工作流的关键，把重复逻辑做成子流程"
    },
    "random_number": {
        "required": [],
        "optional": [
            "decimalPlaces",
            "isFloat",
            "max",
            "maxValue",
            "min",
            "minValue",
            "randomType",
            "variableName"
        ],
        "defaults": {
            "variableName": "random_num"
        },
        "desc": {
            "variableName": "结果变量"
        },
        "example": {},
        "combo": ""
    },
    "get_time": {
        "required": [],
        "optional": [
            "customFormat",
            "format",
            "timeFormat",
            "variableName"
        ],
        "defaults": {
            "variableName": "current_time"
        },
        "desc": {
            "variableName": "结果变量"
        },
        "example": {},
        "combo": ""
    },
    "string_join": {
        "required": [
            "listVariable",
            "separator"
        ],
        "optional": [
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "listVariable": "列表变量名",
            "separator": "连接符"
        },
        "example": {
            "listVariable": "items",
            "separator": "、"
        },
        "combo": ""
    },
    "list_length": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "listVariable": "列表变量"
        },
        "example": {
            "listVariable": "rows"
        },
        "combo": ""
    },
    "dict_keys": {
        "required": [
            "dictVariable"
        ],
        "optional": [
            "keyType",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "dictVariable": "user"
        },
        "combo": "后接 foreach 遍历键"
    },
    "run_command": {
        "required": [
            "command"
        ],
        "optional": [
            "resultVariable",
            "shell",
            "timeout",
            "variableName"
        ],
        "defaults": {
            "timeout": 60,
            "shell": True
        },
        "desc": {
            "command": "命令字符串",
            "shell": "是否走 shell"
        },
        "example": {
            "command": "dir D:\\\\"
        },
        "combo": ""
    },
    "click_image": {
        "required": [
            "imagePath"
        ],
        "optional": [
            "button",
            "clickPosition",
            "clickType",
            "confidence",
            "holdDuration",
            "offsetX",
            "offsetY",
            "resultVariable",
            "searchRegion",
            "timeout",
            "waitTimeout"
        ],
        "defaults": {
            "confidence": 0.8
        },
        "desc": {
            "confidence": "0~1 匹配阈值"
        },
        "example": {
            "imagePath": "D:\\\\btn.png"
        },
        "combo": ""
    },
    "list_files": {
        "required": [
            "folderPath"
        ],
        "optional": [
            "extension",
            "filterPattern",
            "includeExtension",
            "listType",
            "recursive",
            "resultVariable"
        ],
        "defaults": {
            "recursive": False,
            "resultVariable": "files_list"
        },
        "desc": {
            "folderPath": "目标文件夹路径",
            "recursive": "是否递归子文件夹",
            "resultVariable": "结果变量（数组）"
        },
        "example": {
            "folderPath": "D:\\\\data",
            "resultVariable": "files"
        },
        "combo": "后接 foreach 遍历每个文件"
    },
    "format_convert": {
        "required": [
            "inputPath",
            "outputFormat"
        ],
        "optional": [
            "mediaType",
            "outputPath",
            "resultVariable"
        ],
        "defaults": {
            "outputFormat": "mp4",
            "resultVariable": "converted_path"
        },
        "desc": {
            "outputFormat": "目标格式后缀"
        },
        "example": {
            "inputPath": "{file}",
            "outputFormat": "mp4"
        },
        "combo": ""
    },
    "uuid_generator": {
        "required": [],
        "optional": [
            "name",
            "namespace",
            "removeHyphens",
            "resultVariable",
            "uppercase",
            "uuidVersion",
            "version"
        ],
        "defaults": {
            "resultVariable": "uuid"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "random_password_generator": {
        "required": [],
        "optional": [
            "excludeAmbiguous",
            "includeDigits",
            "includeLowercase",
            "includeNumbers",
            "includeSymbols",
            "includeUppercase",
            "length",
            "resultVariable"
        ],
        "defaults": {
            "length": 16,
            "includeUppercase": True,
            "includeSymbols": True,
            "resultVariable": "generated_password"
        },
        "desc": {},
        "example": {
            "length": 20
        },
        "combo": ""
    },
    "webhook_trigger": {
        "required": [],
        "optional": [
            "autoSetParams",
            "method",
            "paramPrefix",
            "path",
            "responseBody",
            "responseStatus",
            "saveToVariable",
            "timeout",
            "validateHeaders",
            "validateParams",
            "webhookId"
        ],
        "defaults": {
            "method": "POST",
            "saveToVariable": "webhook_data"
        },
        "desc": {
            "method": "GET/POST",
            "saveToVariable": "保存请求数据的变量"
        },
        "example": {
            "method": "POST"
        },
        "combo": "工作流第一个节点；后接 json_parse 解析 webhook_data"
    },
    "file_watcher_trigger": {
        "required": [
            "watchPath"
        ],
        "optional": [
            "events",
            "filePattern",
            "fileTypes",
            "saveToVariable",
            "timeout",
            "watchType"
        ],
        "defaults": {
            "saveToVariable": "file_event"
        },
        "desc": {
            "watchPath": "监控的文件夹"
        },
        "example": {
            "watchPath": "D:\\\\inbox"
        },
        "combo": ""
    },
    "email_trigger": {
        "required": [],
        "optional": [
            "checkInterval",
            "emailAccount",
            "emailPassword",
            "emailPort",
            "emailServer",
            "filterFrom",
            "filterSubject",
            "fromFilter",
            "pollInterval",
            "saveToVariable",
            "subjectFilter",
            "timeout"
        ],
        "defaults": {
            "saveToVariable": "email_data"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "api_trigger": {
        "required": [],
        "optional": [
            "apiUrl",
            "body",
            "checkInterval",
            "conditionOperator",
            "conditionPath",
            "conditionValue",
            "headers",
            "method",
            "path",
            "saveToVariable",
            "timeout"
        ],
        "defaults": {
            "saveToVariable": "api_response"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "image_trigger": {
        "required": [
            "imagePath"
        ],
        "optional": [
            "checkInterval",
            "confidence",
            "interval",
            "saveToVariable",
            "searchRegion",
            "timeout"
        ],
        "defaults": {
            "confidence": 0.8,
            "saveToVariable": "image_position"
        },
        "desc": {
            "imagePath": "目标图片"
        },
        "example": {
            "imagePath": "D:\\\\target.png"
        },
        "combo": ""
    },
    "element_change_trigger": {
        "required": [
            "selector"
        ],
        "optional": [
            "interval",
            "observeType",
            "saveChangeInfo",
            "saveNewElementSelector",
            "timeout"
        ],
        "defaults": {
            "saveNewElementSelector": "new_element_selector",
            "saveChangeInfo": "element_change_info"
        },
        "desc": {
            "selector": "监控的父元素 selector"
        },
        "example": {
            "selector": ".comments"
        },
        "combo": "用于监控网页评论新增、商品上架等"
    },
    "scheduled_task": {
        "required": [
            "scheduleType"
        ],
        "optional": [
            "cronExpression",
            "delayHours",
            "delayMinutes",
            "delaySeconds",
            "intervalSeconds",
            "specificTime",
            "targetDate",
            "targetTime"
        ],
        "defaults": {
            "scheduleType": "interval"
        },
        "desc": {
            "scheduleType": "interval/cron/specific"
        },
        "example": {
            "scheduleType": "cron"
        },
        "combo": "工作流入口节点"
    },
    "desktop_app_start": {
        "required": [
            "appPath"
        ],
        "optional": [
            "appArgs",
            "arguments",
            "connectionVariable",
            "waitReady",
            "waitTimeout"
        ],
        "defaults": {
            "waitReady": True
        },
        "desc": {
            "appPath": "EXE 路径"
        },
        "example": {
            "appPath": "C:\\\\app.exe"
        },
        "combo": ""
    },
    "desktop_app_close": {
        "required": [],
        "optional": [
            "appVariable",
            "closeMode",
            "force",
            "processName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "text_to_speech": {
        "required": [
            "text"
        ],
        "optional": [
            "lang",
            "pitch",
            "rate",
            "voice",
            "volume"
        ],
        "defaults": {
            "rate": 1.0,
            "volume": 1.0
        },
        "desc": {
            "rate": "语速 0.1-10",
            "volume": "音量 0-1"
        },
        "example": {
            "text": "工作流已完成"
        },
        "combo": ""
    },
    "db_connect": {
        "required": [
            "host",
            "user",
            "password",
            "database"
        ],
        "optional": [
            "charset",
            "connectionName",
            "connectionVariable",
            "port"
        ],
        "defaults": {
            "port": 3306,
            "charset": "utf8mb4"
        },
        "desc": {
            "host": "MySQL 主机",
            "port": "默认 3306"
        },
        "example": {
            "host": "localhost",
            "user": "root",
            "password": "{db_pwd}",
            "database": "test"
        },
        "combo": "成功后用 db_query / db_execute；最后用 db_close 关闭"
    },
    "phone_tap": {
        "required": [
            "x",
            "y"
        ],
        "optional": [
            "deviceId"
        ],
        "defaults": {},
        "desc": {
            "x": "横坐标",
            "y": "纵坐标"
        },
        "example": {
            "x": 540,
            "y": 960
        },
        "combo": "用拾取按钮拿坐标更准"
    },
    "phone_swipe": {
        "required": [
            "x1",
            "y1",
            "x2",
            "y2"
        ],
        "optional": [
            "deviceId",
            "duration",
            "offsetX",
            "offsetY",
            "swipeMode"
        ],
        "defaults": {
            "duration": 300
        },
        "desc": {
            "duration": "滑动毫秒"
        },
        "example": {
            "x1": 540,
            "y1": 1500,
            "x2": 540,
            "y2": 500
        },
        "combo": ""
    },
    "phone_long_press": {
        "required": [
            "x",
            "y"
        ],
        "optional": [
            "deviceId",
            "duration"
        ],
        "defaults": {
            "duration": 1000
        },
        "desc": {
            "duration": "长按毫秒"
        },
        "example": {
            "x": 540,
            "y": 960,
            "duration": 1500
        },
        "combo": ""
    },
    "phone_input_text": {
        "required": [
            "text"
        ],
        "optional": [
            "autoEnter",
            "autoRestoreKeyboard",
            "autoSwitchKeyboard",
            "deviceId"
        ],
        "defaults": {},
        "desc": {
            "text": "输入文本（手机已 ADB 输入法支持中文）"
        },
        "example": {
            "text": "{username}"
        },
        "combo": "通常前面 phone_tap 点中输入框"
    },
    "phone_screenshot": {
        "required": [],
        "optional": [
            "deviceId",
            "resultVariable",
            "savePath",
            "saveToVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "savePath": "D:\\\\phone.png"
        },
        "combo": ""
    },
    "phone_click_image": {
        "required": [
            "imagePath"
        ],
        "optional": [
            "clickPosition",
            "clickType",
            "confidence",
            "deviceId",
            "resultVariable",
            "timeout",
            "waitTimeout"
        ],
        "defaults": {
            "confidence": 0.85
        },
        "desc": {},
        "example": {
            "imagePath": "D:\\\\target.png"
        },
        "combo": ""
    },
    "phone_wait_image": {
        "required": [
            "imagePath"
        ],
        "optional": [
            "checkInterval",
            "confidence",
            "deviceId",
            "resultVariable",
            "timeout",
            "waitTimeout"
        ],
        "defaults": {
            "resultVariable": "phone_image_found"
        },
        "desc": {},
        "example": {
            "imagePath": "D:\\\\splash.png"
        },
        "combo": ""
    },
    "phone_start_app": {
        "required": [
            "packageName"
        ],
        "optional": [
            "activityName",
            "deviceId"
        ],
        "defaults": {},
        "desc": {
            "packageName": "如 com.tencent.mm"
        },
        "example": {
            "packageName": "com.tencent.mm"
        },
        "combo": ""
    },
    "phone_stop_app": {
        "required": [
            "packageName"
        ],
        "optional": [
            "deviceId"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "packageName": "com.tencent.mm"
        },
        "combo": ""
    },
    "phone_install_app": {
        "required": [
            "apkPath"
        ],
        "optional": [
            "deviceId"
        ],
        "defaults": {},
        "desc": {
            "apkPath": "本地 APK 路径"
        },
        "example": {
            "apkPath": "D:\\\\app.apk"
        },
        "combo": ""
    },
    "phone_set_clipboard": {
        "required": [
            "text"
        ],
        "optional": [
            "deviceId"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "text": "{value}"
        },
        "combo": ""
    },
    "phone_get_clipboard": {
        "required": [],
        "optional": [
            "deviceId",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "qq_wait_message": {
        "required": [],
        "optional": [
            "groupId",
            "matchContent",
            "matchMode",
            "matchText",
            "pollInterval",
            "resultVariable",
            "senderId",
            "sourceType",
            "timeout",
            "waitTimeout"
        ],
        "defaults": {
            "sourceType": "any",
            "matchMode": "contains",
            "resultVariable": "qq_received"
        },
        "desc": {
            "sourceType": "any/private/group",
            "matchMode": "contains/equals/regex"
        },
        "example": {
            "matchMode": "contains"
        },
        "combo": "QQ 机器人对话流程：等消息 → 解析 → 回复"
    },
    "ssh_connect": {
        "required": [
            "host",
            "username",
            "password"
        ],
        "optional": [
            "connectionName",
            "connectionVariable",
            "keyFile",
            "port",
            "timeout"
        ],
        "defaults": {
            "port": 22
        },
        "desc": {},
        "example": {
            "host": "192.168.1.100",
            "username": "root",
            "password": "{pwd}"
        },
        "combo": "成功后 ssh_execute_command；最后 ssh_disconnect"
    },
    "feishu_bitable_read": {
        "required": [
            "appToken",
            "tableId"
        ],
        "optional": [
            "appId",
            "appSecret",
            "resultVariable",
            "variableName",
            "viewId"
        ],
        "defaults": {},
        "desc": {
            "appToken": "多维表格 token",
            "tableId": "数据表 ID"
        },
        "example": {
            "appToken": "...",
            "tableId": "..."
        },
        "combo": ""
    },
    "ai_generate_image": {
        "required": [
            "prompt"
        ],
        "optional": [
            "apiBase",
            "apiKey",
            "engineId",
            "model",
            "n",
            "negativePrompt",
            "outputPath",
            "provider",
            "quality",
            "resultVariable",
            "savePath",
            "size",
            "style",
            "variableName"
        ],
        "defaults": {
            "size": "1024x1024"
        },
        "desc": {
            "prompt": "图片描述"
        },
        "example": {
            "prompt": "一只可爱的猫"
        },
        "combo": ""
    },
    "ai_generate_video": {
        "required": [
            "prompt"
        ],
        "optional": [
            "apiBase",
            "apiKey",
            "apiUrl",
            "aspectRatio",
            "duration",
            "fps",
            "model",
            "outputPath",
            "provider",
            "resultVariable",
            "savePath",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "prompt": "海浪冲击沙滩"
        },
        "combo": ""
    },
    "list_sort": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "order",
            "resultVariable",
            "sortOrder"
        ],
        "defaults": {
            "resultVariable": "sorted_list"
        },
        "desc": {},
        "example": {
            "listVariable": "items"
        },
        "combo": ""
    },
    "dict_sort": {
        "required": [
            "dictVariable"
        ],
        "optional": [
            "order",
            "resultVariable",
            "sortBy",
            "sortOrder"
        ],
        "defaults": {
            "sortBy": "key",
            "resultVariable": "sorted_dict"
        },
        "desc": {
            "sortBy": "key/value"
        },
        "example": {
            "dictVariable": "scores",
            "sortBy": "value"
        },
        "combo": ""
    },
    "math_random_advanced": {
        "required": [],
        "optional": [
            "count",
            "decimals",
            "max",
            "maxValue",
            "min",
            "minValue",
            "randomType",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "random_advanced"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "allure_start_test": {
        "required": [
            "testName"
        ],
        "optional": [
            "description",
            "name",
            "resultVariable",
            "severity",
            "tags",
            "testId"
        ],
        "defaults": {
            "severity": "normal"
        },
        "desc": {
            "severity": "blocker/critical/normal/minor/trivial"
        },
        "example": {
            "testName": "登录测试"
        },
        "combo": ""
    },
    "image_resize": {
        "required": [
            "inputPath",
            "width",
            "height"
        ],
        "optional": [
            "keepAspect",
            "keepRatio",
            "outputPath",
            "resample",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "resized_image"
        },
        "desc": {},
        "example": {
            "inputPath": "{img}",
            "width": 800,
            "height": 600
        },
        "combo": ""
    },
    "markdown_to_pdf": {
        "required": [
            "inputPath",
            "outputPath"
        ],
        "optional": [
            "cssFile",
            "pdfEngine",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "inputPath": "{md}",
            "outputPath": "D:\\\\out.pdf"
        },
        "combo": ""
    },
    "network_capture": {
        "required": [],
        "optional": [
            "captureDuration",
            "captureMode",
            "filterType",
            "filterUrl",
            "proxyPort",
            "resultVariable",
            "searchKeyword",
            "targetPorts",
            "targetProcess",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "前面 open_page，后面 click 触发请求；最后看 captured_data"
    },
    "network_monitor_start": {
        "required": [],
        "optional": [
            "filterType",
            "filterUrl",
            "monitorId",
            "urlPattern"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "和 network_monitor_wait/stop 配对"
    },
    "network_monitor_wait": {
        "required": [],
        "optional": [
            "captureMode",
            "method",
            "monitorId",
            "resultVariable",
            "stopAfterCapture",
            "timeout",
            "urlMatch",
            "urlPattern",
            "variableName"
        ],
        "defaults": {
            "timeout": 30
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "webhook_request": {
        "required": [
            "url",
            "method"
        ],
        "optional": [
            "body",
            "bodyType",
            "cookies",
            "cookiesVariable",
            "followRedirects",
            "headers",
            "headersVariable",
            "params",
            "responseVariable",
            "resultVariable",
            "saveCookies",
            "saveHeaders",
            "saveResponse",
            "saveStatus",
            "statusVariable",
            "timeout",
            "verifySSL"
        ],
        "defaults": {
            "method": "POST",
            "timeout": 30
        },
        "desc": {},
        "example": {
            "url": "https://hooks.slack.com/...",
            "method": "POST",
            "body": "{...}"
        },
        "combo": ""
    },
    "ai_smart_scraper": {
        "required": [
            "url",
            "prompt"
        ],
        "optional": [
            "apiKey",
            "apiUrl",
            "azureEndpoint",
            "headless",
            "llmModel",
            "llmProvider",
            "model",
            "resultVariable",
            "variableName",
            "verbose",
            "waitTime"
        ],
        "defaults": {},
        "desc": {
            "prompt": "对网页内容的提问/抓取目标"
        },
        "example": {
            "url": "https://example.com",
            "prompt": "提取所有产品名称和价格"
        },
        "combo": ""
    },
    "firecrawl_scrape": {
        "required": [
            "url"
        ],
        "optional": [
            "excludeTags",
            "formats",
            "includeTags",
            "onlyMainContent",
            "resultVariable",
            "timeout",
            "variableName",
            "waitFor"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "url": "https://example.com"
        },
        "combo": ""
    },
    "firecrawl_map": {
        "required": [
            "url"
        ],
        "optional": [
            "includeSubdomains",
            "limit",
            "resultVariable",
            "search",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "url": "https://example.com"
        },
        "combo": ""
    },
    "share_folder": {
        "required": [
            "folderPath"
        ],
        "optional": [
            "allowWrite",
            "password",
            "port",
            "resultVariable",
            "shareName"
        ],
        "defaults": {
            "resultVariable": "share_url"
        },
        "desc": {},
        "example": {
            "folderPath": "D:\\\\public"
        },
        "combo": ""
    },
    "share_file": {
        "required": [
            "filePath"
        ],
        "optional": [
            "password",
            "port",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "share_url"
        },
        "desc": {},
        "example": {
            "filePath": "D:\\\\report.pdf"
        },
        "combo": ""
    },
    "real_mouse_click": {
        "required": [
            "x",
            "y"
        ],
        "optional": [
            "button",
            "clickType",
            "clicks",
            "holdDuration"
        ],
        "defaults": {
            "button": "left"
        },
        "desc": {
            "button": "left/right/middle"
        },
        "example": {
            "x": 500,
            "y": 300,
            "button": "left"
        },
        "combo": ""
    },
    "real_keyboard": {
        "required": [
            "text"
        ],
        "optional": [
            "delay",
            "holdDuration",
            "hotkey",
            "inputType",
            "interval",
            "key",
            "pressMode"
        ],
        "defaults": {},
        "desc": {
            "text": "要键盘输入的文本"
        },
        "example": {
            "text": "Hello {name}"
        },
        "combo": ""
    },
    "get_mouse_position": {
        "required": [],
        "optional": [
            "variableName",
            "variableNameX",
            "variableNameY"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "返回 {x, y}"
    },
    "image_exists": {
        "required": [
            "imagePath"
        ],
        "optional": [
            "confidence",
            "resultVariable",
            "searchRegion",
            "timeout",
            "useFullScreen",
            "waitTimeout"
        ],
        "defaults": {
            "confidence": 0.8
        },
        "desc": {},
        "example": {
            "imagePath": "D:\\\\btn.png"
        },
        "combo": "前置判断，后接 condition"
    },
    "element_exists": {
        "required": [
            "selector"
        ],
        "optional": [
            "resultVariable",
            "timeout"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "selector": ".success-msg"
        },
        "combo": ""
    },
    "element_visible": {
        "required": [
            "selector"
        ],
        "optional": [
            "resultVariable",
            "timeout"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "selector": ".popup"
        },
        "combo": ""
    },
    "postgresql_connect": {
        "required": [
            "host",
            "username",
            "password",
            "database"
        ],
        "optional": [
            "connectionName",
            "connectionVariable",
            "port"
        ],
        "defaults": {
            "port": 5432
        },
        "desc": {},
        "example": {
            "host": "localhost",
            "username": "postgres",
            "password": "{p}",
            "database": "test"
        },
        "combo": ""
    },
    "redis_connect": {
        "required": [
            "host"
        ],
        "optional": [
            "connectionName",
            "connectionVariable",
            "db",
            "password",
            "port"
        ],
        "defaults": {
            "port": 6379,
            "db": 0
        },
        "desc": {},
        "example": {
            "host": "localhost"
        },
        "combo": ""
    },
    "shutdown_system": {
        "required": [],
        "optional": [
            "action",
            "delay",
            "force",
            "mode"
        ],
        "defaults": {
            "delay": 0
        },
        "desc": {
            "delay": "延迟秒数"
        },
        "example": {
            "delay": 60
        },
        "combo": ""
    },
    "group": {
        "required": [],
        "optional": [
            "color",
            "label"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "ytdlp_download": {
        "required": [
            "url"
        ],
        "optional": [
            "container",
            "embedChapters",
            "embedThumbnail",
            "fileName",
            "format",
            "outputDir",
            "outputFilename",
            "outputPath",
            "quality",
            "resultVariable",
            "timeRange",
            "timeout",
            "writeInfoJson",
            "writeThumbnail"
        ],
        "defaults": {
            "resultVariable": "downloaded_video"
        },
        "desc": {},
        "example": {
            "url": "https://www.youtube.com/watch?v=..."
        },
        "combo": ""
    },
    "ytdlp_download_audio": {
        "required": [
            "url"
        ],
        "optional": [
            "audioFormat",
            "audioQuality",
            "embedMetadata",
            "embedThumbnail",
            "format",
            "outputDir",
            "outputFilename",
            "outputPath",
            "resultVariable",
            "timeRange",
            "timeout"
        ],
        "defaults": {
            "resultVariable": "downloaded_audio"
        },
        "desc": {},
        "example": {
            "url": "https://..."
        },
        "combo": ""
    },
    "ytdlp_download_subtitle": {
        "required": [
            "url"
        ],
        "optional": [
            "autoSubtitle",
            "language",
            "outputDir",
            "outputFilename",
            "outputPath",
            "resultVariable",
            "subtitleFormat",
            "subtitleLang",
            "timeout"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "url": "https://..."
        },
        "combo": ""
    },
    "stat_normalize": {
        "required": [
            "listVariable"
        ],
        "optional": [
            "max",
            "min",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "normalized"
        },
        "desc": {},
        "example": {
            "listVariable": "values"
        },
        "combo": ""
    },
    "feishu_sheet_read": {
        "required": [
            "spreadsheetToken",
            "range"
        ],
        "optional": [
            "appId",
            "appSecret",
            "resultVariable",
            "sheetId",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "range": "如 Sheet1!A1:D10"
        },
        "example": {
            "spreadsheetToken": "...",
            "range": "Sheet1!A1:Z100"
        },
        "combo": ""
    },
    "camera_capture": {
        "required": [],
        "optional": [
            "cameraIndex",
            "filename",
            "outputFolder",
            "savePath",
            "saveToVariable"
        ],
        "defaults": {
            "cameraIndex": 0,
            "saveToVariable": "camera_photo"
        },
        "desc": {},
        "example": {},
        "combo": ""
    },
    "camera_record": {
        "required": [
            "duration"
        ],
        "optional": [
            "cameraIndex",
            "filename",
            "fps",
            "outputFolder",
            "resolution",
            "savePath",
            "saveToVariable"
        ],
        "defaults": {
            "cameraIndex": 0,
            "saveToVariable": "camera_video"
        },
        "desc": {
            "duration": "录制秒数"
        },
        "example": {
            "duration": 10
        },
        "combo": ""
    },
    "firecrawl_crawl": {
        "required": [
            "url"
        ],
        "optional": [
            "allowExternalLinks",
            "excludePaths",
            "formats",
            "includePaths",
            "limit",
            "maxDepth",
            "maxPages",
            "onlyMainContent",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "url": "https://example.com"
        },
        "combo": ""
    },
    "desktop_app_get_info": {
        "required": [],
        "optional": [
            "appVariable",
            "resultVariable",
            "saveToVariable",
            "windowHandle"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_window_list": {
        "required": [],
        "optional": [
            "filterEnabled",
            "filterVisible",
            "resultVariable",
            "saveToVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "desktop_control_tree": {
        "required": [],
        "optional": [
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "image_ocr": {
        "required": [
            "imagePath"
        ],
        "optional": [
            "endX",
            "endY",
            "language",
            "ocrMode",
            "ocrType",
            "resultVariable",
            "startX",
            "startY"
        ],
        "defaults": {
            "resultVariable": "ocr_text"
        },
        "desc": {},
        "example": {
            "imagePath": "{img}"
        },
        "combo": ""
    },
    "page_load_complete": {
        "required": [],
        "optional": [
            "checkState",
            "resultVariable",
            "saveToVariable",
            "timeout"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "比 wait_page_load 严格：会判断 networkidle"
    },
    "save_image": {
        "required": [
            "selector",
            "savePath"
        ],
        "optional": [
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "selector": "<img> 选择器",
            "savePath": "保存绝对路径"
        },
        "example": {
            "selector": "img.product",
            "savePath": "D:\\\\img.jpg"
        },
        "combo": ""
    },
    "wait_image": {
        "required": [
            "imagePath"
        ],
        "optional": [
            "checkInterval",
            "confidence",
            "resultVariable",
            "searchRegion",
            "timeout",
            "variableNameX",
            "variableNameY",
            "waitTimeout"
        ],
        "defaults": {
            "confidence": 0.85
        },
        "desc": {},
        "example": {
            "imagePath": "D:\\\\target.png"
        },
        "combo": ""
    },
    "get_child_elements": {
        "required": [
            "parentSelector"
        ],
        "optional": [
            "childSelector",
            "resultVariable",
            "variableName"
        ],
        "defaults": {},
        "desc": {
            "parentSelector": "父元素 selector",
            "childSelector": "可选：进一步过滤子元素的 selector"
        },
        "example": {
            "parentSelector": "ul.list",
            "childSelector": "li"
        },
        "combo": ""
    },
    "drag_image": {
        "required": [
            "sourceImagePath",
            "targetX",
            "targetY"
        ],
        "optional": [
            "confidence",
            "dragDuration",
            "duration",
            "resultVariable",
            "searchRegion",
            "sourcePosition",
            "targetImagePath",
            "targetPosition",
            "targetType",
            "waitTimeout"
        ],
        "defaults": {
            "confidence": 0.85
        },
        "desc": {
            "sourceImagePath": "起点图片",
            "targetX": "终点 X 像素",
            "targetY": "终点 Y"
        },
        "example": {
            "sourceImagePath": "D:\\\\drag.png",
            "targetX": 800,
            "targetY": 600
        },
        "combo": ""
    },
    "hover_image": {
        "required": [
            "imagePath"
        ],
        "optional": [
            "confidence",
            "hoverDuration",
            "hoverPosition",
            "resultVariable",
            "searchRegion",
            "timeout",
            "waitTimeout"
        ],
        "defaults": {
            "confidence": 0.85,
            "resultVariable": "image_hovered"
        },
        "desc": {},
        "example": {
            "imagePath": "D:\\\\menu.png"
        },
        "combo": ""
    },
    "pdf_compress": {
        "required": [
            "pdfPath",
            "outputPath"
        ],
        "optional": [
            "imageQuality",
            "quality",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "compressed_pdf"
        },
        "desc": {},
        "example": {
            "pdfPath": "{pdf}",
            "outputPath": "D:\\\\small.pdf"
        },
        "combo": ""
    },
    "image_color_balance": {
        "required": [
            "inputPath"
        ],
        "optional": [
            "blue",
            "factor",
            "green",
            "outputPath",
            "red",
            "resultVariable"
        ],
        "defaults": {
            "resultVariable": "balanced_image"
        },
        "desc": {},
        "example": {
            "inputPath": "{img}"
        },
        "combo": ""
    },
    "html_to_docx": {
        "required": [
            "inputPath",
            "outputPath"
        ],
        "optional": [
            "referenceDoc",
            "resultVariable"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "inputPath": "{html}",
            "outputPath": "D:\\\\out.docx"
        },
        "combo": ""
    },
    "desktop_get_control_tree": {
        "required": [],
        "optional": [
            "appVariable",
            "maxDepth",
            "resultVariable",
            "saveToVariable",
            "windowHandle"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "整棵控件树用于 AI 找到目标元素"
    },
    "phone_image_exists": {
        "required": [
            "imagePath"
        ],
        "optional": [
            "confidence",
            "deviceId",
            "resultVariable",
            "timeout",
            "waitTimeout"
        ],
        "defaults": {
            "confidence": 0.85
        },
        "desc": {},
        "example": {
            "imagePath": "D:\\\\target.png"
        },
        "combo": "前置判断，后接 condition"
    },
    "phone_pull_file": {
        "required": [
            "remotePath",
            "localPath"
        ],
        "optional": [
            "deviceId"
        ],
        "defaults": {},
        "desc": {
            "remotePath": "手机端路径",
            "localPath": "本地保存路径"
        },
        "example": {
            "remotePath": "/sdcard/DCIM/Camera/",
            "localPath": "D:\\\\photos"
        },
        "combo": ""
    },
    "phone_push_file": {
        "required": [
            "localPath",
            "remotePath"
        ],
        "optional": [
            "deviceId"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "localPath": "D:\\\\file.txt",
            "remotePath": "/sdcard/file.txt"
        },
        "combo": ""
    },
    "phone_start_mirror": {
        "required": [],
        "optional": [
            "bitRate",
            "deviceId",
            "maxSize",
            "stayAwake",
            "turnScreenOff"
        ],
        "defaults": {
            "maxSize": 1920,
            "bitRate": "8M"
        },
        "desc": {
            "maxSize": "投屏最大边像素",
            "bitRate": "码率"
        },
        "example": {},
        "combo": ""
    },
    "phone_stop_mirror": {
        "required": [],
        "optional": [
            "deviceId"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": ""
    },
    "phone_uninstall_app": {
        "required": [
            "packageName"
        ],
        "optional": [
            "deviceId"
        ],
        "defaults": {},
        "desc": {},
        "example": {
            "packageName": "com.example"
        },
        "combo": ""
    },
    "infinite_loop": {
        "required": [],
        "optional": [
            "indexVariable",
            "maxIterations"
        ],
        "defaults": {},
        "desc": {},
        "example": {},
        "combo": "需要在循环体里用 break_loop 跳出，否则会跑到上限"
    }
}
