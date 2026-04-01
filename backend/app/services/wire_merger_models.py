"""
并线合并功能的数据库模型扩展
"""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WireMergeProject(Base):
    """并线合并项目"""
    __tablename__ = "wire_merge_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    source_wires: Mapped[list["SourceWire"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    merge_groups: Mapped[list["MergeGroup"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    import_logs: Mapped[list["WireImportLog"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class SourceWire(Base):
    """原始导线数据"""
    __tablename__ = "source_wires"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("wire_merge_projects.id", ondelete="CASCADE"), index=True)
    wire_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    node_a: Mapped[str] = mapped_column(String(100), nullable=False)
    node_b: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(50), nullable=False)
    cable_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # 扩展字段存储
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关联
    project: Mapped["WireMergeProject"] = relationship(back_populates="source_wires")
    group_links: Mapped[list["MergeGroupWire"]] = relationship(back_populates="wire", cascade="all, delete-orphan")


class MergeGroup(Base):
    """合并后的并线组"""
    __tablename__ = "merge_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("wire_merge_projects.id", ondelete="CASCADE"), index=True)
    group_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(50), nullable=False)
    cable_type: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    wire_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关联
    project: Mapped["WireMergeProject"] = relationship(back_populates="merge_groups")
    wire_links: Mapped[list["MergeGroupWire"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class MergeGroupWire(Base):
    """并线组与导线的关联表"""
    __tablename__ = "merge_group_wires"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("merge_groups.id", ondelete="CASCADE"), index=True)
    wire_id: Mapped[int] = mapped_column(ForeignKey("source_wires.id", ondelete="CASCADE"), index=True)

    # 关联
    group: Mapped["MergeGroup"] = relationship(back_populates="wire_links")
    wire: Mapped["SourceWire"] = relationship(back_populates="group_links")


class WireImportLog(Base):
    """导线导入日志"""
    __tablename__ = "wire_import_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("wire_merge_projects.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关联
    project: Mapped["WireMergeProject"] = relationship(back_populates="import_logs")


class MergeRuleConfig(Base):
    """合并规则配置"""
    __tablename__ = "merge_rule_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    # 匹配字段列表
    match_fields: Mapped[list] = mapped_column(JSON, default=list)
    # 自动合并规则
    auto_merge_rules: Mapped[list] = mapped_column(JSON, default=list)
    # 其他配置
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
