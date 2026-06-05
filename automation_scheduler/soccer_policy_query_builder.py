from __future__ import annotations

from .source_policy_review_common import build_policy_queries_for_group


def build_soccer_policy_query_plan() -> dict:
    return build_policy_queries_for_group(
        sport_group="soccer",
        sport_label="Soccer",
        extra_queries=[
            "football-data.co.uk license terms csv",
            "StatsBomb open data license soccer",
            "Understat terms xg public pages",
            "ClubElo data terms football ratings",
            "FiveThirtyEight soccer SPI archive license",
        ],
    )

