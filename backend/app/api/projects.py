from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import OperationLog, Project, User
from app.schemas import ProjectCreate, ProjectOut

router = APIRouter(prefix="/projects", tags=["项目"])


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exists = (
        db.query(Project)
        .filter(Project.name == payload.name, Project.version == payload.version)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="同名版本项目已存在")

    project = Project(name=payload.name, version=payload.version)
    db.add(project)
    db.flush()
    db.add(
        OperationLog(
            user_id=current_user.id,
            action="创建项目",
            target=f"项目:{project.name}",
            detail=f"版本 {project.version}",
        )
    )
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    project_name = project.name
    db.delete(project)
    db.add(
        OperationLog(
            user_id=current_user.id,
            action="删除项目",
            target=f"项目:{project_name}",
            detail="项目及关联数据已删除",
        )
    )
    db.commit()
    return {"message": "项目删除成功"}
