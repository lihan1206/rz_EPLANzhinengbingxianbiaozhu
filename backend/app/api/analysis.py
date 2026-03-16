from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import OperationLog, ParallelGroup, Project, User
from app.schemas import AnalyzeRequest, AnalyzeResult, ParallelGroupOut
from app.services.parallel_analysis import analyze_project_parallel_groups

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
