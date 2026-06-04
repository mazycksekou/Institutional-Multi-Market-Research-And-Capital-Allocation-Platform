from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .nfl_coaching_adapters import adapter_by_id as coaching_adapter_by_id
from .nfl_coaching_adapters import build_nfl_coaching_ingestion_report, load_validated_coaching_rows
from .nfl_coaching_feature_builders import build_nfl_coaching_acquisition_report, build_nfl_coaching_feature_report
from .nfl_coaching_sources import build_nfl_coaching_source_report
from .nfl_completion_report import build_nfl_completion_report, write_nfl_completion_report
from .nfl_historical_pattern_lab import build_nfl_historical_pattern_lab_report
from .nfl_open_data_backfill import build_nfl_open_data_backfill_report, write_nfl_open_data_backfill_report
from .nfl_open_data_feature_builders import build_nfl_feature_builder_report, write_nfl_feature_builder_report
from .nfl_open_data_feature_readiness import build_nfl_feature_readiness_report, write_nfl_feature_readiness_report
from .nfl_open_data_source_exhaustion import build_nfl_source_exhaustion_report, write_nfl_source_exhaustion_report
from .nfl_open_data_sources import build_nfl_open_data_source_report, write_nfl_open_data_source_report
from .scheduler_config import utc_now_iso


def run_nfl_completion_backfill(
    *,
    base_data_dir: str | Path | None = None,
    allow_structured_seed: bool = True,
    allow_manual_import: bool = True,
    max_entities: int = 32,
    max_requests: int = 96,
    persist: bool = True,
) -> dict[str, Any]:
    base = base_data_dir
    open_source_report = build_nfl_open_data_source_report(base_data_dir=base)
    open_source_paths = write_nfl_open_data_source_report(open_source_report, base_data_dir=base) if persist else {}
    source_exhaustion = build_nfl_source_exhaustion_report(base_data_dir=base)
    source_exhaustion_paths = write_nfl_source_exhaustion_report(source_exhaustion, base_data_dir=base) if persist else {}

    open_backfill = build_nfl_open_data_backfill_report(mode="coverage_report", base_data_dir=base)
    open_backfill_paths = write_nfl_open_data_backfill_report(open_backfill, base_data_dir=base) if persist else {}

    feature_builders = build_nfl_feature_builder_report(base_data_dir=base)
    feature_builder_paths = write_nfl_feature_builder_report(feature_builders, base_data_dir=base) if persist else {}
    feature_readiness = build_nfl_feature_readiness_report(base_data_dir=base)
    feature_readiness_paths = write_nfl_feature_readiness_report(feature_readiness, base_data_dir=base) if persist else {}

    coaching_source_report = build_nfl_coaching_source_report(base_data_dir=base)
    coaching_source_paths = {}
    if persist:
        from .nfl_coaching_sources import write_nfl_coaching_source_report

        coaching_source_paths = write_nfl_coaching_source_report(coaching_source_report, base_data_dir=base)

    coaching_acquisition = build_nfl_coaching_acquisition_report(allow_manual_import=allow_manual_import, base_data_dir=base)
    if persist:
        from .nfl_coaching_feature_builders import write_nfl_coaching_acquisition_report

        coaching_acquisition_paths = write_nfl_coaching_acquisition_report(coaching_acquisition, base_data_dir=base)
    else:
        coaching_acquisition_paths = {}

    coaching_seed = coaching_adapter_by_id("wikidata_entity_api")
    if coaching_seed is not None:
        coaching_seed.run_entity_seed_import(
            allow_structured_seed=allow_structured_seed,
            max_entities=max_entities,
            max_requests=max_requests,
            persist_preview=persist,
            base_data_dir=base,
        )

    coaching_feature_report = build_nfl_coaching_feature_report(base_data_dir=base)
    if persist:
        from .nfl_coaching_feature_builders import write_nfl_coaching_feature_report

        coaching_feature_paths = write_nfl_coaching_feature_report(coaching_feature_report, base_data_dir=base)
    else:
        coaching_feature_paths = {}

    coaching_ingestion = build_nfl_coaching_ingestion_report(base_data_dir=base)

    pattern_lab = build_nfl_historical_pattern_lab_report(base_data_dir=base)
    completion = build_nfl_completion_report(base_data_dir=base, run_mode="open_free_mode")
    completion_paths = write_nfl_completion_report(completion) if persist else {}
    return {
        "ok": True,
        "status": "ok",
        "created_at": utc_now_iso(),
        "open_source_report": open_source_report,
        "source_exhaustion": source_exhaustion,
        "open_backfill": open_backfill,
        "feature_builders": feature_builders,
        "feature_readiness": feature_readiness,
        "coaching_source_report": coaching_source_report,
        "coaching_acquisition": coaching_acquisition,
        "coaching_feature_report": coaching_feature_report,
        "coaching_ingestion": coaching_ingestion,
        "pattern_lab": pattern_lab,
        "completion_report": completion,
        "paths": {
            **open_source_paths,
            **source_exhaustion_paths,
            **open_backfill_paths,
            **feature_builder_paths,
            **feature_readiness_paths,
            **coaching_source_paths,
            **coaching_acquisition_paths,
            **coaching_feature_paths,
            **completion_paths,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-data-dir", default=None)
    parser.add_argument("--no-persist", action="store_true")
    parser.add_argument("--allow-structured-seed", action="store_true")
    parser.add_argument("--allow-manual-import", action="store_true")
    parser.add_argument("--max-entities", type=int, default=32)
    parser.add_argument("--max-requests", type=int, default=96)
    args = parser.parse_args(argv)
    report = run_nfl_completion_backfill(
        base_data_dir=args.base_data_dir,
        allow_structured_seed=args.allow_structured_seed or True,
        allow_manual_import=args.allow_manual_import or True,
        max_entities=args.max_entities,
        max_requests=args.max_requests,
        persist=not args.no_persist,
    )
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "completion_record_count": report.get("completion_report", {}).get("record_count_total"),
                "feature_groups_built": report.get("completion_report", {}).get("feature_groups_built"),
                "feature_groups_blocked": report.get("completion_report", {}).get("feature_groups_blocked"),
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "secrets_included": False,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
