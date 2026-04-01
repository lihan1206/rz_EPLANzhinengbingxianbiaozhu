"""
EPLAN智能并线标注系统 - 服务模块
"""

from app.services.wire_merger import (
    WireMerger,
    WireMergerConfig,
    Wire,
    ParallelGroup,
    MergeResult,
    merge_wires_from_csv,
    merge_wires_from_list,
)

from app.services.wire_merger_db import WireMergerRepository

__all__ = [
    "WireMerger",
    "WireMergerConfig",
    "Wire",
    "ParallelGroup",
    "MergeResult",
    "WireMergerRepository",
    "merge_wires_from_csv",
    "merge_wires_from_list",
]
