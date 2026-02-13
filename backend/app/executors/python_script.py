"""Python脚本执行模块"""
import asyncio
import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Optional

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)


@register_executor
class PythonScriptExecutor(ModuleExecutor):
    """Python脚本执行模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "python_script"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        执行Python脚本
        
        配置参数:
        - scriptContent: 脚本内容（直接输入）
        - scriptPath: 脚本文件路径（从文件读取）
        - scriptMode: 脚本模式 ('content' 或 'file')
        - pythonPath: Python解释器路径（可选，默认使用内置Python3.13）
        - useBuiltinPython: 是否使用内置Python（默认True）
        - scriptArgs: 脚本参数（可选，命令行参数）
        - workingDir: 工作目录（可选）
        - timeout: 超时时间（秒，默认60）
        - captureOutput: 是否捕获输出（默认True）
        - resultVariable: 结果变量名（可选，接收脚本返回值）
        - stdoutVariable: 标准输出变量名（可选）
        - stderrVariable: 标准错误变量名（可选）
        - returnCodeVariable: 返回码变量名（可选）
        """
        
        script_mode = config.get('scriptMode', 'content')
        script_content = context.resolve_value(config.get('scriptContent', ''))
        script_path = context.resolve_value(config.get('scriptPath', ''))
        use_builtin_python = config.get('useBuiltinPython', True)
        python_path = context.resolve_value(config.get('pythonPath', ''))
        script_args = context.resolve_value(config.get('scriptArgs', ''))
        working_dir = context.resolve_value(config.get('workingDir', ''))
        timeout = int(config.get('timeout', 60))
        capture_output = config.get('captureOutput', True)
        
        result_variable = config.get('resultVariable', '')
        stdout_variable = config.get('stdoutVariable', '')
        stderr_variable = config.get('stderrVariable', '')
        return_code_variable = config.get('returnCodeVariable', '')
        
        try:
            # 确定Python解释器路径
            if use_builtin_python:
                # 使用内置Python3.13
                project_root = Path(__file__).parent.parent.parent.parent
                builtin_python = project_root / 'Python313' / 'python.exe'
                if not builtin_python.exists():
                    return ModuleResult(
                        success=False,
                        error=f"内置Python不存在: {builtin_python}"
                    )
                python_executable = str(builtin_python)
            elif python_path:
                # 使用用户指定的Python
                if not os.path.exists(python_path):
                    return ModuleResult(
                        success=False,
                        error=f"指定的Python路径不存在: {python_path}"
                    )
                python_executable = python_path
            else:
                # 使用系统Python
                python_executable = sys.executable
            
            # 准备所有变量（通过环境变量传递）
            env = os.environ.copy()
            
            # 将所有工作流变量序列化为JSON并通过环境变量传递
            all_vars = dict(context.variables)
            env['WEBRPA_VARS'] = json.dumps(all_vars, ensure_ascii=False, default=str)
            
            # 准备脚本文件
            temp_script = None
            temp_output_file = None
            if script_mode == 'content':
                # 从内容创建临时脚本文件
                if not script_content:
                    return ModuleResult(success=False, error="脚本内容不能为空")
                
                # 创建临时输出文件（用于接收返回值）
                temp_output_file = tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.json',
                    delete=False,
                    encoding='utf-8'
                )
                temp_output_file.close()
                output_file_path = temp_output_file.name
                
                # 在脚本前添加辅助代码
                helper_code = f'''
# ========== WebRPA 脚本辅助代码（自动添加） ==========
import json
import os
import sys

class VarsProxy:
    """变量代理类，用于通过 vars.变量名 访问工作流变量"""
    def __init__(self, variables):
        self._variables = variables
    
    def __getattr__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return self._variables.get(name)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            self._variables[name] = value
    
    def __dir__(self):
        return list(self._variables.keys())
    
    def get(self, name, default=None):
        """获取变量值，如果不存在则返回默认值"""
        return self._variables.get(name, default)
    
    def keys(self):
        """获取所有变量名"""
        return self._variables.keys()
    
    def values(self):
        """获取所有变量值"""
        return self._variables.values()
    
    def items(self):
        """获取所有变量键值对"""
        return self._variables.items()

# 加载所有工作流变量
_vars_json = os.environ.get('WEBRPA_VARS', '{{}}')
try:
    _all_vars = json.loads(_vars_json)
except:
    _all_vars = {{}}

# 创建 vars 对象，用户可以通过 vars.变量名 访问所有变量
vars = VarsProxy(_all_vars)

# 输出文件路径
_output_file = r'{output_file_path}'

# 用于保存返回值的函数（内部使用）
def _save_result(result):
    """保存返回值到文件"""
    try:
        with open(_output_file, 'w', encoding='utf-8') as f:
            json.dump({{'result': result}}, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        print(f"保存返回值失败: {{e}}", file=sys.stderr)

# ========== 用户脚本开始 ==========
# 定义一个函数来包装用户代码，以便捕获返回值
def _user_script():
'''
                
                # 缩进用户脚本
                indented_script = '\n'.join('    ' + line for line in script_content.split('\n'))
                
                # 添加脚本结尾代码
                footer_code = '''

# ========== 用户脚本结束 ==========

# 执行用户脚本并捕获返回值
try:
    _result = _user_script()
    if _result is not None:
        _save_result(_result)
except Exception as e:
    print(f"脚本执行错误: {{e}}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
                
                # 创建临时文件
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.py',
                    delete=False,
                    encoding='utf-8'
                ) as f:
                    f.write(helper_code + indented_script + '\n' + footer_code)
                    temp_script = f.name
                    script_file = temp_script
            else:
                # 从文件读取
                if not script_path:
                    return ModuleResult(success=False, error="脚本文件路径不能为空")
                
                if not os.path.exists(script_path):
                    return ModuleResult(
                        success=False,
                        error=f"脚本文件不存在: {script_path}"
                    )
                script_file = script_path
                output_file_path = None
            
            # 准备命令
            cmd = [python_executable, script_file]
            
            # 添加脚本参数
            if script_args:
                # 支持空格分隔的参数
                args_list = script_args.split()
                cmd.extend(args_list)
            
            # 准备工作目录
            cwd = working_dir if working_dir and os.path.exists(working_dir) else None
            
            # 执行脚本
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    cwd=cwd,
                    env=env
                )
                
                # 等待执行完成（带超时）
                try:
                    stdout_data, stderr_data = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout
                    )
                    return_code = process.returncode
                except asyncio.TimeoutError:
                    # 超时，终止进程
                    try:
                        process.kill()
                        await process.wait()
                    except:
                        pass
                    
                    return ModuleResult(
                        success=False,
                        error=f"脚本执行超时（{timeout}秒）"
                    )
                
                # 解码输出
                stdout_text = stdout_data.decode('utf-8', errors='ignore') if stdout_data else ''
                stderr_text = stderr_data.decode('utf-8', errors='ignore') if stderr_data else ''
                
                # 读取返回值（如果有）
                script_result = None
                if output_file_path and os.path.exists(output_file_path):
                    try:
                        with open(output_file_path, 'r', encoding='utf-8') as f:
                            result_data = json.load(f)
                            script_result = result_data.get('result')
                    except Exception as e:
                        # 读取返回值失败不影响主流程
                        pass
                
                # 保存到变量
                if stdout_variable:
                    context.set_variable(stdout_variable, stdout_text)
                if stderr_variable:
                    context.set_variable(stderr_variable, stderr_text)
                if return_code_variable:
                    context.set_variable(return_code_variable, return_code)
                if result_variable and script_result is not None:
                    context.set_variable(result_variable, script_result)
                
                # 判断执行结果
                if return_code == 0:
                    message = f"脚本执行成功（返回码: {return_code}）"
                    if script_result is not None:
                        message += f"，已返回结果到变量 {result_variable}"
                    
                    return ModuleResult(
                        success=True,
                        message=message,
                        data={
                            'stdout': stdout_text,
                            'stderr': stderr_text,
                            'returnCode': return_code,
                            'result': script_result
                        }
                    )
                else:
                    return ModuleResult(
                        success=False,
                        error=f"脚本执行失败（返回码: {return_code}）\n标准错误输出:\n{stderr_text}",
                        data={
                            'stdout': stdout_text,
                            'stderr': stderr_text,
                            'returnCode': return_code
                        }
                    )
                
            finally:
                # 清理临时文件
                if temp_script and os.path.exists(temp_script):
                    try:
                        os.unlink(temp_script)
                    except:
                        pass
                if temp_output_file and os.path.exists(temp_output_file.name):
                    try:
                        os.unlink(temp_output_file.name)
                    except:
                        pass
        
        except Exception as e:
            return ModuleResult(success=False, error=f"执行失败: {str(e)}")
