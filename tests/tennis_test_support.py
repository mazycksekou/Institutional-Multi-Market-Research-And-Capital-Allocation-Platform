from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from automation_scheduler.tennis_free_open_exhaustion import run_tennis_final_free_open_exhaustion


REPORT_ROOT = Path("reports")


def _load_json(name: str) -> dict:
    path = REPORT_ROOT / name
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def tennis_artifacts() -> dict[str, dict]:
    run_tennis_final_free_open_exhaustion()
    return {
        "architecture_inventory": _load_json("TENNIS_ARCHITECTURE_INVENTORY.json"),
        "source_ledger": _load_json("TENNIS_FREE_VS_PAID_SOURCE_LEDGER.json"),
        "candidate_inventory": _load_json("TENNIS_CANDIDATE_SOURCE_POLICY_INVENTORY.json"),
        "policy_matrix": _load_json("TENNIS_SOURCE_POLICY_MATRIX.json"),
        "safe_sample_report": _load_json("TENNIS_SAFE_SOURCE_SAMPLE_REPORT.json"),
        "sample_verification": _load_json("TENNIS_TARGETED_SAMPLE_VERIFICATION_RESULTS.json"),
        "loader_backfill": _load_json("TENNIS_LOADER_READY_BACKFILL_REPORT.json"),
        "schema_report": _load_json("TENNIS_SCHEMA_EXPANSION_REPORT.json"),
        "oxylabs_schema_report": _load_json("TENNIS_OXYLABS_SCHEMA_EXPANSION_REPORT.json"),
        "audit_report": _load_json("TENNIS_OXYLABS_SOURCE_EXHAUSTION_LOG.json"),
        "reclassification_report": _load_json("TENNIS_OXYLABS_RECLASSIFICATION_REPORT.json"),
        "paid_matrix": _load_json("TENNIS_PAID_DATA_REQUIREMENT_MATRIX.json"),
        "readiness_report": _load_json("TENNIS_DATA_CALIBRATION_READINESS_REPORT.json"),
        "certificate": _load_json("TENNIS_FREE_OPEN_EXHAUSTION_CERTIFICATE.json"),
        "final_report": _load_json("TENNIS_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.json"),
    }
