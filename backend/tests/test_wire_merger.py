"""
并线合并功能单元测试
"""

import pytest
import tempfile
import os
import csv
import json

from app.services.wire_merger import (
    WireMerger,
    WireMergerConfig,
    Wire,
    merge_wires_from_csv,
    merge_wires_from_list,
)


class TestWireMergerConfig:
    """测试配置类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = WireMergerConfig()
        assert config.default_rules["match_fields"] == ["name", "color", "cable_type"]
        assert config.default_rules["case_sensitive"] == False
        assert config.default_rules["ignore_whitespace"] == True
        assert config.auto_merge_rules == []
    
    def test_add_auto_merge_rule(self):
        """测试添加自动合并规则"""
        config = WireMergerConfig()
        config.add_auto_merge_rule("name", "contains", "JUMP")
        
        assert len(config.auto_merge_rules) == 1
        assert config.auto_merge_rules[0]["field"] == "name"
        assert config.auto_merge_rules[0]["operator"] == "contains"
        assert config.auto_merge_rules[0]["value"] == "JUMP"
    
    def test_load_from_file(self, tmp_path):
        """测试从文件加载配置"""
        config_file = tmp_path / "test_config.json"
        config_data = {
            "match_fields": ["name", "voltage"],
            "case_sensitive": True,
            "ignore_whitespace": False,
            "auto_merge_rules": [
                {"field": "name", "operator": "contains", "value": "TEST"}
            ]
        }
        config_file.write_text(json.dumps(config_data))
        
        config = WireMergerConfig(str(config_file))
        
        assert config.default_rules["match_fields"] == ["name", "voltage"]
        assert config.default_rules["case_sensitive"] == True
        assert config.default_rules["ignore_whitespace"] == False
        assert len(config.auto_merge_rules) == 1


class TestWireMerger:
    """测试合并器核心功能"""
    
    @pytest.fixture
    def sample_wires(self):
        """样本导线数据"""
        return [
            {"WIRE_ID": "W001", "NAME": "控制线", "NODE_A": "K1", "NODE_B": "K2", "COLOR": "黑", "CABLE_TYPE": "控制电缆"},
            {"WIRE_ID": "W002", "NAME": "控制线", "NODE_A": "K1", "NODE_B": "K2", "COLOR": "黑", "CABLE_TYPE": "控制电缆"},
            {"WIRE_ID": "W003", "NAME": "控制线", "NODE_A": "K1", "NODE_B": "K2", "COLOR": "黑", "CABLE_TYPE": "控制电缆"},
            {"WIRE_ID": "W004", "NAME": "控制线", "NODE_A": "K1", "NODE_B": "K2", "COLOR": "红", "CABLE_TYPE": "控制电缆"},
            {"WIRE_ID": "W005", "NAME": "控制线", "NODE_A": "K1", "NODE_B": "K2", "COLOR": "红", "CABLE_TYPE": "控制电缆"},
            {"WIRE_ID": "W006", "NAME": "动力线", "NODE_A": "M1", "NODE_B": "M2", "COLOR": "黄绿", "CABLE_TYPE": "动力电缆"},
            {"WIRE_ID": "W007", "NAME": "动力线", "NODE_A": "M1", "NODE_B": "M2", "COLOR": "黄绿", "CABLE_TYPE": "动力电缆"},
        ]
    
    @pytest.fixture
    def sample_csv(self, tmp_path, sample_wires):
        """创建样本CSV文件"""
        csv_file = tmp_path / "test_wires.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["WIRE_ID", "NAME", "NODE_A", "NODE_B", "COLOR", "CABLE_TYPE"])
            writer.writeheader()
            writer.writerows(sample_wires)
        return str(csv_file)
    
    def test_load_from_csv(self, sample_csv):
        """测试从CSV加载"""
        merger = WireMerger()
        result = merger.load_from_csv(sample_csv)
        
        assert result.success == True
        assert len(merger.wires) == 7
        assert len(result.errors) == 0
    
    def test_load_from_list(self, sample_wires):
        """测试从列表加载"""
        merger = WireMerger()
        result = merger.load_from_list(sample_wires)
        
        assert result.success == True
        assert len(merger.wires) == 7
        assert merger.wires[0].wire_id == "W001"
        assert merger.wires[0].name == "控制线"
    
    def test_missing_required_fields(self):
        """测试缺少必需字段"""
        invalid_data = [
            {"WIRE_ID": "W001", "NAME": "测试线"}  # 缺少其他必需字段
        ]
        
        merger = WireMerger()
        result = merger.load_from_list(invalid_data)
        
        assert result.success == False
        assert len(result.errors) > 0
        assert "缺少必需字段" in result.errors[0]
    
    def test_duplicate_wire_id(self):
        """测试重复WIRE_ID检测"""
        data = [
            {"WIRE_ID": "W001", "NAME": "线1", "NODE_A": "A", "NODE_B": "B", "COLOR": "黑", "CABLE_TYPE": "电缆"},
            {"WIRE_ID": "W001", "NAME": "线2", "NODE_A": "C", "NODE_B": "D", "COLOR": "红", "CABLE_TYPE": "电缆"},
        ]
        
        merger = WireMerger()
        result = merger.load_from_list(data)
        
        assert result.success == True
        assert len(result.warnings) > 0
        assert "重复" in result.warnings[0]
    
    def test_basic_merge(self, sample_wires):
        """测试基本合并功能"""
        merger = WireMerger()
        merger.load_from_list(sample_wires)
        result = merger.analyze()
        
        assert result.success == True
        assert len(result.groups) == 3  # 黑控制线组、红控制线组、黄绿动力线组
        
        # 验证黑控制线组
        black_group = next((g for g in result.groups if g.color == "黑"), None)
        assert black_group is not None
        assert len(black_group.wires) == 3
        assert black_group.name == "控制线"
    
    def test_auto_merge_rule(self):
        """测试自动合并规则"""
        data = [
            {"WIRE_ID": "W001", "NAME": "JUMP_01", "NODE_A": "A", "NODE_B": "B", "COLOR": "蓝", "CABLE_TYPE": "跳线"},
            {"WIRE_ID": "W002", "NAME": "JUMP_02", "NODE_A": "C", "NODE_B": "D", "COLOR": "蓝", "CABLE_TYPE": "跳线"},
            {"WIRE_ID": "W003", "NAME": "JUMP_03", "NODE_A": "E", "NODE_B": "F", "COLOR": "红", "CABLE_TYPE": "跳线"},
        ]
        
        config = WireMergerConfig()
        config.add_auto_merge_rule("name", "contains", "JUMP")
        
        merger = WireMerger(config)
        merger.load_from_list(data)
        result = merger.analyze()
        
        assert result.success == True
        # JUMP线应该合并为一组（不管颜色和类型是否相同）
        jump_group = next((g for g in result.groups if "JUMP" in g.name), None)
        assert jump_group is not None
        assert len(jump_group.wires) == 3
    
    def test_export_to_json(self, sample_wires, tmp_path):
        """测试JSON导出"""
        merger = WireMerger()
        merger.load_from_list(sample_wires)
        result = merger.analyze()
        
        output_file = tmp_path / "output.json"
        json_str = merger.export_to_json(result, str(output_file))
        
        # 验证文件已创建
        assert output_file.exists()
        
        # 验证JSON内容
        data = json.loads(json_str)
        assert data["success"] == True
        assert "summary" in data
        assert "groups" in data
        assert len(data["groups"]) == 3
    
    def test_wire_statistics(self, sample_wires):
        """测试统计功能"""
        merger = WireMerger()
        merger.load_from_list(sample_wires)
        
        stats = merger.get_wire_statistics()
        
        assert stats["total_wires"] == 7
        assert stats["unique_names"] == 2  # 控制线、动力线
        assert stats["unique_colors"] == 3  # 黑、红、黄绿
        assert stats["unique_cable_types"] == 2  # 控制电缆、动力电缆
        assert "黑" in stats["color_distribution"]
        assert stats["color_distribution"]["黑"] == 3


class TestMergeWiresFromCSV:
    """测试便捷函数"""
    
    def test_merge_wires_from_csv(self, tmp_path):
        """测试便捷合并函数"""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["WIRE_ID", "NAME", "NODE_A", "NODE_B", "COLOR", "CABLE_TYPE"])
            writer.writerow(["W001", "测试线", "A", "B", "黑", "电缆"])
            writer.writerow(["W002", "测试线", "A", "B", "黑", "电缆"])
        
        result = merge_wires_from_csv(str(csv_file))
        
        assert result.success == True
        assert len(result.groups) == 1
        assert len(result.groups[0].wires) == 2
    
    def test_merge_wires_from_list(self):
        """测试便捷合并函数（列表输入）"""
        data = [
            {"WIRE_ID": "W001", "NAME": "测试线", "NODE_A": "A", "NODE_B": "B", "COLOR": "黑", "CABLE_TYPE": "电缆"},
            {"WIRE_ID": "W002", "NAME": "测试线", "NODE_A": "A", "NODE_B": "B", "COLOR": "黑", "CABLE_TYPE": "电缆"},
        ]
        
        result = merge_wires_from_list(data)
        
        assert result.success == True
        assert len(result.groups) == 1


class TestLargeDataset:
    """测试大数据集性能"""
    
    def test_large_dataset(self, tmp_path):
        """测试1000+条导线"""
        csv_file = tmp_path / "large.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["WIRE_ID", "NAME", "NODE_A", "NODE_B", "COLOR", "CABLE_TYPE"])
            
            # 生成1000条导线
            for i in range(1000):
                name = f"线组{i % 10}"  # 10个不同的组
                color = ["黑", "红", "蓝", "绿", "黄"][i % 5]
                cable_type = "电缆"
                writer.writerow([f"W{i:04d}", name, "A", "B", color, cable_type])
        
        import time
        start_time = time.time()
        
        result = merge_wires_from_csv(str(csv_file))
        
        elapsed_time = time.time() - start_time
        
        assert result.success == True
        assert elapsed_time < 5.0  # 应该在5秒内完成
        print(f"处理1000条导线耗时: {elapsed_time:.2f}秒")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
