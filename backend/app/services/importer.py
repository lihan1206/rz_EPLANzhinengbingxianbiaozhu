import csv
import io
from collections import Counter
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET


@dataclass
class ParsedImportData:
    components: list[dict]
    wires: list[dict]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duplicate_wire_ids: list[str] = field(default_factory=list)


def _clean_text(value: str | None, default: str = "") -> str:
    if value is None:
        return default
    return value.strip() or default


def _to_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float((value or "").strip())
    except ValueError:
        return default


def parse_csv_payload(content: bytes) -> ParsedImportData:
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    components: list[dict] = []
    wires: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []

    fieldnames = reader.fieldnames or []
    required_wire_fields = ["wire_id", "WIRE_ID", "name", "NAME", "node_a", "NODE_A", "node_b", "NODE_B", "color", "COLOR", "cable_type", "CABLE_TYPE"]
    has_new_fields = any(f in fieldnames for f in ["wire_id", "WIRE_ID", "name", "NAME", "node_a", "NODE_A", "node_b", "NODE_B", "cable_type", "CABLE_TYPE"])

    wire_ids: list[str] = []

    for row_num, row in enumerate(reader, start=2):
        record_type = _clean_text(row.get("record_type") or row.get("类型") or "wire").lower()
        if record_type in {"component", "元件"}:
            components.append(
                {
                    "name": _clean_text(row.get("name") or row.get("元件名称"), "未命名元件"),
                    "type": _clean_text(row.get("type") or row.get("元件类型"), "普通元件"),
                    "terminal": _clean_text(row.get("terminal") or row.get("端子"), "X1"),
                    "description": _clean_text(row.get("description") or row.get("描述"), ""),
                }
            )
            continue

        wire_data = {
            "number": _clean_text(row.get("number") or row.get("导线编号"), "W-未编号"),
            "area": _to_float(row.get("area") or row.get("截面积"), 0.5),
            "color": _clean_text(row.get("color") or row.get("颜色") or row.get("COLOR"), "黑"),
            "material": _clean_text(row.get("material") or row.get("材质"), "铜"),
            "length": _to_float(row.get("length") or row.get("长度"), 0.0),
            "start_terminal": _clean_text(row.get("start_terminal") or row.get("起点端子") or row.get("NODE_A") or row.get("node_a"), "A1"),
            "end_terminal": _clean_text(row.get("end_terminal") or row.get("终点端子") or row.get("NODE_B") or row.get("node_b"), "B1"),
            "is_shielded": _clean_text(row.get("is_shielded") or row.get("屏蔽"), "否") in {"1", "true", "是"},
        }

        if has_new_fields:
            wire_id = _clean_text(row.get("wire_id") or row.get("WIRE_ID"), "")
            name = _clean_text(row.get("name") or row.get("NAME"), "")
            node_a = _clean_text(row.get("node_a") or row.get("NODE_A"), wire_data["start_terminal"])
            node_b = _clean_text(row.get("node_b") or row.get("NODE_B"), wire_data["end_terminal"])
            cable_type = _clean_text(row.get("cable_type") or row.get("CABLE_TYPE"), "")

            wire_data["wire_id"] = wire_id
            wire_data["name"] = name
            wire_data["node_a"] = node_a
            wire_data["node_b"] = node_b
            wire_data["cable_type"] = cable_type

            if wire_id:
                wire_ids.append(wire_id)

            missing_fields = []
            if not wire_id:
                missing_fields.append("WIRE_ID")
            if not name:
                missing_fields.append("NAME")
            if not cable_type:
                missing_fields.append("CABLE_TYPE")

            if missing_fields:
                errors.append(f"第 {row_num} 行: 缺失必填字段 {', '.join(missing_fields)}")

        wires.append(wire_data)

    duplicate_wire_ids = []
    if wire_ids:
        id_counts = Counter(wire_ids)
        duplicate_wire_ids = [wid for wid, count in id_counts.items() if count > 1]
        if duplicate_wire_ids:
            warnings.append(f"发现重复的 WIRE_ID: {', '.join(duplicate_wire_ids)}")

    return ParsedImportData(
        components=components,
        wires=wires,
        errors=errors,
        warnings=warnings,
        duplicate_wire_ids=duplicate_wire_ids,
    )


def parse_xml_payload(content: bytes) -> ParsedImportData:
    root = ET.fromstring(content)

    components: list[dict] = []
    wires: list[dict] = []

    for comp in root.findall(".//component"):
        components.append(
            {
                "name": _clean_text(comp.findtext("name"), "未命名元件"),
                "type": _clean_text(comp.findtext("type"), "普通元件"),
                "terminal": _clean_text(comp.findtext("terminal"), "X1"),
                "description": _clean_text(comp.findtext("description"), ""),
            }
        )

    for wire in root.findall(".//wire"):
        wires.append(
            {
                "number": _clean_text(wire.findtext("number"), "W-未编号"),
                "area": _to_float(wire.findtext("area"), 0.5),
                "color": _clean_text(wire.findtext("color"), "黑"),
                "material": _clean_text(wire.findtext("material"), "铜"),
                "length": _to_float(wire.findtext("length"), 0.0),
                "start_terminal": _clean_text(wire.findtext("start_terminal"), "A1"),
                "end_terminal": _clean_text(wire.findtext("end_terminal"), "B1"),
                "is_shielded": _clean_text(wire.findtext("is_shielded"), "否") in {"1", "true", "是"},
            }
        )

    return ParsedImportData(components=components, wires=wires)
