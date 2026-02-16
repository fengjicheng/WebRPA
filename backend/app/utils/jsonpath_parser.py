"""自定义JSONPath解析器 - 支持中文字段名"""


def parse_jsonpath(data, path: str):
    """
    简单的JSONPath解析器，支持中文字段名
    
    示例:
    - $.data.result.records[0].fields.文本
    - $.data.result.records[0].fields.name
    - $.items[*]
    """
    if path.startswith('$'):
        path = path[1:]
    if path.startswith('.'):
        path = path[1:]
    
    if not path:
        return data
    
    current = data
    parts = _split_path(path)
    
    for part in parts:
        if current is None:
            return None
        
        # 处理数组索引 [0], [*]
        if part.startswith('[') and part.endswith(']'):
            index_str = part[1:-1]
            if index_str == '*':
                # 返回整个数组
                if isinstance(current, list):
                    return current
                else:
                    return None
            else:
                try:
                    index = int(index_str)
                    if isinstance(current, list) and -len(current) <= index < len(current):
                        current = current[index]
                    else:
                        return None
                except ValueError:
                    return None
        else:
            # 处理属性名，可能带数组索引 如: records[0]
            if '[' in part:
                prop_name = part[:part.index('[')]
                array_part = part[part.index('['):]
                
                if isinstance(current, dict) and prop_name in current:
                    current = current[prop_name]
                    current = parse_jsonpath(current, array_part)
                else:
                    return None
            else:
                # 普通属性访问，支持中文
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
    
    return current


def _split_path(path: str) -> list:
    """
    分割JSONPath路径
    
    示例:
    - "data.result.records[0].fields.文本" -> ["data", "result", "records[0]", "fields", "文本"]
    - "items[*]" -> ["items[*]"]
    """
    parts = []
    current = ''
    in_bracket = False
    
    for char in path:
        if char == '[':
            if current:
                # 将属性名和括号合并，如 "records" + "[0]" -> "records[0]"
                in_bracket = True
                current += '['
            else:
                # 单独的括号，如 "[0]"
                in_bracket = True
                current = '['
        elif char == ']':
            current += ']'
            parts.append(current)
            current = ''
            in_bracket = False
        elif char == '.' and not in_bracket:
            if current:
                parts.append(current)
                current = ''
        else:
            current += char
    
    if current:
        parts.append(current)
    
    return parts
