from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


WRITE_ALLOWLIST: dict[str, set[str]] = {}


@dataclass(slots=True)
class ProviderWriteFirewallPolicy:
    provider_name: str = ""
    action_name: str = ""
    policy_status: str = "scaffold_only"
    write_allowlist: dict[str, list[str]] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=lambda: ["scaffold_only"])

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "action_name": self.action_name,
            "policy_status": self.policy_status,
            "write_allowlist": {key: list(value) for key, value in self.write_allowlist.items()},
            "blockers": list(self.blockers),
            "ok": False,
        }


def build_scaffold_write_firewall_policy(provider_name: str = "", action_name: str = "") -> ProviderWriteFirewallPolicy:
    return ProviderWriteFirewallPolicy(provider_name=provider_name, action_name=action_name)
