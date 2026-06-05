from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable


GENERAL_QUERY_TEMPLATES = (
    "{league} {field} dataset",
    "{league} {field} csv",
    "{league} {field} api",
    "{league} {field} parquet",
    "{league} {field} github",
    "{league} {field} data dictionary",
    "{league} {field} archive",
    "{league} {field} public data",
    "{league} {field} official",
    "{league} historical {field}",
    "{sport} {field} open data",
    "{sport} {field} database",
    "{field} site:{official_domain}",
    "{field} site:github.com",
    "{field} filetype:csv",
    "{field} filetype:pdf",
    "{field} data download",
)


FIELD_SYNONYMS: dict[str, list[str]] = {
    "coaching_staff_role_history": ["coaching staff history", "staff role history", "coach role history"],
    "staff_turnover_severity": ["staff turnover", "coaching churn", "coach churn"],
    "official_assignment_tendency": ["official assignment", "referee assignment", "crew assignment"],
    "stadium_surface_roof_state": ["roof state", "surface state", "stadium roof surface"],
    "manager_coach_role_history": ["manager history", "coach history", "manager role history"],
    "draft_pick_origin": ["draft origin", "draft pick history", "amateur draft"],
    "umpire_assignment_tendency": ["umpire assignment", "crew tendency", "umpire crew history"],
    "probable_pitcher_confirmation_history": ["probable pitcher", "starting pitcher confirmation", "pitcher confirmation"],
    "coordinator_continuity": ["coordinator continuity", "coordinator history"],
    "staff_continuity": ["staff continuity", "coaching continuity"],
    "team_game_run_profile": ["run profile", "team scoring profile", "game run profile"],
    "player_availability_volatility": ["availability volatility", "player availability", "availability trend"],
    "player_id": ["player identifier", "player id", "person id"],
    "team_id": ["team identifier", "team id", "club id"],
    "yearID": ["year id", "season year", "season"],
    "playerID": ["player id", "player identifier"],
    "game_pk": ["game pk", "game key", "mlb game pk"],
    "game_id": ["game id", "event id", "match id"],
    "market_odds_blocked": ["market odds", "closing line", "moneyline", "spread line", "total line"],
    "manual_csv_import": ["manual csv import", "manual template import", "csv template"],
    "structured_wiki_seed": ["wikidata seed", "wikipedia structured seed", "wiki seed"],
}


LEAGUE_LABELS = {
    "nfl": "NFL",
    "americanfootball_nfl": "NFL",
    "mlb": "MLB",
    "baseball_mlb": "MLB",
}


OFFICIAL_DOMAIN_HINTS = {
    "nfl": "nfl.com",
    "americanfootball_nfl": "nfl.com",
    "mlb": "mlb.com",
    "baseball_mlb": "mlb.com",
}


def _normalize_field(field_name: str) -> str:
    text = str(field_name or "").strip()
    if not text:
        return ""
    text = re.sub(r"(?<!^)(?=[A-Z])", "_", text)
    text = text.replace("-", "_").replace(" ", "_").lower()
    text = re.sub(r"__+", "_", text)
    return text.strip("_")


def _dedupe(sequence: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in sequence:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


@dataclass(frozen=True)
class QueryVariantBundle:
    sport: str
    field_name: str
    league: str
    official_domain: str
    exact_terms: list[str]
    synonym_terms: list[str]
    query_variants: list[dict[str, str]]


def build_query_variant_bundle(
    *,
    sport: str,
    field_name: str,
    source_family: str | None = None,
    official_domain: str | None = None,
    extra_synonyms: Iterable[str] | None = None,
) -> dict[str, Any]:
    sport_key = str(sport).lower()
    league = LEAGUE_LABELS.get(sport_key, sport_key.upper())
    official_domain = official_domain or OFFICIAL_DOMAIN_HINTS.get(sport_key, "example.com")
    field_token = _normalize_field(field_name).replace("_", " ")
    synonym_terms = list(FIELD_SYNONYMS.get(str(field_name), []))
    if extra_synonyms:
        synonym_terms.extend(str(item) for item in extra_synonyms if str(item).strip())
    if source_family:
        synonym_terms.append(str(source_family).replace("_", " "))
    synonym_terms = _dedupe(synonym_terms)
    exact_terms = _dedupe([field_token, str(field_name).replace("_", " "), str(field_name).replace("_", "")])
    query_variants: list[dict[str, str]] = []
    for template in GENERAL_QUERY_TEMPLATES:
        query = template.format(
            league=league,
            sport=sport_key,
            field=field_token,
            official_domain=official_domain,
        )
        query_variants.append(
            {
                "query": query,
                "template": template,
                "sport": sport_key,
                "league": league,
                "field_name": str(field_name),
            }
        )
    for synonym in synonym_terms:
        query_variants.append(
            {
                "query": f"{league} {synonym} dataset",
                "template": "{league} {field} dataset",
                "sport": sport_key,
                "league": league,
                "field_name": str(field_name),
            }
        )
        query_variants.append(
            {
                "query": f"{synonym} site:{official_domain}",
                "template": "{field} site:{official_domain}",
                "sport": sport_key,
                "league": league,
                "field_name": str(field_name),
            }
        )
    return {
        "sport": sport_key,
        "field_name": str(field_name),
        "league": league,
        "official_domain": official_domain,
        "exact_terms": exact_terms,
        "synonym_terms": synonym_terms,
        "query_variants": _dedupe(item["query"] for item in query_variants),
        "query_variant_records": query_variants,
    }


def build_search_term_bundle(
    *,
    sport: str,
    field_name: str,
    source_family: str | None = None,
    official_domain: str | None = None,
) -> dict[str, Any]:
    bundle = build_query_variant_bundle(
        sport=sport,
        field_name=field_name,
        source_family=source_family,
        official_domain=official_domain,
    )
    return {
        "sport": bundle["sport"],
        "field_name": bundle["field_name"],
        "exact_search_terms": bundle["exact_terms"],
        "synonym_search_terms": bundle["synonym_terms"],
        "query_variants": bundle["query_variants"],
        "query_variant_records": bundle["query_variant_records"],
    }
