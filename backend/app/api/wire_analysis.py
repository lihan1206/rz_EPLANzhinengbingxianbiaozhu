from collections import defaultdict
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/wire-analysis", tags=["导线分析"])


class WireData(BaseModel):
    id: str
    start: str = Field(description="起点端子")
    end: str = Field(description="终点端子")
    area: float = Field(gt=0, description="截面积(mm²)")
    color: str = Field(description="颜色")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="属性（电压等级、屏蔽等）"
    )


class WireAnalysisRequest(BaseModel):
    wires: list[WireData] = Field(description="EPLAN导出的导线数据")
    min_parallel_count: int = Field(default=2, ge=2, le=10, description="最小并线数量")
    max_parallel_count: int = Field(default=4, ge=2, le=20, description="最大并线数量")


class ParallelGroupOutput(BaseModel):
    parallel_group_id: str = Field(description="并线组ID，如PG01")
    count: int = Field(description="并线数量")
    total_area: float = Field(description="总截面积")
    start: str = Field(description="起点端子")
    end: str = Field(description="终点端子")
    label: str = Field(description="标注文本，格式：N×A mm²")
    compliant: bool = Field(description="是否合规")
    notes: list[str] = Field(description="判断依据")


class WireAnalysisResponse(BaseModel):
    parallel_groups: list[ParallelGroupOutput] = Field(description="并线组列表")
    total_groups: int = Field(description="并线组总数")
    total_wires_analyzed: int = Field(description="分析的导线总数")


def _normalize_path(start: str, end: str) -> tuple[str, str]:
    if start <= end:
        return start, end
    return end, start


def _properties_match(prop1: dict[str, Any], prop2: dict[str, Any]) -> bool:
    if set(prop1.keys()) != set(prop2.keys()):
        return False
    for key in prop1:
        if str(prop1[key]) != str(prop2[key]):
            return False
    return True


@router.post("/analyze", response_model=WireAnalysisResponse)
def analyze_wires(request: WireAnalysisRequest):
    if not request.wires:
        raise HTTPException(status_code=400, detail="未提供导线数据")

    buckets: dict[tuple[str, str, str, str], list[WireData]] = defaultdict(list)
    wire_buckets: dict[tuple[str, str, str, str], list[WireData]] = defaultdict(list)

    for wire in request.wires:
        start, end = _normalize_path(wire.start, wire.end)
        key = (start, end, str(wire.area), wire.color)
        buckets[key].append(wire)
        wire_buckets[key].append(wire)

    parallel_groups: list[ParallelGroupOutput] = []
    group_counter = 1

    for key, wire_list in buckets.items():
        start, end, area_str, color = key

        if len(wire_list) < request.min_parallel_count:
            continue

        first_props = wire_list[0].properties
        all_props_match = all(
            _properties_match(wire.properties, first_props) for wire in wire_list[1:]
        )

        if not all_props_match:
            continue

        count = len(wire_list)
        area = float(area_str)
        total_area_val = count * area

        label = f"{count}×{area:.2f} mm²"

        notes: list[str] = []
        compliant = True

        if count < request.min_parallel_count:
            compliant = False
            notes.append(f"并线数量({count})小于最小要求({request.min_parallel_count})")

        if count > request.max_parallel_count:
            compliant = False
            notes.append(f"并线数量({count})超过最大限制({request.max_parallel_count})")

        if compliant and not notes:
            notes.append(f"符合并线规则：{count}根导线，{color}颜色，{area:.2f}mm²截面积")

        if first_props:
            props_str = ", ".join([f"{k}:{v}" for k, v in first_props.items()])
            notes.append(f"属性一致：{props_str}")

        parallel_groups.append(
            ParallelGroupOutput(
                parallel_group_id=f"PG{group_counter:02d}",
                count=count,
                total_area=round(total_area_val, 2),
                start=start,
                end=end,
                label=label,
                compliant=compliant,
                notes=notes,
            )
        )
        group_counter += 1

    return WireAnalysisResponse(
        parallel_groups=parallel_groups,
        total_groups=len(parallel_groups),
        total_wires_analyzed=len(request.wires),
    )
