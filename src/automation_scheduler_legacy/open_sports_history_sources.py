from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from src.services.scheduler_config import sanitize_filename, utc_now_iso


OPEN_SPORTS_HISTORY_SCHEMA_VERSION = "open_sports_history_sources_v1"

SAFETY_FIELDS = {
    "provider_write": False,
    "execution_allowed": False,
    "execution_allowed_count": 0,
    "live_execution_enabled": False,
    "auto_execution_enabled": False,
    "kalshi_order_execution_enabled": False,
    "sportsbook_bet_execution_enabled": False,
    "broker_order_execution_enabled": False,
    "crypto_trade_execution_enabled": False,
    "stock_trade_execution_enabled": False,
    "actual_orders_submitted": 0,
    "actual_bets_submitted": 0,
    "actual_trades_submitted": 0,
    "actual_crypto_swaps_submitted": 0,
    "raw_payload_included": False,
    "secrets_included": False,
    "enabled_source_count": 0,
    "paid_source_enabled_count": 0,
}


def _source(
    *,
    source_id: str,
    module: str,
    source_name: str,
    source_kind: str,
    source_access_type: str,
    current_phase_allowed: bool,
    future_paid_candidate: bool,
    requires_budget_approval: bool,
    approval_status: str,
    enabled: bool = False,
    supports_direct_download: bool = False,
    supports_local_file_import: bool = True,
    supports_manual_export: bool = False,
    supports_api_key: bool = False,
    supports_bulk_backfill: bool = False,
    supports_scheduled_backfill: bool = False,
    terms_review_required: bool = False,
    target_coverage_years: int = 10,
    available_start_year: int | None = None,
    available_end_year: int | None = None,
    recommended_use: str = "compact local historical result preview rows",
    blocked_reason: str | None = "source_disabled",
    max_records_default: int = 25,
    max_records_hard_cap: int = 500,
    bulk_backfill_allowed_after_smoke: bool = False,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "module": module,
        "source_name": source_name,
        "source_kind": source_kind,
        "source_access_type": source_access_type,
        "current_phase_allowed": bool(current_phase_allowed),
        "future_paid_candidate": bool(future_paid_candidate),
        "requires_budget_approval": bool(requires_budget_approval),
        "approval_status": approval_status,
        "enabled": bool(enabled),
        "supports_direct_download": bool(supports_direct_download),
        "supports_local_file_import": bool(supports_local_file_import),
        "supports_manual_export": bool(supports_manual_export),
        "supports_api_key": bool(supports_api_key),
        "supports_bulk_backfill": bool(supports_bulk_backfill),
        "supports_scheduled_backfill": bool(supports_scheduled_backfill),
        "terms_review_required": bool(terms_review_required),
        "target_coverage_years": int(target_coverage_years),
        "available_start_year": available_start_year,
        "available_end_year": available_end_year,
        "recommended_use": recommended_use,
        "blocked_reason": blocked_reason,
        "max_records_default": int(max_records_default),
        "max_records_hard_cap": int(max_records_hard_cap),
        "bulk_backfill_allowed_after_smoke": bool(bulk_backfill_allowed_after_smoke),
        "raw_payload_persistence_allowed": False,
        "provider_write": False,
        "execution_allowed": False,
    }


