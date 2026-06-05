from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from automation_scheduler.ncaaf_free_open_exhaustion import run_ncaaf_final_free_open_exhaustion


ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def ncaaf_artifacts() -> dict[str, Any]:
    reports = ROOT / "reports"
    final_path = reports / "NCAAF_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.json"
    if not final_path.exists():
        run_ncaaf_final_free_open_exhaustion()
    final_report = _read_json(final_path)
    return {
        "final_report": final_report,
        "architecture": _read_json(reports / "NCAAF_ARCHITECTURE_INVENTORY.json"),
        "source_ledger": _read_json(reports / "NCAAF_FREE_VS_PAID_SOURCE_LEDGER.json"),
        "candidate_inventory": _read_json(reports / "NCAAF_CANDIDATE_SOURCE_POLICY_INVENTORY.json"),
        "policy_matrix": _read_json(reports / "NCAAF_SOURCE_POLICY_MATRIX.json"),
        "sample_report": _read_json(reports / "NCAAF_SAFE_SOURCE_SAMPLE_REPORT.json"),
        "sample_verification": _read_json(reports / "NCAAF_TARGETED_SAMPLE_VERIFICATION_RESULTS.json"),
        "backfill": _read_json(reports / "NCAAF_LOADER_READY_BACKFILL_REPORT.json"),
        "schema": _read_json(reports / "NCAAF_SCHEMA_EXPANSION_REPORT.json"),
        "oxylabs_schema": _read_json(reports / "NCAAF_OXYLABS_SCHEMA_EXPANSION_REPORT.json"),
        "audit": _read_json(reports / "NCAAF_OXYLABS_SOURCE_EXHAUSTION_LOG.json"),
        "reclassification": _read_json(reports / "NCAAF_OXYLABS_RECLASSIFICATION_REPORT.json"),
        "paid_matrix": _read_json(reports / "NCAAF_PAID_DATA_REQUIREMENT_MATRIX.json"),
        "readiness": _read_json(reports / "NCAAF_DATA_CALIBRATION_READINESS_REPORT.json"),
        "certificate": _read_json(reports / "NCAAF_FREE_OPEN_EXHAUSTION_CERTIFICATE.json"),
        "manual_template_path": ROOT / "data" / "manual_import_templates" / "ncaaf_remaining_fields_template.csv",
        "manual_docs_path": ROOT / "docs" / "MANUAL_IMPORT_TEMPLATES_NCAAF.md",
        "policy_docs_path": ROOT / "docs" / "NCAAF_SOURCE_POLICY_REVIEW.md",
    }
