"""数据表格操作模块执行器 - 异步版本"""
import asyncio
import os
import json
from datetime import datetime
from pathlib import Path

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)


@register_executor
class TableAddRowExecutor(ModuleExecutor):
    """添加数据行模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_add_row"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        row_data_str = context.resolve_value(config.get('rowData', ''))
        
        if not row_data_str:
            return ModuleResult(success=False, error="行数据不能为空")
        
        try:
            row_data = json.loads(row_data_str)
            
            if not isinstance(row_data, dict):
                return ModuleResult(success=False, error="行数据必须是JSON对象格式")
            
            context.data_rows.append(row_data)
            
            return ModuleResult(
                success=True,
                message=f"已添加数据行，当前共 {len(context.data_rows)} 行",
                data={'row': row_data, 'total_rows': len(context.data_rows)}
            )
        
        except json.JSONDecodeError as e:
            return ModuleResult(success=False, error=f"JSON解析失败: {str(e)}")
        except Exception as e:
            return ModuleResult(success=False, error=f"添加数据行失败: {str(e)}")


@register_executor
class TableAddColumnExecutor(ModuleExecutor):
    """添加数据列模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_add_column"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        column_name = context.resolve_value(config.get('columnName', ''))
        default_value = context.resolve_value(config.get('defaultValue', ''))
        
        if not column_name:
            return ModuleResult(success=False, error="列名不能为空")
        
        try:
            for row in context.data_rows:
                if column_name not in row:
                    row[column_name] = default_value
            
            if not context.data_rows:
                context.data_rows.append({column_name: default_value})
            
            return ModuleResult(
                success=True,
                message=f"已添加列 '{column_name}'",
                data={'column': column_name, 'default': default_value}
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"添加数据列失败: {str(e)}")


@register_executor
class TableSetCellExecutor(ModuleExecutor):
    """设置单元格模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_set_cell"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        row_index_str = context.resolve_value(str(config.get('rowIndex', '0')))
        column_name = context.resolve_value(config.get('columnName', ''))
        cell_value = context.resolve_value(config.get('cellValue', ''))
        
        if not column_name:
            return ModuleResult(success=False, error="列名不能为空")
        
        try:
            row_index = int(row_index_str)
        except ValueError:
            return ModuleResult(success=False, error=f"无效的行索引: {row_index_str}")
        
        if not context.data_rows:
            return ModuleResult(success=False, error="数据表格为空")
        
        if row_index < 0:
            row_index = len(context.data_rows) + row_index
        
        if row_index < 0 or row_index >= len(context.data_rows):
            return ModuleResult(success=False, error=f"行索引 {row_index} 超出范围")
        
        try:
            context.data_rows[row_index][column_name] = cell_value
            
            return ModuleResult(
                success=True,
                message=f"已设置 [{row_index}][{column_name}] = {cell_value}",
                data={'row': row_index, 'column': column_name, 'value': cell_value}
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"设置单元格失败: {str(e)}")


@register_executor
class TableGetCellExecutor(ModuleExecutor):
    """获取单元格模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_get_cell"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        row_index_str = context.resolve_value(str(config.get('rowIndex', '0')))
        column_name = context.resolve_value(config.get('columnName', ''))
        variable_name = config.get('variableName', '')
        
        if not column_name:
            return ModuleResult(success=False, error="列名不能为空")
        if not variable_name:
            return ModuleResult(success=False, error="存储变量名不能为空")
        
        try:
            row_index = int(row_index_str)
        except ValueError:
            return ModuleResult(success=False, error=f"无效的行索引: {row_index_str}")
        
        if not context.data_rows:
            return ModuleResult(success=False, error="数据表格为空")
        
        if row_index < 0:
            row_index = len(context.data_rows) + row_index
        
        if row_index < 0 or row_index >= len(context.data_rows):
            return ModuleResult(success=False, error=f"行索引 {row_index} 超出范围")
        
        row = context.data_rows[row_index]
        
        if column_name not in row:
            return ModuleResult(success=False, error=f"列 '{column_name}' 不存在")
        
        value = row[column_name]
        context.set_variable(variable_name, value)
        
        return ModuleResult(
            success=True,
            message=f"获取 [{row_index}][{column_name}] = {value}",
            data=value
        )


@register_executor
class TableDeleteRowExecutor(ModuleExecutor):
    """删除数据行模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_delete_row"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        row_index_str = context.resolve_value(str(config.get('rowIndex', '0')))
        
        try:
            row_index = int(row_index_str)
        except ValueError:
            return ModuleResult(success=False, error=f"无效的行索引: {row_index_str}")
        
        if not context.data_rows:
            return ModuleResult(success=False, error="数据表格为空")
        
        original_index = row_index
        if row_index < 0:
            row_index = len(context.data_rows) + row_index
        
        if row_index < 0 or row_index >= len(context.data_rows):
            return ModuleResult(success=False, error=f"行索引 {original_index} 超出范围")
        
        try:
            deleted_row = context.data_rows.pop(row_index)
            
            return ModuleResult(
                success=True,
                message=f"已删除第 {row_index} 行，剩余 {len(context.data_rows)} 行",
                data={'deleted': deleted_row, 'remaining': len(context.data_rows)}
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"删除数据行失败: {str(e)}")


@register_executor
class TableClearExecutor(ModuleExecutor):
    """清空数据表模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_clear"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            row_count = len(context.data_rows)
            context.data_rows.clear()
            context.current_row.clear()
            
            return ModuleResult(
                success=True,
                message=f"已清空数据表格 (原有 {row_count} 行)",
                data={'cleared_rows': row_count}
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"清空数据表失败: {str(e)}")


