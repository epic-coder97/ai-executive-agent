from typing import Dict, Any, List
import re
from .tools import Toolbelt

SCHED_PAT = re.compile(r"(schedule|slot|meet|meeting|book|invite)", re.I)
EXP_PAT   = re.compile(r"(expense|report|receipt|reimburse)", re.I)
ZOOM_PAT  = re.compile(r"(zoom|video call|meet link)", re.I)

def naive_plan(task: str) -> List[str]:
    steps: List[str] = []
    t = task.lower()

    if SCHED_PAT.search(t):
        steps += [
            "parse scheduling request",
            "check calendar for conflicts",
            "propose 3 candidate slots",
            "draft email for approval",
        ]

    if EXP_PAT.search(t):
        steps += [
            "create expense report",
            "attach placeholder receipt",
        ]

    if ZOOM_PAT.search(t):
        steps.append("create zoom meeting placeholder")

    if not steps:
        steps = ["analyze request", "perform generic search/tool use", "summarize outcome"]
    return steps


def plan_and_execute(user_id: str, task: str, memory, guards, approvals, rag=None, mock_mode=True):
    toolbelt = Toolbelt(memory=memory, approvals=approvals, guards=guards, mock_mode=mock_mode)
    steps = naive_plan(task)
    trace: List[Dict[str, Any]] = []
    artifacts: List[Dict[str, Any]] = []

    if rag and any(k in task.lower() for k in ["policy", "handbook", "guideline", "expenses"]):
        answer, cites = rag.answer(task)
        artifacts.append({"grounded_answer": answer, "citations": cites})
        trace.append({"title": "RAG answer", "detail": answer})

    for s in steps:
        if s == "parse scheduling request":
            info = toolbelt.parse_scheduling_request(task)
            trace.append({"title": s, "detail": info})
        elif s == "check calendar for conflicts":
            info = toolbelt.calendar_check_conflicts(user_id)
            trace.append({"title": s, "detail": info})
        elif s == "propose 3 candidate slots":
            info = toolbelt.calendar_propose_slots(user_id)
            artifacts.append({"candidate_slots": info})
            trace.append({"title": s, "detail": info})
        elif s == "draft email for approval":
            info = toolbelt.email_draft_for_approval(user_id, task)
            artifacts.append({"email_draft_id": info})
            trace.append({"title": s, "detail": info})
        elif s == "create expense report":
            info = toolbelt.expense_create_report(user_id, task)
            artifacts.append({"expense_report": info})
            trace.append({"title": s, "detail": info})
        elif s == "attach placeholder receipt":
            info = toolbelt.expense_attach_receipt(user_id)
            trace.append({"title": s, "detail": info})
        elif s == "create zoom meeting placeholder":
            info = toolbelt.zoom_create_meeting(user_id, task)
            artifacts.append({"zoom_meeting": info})
            trace.append({"title": s, "detail": info})
        else:
            trace.append({"title": s, "detail": "performed generic step"})

    plan_text = "\n".join(f"- {i+1}. {s}" for i, s in enumerate(steps))
    return {"plan": plan_text, "trace": trace, "artifacts": artifacts}
