"""
EPLAN 导线智能并线标注服务 - JSON 输入版本
支持直接输入 JSON 格式的导线数据，输出结构化并线分析结果
"""

from collections import defaultdict
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class WireInput(BaseModel):
    """输入导线数据结构"""
    id: str = Field(..., description="导线唯一标识")
    start: str = Field(..., description="起点端子")
    end: str = Field(..., description="终点端子")
    area: float = Field(..., gt=0, description="截面积 (mm²)")
    color: str = Field(..., description="颜色")
    voltage_level: str | None = Field(None, description="电压等级")
    shielded: bool = Field(False, description="是否屏蔽")
    material: str | None = Field(None, description="材料")


class AnalysisConfig(BaseModel):
    """分析配置"""
    min_parallel_count: int = Field(default=2, ge=2, description="最小并线数量")
    max_parallel_count: int | None = Field(default=None, ge=2, description="最大并线数量限制")
    check_voltage_consistency: bool = Field(default=True, description="检查电压等级一致性")
    check_shield_consistency: bool = Field(default=True, description="检查屏蔽属性一致性")


class ParallelGroupOutput(BaseModel):
    """并线组输出结构"""
    parallel_group_id: str = Field(..., description="并线组唯一标识")
    count: int = Field(..., description="导线数量")
    total_area: float = Field(..., description="总截面积 (mm²)")
    start: str = Field(..., description="起点端子")
    end: str = Field(..., description="终点端子")
    label: str = Field(..., description="标注文本")
    compliant: bool = Field(..., description="是否合规")
    color: str = Field(..., description="导线颜色")
    area: float = Field(..., description="单根截面积 (mm²)")
    wires: list[str] = Field(default_factory=list, description="包含的导线ID列表")
    notes: list[str] = Field(default_factory=list, description="判断依据/备注")


class AnalysisResult(BaseModel):
    """分析结果"""
    total_wires: int = Field(..., description="总导线数")
    parallel_groups: list[ParallelGroupOutput] = Field(default_factory=list, description="并线组列表")
    ungrouped_wires: list[str] = Field(default_factory=list, description="未分组导线ID列表")


def _normalize_path(start: str, end: str) -> tuple[str, str]:
    """规范化路径方向，确保一致性"""
    if start <= end:
        return start, end
    return end, start


def _check_attribute_consistency(
    wires: list[WireInput],
    config: AnalysisConfig
) -> tuple[bool, list[str]]:
    """
    检查组内导线属性一致性
    返回: (是否一致, 备注列表)
    """
    notes = []
    
    # 检查颜色一致性
    colors = {w.color for w in wires}
    if len(colors) > 1:
        notes.append(f"颜色不一致: {colors}")
        return False, notes
    
    # 检查截面积一致性
    areas = {w.area for w in wires}
    if len(areas) > 1:
        notes.append(f"截面积不一致: {areas} mm²")
        return False, notes
    
    # 检查电压等级一致性
    if config.check_voltage_consistency:
        voltages = {w.voltage_level for w in wires if w.voltage_level}
        if len(voltages) > 1:
            notes.append(f"电压等级不一致: {voltages}")
            return False, notes
    
    # 检查屏蔽属性一致性
    if config.check_shield_consistency:
        shields = {w.shielded for w in wires}
        if len(shields) > 1:
            notes.append("屏蔽属性不一致")
            return False, notes
    
    notes.append("所有属性一致，符合并线条件")
    return True, notes


def _check_compliance(
    wires: list[WireInput],
    config: AnalysisConfig
) -> tuple[bool, list[str]]:
    """
    检查并线组合规性
    返回: (是否合规, 备注列表)
    """
    notes = []
    compliant = True
    
    # 检查数量下限
    if len(wires) < config.min_parallel_count:
        notes.append(f"导线数量 {len(wires)} 小于最小并线数量 {config.min_parallel_count}")
        compliant = False
    
    # 检查数量上限
    if config.max_parallel_count and len(wires) > config.max_parallel_count:
        notes.append(f"导线数量 {len(wires)} 超过最大并线数量限制 {config.max_parallel_count}")
        compliant = False
    
    # 检查属性一致性
    consistent, attr_notes = _check_attribute_consistency(wires, config)
    notes.extend(attr_notes)
    if not consistent:
        compliant = False
    
    if compliant:
        notes.append(f"满足并线条件，共 {len(wires)} 根导线")
    
    return compliant, notes


def _generate_label(count: int, area: float) -> str:
    """生成标注文本: N×A mm²"""
    return f"{count}×{area:.2f}mm²"


def analyze_wires_json(
    wires_data: list[dict[str, Any]],
    config: AnalysisConfig | None = None
) -> AnalysisResult:
    """
    分析 EPLAN 导线数据，识别并线组
    
    Args:
        wires_data: JSON 格式的导线数据列表
        config: 分析配置，使用默认配置如果为 None
    
    Returns:
        AnalysisResult: 分析结果
    """
    if config is None:
        config = AnalysisConfig()
    
    # 解析输入数据
    wires = [WireInput(**w) for w in wires_data]
    
    # 按起点、终点、颜色、截面积分组
    buckets: dict[tuple[str, str, str, float], list[WireInput]] = defaultdict(list)
    
    for wire in wires:
        start, end = _normalize_path(wire.start, wire.end)
        key = (start, end, wire.color, wire.area)
        buckets[key].append(wire)
    
    # 分析并线组
    parallel_groups: list[ParallelGroupOutput] = []
    grouped_wire_ids: set[str] = set()
    group_counter = 0
    
    for (start, end, color, area), bucket_wires in buckets.items():
        # 检查是否满足最小并线数量
        if len(bucket_wires) < config.min_parallel_count:
            continue
        
        group_counter += 1
        group_id = f"PG{group_counter:02d}"
        
        # 检查合规性
        compliant, notes = _check_compliance(bucket_wires, config)
        
        # 计算总截面积
        total_area = sum(w.area for w in bucket_wires)
        
        # 收集导线ID
        wire_ids = [w.id for w in bucket_wires]
        grouped_wire_ids.update(wire_ids)
        
        group = ParallelGroupOutput(
            parallel_group_id=group_id,
            count=len(bucket_wires),
            total_area=round(total_area, 2),
            start=start,
            end=end,
            label=_generate_label(len(bucket_wires), area),
            compliant=compliant,
            color=color,
            area=area,
            wires=wire_ids,
            notes=notes
        )
        parallel_groups.append(group)
    
    # 找出未分组的导线
    all_wire_ids = {w.id for w in wires}
    ungrouped_wires = list(all_wire_ids - grouped_wire_ids)
    
    return AnalysisResult(
        total_wires=len(wires),
        parallel_groups=parallel_groups,
        ungrouped_wires=ungrouped_wires
    )


def analyze_wires_json_raw(
    wires_json: str,
    config_dict: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    原始 JSON 字符串分析接口
    
    Args:
        wires_json: JSON 字符串格式的导线数据
        config_dict: 配置字典
    
    Returns:
        dict: 分析结果字典
    """
    import json
    
    wires_data = json.loads(wires_json)
    config = AnalysisConfig(**config_dict) if config_dict else None
    
    result = analyze_wires_json(wires_data, config)
    return result.model_dump()
