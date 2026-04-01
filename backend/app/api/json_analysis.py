"""
EPLAN 导线并线分析 API - JSON 直接输入版本
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.json_parallel_analysis import (
    AnalysisConfig,
    AnalysisResult,
    analyze_wires_json,
)

router = APIRouter(prefix="/json-analysis", tags=["JSON并线分析"])


class JsonAnalyzeRequest(BaseModel):
    """JSON 分析请求"""
    wires: list[dict[str, Any]] = Field(..., description="导线数据列表")
    config: dict[str, Any] | None = Field(None, description="分析配置")


class JsonAnalyzeResponse(BaseModel):
    """JSON 分析响应"""
    success: bool
    data: AnalysisResult


from pydantic import BaseModel, Field


@router.post("/analyze", response_model=JsonAnalyzeResponse)
def analyze_json_wires(payload: JsonAnalyzeRequest):
    """
    分析 EPLAN 导线 JSON 数据，识别并线组
    
    输入示例:
    ```json
    {
        "wires": [
            {"id": "W001", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
            {"id": "W002", "start": "A1", "end": "B1", "area": 1.5, "color": "红"},
            {"id": "W003", "start": "A2", "end": "B2", "area": 2.5, "color": "蓝"}
        ],
        "config": {
            "min_parallel_count": 2,
            "max_parallel_count": 4
        }
    }
    ```
    
    输出示例:
    ```json
    {
        "success": true,
        "data": {
            "total_wires": 3,
            "parallel_groups": [
                {
                    "parallel_group_id": "PG01",
                    "count": 2,
                    "total_area": 3.0,
                    "start": "A1",
                    "end": "B1",
                    "label": "2×1.50mm²",
                    "compliant": true,
                    "color": "红",
                    "area": 1.5,
                    "wires": ["W001", "W002"],
                    "notes": ["所有属性一致，符合并线条件", "满足并线条件，共 2 根导线"]
                }
            ],
            "ungrouped_wires": ["W003"]
        }
    }
    ```
    """
    try:
        config = None
        if payload.config:
            config = AnalysisConfig(**payload.config)
        
        result = analyze_wires_json(payload.wires, config)
        
        return JsonAnalyzeResponse(
            success=True,
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"分析失败: {str(e)}")


@router.post("/analyze-raw")
def analyze_json_wires_raw(request_data: dict[str, Any]):
    """
    原始 JSON 分析接口，直接接收和返回 JSON
    
    适用于需要直接处理原始 JSON 数据的场景
    """
    try:
        wires = request_data.get("wires", [])
        config_dict = request_data.get("config")
        
        config = AnalysisConfig(**config_dict) if config_dict else None
        result = analyze_wires_json(wires, config)
        
        return {
            "success": True,
            "data": result.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"分析失败: {str(e)}")
