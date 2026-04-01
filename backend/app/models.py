from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    operation_logs: Mapped[list["OperationLog"]] = relationship(back_populates="user")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_project_name_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    components: Mapped[list["Component"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    wires: Mapped[list["Wire"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    parallel_groups: Mapped[list["ParallelGroup"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    import_records: Mapped[list["ImportRecord"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Component(Base):
    __tablename__ = "components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    terminal: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    project: Mapped["Project"] = relationship(back_populates="components")


class Wire(Base):
    __tablename__ = "wires"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    wire_id: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    node_a: Mapped[str] = mapped_column(String(50), nullable=True)
    node_b: Mapped[str] = mapped_column(String(50), nullable=True)
    cable_type: Mapped[str] = mapped_column(String(50), nullable=True)
    number: Mapped[str] = mapped_column(String(30), nullable=False)
    area: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    material: Mapped[str] = mapped_column(String(20), nullable=False, default="铜")
    length: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    start_terminal: Mapped[str] = mapped_column(String(50), nullable=False)
    end_terminal: Mapped[str] = mapped_column(String(50), nullable=False)
    is_shielded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="wires")
    group_links: Mapped[list["GroupWire"]] = relationship(back_populates="wire", cascade="all, delete-orphan")


class ParallelGroup(Base):
    __tablename__ = "parallel_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    group_name: Mapped[str] = mapped_column(String(60), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_area: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    start_terminal: Mapped[str] = mapped_column(String(50), nullable=False)
    end_terminal: Mapped[str] = mapped_column(String(50), nullable=False)
    parallel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    suggestion: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="parallel_groups")
    annotations: Mapped[list["Annotation"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    wire_links: Mapped[list["GroupWire"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class GroupWire(Base):
    __tablename__ = "group_wires"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("parallel_groups.id", ondelete="CASCADE"), index=True)
    wire_id: Mapped[int] = mapped_column(ForeignKey("wires.id", ondelete="CASCADE"), index=True)

    group: Mapped["ParallelGroup"] = relationship(back_populates="wire_links")
    wire: Mapped["Wire"] = relationship(back_populates="group_links")


class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("parallel_groups.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(120), nullable=False)
    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    position_y: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    style: Mapped[str] = mapped_column(String(40), nullable=False, default="标准")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    group: Mapped["ParallelGroup"] = relationship(back_populates="annotations")


class ImportRecord(Base):
    __tablename__ = "import_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(120), nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="成功")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="import_records")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    target: Mapped[str] = mapped_column(String(120), nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="operation_logs")
