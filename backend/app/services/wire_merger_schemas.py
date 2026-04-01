"""
并线合并功能的Pydantic模型
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ========== 请求模型 ==========

class WireData(BaseModel):
    """单条导线数据"""
    WIRE_ID: str = Field(..., description="导线唯一标识")
    NAME: str = Field(..., description="导线名称")
    NODE_A: str = Field(..., description="起始节点")
    NODE_B: str = Field(..., description="终止节点")
    COLOR: str = Field(..., description="导线颜色")
    CABLE_TYPE: str = Field(..., description="电缆类型")
    # 允许扩展字段
    model_config = {"extra": "allow"}


class WireMergeRequest(BaseModel):
    """并线合并请求"""
    project_name: Optional[str] = Field(default=None, description="项目名称")
    wires: list[WireData] = Field(..., description="导线数据列表")
    config_id: Optional[int] = Field(default=None, description="规则配置ID")


class WireMergeFromCSVRequest(BaseModel):
    """从CSV合并请求"""
    project_name: Optional[str] = Field(default=None, description="项目名称")
    config_id: Optional[int] = Field(default=None, description="规则配置ID")


class AutoMergeRule(BaseModel):
    """自动合并规则"""
    field: str = Field(..., description="字段名")
    operator: str = Field(..., description="操作符: contains, equals, starts_with, ends_with")
    value: str = Field(..., description="比较值")


class MergeRuleConfigCreate(BaseModel):
    """创建合并规则配置"""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    description: str = Field(default="", max_length=500, description="配置描述")
    match_fields: list[str] = Field(default=["name", "color", "cable_type"], description="匹配字段列表")
    auto_merge_rules: list[AutoMergeRule] = Field(default=[], description="自动合并规则")
    case_sensitive: bool = Field(default=False, description="是否区分大小写")
    ignore_whitespace: bool = Field(default=True, description="是否忽略空白字符")
    is_default: bool = Field(default=False, description="是否为默认配置")


class MergeRuleConfigUpdate(BaseModel):
    """更新合并规则配置"""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    match_fields: Optional[list[str]] = Field(default=None)
    auto_merge_rules: Optional[list[AutoMergeRule]] = Field(default=None)
    case_sensitive: Optional[bool] = Field(default=None)
    ignore_whitespace: Optional[bool] = Field(default=None)
    is_default: Optional[bool] = Field(default=None)


# ========== 响应模型 ==========

class WireInfo(BaseModel):
    """导线信息"""
    wire_id: str
    name: str
    node_a: str
    node_b: str
    color: str
    cable_type: str


class ParallelGroupOut(BaseModel):
    """并线组输出"""
    group_id: int
    wires: list[str]
    name: str
    color: str
    cable_type: str
    notes: str
    wire_count: int


class MergeSummary(BaseModel):
    """合并摘要"""
    total_groups: int
    total_wires: int
    merged_groups: int


class WireMergeResult(BaseModel):
    """并线合并结果"""
    success: bool
    summary: MergeSummary
    groups: list[ParallelGroupOut]
    errors: list[str]
    warnings: list[str]


class WireImportResult(BaseModel):
    """导线导入结果"""
    success: bool
    project_id: int
    imported_count: int
    errors: list[str]
    warnings: list[str]


class MergeRuleConfigOut(BaseModel):
    """合并规则配置输出"""
    id: int
    name: str
    description: str
    match_fields: list[str]
    auto_merge_rules: list[AutoMergeRule]
    config: dict
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WireMergeProjectOut(BaseModel):
    """并线合并项目输出"""
    id: int
    name: str
    description: str
    config: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WireStatistics(BaseModel):
    """导线统计信息"""
    total_wires: int
    unique_names: int
    unique_colors: int
    unique_cable_types: int
    color_distribution: dict[str, int]
    cable_type_distribution: dict[str, int]


class MergeGroupDetail(BaseModel):
    """并线组详情"""
    group_id: int
    name: str
    color: str
    cable_type: str
    notes: str
    wire_count: int
    wires: list[WireInfo]
    created_at: datetime


class WireMergeProjectDetail(BaseModel):
    """并线合并项目详情"""
    id: int
    name: str
    description: str
    config: dict
    statistics: WireStatistics
    groups: list[MergeGroupDetail]
    created_at: datetime
    updated_at: datetime