def open_sports_history_sources() -> list[dict[str, Any]]:
    sportsdataverse_common = {
        "source_kind": "open_package_or_public_endpoint",
        "source_access_type": "open_package_or_public_endpoint",
        "current_phase_allowed": True,
        "future_paid_candidate": False,
        "requires_budget_approval": False,
        "approval_status": "needs_tiny_verification",
        "supports_direct_download": False,
        "supports_local_file_import": True,
        "supports_api_key": False,
        "supports_bulk_backfill": True,
        "supports_scheduled_backfill": True,
        "terms_review_required": True,
        "target_coverage_years": 10,
        "blocked_reason": None,
        "bulk_backfill_allowed_after_smoke": True,
        "recommended_use": "second-wave open-source lane; verify tiny parser/source contract before bulk backfill",
    }
    research_common = {
        "source_kind": "research_lane",
        "source_access_type": "research_required",
        "current_phase_allowed": False,
        "future_paid_candidate": False,
        "requires_budget_approval": False,
        "approval_status": "research_required",
        "supports_direct_download": False,
        "supports_local_file_import": True,
        "supports_manual_export": True,
        "supports_api_key": False,
        "supports_bulk_backfill": False,
        "supports_scheduled_backfill": False,
        "terms_review_required": True,
        "target_coverage_years": 10,
        "blocked_reason": "open_structured_source_not_confirmed",
        "recommended_use": "research/manual/import lane until a clearly approved open structured source is confirmed",
    }
    return [
        _source(
            source_id="retrosheet_mlb",
            module="baseball_mlb",
            source_name="Retrosheet MLB",
            source_kind="open_historical_dataset",
            source_access_type="open_csv_download",
            current_phase_allowed=True,
            future_paid_candidate=False,
            requires_budget_approval=False,
            approval_status="approved_open_historical",
            supports_direct_download=True,
            supports_local_file_import=True,
            supports_bulk_backfill=True,
            supports_scheduled_backfill=True,
            terms_review_required=False,
            target_coverage_years=10,
            available_start_year=None,
            available_end_year=None,
            bulk_backfill_allowed_after_smoke=True,
            recommended_use="MLB game-level historical scores/results from local CSV or tiny approved download",
        ),
        _source(
            source_id="nflverse_nfl",
            module="americanfootball_nfl",
            source_name="nflverse NFL",
            source_kind="open_historical_dataset",
            source_access_type="open_data_release",
            current_phase_allowed=True,
            future_paid_candidate=False,
            requires_budget_approval=False,
            approval_status="approved_open_historical",
            supports_direct_download=True,
            supports_local_file_import=True,
            supports_bulk_backfill=True,
            supports_scheduled_backfill=True,
            terms_review_required=False,
            target_coverage_years=10,
            available_start_year=None,
            available_end_year=None,
            bulk_backfill_allowed_after_smoke=True,
            recommended_use="NFL schedule/game-level historical scores/results from local CSV or tiny approved download",
        ),
        _source(
            source_id="football_data_uk_soccer",
            module="soccer",
            source_name="football-data.co.uk Soccer CSV",
            source_kind="open_historical_dataset",
            source_access_type="open_csv_download",
            current_phase_allowed=True,
            future_paid_candidate=False,
            requires_budget_approval=False,
            approval_status="needs_tiny_verification",
            supports_direct_download=True,
            supports_local_file_import=True,
            supports_bulk_backfill=True,
            supports_scheduled_backfill=True,
            terms_review_required=True,
            target_coverage_years=10,
            bulk_backfill_allowed_after_smoke=True,
            recommended_use="soccer historical result lane after tiny CSV verification and terms review",
        ),
        _source(
            source_id="jeff_sackmann_tennis_atp",
            module="tennis",
            source_name="Jeff Sackmann ATP Tennis Match Data",
            source_kind="open_historical_dataset",
            source_access_type="open_csv_release",
            current_phase_allowed=True,
            future_paid_candidate=False,
            requires_budget_approval=False,
            approval_status="needs_tiny_verification",
            supports_direct_download=True,
            supports_local_file_import=True,
            supports_bulk_backfill=True,
            supports_scheduled_backfill=True,
            terms_review_required=True,
            target_coverage_years=10,
            bulk_backfill_allowed_after_smoke=True,
            recommended_use="ATP match-result lane after tiny CSV verification and terms review",
        ),
        _source(
            source_id="jeff_sackmann_tennis_wta",
            module="tennis",
            source_name="Jeff Sackmann WTA Tennis Match Data",
            source_kind="open_historical_dataset",
            source_access_type="open_csv_release",
            current_phase_allowed=True,
            future_paid_candidate=False,
            requires_budget_approval=False,
            approval_status="needs_tiny_verification",
            supports_direct_download=True,
            supports_local_file_import=True,
            supports_bulk_backfill=True,
            supports_scheduled_backfill=True,
            terms_review_required=True,
            target_coverage_years=10,
            bulk_backfill_allowed_after_smoke=True,
            recommended_use="WTA match-result lane after tiny CSV verification and terms review",
        ),
        _source(
            source_id="sportsdataverse_ncaaf",
            module="americanfootball_ncaaf",
            source_name="SportsDataverse / CFBD NCAAF",
            **sportsdataverse_common,
        ),
        _source(
            source_id="sportsdataverse_ncaab",
            module="basketball_ncaab",
            source_name="SportsDataverse NCAAB",
            **sportsdataverse_common,
        ),
        _source(
            source_id="sportsdataverse_ncaaw",
            module="basketball_ncaaw",
            source_name="SportsDataverse NCAAW",
            **sportsdataverse_common,
        ),
        _source(
            source_id="sportsdataverse_wnba",
            module="basketball_wnba",
            source_name="SportsDataverse WNBA",
            **sportsdataverse_common,
        ),
        _source(
            source_id="sportsdataverse_nhl",
            module="icehockey_nhl",
            source_name="SportsDataverse NHL",
            **sportsdataverse_common,
        ),
        _source(
            source_id="sportsdataverse_nba_or_hoopr",
            module="basketball_nba",
            source_name="SportsDataverse NBA / hoopR",
            **sportsdataverse_common,
        ),
        _source(
            source_id="ufc_mma_research_lane",
            module="ufc_mma",
            source_name="UFC/MMA Research Lane",
            **research_common,
        ),
        _source(
            source_id="boxing_research_lane",
            module="boxing",
            source_name="Boxing Research Lane",
            **research_common,
        ),
        _source(
            source_id="golf_research_lane",
            module="golf",
            source_name="Golf Research Lane",
            **research_common,
        ),
        _source(
            source_id="sports_reference_manual_export",
            module="sports_reference",
            source_name="Sports Reference Manual Export",
            source_kind="manual_export",
            source_access_type="manual_export_terms_review",
            current_phase_allowed=False,
            future_paid_candidate=False,
            requires_budget_approval=False,
            approval_status="terms_review_required",
            supports_direct_download=False,
            supports_local_file_import=True,
            supports_manual_export=True,
            supports_api_key=False,
            supports_bulk_backfill=False,
            supports_scheduled_backfill=False,
            terms_review_required=True,
            target_coverage_years=10,
            recommended_use="manual export only after terms review; never automated scraping",
            blocked_reason="manual_export_only_no_scraping",
        ),
    ]


