from __future__ import annotations

def evaluate_human_approval_gate(approval_status: str = "pending"):
    allowed = approval_status == "approved"
    return {"human_approval_required": True, "approval_status": approval_status if approval_status in {"pending", "approved", "rejected", "expired"} else "pending", "allowed": allowed}
