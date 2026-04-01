#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.wire_merger import WireMerger


def test_wire_merger():
    merger = WireMerger()

    test_wires = [
        {"WIRE_ID": "W001", "NAME": "POWER_LINE", "NODE_A": "A1", "NODE_B": "B1", "COLOR": "黑色", "CABLE_TYPE": "PVC"},
        {"WIRE_ID": "W002", "NAME": "POWER_LINE", "NODE_A": "A2", "NODE_B": "B2", "COLOR": "黑色", "CABLE_TYPE": "PVC"},
        {"WIRE_ID": "W003", "NAME": "POWER_LINE", "NODE_A": "A3", "NODE_B": "B3", "COLOR": "黑色", "CABLE_TYPE": "PVC"},
        {"WIRE_ID": "W004", "NAME": "SIGNAL_LINE", "NODE_A": "C1", "NODE_B": "D1", "COLOR": "红色", "CABLE_TYPE": "XLPE"},
        {"WIRE_ID": "W005", "NAME": "SIGNAL_LINE", "NODE_A": "C2", "NODE_B": "D2", "COLOR": "红色", "CABLE_TYPE": "XLPE"},
        {"WIRE_ID": "W006", "NAME": "SIGNAL_LINE", "NODE_A": "C3", "NODE_B": "D3", "COLOR": "蓝色", "CABLE_TYPE": "XLPE"},
        {"WIRE_ID": "W007", "NAME": "JUMP_WIRE", "NODE_A": "E1", "NODE_B": "F1", "COLOR": "黄色", "CABLE_TYPE": "Rubber"},
        {"WIRE_ID": "W008", "NAME": "JUMP_WIRE", "NODE_A": "E2", "NODE_B": "F2", "COLOR": "绿色", "CABLE_TYPE": "Rubber"},
        {"WIRE_ID": "W009", "NAME": "JUMP_WIRE", "NODE_A": "E3", "NODE_B": "F3", "COLOR": "蓝色", "CABLE_TYPE": "Rubber"},
    ]

    result = merger.merge_wires(test_wires)
    print("=" * 80)
    print("测试结果:")
    print("=" * 80)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=" * 80)

    if result["success"]:
        print("\n✅ 测试成功!")
        print(f"   - 总导线数: {result['total_wires']}")
        print(f"   - 总并线组数: {result['total_groups']}")
        if result["warnings"]:
            print(f"   - 警告: {result['warnings']}")
    else:
        print("\n❌ 测试失败!")
        print(f"   - 错误: {result['errors']}")


if __name__ == "__main__":
    test_wire_merger()
