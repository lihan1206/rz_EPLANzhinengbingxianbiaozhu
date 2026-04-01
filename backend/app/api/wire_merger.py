from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas import MergeRequest, MergeResult
from app.services.wire_merger import WireMerger

router = APIRouter(prefix="/wire-merger", tags=["并线合并"])


@router.post("/merge", response_model=MergeResult)
def merge_wires(request: MergeRequest):
    """
    合并导线数据
    """
    merger = WireMerger()
    wires = [wire.model_dump() for wire in request.wires]
    result = merger.merge_wires(wires)
    return MergeResult(**result)


@router.post("/merge-csv", response_model=MergeResult)
async def merge_wires_from_csv(file: UploadFile = File(...)):
    """
    从 CSV 文件导入并合并导线数据
    """
    content = await file.read()
    merger = WireMerger()
    result = merger.merge_from_csv(content)
    return MergeResult(**result)


@router.post("/merge-to-db")
def merge_wires_to_db(
    request: MergeRequest,
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    合并导线并写入数据库
    """
    from app.models import Wire as DBWire, ParallelGroup, GroupWire

    merger = WireMerger()
    wires = [wire.model_dump() for wire in request.wires]
    result = merger.merge_wires(wires)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])

    for group in result["groups"]:
        db_group = ParallelGroup(
            project_id=project_id,
            group_name=group["group_id"],
            count=len(group["wires"]),
            total_area=0,
            start_terminal="",
            end_terminal="",
            parallel_type="自定义并线",
            suggestion=group["notes"],
        )
        db.add(db_group)
        db.flush()

        for wire_id in group["wires"]:
            db_link = GroupWire(
                group_id=db_group.id,
                wire_id=0,
            )
            db.add(db_link)

    db.commit()
    return result
