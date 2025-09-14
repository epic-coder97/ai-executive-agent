import json

UNSAFE_PHRASES = [
    "delete all",
    "format drive",
    "share password",
    "send pii",
]

class Guardrails:
    def allow_text(self, text: str) -> bool:
        t = text.lower()
        return not any(p in t for p in UNSAFE_PHRASES)

    def scrub_text(self, text: str) -> str:
        # demo-only scrub
        return text.replace("@", "[at]")

class ApprovalQueue:
    """User-scoped approvals."""
    def __init__(self, memory):
        self.memory = memory

    def require(self, user: str, action: str, summary: str, payload: dict) -> int:
        return self.memory.insert_approval(user, action, summary, json.dumps(payload, ensure_ascii=False))

    def list_pending(self, user: str):
        return self.memory.list_approvals(user=user, approved=0)

    def approve(self, approval_id: int):
        row = self.memory.get_approval(approval_id)
        self.memory.set_approved(approval_id)
        return row

    def approve_all(self, user: str) -> int:
        pend = self.list_pending(user)
        for p in pend:
            self.approve(p["id"])
        return len(pend)
