import json
from pathlib import Path

from app.services.wire_data_analyzer import analyze_wire_data
from app.services.rule_engine import RuleEngine, DefaultMergeRule, PatternMergeRule, RuleConfig


def demo_basic_analysis():
    print("=" * 60)
    print("示例1: 基本并线分析")
    print("=" * 60)

    wires_data = [
        {"wire_id": "W-001", "name": "POWER_MAIN", "node_a": "X10", "node_b": "X11", "color": "黑", "cable_type": "RVV"},
        {"wire_id": "W-002", "name": "POWER_MAIN", "node_a": "X10", "node_b": "X11", "color": "黑", "cable_type": "RVV"},
        {"wire_id": "W-003", "name": "POWER_MAIN", "node_a": "X10", "node_b": "X11", "color": "黑", "cable_type": "RVV"},
        {"wire_id": "W-004", "name": "CONTROL_SIG", "node_a": "X12", "node_b": "X13", "color": "蓝", "cable_type": "RVVP"},
        {"wire_id": "W-005", "name": "CONTROL_SIG", "node_a": "X12", "node_b": "X13", "color": "蓝", "cable_type": "RVVP"},
        {"wire_id": "W-006", "name": "POWER_AUX", "node_a": "X18", "node_b": "X19", "color": "黑", "cable_type": "RVV"},
        {"wire_id": "W-007", "name": "POWER_AUX", "node_a": "X18", "node_b": "X19", "color": "红", "cable_type": "RVV"},
    ]

    result = analyze_wire_data(wires_data)

    print(f"\n总导线数: {result['total_wires']}")
    print(f"已分组导线: {result['grouped_wires']}")
    print(f"未分组导线: {result['ungrouped_wires']}")
    print(f"\n并线组数: {len(result['groups'])}")

    for group in result["groups"]:
        print(f"\n{group['group_id']}:")
        print(f"  导线: {', '.join(group['wires'])}")
        print(f"  名称: {group['name']}")
        print(f"  颜色: {group['color']}")
        print(f"  类型: {group['cable_type']}")
        print(f"  说明: {'; '.join(group['notes'])}")

    if result["warnings"]:
        print(f"\n警告: {'; '.join(result['warnings'])}")
    if result["errors"]:
        print(f"\n错误: {'; '.join(result['errors'])}")


def demo_custom_rules():
    print("\n" + "=" * 60)
    print("示例2: 自定义规则 - JUMP导线自动合并")
    print("=" * 60)

    engine = RuleEngine()
    engine.clear_rules()

    default_rule = DefaultMergeRule(check_name=True, check_color=True, check_cable_type=True)
    engine.add_rule(default_rule, RuleConfig(enabled=True, priority=0))

    jump_rule = PatternMergeRule(pattern="JUMP", field_name="name")
    engine.add_rule(jump_rule, RuleConfig(enabled=True, priority=1))

    wires_data = [
        {"wire_id": "W-001", "name": "JUMP_LINE1", "node_a": "X10", "node_b": "X11", "color": "红", "cable_type": "RVV"},
        {"wire_id": "W-002", "name": "JUMP_LINE1", "node_a": "X10", "node_b": "X11", "color": "红", "cable_type": "RVV"},
        {"wire_id": "W-003", "name": "JUMP_LINE2", "node_a": "X12", "node_b": "X13", "color": "蓝", "cable_type": "RVVP"},
        {"wire_id": "W-004", "name": "JUMP_LINE2", "node_a": "X12", "node_b": "X13", "color": "蓝", "cable_type": "RVVP"},
        {"wire_id": "W-005", "name": "POWER_MAIN", "node_a": "X14", "node_b": "X15", "color": "黑", "cable_type": "RVV"},
        {"wire_id": "W-006", "name": "POWER_MAIN", "node_a": "X14", "node_b": "X15", "color": "黑", "cable_type": "RVV"},
    ]

    from app.services.wire_data_analyzer import WireDataAnalyzer
    analyzer = WireDataAnalyzer()
    analyzer.rule_engine = engine

    result = analyzer.analyze(wires_data)

    print(f"\n总导线数: {result['total_wires']}")
    print(f"并线组数: {len(result['groups'])}")

    for group in result["groups"]:
        print(f"\n{group['group_id']}: {', '.join(group['wires'])} - {group['name']}")


def demo_config_file():
    print("\n" + "=" * 60)
    print("示例3: 使用配置文件")
    print("=" * 60)

    config_path = Path(__file__).parent.parent / "config" / "rules.json"
    print(f"\n配置文件路径: {config_path}")

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print(f"\n配置版本: {config.get('version')}")
        print(f"配置说明: {config.get('description')}")
        print(f"\n已启用规则:")
        for rule in config.get("rules", []):
            if rule.get("enabled"):
                print(f"  - 类型: {rule['type']}, 优先级: {rule['priority']}")
                print(f"    参数: {rule['params']}")
    else:
        print("配置文件不存在")


def demo_error_handling():
    print("\n" + "=" * 60)
    print("示例4: 错误处理 - 重复ID和缺失字段")
    print("=" * 60)

    wires_data = [
        {"wire_id": "W-001", "name": "POWER_MAIN", "node_a": "X10", "node_b": "X11", "color": "黑", "cable_type": "RVV"},
        {"wire_id": "W-001", "name": "POWER_MAIN", "node_a": "X10", "node_b": "X11", "color": "黑", "cable_type": "RVV"},
        {"wire_id": "", "name": "", "node_a": "X12", "node_b": "X13", "color": "蓝", "cable_type": ""},
        {"wire_id": "W-002", "name": "CONTROL", "node_a": "X14", "node_b": "X15", "color": "红", "cable_type": "RVVP"},
    ]

    result = analyze_wire_data(wires_data)

    print(f"\n总导线数: {result['total_wires']}")
    if result["warnings"]:
        print(f"\n警告:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    if result["errors"]:
        print(f"\n错误:")
        for error in result["errors"]:
            print(f"  - {error}")


def demo_json_output():
    print("\n" + "=" * 60)
    print("示例5: JSON格式输出")
    print("=" * 60)

    wires_data = [
        {"wire_id": "W-001", "name": "POWER_MAIN", "node_a": "X10", "node_b": "X11", "color": "黑", "cable_type": "RVV"},
        {"wire_id": "W-002", "name": "POWER_MAIN", "node_a": "X10", "node_b": "X11", "color": "黑", "cable_type": "RVV"},
        {"wire_id": "W-003", "name": "CONTROL", "node_a": "X12", "node_b": "X13", "color": "蓝", "cable_type": "RVVP"},
        {"wire_id": "W-004", "name": "CONTROL", "node_a": "X12", "node_b": "X13", "color": "蓝", "cable_type": "RVVP"},
    ]

    result = analyze_wire_data(wires_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    demo_basic_analysis()
    demo_custom_rules()
    demo_config_file()
    demo_error_handling()
    demo_json_output()
