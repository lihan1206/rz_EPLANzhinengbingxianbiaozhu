from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import OperationLog, ParallelGroup, Project, User
from app.schemas import AnalyzeRequest, AnalyzeResult, ParallelGroupOut, WireAnalyzeRequest, WireAnalyzeResult
from app.services.parallel_analysis import analyze_project_parallel_groups
from app.services.wire_parallel_analyzer import AnalysisConfig, analyze_wires

router = APIRouter(prefix="/analysis", tags=["并线分析"])


@router.post("/{project_id}", response_model=AnalyzeResult)
def analyze_parallel(
    project_id: int,
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    groups_created = analyze_project_parallel_groups(db, project_id, payload.min_parallel_count)
    db.add(
        OperationLog(
            user_id=current_user.id,
            action="并线分析",
            target=f"项目:{project.name}",
            detail=f"规则: 并线数 >= {payload.min_parallel_count}，生成 {groups_created} 组",
        )
    )
    db.commit()
    return AnalyzeResult(groups_created=groups_created)


@router.get("/{project_id}/groups", response_model=list[ParallelGroupOut])
def list_groups(project_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return (
        db.query(ParallelGroup)
        .filter(ParallelGroup.project_id == project_id)
        .order_by(ParallelGroup.created_at.desc())
        .all()
    )


@router.post("/wires/analyze", response_model=WireAnalyzeResult)
def analyze_wires_direct(
    payload: WireAnalyzeRequest,
    _: User = Depends(get_current_user),
):
    config = None
    if payload.config:
        config = AnalysisConfig(
            min_parallel_count=payload.config.min_parallel_count,
            max_parallel_count=payload.config.max_parallel_count,
            check_voltage_compatibility=payload.config.check_voltage_compatibility,
            check_shield_consistency=payload.config.check_shield_consistency,
        )

    wires_data = []
    for wire in payload.wires:
        wire_dict = {
            "id": wire.id,
            "start_terminal": wire.start_terminal,
            "end_terminal": wire.end_terminal,
            "area": wire.area,
            "color": wire.color,
            "attributes": wire.attributes or {},
        }
        wires_data.append(wire_dict)

    groups = analyze_wires(wires_data, config)

    grouped_wire_ids = set()
    for group in groups:
        grouped_wire_ids.update(group.get("wire_ids", []))

    return WireAnalyzeResult(
        parallel_groups=groups,
        total_wires=len(payload.wires),
        grouped_wires=len(grouped_wire_ids),
        ungrouped_wires=len(payload.wires) - len(grouped_wire_ids),
    )
