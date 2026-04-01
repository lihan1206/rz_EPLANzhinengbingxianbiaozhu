# EPLAN智能并线标注系统 - 使用文档

## 概述

EPLAN智能并线标注系统是一个用于自动识别和合并导线的工具。系统根据用户定义的规则，将具有相同属性的导线合并为并线组，生成结构化的JSON输出，并支持将结果保存到MySQL数据库。

## 核心功能

1. **CSV数据导入**：支持从CSV文件导入导线数据
2. **智能并线识别**：基于规则自动识别可合并的导线
3. **自定义规则**：支持灵活的规则配置和扩展
4. **结构化输出**：生成详细的JSON格式结果
5. **数据库集成**：支持将结果保存到MySQL
6. **RESTful API**：提供完整的API接口

## 数据格式

### 输入CSV格式

CSV文件必须包含以下字段：

| 字段名 | 说明 | 示例 |
|--------|------|------|
| WIRE_ID | 导线唯一标识 | W001 |
| NAME | 导线名称 | 控制线 |
| NODE_A | 起始节点 | K1 |
| NODE_B | 终止节点 | K2 |
| COLOR | 导线颜色 | 黑 |
| CABLE_TYPE | 电缆类型 | 控制电缆 |

**示例CSV内容：**
```csv
WIRE_ID,NAME,NODE_A,NODE_B,COLOR,CABLE_TYPE
W001,控制线,K1,K2,黑,控制电缆
W002,控制线,K1,K2,黑,控制电缆
W003,控制线,K1,K2,红,控制电缆
```

### 输出JSON格式

```json
{
  "success": true,
  "summary": {
    "total_groups": 3,
    "total_wires": 7,
    "merged_groups": 2
  },
  "groups": [
    {
      "group_id": 1,
      "wires": ["W001", "W002"],
      "name": "控制线",
      "color": "黑",
      "cable_type": "控制电缆",
      "notes": "基于name+color+cable_type合并，共2条导线",
      "wire_count": 2
    }
  ],
  "errors": [],
  "warnings": []
}
```

## 并线识别规则

### 默认规则

系统默认使用以下规则进行并线识别：

1. **NAME相同**：导线名称必须相同
2. **COLOR相同**：导线颜色必须相同
3. **CABLE_TYPE相同**：电缆类型必须相同

只有同时满足以上三个条件的导线才会被合并到同一组。

### 自动合并规则

支持自定义自动合并规则，例如：

- NAME包含"JUMP"的导线自动合并
- NAME以"TB"开头的导线自动合并
- CABLE_TYPE为"控制线"的导线自动合并

## API接口

### 1. 创建项目

```http
POST /api/wire-merger/projects
Content-Type: application/x-www-form-urlencoded

name=项目名称&description=项目描述&config={"key":"value"}
```

### 2. 从CSV文件合并

```http
POST /api/wire-merger/merge-from-csv
Content-Type: multipart/form-data

file: [CSV文件]
project_name: [可选]项目名称
config_id: [可选]规则配置ID
```

### 3. 从JSON数据合并

```http
POST /api/wire-merger/merge
Content-Type: application/json

{
  "project_name": "项目名称",
  "wires": [
    {
      "WIRE_ID": "W001",
      "NAME": "控制线",
      "NODE_A": "K1",
      "NODE_B": "K2",
      "COLOR": "黑",
      "CABLE_TYPE": "控制电缆"
    }
  ],
  "config_id": 1
}
```

### 4. 获取项目详情

```http
GET /api/wire-merger/projects/{project_id}
```

### 5. 获取项目统计

```http
GET /api/wire-merger/projects/{project_id}/statistics
```

### 6. 获取并线组

```http
GET /api/wire-merger/projects/{project_id}/groups
```

### 7. 创建规则配置

