from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .mlb_completion_report import build_mlb_completion_report, write_mlb_completion_report
from .mlb_cutoff_date_features import build_cutoff_feature_report, write_cutoff_feature_report
from .mlb_open_data_backfill import build_mlb_open_data_backfill_report, write_mlb_open_data_backfill_report
from .mlb_open_data_field_catalog import build_mlb_open_data_field_catalog, write_mlb_open_data_field_catalog
from .mlb_open_data_feature_builders import build_mlb_feature_builder_report, write_mlb_feature_builder_report
from .mlb_open_data_feature_readiness import build_mlb_feature_readiness_report, write_mlb_feature_readiness_report
from .mlb_open_data_sources import build_mlb_open_data_source_report, write_mlb_open_data_source_report
from .mlb_open_data_source_exhaustion import build_source_exhaustion_report, write_source_exhaustion_report
from .mlb_structured_seed_adapters import build_mlb_structured_seed_adapter_report
from .mlb_structured_seed_sources import build_mlb_structured_seed_source_report, write_mlb_structured_seed_source_report
from .scheduler_config import utc_now_iso


def _default_cutoff_context(base: Path) -> dict[str, Any]:
    report = build_mlb_open_data_backfill_report(mode="coverage_report", base_data_dir=base)
    seasons: list[str] = []
    for row in report.get("coverage_rows") or []:
        for season in row.get("seasons_available") or []:
            if str(season).strip():
                seasons.append(str(season))
    numeric = sorted({int(season) for season in seasons if str(season).isdigit()})
    season = str(numeric[-1]) if numeric else (sorted(set(seasons))[-1] if seasons else "2025")
    cutoff_date = f"{season}-12-31" if str(season).isdigit() else utc_now_iso()[:10]
    return {
        "season": season,
        "cutoff_date": cutoff_date,
        "include_postseason": False,
        "allow_cutoff_sensitive_fields": False,
    }


