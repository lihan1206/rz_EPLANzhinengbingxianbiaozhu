import csv
import io
from dataclasses import dataclass
from xml.etree import ElementTree as ET


@dataclass
class ParsedImportData:
    components: list[dict]
    wires: list[dict]


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

    for row in reader:
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

        wires.append(
            {
                "number": _clean_text(row.get("number") or row.get("导线编号"), "W-未编号"),
                "area": _to_float(row.get("area") or row.get("截面积"), 0.5),
                "color": _clean_text(row.get("color") or row.get("颜色"), "黑"),
                "material": _clean_text(row.get("material") or row.get("材质"), "铜"),
                "length": _to_float(row.get("length") or row.get("长度"), 0.0),
                "start_terminal": _clean_text(row.get("start_terminal") or row.get("起点端子"), "A1"),
                "end_terminal": _clean_text(row.get("end_terminal") or row.get("终点端子"), "B1"),
                "is_shielded": _clean_text(row.get("is_shielded") or row.get("屏蔽"), "否") in {"1", "true", "是"},
            }
        )

    return ParsedImportData(components=components, wires=wires)


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
