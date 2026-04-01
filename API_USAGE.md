# EPLAN 导线并线智能标注工具 API 使用说明

## 接口地址

```
POST /api/wire-analysis/analyze
```

## 请求参数

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| wires | array | 是 | 导线数据列表 | - |
| min_parallel_count | int | 否 | 最小并线数量 (≥2) | 2 |
| max_parallel_count | int | 否 | 最大并线数量限制 | 4 |

### 导线数据结构 (WireData)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | string | 导线ID |
| start | string | 起点端子 |
| end | string | 终点端子 |
| area | float | 截面积 (mm²) |
| color | string | 颜色 |
| properties | object | 属性（电压等级、屏蔽等，可选） |

## 请求示例

```json
{
  "wires": [
    {"id": "W001", "start": "X1:1", "end": "X2:1", "area": 2.5, "color": "红色", "properties": {"电压等级": "220V", "屏蔽": "否"}},
    {"id": "W002", "start": "X1:1", "end": "X2:1", "area": 2.5, "color": "红色", "properties": {"电压等级": "220V", "屏蔽": "否"}},
    {"id": "W003", "start": "X1:1", "end": "X2:1", "area": 2.5, "color": "红色", "properties": {"电压等级": "220V", "屏蔽": "否"}},
    {"id": "W004", "start": "X1:2", "end": "X3:1", "area": 1.5, "color": "蓝色", "properties": {"电压等级": "24V", "屏蔽": "是"}},
    {"id": "W005", "start": "X1:2", "end": "X3:1", "area": 1.5, "color": "蓝色", "properties": {"电压等级": "24V", "屏蔽": "是"}}
  ],
  "min_parallel_count": 2,
  "max_parallel_count": 4
}
```

## 响应示例

```json
{
  "parallel_groups": [
    {
      "parallel_group_id": "PG01",
      "count": 3,
      "total_area": 7.5,
      "start": "X1:1",
      "end": "X2:1",
      "label": "3×2.50 mm²",
      "compliant": true,
      "notes": [
        "符合并线规则：3根导线，红色颜色，2.50mm²截面积",
        "属性一致：电压等级:220V, 屏蔽:否"
      ]
    },
    {
      "parallel_group_id": "PG02",
      "count": 2,
      "total_area": 3.0,
      "start": "X1:2",
      "end": "X3:1",
      "label": "2×1.50 mm²",
      "compliant": true,
      "notes": [
        "符合并线规则：2根导线，蓝色颜色，1.50mm²截面积",
        "属性一致：电压等级:24V, 屏蔽:是"
      ]
    }
  ],
  "total_groups": 2,
  "total_wires_analyzed": 5
}
```

## 合并规则

1. **分组键**：按【起点】、【终点】、【颜色】、【截面积】四个维度进行分组
2. **并线条件**：
   - 组内导线数量 ≥ min_parallel_count
   - 所有导线属性完全一致（properties 键值对完全匹配）
3. **合规判断**：
   - 并线数量 ≥ 2 才允许标注
   - 若截面积不同，不合并
   - 若颜色不同，不合并
   - 并线数量超过 max_parallel_count 时，标记为不合规

## 前端页面使用

启动前端项目后，访问 `/wire-analysis` 路径即可使用图形界面进行导线分析。
