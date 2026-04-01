from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=50)


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    version: str = Field(min_length=1, max_length=20)


class ProjectOut(BaseModel):
    id: int
    name: str
    version: str
    created_at: datetime

    class Config:
        from_attributes = True


class ComponentCreate(BaseModel):
    name: str
    type: str
    terminal: str
    description: str = ""


class WireCreate(BaseModel):
    number: str
    area: float = Field(gt=0)
    color: str
    material: str = "铜"
    length: float = Field(ge=0)
    start_terminal: str
    end_terminal: str
    is_shielded: bool = False


class ImportResult(BaseModel):
    imported_components: int
    imported_wires: int
    import_record_id: int


class ParallelGroupOut(BaseModel):
    id: int
    project_id: int
    group_name: str
    count: int
    total_area: Decimal
    start_terminal: str
    end_terminal: str
    parallel_type: str
    suggestion: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    min_parallel_count: int = Field(default=2, ge=2, le=10)


class AnalyzeResult(BaseModel):
    groups_created: int


class AnnotationRequest(BaseModel):
    template: str = Field(default="{{count}}x{{area}}mm²", max_length=80)
    style: str = Field(default="标准", max_length=40)


class AnnotationOut(BaseModel):
    id: int
    group_id: int
    text: str
    position_x: float
    position_y: float
    style: str
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    project_count: int
    wire_count: int
    parallel_group_count: int
    annotation_count: int


class DistributionItem(BaseModel):
    name: str
    value: int


class ImportRecordOut(BaseModel):
    id: int
    project_id: int
    filename: str
    file_format: str
    row_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OperationLogOut(BaseModel):
    id: int
    user_id: int | None
    action: str
    target: str
    detail: str
    created_at: datetime

    class Config:
        from_attributes = True


class WireInput(BaseModel):
    id: str = Field(description="导线唯一标识")
    start_terminal: str = Field(alias="start", description="起点端子")
    end_terminal: str = Field(alias="end", description="终点端子")
    area: float = Field(gt=0, description="截面积(mm²)")
    color: str = Field(description="颜色")
    attributes: dict[str, str | bool | int | float] | None = Field(default=None, description="扩展属性")

    class Config:
        populate_by_name = True


class WireDataInput(BaseModel):
    wire_id: str = Field(description="导线唯一标识")
    name: str = Field(description="导线名称")
    node_a: str = Field(description="节点A")
    node_b: str = Field(description="节点B")
    color: str = Field(description="颜色")
    cable_type: str = Field(description="电缆类型")
    attributes: dict[str, str | bool | int | float] | None = Field(default=None, description="扩展属性")


class WireDataCreate(BaseModel):
    wire_id: str | None = Field(default=None, description="导线唯一标识")
    name: str | None = Field(default=None, description="导线名称")
    node_a: str | None = Field(default=None, description="节点A")
    node_b: str | None = Field(default=None, description="节点B")
    cable_type: str | None = Field(default=None, description="电缆类型")
    number: str = Field(description="导线编号")
    area: float = Field(gt=0, description="截面积(mm²)")
    color: str = Field(description="颜色")
    material: str = Field(default="铜", description="材质")
    length: float = Field(default=0, ge=0, description="长度")
    start_terminal: str = Field(description="起点端子")
    end_terminal: str = Field(description="终点端子")
    is_shielded: bool = Field(default=False, description="是否屏蔽")


class WireAnalyzeConfig(BaseModel):
    min_parallel_count: int = Field(default=2, ge=2, description="最小并线数量")
    max_parallel_count: int = Field(default=4, ge=2, le=10, description="最大并线数量")
    check_voltage_compatibility: bool = Field(default=True, description="检查电压等级兼容性")
    check_shield_consistency: bool = Field(default=True, description="检查屏蔽一致性")


class WireAnalyzeRequest(BaseModel):
    wires: list[WireInput] = Field(min_length=1, description="导线列表")
    config: WireAnalyzeConfig | None = Field(default=None, description="分析配置")


class ParallelGroupResult(BaseModel):
    parallel_group_id: str = Field(description="并线组ID，如 PG01")
    count: int = Field(description="并线数量")
    total_area: float = Field(description="总截面积(mm²)")
    start: str = Field(description="起点端子")
    end: str = Field(description="终点端子")
    label: str = Field(description="标注文本，格式: N×A mm²")
    compliant: bool = Field(description="是否合规")
    notes: list[str] = Field(description="判断依据说明")
    wire_ids: list[str] = Field(description="包含的导线ID列表")
    color: str = Field(description="导线颜色")
    area_per_wire: float = Field(description="单根导线截面积(mm²)")
    attributes: dict[str, str | bool | int | float] = Field(default_factory=dict, description="合并后的属性")


class WireAnalyzeResult(BaseModel):
    parallel_groups: list[ParallelGroupResult] = Field(description="并线组列表")
    total_wires: int = Field(description="输入导线总数")
    grouped_wires: int = Field(description="已分组的导线数")
    ungrouped_wires: int = Field(description="未分组的导线数")


class WireDataAnalyzeRequest(BaseModel):
    wires: list[WireDataInput] = Field(min_length=1, description="导线数据列表")
    config: WireAnalyzeConfig | None = Field(default=None, description="分析配置")
    rules_file: str | None = Field(default=None, description="自定义规则配置文件路径")


class ParallelGroupDataResult(BaseModel):
    group_id: str = Field(description="并线组ID")
    wires: list[str] = Field(description="包含的导线ID列表")
    name: str = Field(description="合并后名称")
    color: str = Field(description="合并后颜色")
    cable_type: str = Field(description="合并后类型")
    notes: list[str] = Field(description="推理说明")


class WireDataAnalyzeResult(BaseModel):
    groups: list[ParallelGroupDataResult] = Field(description="并线组列表")
    total_wires: int = Field(description="输入导线总数")
    grouped_wires: int = Field(description="已分组的导线数")
    ungrouped_wires: int = Field(description="未分组的导线数")
    warnings: list[str] = Field(default_factory=list, description="警告信息列表")
    errors: list[str] = Field(default_factory=list, description="错误信息列表")


class ImportValidationResult(BaseModel):
    valid: bool = Field(description="是否有效")
    errors: list[str] = Field(default_factory=list, description="错误列表")
    warnings: list[str] = Field(default_factory=list, description="警告列表")
    duplicate_wire_ids: list[str] = Field(default_factory=list, description="重复的导线ID列表")
    missing_fields: list[str] = Field(default_factory=list, description="缺失字段列表")
