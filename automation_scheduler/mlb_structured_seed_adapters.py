from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from .mlb_open_data_adapters import WikidataMlbSeedAdapter as _WikidataMlbSeedAdapter
from .mlb_open_data_adapters import WikipediaMlbSeedAdapter as _WikipediaMlbSeedAdapter
from .mlb_open_data_adapters import adapter_by_id as _adapter_by_id
from .mlb_open_data_sources import source_by_id as _open_source_by_id
from .mlb_structured_seed_sources import mlb_structured_seed_sources, source_by_id


WikidataMlbSeedAdapter = _WikidataMlbSeedAdapter
WikipediaMlbSeedAdapter = _WikipediaMlbSeedAdapter


def adapter_by_id(source_id: str):
    source = source_by_id(source_id) or _open_source_by_id(source_id)
    if source is None:
        return None
    if source["source_id"] == "wikidata_mlb_seed":
        return WikidataMlbSeedAdapter(source)
    if source["source_id"] == "wikipedia_mlb_seed":
        return WikipediaMlbSeedAdapter(source)
    return _adapter_by_id(source_id)


def build_mlb_structured_seed_adapter_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    sources = mlb_structured_seed_sources()
    used = []
    blocked = []
    for source in sources:
        adapter = adapter_by_id(source["source_id"])
        if adapter is None:
            continue
        metadata = adapter.run_metadata_check()
        if metadata.get("ok") and metadata.get("status") != "blocked" and source.get("current_phase_allowed"):
            used.append(source["source_id"])
        else:
            blocked.append({"source_id": source["source_id"], "blocker": metadata.get("blocked_reason")})
    return {
        "ok": True,
        "status": "ok",
        "structured_seed_sources_checked": len(sources),
        "structured_seed_sources_used": used,
        "structured_seed_sources_blocked": blocked,
        "wikidata_license_status": "cc0",
        "wikipedia_parses_article_prose": False,
        "wikipedia_attribution_required": True,
        "raw_html_persisted": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "provider_write": False,
        "execution_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", default="wikidata_mlb_seed")
    parser.add_argument("--gate", default="metadata_check")
    parser.add_argument("--allow-structured-seed", action="store_true")
    parser.add_argument("--max-records", type=int, default=25)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    adapter = adapter_by_id(args.source_id)
    if adapter is None:
        print(json.dumps({"ok": False, "status": "blocked", "blocked_reason": "unsupported_source"}, indent=2, sort_keys=True))
        return 1
    if args.gate == "metadata_check":
        report = adapter.run_metadata_check()
    elif args.gate == "tiny_sample":
        report = adapter.run_tiny_sample(allow_structured_seed=args.allow_structured_seed, max_records=args.max_records)
    elif args.gate == "structured_seed_import":
        if hasattr(adapter, "run_structured_seed_import"):
            report = adapter.run_structured_seed_import(allow_structured_seed=args.allow_structured_seed, max_records=args.max_records)
        else:
            report = adapter.run_metadata_check()
    elif args.gate == "coverage_report":
        report = build_mlb_structured_seed_adapter_report()
    else:
        report = adapter.run_metadata_check()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
