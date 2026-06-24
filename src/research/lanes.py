from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .contracts import ResearchLaneDescriptor


def build_research_lane_descriptor(
    lane_id: str,
    name: str,
    *,
    topic: str = "",
    owner: str = "research",
    status: str = "planned",
    tags: Iterable[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ResearchLaneDescriptor:
    cleaned_tags = tuple(str(tag).strip() for tag in (tags or ()) if str(tag).strip())
    return ResearchLaneDescriptor(
        lane_id=str(lane_id).strip() or "lane",
        name=str(name).strip() or "research lane",
        topic=str(topic).strip(),
        owner=str(owner).strip() or "research",
        status=str(status).strip() or "planned",
        tags=cleaned_tags,
        metadata=dict(metadata or {}),
    )


def list_research_lane_tags(descriptor: ResearchLaneDescriptor) -> tuple[str, ...]:
    return tuple(descriptor.tags)

