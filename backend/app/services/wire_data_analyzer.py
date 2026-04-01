import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.services.rule_engine import (
    ParallelGroup,
    RuleEngine,
    WireData,
)


class WireDataAnalyzer:
    def __init__(self, rules_file: str | Path | None = None):
        self.rule_engine = RuleEngine()
        if rules_file:
            self.rule_engine.load_from_file(rules_file)

    def analyze(self, wires_data: list[dict[str, Any]]) -> dict[str, Any]:
        wires = self._parse_wires(wires_data)
        warnings: list[str] = []
        errors: list[str] = []

        validation_result = self._validate_wires(wires)
        warnings.extend(validation_result["warnings"])
        errors.extend(validation_result["errors"])

        if errors:
            return {
                "groups": [],
                "total_wires": len(wires),
                "grouped_wires": 0,
                "ungrouped_wires": len(wires),
                "warnings": warnings,
                "errors": errors,
            }

        groups = self._group_wires(wires)

        grouped_wire_ids = set()
        for group in groups:
            grouped_wire_ids.update(group.wires)

        return {
            "groups": [g.to_dict() for g in groups],
            "total_wires": len(wires),
            "grouped_wires": len(grouped_wire_ids),
            "ungrouped_wires": len(wires) - len(grouped_wire_ids),
            "warnings": warnings,
            "errors": errors,
        }

    def _parse_wires(self, wires_data: list[dict[str, Any]]) -> list[WireData]:
        wires = []
        for data in wires_data:
            wire = WireData(
                wire_id=str(data.get("wire_id", data.get("WIRE_ID", ""))),
                name=str(data.get("name", data.get("NAME", ""))),
                node_a=str(data.get("node_a", data.get("NODE_A", ""))),
                node_b=str(data.get("node_b", data.get("NODE_B", ""))),
                color=str(data.get("color", data.get("COLOR", ""))),
                cable_type=str(data.get("cable_type", data.get("CABLE_TYPE", ""))),
                attributes=data.get("attributes", {}),
            )
            wires.append(wire)
        return wires

    def _validate_wires(self, wires: list[WireData]) -> dict[str, list[str]]:
        warnings = []
        errors = []

        wire_id_counts: dict[str, int] = defaultdict(int)
        for wire in wires:
            if wire.wire_id:
                wire_id_counts[wire.wire_id] += 1

        duplicate_ids = [wid for wid, count in wire_id_counts.items() if count > 1]
        if duplicate_ids:
            warnings.append(f"发现重复的 WIRE_ID: {', '.join(duplicate_ids)}")

        required_fields = ["wire_id", "name", "node_a", "node_b", "color", "cable_type"]
        for i, wire in enumerate(wires):
            missing = []
            for field in required_fields:
                value = getattr(wire, field, "")
                if not value:
                    missing.append(field.upper())

            if missing:
                errors.append(f"导线 #{i+1} 缺失必填字段: {', '.join(missing)}")

        return {"warnings": warnings, "errors": errors}

    def _group_wires(self, wires: list[WireData]) -> list[ParallelGroup]:
        if not wires:
            return []

        groups: list[list[WireData]] = []
        assigned = set()

        for i, wire1 in enumerate(wires):
            if wire1.wire_id in assigned:
                continue

            group = [wire1]
            assigned.add(wire1.wire_id)

            for j, wire2 in enumerate(wires[i + 1 :], start=i + 1):
                if wire2.wire_id in assigned:
                    continue

                should_merge, reason = self.rule_engine.should_merge(wire1, wire2)
                if should_merge:
                    group.append(wire2)
                    assigned.add(wire2.wire_id)

            if len(group) >= 2:
                groups.append(group)

        results: list[ParallelGroup] = []
        for idx, group in enumerate(groups, start=1):
            result = self._create_group(idx, group)
            results.append(result)

        return results

    def _create_group(self, group_num: int, wires: list[WireData]) -> ParallelGroup:
        wire_ids = [w.wire_id for w in wires]
        names = list(set(w.name for w in wires))
        colors = list(set(w.color for w in wires))
        cable_types = list(set(w.cable_type for w in wires))

        notes = []
        if len(names) == 1:
            notes.append(f"名称一致: {names[0]}")
        else:
            notes.append(f"名称不一致: {', '.join(names)}")

        if len(colors) == 1:
            notes.append(f"颜色一致: {colors[0]}")
        else:
            notes.append(f"颜色不一致: {', '.join(colors)}")

        if len(cable_types) == 1:
            notes.append(f"电缆类型一致: {cable_types[0]}")
        else:
            notes.append(f"电缆类型不一致: {', '.join(cable_types)}")

        return ParallelGroup(
            group_id=f"GROUP{group_num:03d}",
            wires=wire_ids,
            name=names[0] if len(names) == 1 else f"混合({len(names)}种)",
            color=colors[0] if len(colors) == 1 else f"混合({len(colors)}种)",
            cable_type=cable_types[0] if len(cable_types) == 1 else f"混合({len(cable_types)}种)",
            notes=notes,
        )


def analyze_wire_data(
    wires_data: list[dict[str, Any]],
    rules_file: str | Path | None = None,
) -> dict[str, Any]:
    analyzer = WireDataAnalyzer(rules_file)
    return analyzer.analyze(wires_data)


def analyze_wire_data_json(
    wires_json: str,
    rules_file: str | Path | None = None,
) -> str:
    wires_data = json.loads(wires_json)
    result = analyze_wire_data(wires_data, rules_file)
    return json.dumps(result, ensure_ascii=False, indent=2)
