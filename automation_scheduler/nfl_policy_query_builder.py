from __future__ import annotations

from .source_policy_review_common import build_policy_queries_for_group


def build_nfl_policy_query_plan() -> dict:
    return build_policy_queries_for_group(
        sport_group="nfl",
        sport_label="NFL",
        extra_queries=[
            "NFL injuries practice reports official source policy",
            "NFL referee assignments public page policy",
            "NFL coaching staff public page terms",
            "nflverse injuries license",
            "Pro Football Reference terms of use football",
        ],
    )

