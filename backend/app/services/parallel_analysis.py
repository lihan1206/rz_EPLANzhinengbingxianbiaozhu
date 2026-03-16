from collections import defaultdict
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import GroupWire, ParallelGroup, Wire


def _normalize_path(start_terminal: str, end_terminal: str) -> tuple[str, str]:
    if start_terminal <= end_terminal:
        return start_terminal, end_terminal
    return end_terminal, start_terminal


def _resolve_parallel_type(wires: list[Wire]) -> str:
    if all(w.is_shielded for w in wires):
        return "屏蔽并线"
    areas = {float(w.area) for w in wires}
    colors = {w.color for w in wires}
    if len(areas) == 1 and len(colors) == 1:
        return "等电位并线"
    return "并联冗余线"


def _build_suggestion(count: int, total_area: Decimal) -> str:
    return f"建议评估是否可合并为 1x{float(total_area):.2f}mm²，当前并线数量 {count}"


def analyze_project_parallel_groups(db: Session, project_id: int, min_parallel_count: int = 2) -> int:
    db.query(GroupWire).filter(
        GroupWire.group_id.in_(
            db.query(ParallelGroup.id).filter(ParallelGroup.project_id == project_id)
        )
    ).delete(synchronize_session=False)
    db.query(ParallelGroup).filter(ParallelGroup.project_id == project_id).delete()
    db.flush()

    wires = db.query(Wire).filter(Wire.project_id == project_id).all()
    buckets: dict[tuple[str, str, str, str], list[Wire]] = defaultdict(list)

    for wire in wires:
        start, end = _normalize_path(wire.start_terminal, wire.end_terminal)
        key = (start, end, str(wire.area), wire.color)
        buckets[key].append(wire)

    groups_created = 0
    for _, bucket_wires in buckets.items():
        if len(bucket_wires) < min_parallel_count:
            continue

        start, end = _normalize_path(bucket_wires[0].start_terminal, bucket_wires[0].end_terminal)
        total_area = sum((Decimal(str(w.area)) for w in bucket_wires), Decimal("0"))
        parallel_type = _resolve_parallel_type(bucket_wires)
        group = ParallelGroup(
            project_id=project_id,
            group_name=f"并线组-{start}-{end}-{groups_created + 1}",
            count=len(bucket_wires),
            total_area=total_area,
            start_terminal=start,
            end_terminal=end,
            parallel_type=parallel_type,
            suggestion=_build_suggestion(len(bucket_wires), total_area),
        )
        db.add(group)
        db.flush()

        for wire in bucket_wires:
            db.add(GroupWire(group_id=group.id, wire_id=wire.id))

        groups_created += 1

    db.commit()
    return groups_created


def render_annotation_text(template: str, count: int, total_area: Decimal) -> str:
    text = template
    text = text.replace("{{count}}", str(count))
    text = text.replace("{{area}}", f"{float(total_area):.2f}")
    return text