@register_executor
class TableExportExecutor(ModuleExecutor):
    """导出数据表模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_export"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        export_format = context.resolve_value(config.get('exportFormat', 'excel'))  # 支持变量引用
        save_path = context.resolve_value(config.get('savePath', ''))
        file_name_pattern = context.resolve_value(config.get('fileNamePattern', ''))
        sheet_name = context.resolve_value(config.get('sheetName', '数据'))  # 新增：Sheet名称
        variable_name = config.get('variableName', '')
        
        if not context.data_rows:
            return ModuleResult(success=False, error="数据表格为空，无法导出")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 文件名处理：先把残留的 {时间戳} 替换掉
            if file_name_pattern:
                file_name = file_name_pattern.replace('{时间戳}', timestamp)
            else:
                file_name = f"data_{timestamp}"
            
            # 扩展名归一化
            ext = '.xlsx' if export_format == 'excel' else '.csv'
            valid_exts = ('.xlsx', '.xls', '.csv')
            # 如果文件名带了任意有效后缀但和当前格式不一致，先去掉
            for vext in valid_exts:
                if file_name.lower().endswith(vext) and vext != ext:
                    file_name = file_name[:-len(vext)]
                    break
            if not file_name.lower().endswith(ext):
                file_name += ext
            
            # 路径处理：兼容三种情况
            #   1) save_path 为空 -> 默认导出到 backend/data 目录
            #   2) save_path 是文件路径（带 .xlsx/.csv 后缀） -> 直接当作最终文件
            #   3) save_path 是目录 -> 拼上 file_name
            #
            # 重要：当 save_path 带的扩展名与当前 export_format 不匹配时，
            # 不再把它误当成目录创建（这是导致"提示成功但找不到文件"的主因）
            default_dir = Path(__file__).parent.parent.parent / 'data'
            
            if save_path:
                save_path_norm = str(save_path).strip()
                save_path_lower = save_path_norm.lower()
                # 判断是否带任意有效扩展名
                is_file_path = any(save_path_lower.endswith(v) for v in valid_exts)
                
                if is_file_path:
                    # 用户给了完整文件路径，按当前导出格式归一化扩展名
                    p = Path(save_path_norm)
                    # 把扩展名替换为目标格式
                    final_path_obj = p.with_suffix(ext)
                    # 如果是相对路径，落到默认目录而不是后端 cwd
                    if not final_path_obj.is_absolute():
                        final_path_obj = default_dir / final_path_obj
                    final_path = str(final_path_obj)
                else:
                    # 当作目录处理
                    target_dir = Path(save_path_norm)
                    if not target_dir.is_absolute():
                        target_dir = default_dir / target_dir
                    target_dir.mkdir(parents=True, exist_ok=True)
                    final_path = str(target_dir / file_name)
            else:
                default_dir.mkdir(parents=True, exist_ok=True)
                final_path = str(default_dir / file_name)
            
            # 确保父目录存在
            parent_dir = os.path.dirname(final_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # 检查目标文件是否被其他程序（例如 Excel）占用，提前给出明确错误
            if os.path.exists(final_path):
                try:
                    with open(final_path, 'a+b'):
                        pass
                except PermissionError:
                    return ModuleResult(
                        success=False,
                        error=f"文件被占用，无法写入（请关闭已打开的 Excel 文件）: {final_path}"
                    )
            
            from app.services.data_collector import DataCollector
            
            collector = DataCollector()
            for row in context.data_rows:
                collector.add_row(row)
            
            row_count = len(context.data_rows)
            
            # 使用线程池执行同步导出操作
            loop = asyncio.get_running_loop()
            try:
                if export_format == 'excel':
                    # 大数据量给出提示日志
                    if row_count >= 100:
                        print(f"[TableExport] 正在导出 {row_count} 行数据到 Excel，请稍候...")
                    await loop.run_in_executor(None, collector.to_excel, final_path, sheet_name)
                else:
                    await loop.run_in_executor(None, collector.to_csv, final_path)
            except Exception as write_err:
                # 写文件阶段任何异常都应当报失败，不要返回 success
                import traceback
                traceback.print_exc()
                return ModuleResult(
                    success=False,
                    error=f"写入文件失败: {write_err}（路径: {final_path}）"
                )
            
            # 写入完成后再校验文件是否真的生成
            if not os.path.exists(final_path):
                return ModuleResult(
                    success=False,
                    error=f"导出完成但文件不存在，请检查路径权限: {final_path}"
                )
            try:
                file_size = os.path.getsize(final_path)
            except OSError:
                file_size = -1
            if file_size == 0:
                return ModuleResult(
                    success=False,
                    error=f"导出文件大小为 0，写入异常: {final_path}"
                )
            
            if variable_name:
                context.set_variable(variable_name, final_path)
            
            message = f"已导出 {row_count} 行数据到: {final_path}"
            if export_format == 'excel':
                message += f" (Sheet: {sheet_name})"
            
            return ModuleResult(
                success=True,
                message=message,
                data={
                    'path': final_path,
                    'rows': row_count,
                    'format': export_format,
                    'sheet_name': sheet_name if export_format == 'excel' else None,
                    'file_size': file_size,
                }
            )
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ModuleResult(success=False, error=f"导出数据表失败: {str(e)}")
