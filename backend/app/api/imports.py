from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Component, ImportRecord, OperationLog, Project, User, Wire
from app.schemas import ImportRecordOut, ImportResult
from app.services.importer import parse_csv_payload, parse_xml_payload

router = APIRouter(prefix="/imports", tags=["数据导入"])


@router.post("/eplan", response_model=ImportResult)
async def import_eplan_file(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    extension = Path(file.filename or "").suffix.lower()
    content = await file.read()
    if extension == ".csv":
        parsed = parse_csv_payload(content)
        file_format = "CSV"
    elif extension == ".xml":
        parsed = parse_xml_payload(content)
        file_format = "XML"
    else:
        raise HTTPException(status_code=400, detail="仅支持 CSV 或 XML 文件")

    for component_data in parsed.components:
        db.add(Component(project_id=project_id, **component_data))

    for wire_data in parsed.wires:
        db.add(Wire(project_id=project_id, **wire_data))

    import_record = ImportRecord(
        project_id=project_id,
        filename=file.filename or "未命名文件",
        file_format=file_format,
        row_count=len(parsed.components) + len(parsed.wires),
        status="成功",
    )
    db.add(import_record)
    db.flush()

    db.add(
        OperationLog(
            user_id=current_user.id,
            action="导入数据",
            target=f"项目:{project.name}",
            detail=f"文件 {file.filename}，导入 {len(parsed.wires)} 条导线",
        )
    )
    db.commit()

    return ImportResult(
        imported_components=len(parsed.components),
        imported_wires=len(parsed.wires),
        import_record_id=import_record.id,
    )


@router.get("/records", response_model=list[ImportRecordOut])
def import_records(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    records = (
        db.query(ImportRecord)
        .filter(ImportRecord.project_id == project_id)
        .order_by(ImportRecord.created_at.desc())
        .all()
    )
    return records
