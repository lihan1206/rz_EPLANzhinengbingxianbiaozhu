"""
并线合并功能API接口
"""

import os
import tempfile
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import json

from app.core.deps import get_db, get_current_user
from app.models import User
from app.services.wire_merger import WireMerger, WireMergerConfig, merge_wires_from_list
from app.services.wire_merger_db import WireMergerRepository
from app.services.wire_merger_schemas import (
    WireMergeRequest,
    WireMergeResult,
    WireImportResult,
    MergeRuleConfigCreate,
    MergeRuleConfigUpdate,
    MergeRuleConfigOut,
    WireMergeProjectOut,
    WireMergeProjectDetail,
    WireStatistics,
    MergeGroupDetail,
    WireInfo,
)

router = APIRouter(prefix="/wire-merger", tags=["wire-merger"])


def get_repo(db: Session = Depends(get_db)) -> WireMergerRepository:
    """获取数据仓库"""
    return WireMergerRepository(db)


# ========== 项目管理接口 ==========

@router.post("/projects", response_model=WireMergeProjectOut)
def create_project(
    name: str = Form(..., description="项目名称"),
    description: str = Form("", description="项目描述"),
    config: Optional[str] = Form(None, description="配置JSON字符串"),
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """创建并线合并项目"""
    config_dict = {}
    if config:
        try:
            config_dict = json.loads(config)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="配置JSON格式错误")
    
    project = repo.create_project(name=name, description=description, config=config_dict)
    return project


