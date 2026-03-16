from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=50)


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    version: str = Field(min_length=1, max_length=20)


class ProjectOut(BaseModel):
    id: int
    name: str
    version: str
    created_at: datetime

    class Config:
        from_attributes = True


class ComponentCreate(BaseModel):
    name: str
    type: str
    terminal: str
    description: str = ""


class WireCreate(BaseModel):
    number: str
    area: float = Field(gt=0)
    color: str
    material: str = "铜"
    length: float = Field(ge=0)
    start_terminal: str
    end_terminal: str
    is_shielded: bool = False


class ImportResult(BaseModel):
    imported_components: int
    imported_wires: int
    import_record_id: int


class ParallelGroupOut(BaseModel):
    id: int
    project_id: int
    group_name: str
    count: int
    total_area: Decimal
    start_terminal: str
    end_terminal: str
    parallel_type: str
    suggestion: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    min_parallel_count: int = Field(default=2, ge=2, le=10)


class AnalyzeResult(BaseModel):
    groups_created: int


class AnnotationRequest(BaseModel):
    template: str = Field(default="{{count}}x{{area}}mm²", max_length=80)
    style: str = Field(default="标准", max_length=40)


class AnnotationOut(BaseModel):
    id: int
    group_id: int
    text: str
    position_x: float
    position_y: float
    style: str
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    project_count: int
    wire_count: int
    parallel_group_count: int
    annotation_count: int


class DistributionItem(BaseModel):
    name: str
    value: int


class ImportRecordOut(BaseModel):
    id: int
    project_id: int
    filename: str
    file_format: str
    row_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OperationLogOut(BaseModel):
    id: int
    user_id: int | None
    action: str
    target: str
    detail: str
    created_at: datetime

    class Config:
        from_attributes = True
