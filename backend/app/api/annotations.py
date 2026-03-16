from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Annotation, OperationLog, ParallelGroup, User
from app.schemas import AnnotationOut, AnnotationRequest
from app.services.parallel_analysis import render_annotation_text

router = APIRouter(prefix="/annotations", tags=["自动标注"])


@router.post("/generate/{project_id}", response_model=list[AnnotationOut])
def generate_annotations(
    project_id: int,
    payload: AnnotationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Annotation).filter(
        Annotation.group_id.in_(
            db.query(ParallelGroup.id).filter(ParallelGroup.project_id == project_id)
        )
    ).delete(synchronize_session=False)

    groups = db.query(ParallelGroup).filter(ParallelGroup.project_id == project_id).all()
    created: list[Annotation] = []

    for idx, group in enumerate(groups, start=1):
        text = render_annotation_text(payload.template, group.count, group.total_area)
        annotation = Annotation(
            group_id=group.id,
            text=text,
            style=payload.style,
            position_x=80 + idx * 20,
            position_y=120 + idx * 12,
        )
        db.add(annotation)
        created.append(annotation)

    db.add(
        OperationLog(
            user_id=current_user.id,
            action="生成标注",
            target=f"项目ID:{project_id}",
            detail=f"生成标注 {len(created)} 条，模板 {payload.template}",
        )
    )
    db.commit()

    for item in created:
        db.refresh(item)
    return created


@router.get("/{project_id}", response_model=list[AnnotationOut])
def list_annotations(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        db.query(Annotation)
        .join(ParallelGroup, ParallelGroup.id == Annotation.group_id)
        .filter(ParallelGroup.project_id == project_id)
        .order_by(Annotation.created_at.desc())
        .all()
    )
