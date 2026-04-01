import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class WireData:
    wire_id: str
    name: str
    node_a: str
    node_b: str
    color: str
    cable_type: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "wire_id": self.wire_id,
            "name": self.name,
            "node_a": self.node_a,
            "node_b": self.node_b,
            "color": self.color,
            "cable_type": self.cable_type,
            "attributes": self.attributes,
        }


@dataclass
class ParallelGroup:
    group_id: str
    wires: list[str]
    name: str
    color: str
    cable_type: str
    notes: list[str]

    def to_dict(self) -> dict:
        return {
            "group_id": self.group_id,
            "wires": self.wires,
            "name": self.name,
            "color": self.color,
            "cable_type": self.cable_type,
            "notes": self.notes,
        }


class MergeRule(ABC):
    @abstractmethod
    def should_merge(self, wire1: WireData, wire2: WireData) -> bool:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass


class DefaultMergeRule(MergeRule):
    def __init__(self, check_name: bool = True, check_color: bool = True, check_cable_type: bool = True):
        self.check_name = check_name
        self.check_color = check_color
        self.check_cable_type = check_cable_type

    def should_merge(self, wire1: WireData, wire2: WireData) -> bool:
        if self.check_name and wire1.name != wire2.name:
            return False
        if self.check_color and wire1.color != wire2.color:
            return False
        if self.check_cable_type and wire1.cable_type != wire2.cable_type:
            return False
        return True

    def get_description(self) -> str:
        checks = []
        if self.check_name:
            checks.append("NAME相同")
        if self.check_color:
            checks.append("COLOR相同")
        if self.check_cable_type:
            checks.append("CABLE_TYPE相同")
        return f"默认规则: {', '.join(checks)}"


class PatternMergeRule(MergeRule):
    def __init__(self, pattern: str, field_name: str = "name"):
        self.pattern = pattern
        self.field_name = field_name
        self._compiled = re.compile(pattern, re.IGNORECASE)

    def should_merge(self, wire1: WireData, wire2: WireData) -> bool:
        value1 = getattr(wire1, self.field_name, "")
        value2 = getattr(wire2, self.field_name, "")

        if self._compiled.search(value1) and self._compiled.search(value2):
            return wire1.name == wire2.name and wire1.color == wire2.color

        return False

    def get_description(self) -> str:
        return f"模式规则: {self.field_name} 匹配 '{self.pattern}'"


class AttributeMergeRule(MergeRule):
    def __init__(self, attribute_name: str, match_value: Any = None):
        self.attribute_name = attribute_name
        self.match_value = match_value

    def should_merge(self, wire1: WireData, wire2: WireData) -> bool:
        attr1 = wire1.attributes.get(self.attribute_name)
        attr2 = wire2.attributes.get(self.attribute_name)

        if attr1 is None or attr2 is None:
            return False

        if self.match_value is not None:
            return attr1 == self.match_value and attr2 == self.match_value

        return attr1 == attr2

    def get_description(self) -> str:
        if self.match_value is not None:
            return f"属性规则: {self.attribute_name} = {self.match_value}"
        return f"属性规则: {self.attribute_name} 相同"


class CustomFunctionRule(MergeRule):
    def __init__(self, func: Callable[[WireData, WireData], bool], description: str):
        self.func = func
        self._description = description

    def should_merge(self, wire1: WireData, wire2: WireData) -> bool:
        return self.func(wire1, wire2)

    def get_description(self) -> str:
        return self._description


@dataclass
class RuleConfig:
    enabled: bool = True
    priority: int = 0
    rule_type: str = "default"
    params: dict[str, Any] = field(default_factory=dict)


class RuleEngine:
    def __init__(self):
        self.rules: list[tuple[MergeRule, RuleConfig]] = []
        self._load_default_rules()

    def _load_default_rules(self):
        default_rule = DefaultMergeRule(check_name=True, check_color=True, check_cable_type=True)
        config = RuleConfig(enabled=True, priority=0, rule_type="default")
        self.rules.append((default_rule, config))

    def add_rule(self, rule: MergeRule, config: RuleConfig | None = None):
        if config is None:
            config = RuleConfig(enabled=True, priority=len(self.rules))

        self.rules.append((rule, config))
        self.rules.sort(key=lambda x: x[1].priority)

    def remove_rule(self, index: int):
        if 0 <= index < len(self.rules):
            self.rules.pop(index)

    def clear_rules(self):
        self.rules.clear()

    def load_from_file(self, filepath: str | Path):
        filepath = Path(filepath)
        if not filepath.exists():
            return

        with open(filepath, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        self._apply_config(config_data)

    def _apply_config(self, config_data: dict):
        if "rules" not in config_data:
            return

        self.clear_rules()

        for rule_def in config_data["rules"]:
            if not rule_def.get("enabled", True):
                continue

            rule_type = rule_def.get("type", "default")
            params = rule_def.get("params", {})
            priority = rule_def.get("priority", 0)

            rule = self._create_rule(rule_type, params)
            if rule:
                config = RuleConfig(
                    enabled=True,
                    priority=priority,
                    rule_type=rule_type,
                    params=params,
                )
                self.add_rule(rule, config)

    def _create_rule(self, rule_type: str, params: dict) -> MergeRule | None:
        if rule_type == "default":
            return DefaultMergeRule(
                check_name=params.get("check_name", True),
                check_color=params.get("check_color", True),
                check_cable_type=params.get("check_cable_type", True),
            )
        elif rule_type == "pattern":
            pattern = params.get("pattern", "")
            field_name = params.get("field", "name")
            if pattern:
                return PatternMergeRule(pattern, field_name)
        elif rule_type == "attribute":
            attr_name = params.get("attribute_name", "")
            match_value = params.get("match_value")
            if attr_name:
                return AttributeMergeRule(attr_name, match_value)

        return None

    def should_merge(self, wire1: WireData, wire2: WireData) -> tuple[bool, str]:
        for rule, config in self.rules:
            if not config.enabled:
                continue

            if rule.should_merge(wire1, wire2):
                return True, rule.get_description()

        return False, "未匹配任何合并规则"

    def get_rule_descriptions(self) -> list[str]:
        return [rule.get_description() for rule, config in self.rules if config.enabled]
