import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import ParallelGroup, User

router = APIRouter(prefix="/exports", tags=["数据导出"])


@router.get("/groups/{project_id}")
def export_groups_csv(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    groups = db.query(ParallelGroup).filter(ParallelGroup.project_id == project_id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["组名", "并线数量", "总截面积", "起点端子", "终点端子", "并线类型", "建议"])

    for group in groups:
        writer.writerow(
            [
                group.group_name,
                group.count,
                float(group.total_area),
                group.start_terminal,
                group.end_terminal,
                group.parallel_type,
                group.suggestion,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=parallel_groups_{project_id}.csv"},
    )