def run_mlb_completion_backfill(
    *,
    base_data_dir: str | Path | None = None,
    run_mode: str = "open_free_mode",
    allow_oxylabs: bool = False,
    allow_paid_retrieval: bool = False,
    allow_structured_seed: bool = True,
    allow_manual_import: bool = True,
    season: str | int | None = None,
    cutoff_date: str | None = None,
    team: str | None = None,
    player_id: str | None = None,
    include_postseason: bool = False,
    allow_cutoff_sensitive_fields: bool = False,
    max_entities: int = 32,
    max_requests: int = 96,
    persist: bool = True,
) -> dict[str, Any]:
    base = Path(base_data_dir) if base_data_dir is not None else None
    open_source_report = build_mlb_open_data_source_report(base_data_dir=base)
    open_source_paths = write_mlb_open_data_source_report(open_source_report, base_data_dir=base) if persist else {}

    field_catalog = build_mlb_open_data_field_catalog(base_data_dir=base)
    field_catalog_paths = write_mlb_open_data_field_catalog(field_catalog, base_data_dir=base) if persist else {}

    source_exhaustion = build_source_exhaustion_report(base_data_dir=base)
    source_exhaustion_paths = write_source_exhaustion_report(source_exhaustion, base_data_dir=base) if persist else {}

    open_backfill = build_mlb_open_data_backfill_report(mode="coverage_report", base_data_dir=base)
    open_backfill_paths = write_mlb_open_data_backfill_report(open_backfill, base_data_dir=base) if persist else {}

    feature_builders = build_mlb_feature_builder_report(base_data_dir=base)
    feature_builder_paths = write_mlb_feature_builder_report(feature_builders, base_data_dir=base) if persist else {}

    feature_readiness = build_mlb_feature_readiness_report(base_data_dir=base)
    feature_readiness_paths = write_mlb_feature_readiness_report(feature_readiness, base_data_dir=base) if persist else {}

    structured_seed_sources = build_mlb_structured_seed_source_report(base_data_dir=base)
    structured_seed_paths = write_mlb_structured_seed_source_report(structured_seed_sources, base_data_dir=base) if persist else {}
    structured_seed_adapter = build_mlb_structured_seed_adapter_report(base_data_dir=base)

    cutoff_context = _default_cutoff_context(base or Path("."))
    cutoff_context.update(
        {
            "season": str(season) if season is not None else cutoff_context["season"],
            "cutoff_date": cutoff_date or cutoff_context["cutoff_date"],
            "include_postseason": bool(include_postseason),
            "allow_cutoff_sensitive_fields": bool(allow_cutoff_sensitive_fields),
            "team": team,
            "player_id": player_id,
        }
    )
    cutoff_report = build_cutoff_feature_report(base_data_dir=base, **cutoff_context)
    cutoff_paths = write_cutoff_feature_report(cutoff_report, base_data_dir=base) if persist else {}

    completion = build_mlb_completion_report(
        base_data_dir=base,
        run_mode=run_mode,
        allow_oxylabs=allow_oxylabs,
        allow_paid_retrieval=allow_paid_retrieval,
        season=cutoff_context["season"],
        cutoff_date=cutoff_context["cutoff_date"],
        team=team,
        player_id=player_id,
        include_postseason=include_postseason,
        allow_cutoff_sensitive_fields=allow_cutoff_sensitive_fields,
    )
    completion_paths = write_mlb_completion_report(completion) if persist else {}
    return {
        "ok": True,
        "status": "ok",
        "created_at": utc_now_iso(),
        "open_source_report": open_source_report,
        "field_catalog": field_catalog,
        "source_exhaustion": source_exhaustion,
        "open_backfill": open_backfill,
        "feature_builders": feature_builders,
        "feature_readiness": feature_readiness,
        "structured_seed_sources": structured_seed_sources,
        "structured_seed_adapter": structured_seed_adapter,
        "cutoff_report": cutoff_report,
        "completion_report": completion,
        "paths": {
            **open_source_paths,
            **field_catalog_paths,
            **source_exhaustion_paths,
            **open_backfill_paths,
            **feature_builder_paths,
            **feature_readiness_paths,
            **structured_seed_paths,
            **cutoff_paths,
            **completion_paths,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-data-dir", default=None)
    parser.add_argument("--run-mode", default="open_free_mode", choices=["open_free_mode", "approved_paid_mode"])
    parser.add_argument("--allow-oxylabs", action="store_true")
    parser.add_argument("--allow-paid-retrieval", action="store_true")
    parser.add_argument("--allow-structured-seed", action="store_true")
    parser.add_argument("--allow-manual-import", action="store_true")
    parser.add_argument("--season", default=None)
    parser.add_argument("--cutoff-date", default=None)
    parser.add_argument("--team", default=None)
    parser.add_argument("--player-id", default=None)
    parser.add_argument("--include-postseason", action="store_true")
    parser.add_argument("--allow-cutoff-sensitive-fields", action="store_true")
    parser.add_argument("--max-entities", type=int, default=32)
    parser.add_argument("--max-requests", type=int, default=96)
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args(argv)
    run_mode = "approved_paid_mode" if args.allow_oxylabs and args.allow_paid_retrieval and args.run_mode == "open_free_mode" else args.run_mode
    report = run_mlb_completion_backfill(
        base_data_dir=args.base_data_dir,
        run_mode=run_mode,
        allow_oxylabs=args.allow_oxylabs,
        allow_paid_retrieval=args.allow_paid_retrieval,
        allow_structured_seed=args.allow_structured_seed or True,
        allow_manual_import=args.allow_manual_import or True,
        season=args.season,
        cutoff_date=args.cutoff_date,
        team=args.team,
        player_id=args.player_id,
        include_postseason=args.include_postseason,
        allow_cutoff_sensitive_fields=args.allow_cutoff_sensitive_fields,
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
                "cutoff_safe_feature_count": report.get("completion_report", {}).get("cutoff_safe_feature_count"),
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "secrets_included": False,
                "enabled_source_count": 0,
                "paid_source_enabled_count": report.get("completion_report", {}).get("paid_source_enabled_count", 0),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
