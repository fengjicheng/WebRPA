"""
自定义模块数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CustomModuleParameter(BaseModel):
    """自定义模块参数定义"""
    name: str = Field(..., description="参数名称")
    label: str = Field(..., description="参数显示标签")
    type: str = Field(default="string", description="参数类型: string, number, boolean, select, textarea")
    default_value: Any = Field(default="", description="默认值")
    required: bool = Field(default=False, description="是否必填")
    placeholder: str = Field(default="", description="占位符文本")
    description: str = Field(default="", description="参数说明")
    options: List[Dict[str, str]] = Field(default_factory=list, description="下拉选项（type=select时使用）")


class CustomModuleOutput(BaseModel):
    """自定义模块输出定义"""
    name: str = Field(..., description="输出变量名")
    label: str = Field(..., description="输出显示标签")
    description: str = Field(default="", description="输出说明")


class CustomModule(BaseModel):
    """自定义模块"""
    id: str = Field(..., description="模块ID")
    name: str = Field(..., description="模块名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(default="", description="模块描述")
    icon: str = Field(default="📦", description="模块图标")
    color: str = Field(default="#8B5CF6", description="模块颜色（十六进制）")
    category: str = Field(default="custom", description="模块分类")
    
    # 参数定义
    parameters: List[CustomModuleParameter] = Field(default_factory=list, description="输入参数")
    outputs: List[CustomModuleOutput] = Field(default_factory=list, description="输出变量")
    
    # 工作流定义
    workflow: Dict[str, Any] = Field(..., description="内部工作流定义（nodes和edges）")
    
    # 元数据
    author: str = Field(default="", description="作者")
    version: str = Field(default="1.0.0", description="版本号")
    tags: List[str] = Field(default_factory=list, description="标签")
    
    # 统计信息
    usage_count: int = Field(default=0, description="使用次数")
    download_count: int = Field(default=0, description="下载次数")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    # 发布状态
    is_published: bool = Field(default=False, description="是否已发布到工作流仓库")
    is_builtin: bool = Field(default=False, description="是否为内置模块")
    is_favorite: bool = Field(default=False, description="是否收藏")
    sort_order: int = Field(default=0, description="排序顺序")


class CustomModuleCreate(BaseModel):
    """创建自定义模块请求"""
    name: str = Field(..., description="模块名称（英文标识符）")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(default="", description="模块描述")
    icon: str = Field(default="📦", description="模块图标")
    color: str = Field(default="#8B5CF6", description="模块颜色（十六进制）")
    category: str = Field(default="custom", description="模块分类")
    parameters: List[CustomModuleParameter] = Field(default_factory=list, description="输入参数")
    outputs: List[CustomModuleOutput] = Field(default_factory=list, description="输出变量")
    workflow: Dict[str, Any] = Field(..., description="内部工作流定义")
    tags: List[str] = Field(default_factory=list, description="标签")


class CustomModuleUpdate(BaseModel):
    """更新自定义模块请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    parameters: Optional[List[CustomModuleParameter]] = None
    outputs: Optional[List[CustomModuleOutput]] = None
    workflow: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    sort_order: Optional[int] = None


class CustomModuleListResponse(BaseModel):
    """自定义模块列表响应"""
    modules: List[CustomModule]
    total: int
