"""
并线合并功能的数据库操作层
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.services.wire_merger_models import (
    WireMergeProject,
    SourceWire,
    MergeGroup,
    MergeGroupWire,
    WireImportLog,
    MergeRuleConfig,
)
from app.services.wire_merger import Wire, ParallelGroup, MergeResult


class WireMergerRepository:
    """并线合并数据仓库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== 项目管理 ==========
    
    def create_project(self, name: str, description: str = "", config: dict = None) -> WireMergeProject:
        """创建项目"""
        project = WireMergeProject(
            name=name,
            description=description,
            config=config or {}
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def get_project(self, project_id: int) -> Optional[WireMergeProject]:
        """获取项目"""
        return self.db.query(WireMergeProject).filter(WireMergeProject.id == project_id).first()
    
    def get_projects(self, skip: int = 0, limit: int = 100):
        """获取项目列表"""
        return self.db.query(WireMergeProject).order_by(WireMergeProject.created_at.desc()).offset(skip).limit(limit).all()
    
    def delete_project(self, project_id: int) -> bool:
        """删除项目"""
        project = self.get_project(project_id)
        if project:
            self.db.delete(project)
            self.db.commit()
            return True
        return False
    
    # ========== 导线数据管理 ==========
    
    def import_wires(self, project_id: int, wires: list[Wire]) -> int:
        """导入导线数据"""
        count = 0
        for wire in wires:
            db_wire = SourceWire(
                project_id=project_id,
                wire_id=wire.wire_id,
                name=wire.name,
                node_a=wire.node_a,
                node_b=wire.node_b,
                color=wire.color,
                cable_type=wire.cable_type,
                extra_data=wire.extra_fields
            )
            self.db.add(db_wire)
            count += 1
        
        self.db.commit()
        return count
    
    def get_wires_by_project(self, project_id: int):
        """获取项目的所有导线"""
        return self.db.query(SourceWire).filter(SourceWire.project_id == project_id).all()
    
    def clear_wires(self, project_id: int) -> int:
        """清空项目的导线数据"""
        result = self.db.query(SourceWire).filter(SourceWire.project_id == project_id).delete()
        self.db.commit()
        return result
    
    def get_wire_statistics(self, project_id: int) -> dict:
        """获取导线统计信息"""
        stats = {
            "total_wires": 0,
            "unique_names": 0,
            "unique_colors": 0,
            "unique_cable_types": 0,
            "color_distribution": {},
            "cable_type_distribution": {}
        }
        
        # 基础统计
        stats["total_wires"] = self.db.query(SourceWire).filter(SourceWire.project_id == project_id).count()
        stats["unique_names"] = self.db.query(SourceWire.name).filter(SourceWire.project_id == project_id).distinct().count()
        stats["unique_colors"] = self.db.query(SourceWire.color).filter(SourceWire.project_id == project_id).distinct().count()
        stats["unique_cable_types"] = self.db.query(SourceWire.cable_type).filter(SourceWire.project_id == project_id).distinct().count()
        
        # 颜色分布
        color_counts = self.db.query(
            SourceWire.color,
            func.count(SourceWire.id)
        ).filter(SourceWire.project_id == project_id).group_by(SourceWire.color).all()
        stats["color_distribution"] = {color: count for color, count in color_counts}
        
        # 类型分布
        type_counts = self.db.query(
            SourceWire.cable_type,
            func.count(SourceWire.id)
        ).filter(SourceWire.project_id == project_id).group_by(SourceWire.cable_type).all()
        stats["cable_type_distribution"] = {cable_type: count for cable_type, count in type_counts}
        
        return stats
    
    # ========== 合并组管理 ==========
    
    def save_merge_groups(self, project_id: int, groups: list[ParallelGroup]):
        """保存合并组结果"""
        # 先清除旧的合并结果
        self.clear_merge_groups(project_id)
        
        for group in groups:
            db_group = MergeGroup(
                project_id=project_id,
                group_id=group.group_id,
                name=group.name,
                color=group.color,
                cable_type=group.cable_type,
                notes=group.notes,
                wire_count=len(group.wires)
            )
            self.db.add(db_group)
            self.db.flush()  # 获取group.id
            
            # 建立导线关联
            for wire_detail in group.wire_details:
                # 查找对应的SourceWire
                source_wire = self.db.query(SourceWire).filter(
                    SourceWire.project_id == project_id,
                    SourceWire.wire_id == wire_detail.wire_id
                ).first()
                
                if source_wire:
                    link = MergeGroupWire(
                        group_id=db_group.id,
                        wire_id=source_wire.id
                    )
                    self.db.add(link)
        
        self.db.commit()
    
    def get_merge_groups(self, project_id: int):
        """获取合并组"""
        return self.db.query(MergeGroup).filter(MergeGroup.project_id == project_id).order_by(MergeGroup.group_id).all()
    
    def clear_merge_groups(self, project_id: int):
        """清除合并组"""
        self.db.query(MergeGroup).filter(MergeGroup.project_id == project_id).delete()
        self.db.commit()
    
    # ========== 导入日志 ==========
    
    def create_import_log(self, project_id: int, filename: str, result: MergeResult, row_count: int) -> WireImportLog:
        """创建导入日志"""
        log = WireImportLog(
            project_id=project_id,
            filename=filename,
            row_count=row_count,
            success_count=len(result.groups) if result.success else 0,
            error_count=len(result.errors),
            warning_count=len(result.warnings),
            errors=result.errors,
            warnings=result.warnings
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_import_logs(self, project_id: int):
        """获取导入日志"""
        return self.db.query(WireImportLog).filter(WireImportLog.project_id == project_id).order_by(WireImportLog.created_at.desc()).all()
    
    # ========== 规则配置管理 ==========
    
    def create_rule_config(self, name: str, description: str, match_fields: list,
                          auto_merge_rules: list, config: dict, is_default: bool = False) -> MergeRuleConfig:
        """创建规则配置"""
        # 如果设置为默认，取消其他默认配置
        if is_default:
            self.db.query(MergeRuleConfig).filter(MergeRuleConfig.is_default == True).update({"is_default": False})
        
        rule_config = MergeRuleConfig(
            name=name,
            description=description,
            match_fields=match_fields,
            auto_merge_rules=auto_merge_rules,
            config=config,
            is_default=is_default
        )
        self.db.add(rule_config)
        self.db.commit()
        self.db.refresh(rule_config)
        return rule_config
    
    def get_rule_config(self, config_id: int) -> Optional[MergeRuleConfig]:
        """获取规则配置"""
        return self.db.query(MergeRuleConfig).filter(MergeRuleConfig.id == config_id).first()
    
    def get_default_rule_config(self) -> Optional[MergeRuleConfig]:
        """获取默认规则配置"""
        return self.db.query(MergeRuleConfig).filter(MergeRuleConfig.is_default == True).first()
    
    def get_rule_configs(self, skip: int = 0, limit: int = 100):
        """获取规则配置列表"""
        return self.db.query(MergeRuleConfig).order_by(MergeRuleConfig.created_at.desc()).offset(skip).limit(limit).all()
    
    def update_rule_config(self, config_id: int, **kwargs) -> Optional[MergeRuleConfig]:
        """更新规则配置"""
        config = self.get_rule_config(config_id)
        if not config:
            return None
        
        # 如果设置为默认，取消其他默认配置
        if kwargs.get("is_default"):
            self.db.query(MergeRuleConfig).filter(MergeRuleConfig.is_default == True).update({"is_default": False})
        
        for key, value in kwargs.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)
        
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def delete_rule_config(self, config_id: int) -> bool:
        """删除规则配置"""
        config = self.get_rule_config(config_id)
        if config:
            self.db.delete(config)
            self.db.commit()
            return True
        return False