def source_by_id(source_id: str) -> dict[str, Any] | None:
    for source in open_sports_history_sources():
        if source["source_id"] == source_id:
            return source
    return None


def _report_root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "open_sports_history"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _rel(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def build_open_sports_history_source_report(
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    sources = open_sports_history_sources()
    counts = Counter(str(source.get("approval_status") or "unknown") for source in sources)
    enabled_count = sum(1 for source in sources if source.get("enabled"))
    paid_enabled = sum(1 for source in sources if source.get("enabled") and source.get("requires_budget_approval"))
    terms_review = [source["source_id"] for source in sources if source.get("terms_review_required")]
    approved = [source["source_id"] for source in sources if source.get("approval_status") == "approved_open_historical"]
    manual = [source["source_id"] for source in sources if source.get("source_kind") == "manual_export"]
    ok = enabled_count == 0 and paid_enabled == 0
    return {
        **SAFETY_FIELDS,
        "ok": ok,
        "status": "ok" if ok else "blocked",
        "schema_version": OPEN_SPORTS_HISTORY_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"open_sports_history_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "runtime_data_dir": str(resolve_base_data_dir(base_data_dir)),
        "sources_registered": len(sources),
        "sources_current_phase_allowed": sum(1 for source in sources if source.get("current_phase_allowed")),
        "sources_enabled": enabled_count,
        "enabled_source_count": enabled_count,
        "paid_source_enabled_count": paid_enabled,
        "terms_review_required_sources": terms_review,
        "approved_open_historical_sources": approved,
        "manual_export_sources": manual,
        "approval_status_counts": dict(sorted(counts.items())),
        "sources": sources,
        "downloads_attempted": 0,
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "recommended_next_action": "import a tiny local Retrosheet or nflverse CSV fixture with dry-run preview",
        "storage_health": get_storage_health(),
    }


def render_open_sports_history_source_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Open Sports History Sources",
        "",
        f"1. sources_registered: {report.get('sources_registered')}",
        f"2. current_phase_allowed: {report.get('sources_current_phase_allowed')}",
        f"3. enabled_source_count: {report.get('enabled_source_count')}",
        f"4. paid_source_enabled_count: {report.get('paid_source_enabled_count')}",
        f"5. approved_open_historical_sources: {', '.join(report.get('approved_open_historical_sources') or [])}",
        f"6. terms_review_required_sources: {', '.join(report.get('terms_review_required_sources') or [])}",
        f"7. manual_export_sources: {', '.join(report.get('manual_export_sources') or [])}",
        f"8. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Sources",
    ]
    for source in report.get("sources") or []:
        lines.append(
            f"- {source.get('source_id')}: {source.get('approval_status')}; enabled={str(source.get('enabled')).lower()}; access={source.get('source_access_type')}; blocked_reason={source.get('blocked_reason')}"
        )
    return "\n".join(lines) + "\n"


def write_open_sports_history_source_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _report_root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    day = created[:10]
    run_id = sanitize_filename(str(report.get("run_id") or f"open_sports_history_{created}_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    daily_json = root / "daily" / f"{day}.json"
    daily_md = root / "daily" / f"{day}.md"
    paths = {
        "latest_json_path": _rel(latest_json, base_data_dir),
        "latest_markdown_path": _rel(latest_md, base_data_dir),
        "item_json_path": _rel(item_json, base_data_dir),
        "item_markdown_path": _rel(item_md, base_data_dir),
        "daily_json_path": _rel(daily_json, base_data_dir),
        "daily_markdown_path": _rel(daily_md, base_data_dir),
    }
    payload = {**SAFETY_FIELDS, **report, **paths, "raw_payload_included": False, "secrets_included": False}
    markdown = render_open_sports_history_source_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    _atomic_write_json(daily_json, payload)
    _atomic_write_text(daily_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_open_sports_history_source_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_open_sports_history_source_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "status": report["status"],
                "run_id": report["run_id"],
                "sources_registered": report["sources_registered"],
                "sources_current_phase_allowed": report["sources_current_phase_allowed"],
                "sources_enabled": report["sources_enabled"],
                "enabled_source_count": report["enabled_source_count"],
                "paid_source_enabled_count": report["paid_source_enabled_count"],
                "terms_review_required_sources": report["terms_review_required_sources"],
                "approved_open_historical_sources": report["approved_open_historical_sources"],
                "manual_export_sources": report["manual_export_sources"],
                "downloads_attempted": 0,
                "provider_calls_attempted": 0,
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "secrets_included": False,
                "recommended_next_action": report["recommended_next_action"],
                "latest_json_path": paths.get("latest_json_path"),
                "latest_markdown_path": paths.get("latest_markdown_path"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
