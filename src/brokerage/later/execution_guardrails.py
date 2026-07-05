from __future__ import annotations


def get_execution_guardrails() -> dict[str, object]:
    return {
        "future_only": True,
        "requires_human_approval": True,
        "requires_intentional_flag_enablement": True,
        "requires_provider_credentials": False,
        "supports_paper_execution_only": True,
        "live_order_placement_implemented": False,
        "live_bet_placement_implemented": False,
    }
