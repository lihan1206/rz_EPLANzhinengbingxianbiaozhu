from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class WireInput:
    id: str
    start_terminal: str
    end_terminal: str
    area: float
    color: str
    attributes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "WireInput":
        return cls(
            id=str(data.get("id", "")),
            start_terminal=data.get("start_terminal", data.get("起点", "")),
            end_terminal=data.get("end_terminal", data.get("终点", "")),
            area=float(data.get("area", data.get("截面积", 0))),
            color=data.get("color", data.get("颜色", "")),
            attributes=data.get("attributes", data.get("属性", {})),
        )


@dataclass
class ParallelGroupResult:
    parallel_group_id: str
    count: int
    total_area: float
    start: str
    end: str
    label: str
    compliant: bool
    notes: list[str]
    wire_ids: list[str]
    color: str
    area_per_wire: float
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "parallel_group_id": self.parallel_group_id,
            "count": self.count,
            "total_area": round(self.total_area, 2),
            "start": self.start,
            "end": self.end,
            "label": self.label,
            "compliant": self.compliant,
            "notes": self.notes,
            "wire_ids": self.wire_ids,
            "color": self.color,
            "area_per_wire": round(self.area_per_wire, 2),
            "attributes": self.attributes,
        }


@dataclass
class AnalysisConfig:
    min_parallel_count: int = 2
    max_parallel_count: int = 4
    check_voltage_compatibility: bool = True
    check_shield_consistency: bool = True


def _normalize_path(start: str, end: str) -> tuple[str, str]:
    if start <= end:
        return start, end
    return end, start


def _check_attribute_consistency(wires: list[WireInput]) -> tuple[bool, list[str]]:
    notes = []
    is_consistent = True

    voltage_levels = set()
    shield_statuses = set()
    other_attrs = defaultdict(set)

    for wire in wires:
        attrs = wire.attributes or {}
        if "voltage_level" in attrs or "电压等级" in attrs:
            voltage_levels.add(attrs.get("voltage_level", attrs.get("电压等级")))
        if "shielded" in attrs or "屏蔽" in attrs:
            shield_statuses.add(attrs.get("shielded", attrs.get("屏蔽")))
        for key, value in attrs.items():
            if key not in ["voltage_level", "电压等级", "shielded", "屏蔽"]:
                other_attrs[key].add(str(value))

    if len(voltage_levels) > 1:
        is_consistent = False
        notes.append(f"电压等级不一致: {', '.join(map(str, voltage_levels))}")

    if len(shield_statuses) > 1:
        is_consistent = False
        notes.append(f"屏蔽状态不一致: {', '.join(map(str, shield_statuses))}")

    for attr_name, values in other_attrs.items():
        if len(values) > 1:
            notes.append(f"属性 {attr_name} 存在差异: {', '.join(values)}")

    return is_consistent, notes


def _check_compliance(
    wires: list[WireInput],
    config: AnalysisConfig,
) -> tuple[bool, list[str]]:
    notes = []
    is_compliant = True

    if len(wires) < config.min_parallel_count:
        is_compliant = False
        notes.append(f"并线数量不足: 当前 {len(wires)} 根，最少需要 {config.min_parallel_count} 根")

    if len(wires) > config.max_parallel_count:
        is_compliant = False
        notes.append(f"并线数量超限: 当前 {len(wires)} 根，最多允许 {config.max_parallel_count} 根")

    attr_consistent, attr_notes = _check_attribute_consistency(wires)
    if not attr_consistent:
        is_compliant = False
        notes.extend(attr_notes)

    return is_compliant, notes


def _generate_label(count: int, area: float) -> str:
    return f"{count}×{area:.2f}mm²"


def analyze_wires(
    wires_data: list[dict],
    config: AnalysisConfig | None = None,
) -> list[dict]:
    if config is None:
        config = AnalysisConfig()

    wires = [WireInput.from_dict(w) for w in wires_data]

    buckets: dict[tuple[str, str, str, float], list[WireInput]] = defaultdict(list)

    for wire in wires:
        start, end = _normalize_path(wire.start_terminal, wire.end_terminal)
        key = (start, end, wire.color, wire.area)
        buckets[key].append(wire)

    results: list[ParallelGroupResult] = []
    group_counter = 0

    for (start, end, color, area), bucket_wires in buckets.items():
        if len(bucket_wires) < config.min_parallel_count:
            continue

        group_counter += 1
        total_area = sum(Decimal(str(w.area)) for w in bucket_wires) * Decimal(str(len(bucket_wires)))
        total_area = float(Decimal(str(area)) * len(bucket_wires))

        is_compliant, notes = _check_compliance(bucket_wires, config)

        merged_attrs = {}
        for wire in bucket_wires:
            if wire.attributes:
                for k, v in wire.attributes.items():
                    if k not in merged_attrs:
                        merged_attrs[k] = v

        result = ParallelGroupResult(
            parallel_group_id=f"PG{group_counter:02d}",
            count=len(bucket_wires),
            total_area=total_area,
            start=start,
            end=end,
            label=_generate_label(len(bucket_wires), area),
            compliant=is_compliant,
            notes=notes if notes else ["符合并线规范"],
            wire_ids=[w.id for w in bucket_wires],
            color=color,
            area_per_wire=area,
            attributes=merged_attrs,
        )
        results.append(result)

    return [r.to_dict() for r in results]


def analyze_wires_json(wires_json: str, config: AnalysisConfig | None = None) -> str:
    import json

    wires_data = json.loads(wires_json)
    results = analyze_wires(wires_data, config)
    return json.dumps(results, ensure_ascii=False, indent=2)
