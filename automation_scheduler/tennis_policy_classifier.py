from __future__ import annotations

from .completed_sports_policy_classifier import classify_completed_sports_source


def classify_tennis_source(
    candidate: dict[str, object],
    *,
    source_page: dict[str, object],
    robots_review: dict[str, object],
    terms_review: dict[str, object],
    license_review: dict[str, object],
    api_docs_review: dict[str, object],
) -> dict[str, object]:
    return dict(
        classify_completed_sports_source(
            candidate,
            source_page=source_page,
            robots_review=robots_review,
            terms_review=terms_review,
            license_review=license_review,
            api_docs_review=api_docs_review,
        )
    )
