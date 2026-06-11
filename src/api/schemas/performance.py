from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class PerformanceBacktestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    model_id: str = Field(min_length=1, max_length=120)
    historical_rows_path: Optional[str] = None
    rows: Optional[list[dict[str, Any]]] = None
    dry_run: bool = True
