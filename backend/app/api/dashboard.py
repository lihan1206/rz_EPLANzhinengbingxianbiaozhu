from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Annotation, ParallelGroup, Project, User, Wire
from app.schemas import DashboardSummary, DistributionItem

router = APIRouter(prefix="/dashboard", tags=["可视化"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return DashboardSummary(
        project_count=db.query(func.count(Project.id)).scalar() or 0,
        wire_count=db.query(func.count(Wire.id)).scalar() or 0,
        parallel_group_count=db.query(func.count(ParallelGroup.id)).scalar() or 0,
        annotation_count=db.query(func.count(Annotation.id)).scalar() or 0,
    )


@router.get("/distribution/{project_id}", response_model=list[DistributionItem])
def distribution(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    groups = db.query(ParallelGroup).filter(ParallelGroup.project_id == project_id).all()
    counter = Counter(g.parallel_type for g in groups)
    return [DistributionItem(name=name, value=value) for name, value in counter.items()]
