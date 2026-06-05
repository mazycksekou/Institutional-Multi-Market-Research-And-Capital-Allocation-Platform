from __future__ import annotations

from .source_policy_review_common import build_policy_queries_for_group


def build_nhl_policy_query_plan() -> dict:
    return build_policy_queries_for_group(
        sport_group="nhl",
        sport_label="NHL",
        extra_queries=[
            "NHL injuries roster page terms",
            "NHL officials public page robots",
            "Natural Stat Trick terms xG line combinations",
            "DailyFaceoff starting goalies terms",
            "Hockey Reference terms hockey data",
        ],
    )

