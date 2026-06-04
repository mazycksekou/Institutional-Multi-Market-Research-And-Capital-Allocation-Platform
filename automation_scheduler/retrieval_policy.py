from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


def normalize_domain(value: str) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if "://" not in text:
        text = f"https://{text}"
    parsed = urlparse(text)
    host = (parsed.netloc or parsed.path or "").split("@")[-1].split(":")[0].strip().lower()
    return host.lstrip("www.")


def domain_matches(pattern: str, domain: str) -> bool:
    pat = normalize_domain(pattern)
    host = normalize_domain(domain)
    if not pat or not host:
        return False
    if pat.startswith("*."):
        suffix = pat[2:]
        return host == suffix or host.endswith(f".{suffix}")
    return host == pat or host.endswith(f".{pat}")


def domain_is_blocked(domain: str, blocklist: tuple[str, ...]) -> bool:
    return any(domain_matches(pattern, domain) for pattern in blocklist)


def domain_is_allowed(domain: str, allowlist: tuple[str, ...]) -> bool:
    return any(domain_matches(pattern, domain) for pattern in allowlist)


@dataclass(frozen=True)
class RetrievalPolicy:
    allow_oxylabs: bool = False
    allow_paid_retrieval: bool = False
    source_id: str = ""
    domain: str = ""
    source_allowlist: tuple[str, ...] = ()
    domain_allowlist: tuple[str, ...] = ()
    domain_blocklist: tuple[str, ...] = ()

    def evaluate(self) -> dict[str, object]:
        normalized_domain = normalize_domain(self.domain)
        if not self.allow_oxylabs:
            return self._blocked("oxylabs_disabled_by_default")
        if not self.allow_paid_retrieval:
            return self._blocked("paid_retrieval_not_authorized")
        if self.source_allowlist and self.source_id not in set(self.source_allowlist):
            return self._blocked("source_id_not_allowlisted")
        if normalized_domain and self.domain_blocklist and domain_is_blocked(normalized_domain, self.domain_blocklist):
            return self._blocked("domain_blocklisted")
        if self.domain_allowlist and normalized_domain and not domain_is_allowed(normalized_domain, self.domain_allowlist):
            return self._blocked("domain_not_allowlisted")
        return {
            "allowed": True,
            "blocked_reason": None,
            "paid_source_enabled_count": 1,
            "open_free_mode": False,
            "allow_oxylabs": self.allow_oxylabs,
            "allow_paid_retrieval": self.allow_paid_retrieval,
            "source_id": self.source_id,
            "domain": normalized_domain,
        }

    def _blocked(self, reason: str) -> dict[str, object]:
        return {
            "allowed": False,
            "blocked_reason": reason,
            "paid_source_enabled_count": 0,
            "open_free_mode": True,
            "allow_oxylabs": self.allow_oxylabs,
            "allow_paid_retrieval": self.allow_paid_retrieval,
            "source_id": self.source_id,
            "domain": normalize_domain(self.domain),
        }
