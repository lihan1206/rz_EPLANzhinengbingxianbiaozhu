"""
EPLAN 导线并线分析 - JSON 格式测试脚本
"""

import json
from app.services.json_parallel_analysis import analyze_wires_json, AnalysisConfig


# 测试数据 1: 基本并线场景
test_wires_1 = [
    {"id": "W001", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
    {"id": "W002", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
    {"id": "W003", "start": "A2", "end": "B2", "area": 2.5, "color": "蓝"},
    {"id": "W004", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
]

# 测试数据 2: 颜色不一致（不应合并）
test_wires_2 = [
    {"id": "W001", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
    {"id": "W002", "start": "A1", "end": "B1", "area": 1.5, "color": "蓝"},
]

# 测试数据 3: 截面积不一致（不应合并）
test_wires_3 = [
    {"id": "W001", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
    {"id": "W002", "start": "A1", "end": "B1", "area": 2.5, "color": "红"},
]

# 测试数据 4: 多组并线 + 超过最大限制
test_wires_4 = [
    {"id": "W001", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
    {"id": "W002", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
    {"id": "W003", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
    {"id": "W004", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
    {"id": "W005", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
    {"id": "W006", "start": "A2", "end": "B2", "area": 2.5, "color": "蓝", "shielded": True},
    {"id": "W007", "start": "A2", "end": "B2", "area": 2.5, "color": "蓝", "shielded": True},
]

# 测试数据 5: 带电压等级和屏蔽属性
test_wires_5 = [
    {"id": "W001", "start": "A1", "end": "B1", "area": 4.0, "color": "黄绿", "voltage_level": "380V", "shielded": True},
    {"id": "W002", "start": "A1", "end": "B1", "area": 4.0, "color": "黄绿", "voltage_level": "380V", "shielded": True},
    {"id": "W003", "start": "A1", "end": "B1", "area": 4.0, "color": "黄绿", "voltage_level": "220V", "shielded": True},
]


def run_test(name: str, wires: list, config: AnalysisConfig = None):
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"{'='*60}")
    print(f"输入导线数: {len(wires)}")
    
    result = analyze_wires_json(wires, config)
    
    print(f"\n总导线数: {result.total_wires}")
    print(f"并线组数: {len(result.parallel_groups)}")
    print(f"未分组导线: {result.ungrouped_wires}")
    
    if result.parallel_groups:
        print(f"\n并线组详情:")
        for group in result.parallel_groups:
            print(f"\n  [{group.parallel_group_id}]")
            print(f"    路径: {group.start} → {group.end}")
            print(f"    数量: {group.count}")
            print(f"    总截面积: {group.total_area} mm²")
            print(f"    标注: {group.label}")
            print(f"    合规: {'✓' if group.compliant else '✗'}")
            print(f"    导线: {group.wires}")
            print(f"    备注: {group.notes}")
    
    # 输出标准 JSON
    print(f"\n标准 JSON 输出:")
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    
    return result


if __name__ == "__main__":
    print("EPLAN 导线智能并线标注 - JSON 分析测试")
    
    # 测试 1: 基本场景
    run_test("基本并线场景 (3根同组，1根单独)", test_wires_1)
    
    # 测试 2: 颜色不一致
    run_test("颜色不一致 (不应合并)", test_wires_2)
    
    # 测试 3: 截面积不一致
    run_test("截面积不一致 (不应合并)", test_wires_3)
    
    # 测试 4: 多组并线 + 最大限制 4
    config_4 = AnalysisConfig(min_parallel_count=2, max_parallel_count=4)
    run_test("多组并线 + 最大限制4 (5根应不合规)", test_wires_4, config_4)
    
    # 测试 5: 电压等级不一致
    config_5 = AnalysisConfig(check_voltage_consistency=True)
    run_test("电压等级不一致 (不应合并)", test_wires_5, config_5)
    
    print(f"\n{'='*60}")
    print("所有测试完成!")
    print(f"{'='*60}")
