from __future__ import annotations

from .source_policy_review_common import build_policy_queries_for_group


def build_basketball_policy_query_plan() -> dict:
    return build_policy_queries_for_group(
        sport_group="basketball",
        sport_label="Basketball",
        extra_queries=[
            "NBA injury report official policy",
            "WNBA official stats terms",
            "NCAA NET rankings policy robots",
            "Second Spectrum tracking product terms",
            "Genius Sports college lineup data docs policy",
        ],
    )

