import csv
import io
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


class WireMerger:
    def __init__(self, rules_path: str | None = None):
        if rules_path is None:
            rules_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "core", "merge_rules.json"
            )
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, rules_path: str) -> dict:
        with open(rules_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _check_condition(self, wire: dict, condition: dict) -> bool:
        field = condition["field"]
        operator = condition["operator"]
        value = condition["value"]
        wire_value = str(wire.get(field, ""))

        if operator == "equals":
            return wire_value == value
        elif operator == "contains":
            return value in wire_value
        elif operator == "starts_with":
            return wire_value.startswith(value)
        elif operator == "ends_with":
            return wire_value.endswith(value)
        return False

    def _get_group_key(self, wire: dict, group_by: list[str]) -> tuple:
        key_parts = []
        for field in group_by:
            key_parts.append(str(wire.get(field, "")))
        return tuple(key_parts)

    def merge_wires(
        self, wires: list[dict]
    ) -> dict[str, Any]:
        required_fields = self.rules["required_fields"]
        errors = []
        warnings = []

        for i, wire in enumerate(wires):
            missing_fields = [f for f in required_fields if f not in wire]
            if missing_fields:
                errors.append(f"第 {i+1} 条导线缺少字段: {', '.join(missing_fields)}")

        if errors:
            return {
                "success": False,
                "errors": errors,
                "warnings": warnings,
                "groups": []
            }

        wire_ids = [wire["WIRE_ID"] for wire in wires]
        if len(wire_ids) != len(set(wire_ids)):
            seen = set()
            duplicates = []
            for wid in wire_ids:
                if wid in seen:
                    duplicates.append(wid)
                seen.add(wid)
            warnings.append(f"存在重复的 WIRE_ID: {', '.join(duplicates)}")

        custom_rules = sorted(
            self.rules["custom_rules"],
            key=lambda x: x.get("priority", 0),
            reverse=True
        )

        default_group_by = self.rules["default_rules"]["group_by"]

        custom_groups = defaultdict(list)
        remaining_wires = []

        for wire in wires:
            matched = False
            for rule in custom_rules:
                if self._check_condition(wire, rule["condition"]):
                    key = self._get_group_key(wire, rule["group_by"])
                    custom_groups[(rule["name"], key)].append(wire)
                    matched = True
                    break
            if not matched:
                remaining_wires.append(wire)

        default_groups = defaultdict(list)
        for wire in remaining_wires:
            key = self._get_group_key(wire, default_group_by)
            default_groups[key].append(wire)

        groups = []
        group_counter = 1

        for (rule_name, key), wire_list in custom_groups.items():
            rule = next(r for r in custom_rules if r["name"] == rule_name)
            first_wire = wire_list[0]
            groups.append({
                "group_id": f"G{group_counter:04d}",
                "wires": [w["WIRE_ID"] for w in wire_list],
                "name": first_wire["NAME"],
                "color": first_wire["COLOR"],
                "cable_type": first_wire["CABLE_TYPE"],
                "notes": f"应用自定义规则: {rule['description']}"
            })
            group_counter += 1

        for key, wire_list in default_groups.items():
            first_wire = wire_list[0]
            name = first_wire["NAME"]
            color = first_wire["COLOR"]
            cable_type = first_wire["CABLE_TYPE"]

            all_same_color = all(w["COLOR"] == color for w in wire_list)
            all_same_type = all(w["CABLE_TYPE"] == cable_type for w in wire_list)

            notes = "成功合并：NAME、COLOR、CABLE_TYPE 均相同"
            if not all_same_color:
                notes = "未合并，颜色不同"
            if not all_same_type:
                notes = "未合并，电缆类型不同"

            groups.append({
                "group_id": f"G{group_counter:04d}",
                "wires": [w["WIRE_ID"] for w in wire_list],
                "name": name,
                "color": color,
                "cable_type": cable_type,
                "notes": notes
            })
            group_counter += 1

        return {
            "success": True,
            "errors": errors,
            "warnings": warnings,
            "groups": groups,
            "total_wires": len(wires),
            "total_groups": len(groups)
        }

    def merge_from_csv(self, csv_content: bytes) -> dict[str, Any]:
        try:
            decoded = csv_content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(decoded))
            wires = list(reader)
            return self.merge_wires(wires)
        except Exception as e:
            return {
                "success": False,
                "errors": [f"CSV 解析错误: {str(e)}"],
                "warnings": [],
                "groups": []
            }