```http
POST /api/wire-merger/configs
Content-Type: application/json

{
  "name": "配置名称",
  "description": "配置描述",
  "match_fields": ["name", "color", "cable_type"],
  "auto_merge_rules": [
    {
      "field": "name",
      "operator": "contains",
      "value": "JUMP"
    }
  ],
  "case_sensitive": false,
  "ignore_whitespace": true,
  "is_default": false
}
```

### 8. 获取规则配置列表

```http
GET /api/wire-merger/configs
```

### 9. 获取默认规则配置

```http
GET /api/wire-merger/configs/default
```

## 配置文件

### 配置文件格式（JSON）

```json
{
  "name": "默认并线规则",
  "description": "基于NAME、COLOR、CABLE_TYPE三字段匹配的默认规则",
  "match_fields": ["name", "color", "cable_type"],
  "auto_merge_rules": [
    {
      "field": "name",
      "operator": "contains",
      "value": "JUMP",
      "description": "NAME包含JUMP的导线自动合并"
    }
  ],
  "case_sensitive": false,
  "ignore_whitespace": true
}
```

### 配置项说明

| 配置项 | 类型 | 说明 |
|--------|------|------|
| match_fields | array | 用于匹配的字段列表 |
| auto_merge_rules | array | 自动合并规则列表 |
| case_sensitive | boolean | 是否区分大小写 |
| ignore_whitespace | boolean | 是否忽略空白字符 |

### 自动合并规则操作符

| 操作符 | 说明 |
|--------|------|
| contains | 包含 |
| equals | 等于 |
| starts_with | 以...开头 |
| ends_with | 以...结尾 |

## Python SDK使用

### 基础用法

```python
from app.services.wire_merger import WireMerger, WireMergerConfig

# 创建合并器
merger = WireMerger()

# 从CSV加载
result = merger.load_from_csv("wires.csv")
if result.success:
    # 执行分析
    result = merger.analyze()
    
    # 导出结果
    json_output = merger.export_to_json(result, "output.json")
    print(json_output)
```

### 使用自定义配置

```python
from app.services.wire_merger import WireMerger, WireMergerConfig

# 创建配置
config = WireMergerConfig()
config.add_auto_merge_rule("name", "contains", "JUMP")
config.default_rules["match_fields"] = ["name", "color", "cable_type", "voltage"]

# 使用配置创建合并器
merger = WireMerger(config)
merger.load_from_csv("wires.csv")
result = merger.analyze()
```

### 便捷函数

```python
from app.services.wire_merger import merge_wires_from_csv, merge_wires_from_list

# 从CSV合并
result = merge_wires_from_csv("wires.csv", "config.json")

# 从列表合并
data = [
    {"WIRE_ID": "W001", "NAME": "线1", ...},
    {"WIRE_ID": "W002", "NAME": "线1", ...},
]
result = merge_wires_from_list(data)
```

## 错误处理

### 输入验证错误

- 缺少必需字段
- 重复的WIRE_ID
- 空的WIRE_ID
- CSV格式错误

### 输出错误信息

```json
{
  "success": false,
  "errors": ["缺少必需字段: COLOR, CABLE_TYPE"],
  "warnings": ["第5行: 重复的WIRE_ID 'W003'"]
}
```

## 数据库表结构

### wire_merge_projects
存储并线合并项目信息

### source_wires
存储原始导线数据

### merge_groups
存储合并后的并线组

### merge_group_wires
存储并线组与导线的关联关系

### wire_import_logs
存储导入日志

### merge_rule_configs
存储合并规则配置

## 性能说明

- 支持1000+条导线的批量处理
- 典型处理时间：< 5秒（1000条导线）
- 内存占用：与导线数量成正比

## 扩展性

系统支持以下扩展：

1. **新增匹配字段**：如VOLTAGE、LENGTH等
2. **自定义规则**：通过配置文件或API动态添加
3. **多数据源**：支持CSV、JSON、数据库等多种输入
4. **自定义输出格式**：可扩展为XML、Excel等格式
