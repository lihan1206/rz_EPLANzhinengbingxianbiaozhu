"""
EPLAN智能并线标注系统 - 并线识别与合并服务

功能：
1. 从CSV导入导线数据
2. 基于规则识别并线组
3. 支持自定义规则扩展
4. 生成结构化JSON输出
5. 错误处理与验证
"""

import csv
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Wire:
    """导线数据模型"""
    wire_id: str
    name: str
    node_a: str
    node_b: str
    color: str
    cable_type: str
    # 扩展字段，支持未来新增属性
    extra_fields: dict = field(default_factory=dict)


@dataclass
class ParallelGroup:
    """并线组结果模型"""
    group_id: int
    wires: list[str]  # WIRE_ID列表
    name: str
    color: str
    cable_type: str
    notes: str
    # 合并的导线详情
    wire_details: list[Wire] = field(default_factory=list)
    # 未合并的导线及其原因
    excluded_wires: list[dict] = field(default_factory=list)


@dataclass
class MergeResult:
    """合并操作结果"""
    success: bool
    groups: list[ParallelGroup] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class WireMergerConfig:
    """并线合并配置"""
    
    def __init__(self, config_path: Optional[str] = None):
        # 默认规则：NAME、COLOR、CABLE_TYPE必须相同
        self.default_rules = {
            "match_fields": ["name", "color", "cable_type"],
            "case_sensitive": False,
            "ignore_whitespace": True
        }
        
        # 自定义规则列表
        self.custom_rules: list[Callable[[Wire], bool]] = []
        
        # 自动合并规则（如NAME包含"JUMP"的导线自动合并）
        self.auto_merge_rules: list[dict] = []
        
        if config_path:
            self.load_from_file(config_path)
    
    def load_from_file(self, config_path: str) -> None:
        """从JSON文件加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if "match_fields" in config:
                self.default_rules["match_fields"] = config["match_fields"]
            if "case_sensitive" in config:
                self.default_rules["case_sensitive"] = config["case_sensitive"]
            if "ignore_whitespace" in config:
                self.default_rules["ignore_whitespace"] = config["ignore_whitespace"]
            if "auto_merge_rules" in config:
                self.auto_merge_rules = config["auto_merge_rules"]
                
            logger.info(f"配置已加载: {config_path}")
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
    
    def add_auto_merge_rule(self, field: str, operator: str, value: Any) -> None:
        """
        添加自动合并规则
        
        Args:
            field: 字段名（如 "name", "color"）
            operator: 操作符（"contains", "equals", "starts_with", "ends_with"）
            value: 比较值
        """
        self.auto_merge_rules.append({
            "field": field,
            "operator": operator,
            "value": value
        })
    
    def to_dict(self) -> dict:
        """导出配置为字典"""
        return {
            "default_rules": self.default_rules,
            "auto_merge_rules": self.auto_merge_rules
        }


class WireMerger:
    """
    导线并线识别与合并引擎
    
    核心功能：
    1. 基于规则的并线识别
    2. 支持自定义匹配规则
    3. 支持自动合并规则
    4. 详细的合并说明
    """
    
    # 必需的CSV字段
    REQUIRED_FIELDS = ["WIRE_ID", "NAME", "NODE_A", "NODE_B", "COLOR", "CABLE_TYPE"]
    
    def __init__(self, config: Optional[WireMergerConfig] = None):
        self.config = config or WireMergerConfig()
        self.wires: list[Wire] = []
        self.wire_id_set: set[str] = set()
    
    def load_from_csv(self, csv_path: str) -> MergeResult:
        """
        从CSV文件加载导线数据
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            MergeResult: 加载结果
        """
        result = MergeResult(success=True)
        self.wires = []
        self.wire_id_set = set()
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # 验证必需字段
                if not reader.fieldnames:
                    result.success = False
                    result.errors.append("CSV文件为空或格式错误")
                    return result
                
                missing_fields = [f for f in self.REQUIRED_FIELDS if f not in reader.fieldnames]
                if missing_fields:
                    result.success = False
                    result.errors.append(f"缺少必需字段: {', '.join(missing_fields)}")
                    return result
                
                # 读取数据
                for row_num, row in enumerate(reader, start=2):
                    try:
                        wire_id = row.get("WIRE_ID", "").strip()
                        
                        # 验证WIRE_ID
                        if not wire_id:
                            result.warnings.append(f"第{row_num}行: WIRE_ID为空，已跳过")
                            continue
                        
                        # 检查重复WIRE_ID
                        if wire_id in self.wire_id_set:
                            result.warnings.append(f"第{row_num}行: 重复的WIRE_ID '{wire_id}'")
                        else:
                            self.wire_id_set.add(wire_id)
                        
                        # 提取扩展字段
                        extra_fields = {}
                        for key in row.keys():
                            if key not in self.REQUIRED_FIELDS:
                                extra_fields[key] = row.get(key, "").strip()
                        
                        wire = Wire(
                            wire_id=wire_id,
                            name=self._normalize_value(row.get("NAME", "")),
                            node_a=row.get("NODE_A", "").strip(),
                            node_b=row.get("NODE_B", "").strip(),
                            color=self._normalize_value(row.get("COLOR", "")),
                            cable_type=self._normalize_value(row.get("CABLE_TYPE", "")),
                            extra_fields=extra_fields
                        )
                        
                        self.wires.append(wire)
                        
                    except Exception as e:
                        result.warnings.append(f"第{row_num}行: 解析错误 - {e}")
                
                logger.info(f"成功加载 {len(self.wires)} 条导线数据")
                
        except FileNotFoundError:
            result.success = False
            result.errors.append(f"文件不存在: {csv_path}")
        except Exception as e:
            result.success = False
            result.errors.append(f"读取CSV失败: {e}")
        
        return result
    
    def load_from_list(self, data: list[dict]) -> MergeResult:
        """
        从字典列表加载导线数据
        
        Args:
            data: 包含导线数据的字典列表
            
        Returns:
            MergeResult: 加载结果
        """
        result = MergeResult(success=True)
        self.wires = []
        self.wire_id_set = set()
        
        if not data:
            result.warnings.append("输入数据为空")
            return result
        
        # 验证必需字段
        first_row = data[0]
        missing_fields = [f for f in self.REQUIRED_FIELDS if f not in first_row]
        if missing_fields:
            result.success = False
            result.errors.append(f"缺少必需字段: {', '.join(missing_fields)}")
            return result
        
        # 读取数据
        for row_num, row in enumerate(data, start=1):
            try:
                wire_id = row.get("WIRE_ID", "").strip() if isinstance(row.get("WIRE_ID"), str) else str(row.get("WIRE_ID", ""))
                
                if not wire_id:
                    result.warnings.append(f"第{row_num}行: WIRE_ID为空，已跳过")
                    continue
                
                if wire_id in self.wire_id_set:
                    result.warnings.append(f"第{row_num}行: 重复的WIRE_ID '{wire_id}'")
                else:
                    self.wire_id_set.add(wire_id)
                
                # 提取扩展字段
                extra_fields = {}
                for key in row.keys():
                    if key not in self.REQUIRED_FIELDS:
                        extra_fields[key] = row.get(key, "")
                
                wire = Wire(
                    wire_id=wire_id,
                    name=self._normalize_value(row.get("NAME", "")),
                    node_a=row.get("NODE_A", "").strip() if isinstance(row.get("NODE_A"), str) else str(row.get("NODE_A", "")),
                    node_b=row.get("NODE_B", "").strip() if isinstance(row.get("NODE_B"), str) else str(row.get("NODE_B", "")),
                    color=self._normalize_value(row.get("COLOR", "")),
                    cable_type=self._normalize_value(row.get("CABLE_TYPE", "")),
                    extra_fields=extra_fields
                )
                
                self.wires.append(wire)
                
            except Exception as e:
                result.warnings.append(f"第{row_num}行: 解析错误 - {e}")
        
        return result
    
    def analyze(self) -> MergeResult:
        """
        执行并线分析
        
        分析逻辑：
        1. 首先按NAME分组
        2. 在每个NAME组内，按COLOR和CABLE_TYPE进一步分组
        3. 应用自动合并规则
        4. 生成合并结果和说明
        
        Returns:
            MergeResult: 分析结果
        """
        result = MergeResult(success=True)
        
        if not self.wires:
            result.warnings.append("没有导线数据可供分析")
            return result
        
        try:
            groups = self._group_wires()
            result.groups = self._create_parallel_groups(groups)
            logger.info(f"分析完成，发现 {len(result.groups)} 个并线组")
        except Exception as e:
            result.success = False
            result.errors.append(f"分析失败: {e}")
        
        return result
    
    def _normalize_value(self, value: Any) -> str:
        """标准化字段值"""
        if value is None:
            return ""
        value = str(value).strip()
        if self.config.default_rules.get("ignore_whitespace", True):
            value = " ".join(value.split())
        if not self.config.default_rules.get("case_sensitive", False):
            value = value.lower()
        return value
    
    def _group_wires(self) -> dict:
        """
        按规则对导线进行分组
        
        Returns:
            dict: 分组结果 {group_key: [wires]}
        """
        # 第一层：按NAME分组
        name_groups = defaultdict(list)
        for wire in self.wires:
            name_groups[wire.name].append(wire)
        
        # 第二层：在每个NAME组内，按匹配字段分组
        final_groups = defaultdict(list)
        
        for name, wires in name_groups.items():
            # 检查是否需要自动合并
            auto_merge = self._check_auto_merge(wires[0]) if wires else False
            
            if auto_merge:
                # 自动合并规则触发，所有导线合并为一组
                group_key = self._generate_group_key(wires[0], auto_merge=True)
                final_groups[group_key].extend(wires)
            else:
                # 按匹配字段分组
                match_fields = self.config.default_rules.get("match_fields", ["name", "color", "cable_type"])
                
                for wire in wires:
                    group_key = self._generate_group_key(wire, match_fields=match_fields)
                    final_groups[group_key].append(wire)
        
        return final_groups
    
    def _generate_group_key(self, wire: Wire, match_fields: Optional[list] = None, auto_merge: bool = False) -> str:
        """生成组键"""
        if auto_merge:
            return f"auto_merge:{wire.name}"
        
        match_fields = match_fields or ["name", "color", "cable_type"]
        key_parts = []
        
        for field in match_fields:
            value = getattr(wire, field, "")
            key_parts.append(f"{field}={value}")
        
        return "|".join(key_parts)
    
    def _check_auto_merge(self, wire: Wire) -> bool:
        """检查是否触发自动合并规则"""
        for rule in self.config.auto_merge_rules:
            field = rule.get("field", "")
            operator = rule.get("operator", "equals")
            value = rule.get("value", "")
            
            wire_value = getattr(wire, field, "")
            
            if operator == "contains":
                if value.lower() in wire_value.lower():
                    return True
            elif operator == "equals":
                if wire_value.lower() == value.lower():
                    return True
            elif operator == "starts_with":
                if wire_value.lower().startswith(value.lower()):
                    return True
            elif operator == "ends_with":
                if wire_value.lower().endswith(value.lower()):
                    return True
        
        return False
    
    def _create_parallel_groups(self, groups: dict) -> list[ParallelGroup]:
        """创建并线组结果"""
        parallel_groups = []
        group_id = 1
        
        for group_key, wires in groups.items():
            if len(wires) < 1:
                continue
            
            # 使用第一条导线作为组的代表
            representative = wires[0]
            
            # 生成合并说明
            notes = self._generate_notes(wires, group_key)
            
            group = ParallelGroup(
                group_id=group_id,
                wires=[w.wire_id for w in wires],
                name=representative.name,
                color=representative.color,
                cable_type=representative.cable_type,
                notes=notes,
                wire_details=wires,
                excluded_wires=[]
            )
            
            parallel_groups.append(group)
            group_id += 1
        
        # 按wire数量降序排序，数量多的优先
        parallel_groups.sort(key=lambda g: len(g.wires), reverse=True)
        
        # 重新编号
        for i, group in enumerate(parallel_groups, start=1):
            group.group_id = i
        
        return parallel_groups
    
    def _generate_notes(self, wires: list[Wire], group_key: str) -> str:
        """生成合并说明"""
        if len(wires) == 1:
            return "单条导线，无需合并"
        
        # 检查是否是自动合并
        if group_key.startswith("auto_merge:"):
            rule_desc = []
            for rule in self.config.auto_merge_rules:
                rule_desc.append(f"{rule['field']}{rule['operator']}{rule['value']}")
            return f"自动合并: 满足规则 {'; '.join(rule_desc)}"
        
        # 检查属性一致性
        colors = set(w.color for w in wires)
        cable_types = set(w.cable_type for w in wires)
        
        if len(colors) > 1 or len(cable_types) > 1:
            return "警告: 组内属性不一致"
        
        match_fields = self.config.default_rules.get("match_fields", ["name", "color", "cable_type"])
        return f"基于{'+'.join(match_fields)}合并，共{len(wires)}条导线"
    
    def export_to_json(self, result: MergeResult, output_path: Optional[str] = None) -> str:
        """
        导出结果为JSON格式
        
        Args:
            result: 合并结果
            output_path: 输出文件路径（可选）
            
        Returns:
            str: JSON字符串
        """
        output = {
            "success": result.success,
            "summary": {
                "total_groups": len(result.groups),
                "total_wires": sum(len(g.wires) for g in result.groups),
                "merged_groups": sum(1 for g in result.groups if len(g.wires) > 1)
            },
            "groups": [],
            "errors": result.errors,
            "warnings": result.warnings
        }
        
        for group in result.groups:
            group_data = {
                "group_id": group.group_id,
                "wires": group.wires,
                "name": group.name,
                "color": group.color,
                "cable_type": group.cable_type,
                "notes": group.notes,
                "wire_count": len(group.wires)
            }
            output["groups"].append(group_data)
        
        json_str = json.dumps(output, ensure_ascii=False, indent=2)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"结果已导出: {output_path}")
        
        return json_str
    
    def get_wire_statistics(self) -> dict:
        """获取导线统计信息"""
        if not self.wires:
            return {}
        
        stats = {
            "total_wires": len(self.wires),
            "unique_names": len(set(w.name for w in self.wires)),
            "unique_colors": len(set(w.color for w in self.wires)),
            "unique_cable_types": len(set(w.cable_type for w in self.wires)),
            "color_distribution": {},
            "cable_type_distribution": {}
        }
        
        for wire in self.wires:
            stats["color_distribution"][wire.color] = stats["color_distribution"].get(wire.color, 0) + 1
            stats["cable_type_distribution"][wire.cable_type] = stats["cable_type_distribution"].get(wire.cable_type, 0) + 1
        
        return stats


# 便捷函数
def merge_wires_from_csv(csv_path: str, config_path: Optional[str] = None) -> MergeResult:
    """
    从CSV文件合并导线的便捷函数
    
    Args:
        csv_path: CSV文件路径
        config_path: 配置文件路径（可选）
        
    Returns:
        MergeResult: 合并结果
    """
    config = WireMergerConfig(config_path) if config_path else None
    merger = WireMerger(config)
    
    load_result = merger.load_from_csv(csv_path)
    if not load_result.success:
        return load_result
    
    return merger.analyze()


def merge_wires_from_list(data: list[dict], config_path: Optional[str] = None) -> MergeResult:
    """
    从字典列表合并导线的便捷函数
    
    Args:
        data: 导线数据列表
        config_path: 配置文件路径（可选）
        
    Returns:
        MergeResult: 合并结果
    """
    config = WireMergerConfig(config_path) if config_path else None
    merger = WireMerger(config)
    
    load_result = merger.load_from_list(data)
    if not load_result.success:
        return load_result
    
    return merger.analyze()
