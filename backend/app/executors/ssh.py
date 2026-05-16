"""SSH远程操作模块执行器"""
import json
from typing import Any, Optional
from app.executors.base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor


@register_executor
class SSHConnectExecutor(ModuleExecutor):
    """SSH连接执行器"""
    
    @property
    def module_type(self) -> str:
        return "ssh_connect"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """建立SSH连接"""
        try:
            import paramiko
            
            host = context.resolve_value(config.get('host', ''))
            port = int(context.resolve_value(config.get('port', 22)))
            username = context.resolve_value(config.get('username', ''))
            password = context.resolve_value(config.get('password', ''))
            key_file = context.resolve_value(config.get('keyFile', ''))
            connection_name = config.get('connectionName', 'ssh_conn')
            timeout = int(config.get('timeout', 30))
            
            if not all([host, username]):
                return ModuleResult(
                    success=False,
                    message="SSH连接配置不完整（主机和用户名必填）",
                    error="配置不完整"
                )
            
            # 创建SSH客户端
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接参数
            connect_kwargs = {
                'hostname': host,
                'port': port,
                'username': username,
                'timeout': timeout
            }
            
            # 使用密钥或密码认证
            if key_file:
                connect_kwargs['key_filename'] = key_file
            elif password:
                connect_kwargs['password'] = password
            else:
                return ModuleResult(
                    success=False,
                    message="必须提供密码或密钥文件",
                    error="认证信息缺失"
                )
            
            # 建立连接
            client.connect(**connect_kwargs)
            
            # 保存连接到上下文
            if not hasattr(context, '_ssh_connections'):
                context._ssh_connections = {}
            context._ssh_connections[connection_name] = client
            
            return ModuleResult(
                success=True,
                message=f"成功连接到SSH服务器: {username}@{host}:{port}"
            )
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[SSHConnectExecutor] 执行失败: {error_detail}")
            return ModuleResult(
                success=False,
                message=f"SSH连接失败: {str(e)}",
                error=str(e)
            )


@register_executor
class SSHExecuteCommandExecutor(ModuleExecutor):
    """SSH命令执行执行器"""
    
    @property
    def module_type(self) -> str:
        return "ssh_execute_command"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """执行SSH命令"""
        try:
            connection_name = config.get('connectionName', 'ssh_conn')
            command = context.resolve_value(config.get('command', ''))
            output_variable = config.get('outputVariable', 'ssh_output')
            error_variable = config.get('errorVariable', 'ssh_error')
            exit_code_variable = config.get('exitCodeVariable', 'ssh_exit_code')
            timeout = int(config.get('timeout', 30))
            
            if not command:
                return ModuleResult(
                    success=False,
                    message="命令不能为空",
                    error="命令为空"
                )
            
            # 获取SSH连接
            if not hasattr(context, '_ssh_connections') or connection_name not in context._ssh_connections:
                return ModuleResult(
                    success=False,
                    message=f"SSH连接 {connection_name} 不存在，请先建立连接",
                    error="连接不存在"
                )
            
            client = context._ssh_connections[connection_name]
            
            # 执行命令
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            # 获取输出
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            # 保存结果到变量
            context.set_variable(output_variable, output)
            context.set_variable(error_variable, error)
            context.set_variable(exit_code_variable, exit_code)
            
            success = exit_code == 0
            message = f"命令执行{'成功' if success else '失败'}，退出码: {exit_code}"
            
            return ModuleResult(
                success=success,
                message=message,
                data={
                    'output': output,
                    'error': error,
                    'exit_code': exit_code
                }
            )
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[SSHExecuteCommandExecutor] 执行失败: {error_detail}")
            return ModuleResult(
                success=False,
                message=f"SSH命令执行失败: {str(e)}",
                error=str(e)
            )


@register_executor
class SSHUploadFileExecutor(ModuleExecutor):
    """SSH文件上传执行器"""
    
    @property
    def module_type(self) -> str:
        return "ssh_upload_file"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """上传文件到远程服务器"""
        try:
            connection_name = config.get('connectionName', 'ssh_conn')
            local_path = context.resolve_value(config.get('localPath', ''))
            remote_path = context.resolve_value(config.get('remotePath', ''))
            
            if not all([local_path, remote_path]):
                return ModuleResult(
                    success=False,
                    message="本地路径和远程路径不能为空",
                    error="路径为空"
                )
            
            # 获取SSH连接
            if not hasattr(context, '_ssh_connections') or connection_name not in context._ssh_connections:
                return ModuleResult(
                    success=False,
                    message=f"SSH连接 {connection_name} 不存在",
                    error="连接不存在"
                )
            
            client = context._ssh_connections[connection_name]
            
            # 创建SFTP客户端
            sftp = client.open_sftp()
            
            # 上传文件
            sftp.put(local_path, remote_path)
            
            # 关闭SFTP
            sftp.close()
            
            return ModuleResult(
                success=True,
                message=f"文件上传成功: {local_path} -> {remote_path}"
            )
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[SSHUploadFileExecutor] 执行失败: {error_detail}")
            return ModuleResult(
                success=False,
                message=f"SSH文件上传失败: {str(e)}",
                error=str(e)
            )


@register_executor
class SSHDownloadFileExecutor(ModuleExecutor):
    """SSH文件下载执行器"""
    
    @property
    def module_type(self) -> str:
        return "ssh_download_file"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """从远程服务器下载文件"""
        try:
            connection_name = config.get('connectionName', 'ssh_conn')
            remote_path = context.resolve_value(config.get('remotePath', ''))
            local_path = context.resolve_value(config.get('localPath', ''))
            
            if not all([remote_path, local_path]):
                return ModuleResult(
                    success=False,
                    message="远程路径和本地路径不能为空",
                    error="路径为空"
                )
            
            # 获取SSH连接
            if not hasattr(context, '_ssh_connections') or connection_name not in context._ssh_connections:
                return ModuleResult(
                    success=False,
                    message=f"SSH连接 {connection_name} 不存在",
                    error="连接不存在"
                )
            
            client = context._ssh_connections[connection_name]
            
            # 创建SFTP客户端
            sftp = client.open_sftp()
            
            # 下载文件
            sftp.get(remote_path, local_path)
            
            # 关闭SFTP
            sftp.close()
            
            return ModuleResult(
                success=True,
                message=f"文件下载成功: {remote_path} -> {local_path}"
            )
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[SSHDownloadFileExecutor] 执行失败: {error_detail}")
            return ModuleResult(
                success=False,
                message=f"SSH文件下载失败: {str(e)}",
                error=str(e)
            )


@register_executor
class SSHDisconnectExecutor(ModuleExecutor):
    """SSH断开连接执行器"""
    
    @property
    def module_type(self) -> str:
        return "ssh_disconnect"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """断开SSH连接"""
        try:
            connection_name = config.get('connectionName', 'ssh_conn')
            
            # 获取SSH连接
            if not hasattr(context, '_ssh_connections') or connection_name not in context._ssh_connections:
                return ModuleResult(
                    success=False,
                    message=f"SSH连接 {connection_name} 不存在",
                    error="连接不存在"
                )
            
            client = context._ssh_connections[connection_name]
            
            # 关闭连接
            client.close()
            
            # 从上下文中移除
            del context._ssh_connections[connection_name]
            
            return ModuleResult(
                success=True,
                message=f"SSH连接 {connection_name} 已断开"
            )
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[SSHDisconnectExecutor] 执行失败: {error_detail}")
            return ModuleResult(
                success=False,
                message=f"SSH断开连接失败: {str(e)}",
                error=str(e)
            )
