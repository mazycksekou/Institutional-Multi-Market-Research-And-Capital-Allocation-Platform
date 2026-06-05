from __future__ import annotations

from .source_policy_review_common import build_policy_queries_for_group


def build_mlb_policy_query_plan() -> dict:
    return build_policy_queries_for_group(
        sport_group="mlb",
        sport_label="MLB",
        extra_queries=[
            "MLB Stats API terms of use officials endpoint",
            "Baseball Savant csv docs terms policy",
            "Retrosheet event files notice license",
            "MLB injuries transactions public page policy",
            "FanGraphs terms baseball data use",
        ],
    )

