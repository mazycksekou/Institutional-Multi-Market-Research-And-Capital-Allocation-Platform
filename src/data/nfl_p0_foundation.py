from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.data.data_paths import get_runtime_data_path
from src.data.market_profile_contracts import MarketProfileContract, validate_market_profile_contract
from src.data.market_profile_registry import get_market_profile, register_market_profile
from src.data.validation import validate_dataset_rows
from src.storage.local_store import LocalStorageEngine, backend_available, create_local_storage_engine


NFL_P0_SCHEMA_VERSION = "src.data.nfl_p0_foundation.v1"
NFL_P0_DATASET_VERSION = "nfl_p0.v001"
NFL_P0_DATASET_NAME = "nfl_p0_foundation"
NFL_P0_SOURCE_NAME = "nfl_p0_fixture"
NFL_P0_SOURCE_TYPE = "fixture"
NFL_P0_PROVIDER = "local_fixture"
NFL_P0_MARKET = "nfl_p0"
NFL_P0_MARKET_TYPE = "foundation"
NFL_P0_ASSET_CLASS = "sports"
NFL_P0_OWNER = "src.data"
DEFAULT_NFL_P0_STORAGE_PATH = get_runtime_data_path("nfl_p0", "canonical_data.sqlite")
DEFAULT_NFL_P0_GAME_COUNT = 4
NFL_P0_PROFILE_ID = "sports:nfl"
NFL_P0_PROFILE_FAMILY = "sports"
NFL_P0_PROFILE_MARKET_SCOPE = "americanfootball_nfl"


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _normalize_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def _normalize_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: Any) -> datetime | None:
    text = _normalize_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _iso_nowish(value: datetime) -> str:
    return value.replace(microsecond=0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return f"{prefix}-{uuid.uuid5(uuid.NAMESPACE_URL, seed).hex[:16]}"


def _as_json(value: Any) -> str:
    def default(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        if hasattr(obj, "as_dict"):
            return obj.as_dict()
        if isinstance(obj, set):
            return sorted(obj)
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return str(obj)

    return json.dumps(value, default=default, ensure_ascii=False, sort_keys=True)


def _source_signature(source_name: str, source_snapshot_time: str) -> str:
    return f"{source_name}:{source_snapshot_time}"


def get_nfl_p0_market_profile() -> MarketProfileContract:
    from src.market_intelligence.market_profiles import NFL_AS_SPORTS_PROFILE_INSTANCE

    profile = get_market_profile(NFL_P0_PROFILE_ID)
    if profile is None:
        try:
            register_market_profile(NFL_AS_SPORTS_PROFILE_INSTANCE)
        except ValueError:
            pass
        profile = get_market_profile(NFL_P0_PROFILE_ID) or NFL_AS_SPORTS_PROFILE_INSTANCE
    return profile


def validate_nfl_p0_market_profile(profile: MarketProfileContract | None = None) -> dict[str, Any]:
    from src.market_intelligence.market_profiles import NFL_AS_SPORTS_PROFILE_INSTANCE

    resolved = profile or get_nfl_p0_market_profile()
    validation = validate_market_profile_contract(resolved)
    expected = NFL_AS_SPORTS_PROFILE_INSTANCE
    errors = list(validation.get("errors", []))
    warnings = list(validation.get("warnings", []))

    comparisons = (
        ("profile_id", resolved.profile_id, expected.profile_id),
        ("profile_family", resolved.profile_family, expected.profile_family),
        ("market_scope", resolved.market_scope, expected.market_scope),
        ("canonical_identifiers", resolved.canonical_identifiers, expected.canonical_identifiers),
        ("required_timestamps", resolved.required_timestamps, expected.required_timestamps),
        ("canonical_fields", resolved.canonical_fields, expected.canonical_fields),
        ("atomic_feature_groups", resolved.atomic_feature_groups, expected.atomic_feature_groups),
        ("composite_feature_groups", resolved.composite_feature_groups, expected.composite_feature_groups),
        ("validation_rules", resolved.validation_rules, expected.validation_rules),
        ("leakage_rules", resolved.leakage_rules, expected.leakage_rules),
        ("storage_requirements", resolved.storage_requirements, expected.storage_requirements),
        ("feature_store_requirements", resolved.feature_store_requirements, expected.feature_store_requirements),
        ("backtest_requirements", resolved.backtest_requirements, expected.backtest_requirements),
        ("streamlit_requirements", resolved.streamlit_requirements, expected.streamlit_requirements),
        ("research_requirements", resolved.research_requirements, expected.research_requirements),
        ("worldview_permissions", resolved.worldview_permissions, expected.worldview_permissions),
        ("paper_trading_requirements", resolved.paper_trading_requirements, expected.paper_trading_requirements),
        ("live_execution_gates", resolved.live_execution_gates, expected.live_execution_gates),
    )
    for field_name, actual, expected_value in comparisons:
        if actual != expected_value:
            errors.append(f"{field_name}: expected {expected_value!r}, got {actual!r}")

    profile_status = "ready" if not errors else "blocked"
    return {
        "ok": not errors,
        "status": profile_status,
        "profile_id": resolved.profile_id,
        "profile_family": resolved.profile_family,
        "market_scope": resolved.market_scope,
        "profile": resolved.as_dict(),
        "expected_profile": expected.as_dict(),
        "validation": {
            "ok": bool(validation.get("ok")),
            "profile_id": validation.get("profile_id"),
            "profile_family": validation.get("profile_family"),
            "errors": list(validation.get("errors", [])),
            "warnings": list(validation.get("warnings", [])),
        },
        "errors": list(dict.fromkeys(errors)),
        "warnings": warnings,
    }


def _fixture_market_label(market: str) -> str:
    return {
        "spread": "pregame_spread",
        "moneyline": "pregame_moneyline",
        "total": "pregame_total",
    }.get(market, market)


@dataclass(slots=True, frozen=True)
class NflP0TableContract:
    table_name: str
    row_id_field: str
    required_fields: tuple[str, ...]
    required_timestamps: tuple[str, ...]
    join_keys: tuple[str, ...]
    point_in_time_rules: tuple[str, ...]
    numeric_fields: tuple[str, ...]
    description: str
    market_type: str
    result_only: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "table_name", _normalize_text(self.table_name))
        object.__setattr__(self, "row_id_field", _normalize_text(self.row_id_field))
        object.__setattr__(self, "required_fields", tuple(_normalize_text(value) for value in self.required_fields if _normalize_text(value)))
        object.__setattr__(self, "required_timestamps", tuple(_normalize_text(value) for value in self.required_timestamps if _normalize_text(value)))
        object.__setattr__(self, "join_keys", tuple(_normalize_text(value) for value in self.join_keys if _normalize_text(value)))
        object.__setattr__(self, "point_in_time_rules", tuple(_normalize_text(value) for value in self.point_in_time_rules if _normalize_text(value)))
        object.__setattr__(self, "numeric_fields", tuple(_normalize_text(value) for value in self.numeric_fields if _normalize_text(value)))
        object.__setattr__(self, "description", _normalize_text(self.description))
        object.__setattr__(self, "market_type", _normalize_text(self.market_type))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def as_dict(self) -> dict[str, Any]:
        return {
            "table_name": self.table_name,
            "row_id_field": self.row_id_field,
            "required_fields": list(self.required_fields),
            "required_timestamps": list(self.required_timestamps),
            "join_keys": list(self.join_keys),
            "point_in_time_rules": list(self.point_in_time_rules),
            "numeric_fields": list(self.numeric_fields),
            "description": self.description,
            "market_type": self.market_type,
            "result_only": self.result_only,
            "metadata": dict(self.metadata),
        }


NFL_P0_TABLE_CONTRACTS: dict[str, NflP0TableContract] = {
    "nfl_games": NflP0TableContract(
        table_name="nfl_games",
        row_id_field="game_id",
        required_fields=(
            "game_id",
            "season",
            "season_type",
            "week",
            "game_date",
            "kickoff_time",
            "home_team_id",
            "home_team",
            "away_team_id",
            "away_team",
            "venue_id",
            "venue_name",
            "source_name",
            "source_type",
            "source_snapshot_time",
            "snapshot_time",
            "dataset_version",
            "lineage_id",
            "schema_version",
            "quality_score",
            "completeness_score",
            "status",
        ),
        required_timestamps=("game_date", "kickoff_time", "source_snapshot_time", "snapshot_time", "created_at", "updated_at"),
        join_keys=("game_id", "home_team_id", "away_team_id", "kickoff_time"),
        point_in_time_rules=("snapshot_time <= kickoff_time", "source_snapshot_time <= kickoff_time"),
        numeric_fields=("season", "week", "quality_score", "completeness_score", "neutral_site"),
        description="Canonical game identity and schedule anchor.",
        market_type="game_identity",
    ),
    "nfl_schedule": NflP0TableContract(
        table_name="nfl_schedule",
        row_id_field="schedule_id",
        required_fields=(
            "schedule_id",
            "game_id",
            "season",
            "season_type",
            "week",
            "kickoff_time",
            "home_team_id",
            "home_team",
            "away_team_id",
            "away_team",
            "venue_id",
            "venue_name",
            "source_name",
            "source_type",
            "source_snapshot_time",
            "snapshot_time",
            "dataset_version",
            "lineage_id",
            "schema_version",
            "quality_score",
            "completeness_score",
            "status",
        ),
        required_timestamps=("kickoff_time", "source_snapshot_time", "snapshot_time", "created_at", "updated_at"),
        join_keys=("schedule_id", "game_id", "kickoff_time"),
        point_in_time_rules=("snapshot_time <= kickoff_time", "source_snapshot_time <= kickoff_time"),
        numeric_fields=("season", "week", "quality_score", "completeness_score"),
        description="Canonical schedule snapshot for a game.",
        market_type="schedule",
    ),
    "nfl_results": NflP0TableContract(
        table_name="nfl_results",
        row_id_field="result_id",
        required_fields=(
            "result_id",
            "game_id",
            "season",
            "season_type",
            "week",
            "game_time",
            "final_scored_at",
            "final_score_home",
            "final_score_away",
            "winner_team_id",
            "winner_team",
            "margin",
            "total_points",
            "source_name",
            "source_type",
            "source_snapshot_time",
            "snapshot_time",
            "dataset_version",
            "lineage_id",
            "schema_version",
            "quality_score",
            "completeness_score",
            "status",
            "settlement_status",
            "finalization_status",
        ),
        required_timestamps=("game_time", "final_scored_at", "source_snapshot_time", "snapshot_time", "created_at", "updated_at"),
        join_keys=("result_id", "game_id", "final_scored_at"),
        point_in_time_rules=("final_scored_at >= game_time", "snapshot_time >= final_scored_at"),
        numeric_fields=("season", "week", "final_score_home", "final_score_away", "margin", "total_points", "quality_score", "completeness_score"),
        description="Settled result row for a game.",
        market_type="results",
        result_only=True,
    ),
    "nfl_odds_snapshots": NflP0TableContract(
        table_name="nfl_odds_snapshots",
        row_id_field="odds_snapshot_id",
        required_fields=(
            "odds_snapshot_id",
            "game_id",
            "kickoff_time",
            "book",
            "market",
            "selection",
            "american_odds",
            "decimal_odds",
            "implied_probability",
            "market_label",
            "freshness_score",
            "source_name",
            "source_type",
            "source_snapshot_time",
            "snapshot_time",
            "decision_time",
            "dataset_version",
            "lineage_id",
            "schema_version",
            "quality_score",
            "completeness_score",
            "status",
        ),
        required_timestamps=("kickoff_time", "source_snapshot_time", "snapshot_time", "decision_time", "created_at", "updated_at"),
        join_keys=("odds_snapshot_id", "game_id", "book", "market", "snapshot_time"),
        point_in_time_rules=("snapshot_time <= kickoff_time", "decision_time <= kickoff_time", "source_snapshot_time <= kickoff_time"),
        numeric_fields=("line_value", "american_odds", "decimal_odds", "implied_probability", "freshness_score", "quality_score", "completeness_score"),
        description="Pregame odds snapshot for baseline markets.",
        market_type="odds_snapshot",
    ),
    "nfl_weather_snapshots": NflP0TableContract(
        table_name="nfl_weather_snapshots",
        row_id_field="weather_snapshot_id",
        required_fields=(
            "weather_snapshot_id",
            "game_id",
            "kickoff_time",
            "forecast_time",
            "weather_condition",
            "temperature_f",
            "wind_mph",
            "wind_gust_mph",
            "precipitation_pct",
            "humidity_pct",
            "pressure_hpa",
            "indoor_flag",
            "forecast_freshness",
            "source_name",
            "source_type",
            "source_snapshot_time",
            "snapshot_time",
            "decision_time",
            "dataset_version",
            "lineage_id",
            "schema_version",
            "quality_score",
            "completeness_score",
            "status",
        ),
        required_timestamps=("kickoff_time", "forecast_time", "source_snapshot_time", "snapshot_time", "decision_time", "created_at", "updated_at"),
        join_keys=("weather_snapshot_id", "game_id", "forecast_time"),
        point_in_time_rules=("forecast_time <= kickoff_time", "snapshot_time <= kickoff_time", "decision_time <= kickoff_time"),
        numeric_fields=("temperature_f", "wind_mph", "wind_gust_mph", "precipitation_pct", "humidity_pct", "pressure_hpa", "forecast_freshness", "quality_score", "completeness_score", "indoor_flag"),
        description="Pregame weather forecast snapshot.",
        market_type="weather_snapshot",
    ),
    "nfl_injury_snapshots": NflP0TableContract(
        table_name="nfl_injury_snapshots",
        row_id_field="injury_snapshot_id",
        required_fields=(
            "injury_snapshot_id",
            "game_id",
            "kickoff_time",
            "team_id",
            "team_name",
            "opponent_team_id",
            "player_id",
            "player_name",
            "position",
            "report_status",
            "availability_status",
            "practice_status",
            "report_primary_injury",
            "injury_category",
            "report_time",
            "timing_confidence",
            "report_source",
            "source_name",
            "source_type",
            "source_snapshot_time",
            "snapshot_time",
            "decision_time",
            "dataset_version",
            "lineage_id",
            "schema_version",
            "quality_score",
            "completeness_score",
            "status",
        ),
        required_timestamps=("kickoff_time", "report_time", "source_snapshot_time", "snapshot_time", "decision_time", "created_at", "updated_at"),
        join_keys=("injury_snapshot_id", "team_id", "player_id", "snapshot_time"),
        point_in_time_rules=("report_time <= kickoff_time", "snapshot_time <= kickoff_time", "decision_time <= kickoff_time", "source_snapshot_time <= kickoff_time"),
        numeric_fields=("season", "week", "timing_confidence", "quality_score", "completeness_score"),
        description="Pregame injury and availability snapshot for a player.",
        market_type="injury_snapshot",
    ),
    "nfl_team_stats_snapshots": NflP0TableContract(
        table_name="nfl_team_stats_snapshots",
        row_id_field="team_stats_snapshot_id",
        required_fields=(
            "team_stats_snapshot_id",
            "team_id",
            "team_name",
            "opponent_team_id",
            "game_id",
            "kickoff_time",
            "season",
            "season_type",
            "week",
            "rest_days",
            "travel_distance_miles",
            "travel_timezone_change",
            "offensive_efficiency",
            "defensive_efficiency",
            "pace",
            "play_volume",
            "scoring_efficiency",
            "turnover_rate",
            "red_zone_efficiency",
            "third_down_efficiency",
            "special_teams_efficiency",
            "coaching_continuity",
            "roster_continuity",
            "injury_adjusted_availability",
            "position_group",
            "efficiency_window_games",
            "source_name",
            "source_type",
            "source_snapshot_time",
            "snapshot_time",
            "decision_time",
            "dataset_version",
            "lineage_id",
            "schema_version",
            "quality_score",
            "completeness_score",
            "status",
        ),
        required_timestamps=("kickoff_time", "source_snapshot_time", "snapshot_time", "decision_time", "created_at", "updated_at"),
        join_keys=("team_stats_snapshot_id", "team_id", "game_id", "snapshot_time"),
        point_in_time_rules=("snapshot_time <= kickoff_time", "decision_time <= kickoff_time", "source_snapshot_time <= kickoff_time"),
        numeric_fields=(
            "season",
            "week",
            "rest_days",
            "travel_distance_miles",
            "travel_timezone_change",
            "offensive_efficiency",
            "defensive_efficiency",
            "pace",
            "play_volume",
            "scoring_efficiency",
            "turnover_rate",
            "red_zone_efficiency",
            "third_down_efficiency",
            "special_teams_efficiency",
            "coaching_continuity",
            "roster_continuity",
            "injury_adjusted_availability",
            "efficiency_window_games",
            "quality_score",
            "completeness_score",
        ),
        description="Pregame team efficiency snapshot with rest and travel context.",
        market_type="team_efficiency",
    ),
}


def _row_base(
    contract: NflP0TableContract,
    row: Mapping[str, Any],
    *,
    dataset_version: str,
    created_at: str,
    updated_at: str,
) -> dict[str, Any]:
    payload = dict(row)
    source_name = _normalize_text(payload.get("source_name"), NFL_P0_SOURCE_NAME)
    source_type = _normalize_text(payload.get("source_type"), NFL_P0_SOURCE_TYPE)
    source_snapshot_time = _normalize_text(
        payload.get("source_snapshot_time"),
        _normalize_text(payload.get("snapshot_time"), created_at),
    )
    snapshot_time = _normalize_text(payload.get("snapshot_time"), source_snapshot_time or created_at)
    decision_time = _normalize_text(payload.get("decision_time"), snapshot_time)
    source_signature = _normalize_text(payload.get("source_signature"), _source_signature(source_name, source_snapshot_time))
    base = {
        "schema_version": NFL_P0_SCHEMA_VERSION,
        "created_at": _normalize_text(payload.get("created_at"), created_at),
        "updated_at": _normalize_text(payload.get("updated_at"), updated_at),
        "source": _normalize_text(payload.get("source"), source_name),
        "provider": _normalize_text(payload.get("provider"), NFL_P0_PROVIDER),
        "market": _normalize_text(payload.get("market"), NFL_P0_MARKET),
        "market_type": _normalize_text(payload.get("market_type"), contract.market_type),
        "asset_class": _normalize_text(payload.get("asset_class"), NFL_P0_ASSET_CLASS),
        "snapshot_id": _normalize_text(payload.get("snapshot_id"), f"{dataset_version}.{contract.table_name}.snapshot"),
        "lineage_id": _normalize_text(payload.get("lineage_id"), f"{dataset_version}.{contract.table_name}.lineage"),
        "version_id": _normalize_text(payload.get("version_id"), dataset_version),
        "quality_score": _normalize_float(payload.get("quality_score"), 1.0),
        "dataset_version": _normalize_text(payload.get("dataset_version"), dataset_version),
        "source_name": source_name,
        "source_type": source_type,
        "source_snapshot_time": source_snapshot_time,
        "snapshot_time": snapshot_time,
        "decision_time": decision_time,
        "status": _normalize_text(payload.get("status"), "active"),
        "completeness_score": _normalize_float(payload.get("completeness_score"), 1.0),
        "payload_json": _as_json(payload),
        "source_metadata_json": _as_json(
            {
                "source_name": source_name,
                "source_type": source_type,
                "source_snapshot_time": source_snapshot_time,
                "provider": _normalize_text(payload.get("provider"), NFL_P0_PROVIDER),
                "source_signature": source_signature,
            }
        ),
        "source_signature": source_signature,
    }
    return base


def _stable_row_id(contract: NflP0TableContract, payload: Mapping[str, Any], *, dataset_version: str, index: int) -> str:
    current = _normalize_text(payload.get(contract.row_id_field))
    if current:
        return current
    seed_fields = (
        contract.row_id_field,
        payload.get("game_id"),
        payload.get("team_id"),
        payload.get("book"),
        payload.get("market"),
        payload.get("market_label"),
        payload.get("snapshot_time"),
        payload.get("kickoff_time"),
        index,
    )
    return _stable_id(contract.row_id_field, dataset_version, *seed_fields)


def _team_strength_index(team_id: str) -> float:
    base = {
        "BUF": 0.74,
        "KC": 0.77,
        "SF": 0.76,
        "DAL": 0.71,
        "BAL": 0.75,
        "MIA": 0.72,
        "GB": 0.69,
        "CHI": 0.63,
    }
    return base.get(team_id, 0.68)


def _travel_distance(home_team_id: str, away_team_id: str) -> float:
    distances = {
        ("BUF", "KC"): 780.0,
        ("SF", "DAL"): 1460.0,
        ("BAL", "MIA"): 960.0,
        ("GB", "CHI"): 175.0,
    }
    return distances.get((home_team_id, away_team_id), 650.0)


def _venue_spec(home_team_id: str) -> dict[str, str]:
    venues = {
        "BUF": {"venue_id": "highmark", "venue_name": "Highmark Stadium", "venue_city": "Orchard Park", "venue_state": "NY"},
        "KC": {"venue_id": "arrowhead", "venue_name": "GEHA Field at Arrowhead Stadium", "venue_city": "Kansas City", "venue_state": "MO"},
        "SF": {"venue_id": "levi", "venue_name": "Levi's Stadium", "venue_city": "Santa Clara", "venue_state": "CA"},
        "DAL": {"venue_id": "atandt", "venue_name": "AT&T Stadium", "venue_city": "Arlington", "venue_state": "TX"},
        "BAL": {"venue_id": "m_bank", "venue_name": "M&T Bank Stadium", "venue_city": "Baltimore", "venue_state": "MD"},
        "MIA": {"venue_id": "hardrock", "venue_name": "Hard Rock Stadium", "venue_city": "Miami Gardens", "venue_state": "FL"},
        "GB": {"venue_id": "lambeau", "venue_name": "Lambeau Field", "venue_city": "Green Bay", "venue_state": "WI"},
        "CHI": {"venue_id": "soldier", "venue_name": "Soldier Field", "venue_city": "Chicago", "venue_state": "IL"},
    }
    return venues.get(home_team_id, {"venue_id": "unknown", "venue_name": "Unknown Stadium", "venue_city": "Unknown", "venue_state": ""})


def _game_specs(game_count: int) -> list[dict[str, Any]]:
    base_start = datetime(2024, 9, 5, 20, 20, tzinfo=timezone.utc)
    pairings = [
        ("BUF", "Buffalo Bills", "KC", "Kansas City Chiefs"),
        ("SF", "San Francisco 49ers", "DAL", "Dallas Cowboys"),
        ("BAL", "Baltimore Ravens", "MIA", "Miami Dolphins"),
        ("GB", "Green Bay Packers", "CHI", "Chicago Bears"),
    ]
    specs: list[dict[str, Any]] = []
    for index in range(max(1, int(game_count))):
        home_team_id, home_team, away_team_id, away_team = pairings[index % len(pairings)]
        kickoff = base_start + timedelta(days=(index // len(pairings)) * 7 + index)
        venue = _venue_spec(home_team_id)
        game_id = f"nfl-p0-game-{index + 1:03d}"
        specs.append(
            {
                "game_id": game_id,
                "season": 2024,
                "season_type": "regular",
                "week": 1 + index,
                "game_date": kickoff.date().isoformat(),
                "kickoff_time": _iso_nowish(kickoff),
                "home_team_id": home_team_id,
                "home_team": home_team,
                "away_team_id": away_team_id,
                "away_team": away_team,
                "venue_id": venue["venue_id"],
                "venue_name": venue["venue_name"],
                "venue_city": venue["venue_city"],
                "venue_state": venue["venue_state"],
                "neutral_site": 0,
            }
        )
    return specs


def build_nfl_p0_fixture(
    game_count: int = DEFAULT_NFL_P0_GAME_COUNT,
    *,
    dataset_version: str = NFL_P0_DATASET_VERSION,
) -> dict[str, Any]:
    created_at = "2024-08-15T12:00:00Z"
    games = _game_specs(game_count)
    tables: dict[str, list[dict[str, Any]]] = {name: [] for name in NFL_P0_TABLE_CONTRACTS}
    team_last_game_day: dict[str, datetime] = {}

    for index, game in enumerate(games):
        kickoff = _parse_iso(game["kickoff_time"]) or datetime(2024, 9, 5, 20, 20, tzinfo=timezone.utc)
        schedule_snapshot = kickoff - timedelta(days=7)
        odds_snapshot = kickoff - timedelta(days=1)
        weather_snapshot = kickoff - timedelta(hours=12)
        injury_report_time = kickoff - timedelta(hours=30)
        injury_snapshot = kickoff - timedelta(hours=24)
        stats_snapshot = kickoff - timedelta(days=2)
        result_time = kickoff + timedelta(hours=3, minutes=10)
        game_version_seed = f"{dataset_version}.game.{index + 1:03d}"

        tables["nfl_games"].append(
            {
                **game,
                "dataset_version": dataset_version,
                "source_name": NFL_P0_SOURCE_NAME,
                "source_type": NFL_P0_SOURCE_TYPE,
                "source_snapshot_time": _iso_nowish(schedule_snapshot),
                "snapshot_time": _iso_nowish(schedule_snapshot),
                "decision_time": _iso_nowish(schedule_snapshot),
                "status": "scheduled",
                "finalization_status": "unfinalized",
                "completeness_score": 1.0,
                "source_signature": _source_signature(NFL_P0_SOURCE_NAME, _iso_nowish(schedule_snapshot)),
                "market_type": "game_identity",
                "provider": NFL_P0_PROVIDER,
                "market": NFL_P0_MARKET,
                "asset_class": NFL_P0_ASSET_CLASS,
                "snapshot_id": f"{game_version_seed}.games.snapshot",
                "lineage_id": f"{game_version_seed}.games.lineage",
                "version_id": dataset_version,
                "quality_score": 1.0,
            }
        )

        tables["nfl_schedule"].append(
            {
                "schedule_id": f"{game['game_id']}.schedule",
                **game,
                "dataset_version": dataset_version,
                "source_name": NFL_P0_SOURCE_NAME,
                "source_type": NFL_P0_SOURCE_TYPE,
                "source_snapshot_time": _iso_nowish(schedule_snapshot),
                "snapshot_time": _iso_nowish(schedule_snapshot),
                "decision_time": _iso_nowish(schedule_snapshot),
                "status": "scheduled",
                "schedule_status": "scheduled",
                "completeness_score": 1.0,
                "source_signature": _source_signature(NFL_P0_SOURCE_NAME, _iso_nowish(schedule_snapshot)),
                "market_type": "schedule",
                "provider": NFL_P0_PROVIDER,
                "market": NFL_P0_MARKET,
                "asset_class": NFL_P0_ASSET_CLASS,
                "snapshot_id": f"{game_version_seed}.schedule.snapshot",
                "lineage_id": f"{game_version_seed}.schedule.lineage",
                "version_id": dataset_version,
                "quality_score": 1.0,
            }
        )

        home_score = 24 + (index % 4) * 3
        away_score = 17 + (index % 3) * 4
        if index % 2 == 1:
            home_score, away_score = away_score, home_score
        winner_team_id = game["home_team_id"] if home_score >= away_score else game["away_team_id"]
        winner_team = game["home_team"] if winner_team_id == game["home_team_id"] else game["away_team"]
        tables["nfl_results"].append(
            {
                "result_id": f"{game['game_id']}.result",
                **game,
                "game_time": game["kickoff_time"],
                "final_scored_at": _iso_nowish(result_time),
                "final_score_home": home_score,
                "final_score_away": away_score,
                "winner_team_id": winner_team_id,
                "winner_team": winner_team,
                "margin": home_score - away_score,
                "total_points": home_score + away_score,
                "dataset_version": dataset_version,
                "source_name": NFL_P0_SOURCE_NAME,
                "source_type": NFL_P0_SOURCE_TYPE,
                "source_snapshot_time": _iso_nowish(result_time),
                "snapshot_time": _iso_nowish(result_time),
                "decision_time": _iso_nowish(result_time),
                "status": "final",
                "settlement_status": "settled",
                "finalization_status": "final",
                "completeness_score": 1.0,
                "source_signature": _source_signature(NFL_P0_SOURCE_NAME, _iso_nowish(result_time)),
                "market_type": "results",
                "provider": NFL_P0_PROVIDER,
                "market": NFL_P0_MARKET,
                "asset_class": NFL_P0_ASSET_CLASS,
                "snapshot_id": f"{game_version_seed}.results.snapshot",
                "lineage_id": f"{game_version_seed}.results.lineage",
                "version_id": dataset_version,
                "quality_score": 1.0,
            }
        )

        odds_market_rows = [
            ("spread", "home", -3.5 + (index % 2) * 0.5, -110.0, 1.91, 0.5208),
            ("moneyline", "home", None, -145.0 + index * 5, 1.69 + index * 0.01, 0.5930),
            ("total", "over", 46.5 + index, -108.0, 1.93, 0.5160),
        ]
        for market_index, (market, selection, line_value, american_odds, decimal_odds, implied_probability) in enumerate(odds_market_rows):
            tables["nfl_odds_snapshots"].append(
                {
                    "odds_snapshot_id": f"{game['game_id']}.{market}.odds",
                    **game,
                    "kickoff_time": game["kickoff_time"],
                    "book": "consensus",
                    "market": market,
                    "selection": selection,
                    "line_value": line_value,
                    "american_odds": american_odds,
                    "decimal_odds": decimal_odds,
                    "implied_probability": implied_probability,
                    "market_label": _fixture_market_label(market),
                    "freshness_score": 0.95 - market_index * 0.02,
                    "dataset_version": dataset_version,
                    "source_name": NFL_P0_SOURCE_NAME,
                    "source_type": NFL_P0_SOURCE_TYPE,
                    "source_snapshot_time": _iso_nowish(odds_snapshot),
                    "snapshot_time": _iso_nowish(odds_snapshot),
                    "decision_time": _iso_nowish(odds_snapshot),
                    "status": "pregame",
                    "completeness_score": 1.0,
                    "source_signature": _source_signature(NFL_P0_SOURCE_NAME, _iso_nowish(odds_snapshot)),
                    "market_type": market,
                    "provider": NFL_P0_PROVIDER,
                    "asset_class": NFL_P0_ASSET_CLASS,
                    "snapshot_id": f"{game_version_seed}.{market}.snapshot",
                    "lineage_id": f"{game_version_seed}.{market}.lineage",
                    "version_id": dataset_version,
                    "quality_score": 1.0,
                }
            )

        tables["nfl_weather_snapshots"].append(
            {
                "weather_snapshot_id": f"{game['game_id']}.weather",
                **game,
                "kickoff_time": game["kickoff_time"],
                "forecast_time": _iso_nowish(weather_snapshot),
                "weather_condition": "clear",
                "temperature_f": 68.0 - index * 2,
                "wind_mph": 8.0 + index,
                "wind_gust_mph": 12.0 + index * 1.5,
                "precipitation_pct": 10.0 + index * 3,
                "humidity_pct": 55.0 + index * 2,
                "pressure_hpa": 1012.0 - index,
                "indoor_flag": 0,
                "forecast_freshness": 0.88,
                "dataset_version": dataset_version,
                "source_name": NFL_P0_SOURCE_NAME,
                "source_type": NFL_P0_SOURCE_TYPE,
                "source_snapshot_time": _iso_nowish(weather_snapshot),
                "snapshot_time": _iso_nowish(weather_snapshot),
                "decision_time": _iso_nowish(weather_snapshot),
                "status": "pregame",
                "completeness_score": 1.0,
                "source_signature": _source_signature(NFL_P0_SOURCE_NAME, _iso_nowish(weather_snapshot)),
                "market_type": "weather",
                "provider": NFL_P0_PROVIDER,
                "market": NFL_P0_MARKET,
                "asset_class": NFL_P0_ASSET_CLASS,
                "snapshot_id": f"{game_version_seed}.weather.snapshot",
                "lineage_id": f"{game_version_seed}.weather.lineage",
                "version_id": dataset_version,
                "quality_score": 1.0,
            }
        )

        injury_rows = (
            (
                game["home_team_id"],
                game["home_team"],
                game["away_team_id"],
                f"{game['home_team_id']}.player.qb.001",
                f"{game['home_team']} QB",
                "QB",
                "Questionable",
                "limited",
                "Limited",
                "ankle",
                "lower_body",
                "official_team_report",
            ),
            (
                game["away_team_id"],
                game["away_team"],
                game["home_team_id"],
                f"{game['away_team_id']}.player.wr.001",
                f"{game['away_team']} WR",
                "WR",
                "Out",
                "unavailable",
                "DNP",
                "hamstring",
                "soft_tissue",
                "official_team_report",
            ),
        )
        for player_index, (
            team_id,
            team_name,
            opponent_team_id,
            player_id,
            player_name,
            position,
            report_status,
            availability_status,
            practice_status,
            report_primary_injury,
            injury_category,
            report_source,
        ) in enumerate(injury_rows):
            tables["nfl_injury_snapshots"].append(
                {
                    "injury_snapshot_id": f"{game['game_id']}.{team_id}.injury.{player_index + 1:02d}",
                    **game,
                    "kickoff_time": game["kickoff_time"],
                    "team_id": team_id,
                    "team_name": team_name,
                    "opponent_team_id": opponent_team_id,
                    "player_id": player_id,
                    "player_name": player_name,
                    "position": position,
                    "report_status": report_status,
                    "availability_status": availability_status,
                    "practice_status": practice_status,
                    "report_primary_injury": report_primary_injury,
                    "injury_category": injury_category,
                    "report_time": _iso_nowish(injury_report_time),
                    "timing_confidence": 0.96 - player_index * 0.02,
                    "report_source": report_source,
                    "dataset_version": dataset_version,
                    "source_name": NFL_P0_SOURCE_NAME,
                    "source_type": NFL_P0_SOURCE_TYPE,
                    "source_snapshot_time": _iso_nowish(injury_snapshot),
                    "snapshot_time": _iso_nowish(injury_snapshot),
                    "decision_time": _iso_nowish(injury_snapshot),
                    "status": "pregame",
                    "completeness_score": 1.0,
                    "source_signature": _source_signature(NFL_P0_SOURCE_NAME, _iso_nowish(injury_snapshot)),
                    "market_type": "injury_snapshot",
                    "provider": NFL_P0_PROVIDER,
                    "market": NFL_P0_MARKET,
                    "asset_class": NFL_P0_ASSET_CLASS,
                    "snapshot_id": f"{game_version_seed}.{team_id}.injury.snapshot",
                    "lineage_id": f"{game_version_seed}.{team_id}.injury.lineage",
                    "version_id": dataset_version,
                    "quality_score": 1.0,
                }
            )

        for team_side, team_id, team_name, opponent_id, rest_days, travel_distance, travel_timezone_change in (
            ("home", game["home_team_id"], game["home_team"], game["away_team_id"], max(7, 10 - index), 0.0, 0.0),
            ("away", game["away_team_id"], game["away_team"], game["home_team_id"], max(5, 7 - (index % 3)), _travel_distance(game["home_team_id"], game["away_team_id"]), 1.0 if index % 2 else 0.0),
        ):
            last_game_time = team_last_game_day.get(team_id)
            if last_game_time is not None:
                rest_days = max(rest_days, (kickoff.date() - last_game_time.date()).days)
            team_last_game_day[team_id] = kickoff
            base_efficiency = _team_strength_index(team_id)
            tables["nfl_team_stats_snapshots"].append(
                {
                    "team_stats_snapshot_id": f"{game['game_id']}.{team_id}.team_stats",
                    **game,
                    "team_id": team_id,
                    "team_name": team_name,
                    "opponent_team_id": opponent_id,
                    "kickoff_time": game["kickoff_time"],
                    "season": game["season"],
                    "season_type": game["season_type"],
                    "week": game["week"],
                    "rest_days": float(rest_days),
                    "travel_distance_miles": float(travel_distance),
                    "travel_timezone_change": float(travel_timezone_change),
                    "offensive_efficiency": round(base_efficiency + (0.03 if team_side == "home" else -0.02), 4),
                    "defensive_efficiency": round(0.52 + (0.04 if team_side == "home" else -0.01) + index * 0.01, 4),
                    "pace": round(61.0 + index * 1.5 + (0.5 if team_side == "away" else 0.0), 2),
                    "play_volume": 58 + index * 2 + (1 if team_side == "home" else 0),
                    "scoring_efficiency": round(0.42 + index * 0.03 + (0.02 if team_side == "home" else -0.01), 4),
                    "turnover_rate": round(0.12 - index * 0.005 + (0.01 if team_side == "away" else 0.0), 4),
                    "red_zone_efficiency": round(0.48 + index * 0.015 + (0.02 if team_side == "home" else -0.015), 4),
                    "third_down_efficiency": round(0.40 + index * 0.01 + (0.015 if team_side == "home" else -0.01), 4),
                    "special_teams_efficiency": round(0.5 + index * 0.01 + (0.01 if team_side == "home" else -0.005), 4),
                    "coaching_continuity": round(0.88 - index * 0.01, 4),
                    "roster_continuity": round(0.84 - index * 0.015, 4),
                    "injury_adjusted_availability": round(0.90 - index * 0.02, 4),
                    "position_group": "team",
                    "efficiency_window_games": 4 + index,
                    "dataset_version": dataset_version,
                    "source_name": NFL_P0_SOURCE_NAME,
                    "source_type": NFL_P0_SOURCE_TYPE,
                    "source_snapshot_time": _iso_nowish(stats_snapshot),
                    "snapshot_time": _iso_nowish(stats_snapshot),
                    "decision_time": _iso_nowish(stats_snapshot),
                    "status": "pregame",
                    "completeness_score": 1.0,
                    "source_signature": _source_signature(NFL_P0_SOURCE_NAME, _iso_nowish(stats_snapshot)),
                    "market_type": "team_efficiency",
                    "provider": NFL_P0_PROVIDER,
                    "market": NFL_P0_MARKET,
                    "asset_class": NFL_P0_ASSET_CLASS,
                    "snapshot_id": f"{game_version_seed}.{team_id}.team_stats.snapshot",
                    "lineage_id": f"{game_version_seed}.{team_id}.team_stats.lineage",
                    "version_id": dataset_version,
                    "quality_score": 1.0,
                }
            )

    return {
        "dataset_version": dataset_version,
        "dataset_name": NFL_P0_DATASET_NAME,
        "game_count": len(games),
        "source_name": NFL_P0_SOURCE_NAME,
        "source_type": NFL_P0_SOURCE_TYPE,
        "provider": NFL_P0_PROVIDER,
        "tables": tables,
        "contracts": {name: contract.as_dict() for name, contract in NFL_P0_TABLE_CONTRACTS.items()},
        "created_at": created_at,
    }


def normalize_nfl_p0_rows(
    table_name: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    dataset_version: str = NFL_P0_DATASET_VERSION,
    created_at: str | None = None,
    updated_at: str | None = None,
) -> list[dict[str, Any]]:
    contract = NFL_P0_TABLE_CONTRACTS[table_name]
    created = _normalize_text(created_at, _utc_now_iso())
    updated = _normalize_text(updated_at, created)
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        payload = dict(row)
        row_id = _stable_row_id(contract, payload, dataset_version=dataset_version, index=index)
        if contract.row_id_field not in payload or not _normalize_text(payload.get(contract.row_id_field)):
            payload[contract.row_id_field] = row_id
        payload.setdefault("dataset_version", dataset_version)
        payload.setdefault("source_name", NFL_P0_SOURCE_NAME)
        payload.setdefault("source_type", NFL_P0_SOURCE_TYPE)
        payload.setdefault("provider", NFL_P0_PROVIDER)
        payload.setdefault("market", NFL_P0_MARKET)
        payload.setdefault("asset_class", NFL_P0_ASSET_CLASS)
        payload.setdefault("market_type", contract.market_type)
        payload.setdefault("status", "active" if not contract.result_only else "final")
        if "kickoff_time" not in payload and "game_time" in payload:
            payload["kickoff_time"] = payload["game_time"]
        if "snapshot_time" not in payload:
            payload["snapshot_time"] = payload.get("source_snapshot_time") or payload.get("decision_time") or created
        if "source_snapshot_time" not in payload:
            payload["source_snapshot_time"] = payload["snapshot_time"]
        if "decision_time" not in payload:
            payload["decision_time"] = payload["snapshot_time"]
        payload["payload_json"] = _as_json(row)
        payload["source_metadata_json"] = _as_json(
            {
                "source_name": _normalize_text(payload.get("source_name"), NFL_P0_SOURCE_NAME),
                "source_type": _normalize_text(payload.get("source_type"), NFL_P0_SOURCE_TYPE),
                "source_snapshot_time": _normalize_text(payload.get("source_snapshot_time"), created),
                "provider": _normalize_text(payload.get("provider"), NFL_P0_PROVIDER),
                "source_signature": _normalize_text(payload.get("source_signature"), _source_signature(_normalize_text(payload.get("source_name"), NFL_P0_SOURCE_NAME), _normalize_text(payload.get("source_snapshot_time"), created))),
            }
        )
        payload["source_signature"] = _normalize_text(
            payload.get("source_signature"),
            _source_signature(_normalize_text(payload.get("source_name"), NFL_P0_SOURCE_NAME), _normalize_text(payload.get("source_snapshot_time"), created)),
        )
        payload["schema_version"] = NFL_P0_SCHEMA_VERSION
        payload["created_at"] = _normalize_text(payload.get("created_at"), created)
        payload["updated_at"] = _normalize_text(payload.get("updated_at"), updated)
        payload["snapshot_id"] = _normalize_text(payload.get("snapshot_id"), f"{dataset_version}.{table_name}.snapshot")
        payload["lineage_id"] = _normalize_text(payload.get("lineage_id"), f"{dataset_version}.{table_name}.lineage")
        payload["version_id"] = _normalize_text(payload.get("version_id"), dataset_version)
        payload["quality_score"] = _normalize_float(payload.get("quality_score"), 1.0)
        payload["completeness_score"] = _normalize_float(payload.get("completeness_score"), 1.0)
        integer_fields = {"season", "week", "indoor_flag", "efficiency_window_games", "neutral_site", "final_score_home", "final_score_away", "margin", "total_points"}
        for field in contract.numeric_fields:
            if field in payload:
                payload[field] = _normalize_int(payload.get(field)) if field in integer_fields else _normalize_float(payload.get(field))
        normalized.append(payload)
    return normalized


def _point_in_time_issues(contract: NflP0TableContract, row: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    kickoff = _parse_iso(row.get("kickoff_time") or row.get("game_time"))
    snapshot = _parse_iso(row.get("snapshot_time"))
    source_snapshot = _parse_iso(row.get("source_snapshot_time"))
    decision = _parse_iso(row.get("decision_time"))
    final_scored_at = _parse_iso(row.get("final_scored_at"))
    game_time = _parse_iso(row.get("game_time"))

    if contract.result_only:
        if game_time and final_scored_at and final_scored_at < game_time:
            issues.append("result_before_game_time")
        if final_scored_at and snapshot and snapshot < final_scored_at:
            issues.append("result_snapshot_before_finalization")
        return issues

    if kickoff is not None:
        for label, instant in (("snapshot_time", snapshot), ("source_snapshot_time", source_snapshot), ("decision_time", decision)):
            if instant is not None and instant > kickoff:
                issues.append(f"{label}_after_kickoff")
    return issues


def validate_nfl_p0_rows(
    table_name: str,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    contract = NFL_P0_TABLE_CONTRACTS[table_name]
    base = validate_dataset_rows(rows, required_fields=contract.required_fields)
    missing_rows = list(base.get("missing_rows", []))
    missing_fields = [field for row in missing_rows for field in row.get("missing_fields", [])]
    duplicate_ids: list[str] = []
    seen_ids: set[str] = set()
    for row in rows:
        row_id = _normalize_text(row.get(contract.row_id_field))
        if not row_id:
            continue
        if row_id in seen_ids and row_id not in duplicate_ids:
            duplicate_ids.append(row_id)
        seen_ids.add(row_id)

    schema_issues = [index for index, row in enumerate(rows) if _normalize_text(row.get("schema_version")) != NFL_P0_SCHEMA_VERSION]
    source_issues = [index for index, row in enumerate(rows) if not _normalize_text(row.get("source_name")) or not _normalize_text(row.get("source_type"))]
    metadata_issues = [
        f"{index}:{field}"
        for index, row in enumerate(rows)
        for field in ("source_signature", "source_metadata_json", "payload_json")
        if not _normalize_text(row.get(field))
    ]
    lineage_issues = [index for index, row in enumerate(rows) if not _normalize_text(row.get("lineage_id")) or not _normalize_text(row.get("snapshot_id")) or not _normalize_text(row.get("version_id"))]
    point_in_time_issues = [issue for row in rows for issue in _point_in_time_issues(contract, row)]
    numeric_issues: list[str] = []
    for index, row in enumerate(rows):
        for field in contract.numeric_fields:
            value = row.get(field)
            if value in (None, ""):
                continue
            try:
                if field in {"season", "week", "indoor_flag", "efficiency_window_games"}:
                    int(float(value))
                else:
                    float(value)
            except (TypeError, ValueError):
                numeric_issues.append(f"{index}:{field}")

    errors = list(dict.fromkeys([
        *missing_fields,
        *[f"duplicate:{value}" for value in duplicate_ids],
        *[f"schema_version:{index}" for index in schema_issues],
        *[f"source_metadata:{index}" for index in source_issues],
        *[f"provenance:{issue}" for issue in metadata_issues],
        *[f"lineage_metadata:{index}" for index in lineage_issues],
        *[f"point_in_time:{issue}" for issue in point_in_time_issues],
        *[f"numeric:{issue}" for issue in numeric_issues],
    ]))
    ok = not errors
    return {
        "ok": ok,
        "status": "validated" if ok else "rejected",
        "table_name": table_name,
        "row_count": len(rows),
        "error_count": len(errors),
        "warning_count": len(point_in_time_issues),
        "missing_fields": missing_fields,
        "duplicate_keys": duplicate_ids,
        "schema_version_issues": schema_issues,
        "source_issues": source_issues,
        "metadata_issues": metadata_issues,
        "lineage_issues": lineage_issues,
        "point_in_time_issues": point_in_time_issues,
        "numeric_issues": numeric_issues,
        "errors": errors,
        "validation_contract": contract.as_dict(),
        "base_validation": base,
    }


def create_nfl_p0_storage_engine(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
) -> LocalStorageEngine:
    path = Path(storage_path or DEFAULT_NFL_P0_STORAGE_PATH)
    return create_local_storage_engine(path, backend=backend)


def bootstrap_nfl_p0_foundation(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    fixture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile_validation = validate_nfl_p0_market_profile()
    if not profile_validation["ok"]:
        raise ValueError(f"NFL market profile validation failed: {', '.join(profile_validation['errors']) or 'unknown error'}")
    storage = create_nfl_p0_storage_engine(storage_path, backend=backend)
    try:
        if fixture is None:
            fixture = build_nfl_p0_fixture()
        table_results: dict[str, dict[str, Any]] = {}
        for table_name, rows in fixture["tables"].items():
            normalized_rows = normalize_nfl_p0_rows(table_name, rows, dataset_version=fixture["dataset_version"], created_at=fixture["created_at"], updated_at=fixture["created_at"])
            validation = validate_nfl_p0_rows(table_name, normalized_rows)
            for row in normalized_rows:
                storage.upsert(table_name, row, key_columns=(NFL_P0_TABLE_CONTRACTS[table_name].row_id_field,))
            table_results[table_name] = {
                **validation,
                "normalized_row_count": len(normalized_rows),
                "stored_row_count": storage.count(table_name),
            }
        readiness = build_nfl_p0_readiness_snapshot(storage=storage, precomputed_results=table_results, fixture=fixture)
        readiness["bootstrap"] = {
            "dataset_version": fixture["dataset_version"],
            "game_count": fixture["game_count"],
            "table_results": table_results,
        }
        readiness["market_profile"] = profile_validation
        return readiness
    finally:
        storage.close()


def build_nfl_p0_readiness_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    storage: LocalStorageEngine | None = None,
    precomputed_results: Mapping[str, Mapping[str, Any]] | None = None,
    fixture: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    profile_validation = validate_nfl_p0_market_profile()
    close_storage = False
    if storage is None:
        storage = create_nfl_p0_storage_engine(storage_path, backend=backend)
        close_storage = True
    try:
        table_readiness: dict[str, dict[str, Any]] = {}
        missing_tables: list[str] = []
        ready_tables: list[str] = []
        blocked_tables: list[str] = []
        for table_name, contract in NFL_P0_TABLE_CONTRACTS.items():
            exists = storage.table_exists(table_name)
            rows = storage.fetch(table_name, order_by=f"{contract.row_id_field} ASC") if exists else []
            validation = dict(precomputed_results.get(table_name) or validate_nfl_p0_rows(table_name, rows)) if precomputed_results else validate_nfl_p0_rows(table_name, rows)
            count = len(rows)
            table_status = "ready" if exists and count > 0 and validation.get("ok") else "missing" if not exists or count == 0 else "blocked"
            table_readiness[table_name] = {
                "table_name": table_name,
                "exists": exists,
                "row_count": count,
                "status": table_status,
                "validation": validation,
                "required_fields": list(contract.required_fields),
                "point_in_time_rules": list(contract.point_in_time_rules),
                "description": contract.description,
            }
            if table_status == "ready":
                ready_tables.append(table_name)
            elif table_status == "missing":
                missing_tables.append(table_name)
            else:
                blocked_tables.append(table_name)
        overall_status = "ready" if profile_validation["ok"] and len(ready_tables) == len(NFL_P0_TABLE_CONTRACTS) else "partial" if ready_tables and profile_validation["ok"] else "blocked" if not profile_validation["ok"] else "missing"
        return {
            "ok": overall_status == "ready",
            "status": overall_status,
            "dataset_name": NFL_P0_DATASET_NAME,
            "dataset_version": (fixture or {}).get("dataset_version", NFL_P0_DATASET_VERSION),
            "storage": storage.health(),
            "market_profile": profile_validation,
            "table_readiness": table_readiness,
            "ready_tables": ready_tables,
            "missing_tables": missing_tables,
            "blocked_tables": blocked_tables,
            "summary": {
                "table_count": len(NFL_P0_TABLE_CONTRACTS),
                "ready_table_count": len(ready_tables),
                "missing_table_count": len(missing_tables),
                "blocked_table_count": len(blocked_tables),
                "market_profile_status": profile_validation["status"],
                "row_counts": {name: details.get("row_count", 0) for name, details in table_readiness.items()},
            },
            "fixture_summary": {
                "game_count": (fixture or {}).get("game_count", 0),
                "source_name": (fixture or {}).get("source_name", NFL_P0_SOURCE_NAME),
                "provider": (fixture or {}).get("provider", NFL_P0_PROVIDER),
            },
        }
    finally:
        if close_storage:
            storage.close()


def build_nfl_p0_dashboard_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
) -> dict[str, Any]:
    snapshot = build_nfl_p0_readiness_snapshot(storage_path=storage_path, backend=backend)
    snapshot["table_counts"] = {name: details.get("row_count", 0) for name, details in snapshot.get("table_readiness", {}).items()}
    snapshot["dataset_readiness"] = {
        "status": snapshot.get("status"),
        "ready_table_count": len(snapshot.get("ready_tables", [])),
        "total_table_count": len(NFL_P0_TABLE_CONTRACTS),
        "missing_tables": snapshot.get("missing_tables", []),
        "blocked_tables": snapshot.get("blocked_tables", []),
    }
    snapshot["readiness_summary"] = {
        "table_readiness_ready": len(snapshot.get("ready_tables", [])),
        "table_readiness_missing": len(snapshot.get("missing_tables", [])),
        "table_readiness_blocked": len(snapshot.get("blocked_tables", [])),
    }
    return snapshot


__all__ = [
    "DEFAULT_NFL_P0_GAME_COUNT",
    "DEFAULT_NFL_P0_STORAGE_PATH",
    "NFL_P0_ASSET_CLASS",
    "NFL_P0_DATASET_NAME",
    "NFL_P0_DATASET_VERSION",
    "NFL_P0_MARKET",
    "NFL_P0_PROFILE_FAMILY",
    "NFL_P0_PROFILE_ID",
    "NFL_P0_PROFILE_MARKET_SCOPE",
    "NFL_P0_MARKET_TYPE",
    "NFL_P0_OWNER",
    "NFL_P0_PROVIDER",
    "NFL_P0_SCHEMA_VERSION",
    "NFL_P0_SOURCE_NAME",
    "NFL_P0_SOURCE_TYPE",
    "NFL_P0_TABLE_CONTRACTS",
    "NflP0TableContract",
    "backend_available",
    "bootstrap_nfl_p0_foundation",
    "build_nfl_p0_dashboard_snapshot",
    "build_nfl_p0_fixture",
    "get_nfl_p0_market_profile",
    "create_nfl_p0_storage_engine",
    "normalize_nfl_p0_rows",
    "validate_nfl_p0_market_profile",
    "validate_nfl_p0_rows",
]
