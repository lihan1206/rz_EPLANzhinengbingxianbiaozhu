from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models import OperationLog, User
from app.schemas import OperationLogOut

router = APIRouter(prefix="/logs", tags=["操作日志"])


@router.get("", response_model=list[OperationLogOut])
def list_logs(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(OperationLog).order_by(OperationLog.created_at.desc()).limit(200).all()