@router.get("/projects", response_model=list[WireMergeProjectOut])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表"""
    return repo.get_projects(skip=skip, limit=limit)


@router.get("/projects/{project_id}", response_model=WireMergeProjectDetail)
def get_project_detail(
    project_id: int,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情（包含统计和合并组）"""
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取统计信息
    stats = repo.get_wire_statistics(project_id)
    
    # 获取合并组
    db_groups = repo.get_merge_groups(project_id)
    groups = []
    for g in db_groups:
        wires = []
        for link in g.wire_links:
            w = link.wire
            wires.append(WireInfo(
                wire_id=w.wire_id,
                name=w.name,
                node_a=w.node_a,
                node_b=w.node_b,
                color=w.color,
                cable_type=w.cable_type
            ))
        
        groups.append(MergeGroupDetail(
            group_id=g.group_id,
            name=g.name,
            color=g.color,
            cable_type=g.cable_type,
            notes=g.notes,
            wire_count=g.wire_count,
            wires=wires,
            created_at=g.created_at
        ))
    
    return WireMergeProjectDetail(
        id=project.id,
        name=project.name,
        description=project.description,
        config=project.config,
        statistics=WireStatistics(**stats),
        groups=groups,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """删除项目"""
    if not repo.delete_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    return {"message": "项目已删除"}


# ========== 数据导入与合并接口 ==========

@router.post("/merge", response_model=WireMergeResult)
def merge_wires(
    request: WireMergeRequest,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """
    执行导线并线合并
    
    请求体包含导线数据列表，系统根据规则识别并线组
    """
    # 获取规则配置
    config = None
    if request.config_id:
        db_config = repo.get_rule_config(request.config_id)
        if db_config:
            config = WireMergerConfig()
            config.default_rules["match_fields"] = db_config.match_fields
            config.default_rules["case_sensitive"] = db_config.config.get("case_sensitive", False)
            config.default_rules["ignore_whitespace"] = db_config.config.get("ignore_whitespace", True)
            config.auto_merge_rules = db_config.auto_merge_rules
    
    # 创建项目
    project_name = request.project_name or f"合并项目_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    project = repo.create_project(name=project_name)
    
    # 执行合并
    merger = WireMerger(config)
    
    # 转换数据
    wire_dicts = [wire.model_dump() for wire in request.wires]
    load_result = merger.load_from_list(wire_dicts)
    
    if not load_result.success:
        return WireMergeResult(
            success=False,
            summary={"total_groups": 0, "total_wires": 0, "merged_groups": 0},
            groups=[],
            errors=load_result.errors,
            warnings=load_result.warnings
        )
    
    # 保存原始导线数据
    repo.import_wires(project.id, merger.wires)
    
    # 执行分析
    result = merger.analyze()
    
    # 保存合并结果
    if result.success:
        repo.save_merge_groups(project.id, result.groups)
    
    # 创建导入日志
    repo.create_import_log(project.id, "API直接导入", result, len(request.wires))
    
    # 构建响应
    from app.services.wire_merger_schemas import ParallelGroupOut, MergeSummary
    
    groups_out = []
    for g in result.groups:
        groups_out.append(ParallelGroupOut(
            group_id=g.group_id,
            wires=g.wires,
            name=g.name,
            color=g.color,
            cable_type=g.cable_type,
            notes=g.notes,
            wire_count=len(g.wires)
        ))
    
    summary = MergeSummary(
        total_groups=len(result.groups),
        total_wires=sum(len(g.wires) for g in result.groups),
        merged_groups=sum(1 for g in result.groups if len(g.wires) > 1)
    )
    
    return WireMergeResult(
        success=result.success,
        summary=summary,
        groups=groups_out,
        errors=result.errors,
        warnings=result.warnings
    )


@router.post("/merge-from-csv", response_model=WireMergeResult)
async def merge_wires_from_csv(
    file: UploadFile = File(..., description="CSV文件"),
    project_name: Optional[str] = Form(None, description="项目名称"),
    config_id: Optional[int] = Form(None, description="规则配置ID"),
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """
    从CSV文件导入并执行并线合并
    
    CSV文件必须包含以下字段：WIRE_ID, NAME, NODE_A, NODE_B, COLOR, CABLE_TYPE
    """
    # 验证文件类型
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")
    
    # 保存上传的文件
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取规则配置
        config = None
        if config_id:
            db_config = repo.get_rule_config(config_id)
            if db_config:
                config = WireMergerConfig()
                config.default_rules["match_fields"] = db_config.match_fields
                config.default_rules["case_sensitive"] = db_config.config.get("case_sensitive", False)
                config.default_rules["ignore_whitespace"] = db_config.config.get("ignore_whitespace", True)
                config.auto_merge_rules = db_config.auto_merge_rules
        
        # 创建项目
        name = project_name or file.filename.rsplit('.', 1)[0]
        project = repo.create_project(name=name)
        
        # 执行合并
        merger = WireMerger(config)
        load_result = merger.load_from_csv(temp_path)
        
        if not load_result.success:
            from app.services.wire_merger_schemas import MergeSummary
            return WireMergeResult(
                success=False,
                summary=MergeSummary(total_groups=0, total_wires=0, merged_groups=0),
                groups=[],
                errors=load_result.errors,
                warnings=load_result.warnings
            )
        
        # 保存原始导线数据
        repo.import_wires(project.id, merger.wires)
        
        # 执行分析
        result = merger.analyze()
        
        # 保存合并结果
        if result.success:
            repo.save_merge_groups(project.id, result.groups)
        
        # 创建导入日志
        repo.create_import_log(project.id, file.filename, result, len(merger.wires))
        
        # 构建响应
        from app.services.wire_merger_schemas import ParallelGroupOut, MergeSummary
        
        groups_out = []
        for g in result.groups:
            groups_out.append(ParallelGroupOut(
                group_id=g.group_id,
                wires=g.wires,
                name=g.name,
                color=g.color,
                cable_type=g.cable_type,
                notes=g.notes,
                wire_count=len(g.wires)
            ))
        
        summary = MergeSummary(
            total_groups=len(result.groups),
            total_wires=sum(len(g.wires) for g in result.groups),
            merged_groups=sum(1 for g in result.groups if len(g.wires) > 1)
        )
        
        return WireMergeResult(
            success=result.success,
            summary=summary,
            groups=groups_out,
            errors=result.errors,
            warnings=result.warnings
        )
        
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/projects/{project_id}/statistics", response_model=WireStatistics)
def get_project_statistics(
    project_id: int,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """获取项目统计信息"""
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    stats = repo.get_wire_statistics(project_id)
    return WireStatistics(**stats)


@router.get("/projects/{project_id}/groups", response_model=list[MergeGroupDetail])
def get_project_groups(
    project_id: int,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """获取项目的并线组"""
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_groups = repo.get_merge_groups(project_id)
    groups = []
    for g in db_groups:
        wires = []
        for link in g.wire_links:
            w = link.wire
            wires.append(WireInfo(
                wire_id=w.wire_id,
                name=w.name,
                node_a=w.node_a,
                node_b=w.node_b,
                color=w.color,
                cable_type=w.cable_type
            ))
        
        groups.append(MergeGroupDetail(
            group_id=g.group_id,
            name=g.name,
            color=g.color,
            cable_type=g.cable_type,
            notes=g.notes,
            wire_count=g.wire_count,
            wires=wires,
            created_at=g.created_at
        ))
    
    return groups


# ========== 规则配置接口 ==========

@router.post("/configs", response_model=MergeRuleConfigOut)
def create_rule_config(
    config: MergeRuleConfigCreate,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """创建合并规则配置"""
    # 检查名称是否已存在
    existing = repo.db.query(repo.db.query(MergeRuleConfig).filter_by(name=config.name).exists()).scalar()
    if existing:
        raise HTTPException(status_code=400, detail="配置名称已存在")
    
    rule_config = repo.create_rule_config(
        name=config.name,
        description=config.description,
        match_fields=config.match_fields,
        auto_merge_rules=[rule.model_dump() for rule in config.auto_merge_rules],
        config={
            "case_sensitive": config.case_sensitive,
            "ignore_whitespace": config.ignore_whitespace
        },
        is_default=config.is_default
    )
    return rule_config


@router.get("/configs", response_model=list[MergeRuleConfigOut])
def list_rule_configs(
    skip: int = 0,
    limit: int = 100,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """获取规则配置列表"""
    return repo.get_rule_configs(skip=skip, limit=limit)


@router.get("/configs/{config_id}", response_model=MergeRuleConfigOut)
def get_rule_config(
    config_id: int,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """获取规则配置详情"""
    config = repo.get_rule_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.put("/configs/{config_id}", response_model=MergeRuleConfigOut)
def update_rule_config(
    config_id: int,
    config_update: MergeRuleConfigUpdate,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """更新规则配置"""
    update_data = config_update.model_dump(exclude_unset=True)
    
    # 转换auto_merge_rules
    if "auto_merge_rules" in update_data and update_data["auto_merge_rules"]:
        update_data["auto_merge_rules"] = [rule.model_dump() for rule in update_data["auto_merge_rules"]]
    
    # 处理config字段
    if "case_sensitive" in update_data or "ignore_whitespace" in update_data:
        existing = repo.get_rule_config(config_id)
        if existing:
            existing_config = existing.config or {}
            if "case_sensitive" in update_data:
                existing_config["case_sensitive"] = update_data.pop("case_sensitive")
            if "ignore_whitespace" in update_data:
                existing_config["ignore_whitespace"] = update_data.pop("ignore_whitespace")
            update_data["config"] = existing_config
    
    updated = repo.update_rule_config(config_id, **update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="配置不存在")
    return updated


@router.delete("/configs/{config_id}")
def delete_rule_config(
    config_id: int,
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """删除规则配置"""
    if not repo.delete_rule_config(config_id):
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"message": "配置已删除"}


@router.get("/configs/default", response_model=Optional[MergeRuleConfigOut])
def get_default_config(
    repo: WireMergerRepository = Depends(get_repo),
    current_user: User = Depends(get_current_user)
):
    """获取默认规则配置"""
    return repo.get_default_rule_config()


# 导入datetime
from datetime import datetime
