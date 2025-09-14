from typing import Dict, Any
from mocks import gcal, gmail, slack, expensify, zoom

class Toolbelt:
    def __init__(self, memory, approvals, guards, mock_mode: bool = True):
        self.memory = memory
        self.approvals = approvals
        self.guards = guards
        self.mock_mode = mock_mode

    # ---- Scheduling helpers ----
    def parse_scheduling_request(self, task: str) -> Dict[str, Any]:
        # naive parse, demo only
        return {"attendee": "Alex", "duration_min": 30, "day_hint": "Tuesday"}

    def calendar_check_conflicts(self, user_id: str) -> Dict[str, Any]:
        busy = gcal.list_events(user_id)
        return {"busy_blocks": busy}

    def calendar_propose_slots(self, user_id: str):
        return gcal.propose_slots(user_id, duration_min=30, day_hint="Tuesday")

    # ---- Email ----
    def email_draft_for_approval(self, user_id: str, task: str):
        draft = gmail.create_draft(
            to="alex@example.com",
            subject="Meeting proposal",
            body=(
                "Hi Alex,\n\nCould we do a 30-minute sync next Tuesday? "
                "Suggested times attached.\n\nThanks,\nEA Agent"
            ),
        )
        approval_id = self.approvals.require(
            user=user_id,
            action="send_email",
            summary="Send meeting proposal to Alex",
            payload=draft,
        )
        return {"draft": draft, "approval_id": approval_id}

    # ---- Expenses ----
    def expense_create_report(self, user_id: str, task: str):
        return expensify.create_report(user_id, title="October Ops Expenses")

    def expense_attach_receipt(self, user_id: str):
        return expensify.attach_placeholder_receipt()

    # ---- Zoom ----
    def zoom_create_meeting(self, user_id: str, task: str):
        mtg = zoom.create_meeting(topic="Sync", when="Thu 2pm PT")
        return mtg

    # ---- Slack ----
    def slack_post(self, channel: str, text: str):
        if not self.guards.allow_text(text):
            return {"blocked": True, "reason": "unsafe content"}
        clean = self.guards.scrub_text(text)
        return slack.post_message(channel, clean)
